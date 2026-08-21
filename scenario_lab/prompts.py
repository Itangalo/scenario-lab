"""Prompt construction from templates and scenario data."""

from pathlib import Path
from typing import Optional, Any
from .models import Scenario, Actor
import json
from jinja2 import Template
from jinja2.sandbox import SandboxedEnvironment


TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class PromptBuilder:
    """Constructs prompts from templates and scenario data."""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario

        # SECURITY: Create sandboxed Jinja2 environment for custom templates
        # This prevents template injection attacks (SSTI) in user-provided templates
        self.jinja_env = SandboxedEnvironment(
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self._load_templates()

    def _load_templates(self):
        """Load all prompt templates from templates directory."""
        system_dir = TEMPLATES_DIR / "system-prompts"
        user_dir = TEMPLATES_DIR / "user-prompts"
        
        self.system_templates = {
            "events_system": (system_dir / "events.md").read_text(encoding="utf-8"),
            "actor_system": (system_dir / "actor.md").read_text(encoding="utf-8"),
            "rules_system": (system_dir / "metric-rules.md").read_text(encoding="utf-8"),
            "metrics_system": (system_dir / "metrics-update.md").read_text(encoding="utf-8"),
            "summarize": (system_dir / "summarize.md").read_text(encoding="utf-8"),
            "analysis_system": (system_dir / "analysis.md").read_text(encoding="utf-8"),
            "synthesis_system": (system_dir / "synthesis.md").read_text(encoding="utf-8"),
            "format_fix_system": (system_dir / "format-fix.md").read_text(encoding="utf-8"),
            "constitutional_referee_system": (system_dir / "constitutional-referee.md").read_text(encoding="utf-8"),
            "constitutional_referee_correction_system": (system_dir / "constitutional-referee-correction.md").read_text(encoding="utf-8"),
        }

        self.user_templates = {
            "events": (user_dir / "events.md").read_text(encoding="utf-8"),
            "actor": (user_dir / "actor.md").read_text(encoding="utf-8"),
            "metric_rules": (user_dir / "metric-rules.md").read_text(encoding="utf-8"),
            "metrics_update": (user_dir / "metrics-update.md").read_text(encoding="utf-8"),
            "summarize": (user_dir / "summarize.md").read_text(encoding="utf-8"),
            "analysis": (user_dir / "analysis.md").read_text(encoding="utf-8"),
            "synthesis": (user_dir / "synthesis.md").read_text(encoding="utf-8"),
            "format_fix_events": (user_dir / "format-fix-events.md").read_text(encoding="utf-8"),
            "format_fix_metrics": (user_dir / "format-fix-metrics.md").read_text(encoding="utf-8"),
            "constitutional_referee": (user_dir / "constitutional-referee.md").read_text(encoding="utf-8"),
            "constitutional_referee_correction": (user_dir / "constitutional-referee-correction.md").read_text(encoding="utf-8"),
        }

    def _get_system_prompt(self, prompt_type: str, actor_id: Optional[str] = None) -> str:
        """Get system prompt, preferring custom over template.

        Args:
            prompt_type: Type of prompt ("events", "actor", "metric_rules", "metrics_update")
            actor_id: Optional actor ID for actor-specific prompts

        Returns:
            Rendered system prompt.

        System prompts are rendered with the same sandboxed Jinja environment
        as user prompts. Before this, they went through a plain string replace
        that handled only a handful of space-free placeholders, so a scenario
        override written as a Jinja template (conditionals, spaced
        placeholders) reached the model as raw template source with every
        branch present at once – silently, since nothing errors on unrendered
        markup. The constitutional-referee prompts were already Jinja-rendered;
        this makes the rest consistent.
        """
        # Map prompt type to template key
        template_key_map = {
            "events": "events_system",
            "actor": "actor_system",
            "metric_rules": "rules_system",
            "metrics_update": "metrics_system",
            "analysis": "analysis_system",
            "synthesis": "synthesis_system",
            "format_fix": "format_fix_system",
        }
        template_key = template_key_map.get(prompt_type, f"{prompt_type}_system")

        # For actor prompts, check for actor-specific custom prompt first
        if prompt_type == "actor" and actor_id:
            actor_specific_key = f"actor_{actor_id}"
            if actor_specific_key in self.scenario.custom_system_prompts:
                prompt = self.scenario.custom_system_prompts[actor_specific_key]
                return self._render_system_prompt(prompt, actor_id)

        # Check if scenario has generic custom prompt for this type
        custom_key = prompt_type.replace("-", "_")
        if custom_key in self.scenario.custom_system_prompts:
            prompt = self.scenario.custom_system_prompts[custom_key]
            return self._render_system_prompt(prompt, actor_id)

        # Fall back to template
        return self._render_system_prompt(self.system_templates[template_key], actor_id)

    def _render_system_prompt(self, prompt: str, actor_id: Optional[str] = None) -> str:
        """Render a system prompt template with the sandboxed Jinja environment.

        SECURITY: uses the same sandboxed environment as custom user prompts,
        since scenario-supplied system prompts are equally untrusted input.
        """
        template = self.jinja_env.from_string(prompt)
        return template.render(**self._get_system_prompt_context(actor_id))

    def _get_system_prompt_context(self, actor_id: Optional[str] = None) -> dict[str, Any]:
        """Build the render context available to system prompt templates.

        Includes the legacy placeholder names so existing prompts written as
        ``{{actors_list}}`` keep working unchanged, plus ``actor_id`` and one
        ``metric_<id>`` per metric so actor prompts can branch on who they are
        and reference live metric values – which is what scenario authors were
        already writing before it worked.
        """
        context: dict[str, Any] = {
            "scenario_name": self.scenario.config.name,
            "scenario_description": self.scenario.config.description,
            "actors_list": self._format_actors_list(),
            "metrics_list": self._format_metrics_list(),
            "constitution": self.scenario.constitution or "",
            "output_language": self.scenario.config.output_language,
            "actor_id": actor_id,
            "actor_name": "",
            "actor_description": "",
        }

        if actor_id and actor_id in self.scenario.actors:
            actor = self.scenario.actors[actor_id]
            context["actor_name"] = actor.name
            context["actor_description"] = actor.long_description
            context["actor_short_description"] = actor.short_description

        # Individual metric values as {{metric_<id>}}, matching user prompts.
        for m_id, metric in self.scenario.metrics.metrics.items():
            context[f"metric_{m_id.replace('-', '_')}"] = metric.value

        return context

    def _format_actors_list(self) -> str:
        """Render the actor roster used by several system prompts."""
        return "\n".join(
            f"* {actor.name}: {actor.short_description}"
            for actor in self.scenario.actors.values()
        )

    def _format_metrics_list(self) -> str:
        """Render the metric catalog used by several system prompts."""
        lines: list[str] = []
        for metric_id, metric in self.scenario.metrics.metrics.items():
            lines.append(f"* {metric_id}")
            lines.append(f"  * Description: {metric.description}")
            lines.append(f"  * Range: {metric.min_value} to {metric.max_value} {metric.unit}")
            if metric.reference_points:
                lines.append("  * Reference points:")
                for value, desc in sorted(metric.reference_points.items()):
                    lines.append(f"    - {value}: {desc}")
        return "\n".join(lines)

    def _get_user_template(self, prompt_type: str) -> Template:
        """Get user prompt template, preferring custom over default.

        Args:
            prompt_type: Type of prompt ("events", "actor", "metric_rules", "metrics_update")

        Returns:
            Jinja2 Template object
        """
        # Normalize prompt type to match dictionary keys (e.g. "metric-rules" -> "metric_rules")
        key = prompt_type.replace("-", "_")

        # Check custom scenario prompts first
        if key in self.scenario.custom_user_prompts:
            # SECURITY: Use sandboxed environment for custom templates to prevent SSTI
            return self.jinja_env.from_string(self.scenario.custom_user_prompts[key])

        # Default templates are trusted, but use sandboxed env for consistency
        return self.jinja_env.from_string(self.user_templates[key])

    def _replace_placeholders(self, prompt: str, actor_id: Optional[str] = None) -> str:
        """Deprecated: retained for callers outside the package.

        System prompts are now rendered by :meth:`_render_system_prompt`, which
        handles the same placeholders plus full Jinja syntax.
        """
        return self._render_system_prompt(prompt, actor_id)

    def _get_common_context(self, turn: int) -> dict[str, Any]:
        """Get context variables common to all prompts."""
        time_period = self._get_time_period(turn)
        metrics_json = self.scenario.metrics.to_json()
        world_state = self.scenario.world_state.narrative
        
        notepad = "(Empty)"
        if self.scenario.notepad.strip():
            notepad = self.scenario.notepad

        context = {
            "turn": turn,
            "time_period": time_period,
            "metrics_json": metrics_json,
            "world_state": world_state,
            "historical_summary": self.scenario.world_state.historical_summary,
            "notepad": notepad,
            "output_language": self.scenario.config.output_language,
        }
        
        # Add current month information if possible (simple parsing)
        # This assumes time_period format like "January-June 2026" or "September 2026"
        context["time_period_lower"] = time_period.lower()
        
        # Add individual metrics as {{metric_ID}}
        for m_id, metric in self.scenario.metrics.metrics.items():
            # Sanitize ID for use as variable name
            safe_id = m_id.replace("-", "_")
            context[f"metric_{safe_id}"] = metric.value
            
        return context

    def build_events_prompt(self, turn: int) -> tuple[str, str]:
        """Build system and user prompts for events step.

        Returns:
            (system_prompt, user_prompt)
        """
        # Get system prompt (custom or template)
        system = self._get_system_prompt("events")

        # Get user template
        template = self._get_user_template("events")

        # Build context
        context = self._get_common_context(turn)
        context["events_list"] = self._format_events_list()

        emergent = self.scenario.config.emergent_events
        context["emergent_events_enabled"] = emergent.enabled
        context["emergent_max_per_turn"] = emergent.max_per_turn
        context["emergent_max_probability"] = emergent.max_probability

        # Render user prompt
        user = template.render(**context)

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
        # Get system prompt (custom or template)
        system = self._get_system_prompt("actor", actor_id)

        # Get user template
        template = self._get_user_template("actor")
        
        # Build context
        context = self._get_common_context(turn)
        
        # Add actor-specific context
        if actor_id in self.scenario.actors:
            actor = self.scenario.actors[actor_id]
            context["actor_name"] = actor.name
            context["actor_description"] = actor.long_description
        
        context["triggered_events"] = self._format_triggered_events(triggered_events)

        # Render user prompt
        user = template.render(**context)

        return system, user

    def _format_triggered_events(self, triggered_events: list[dict]) -> str:
        """Format triggered events for actor/rules/metrics prompts.

        Listed events use the description from the scenario definition.
        Emergent events are not in the scenario definition, so they fall back
        to the description the Game Master proposed for them.
        """
        event_lines = []
        for event in triggered_events:
            event_obj = next((e for e in self.scenario.events if e.id == event["id"]), None)
            if event_obj:
                event_lines.append(f"**{event_obj.id}:** {event_obj.description}")
            elif event.get("description"):
                event_lines.append(f"**{event['id']} (emergent event):** {event['description']}")
        return "\n".join(event_lines)

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
        # Get system prompt (custom or template)
        system = self._get_system_prompt("metric_rules")

        # Get user template
        template = self._get_user_template("metric_rules")
        
        # Build context
        context = self._get_common_context(turn)
        context["metric_rules"] = self.scenario.metric_rules
        context["rule_evolution_policy"] = self._format_rule_evolution_policy(turn)
        context["triggered_events"] = self._format_triggered_events(triggered_events)

        # Format actor actions
        actions_lines = []
        for actor_id, actions in actor_actions.items():
            actor = self.scenario.actors[actor_id]
            actions_lines.append(f"**{actor.name}:**")
            actions_lines.append("")
            actions_lines.append(actions)
            actions_lines.append("")
        context["actor_actions"] = "\n".join(actions_lines)

        # Render user prompt
        user = template.render(**context)
        
        return system, user

    def _format_rule_evolution_policy(self, turn: int) -> str:
        """Describe rule-evolution guardrails for the current turn."""
        policy = self.scenario.config.rule_evolution
        lines = [
            f"- Maximum substantive rule changes this turn: {policy.max_changes_per_turn}",
            "- Default posture: keep the existing rule set unless clear evidence justifies a change.",
            "- Small, explicit, well-motivated edits are preferred over broad rewrites.",
        ]
        if turn <= policy.freeze_until_turn:
            lines.insert(
                0,
                f"- Substantive rule changes are not allowed before turn {policy.freeze_until_turn + 1}. "
                "Carry forward the current rules and state that no material rule changes were made.",
            )
        return "\n".join(lines)

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
        # Get system prompt (custom or template)
        system = self._get_system_prompt("metrics_update")
        
        # Get user template
        template = self._get_user_template("metrics_update")
        
        # Build context
        context = self._get_common_context(turn)
        context["metric_rules"] = self.scenario.metric_rules
        context["triggered_events"] = self._format_triggered_events(triggered_events)
        
        # Format actor actions
        actions_lines = []
        for actor_id, actions in actor_actions.items():
            actor = self.scenario.actors[actor_id]
            actions_lines.append(f"**{actor.name}:**")
            actions_lines.append("")
            actions_lines.append(actions)
            actions_lines.append("")
        context["actor_actions"] = "\n".join(actions_lines)

        # Render user prompt
        user = template.render(**context)
        
        return system, user

    def build_summary_prompt(self, historical_summary: str, current_narrative: str) -> tuple[str, str]:
        """Build prompts for summarization step.

        Args:
            historical_summary: Concise summary of previous turns
            current_narrative: Narrative of the current turn

        Returns:
            (system_prompt, user_prompt)
        """
        system = self.system_templates["summarize"]
        
        # Get user template
        template = self._get_user_template("summarize")
        
        # Build context
        context = {
            "historical_summary": historical_summary,
            "current_narrative": current_narrative,
            "output_language": self.scenario.config.output_language, # Pass output language to summary prompt
        }

        user = template.render(**context)
        
        return system, user

    def build_analysis_prompt(self, analysis_context: dict[str, Any]) -> tuple[str, str]:
        """Build prompts for post-run analysis."""
        system = self._get_system_prompt("analysis")
        template = self._get_user_template("analysis")

        context = {
            "output_language": self.scenario.config.output_language,
            **analysis_context,
        }

        user = template.render(**context)
        return system, user

    def build_synthesis_prompt(self, synthesis_context: dict[str, Any]) -> tuple[str, str]:
        """Build prompts for cross-run synthesis over an ensemble of runs."""
        system = self._get_system_prompt("synthesis")
        template = self._get_user_template("synthesis")

        context = {
            "output_language": self.scenario.config.output_language,
            **synthesis_context,
        }

        user = template.render(**context)
        return system, user

    def build_format_fix_events_prompt(self, turn: int, previous_response: str) -> tuple[str, str]:
        """Build prompts to fix invalid events output formatting."""
        system = self._get_system_prompt("format_fix")
        template = self._get_user_template("format_fix_events")
        context = self._get_common_context(turn)
        context["previous_response"] = previous_response
        user = template.render(**context)
        return system, user

    def build_format_fix_metrics_prompt(self, turn: int, previous_response: str) -> tuple[str, str]:
        """Build prompts to fix invalid metrics update output formatting."""
        system = self._get_system_prompt("format_fix")
        template = self._get_user_template("format_fix_metrics")
        context = self._get_common_context(turn)
        context["previous_response"] = previous_response
        user = template.render(**context)
        return system, user

    def build_constitutional_referee_prompt(
        self, turn: int, previous_metrics: dict, new_metrics: dict, narrative: str
    ) -> tuple[str, str]:
        """Build prompts for constitutional referee step.

        Args:
            turn: Current turn number
            previous_metrics: Metrics before the update
            new_metrics: Proposed new metrics
            narrative: Narrative explaining the changes

        Returns:
            (system_prompt, user_prompt)
        """
        system = self._render_constitutional_system_prompt("constitutional_referee")

        # Get user template
        template = self._get_user_template("constitutional_referee")

        # Build context
        from .loader import get_time_period

        time_period = get_time_period(
            self.scenario.config.start_date, turn, self.scenario.config.time_scale
        )

        context = {
            "turn": turn,
            "time_period": time_period,
            "previous_metrics_json": json.dumps(previous_metrics, indent=2, ensure_ascii=False),
            "new_metrics_json": json.dumps(new_metrics, indent=2, ensure_ascii=False),
            "narrative": narrative,
        }

        user = template.render(**context)

        return system, user

    def build_constitutional_correction_prompt(
        self,
        turn: int,
        previous_metrics: dict,
        new_metrics: dict,
        narrative: str,
        violations: str,
    ) -> tuple[str, str]:
        """Build prompts for correcting a metrics update after constitutional violations."""
        system = self._render_constitutional_system_prompt("constitutional_referee_correction")
        template = self._get_user_template("constitutional_referee_correction")

        from .loader import get_time_period

        time_period = get_time_period(
            self.scenario.config.start_date, turn, self.scenario.config.time_scale
        )

        context = {
            "turn": turn,
            "time_period": time_period,
            "previous_metrics_json": json.dumps(previous_metrics, indent=2, ensure_ascii=False),
            "new_metrics_json": json.dumps(new_metrics, indent=2, ensure_ascii=False),
            "narrative": narrative,
            "violations": violations,
            "output_language": self.scenario.config.output_language,
        }

        user = template.render(**context)

        return system, user

    def _render_constitutional_system_prompt(self, prompt_type: str) -> str:
        """Render a constitutional system prompt with the scenario constitution injected."""
        key = prompt_type.replace("-", "_")

        if key in self.scenario.custom_system_prompts:
            template_text = self.scenario.custom_system_prompts[key]
        else:
            template_text = self.system_templates[f"{key}_system"]

        system_template = self.jinja_env.from_string(template_text)
        return system_template.render(constitution=self.scenario.constitution)

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
