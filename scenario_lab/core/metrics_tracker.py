"""
Metrics Tracker for Scenario Lab V2

Manages and tracks quantitative metrics throughout scenario execution.
Works with immutable ScenarioState and MetricRecord dataclasses.

V2 Design:
- Pure functions instead of mutable state
- Works with ScenarioState.metrics list
- Returns new MetricRecord objects
- No internal state storage
"""
import json
import yaml
import re
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import asdict

from scenario_lab.models.state import MetricRecord, ScenarioState

logger = logging.getLogger(__name__)


class MetricsTracker:
    """
    Tracks quantitative metrics defined in scenario configuration (V2 - Pure functions)

    Unlike V1, this doesn't maintain internal state. It loads metric definitions
    and provides functions to extract metrics from text and calculate statistics.
    """

    def __init__(self, metrics_config_path: Optional[Path] = None):
        """
        Initialize metrics tracker

        Args:
            metrics_config_path: Path to metrics.yaml file (optional)
        """
        self.metrics_definitions: Dict[str, Dict[str, Any]] = {}
        self.scenario_name: str = ""

        if metrics_config_path and metrics_config_path.exists():
            self.load_metrics_definitions(metrics_config_path)

    def load_metrics_definitions(self, config_path: Path):
        """
        Load metrics definitions from YAML file

        Args:
            config_path: Path to metrics.yaml
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            self.metrics_definitions = config.get('metrics', {})
            self.scenario_name = config.get('scenario_name', '')

            logger.info(f"Loaded {len(self.metrics_definitions)} metric definitions")

        except Exception as e:
            logger.error(f"Failed to load metrics definitions from {config_path}: {e}")
            raise

    def extract_metrics_from_text(
        self,
        turn: int,
        text: str,
        actor_name: Optional[str] = None
    ) -> List[MetricRecord]:
        """
        Extract metrics from text using patterns defined in metrics config

        Args:
            turn: Turn number
            text: Text to extract metrics from (world state, actor decision, etc.)
            actor_name: Optional actor name for actor-specific metrics

        Returns:
            List of MetricRecord objects extracted from text
        """
        extracted_metrics: List[MetricRecord] = []

        for metric_name, metric_def in self.metrics_definitions.items():
            # Skip if this is an actor-specific metric and we don't have actor context
            if metric_def.get('actor_specific') and not actor_name:
                continue

            # Skip if metric is for a different actor
            if metric_def.get('actor_specific') and metric_def.get('actor') != actor_name:
                continue

            extraction_method = metric_def.get('extraction_method', 'regex')

            if extraction_method == 'regex':
                pattern = metric_def.get('pattern')
                if pattern:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        # Take the last match (most recent mention)
                        value = matches[-1]

                        # If value is a tuple (from multiple regex groups), extract the non-empty value
                        if isinstance(value, tuple):
                            value = next((v for v in value if v), '')

                        # Convert to appropriate type
                        value_type = metric_def.get('type', 'string')
                        converted_value = self._convert_value(value, value_type)

                        # Create MetricRecord
                        metric_record = MetricRecord(
                            name=metric_name,
                            value=float(converted_value) if isinstance(converted_value, (int, float)) else 0.0,
                            turn=turn,
                            metadata={
                                'actor': actor_name,
                                'type': value_type,
                                'raw_value': str(value),
                                'unit': metric_def.get('unit', ''),
                                'definition': metric_def.get('description', '')
                            }
                        )

                        extracted_metrics.append(metric_record)

                        logger.debug(
                            f"Extracted metric '{metric_name}': {converted_value} "
                            f"(turn {turn}, actor: {actor_name or 'N/A'})"
                        )

            elif extraction_method == 'manual':
                # Manual extraction - metrics will be created directly
                pass

        return extracted_metrics

    def extract_metrics_from_world_state(
        self,
        state: ScenarioState
    ) -> List[MetricRecord]:
        """
        Extract metrics from current world state

        Args:
            state: Current scenario state

        Returns:
            List of MetricRecord objects
        """
        world_state_content = state.world_state.content
        return self.extract_metrics_from_text(
            turn=state.turn,
            text=world_state_content,
            actor_name=None  # World state is not actor-specific
        )

    def extract_metrics_from_decisions(
        self,
        state: ScenarioState
    ) -> List[MetricRecord]:
        """
        Extract metrics from actor decisions

        Args:
            state: Current scenario state with decisions

        Returns:
            List of MetricRecord objects
        """
        extracted_metrics: List[MetricRecord] = []

        for actor_name, decision in state.decisions.items():
            # Extract from reasoning
            metrics = self.extract_metrics_from_text(
                turn=state.turn,
                text=decision.reasoning,
                actor_name=actor_name
            )
            extracted_metrics.extend(metrics)

            # Extract from action
            metrics = self.extract_metrics_from_text(
                turn=state.turn,
                text=decision.action,
                actor_name=actor_name
            )
            extracted_metrics.extend(metrics)

        return extracted_metrics

    def calculate_summary_statistics(
        self,
        state: ScenarioState
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
        for metric_name, metric_records in metrics_by_name.items():
            if not metric_records:
                continue

            values = [m.value for m in metric_records]
            turns = [m.turn for m in metric_records]

            # Get metric definition
            metric_def = self.metrics_definitions.get(metric_name, {})
            metric_type = metric_def.get('type', 'float')

            stats[metric_name] = {
                "name": metric_name,
                "type": metric_type,
                "unit": metric_def.get('unit', ''),
                "description": metric_def.get('description', ''),
                "count": len(values),
                "turns": turns,
                "values": values,
            }

            # Calculate numeric statistics if applicable
            if metric_type in ['integer', 'float'] and values:
                stats[metric_name].update({
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                    "first": values[0],
                    "last": values[-1],
                    "change": values[-1] - values[0] if len(values) > 1 else 0.0
                })

        return stats

    def get_metrics_summary(
        self,
        state: ScenarioState
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
            "scenario": self.scenario_name,
            "total_turns": state.turn,
            "total_metrics": len(state.metrics),
            "metrics_definitions": self.metrics_definitions,
            "metrics_by_turn": metrics_by_turn,
            "final_metrics": final_metrics,
            "summary_statistics": stats
        }

    def save_metrics_summary(
        self,
        state: ScenarioState,
        output_path: Path
    ):
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

    def _convert_value(self, value: str, value_type: str) -> Any:
        """
        Convert string value to appropriate type

        Args:
            value: String value to convert
            value_type: Target type ('integer', 'float', 'boolean', 'string')

        Returns:
            Converted value
        """
        try:
            if value_type == 'integer':
                return int(value)
            elif value_type == 'float':
                # Handle scientific notation (e.g., "10^25")
                if '^' in value:
                    base, exp = value.split('^')
                    return float(base) ** float(exp)
                return float(value)
            elif value_type == 'boolean':
                # For boolean metrics, any non-empty match indicates True
                if value:
                    return 1.0  # Convert to numeric for MetricRecord
                return 0.0
            else:  # string or unknown
                # Try to convert to float for MetricRecord, otherwise return 0.0
                try:
                    return float(value)
                except ValueError:
                    return 0.0
        except (ValueError, TypeError):
            return 0.0  # Default to 0.0 if conversion fails

    def print_summary(self, state: ScenarioState):
        """
        Print formatted metrics summary

        Args:
            state: Scenario state
        """
        print("\n" + "=" * 60)
        print("METRICS SUMMARY")
        print("=" * 60)

        if not state.metrics:
            print("\nNo metrics recorded.")
            return

        # Get statistics
        stats = self.calculate_summary_statistics(state)

        # Group metrics by turn
        metrics_by_turn: Dict[int, List[MetricRecord]] = {}
        for metric in state.metrics:
            if metric.turn not in metrics_by_turn:
                metrics_by_turn[metric.turn] = []
            metrics_by_turn[metric.turn].append(metric)

        # Print by turn
        print("\nMetrics by Turn:")
        for turn in sorted(metrics_by_turn.keys()):
            print(f"\n  Turn {turn}:")
            for metric in metrics_by_turn[turn]:
                metric_def = self.metrics_definitions.get(metric.name, {})
                unit = metric_def.get('unit', '')
                if unit:
                    print(f"    {metric.name}: {metric.value} {unit}")
                else:
                    print(f"    {metric.name}: {metric.value}")

        # Print summary statistics
        if stats:
            print("\nSummary Statistics:")
            for metric_name, stat_data in stats.items():
                print(f"\n  {metric_name}:")
                if 'min' in stat_data:  # Numeric metric
                    print(f"    Min: {stat_data['min']}")
                    print(f"    Max: {stat_data['max']}")
                    print(f"    Mean: {stat_data['mean']:.2f}")
                    print(f"    Change: {stat_data['change']:.2f}")
                    print(f"    Trend: {stat_data['values']}")

        print("=" * 60 + "\n")


def load_metrics_tracker(scenario_path: Path) -> Optional[MetricsTracker]:
    """
    Load metrics tracker from scenario directory

    Args:
        scenario_path: Path to scenario directory

    Returns:
        MetricsTracker if metrics.yaml exists, None otherwise
    """
    metrics_file = scenario_path / "metrics.yaml"

    if not metrics_file.exists():
        logger.debug(f"No metrics.yaml found in {scenario_path}")
        return None

    try:
        tracker = MetricsTracker(metrics_file)
        return tracker

    except Exception as e:
        logger.warning(f"Failed to load metrics tracker: {e}")
        return None
