"""
World Interpreter for Scenario Lab V3.

Translates actor narratives into mechanical consequences (metric changes).
"""

import json
import random
from typing import List, Dict, Any, Optional
from pathlib import Path

from scenario_lab.models import (
    WorldState,
    InterpreterOutput,
    MetricChange,
    MetricMetadata,
    Metrics,
    ActorView,
)
from scenario_lab.llm_provider import LLMProvider


class WorldInterpreter:
    """
    Translates natural language narratives into structured metric changes.

    The World Interpreter acts as a bridge between actor narratives and
    mechanical consequences, using an LLM to understand intent and map
    it to appropriate metric adjustments.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        model: str,
        prompt_template_path: Optional[Path] = None,
    ):
        """
        Initialize the World Interpreter.

        Args:
            llm_provider: LLM provider for interpretation
            model: Model name to use
            prompt_template_path: Path to prompt template file (optional)
        """
        self.llm_provider = llm_provider
        self.model = model
        self.prompt_template = self._load_prompt_template(prompt_template_path)

    def _load_prompt_template(self, path: Optional[Path]) -> str:
        """Load prompt template from file or use default."""
        if path and path.exists():
            return path.read_text()

        # Default prompt template
        return """You are the World Interpreter for Scenario Lab, a strategic simulation system.

Your role: Translate actor narratives into mechanical consequences (metric changes).

IMPORTANT CONSTRAINTS:
1. Actors can DIRECTLY affect their own metrics (private and public)
2. Actors can INDIRECTLY influence world metrics through their actions' consequences
3. Other actors' metrics change only through relationships, agreements, or world events
4. Stay within defined magnitude ranges (small/medium/large)
5. Be CONSERVATIVE: Small changes are more plausible than large ones
6. Only suggest changes that are clearly justified by the narrative

ACTOR: {actor_name}

ACTOR NARRATIVE:
{narrative}

CURRENT METRICS (for context):
{visible_metrics}

METRIC METADATA:
{metric_metadata}

TASK:
Analyze the actor's narrative and determine what mechanical changes should occur.

OUTPUT FORMAT (JSON):
{{
  "metric_changes": [
    {{
      "metric": "full.path.to.metric",
      "operation": "adjust",
      "magnitude": "small|medium|large",
      "direction": "increase|decrease",
      "reasoning": "clear explanation of why this change makes sense"
    }}
  ],
  "interpretation": "A narrative summary of what happened for the Director to weave into the story",
  "confidence": 0.8
}}

METRIC CHANGE RULES:
- operation: "adjust" uses magnitude+direction, "set" uses exact value
- For "adjust": magnitude must be one of ["small", "medium", "large"]
- For "adjust": direction must be one of ["increase", "decrease"]
- reasoning: Must explain the logical connection between narrative and change

MAGNITUDE GUIDELINES:
- small: Minor adjustments, routine actions, incremental progress
- medium: Significant but not transformative changes, major initiatives
- large: Dramatic shifts, crisis responses, transformative actions

