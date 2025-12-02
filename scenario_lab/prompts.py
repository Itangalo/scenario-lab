"""Prompt construction from templates and scenario data."""

from pathlib import Path
from typing import Optional
from .models import Scenario, Actor
import json


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class PromptBuilder:
    """Constructs prompts from templates and scenario data."""

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self._load_templates()

    def _load_templates(self):
        """Load all prompt templates."""
        system_dir = PROMPTS_DIR / "system"
        self.templates = {
            "events_system": (system_dir / "events.md").read_text(encoding="utf-8"),
            "actor_system": (system_dir / "actor.md").read_text(encoding="utf-8"),
            "rules_system": (system_dir / "metric-rules.md").read_text(encoding="utf-8"),
            "metrics_system": (system_dir / "metrics-update.md").read_text(encoding="utf-8"),
        }

    def build_events_prompt(self, turn: int) -> tuple[str, str]:
        """Build system and user prompts for events step.

        Returns:
            (system_prompt, user_prompt)
        """
        time_period = self._get_time_period(turn)

        # System prompt uses template as-is for now
        system = self.templates["events_system"]

        # Build user prompt
        user_parts = [
            f"Det är nu runda {turn} som omfattar {time_period}.",
            "",
        ]

        # Add metrics history context
        if turn == 1:
            user_parts.append("Detta är första rundan, så det finns ingen tidigare historik. Nuvarande metrics ser ut så här:")
        else:
            user_parts.append("Nuvarande metrics ser ut så här:")

        user_parts.append("")
        user_parts.append("```json")
        user_parts.append(self.scenario.metrics.to_json())
        user_parts.append("```")
        user_parts.append("")

        # Add world state
        user_parts.append("Världens tillstånd vid start av rundan beskrivs så här:")
        user_parts.append("")
        user_parts.append(self.scenario.world_state.narrative)
        user_parts.append("")
        user_parts.append("---")
        user_parts.append("")

        # Add events list
        user_parts.append("Listan över potentiella externa händelser ser ut så här:")
        user_parts.append("")
        user_parts.append(self._format_events_list())
        user_parts.append("")
        user_parts.append("---")
        user_parts.append("")

        # Add instruction
        user_parts.append(
            "Använd bakgrundsinformationen för att avgöra vilka externa event som kan inträffa i den här rundan. "
            "Om sannolikheten anges som en formel eller beskrivning, ska du beräkna det faktiska värdet."
        )
        user_parts.append("")
        user_parts.append(
            "Ditt svar ska vara en JSON-array med objekt för varje händelse vars villkor är uppfyllt, "
            "på det här formatet:"
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
            "Sannolikheten ska anges som ett värde mellan 0 och 1. "
            "Om ingen händelse uppfyller villkoren ska du svara med en tom array: `[]`"
        )
        user_parts.append("")
        user_parts.append("Svara *endast* med denna JSON-array, inget annat.")

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

        # System prompt uses template as-is for now
        system = self.templates["actor_system"]

        # Build user prompt
        user_parts = [
            f"Det är nu runda {turn} som omfattar {time_period}.",
            "",
        ]

        # Add metrics
        user_parts.append("Nuvarande metrics ser ut så här:")
        user_parts.append("")
        user_parts.append("```json")
        user_parts.append(self.scenario.metrics.to_json())
        user_parts.append("```")
        user_parts.append("")

        # Add world state
        user_parts.append("Världens tillstånd vid start av rundan beskrivs så här:")
        user_parts.append("")
        user_parts.append(self.scenario.world_state.narrative)
        user_parts.append("")
        user_parts.append("---")
        user_parts.append("")

        # Add triggered events if any
        if triggered_events:
            user_parts.append("Denna runda har följande externa händelser inträffat:")
            user_parts.append("")
            for event in triggered_events:
                event_obj = next((e for e in self.scenario.events if e.id == event["id"]), None)
                if event_obj:
                    user_parts.append(f"**{event_obj.id}:** {event_obj.description}")
            user_parts.append("")
        else:
            user_parts.append("Denna runda inträffar inga speciella händelser.")
            user_parts.append("")

        user_parts.append("---")
        user_parts.append("")

        # Add instruction
        user_parts.append(
            "Använd bakgrundsinformationen för att avgöra om (1) dina mål bör justeras och "
            "(2) vilka handlingar du vill utföra under rundan."
        )
        user_parts.append("")
        user_parts.append(
            "Handlingarna ska ligga i linje med dina mål och vara realistiska utifrån tid och andra resurser. "
            "Dina handlingar kommer att bedömas av en Game Master, som avgör hur de påverkar världen. "
            "Djärva åtgärder kan ha större inverkan, men också större risk att misslyckas."
        )
        user_parts.append("")
        user_parts.append("Svara med en Markdown-text som innehåller följande delar:")
        user_parts.append("")
        user_parts.append("* Rubrik nivå 2: Mål")
        user_parts.append("* Kortfattad beskrivning av dina mål i en punktlista")
        user_parts.append("* Eventuellt rubrik nivå 3: Anledning till ändringar (endast om målen ändrats)")
        user_parts.append("* Kortfattad beskrivning av varför målen ändrats (endast om målen ändrats)")
        user_parts.append("* Rubrik nivå 2: Handlingar")
        user_parts.append(
            "* Ett stycke för varje handling, som på lagom nivå beskriver varje handlingen du avser att genomföra under rundan."
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

        # System prompt uses template as-is
        system = self.templates["rules_system"]

        # Build user prompt
        user_parts = [
            f"Det är nu runda {turn} som omfattar {time_period}.",
            "",
            "Så här såg Metrics Rules ut (eventuellt uppdaterade):",
            "",
            self.scenario.metric_rules,
            "",
            "Världens tillstånd vid start av rundan beskrivs så här:",
            "",
            self.scenario.world_state.narrative,
            "",
            "---",
            "",
        ]

        # Add triggered events
        user_parts.append("Denna runda har följande externa händelser inträffat:")
        user_parts.append("")
        if triggered_events:
            for event in triggered_events:
                event_obj = next((e for e in self.scenario.events if e.id == event["id"]), None)
                if event_obj:
                    user_parts.append(f"**{event_obj.id}:** {event_obj.description}")
        else:
            user_parts.append("Inga")
        user_parts.append("")
        user_parts.append("---")
        user_parts.append("")

        # Add actor actions
        user_parts.append("Aktörerna i scenariot beskriver sina handlingar så här:")
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
            "Använd den här informationen för att bedöma om Metric Rules bör uppdateras baserat på "
            "vad som hänt i världen och vad aktörerna gjort."
        )
        user_parts.append("")
        user_parts.append("Svara med en uppdaterad lista av Metric Rules i samma format som tidigare.")

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

        # System prompt uses template as-is
        system = self.templates["metrics_system"]

        # Build user prompt
        user_parts = [
            f"Det är nu runda {turn} som omfattar {time_period}.",
            "",
            "Så här såg Metrics Rules ut (eventuellt uppdaterade):",
            "",
            self.scenario.metric_rules,
            "",
            "Världens tillstånd vid start av rundan beskrivs så här:",
            "",
            self.scenario.world_state.narrative,
            "",
            "---",
            "",
        ]

        # Add triggered events
        user_parts.append("Denna runda har följande externa händelser inträffat:")
        user_parts.append("")
        if triggered_events:
            for event in triggered_events:
                event_obj = next((e for e in self.scenario.events if e.id == event["id"]), None)
                if event_obj:
                    user_parts.append(f"**{event_obj.id}:** {event_obj.description}")
        else:
            user_parts.append("Inga")
        user_parts.append("")
        user_parts.append("---")
        user_parts.append("")

        # Add actor actions
        user_parts.append("Aktörerna i scenariot beskriver sina handlingar så här:")
        user_parts.append("")
        for actor_id, actions in actor_actions.items():
            actor = self.scenario.actors[actor_id]
            user_parts.append(f"**{actor.name}:**")
            user_parts.append("")
            user_parts.append(actions)
            user_parts.append("")

        user_parts.append("---")
        user_parts.append("")
        user_parts.append("Använd den här informationen för att göra följande:")
        user_parts.append("")
        user_parts.append(
            "* Avgöra hur framgångsrika aktörerna är med sina handlingar. "
            "Detta baseras hur världen ser ut samt din bedömning av hur sannolikt det är att de lyckas."
        )
        user_parts.append("* Utgå från aktörernas handlingar och Metric Rules för att bestämma Metrics inför nästa runda.")
        user_parts.append("* Skriva en sammanhängande berättelse som berättar vad som händer i världen under den här rundan.")
        user_parts.append("")
        user_parts.append("Svara med en Markdown-text med följande innehåll:")
        user_parts.append("")
        user_parts.append("* Rubrik nivå 2: Metrics")
        user_parts.append('* Ett JSON-objekt som beskriver samtliga metrics, i följande format: `{"metric1_name": value1, "metric2_name": value2}`')
        user_parts.append("* Rubrik nivå 2: Narrativ")
        user_parts.append("* En sammanhängande berättelse om vad som händer i världen under rundan (max 400 ord). Du kan använda underrubriker (nivå 3) om du önskar.")

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
            lines.append(f"- Villkor: {event.condition}")
            lines.append(f"- Sannolikhet: {event.probability}")
            lines.append(f"- Kan upprepas: {'Ja' if event.can_repeat else 'Nej'}")
            lines.append(f"- Beskrivning: {event.description}")
            lines.append("")

        return "\n".join(lines)

    def _get_time_period(self, turn: int) -> str:
        """Get time period string for turn."""
        from .loader import get_time_period

        return get_time_period(
            self.scenario.config.start_date, turn, self.scenario.config.time_scale
        )
