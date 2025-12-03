"""Prompt construction from templates and scenario data."""

from pathlib import Path
from typing import Optional
from .models import Scenario, Actor
import json


TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class PromptBuilder:
    """Constructs prompts from templates and scenario data."""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self._load_templates()

    def _load_templates(self):
        """Load all prompt templates from templates directory."""
        system_dir = TEMPLATES_DIR / "system-prompts"
        self.templates = {
            "events_system": (system_dir / "events.md").read_text(encoding="utf-8"),
            "actor_system": (system_dir / "actor.md").read_text(encoding="utf-8"),
            "rules_system": (system_dir / "metric-rules.md").read_text(encoding="utf-8"),
            "metrics_system": (system_dir / "metrics-update.md").read_text(encoding="utf-8"),
        }

    def _get_system_prompt(self, prompt_type: str, actor_id: Optional[str] = None) -> str:
        """Get system prompt, preferring custom over template.

        Args:
            prompt_type: Type of prompt ("events", "actor", "metric_rules", "metrics_update")
            actor_id: Optional actor ID for actor-specific prompts

        Returns:
            System prompt with placeholders replaced if custom
        """
        # Map prompt type to template key
        template_key_map = {
            "events": "events_system",
            "actor": "actor_system",
            "metric_rules": "rules_system",
            "metrics_update": "metrics_system",
        }
        template_key = template_key_map.get(prompt_type, f"{prompt_type}_system")

        # For actor prompts, check for actor-specific custom prompt first
        if prompt_type == "actor" and actor_id:
            actor_specific_key = f"actor_{actor_id}"
            if actor_specific_key in self.scenario.custom_system_prompts:
                # Use actor-specific custom prompt and replace placeholders
                prompt = self.scenario.custom_system_prompts[actor_specific_key]
                return self._replace_placeholders(prompt, actor_id)

        # Check if scenario has generic custom prompt for this type
        custom_key = prompt_type.replace("-", "_")
        if custom_key in self.scenario.custom_system_prompts:
            # Use custom prompt and replace placeholders
            prompt = self.scenario.custom_system_prompts[custom_key]
            return self._replace_placeholders(prompt, actor_id)

        # Fall back to template (no placeholder replacement for templates)
        return self.templates[template_key]

    def _replace_placeholders(self, prompt: str, actor_id: Optional[str] = None) -> str:
        """Replace placeholders in custom system prompts with scenario data.

        Args:
            prompt: Prompt text with placeholders
            actor_id: Optional actor ID for actor-specific replacements

        Returns:
            Prompt with placeholders replaced
        """
        # Build actors list
        actors_list = []
        for aid, actor in self.scenario.actors.items():
            actors_list.append(f"* {actor.name}: {actor.short_description}")
        actors_text = "\n".join(actors_list)

        # Build metrics list
        metrics_list = []
        for metric_id, metric in self.scenario.metrics.metrics.items():
            metrics_list.append(f"* {metric_id}")
            metrics_list.append(f"  * Description: {metric.description}")
            metrics_list.append(f"  * Range: {metric.min_value} to {metric.max_value} {metric.unit}")
            if metric.reference_points:
                metrics_list.append("  * Reference points:")
                for value, desc in sorted(metric.reference_points.items()):
                    metrics_list.append(f"    - {value}: {desc}")
        metrics_text = "\n".join(metrics_list)

        # Replace placeholders
        result = prompt.replace("{{scenario_description}}", self.scenario.config.description)
        result = result.replace("{{actors_list}}", actors_text)
        result = result.replace("{{metrics_list}}", metrics_text)

        # Actor-specific replacements
        if actor_id and actor_id in self.scenario.actors:
            actor = self.scenario.actors[actor_id]
            result = result.replace("{{actor_name}}", actor.name)
            result = result.replace("{{actor_description}}", actor.long_description)

        return result

    def build_events_prompt(self, turn: int) -> tuple[str, str]:
        """Build system and user prompts for events step.

        Returns:
            (system_prompt, user_prompt)
        """
        time_period = self._get_time_period(turn)

        # Get system prompt (custom or template)
        system = self._get_system_prompt("events")

        # Build user prompt
        user_parts = [
            f"It is now turn {turn} which covers {time_period}.",
            "",
        ]

        # Add metrics history context
        if turn == 1:
            user_parts.append("This is the first turn, so there is no previous history. Current metrics look like this:")
        else:
            user_parts.append("Current metrics look like this:")

        user_parts.append("")
        user_parts.append("```json")
        user_parts.append(self.scenario.metrics.to_json())
        user_parts.append("```")
        user_parts.append("")

        # Add world state
        user_parts.append("The world state at the start of the turn is described as follows:")
        user_parts.append("")
        user_parts.append(self.scenario.world_state.narrative)
        user_parts.append("")
        user_parts.append("---")
        user_parts.append("")

        # Add notepad
        user_parts.append("The notepad contains the following information:")
        user_parts.append("")
        if self.scenario.notepad.strip():
            user_parts.append(self.scenario.notepad)
        else:
            user_parts.append("(Empty)")
        user_parts.append("")
        user_parts.append("---")
        user_parts.append("")

        # Add events list
        user_parts.append("The list of potential external events looks like this:")
        user_parts.append("")
        user_parts.append(self._format_events_list())
        user_parts.append("")
        user_parts.append("---")
        user_parts.append("")

        # Add instruction
        user_parts.append(
            "Use the background information to determine which external events can occur in this turn. "
            "If the probability is specified as a formula or description, you should calculate the actual value."
        )
        user_parts.append("")
        user_parts.append(
            "Your response should be a JSON array with objects for each event whose conditions are met, "
            "in this format:"
        )
        user_parts.append("")
        user_parts.append("```json")
        user_parts.append('[')
        user_parts.append('  {"id": "event1_id", "probability": 0.10},')
        user_parts.append('  {"id": "event2_id", "probability": 0.24}')
        user_parts.append(']')
        user_parts.append("```")
        user_parts.append("")
        user_parts.append(
            "The probability should be specified as a value between 0 and 1. "
            "If no event meets the conditions, respond with an empty array: `[]`"
        )
        user_parts.append("")
        user_parts.append("Respond *only* with this JSON array, nothing else.")

        user = "\n".join(user_parts)
        return system, user

    def build_actor_prompt(
        self, actor_id: str, turn: int, triggered_events: list[dict]
    ) -> tuple[str, str]:
        """Build prompts for a specific actor.

        Args:
            actor_id: ID of the actor
            turn: Current turn number
            triggered_events: List of events that occurred this turn

        Returns:
            (system_prompt, user_prompt)
        """
        actor = self.scenario.actors[actor_id]
        time_period = self._get_time_period(turn)

        # Get system prompt (custom or template)
        system = self._get_system_prompt("actor", actor_id)

        # Build user prompt
        user_parts = [
            f"It is now turn {turn} which covers {time_period}.",
            "",
        ]

        # Add metrics
        user_parts.append("Current metrics look like this:")
        user_parts.append("")
        user_parts.append("```json")
        user_parts.append(self.scenario.metrics.to_json())
        user_parts.append("```")
        user_parts.append("")

        # Add world state
        user_parts.append("The world state at the start of the turn is described as follows:")
        user_parts.append("")
        user_parts.append(self.scenario.world_state.narrative)
        user_parts.append("")
        user_parts.append("---")
        user_parts.append("")

        # Add triggered events if any
        if triggered_events:
            user_parts.append("This turn, the following external events have occurred:")
            user_parts.append("")
            for event in triggered_events:
                event_obj = next((e for e in self.scenario.events if e.id == event["id"]), None)
                if event_obj:
                    user_parts.append(f"**{event_obj.id}:** {event_obj.description}")
            user_parts.append("")
        else:
            user_parts.append("No special events occur this turn.")
            user_parts.append("")

        user_parts.append("---")
        user_parts.append("")

        # Add instruction
        user_parts.append(
            "Use the background information to determine (1) whether your goals should be adjusted and "
            "(2) which actions you want to take during the turn."
        )
        user_parts.append("")
        user_parts.append(
            "Actions should align with your goals and be realistic given time and other resources. "
            "Your actions will be evaluated by a Game Master, who determines how they affect the world. "
            "Bold actions can have greater impact, but also greater risk of failure."
        )
        user_parts.append("")
        user_parts.append("Respond with a Markdown text containing the following sections:")
        user_parts.append("")
        user_parts.append("* Heading level 2: Goals")
        user_parts.append("* Brief description of your goals in a bullet list")
        user_parts.append("* Optional heading level 3: Reason for changes (only if goals changed)")
        user_parts.append("* Brief description of why goals changed (only if goals changed)")
        user_parts.append("* Heading level 2: Actions")
        user_parts.append(
            "* One paragraph for each action, describing at an appropriate level each action you intend to carry out during the turn."
        )

        user = "\n".join(user_parts)
        return system, user

    def build_rules_prompt(
        self, turn: int, actor_actions: dict[str, str], triggered_events: list[dict]
    ) -> tuple[str, str]:
        """Build prompts for metric rules update.

        Args:
            turn: Current turn number
            actor_actions: Dict of actor_id -> action markdown
            triggered_events: List of events that occurred

        Returns:
            (system_prompt, user_prompt)
        """
        time_period = self._get_time_period(turn)

        # Get system prompt (custom or template)
        system = self._get_system_prompt("metric_rules")

        # Build user prompt
        user_parts = [
            f"It is now turn {turn} which covers {time_period}.",
            "",
            "The Metric Rules looked like this (possibly updated):",
            "",
            self.scenario.metric_rules,
            "",
            "The world state at the start of the turn is described as follows:",
            "",
            self.scenario.world_state.narrative,
            "",
            "---",
            "",
            "The notepad contains the following information:",
            "",
        ]

        if self.scenario.notepad.strip():
            user_parts.append(self.scenario.notepad)
        else:
            user_parts.append("(Empty)")

        user_parts.extend([
            "",
            "---",
            "",
        ])

        # Add triggered events
        user_parts.append("This turn, the following external events have occurred:")
        user_parts.append("")
        if triggered_events:
            for event in triggered_events:
                event_obj = next((e for e in self.scenario.events if e.id == event["id"]), None)
                if event_obj:
                    user_parts.append(f"**{event_obj.id}:** {event_obj.description}")
        else:
            user_parts.append("None")
        user_parts.append("")
        user_parts.append("---")
        user_parts.append("")

        # Add actor actions
        user_parts.append("The actors in the scenario describe their actions as follows:")
        user_parts.append("")
        for actor_id, actions in actor_actions.items():
            actor = self.scenario.actors[actor_id]
            user_parts.append(f"**{actor.name}:**")
            user_parts.append("")
            user_parts.append(actions)
            user_parts.append("")

        user_parts.append("---")
        user_parts.append("")
        user_parts.append(
            "Use this information to assess whether Metric Rules should be updated based on "
            "what has happened in the world and what the actors have done."
        )
        user_parts.append("")
        user_parts.append("Respond with an updated list of Metric Rules in the same format as before.")

        user = "\n".join(user_parts)
        return system, user

    def build_metrics_prompt(
        self, turn: int, actor_actions: dict[str, str], triggered_events: list[dict]
    ) -> tuple[str, str]:
        """Build prompts for metrics update.

        Args:
            turn: Current turn number
            actor_actions: Dict of actor_id -> action markdown
            triggered_events: List of events that occurred

        Returns:
            (system_prompt, user_prompt)
        """
        time_period = self._get_time_period(turn)

        # Get system prompt (custom or template)
        system = self._get_system_prompt("metrics_update")

        # Build user prompt
        user_parts = [
            f"It is now turn {turn} which covers {time_period}.",
            "",
            "The Metric Rules looked like this (possibly updated):",
            "",
            self.scenario.metric_rules,
            "",
            "The world state at the start of the turn is described as follows:",
            "",
            self.scenario.world_state.narrative,
            "",
            "---",
            "",
            "The notepad contains the following information:",
            "",
        ]

        if self.scenario.notepad.strip():
            user_parts.append(self.scenario.notepad)
        else:
            user_parts.append("(Empty)")

        user_parts.extend([
            "",
            "---",
            "",
        ])

        # Add triggered events
        user_parts.append("This turn, the following external events have occurred:")
        user_parts.append("")
        if triggered_events:
            for event in triggered_events:
                event_obj = next((e for e in self.scenario.events if e.id == event["id"]), None)
                if event_obj:
                    user_parts.append(f"**{event_obj.id}:** {event_obj.description}")
        else:
            user_parts.append("None")
        user_parts.append("")
        user_parts.append("---")
        user_parts.append("")

        # Add actor actions
        user_parts.append("The actors in the scenario describe their actions as follows:")
        user_parts.append("")
        for actor_id, actions in actor_actions.items():
            actor = self.scenario.actors[actor_id]
            user_parts.append(f"**{actor.name}:**")
            user_parts.append("")
            user_parts.append(actions)
            user_parts.append("")

        user_parts.append("---")
        user_parts.append("")
        user_parts.append("Use this information to do the following:")
        user_parts.append("")
        user_parts.append(
            "* Determine how successful the actors are with their actions. "
            "This is based on how the world looks and your assessment of how likely they are to succeed."
        )
        user_parts.append("* Based on the actors' actions and Metric Rules, determine Metrics for the next turn.")
        user_parts.append("* Write a coherent narrative that tells what happens in the world during this turn.")
        user_parts.append("")
        user_parts.append("Respond with a Markdown text with the following content:")
        user_parts.append("")
        user_parts.append("* Heading level 2: Metrics")
        user_parts.append('* A JSON object describing all metrics, in the following format: `{"metric1_name": value1, "metric2_name": value2}`')
        user_parts.append("* Heading level 2: Narrative")
        user_parts.append("* A coherent story about what happens in the world during the turn (max 400 words). You may use subheadings (level 3) if desired.")

        user = "\n".join(user_parts)
        return system, user

    def _format_events_list(self) -> str:
        """Format available events for events prompt."""
        lines = []
        for event in self.scenario.events:
            # Skip already-occurred non-repeatable events
            if event.occurred and not event.can_repeat:
                continue

            lines.append(f"**{event.id}**")
            lines.append(f"- ID: {event.id}")
            lines.append(f"- Condition: {event.condition}")
            lines.append(f"- Probability: {event.probability}")
            lines.append(f"- Can repeat: {'Yes' if event.can_repeat else 'No'}")
            lines.append(f"- Description: {event.description}")
            lines.append("")

        return "\n".join(lines)

    def _get_time_period(self, turn: int) -> str:
        """Get time period string for turn."""
        from .loader import get_time_period

        return get_time_period(
            self.scenario.config.start_date, turn, self.scenario.config.time_scale
        )