Return ONLY valid JSON, no additional text."""

    async def interpret_narrative(
        self,
        actor: str,
        narrative: str,
        actor_view: ActorView,
        full_metrics: Metrics,
    ) -> InterpreterOutput:
        """
        Interpret an actor's narrative and produce structured metric changes.

        Args:
            actor: Name of the actor whose narrative is being interpreted
            narrative: The actor's free-form narrative description
            actor_view: The actor's filtered view of the world
            full_metrics: Complete metrics (for metadata access)

        Returns:
            InterpreterOutput with metric changes and interpretation
        """
        # Build context for the LLM
        visible_metrics_str = self._format_metrics(actor_view.visible_metrics)
        metadata_str = self._format_metadata(full_metrics)

        # Fill in the prompt template
        prompt = self.prompt_template.format(
            actor_name=actor,
            narrative=narrative,
            visible_metrics=visible_metrics_str,
            metric_metadata=metadata_str,
        )

        # Call LLM
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm_provider.complete(
            messages,
            self.model,
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        # Parse response
        try:
            data = json.loads(response)
            return InterpreterOutput(
                metric_changes=[MetricChange(**change) for change in data.get("metric_changes", [])],
                interpretation=data.get("interpretation", ""),
                confidence=data.get("confidence", 1.0),
            )
        except Exception as e:
            # Fallback if parsing fails
            return InterpreterOutput(
                metric_changes=[],
                interpretation=f"Failed to interpret narrative: {str(e)}",
                confidence=0.0,
            )

    def _format_metrics(self, metrics: Metrics) -> str:
        """Format metrics for display in prompt."""
        lines = ["WORLD METRICS:"]
        for key, value in metrics.world.items():
            lines.append(f"  {key}: {value}")

        lines.append("\nACTOR METRICS:")
        for actor, actor_metrics in metrics.actors.items():
            lines.append(f"  {actor}:")
            if actor_metrics.public:
                lines.append("    PUBLIC:")
                for key, value in actor_metrics.public.items():
                    lines.append(f"      {key}: {value}")
            if actor_metrics.private:
                lines.append("    PRIVATE:")
                for key, value in actor_metrics.private.items():
                    lines.append(f"      {key}: {value}")

        return "\n".join(lines)

    def _format_metadata(self, metrics: Metrics) -> str:
        """Format metric metadata for display in prompt."""
        if not metrics.metadata_registry:
            return "No metadata defined (using default ranges)"

        lines = []
        for path, metadata in metrics.metadata_registry.items():
            lines.append(f"\n{path}:")
            if metadata.description:
                lines.append(f"  description: {metadata.description}")
            if metadata.min is not None:
                lines.append(f"  min: {metadata.min}")
            if metadata.max is not None:
                lines.append(f"  max: {metadata.max}")
            if metadata.change_magnitudes:
                lines.append(f"  small change: {metadata.change_magnitudes.small}")
                lines.append(f"  medium change: {metadata.change_magnitudes.medium}")
                lines.append(f"  large change: {metadata.change_magnitudes.large}")
            if metadata.randomness > 0:
                lines.append(f"  randomness: {metadata.randomness}")

        return "\n".join(lines) if lines else "No metadata defined"

    def validate_change(
        self,
        actor: str,
        change: MetricChange,
        metrics: Metrics,
    ) -> tuple[bool, str]:
        """
        Validate that a metric change is allowed.

        Args:
            actor: Actor requesting the change
            change: The metric change to validate
            metrics: Current metrics state

        Returns:
            (is_valid, reason) tuple
        """
        # Parse metric path
        parts = change.metric.split(".")

        # Rule 1: Actors can only directly modify their own private metrics
        if parts[0] == "actors":
            if len(parts) < 3:
                return False, "Invalid metric path"

            target_actor = parts[1]
            visibility = parts[2]

            if target_actor != actor:
                return False, f"Actor {actor} cannot directly modify {target_actor}'s metrics"

            # Actors can modify their own private AND public metrics
            if visibility not in ["private", "public"]:
                return False, f"Invalid metric visibility: {visibility}"

        # Rule 2: World metrics can only be changed indirectly
        # (This is enforced by the prompt, but we log a warning)
        elif parts[0] == "world":
            # Allow but flag for review
            pass

        # Rule 3: Validate magnitude ranges
        metadata = metrics.get_metadata(change.metric)
        if change.operation == "adjust" and metadata and metadata.change_magnitudes:
            magnitude_range = getattr(metadata.change_magnitudes, change.magnitude)
            # This is just a range, actual value will be chosen randomly within it
            # So we just validate that the magnitude exists
            if change.magnitude not in ["small", "medium", "large"]:
                return False, f"Invalid magnitude: {change.magnitude}"

        # Rule 4: Validate bounds for set operations
        if change.operation == "set" and metadata:
            if metadata.min is not None and change.value < metadata.min:
                return False, f"Value {change.value} below minimum {metadata.min}"
            if metadata.max is not None and change.value > metadata.max:
                return False, f"Value {change.value} above maximum {metadata.max}"

        return True, "Valid"

    def apply_change(
        self,
        change: MetricChange,
        metrics: Metrics,
    ) -> float:
        """
        Apply a metric change and return the new value.

        Args:
            change: The metric change to apply
            metrics: Current metrics state (modified in place)

        Returns:
            New metric value after change
        """
        current_value = metrics.get_value(change.metric) or 0.0
        metadata = metrics.get_metadata(change.metric)

        if change.operation == "set":
            new_value = change.value
        elif change.operation == "adjust":
            # Get magnitude range
            if metadata and metadata.change_magnitudes:
                magnitude_range = getattr(metadata.change_magnitudes, change.magnitude)
            else:
                # Use defaults
                default_ranges = {
                    "small": (0.01, 0.05),
                    "medium": (0.05, 0.15),
                    "large": (0.15, 0.5),
                }
                magnitude_range = default_ranges[change.magnitude]

            # Pick random value within range
            change_amount = random.uniform(*magnitude_range)

            # Apply randomness if specified
            if metadata and metadata.randomness > 0:
                variance = random.uniform(-metadata.randomness, metadata.randomness)
                change_amount *= (1 + variance)

            # Scale by current value (percentage change)
            if current_value != 0:
                delta = current_value * change_amount
            else:
                # If current value is 0, use absolute change
                delta = change_amount

            # Apply direction
            if change.direction == "increase":
                new_value = current_value + delta
            else:
                new_value = current_value - delta
        else:
            new_value = current_value

        # Validate bounds
        if metadata:
            if metadata.min is not None:
                new_value = max(new_value, metadata.min)
            if metadata.max is not None:
                new_value = min(new_value, metadata.max)

        # Update metrics
        metrics.set_value(change.metric, new_value)

        return new_value
