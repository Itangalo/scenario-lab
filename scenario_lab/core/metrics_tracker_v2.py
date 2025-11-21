"""
Metrics Tracker V2 for Scenario Lab

Pure V2 implementation using Pydantic schemas and immutable state.
Replaces V1-style metrics_tracker.py with clean V2 patterns.

Key Differences from V1:
- Takes MetricsConfig (Pydantic) instead of YAML path
- Supports V2 extraction types (llm, keyword, pattern, manual)
- Uses async LLM calls for 'llm' extraction type
- Works with immutable ScenarioState
- No internal mutable state
"""
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from scenario_lab.schemas.metrics import MetricsConfig, MetricConfig, MetricExtraction
from scenario_lab.models.state import MetricRecord, ScenarioState
from scenario_lab.utils.api_client import make_llm_call_async, LLMResponse

logger = logging.getLogger(__name__)


class MetricsTrackerV2:
    """
    V2-native metrics tracker using Pydantic schemas

    Supports all V2 extraction types:
    - llm: Use LLM to extract metric from text
    - keyword: Search for keywords and score (count/presence/density)
    - pattern: Regex pattern matching
    - manual: Metrics created directly by user
    """

    def __init__(self, metrics_config: MetricsConfig, api_key: Optional[str] = None):
        """
        Initialize metrics tracker V2

        Args:
            metrics_config: Pydantic MetricsConfig from scenario_lab.schemas.metrics
            api_key: API key for LLM calls (for 'llm' extraction type)
        """
        self.config = metrics_config
        self.api_key = api_key

        # Convert metrics list to dict for fast lookup
        self.metrics: Dict[str, MetricConfig] = {
            m.name: m for m in metrics_config.metrics
        }

        logger.info(f"Initialized MetricsTrackerV2 with {len(self.metrics)} metrics")

    async def extract_metrics_from_text(
        self,
        turn: int,
        text: str,
        actor_name: Optional[str] = None,
    ) -> List[MetricRecord]:
        """
        Extract metrics from text using configured extraction methods

        Args:
            turn: Current turn number
            text: Text to extract metrics from
            actor_name: Optional actor name for actor-specific metrics

        Returns:
            List of MetricRecord objects extracted from text
        """
        extracted: List[MetricRecord] = []

        for metric_name, metric_config in self.metrics.items():
            # Skip actor-specific metrics if no actor context
            if metric_config.actor_specific and not actor_name:
                continue

            # Skip NON-actor-specific metrics when extracting from actor decisions
            # (they will be extracted once from world state instead)
            if not metric_config.actor_specific and actor_name:
                continue

            # Extract based on type
            extraction = metric_config.extraction

            if extraction.type == "llm":
                record = await self._extract_with_llm(
                    metric_config, turn, text, actor_name
                )
                if record:
                    extracted.append(record)

            elif extraction.type == "keyword":
                record = self._extract_with_keyword(
                    metric_config, turn, text, actor_name
                )
                if record:
                    extracted.append(record)

            elif extraction.type == "pattern":
                record = self._extract_with_pattern(
                    metric_config, turn, text, actor_name
                )
                if record:
                    extracted.append(record)

            elif extraction.type == "manual":
                # Manual metrics are created directly, skip extraction
                pass

        return extracted

    async def _extract_with_llm(
        self,
        metric: MetricConfig,
        turn: int,
        text: str,
        actor_name: Optional[str],
    ) -> Optional[MetricRecord]:
        """
        Extract metric using LLM

        Args:
            metric: Metric configuration
            turn: Current turn
            text: Text to analyze
            actor_name: Optional actor name

        Returns:
            MetricRecord if extraction succeeds, None otherwise
        """
        extraction = metric.extraction

        if not extraction.prompt:
            logger.warning(f"No prompt specified for LLM extraction of {metric.name}")
            return None

        # Build LLM prompt
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a metrics extraction assistant. "
                    "Extract the requested metric from the provided text. "
                    "Return ONLY a numeric value (integer or float). "
                    "If the metric cannot be determined, return 0."
                )
            },
            {
                "role": "user",
                "content": f"{extraction.prompt}\n\nText to analyze:\n{text}"
            }
        ]

        # Determine model to use
        model = extraction.model or "openai/gpt-4o-mini"

        try:
            # Make async LLM call
            response: LLMResponse = await make_llm_call_async(
                model=model,
                messages=messages,
                api_key=self.api_key,
                max_retries=2,
                context={"metric": metric.name, "turn": turn},
            )

            # Parse response (pass categories for categorical metrics)
            value = self._parse_numeric_value(
                response.content, metric.type, metric.categories
            )

            # Create MetricRecord
            record = MetricRecord(
                name=metric.name,
                value=value,
                turn=turn,
                timestamp=datetime.now(),
                metadata={
                    "actor": actor_name,
                    "extraction_type": "llm",
                    "model": model,
                    "raw_response": response.content,
                    "unit": metric.unit,
                    "description": metric.description,
                }
            )

            logger.debug(
                f"Extracted metric '{metric.name}' via LLM: {value} "
                f"(turn {turn}, actor: {actor_name or 'N/A'})"
            )

            return record

        except Exception as e:
            logger.error(f"Failed to extract metric '{metric.name}' via LLM: {e}")
            return None

    def _extract_with_keyword(
        self,
        metric: MetricConfig,
        turn: int,
        text: str,
        actor_name: Optional[str],
    ) -> Optional[MetricRecord]:
        """
        Extract metric using keyword search

        Args:
            metric: Metric configuration
            turn: Current turn
            text: Text to analyze
            actor_name: Optional actor name

        Returns:
            MetricRecord if keywords found, None otherwise
        """
        extraction = metric.extraction

        if not extraction.keywords:
            logger.warning(f"No keywords specified for keyword extraction of {metric.name}")
            return None

        # Count keyword occurrences
        text_lower = text.lower()
        matches = []

        for keyword in extraction.keywords:
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)
            if count > 0:
                matches.extend([keyword] * count)

        # Calculate value based on scoring method
        scoring = extraction.scoring or "count"

        if scoring == "count":
            value = float(len(matches))
        elif scoring == "presence":
            value = 1.0 if matches else 0.0
        elif scoring == "density":
            # Keywords per 100 words
            word_count = len(text.split())
            value = (len(matches) / word_count * 100) if word_count > 0 else 0.0
        else:
            logger.warning(f"Unknown scoring method '{scoring}', using count")
            value = float(len(matches))

        # Only create record if matches found (unless scoring is presence)
        if value == 0.0 and scoring != "presence":
            return None

        record = MetricRecord(
            name=metric.name,
            value=value,
            turn=turn,
            timestamp=datetime.now(),
            metadata={
                "actor": actor_name,
                "extraction_type": "keyword",
                "keywords": extraction.keywords,
                "matches": matches[:10],  # First 10 matches
                "scoring": scoring,
                "unit": metric.unit,
                "description": metric.description,
            }
        )

        logger.debug(
            f"Extracted metric '{metric.name}' via keyword: {value} "
            f"(turn {turn}, actor: {actor_name or 'N/A'})"
        )

        return record

    def _extract_with_pattern(
        self,
        metric: MetricConfig,
        turn: int,
        text: str,
        actor_name: Optional[str],
    ) -> Optional[MetricRecord]:
        """
        Extract metric using regex pattern

        Args:
            metric: Metric configuration
            turn: Current turn
            text: Text to analyze
            actor_name: Optional actor name

        Returns:
            MetricRecord if pattern matches, None otherwise
        """
        extraction = metric.extraction

        if not extraction.pattern:
            logger.warning(f"No pattern specified for pattern extraction of {metric.name}")
            return None

        try:
            # Find all matches
            matches = re.findall(extraction.pattern, text, re.IGNORECASE)

            if not matches:
                return None

            # Take last match (most recent mention)
            raw_value = matches[-1]

            # If match is a tuple (multiple regex groups), extract non-empty value
            if isinstance(raw_value, tuple):
                raw_value = next((v for v in raw_value if v), '')

            # Convert to numeric value (pass categories for categorical metrics)
            value = self._parse_numeric_value(raw_value, metric.type, metric.categories)

            record = MetricRecord(
                name=metric.name,
                value=value,
                turn=turn,
                timestamp=datetime.now(),
                metadata={
                    "actor": actor_name,
                    "extraction_type": "pattern",
                    "pattern": extraction.pattern,
                    "raw_value": str(raw_value),
                    "match_count": len(matches),
                    "unit": metric.unit,
                    "description": metric.description,
                }
            )

            logger.debug(
                f"Extracted metric '{metric.name}' via pattern: {value} "
                f"(turn {turn}, actor: {actor_name or 'N/A'})"
            )

            return record

        except re.error as e:
            logger.error(f"Invalid regex pattern for metric '{metric.name}': {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to extract metric '{metric.name}' via pattern: {e}")
            return None

    def _parse_numeric_value(
        self,
        raw_value: str,
        metric_type: str,
        categories: Optional[List[str]] = None
    ) -> float:
        """
        Parse string value to float

        Args:
            raw_value: Raw string value
            metric_type: Metric type (continuous, categorical, boolean)
            categories: List of valid categories (for categorical metrics)

        Returns:
            Parsed float value (for categorical: index in categories list)
        """
        try:
            # Remove whitespace
            value_str = str(raw_value).strip()

            # Handle boolean
            if metric_type == "boolean":
                if value_str.lower() in ("true", "yes", "1"):
                    return 1.0
                else:
                    return 0.0

            # Handle categorical - return index in categories list
            if metric_type == "categorical" and categories:
                value_lower = value_str.lower()
                for idx, cat in enumerate(categories):
                    if cat.lower() == value_lower:
                        return float(idx)
                # Category not found - log but don't warn excessively
                logger.debug(f"Categorical value '{raw_value}' not in categories {categories}")
                return -1.0  # Indicates unknown category

            # Handle scientific notation (e.g., "10^25")
            if '^' in value_str:
                base, exp = value_str.split('^')
                return float(base) ** float(exp)

            # Try direct float conversion
            return float(value_str)

        except (ValueError, TypeError, ZeroDivisionError):
            logger.warning(f"Could not parse value '{raw_value}' as float, returning 0.0")
            return 0.0

    async def extract_metrics_from_world_state(
        self,
        state: ScenarioState,
    ) -> List[MetricRecord]:
        """
        Extract metrics from current world state

        Args:
            state: Current scenario state

        Returns:
            List of MetricRecord objects
        """
        return await self.extract_metrics_from_text(
            turn=state.turn,
            text=state.world_state.content,
            actor_name=None,  # World state is not actor-specific
        )

    async def extract_metrics_from_decisions(
        self,
        state: ScenarioState,
    ) -> List[MetricRecord]:
        """
        Extract metrics from actor decisions

        Args:
            state: Current scenario state with decisions

        Returns:
            List of MetricRecord objects
        """
        extracted: List[MetricRecord] = []

        for actor_name, decision in state.decisions.items():
            # Extract from reasoning
            reasoning_metrics = await self.extract_metrics_from_text(
                turn=state.turn,
                text=decision.reasoning,
                actor_name=actor_name,
            )
            extracted.extend(reasoning_metrics)

            # Extract from action
            action_metrics = await self.extract_metrics_from_text(
                turn=state.turn,
                text=decision.action,
                actor_name=actor_name,
            )
            extracted.extend(action_metrics)

        return extracted

    def calculate_summary_statistics(
        self,
        state: ScenarioState,
    ) -> Dict[str, Any]:
        """
        Calculate summary statistics for metrics in state

        Args:
            state: Scenario state with metrics

        Returns:
            Dictionary with statistics for each metric
        """
        stats: Dict[str, Dict[str, Any]] = {}

        # Group metrics by name
        metrics_by_name: Dict[str, List[MetricRecord]] = {}
        for metric in state.metrics:
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = []
            metrics_by_name[metric.name].append(metric)

        # Calculate statistics for each metric
        for metric_name, records in metrics_by_name.items():
            if not records:
                continue

            values = [m.value for m in records]
            turns = [m.turn for m in records]

            # Get metric config
            metric_config = self.metrics.get(metric_name)
            if not metric_config:
                continue

            stats[metric_name] = {
                "name": metric_name,
                "type": metric_config.type,
                "unit": metric_config.unit or "",
                "description": metric_config.description,
                "count": len(values),
                "turns": turns,
                "values": values,
            }

            # Calculate numeric statistics for continuous metrics
            if metric_config.type == "continuous" and values:
                stats[metric_name].update({
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                    "first": values[0],
                    "last": values[-1],
                    "change": values[-1] - values[0] if len(values) > 1 else 0.0,
                })

        return stats

    def get_metrics_summary(
        self,
        state: ScenarioState,
    ) -> Dict[str, Any]:
        """
        Get comprehensive metrics summary

        Args:
            state: Scenario state

        Returns:
            Dictionary with metrics summary
        """
        stats = self.calculate_summary_statistics(state)

        # Get metrics by turn
        metrics_by_turn: Dict[int, Dict[str, float]] = {}
        for metric in state.metrics:
            if metric.turn not in metrics_by_turn:
                metrics_by_turn[metric.turn] = {}
            metrics_by_turn[metric.turn][metric.name] = metric.value

        # Get final metrics (from last turn)
        final_metrics = {}
        if state.metrics:
            last_turn = max(m.turn for m in state.metrics)
            final_metrics = {
                m.name: m.value
                for m in state.metrics
                if m.turn == last_turn
            }

        return {
            "scenario": state.scenario_name,
            "total_turns": state.turn,
            "total_metrics": len(state.metrics),
            "metrics_by_turn": metrics_by_turn,
            "final_metrics": final_metrics,
            "summary_statistics": stats,
        }

    def save_metrics_summary(
        self,
        state: ScenarioState,
        output_path: Path,
    ) -> None:
        """
        Save metrics summary to JSON file

        Args:
            state: Scenario state
            output_path: Path to output JSON file
        """
        summary = self.get_metrics_summary(state)

        try:
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)

            logger.info(f"Saved metrics summary to {output_path}")

        except Exception as e:
            logger.error(f"Failed to save metrics summary to {output_path}: {e}")
            raise
