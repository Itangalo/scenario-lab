"""Orchestrator for executing simulation turns."""

import random
import json
from typing import Protocol
from .models import Scenario, TurnResult, WorldState
from .prompts import PromptBuilder
from .llm import LLMResponse


class LLMClientProtocol(Protocol):
    """Protocol for LLM clients (real or mock)."""

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        ...

    def close(self):
        ...


class Orchestrator:
    """Executes the simulation turn loop."""

    def __init__(self, scenario: Scenario, llm_client: LLMClientProtocol):
        self.scenario = scenario
        self.llm = llm_client
        self.prompt_builder = PromptBuilder(scenario)

    def run_turn(self, turn: int) -> TurnResult:
        """Execute one complete turn.

        Args:
            turn: Turn number (1-indexed)

        Returns:
            TurnResult with all outputs from the turn
        """
        from .loader import get_time_period

        time_period = get_time_period(
            self.scenario.config.start_date, turn, self.scenario.config.time_scale
        )

        print(f"\n{'='*60}")
        print(f"TURN {turn}: {time_period}")
        print(f"{'='*60}")

        # Step 1: Determine events
        print("\n[1/4] Determining external events...")
        triggered_events = self._run_events_step(turn)
        print(f"  → {len(triggered_events)} events triggered")

        # Step 2: Get actor actions
        print("\n[2/4] Getting actor actions...")
        actor_outputs = self._run_actors_step(turn, triggered_events)
        print(f"  → {len(actor_outputs)} actors responded")

        # Step 3: Update metric rules
        print("\n[3/4] Updating metric rules...")
        new_rules = self._run_rules_step(turn, actor_outputs, triggered_events)
        self.scenario.metric_rules = new_rules
        print(f"  → Rules updated")

        # Step 4: Update metrics and generate narrative
        print("\n[4/4] Updating metrics and generating narrative...")
        new_metrics, narrative = self._run_metrics_step(turn, actor_outputs, triggered_events)
        print(f"  → Metrics and narrative updated")

        # Update scenario state
        self._update_scenario_state(new_metrics, narrative, turn, time_period)

        # Build and return result
        return TurnResult(
            turn=turn,
            time_period=time_period,
            triggered_events=triggered_events,
            actor_outputs=actor_outputs,
            metric_rules=new_rules,
            metrics=new_metrics,
            narrative=narrative,
        )

    def _run_events_step(self, turn: int) -> list[dict]:
        """Step 1: Determine which events occur.

        Returns:
            List of triggered events with their probabilities
        """
        system, user = self.prompt_builder.build_events_prompt(turn)
        response = self.llm.complete(system, user)

        try:
            # Parse LLM response: list of events with probabilities
            candidate_events = response.extract_json_array()
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  Warning: Could not parse events response: {e}")
            print(f"  Response was: {response.content[:200]}...")
            return []

        # Validate and roll dice for each event
        triggered = []
        for event_data in candidate_events:
            if "id" not in event_data or "probability" not in event_data:
                print(f"  Warning: Skipping invalid event data: {event_data}")
                continue

            event_id = event_data["id"]
            probability = event_data["probability"]

            # Validate event exists
            event_obj = next((e for e in self.scenario.events if e.id == event_id), None)
            if not event_obj:
                print(f"  Warning: Unknown event '{event_id}', skipping")
                continue

            # Validate probability
            if not isinstance(probability, (int, float)) or not 0 <= probability <= 1:
                print(f"  Warning: Invalid probability {probability} for {event_id}, skipping")
                continue

            # Roll dice
            if random.random() < probability:
                triggered.append(event_data)
                print(f"  ✓ Event triggered: {event_id} (p={probability:.2%})")

                # Mark non-repeatable events as occurred
                if not event_obj.can_repeat:
                    self._mark_event_occurred(event_id)
            else:
                print(f"    Event not triggered: {event_id} (p={probability:.2%})")

        return triggered

    def _run_actors_step(self, turn: int, triggered_events: list[dict]) -> dict[str, str]:
        """Step 2: Get actions from each actor.

        Args:
            turn: Current turn number
            triggered_events: List of events that occurred

        Returns:
            Dict mapping actor_id to their markdown output
        """
        outputs = {}

        for actor_id in self.scenario.actors:
            actor = self.scenario.actors[actor_id]
            print(f"  → {actor.name}...")

            system, user = self.prompt_builder.build_actor_prompt(actor_id, turn, triggered_events)
            response = self.llm.complete(system, user)
            outputs[actor_id] = response.content

            # Update actor's last actions in scenario
            self.scenario.actors[actor_id].last_actions = response.content

        return outputs

    def _run_rules_step(
        self, turn: int, actor_outputs: dict[str, str], triggered_events: list[dict]
    ) -> str:
        """Step 3: Update metric rules.

        Args:
            turn: Current turn number
            actor_outputs: Dict of actor outputs
            triggered_events: List of events that occurred

        Returns:
            Updated metric rules as markdown
        """
        system, user = self.prompt_builder.build_rules_prompt(turn, actor_outputs, triggered_events)
        response = self.llm.complete(system, user)
        return response.content

    def _run_metrics_step(
        self, turn: int, actor_outputs: dict[str, str], triggered_events: list[dict]
    ) -> tuple[dict, str]:
        """Step 4: Update metrics and generate narrative.

        Args:
            turn: Current turn number
            actor_outputs: Dict of actor outputs
            triggered_events: List of events that occurred

        Returns:
            Tuple of (metrics dict, narrative string)
        """
        system, user = self.prompt_builder.build_metrics_prompt(
            turn, actor_outputs, triggered_events
        )
        response = self.llm.complete(system, user)

        try:
            metrics, narrative = response.extract_metrics_and_narrative()
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  Warning: Could not parse metrics response: {e}")
            print(f"  Response was: {response.content[:200]}...")

            # Return previous metrics with error narrative
            current_metrics = {m.id: m.value for m in self.scenario.metrics.metrics.values()}
            error_narrative = (
                "[ERROR: Could not parse metrics response. Keeping previous values.]\n\n"
                + response.content
            )
            return current_metrics, error_narrative

        # Validate and clamp metrics
        for metric_id, value in list(metrics.items()):
            if metric_id in self.scenario.metrics.metrics:
                metric = self.scenario.metrics.metrics[metric_id]
                if not isinstance(value, (int, float)):
                    print(f"  Warning: Invalid value type for {metric_id}: {type(value)}")
                    metrics[metric_id] = metric.value  # Keep previous
                elif not metric.min_value <= value <= metric.max_value:
                    print(
                        f"  Warning: Value {value} out of bounds for {metric_id} "
                        f"({metric.min_value}-{metric.max_value}), clamping"
                    )
                    metrics[metric_id] = max(metric.min_value, min(metric.max_value, value))
            else:
                print(f"  Warning: Unknown metric '{metric_id}' in response, skipping")
                del metrics[metric_id]

        return metrics, narrative

    def _mark_event_occurred(self, event_id: str):
        """Mark event as occurred (for non-repeatable events)."""
        for event in self.scenario.events:
            if event.id == event_id and not event.can_repeat:
                event.occurred = True
                self.scenario.occurred_events.add(event_id)

    def _update_scenario_state(
        self, new_metrics: dict, narrative: str, turn: int, time_period: str
    ):
        """Update scenario with turn results."""
        self.scenario.metrics.update_from_dict(new_metrics)
        self.scenario.world_state.narrative = narrative
        self.scenario.world_state.turn = turn
        self.scenario.world_state.time_period = time_period


def run_simulation(
    scenario: Scenario, llm_client: LLMClientProtocol, num_turns: int = None
) -> list[TurnResult]:
    """Run a complete simulation.

    Args:
        scenario: Loaded scenario
        llm_client: LLM client (real or mock)
        num_turns: Number of turns to run (default: from config)

    Returns:
        List of TurnResults
    """
    orchestrator = Orchestrator(scenario, llm_client)
    max_turns = num_turns or scenario.config.max_turns
    results = []

    for turn in range(1, max_turns + 1):
        result = orchestrator.run_turn(turn)
        results.append(result)
        scenario.turn_history.append(result)

    return results
