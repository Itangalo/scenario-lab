"""Prompt construction from templates and scenario data."""

from pathlib import Path
from typing import Optional, Any
from .statements import render_ledger
from .models import Scenario, build_expression_env, Actor
import json
import hashlib

from jinja2 import Template
from jinja2.sandbox import SandboxedEnvironment


TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _prompt_key(text: str) -> str:
    """Content key for provenance lookup, so concurrent builds cannot collide."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _as_sentence(text: str) -> str:
    """Give a scenario description its own terminating full stop.

    The templates used to write `{{ scenario_description.rstrip('.') }}.`, which
    reads the same but leaves the final stop belonging to the template while the
    context value still carries one. The provenance spans are found by locating
    the context value in the rendered text, so that stop was attributed to the
    description anyway -- swallowing the template's own character and leaving the
    sign-off documents showing a sentence that stops dead at "focuses on". Adding
    the stop here keeps the value and the rendered text identical.
    """
    text = text.strip()
    if not text or text.endswith((".", "!", "?", ":")):
        return text
    return text + "."


class PromptBuilder:
    """Constructs prompts from templates and scenario data."""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario

        # Provenance of rendered prompts, keyed by a hash of the rendered text.
        # Recorded while the prompt is assembled rather than inferred from it
        # afterwards: which template file was used, and which scenario file or
        # run-time structure each interpolated value came from. Keyed by content
        # so that a concurrent multi-actor turn cannot mix two prompts up.
        self._provenance: dict[str, dict] = {}
        self._template_label: str = "unknown"

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
            "cohort_comparison_system": (system_dir / "cohort-comparison.md").read_text(encoding="utf-8"),
            "format_fix_system": (system_dir / "format-fix.md").read_text(encoding="utf-8"),
            "constitutional_referee_system": (system_dir / "constitutional-referee.md").read_text(encoding="utf-8"),
            "constitutional_referee_correction_system": (system_dir / "constitutional-referee-correction.md").read_text(encoding="utf-8"),
            "statement_relevance_system": (system_dir / "statement_relevance.md").read_text(encoding="utf-8"),
        }

        self.user_templates = {
            "events": (user_dir / "events.md").read_text(encoding="utf-8"),
            "actor": (user_dir / "actor.md").read_text(encoding="utf-8"),
            "metric_rules": (user_dir / "metric-rules.md").read_text(encoding="utf-8"),
            "metrics_update": (user_dir / "metrics-update.md").read_text(encoding="utf-8"),
            "summarize": (user_dir / "summarize.md").read_text(encoding="utf-8"),
            "analysis": (user_dir / "analysis.md").read_text(encoding="utf-8"),
            "synthesis": (user_dir / "synthesis.md").read_text(encoding="utf-8"),
            "cohort_comparison": (user_dir / "cohort-comparison.md").read_text(encoding="utf-8"),
            "format_fix_events": (user_dir / "format-fix-events.md").read_text(encoding="utf-8"),
            "format_fix_metrics": (user_dir / "format-fix-metrics.md").read_text(encoding="utf-8"),
            "constitutional_referee": (user_dir / "constitutional-referee.md").read_text(encoding="utf-8"),
            "constitutional_referee_correction": (user_dir / "constitutional-referee-correction.md").read_text(encoding="utf-8"),
            "statement_relevance": (user_dir / "statement_relevance.md").read_text(encoding="utf-8"),
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
            self._template_label = f"system-prompts/{prompt_type}.md (this scenario's override)"
            return self._render_system_prompt(prompt, actor_id)

        # Fall back to template
        self._template_label = f"templates/system-prompts/{prompt_type}.md (shared default)"
        return self._render_system_prompt(self.system_templates[template_key], actor_id)

    def _render_system_prompt(self, prompt: str, actor_id: Optional[str] = None) -> str:
        """Render a system prompt template with the sandboxed Jinja environment.

        SECURITY: uses the same sandboxed environment as custom user prompts,
        since scenario-supplied system prompts are equally untrusted input.
        """
        template = self.jinja_env.from_string(prompt)
        return self._render(template, self._get_system_prompt_context(actor_id))

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
            "scenario_description": _as_sentence(self.scenario.config.description),
            "actors_list": self._format_actors_list(),
            # So a template can say "a single actor" rather than announce a
            # list of one. Scenarios with one actor are ordinary here.
            "actor_count": len(self.scenario.actors),
            "metrics_list": self._format_metrics_list(),
            "constitution": self.scenario.constitution or "",
            "output_language": self.scenario.config.output_language,
            "actor_id": actor_id,
            "actor_name": "",
            "actor_description": "",
            "behavioral_traits": "",
        }

        if actor_id and actor_id in self.scenario.actors:
            actor = self.scenario.actors[actor_id]
            context["actor_name"] = actor.name
            context["actor_description"] = actor.long_description
            context["actor_short_description"] = actor.short_description
            # Traits never change, so they belong in the cache-controlled
            # system prompt rather than the per-turn user prompt.
            context["behavioral_traits"] = "\n".join(
                f"- {trait}" for trait in actor.behavioral_traits
            )

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
            self._template_label = f"user-prompts/{prompt_type}.md (this scenario's override)"
            return self.jinja_env.from_string(self.scenario.custom_user_prompts[key])

        # Default templates are trusted, but use sandboxed env for consistency
        self._template_label = f"templates/user-prompts/{prompt_type}.md (shared default)"
        return self.jinja_env.from_string(self.user_templates[key])

    def _replace_placeholders(self, prompt: str, actor_id: Optional[str] = None) -> str:
        """Deprecated: retained for callers outside the package.

        System prompts are now rendered by :meth:`_render_system_prompt`, which
        handles the same placeholders plus full Jinja syntax.
        """
        return self._render_system_prompt(prompt, actor_id)

    # Marks the tracked section that _compose_notepad appends to the Game
    # Master's notepad. Idempotency depends on the exact header string.
    EMERGING_SECTION_HEADER = "## Emerging developments (tracked)"

    def _compose_notepad(self) -> str:
        """Render the notepad as the LLM steps should see it this turn.

        The stored notepad is exactly what the metrics step wrote last turn.
        When emergent events are enabled, a tracked section listing emerging
        developments is appended on top, regenerated from
        ``scenario.emerging_developments`` each time so it can never go stale:
        if a model copies the section into its own notepad output, the stale
        copy is stripped before the fresh one is added. The actor's prompt does
        not render the notepad, so tracked developments reach actors only as
        narrative traces written by the Game Master.
        """
        base = self.scenario.notepad.strip()
        if self.EMERGING_SECTION_HEADER in base:
            base = base.split(self.EMERGING_SECTION_HEADER)[0].rstrip()

        developments = self.scenario.emerging_developments
        cfg = self.scenario.config.emergent_events
        if not (cfg.enabled and cfg.track_unfired) or not developments:
            return base or "(Empty)"

        lines = [self.EMERGING_SECTION_HEADER, ""]
        for dev in developments:
            note = dev.description.strip() or "(no description recorded)"
            lines.append(
                f"- `{dev.id}` -- first noted turn {dev.first_turn}, "
                f"listed in {dev.appearances} turn(s) so far: {note}"
            )
        section = "\n".join(lines)
        return f"{base}\n\n{section}" if base else section

    # Where each interpolated value comes from. Named here rather than guessed
    # later, because the whole point of the sign-off documents is to distinguish
    # a scenario file that reaches the model from one that only looks as though
    # it does. Values not listed are short scalars (turn number, time period)
    # that no reviewer needs traced.
    VARIABLE_SOURCES: dict[str, str] = {
        "metrics_list": "metrics.md, one entry per metric with its reference points",
        "metrics_json": "the run's live metric values",
        "events_list": "events.md, parsed to id / condition / probability / description per event -- the prose sections of that file are NOT rendered",
        "event_history": "the run's own event record",
        "metric_rules": "metric-rules.md as it currently stands, including any variant patch",
        "constitution": "constitution.md",
        "actors_list": "background/actors/*.md, short descriptions only",
        "actor_description": "background/actors/<actor>.md, the Long description section up to its first ### heading -- everything below that is dropped by load_actor",
        "actor_short_description": "background/actors/<actor>.md, Short description",
        "statement_ledger": "the actor's live statement ledger",
        "statements_list": "the actor's live statement ledger",
        "behavioral_traits": "background/actors/<actor>.md, Behavioral traits",
        "historical_summary": "the run's rolling summary, written by the Game Master",
        "notepad": "the Game Master's notepad, carried across turns",
        "previous_actions": "the actor's own response from the previous turn",
        "scenario_description": "scenario.yaml, description",
        "scenario_name": "scenario.yaml, name",
        "triggered_events_text": "the events that fired this turn",
    }

    def _variable_sources(self, turn: int) -> dict[str, str]:
        """VARIABLE_SOURCES with the entries whose origin depends on the turn."""
        sources = dict(self.VARIABLE_SOURCES)
        if turn <= 1:
            sources["world_state"] = "background/context.md, seeded as the opening world state"
        else:
            sources["world_state"] = "the Game Master's narrative from the previous turn"
        if turn > 1:
            sources["background_context"] = (
                "background/fixed-facts.md"
                if self.scenario.fixed_facts
                else "background/context.md, in full (no background/fixed-facts.md in this scenario)"
            )
        return sources

    def _render(self, template, context: dict[str, Any], turn: Optional[int] = None) -> str:
        """Render a template and record where every part of the result came from.

        The spans are found by locating each interpolated value in the rendered
        text. Jinja inserts values verbatim, so this is a lookup rather than a
        guess; anything not covered by a span is the template's own words.
        """
        rendered = template.render(**context)
        sources = self._variable_sources(turn if turn is not None else 0)
        spans: list[dict] = []
        for name, source in sources.items():
            value = context.get(name)
            if not isinstance(value, str) or len(value.strip()) < 20:
                continue
            start = 0
            while True:
                index = rendered.find(value, start)
                if index == -1:
                    break
                spans.append({"start": index, "end": index + len(value), "variable": name, "source": source})
                start = index + len(value)
        # Widest first at a shared start, so containment below keeps the outer.
        spans.sort(key=lambda s: (s["start"], -(s["end"] - s["start"])))
        # Values nest: an actor's short description is also a substring of the
        # actors list built from it. Reporting both spans made the sign-off
        # documents print the short description twice, once inside the roster
        # and once on its own. The enclosing span is the one that says where the
        # text in the prompt actually came from, so the nested one is dropped.
        outermost: list[dict] = []
        reach = -1
        for span in spans:
            if span["end"] <= reach:
                continue
            outermost.append(span)
            reach = max(reach, span["end"])
        spans = outermost
        self._provenance[_prompt_key(rendered)] = {
            "template": self._template_label,
            "spans": spans,
        }
        return rendered

    def provenance_for(self, rendered: str) -> Optional[dict]:
        """Return the recorded provenance of a rendered prompt, if it was recorded."""
        return self._provenance.get(_prompt_key(rendered))

    def _background_context_for_turn(self, turn: int) -> str:
        """Return the fixed-background block for this turn, if it earns its place.

        Empty in turn 1, where ``world_state`` already carries the full context
        and the block would duplicate it. From turn 2 on, the scenario's compact
        ``fixed_facts`` when it has one, and the full context when it does not.
        """
        if turn <= 1:
            return ""
        return (self.scenario.fixed_facts or self.scenario.context or "").strip()

    def _get_common_context(self, turn: int) -> dict[str, Any]:
        """Get context variables common to all prompts."""
        time_period = self._get_time_period(turn)
        metrics_json = self.scenario.metrics.to_json()
        world_state = self.scenario.world_state.narrative

        notepad = self._compose_notepad()

        context = {
            "turn": turn,
            "time_period": time_period,
            "time_scale": self.scenario.config.time_scale,
            "metrics_json": metrics_json,
            "world_state": world_state,
            "historical_summary": self.scenario.world_state.historical_summary,
            "notepad": notepad,
            # background/context.md is loaded once and then only used to seed
            # world_state.narrative, which the Game Master overwrites in turn 1.
            # Anything a scenario fixes at the start -- an election result, a
            # treaty, a map -- otherwise vanishes after a single turn, so it is
            # kept available for the whole run as its own block.
            #
            # Two refinements on that, both about not saying the same thing
            # twice. In turn 1 world_state IS the context, verbatim, so
            # rendering the block as well puts the entire opening description
            # into the prompt a second time; it is suppressed there. From turn 2
            # a scenario that provides background/fixed-facts.md gets that
            # compact restatement instead of the full opening, which is what the
            # block is actually for once the narrative has moved on.
            "background_context": self._background_context_for_turn(turn),
            "output_language": self.scenario.config.output_language,
            # Lets templates branch on the emergent-events policy (for example
            # to explain the tracked notepad section) without hardcoding any
            # of its wording.
            "emergent_events_enabled": self.scenario.config.emergent_events.enabled,
            "has_emerging_developments": bool(
                self.scenario.config.emergent_events.enabled
                and self.scenario.config.emergent_events.track_unfired
                and self.scenario.emerging_developments
            ),
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

    def _format_event_history(self, turn: int) -> str:
        """Chronological record of what has fired, one line per completed turn.

        Gate conditions are windowed ("if X occurred in any of the previous 4
        completed turns"), and until this existed the events step had to answer
        that from the narrative and the historical summary -- prose that
        condenses and loses dates. Giving it the record directly makes gate
        judgments checkable rather than recalled.
        """
        if not self.scenario.event_log:
            return ""
        by_turn: dict[int, list[str]] = {}
        for entry in self.scenario.event_log:
            entry_turn = entry.get("turn")
            event_id = entry.get("id")
            if not isinstance(entry_turn, int) or not isinstance(event_id, str):
                continue
            if entry_turn >= turn:  # only completed turns count for windows
                continue
            ids = by_turn.setdefault(entry_turn, [])
            if event_id not in ids:
                ids.append(event_id)
        if not by_turn:
            return ""
        return "\n".join(
            f"- Turn {t} ({turn - t} turn(s) ago): " + ", ".join(by_turn[t])
            for t in sorted(by_turn)
        )

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
        context["event_history"] = self._format_event_history(turn)

        emergent = self.scenario.config.emergent_events
        context["emergent_events_enabled"] = emergent.enabled
        context["emergent_max_per_turn"] = emergent.max_per_turn
        context["emergent_max_probability"] = emergent.max_probability

        # Render user prompt
        user = self._render(template, context, context.get("turn"))

        return system, user

    def build_actor_prompt(
        self,
        actor_id: str,
        turn: int,
        triggered_events: list[dict],
        previous_actions: str = "",
    ) -> tuple[str, str]:
        """Build prompts for a specific actor.

        Args:
            actor_id: ID of the actor
            turn: Current turn number
            triggered_events: List of events that occurred this turn
            previous_actions: The actor's own response from the previous turn.
                Empty on turn 1. Not rendered by the default template, but
                supplied so scenario overrides can give an actor a memory of
                its own last output -- the only durable record some scenarios
                need (portfolios, tracked commitments) that the lossy
                historical summary cannot provide.

        Returns:
            (system_prompt, user_prompt)
        """
        # Get system prompt (custom or template)
        system = self._get_system_prompt("actor", actor_id)

        # Get user template
        template = self._get_user_template("actor")

        # Build context
        context = self._get_common_context(turn)
        context["previous_actions"] = previous_actions
        
        # Add actor-specific context
        context["statement_ledger"] = ""
        if actor_id in self.scenario.actors:
            actor = self.scenario.actors[actor_id]
            context["actor_name"] = actor.name
            context["actor_description"] = actor.long_description
            # The ledger changes across turns, so it goes in the user prompt.
            # Rendered verbatim from the live ledger: the actor never restates
            # it, which is what keeps drift from being invisible.
            context["statement_ledger"] = render_ledger(actor)

        context["triggered_events"] = self._format_triggered_events(triggered_events)

        # Render user prompt
        user = self._render(template, context, context.get("turn"))

        return system, user

    def build_statement_relevance_prompt(
        self,
        actor_id: str,
        statement,
        proposal,
        triggered_events: list[dict],
        world_state: str,
        previous_actions: str = "",
    ) -> tuple[str, str]:
        """Build prompts for the relevance check on one statement proposal.

        Deliberately narrow: the referee sees the statement, the proposal, the
        named trigger and this turn's inputs -- enough to locate the trigger and
        judge whether it bears on the statement, and nothing that would invite a
        judgement about whether the change is a good idea.
        """
        system = self.system_templates["statement_relevance_system"]

        if proposal.kind == "modify":
            summary = f"Rewrite it to read: {proposal.text}"
        elif proposal.kind == "reclassify":
            summary = f"Downgrade it from {statement.tier} to {proposal.tier}."
        elif proposal.kind == "retire":
            summary = "Drop the statement entirely."
        else:
            summary = f"{proposal.kind} `{proposal.statement_id}`"

        actor = self.scenario.actors.get(actor_id)
        context = {
            "actor_name": actor.name if actor else actor_id,
            "statement_id": statement.id,
            "statement_tier": statement.tier,
            "statement_text": statement.text,
            "proposal_summary": summary,
            "trigger": proposal.trigger,
            "triggered_events": self._format_triggered_events(triggered_events),
            "world_state": world_state,
            "previous_actions": previous_actions,
        }

        template = self._get_user_template("statement_relevance")
        return system, self._render(template, context, context.get("turn"))

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
        user = self._render(template, context, context.get("turn"))
        
        return system, user

    def _format_rule_evolution_policy(self, turn: int) -> str:
        """Describe rule-evolution guardrails for the current turn."""
        policy = self.scenario.config.rule_evolution
        # Phrased as a ceiling that is rarely reached, not as a quota. The bare
        # figure read as a target: with max_changes_per_turn: 1 the step rewrote
        # roughly one rule per unfrozen turn whether or not anything needed it,
        # which is why the statement ledger deliberately copied none of this
        # shape (see docs/ARCHITECTURE.md).
        allowance = (
            "at most one rule may change, and on most turns none should"
            if policy.max_changes_per_turn == 1
            else f"at most {policy.max_changes_per_turn} rules may change, and on most turns none should"
        )
        lines = [
            f"- Rule changes are rare. On the occasional turn where the world has "
            f"plainly outrun a rule, {allowance}.",
            "- The ceiling is not a quota. A turn that changes nothing is the normal "
            "outcome, not a failure to find something.",
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
        user = self._render(template, context, context.get("turn"))
        
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

        user = self._render(template, context, context.get("turn"))
        
        return system, user

    def build_analysis_prompt(self, analysis_context: dict[str, Any]) -> tuple[str, str]:
        """Build prompts for post-run analysis."""
        system = self._get_system_prompt("analysis")
        template = self._get_user_template("analysis")

        context = {
            "output_language": self.scenario.config.output_language,
            **analysis_context,
        }

        user = self._render(template, context, context.get("turn"))
        return system, user

    def build_synthesis_prompt(self, synthesis_context: dict[str, Any]) -> tuple[str, str]:
        """Build prompts for cross-run synthesis over an ensemble of runs."""
        system = self._get_system_prompt("synthesis")
        template = self._get_user_template("synthesis")

        context = {
            "output_language": self.scenario.config.output_language,
            **synthesis_context,
        }

        user = self._render(template, context, context.get("turn"))
        return system, user

    def build_cohort_comparison_prompt(self, comparison_context: dict[str, Any]) -> tuple[str, str]:
        """Build prompts for the stitching pass that compares cohort syntheses."""
        system = self._get_system_prompt("cohort_comparison")
        template = self._get_user_template("cohort_comparison")

        context = {
            "output_language": self.scenario.config.output_language,
            **comparison_context,
        }

        user = self._render(template, context, context.get("turn"))
        return system, user

    def build_format_fix_events_prompt(self, turn: int, previous_response: str) -> tuple[str, str]:
        """Build prompts to fix invalid events output formatting."""
        system = self._get_system_prompt("format_fix")
        template = self._get_user_template("format_fix_events")
        context = self._get_common_context(turn)
        context["previous_response"] = previous_response
        user = self._render(template, context, context.get("turn"))
        return system, user

    def build_format_fix_metrics_prompt(
        self, turn: int, previous_response: str, missing_metrics: Optional[list[str]] = None
    ) -> tuple[str, str]:
        """Build prompts to fix invalid metrics update output formatting.

        Args:
            turn: Current turn number
            previous_response: The response that could not be used
            missing_metrics: Metric ids the response omitted, if the response
                parsed but was incomplete. Rendered with the value each metric
                holds going into the turn, because a metric the Game Master
                never mentioned has no value to recover from the response
                itself.
        """
        system = self._get_system_prompt("format_fix")
        template = self._get_user_template("format_fix_metrics")
        context = self._get_common_context(turn)
        context["previous_response"] = previous_response
        context["missing_metrics"] = self._format_missing_metrics(missing_metrics or [])
        user = self._render(template, context, context.get("turn"))
        return system, user

    def _format_missing_metrics(self, missing_metrics: list[str]) -> str:
        """Render omitted metric ids as a list carrying their incoming values."""
        lines = []
        for metric_id in missing_metrics:
            metric = self.scenario.metrics.metrics.get(metric_id)
            if metric is None:
                lines.append(f"- `{metric_id}`")
            else:
                lines.append(f"- `{metric_id}` (currently {metric.value})")
        return "\n".join(lines)

    def build_constitutional_referee_prompt(
        self,
        turn: int,
        previous_metrics: dict,
        new_metrics: dict,
        narrative: str,
        notepad: Optional[str] = None,
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

        # The referee judges constraints that may depend on what has already
        # happened ("once a procedural step has occurred"). Without the notepad it
        # sees only this turn's delta and cannot judge such a constraint at all.
        context = {
            "turn": turn,
            "time_period": time_period,
            "previous_metrics_json": json.dumps(previous_metrics, indent=2, ensure_ascii=False),
            "new_metrics_json": json.dumps(new_metrics, indent=2, ensure_ascii=False),
            "narrative": narrative,
            # The notepad for the turn under judgement, which includes anything
            # this turn added. Falling back to scenario state would show the
            # referee the *previous* turn's record, because scenario.notepad is
            # only updated after this step.
            "notepad": (notepad if notepad is not None else self.scenario.notepad).strip() or "(Empty)",
        }

        user = self._render(template, context, context.get("turn"))

        return system, user

    def build_constitutional_correction_prompt(
        self,
        turn: int,
        previous_metrics: dict,
        new_metrics: dict,
        narrative: str,
        violations: str,
        notepad: Optional[str] = None,
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
            "notepad": (notepad if notepad is not None else self.scenario.notepad).strip() or "(Empty)",
            "output_language": self.scenario.config.output_language,
        }

        user = self._render(template, context, context.get("turn"))

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
        """Format available events for the events prompt.

        Events carrying an `Eligible:` gate that evaluates false against the
        current metrics are left out entirely: the model cannot list what it is
        not shown, so deterministic thresholds never depend on prose discipline.
        """
        from .validator import eval_boolean_expression

        lines = []
        for event in self.scenario.events:
            # Skip already-occurred non-repeatable events
            if event.occurred and not event.can_repeat:
                continue

            if event.eligible:
                try:
                    if not eval_boolean_expression(event.eligible, build_expression_env(self.scenario)):
                        continue
                except (NameError, ValueError, TypeError, SyntaxError) as exc:
                    # A broken expression must not silently hide an event; show
                    # it and let validation surface the defect.
                    print(
                        f"  Warning: Eligibility expression for '{event.id}' "
                        f"could not be evaluated ({exc}); event shown regardless."
                    )

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
