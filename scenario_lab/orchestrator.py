"""Orchestrator for executing simulation turns."""

import json
import random
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Protocol, Optional, Union, TYPE_CHECKING
from .models import Scenario, TurnResult, WorldState, ModelRoute
from .prompts import PromptBuilder
from .llm import LLMResponse, LLMParseError, LLMError, LLMUnsupportedStructuredError
from .router import FallbackRouter
from .providers.registry import ProviderRegistry

if TYPE_CHECKING:
    from .output import OutputManager


class LLMClientProtocol(Protocol):
    """Protocol for LLM clients (real or mock)."""

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        ...

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        schema_name: str,
    ) -> LLMResponse:
        ...

    def close(self):
        ...


class _RecordingClient:
    """Thin wrapper around an LLM client that records each call as a transcript.

    It defers all behavior to the wrapped client and, after each ``complete``
    call, asks the orchestrator to persist the prompt/response transcript. The
    task name and turn are resolved from the orchestrator's thread-local call
    context, which lets a single shared client (for example a router reused by
    several actors running in parallel) still log the correct task name.
    """

    def __init__(self, inner: "LLMClientProtocol", orchestrator: "Orchestrator"):
        self._inner = inner
        self._orchestrator = orchestrator
        # Expose ``models`` if the inner client has it (used by reuse logic/tests).
        self.models = getattr(inner, "models", None)

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        response = self._inner.complete(system_prompt, user_prompt)
        # Buffer the call so the orchestrator can persist it from the single
        # `_record_llm_call` point, which knows the turn and task name.
        self._orchestrator._buffer_llm_io(system_prompt, user_prompt, response)
        return response

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: dict,
        schema_name: str,
    ) -> LLMResponse:
        response = self._inner.complete_structured(
            system_prompt, user_prompt, schema, schema_name
        )
        # Structured calls are buffered and persisted the same way as text calls.
        self._orchestrator._buffer_llm_io(system_prompt, user_prompt, response)
        return response

    def close(self) -> None:
        # The underlying client/router is owned and closed elsewhere.
        pass


class Orchestrator:
    """Executes the simulation turn loop with per-task LLM selection."""

    def __init__(
        self,
        scenario: Scenario,
        llm_client: Optional[Union[LLMClientProtocol, dict[str, LLMClientProtocol]]] = None,
        output_manager: Optional["OutputManager"] = None,
        progress_tracker: Optional["ProgressTracker"] = None,
    ):
        """Initialize orchestrator.

        Args:
            scenario: The scenario to run
            llm_client: Either:
                - Single LLM client (uses same for all tasks, backward compatible)
                - Dict of clients {"events": client, "actors": {...}, "rules": client, "metrics": client}
                - None (creates clients based on scenario.config.llm)
            output_manager: Optional OutputManager for incremental writing
            progress_tracker: Optional ProgressTracker for progress display
        """
        self.scenario = scenario
        self.prompt_builder = PromptBuilder(scenario)
        self.output_manager = output_manager
        self.progress_tracker = progress_tracker
        self._owned_routers: list[FallbackRouter] = []

        # Resolve the random seed for the dice RNG. If unset, generate a
        # 64-bit seed so that every run records a concrete, reproducible seed.
        if self.scenario.config.random_seed is None:
            self.scenario.config.random_seed = random.getrandbits(64)
        self.random_seed: int = self.scenario.config.random_seed

        # Structured-output state for the events step. In "auto" mode, once the
        # events model rejects structured output we stop retrying it for the run.
        self._structured_events_mode: str = self.scenario.config.llm.structured_outputs
        self._structured_events_unsupported: bool = False

        # LLM I/O transcript logging state.
        self._log_llm_io: bool = bool(self.scenario.config.logging.llm_io)
        self._llm_io_context = threading.local()
        self._llm_io_lock = threading.Lock()
        self._llm_io_sequences: dict[int, int] = {}

        # Initialize cost tracking
        from .cost import CostTracker
        self.cost_tracker = CostTracker()

        # Setup LLM routers
        if llm_client is None:
            self.llm_clients = self._create_routers_from_config()
        elif isinstance(llm_client, dict):
            self.llm_clients = llm_client
        else:
            # Single client/router for all tasks (backward compatible with MockLLMClient)
            self.llm_clients = {
                "events": llm_client,
                "actors": {},
                "rules": llm_client,
                "metrics": llm_client,
                "summary": llm_client,
                "referee": llm_client,
            }

        # Wrap clients for transcript logging if enabled.
        if self._log_llm_io and self.output_manager is not None:
            self.llm_clients = self._wrap_clients_for_io(self.llm_clients)

    @staticmethod
    def _primary_route_key(routes: "ModelRoute | list[ModelRoute]") -> str:
        """Return the string key for the primary route, used for reuse deduplication."""
        primary = routes[0] if isinstance(routes, list) else routes
        return str(primary)

    @staticmethod
    def _routes_match(
        a: "ModelRoute | list[ModelRoute]",
        b: "ModelRoute | list[ModelRoute]",
    ) -> bool:
        """True if both route specs share the same primary route."""
        return Orchestrator._primary_route_key(a) == Orchestrator._primary_route_key(b)

    def _make_router(
        self,
        routes: "ModelRoute | list[ModelRoute]",
        registry: ProviderRegistry,
        temperature: float,
        max_tokens: int,
    ) -> FallbackRouter:
        """Build a FallbackRouter and register it for cleanup."""
        route_list = routes if isinstance(routes, list) else [routes]
        router = FallbackRouter(
            routes=route_list,
            registry=registry,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._owned_routers.append(router)
        return router

    def _create_routers_from_config(self) -> dict:
        """Create FallbackRouters based on scenario configuration."""
        config = self.scenario.config.llm
        registry = ProviderRegistry(call_timeout_seconds=config.call_timeout_seconds)

        router_cache: dict[str, FallbackRouter] = {}

        def get_or_create(
            routes: "ModelRoute | list[ModelRoute]",
            temperature: float,
            max_tokens: int,
        ) -> FallbackRouter:
            key = self._primary_route_key(routes)
            if key in router_cache:
                return router_cache[key]
            router = self._make_router(routes, registry, temperature, max_tokens)
            router_cache[key] = router
            return router

        events_router = get_or_create(
            config.events, config.temperature, config.get_task_max_tokens("events")
        )

        actor_routers: dict[str, FallbackRouter] = {}
        for actor_id in self.scenario.config.actor_ids:
            routes = config.get_actor_routes(actor_id)
            actor_routers[actor_id] = get_or_create(
                routes, config.temperature, config.get_task_max_tokens("actors")
            )

        rules_router = get_or_create(
            config.rules, config.temperature, config.get_task_max_tokens("rules")
        )
        metrics_router = get_or_create(
            config.metrics, config.temperature, config.get_task_max_tokens("metrics")
        )
        summary_router = get_or_create(
            config.summary, 0.3, config.get_task_max_tokens("summary")
        )
        referee_router = get_or_create(
            config.referee, 0.3, config.get_task_max_tokens("referee", default=1000)
        )

        return {
            "events": events_router,
            "actors": actor_routers,
            "rules": rules_router,
            "metrics": metrics_router,
            "summary": summary_router,
            "referee": referee_router,
        }

    def close(self):
        """Close all owned routers (and their underlying providers via registry)."""
        for router in self._owned_routers:
            router.close()

    def _wrap_clients_for_io(self, clients: dict) -> dict:
        """Wrap every per-task client in a recording wrapper for transcripts."""
        wrapped: dict = {}
        for task, value in clients.items():
            if isinstance(value, dict):
                wrapped[task] = {
                    actor_id: _RecordingClient(client, self)
                    for actor_id, client in value.items()
                }
            elif value is None:
                wrapped[task] = value
            else:
                wrapped[task] = _RecordingClient(value, self)
        return wrapped

    def _buffer_llm_io(
        self, system_prompt: str, user_prompt: str, response: LLMResponse
    ) -> None:
        """Stash the latest LLM call on the current thread for later persistence."""
        self._llm_io_context.pending = (system_prompt, user_prompt, response)

    def _next_llm_io_sequence(self, turn: int) -> int:
        """Return the next per-turn sequence number for transcript files."""
        with self._llm_io_lock:
            seq = self._llm_io_sequences.get(turn, 0) + 1
            self._llm_io_sequences[turn] = seq
            return seq

    def _record_llm_call(self, turn: int, task_name: str, response: LLMResponse):
        """Record token usage and cost from an LLM call.

        When LLM I/O logging is enabled, this is also the single point where the
        prompt/response transcript is persisted, using the call buffered by the
        recording client wrapper on this thread.

        Args:
            turn: Turn number
            task_name: Task identifier (e.g., "events", "actor:government", "rules")
            response: LLM response with usage data
        """
        from .cost import CostCalculator

        usage = response.get_usage()
        cost_details = None
        if usage:
            cost_details = CostCalculator.calculate_cost(usage)
            self.cost_tracker.record_call(turn, task_name, cost_details)

        if self._log_llm_io and self.output_manager is not None:
            self._persist_llm_io(turn, task_name, response, usage, cost_details)

    def _persist_llm_io(
        self,
        turn: int,
        task_name: str,
        response: LLMResponse,
        usage,
        cost_details,
    ) -> None:
        """Write the buffered transcript for the current call, if any."""
        pending = getattr(self._llm_io_context, "pending", None)
        if pending is None:
            return
        system_prompt, user_prompt, buffered_response = pending
        self._llm_io_context.pending = None

        # Guard against a stale buffer from an unrelated call.
        if buffered_response is not response:
            return

        record = {
            "task": task_name,
            "model": usage.model if usage else response.raw_response.get("model", "unknown"),
            "system": system_prompt,
            "user": user_prompt,
            "response": response.content,
            "prompt_tokens": usage.prompt_tokens if usage else None,
            "completion_tokens": usage.completion_tokens if usage else None,
            "total_tokens": usage.total_tokens if usage else None,
            "cost_usd": round(cost_details.total_cost_usd, 6) if cost_details else None,
        }
        sequence = self._next_llm_io_sequence(turn)
        self.output_manager.save_llm_io(turn, sequence, task_name, record)

    def get_run_costs(self):
        """Get complete cost summary for this run.

        Returns:
            RunCosts object with all cost aggregations
        """
        return self.cost_tracker.get_run_costs()

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

        # Start turn tracking
        if self.progress_tracker:
            self.progress_tracker.start_turn(turn, time_period)
        else:
            print(f"\n{'='*60}")
            print(f"TURN {turn}: {time_period}")
            print(f"{'='*60}")

        # Step 1: Determine events
        if self.progress_tracker:
            with self.progress_tracker.start_step(1, "") as step:
                triggered_events = self._run_events_step(turn)
                step.update(f"{len(triggered_events)} events triggered")
        else:
            print("\n[1/5] Determining external events...")
            triggered_events = self._run_events_step(turn)
            print(f"  → {len(triggered_events)} events triggered")

        if self.output_manager:
            self.output_manager.save_events(turn, triggered_events)

        # Step 2: Get actor actions
        if self.progress_tracker:
            with self.progress_tracker.start_step(2, "") as step:
                actor_outputs = self._run_actors_step(turn, triggered_events)
                step.update(f"{len(actor_outputs)} actors responded")
        else:
            print("\n[2/5] Getting actor actions...")
            actor_outputs = self._run_actors_step(turn, triggered_events)
            print(f"  → {len(actor_outputs)} actors responded")

        # Step 3: Update metric rules
        if self.progress_tracker:
            with self.progress_tracker.start_step(3, "") as step:
                new_rules = self._run_rules_step(turn, actor_outputs, triggered_events)
                self.scenario.metric_rules = new_rules
                step.update("Rules updated")
        else:
            print("\n[3/5] Updating metric rules...")
            new_rules = self._run_rules_step(turn, actor_outputs, triggered_events)
            self.scenario.metric_rules = new_rules
            print(f"  → Rules updated")

        if self.output_manager:
            self.output_manager.save_metric_rules(turn, new_rules)

        # Step 4: Update metrics and generate narrative
        if self.progress_tracker:
            with self.progress_tracker.start_step(4, "") as step:
                new_metrics, narrative, notepad = self._run_metrics_step(turn, actor_outputs, triggered_events)
                step.update("Metrics and narrative updated")
        else:
            print("\n[4/6] Updating metrics and generating narrative...")
            new_metrics, narrative, notepad = self._run_metrics_step(turn, actor_outputs, triggered_events)
            print(f"  → Metrics and narrative updated")

        if self.output_manager:
            self.output_manager.save_metrics_and_narrative(turn, new_metrics, narrative)
            self.output_manager.save_notepad(turn, notepad)
            self.output_manager.update_summary(turn, new_metrics)

        # Step 5: Constitutional referee (optional)
        if self.scenario.constitution:
            if self.progress_tracker:
                with self.progress_tracker.start_step(5, "") as step:
                    new_metrics, narrative = self._run_constitutional_referee_step(
                        turn, new_metrics, narrative
                    )
                    step.update("Constitution validated")
            else:
                print("\n[5/6] Validating against constitutional constraints...")
                new_metrics, narrative = self._run_constitutional_referee_step(
                    turn, new_metrics, narrative
                )
                print(f"  → Constitution validated")

            # Update saved metrics/narrative if they were corrected
            if self.output_manager:
                self.output_manager.save_metrics_and_narrative(turn, new_metrics, narrative)
                self.output_manager.update_summary(turn, new_metrics)

        # Step 6: Update historical summary
        if self.progress_tracker:
            with self.progress_tracker.start_step(6, "") as step:
                new_historical_summary = self._run_summarization_step(turn, narrative)
                step.update("Summary updated")
        else:
            step_num = "6/6" if self.scenario.constitution else "5/5"
            print(f"\n[{step_num}] Updating historical summary...")
            new_historical_summary = self._run_summarization_step(turn, narrative)
            print(f"  → Summary updated")

        if self.output_manager:
            self.output_manager.save_historical_summary(turn, new_historical_summary)

        # Update scenario state
        self._update_scenario_state(new_metrics, narrative, new_historical_summary, notepad, turn, time_period)

        # Display turn costs
        turn_costs = self.cost_tracker.get_turn_costs(turn)
        if turn_costs:
            if self.progress_tracker:
                self.progress_tracker.complete_turn(turn, turn_costs.total_cost_usd, turn_costs.total_tokens)
            else:
                print(f"\n💰 Turn {turn} cost: ${turn_costs.total_cost_usd:.4f} ({turn_costs.total_tokens:,} tokens)")

        # Build and return result
        return TurnResult(
            turn=turn,
            time_period=time_period,
            triggered_events=triggered_events,
            actor_outputs=actor_outputs,
            metric_rules=new_rules,
            metrics=new_metrics,
            narrative=narrative,
            notepad=notepad,
        )

    def _event_roll(self, turn: int, event_id: str) -> float:
        """Return a deterministic dice roll in [0, 1) for one event this turn.

        The roll is derived from the run seed, turn, and event id, so it is
        stable given the seed and independent of call order. This lets resume
        and branch reproduce identical rolls without persisting RNG state.
        """
        return random.Random(f"{self.random_seed}:{turn}:{event_id}").random()

    def _event_override_for_turn(self, turn: int):
        """Return the EventOverrides scoped to this turn, if any."""
        overrides = self.scenario.config.event_overrides
        if overrides is not None and overrides.turn == turn:
            return overrides
        return None

    def _run_events_step(self, turn: int) -> list[dict]:
        """Step 1: Determine which events occur.

        Returns:
            List of triggered events with their probabilities
        """
        triggered, evaluations = self._evaluate_events(turn)
        if self.output_manager:
            self.output_manager.save_event_evaluations(turn, evaluations)
        return triggered

    def _fetch_candidate_events(
        self, turn: int, system: str, user: str
    ) -> Optional[list]:
        """Get the candidate-event list from the LLM for one turn.

        Tries the provider-native structured path when ``llm.structured_outputs``
        is active ("true", or "auto" while the model is not known-unsupported),
        otherwise uses the legacy text path (extract_json_array + one format-fix
        retry).

        Returns:
            The candidate list, or None when the legacy path ends in an
            unrecoverable parse failure (caller records the parse-failure
            marker and proceeds with zero events).
        """
        mode = self._structured_events_mode
        try_structured = mode == "true" or (
            mode == "auto" and not self._structured_events_unsupported
        )

        if try_structured:
            from .schemas import EVENTS_SCHEMA_NAME, events_array_schema

            schema = events_array_schema(
                emergent=self.scenario.config.emergent_events.enabled
            )
            try:
                response = self.llm_clients["events"].complete_structured(
                    system, user, schema, EVENTS_SCHEMA_NAME
                )
            except (LLMUnsupportedStructuredError, AttributeError, NotImplementedError) as e:
                # AttributeError/NotImplementedError cover injected clients that
                # predate complete_structured – treat them as unsupported too.
                if mode == "true":
                    raise LLMError(
                        "llm.structured_outputs is 'true' but the events model "
                        f"does not support structured output: {e}"
                    ) from e
                self._structured_events_unsupported = True
                print(
                    "  Info: Events model does not support structured outputs; "
                    "using legacy JSON parsing for the rest of this run."
                )
            else:
                self._record_llm_call(turn, "events", response)
                data = response.structured_data
                if isinstance(data, list):
                    # Per-event validation downstream handles bad items.
                    return data
                # Defensive: a strict schema should guarantee a list. Treat
                # anything else like a parse failure of the structured path.
                if mode == "true":
                    raise LLMError(
                        "Structured events response was not a JSON array "
                        f"(got {type(data).__name__})."
                    )
                print(
                    "  Warning: Structured events response was not a JSON array; "
                    "falling back to legacy parsing."
                )

        # Legacy text path: parse, then one format-fix retry.
        response = self.llm_clients["events"].complete(system, user)
        self._record_llm_call(turn, "events", response)

        try:
            return response.extract_json_array()
        except (json.JSONDecodeError, ValueError, LLMParseError) as e:
            print(f"  Warning: Could not parse events response: {e}")
            print(f"  Response was: {response.content[:200]}...")

            # Retry once with format-fix prompt
            try:
                fix_system, fix_user = self.prompt_builder.build_format_fix_events_prompt(
                    turn, response.content
                )
                fix_response = self.llm_clients["events"].complete(fix_system, fix_user)
                self._record_llm_call(turn, "events:format_fix", fix_response)
                candidate_events = fix_response.extract_json_array()
                print("  ✓ Events format fixed on retry")
                return candidate_events
            except Exception as fix_e:
                print(f"  Warning: Events format-fix retry failed: {fix_e}")
                return None

    def _evaluate_events(self, turn: int) -> tuple[list[dict], list[dict]]:
        """Evaluate candidate events and roll the seeded dice.

        With ``llm.probability_samples > 1``, the candidate list is elicited
        multiple times and per-event probabilities are aggregated (mean with
        absent-as-zero over valid samples) before the single dice roll.

        Returns:
            Tuple of (triggered_events, evaluations). ``triggered_events`` keeps
            the legacy shape (the raw LLM event dicts) for 1-events.json.
            ``evaluations`` is the full per-event record for
            1-event-evaluations.json.
        """
        system, user = self.prompt_builder.build_events_prompt(turn)

        n_samples = self.scenario.config.llm.probability_samples
        samples: list[list] = []
        for _ in range(n_samples):
            candidates = self._fetch_candidate_events(turn, system, user)
            if candidates is not None:
                samples.append(candidates)

        if not samples:
            # Every elicitation ended in an unrecoverable parse failure. Make
            # the silent-bias case visible in the artifact so a parse failure
            # cannot be mistaken for "no events this turn".
            print(
                "  Warning: Events step ended with zero events due to a parse "
                "failure (recorded in event-evaluations artifact)."
            )
            return [], [{"parse_failure": True, "triggered": False}]

        sample_skipped: list[dict] = []
        if n_samples == 1:
            candidate_events = samples[0]
        else:
            if len(samples) < n_samples:
                print(
                    f"  Warning: Only {len(samples)}/{n_samples} event samples "
                    "were usable; aggregating over the valid ones."
                )
            candidate_events, sample_skipped = self._aggregate_event_samples(samples)

        override = self._event_override_for_turn(turn)
        force_ids = set(override.force) if override else set()
        suppress_ids = set(override.suppress) if override else set()

        triggered: list[dict] = []
        evaluations: list[dict] = list(sample_skipped)

        emergent_cfg = self.scenario.config.emergent_events
        emergent_accepted = 0

        for event_data in candidate_events:
            if not isinstance(event_data, dict) or "id" not in event_data or "probability" not in event_data:
                print(f"  Warning: Skipping invalid event data: {event_data}")
                evaluations.append(
                    {
                        "id": event_data.get("id") if isinstance(event_data, dict) else None,
                        "skipped": "Invalid event data (missing id or probability)",
                        "triggered": False,
                    }
                )
                continue

            event_id = event_data["id"]
            probability = event_data["probability"]

            # Classify: listed event, emergent proposal, or unknown.
            event_obj = next((e for e in self.scenario.events if e.id == event_id), None)
            is_emergent = event_obj is None and bool(event_data.get("emergent"))

            if event_obj is None and not is_emergent:
                print(f"  Warning: Unknown event '{event_id}', skipping")
                evaluation = {key: value for key, value in event_data.items()}
                evaluation["skipped"] = f"Unknown event '{event_id}'"
                evaluation["triggered"] = False
                evaluations.append(evaluation)
                continue

            if event_obj is not None:
                # Keep artifacts tidy: drop the extended-contract filler fields
                # that listed events carry when emergent events are enabled.
                if not event_data.get("emergent"):
                    event_data.pop("emergent", None)
                if event_data.get("description") == "":
                    event_data.pop("description", None)

            if is_emergent:
                skip_reason = None
                description = event_data.get("description")
                if not emergent_cfg.enabled:
                    skip_reason = "Emergent events are disabled for this scenario"
                elif not isinstance(description, str) or not description.strip():
                    skip_reason = "Emergent event missing description"
                if skip_reason:
                    print(f"  Warning: Skipping emergent event '{event_id}': {skip_reason}")
                    evaluation = {key: value for key, value in event_data.items()}
                    evaluation["skipped"] = skip_reason
                    evaluation["triggered"] = False
                    evaluations.append(evaluation)
                    continue

            # Validate probability
            if not isinstance(probability, (int, float)) or not 0 <= probability <= 1:
                print(f"  Warning: Invalid probability {probability} for {event_id}, skipping")
                evaluation = {key: value for key, value in event_data.items()}
                evaluation["skipped"] = f"Invalid probability {probability}"
                evaluation["triggered"] = False
                evaluations.append(evaluation)
                continue

            if is_emergent:
                if emergent_accepted >= emergent_cfg.max_per_turn:
                    print(
                        f"  Warning: Skipping emergent event '{event_id}': "
                        f"exceeds emergent_events.max_per_turn ({emergent_cfg.max_per_turn})"
                    )
                    evaluation = {key: value for key, value in event_data.items()}
                    evaluation["skipped"] = (
                        f"Exceeds emergent_events.max_per_turn ({emergent_cfg.max_per_turn})"
                    )
                    evaluation["triggered"] = False
                    evaluations.append(evaluation)
                    continue

                # Normalize the id so emergent events are recognizable in all
                # artifacts and cannot collide with listed event ids.
                if not event_id.startswith("emergent_"):
                    event_data["id_normalized_from"] = event_id
                    event_id = f"emergent_{event_id}"
                    event_data["id"] = event_id

                # Guardrail: cap the proposed probability at the scenario policy.
                if probability > emergent_cfg.max_probability:
                    event_data["probability_capped_from"] = probability
                    probability = emergent_cfg.max_probability
                    event_data["probability"] = probability

                event_data["emergent"] = True
                emergent_accepted += 1

            roll = self._event_roll(turn, event_id)

            # Start the evaluation record with any extra fields the LLM returned.
            evaluation = {key: value for key, value in event_data.items()}
            evaluation["probability"] = probability
            evaluation["roll"] = roll

            forced = event_id in force_ids
            suppressed = event_id in suppress_ids

            if forced and suppressed:
                # Suppression wins over forcing to keep behavior unambiguous.
                forced = False

            if suppressed:
                is_triggered = False
                evaluation["suppressed"] = True
            elif forced:
                is_triggered = True
                evaluation["forced"] = True
            else:
                is_triggered = roll < probability

            evaluation["triggered"] = is_triggered

            if is_triggered:
                triggered.append(event_data)
                label = f"{event_id} (emergent)" if is_emergent else event_id
                if forced:
                    print(f"  ✓ Event triggered (forced): {label} (p={probability:.2%})")
                else:
                    print(f"  ✓ Event triggered: {label} (p={probability:.2%}, roll={roll:.2f})")

                if is_emergent:
                    # Emergent events are one-off by definition; record them so
                    # summary.json preserves the full occurred-events history.
                    self.scenario.occurred_events.add(event_id)
                elif not event_obj.can_repeat:
                    # Mark non-repeatable events as occurred
                    self._mark_event_occurred(event_id)
            else:
                if suppressed:
                    print(f"    Event suppressed: {event_id} (p={probability:.2%})")
                else:
                    print(f"    Event not triggered: {event_id} (p={probability:.2%}, roll={roll:.2f})")

            evaluations.append(evaluation)

        return triggered, evaluations

    @staticmethod
    def _aggregate_event_samples(samples: list[list]) -> tuple[list[dict], list[dict]]:
        """Aggregate candidate events from multiple elicitation samples.

        Per event id, the aggregated probability is the mean across samples,
        counting samples where the id is absent as 0 (absence means the event's
        conditions were judged not met). Extra fields (for example emergent
        descriptions) come from the first appearance.

        Returns:
            Tuple of (aggregated_candidates, skipped_evaluations). Skipped
            evaluations record per-sample entries that were malformed, tagged
            with the sample index.
        """
        n = len(samples)
        order: list[str] = []
        entries: dict[str, dict] = {}
        sample_values: dict[str, list[float]] = {}
        present_counts: dict[str, int] = {}
        skipped: list[dict] = []

        for index, sample in enumerate(samples):
            seen_in_sample: set[str] = set()
            for event_data in sample:
                probability = event_data.get("probability") if isinstance(event_data, dict) else None
                if (
                    not isinstance(event_data, dict)
                    or not isinstance(event_data.get("id"), str)
                    or not isinstance(probability, (int, float))
                    or isinstance(probability, bool)
                    or not 0 <= probability <= 1
                ):
                    skipped.append(
                        {
                            "id": event_data.get("id") if isinstance(event_data, dict) else None,
                            "sample": index,
                            "skipped": "Invalid event data in sample (missing id or invalid probability)",
                            "triggered": False,
                        }
                    )
                    continue

                event_id = event_data["id"]
                if event_id in seen_in_sample:
                    # Duplicate id within one sample: first occurrence wins.
                    continue
                seen_in_sample.add(event_id)

                if event_id not in entries:
                    order.append(event_id)
                    entries[event_id] = dict(event_data)
                    sample_values[event_id] = [0.0] * n
                    present_counts[event_id] = 0
                sample_values[event_id][index] = float(probability)
                present_counts[event_id] += 1

        aggregated: list[dict] = []
        for event_id in order:
            entry = entries[event_id]
            values = sample_values[event_id]
            entry["probability"] = sum(values) / n
            entry["probability_samples"] = values
            entry["samples_present"] = present_counts[event_id]
            entry["n_samples"] = n
            aggregated.append(entry)

        return aggregated, skipped

    def _run_actors_step(self, turn: int, triggered_events: list[dict]) -> dict[str, str]:
        """Step 2: Get actions from each actor.

        Args:
            turn: Current turn number
            triggered_events: List of events that occurred

        Returns:
            Dict mapping actor_id to their markdown output
        """
        outputs = {}
        actor_ids = list(self.scenario.actors.keys())

        def get_client(actor_id: str):
            """Resolve LLM client for a specific actor."""
            if "actors" in self.llm_clients and actor_id in self.llm_clients["actors"]:
                return self.llm_clients["actors"][actor_id]
            return self.llm_clients["events"]

        def run_actor(actor_id: str) -> tuple[str, LLMResponse]:
            """Execute one actor prompt and return raw response."""
            client = get_client(actor_id)
            system, user = self.prompt_builder.build_actor_prompt(actor_id, turn, triggered_events)
            response = client.complete(system, user)
            return actor_id, response

        # Parallelize actor prompts when possible (independent prompts)
        if len(actor_ids) > 1:
            max_workers = min(len(actor_ids), 8)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(run_actor, actor_id): actor_id for actor_id in actor_ids}

                for future in as_completed(futures):
                    actor_id, response = future.result()
                    self._record_llm_call(turn, f"actor:{actor_id}", response)
                    outputs[actor_id] = response.content
                    self.scenario.actors[actor_id].last_actions = response.content

                    if self.output_manager:
                        self.output_manager.save_actor_output(turn, actor_id, response.content)

            # Keep output ordering deterministic for downstream consumers/tests
            return {actor_id: outputs[actor_id] for actor_id in actor_ids}

        # Fallback to sequential flow for single-actor scenarios
        for actor_id in actor_ids:
            actor = self.scenario.actors[actor_id]
            print(f"  → {actor.name}...")

            # Get appropriate client for this actor
            client = get_client(actor_id)

            system, user = self.prompt_builder.build_actor_prompt(actor_id, turn, triggered_events)
            response = client.complete(system, user)
            self._record_llm_call(turn, f"actor:{actor_id}", response)
            outputs[actor_id] = response.content

            # Update actor's last actions in scenario
            self.scenario.actors[actor_id].last_actions = response.content

            # Write immediately if output manager is present
            if self.output_manager:
                self.output_manager.save_actor_output(turn, actor_id, response.content)

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
        from .metric_rules import parse_versioned_rules, validate_rules_format, get_changelog_summary

        if turn <= self.scenario.config.rule_evolution.freeze_until_turn:
            print("  ⏭️  Rules step skipped due to freeze policy")
            skipped_rules = self._build_noop_rules_update(turn)
            parsed, warnings, parse_error = self._analyze_rules_output(skipped_rules, turn)
            if parse_error is None and parsed is not None:
                print("  📝 Rules changes: No material changes")
                if self.output_manager:
                    self.output_manager.save_rules_metadata(
                        turn,
                        {
                            "version": parsed.version,
                            "has_changelog": parsed.has_changelog,
                            "changelog_entries": [],
                            "format_warnings": warnings,
                            "is_noop_update": parsed.is_noop_update,
                            "final_action": "skipped_due_to_freeze",
                            "policy": {
                                "freeze_until_turn": self.scenario.config.rule_evolution.freeze_until_turn,
                                "max_changes_per_turn": self.scenario.config.rule_evolution.max_changes_per_turn,
                            },
                        },
                    )
            return skipped_rules

        system, user = self.prompt_builder.build_rules_prompt(turn, actor_outputs, triggered_events)
        response = self.llm_clients["rules"].complete(system, user)
        self._record_llm_call(turn, "rules", response)
        parsed, warnings, parse_error = self._analyze_rules_output(response.content, turn)

        should_retry_for_truncation = (
            response.get_finish_reason() == "length"
            or "Rules content is empty or too short" in warnings
        )

        if should_retry_for_truncation:
            print("  ⚠️  Rules output truncated (finish_reason=length or missing rules), retrying with concise constraints...")
            concise_system = (
                system
                + "\n\nKeep the response concise. Prioritize completeness over detail."
            )
            concise_user = (
                user
                + "\n\nIMPORTANT OUTPUT LIMITS:\n"
                + "- Keep total output concise (target under ~1200 tokens).\n"
                + "- Max 6 changelog entries total.\n"
                + "- Motivation and Expected impact: max 1 short sentence each.\n"
                + "- You MUST include a complete '## Rules' section with 5-10 numbered rules.\n"
                + "- Do not add any preamble."
            )
            retry_response = self.llm_clients["rules"].complete(concise_system, concise_user)
            self._record_llm_call(turn, "rules:concise_retry", retry_response)

            retry_parsed, retry_warnings, retry_parse_error = self._analyze_rules_output(retry_response.content, turn)
            if retry_parse_error is None and "Rules content is empty or too short" not in retry_warnings:
                response = retry_response
                parsed = retry_parsed
                warnings = retry_warnings
                parse_error = retry_parse_error

        policy_violations = self._validate_rule_update_policy(turn, parsed)
        if parse_error is None and parsed is not None and policy_violations:
            print("  ⚠️  Rules policy violation detected, retrying with stricter constraints...")
            strict_system = (
                system
                + "\n\nRule-evolution policy is binding. Prefer carrying the previous rules forward unchanged "
                + "unless the prompt explicitly justifies a small, necessary edit."
            )
            strict_user = (
                user
                + "\n\nSTRICT RULE EVOLUTION POLICY:\n"
                + "\n".join(f"- {violation}" for violation in policy_violations)
                + "\n- If the policy forbids substantive changes this turn, keep the rules materially identical."
                + "\n- In that case, use a changelog line that says `- No material rule changes.`"
                + "\n- Do not broaden, relax, or rewrite the rule system."
            )
            retry_response = self.llm_clients["rules"].complete(strict_system, strict_user)
            self._record_llm_call(turn, "rules:policy_retry", retry_response)
            retry_parsed, retry_warnings, retry_parse_error = self._analyze_rules_output(retry_response.content, turn)
            retry_policy_violations = self._validate_rule_update_policy(turn, retry_parsed)
            if retry_parse_error is None and retry_parsed is not None and not retry_policy_violations:
                response = retry_response
                parsed = retry_parsed
                warnings = retry_warnings
                parse_error = retry_parse_error
            else:
                print("  ⚠️  Rules output still violated policy, carrying forward previous rules")
                response = LLMResponse(
                    content=self._build_noop_rules_update(turn),
                    raw_response={"model": "policy-fallback/noop-rules"},
                )
                parsed, warnings, parse_error = self._analyze_rules_output(response.content, turn)

        # Parse and validate versioned rules
        try:
            if parse_error is not None or parsed is None:
                raise parse_error or ValueError("Could not parse rules output")
            if warnings:
                for warning in warnings:
                    print(f"  ⚠️  Rules format: {warning}")

            # Log changelog summary
            if parsed.has_changelog:
                summary = get_changelog_summary(parsed)
                print(f"  📝 Rules changes: {summary}")

            # Store parsed metadata for output manager
            if self.output_manager:
                self.output_manager.save_rules_metadata(turn, {
                    "version": parsed.version,
                    "has_changelog": parsed.has_changelog,
                    "changelog_entries": [
                        {
                            "type": entry.change_type,
                            "rule_name": entry.rule_name,
                            "motivation": entry.motivation,
                            "expected_impact": entry.expected_impact,
                        }
                        for entry in parsed.changelog_entries
                    ],
                    "format_warnings": warnings,
                    "is_noop_update": parsed.is_noop_update,
                    "final_action": "updated"
                    if not parsed.is_noop_update
                    else "carried_forward",
                    "policy": {
                        "freeze_until_turn": self.scenario.config.rule_evolution.freeze_until_turn,
                        "max_changes_per_turn": self.scenario.config.rule_evolution.max_changes_per_turn,
                    },
                })

        except ValueError as e:
            print(f"  ⚠️  Could not parse rules version/changelog: {e}")
            print(f"  Continuing with raw content...")

        return response.content

    def _analyze_rules_output(
        self, raw_content: str, turn: int
    ) -> tuple[Optional[object], list[str], Optional[ValueError]]:
        """Parse and validate versioned rules output."""
        from .metric_rules import parse_versioned_rules, validate_rules_format

        try:
            parsed_rules = parse_versioned_rules(raw_content, turn)
            _, parsed_warnings = validate_rules_format(raw_content, turn)
            return parsed_rules, parsed_warnings, None
        except ValueError as err:
            return None, [], err

    def _validate_rule_update_policy(self, turn: int, parsed_rules: Optional[object]) -> list[str]:
        """Check whether a rules update complies with scenario rule-evolution guardrails."""
        if parsed_rules is None:
            return []

        policy = self.scenario.config.rule_evolution
        violations: list[str] = []
        previous_rules_content = self._extract_rules_content(self.scenario.metric_rules)
        new_rules_content = self._extract_rules_content(parsed_rules.full_content)

        if turn <= policy.freeze_until_turn:
            if not parsed_rules.is_noop_update:
                violations.append(
                    f"Turn {turn} is within the freeze window through turn {policy.freeze_until_turn}; "
                    "the changelog must state that no material rule changes were made."
                )
            if self._normalize_rules_text(previous_rules_content) != self._normalize_rules_text(new_rules_content):
                violations.append("Frozen turns must keep the substantive rules unchanged.")

        if not parsed_rules.is_noop_update and len(parsed_rules.changelog_entries) > policy.max_changes_per_turn:
            violations.append(
                f"This turn changed {len(parsed_rules.changelog_entries)} rules, exceeding the configured limit "
                f"of {policy.max_changes_per_turn}."
            )

        return violations

    def _extract_rules_content(self, content: str) -> str:
        """Extract the substantive rules section from versioned rules markdown."""
        rules_match = re.search(r"##\s*Rules\s*\n(.*)", content, re.DOTALL | re.IGNORECASE)
        if rules_match:
            return rules_match.group(1).strip()
        return content.strip()

    def _normalize_rules_text(self, content: str) -> str:
        """Normalize rules text for policy comparisons."""
        return re.sub(r"\s+", " ", content).strip().lower()

    def _build_noop_rules_update(self, turn: int) -> str:
        """Carry forward the previous rule set with a no-change changelog."""
        version_match = re.search(
            r"#\s*Metric\s+Rules\s+v(\d+)",
            self.scenario.metric_rules,
            re.IGNORECASE,
        )
        previous_version = int(version_match.group(1)) if version_match else max(turn - 1, 1)
        rules_content = self._extract_rules_content(self.scenario.metric_rules)
        freeze_until = self.scenario.config.rule_evolution.freeze_until_turn
        if turn <= freeze_until:
            motivation = (
                f"Rule evolution is frozen through turn {freeze_until}, so the prior rule set remains in force."
            )
        else:
            motivation = "No strong evidence justified a substantive rule change this turn."

        return (
            f"# Metric Rules v{previous_version + 1} (Turn {turn})\n\n"
            f"## Changelog from v{previous_version}\n\n"
            "- No material rule changes.\n"
            f"  - **Motivation:** {motivation}\n"
            "  - **Expected impact:** Metric dynamics continue under the prior rule set.\n\n"
            "## Rules\n\n"
            f"{rules_content}\n"
        )

    def _run_metrics_step(
        self, turn: int, actor_outputs: dict[str, str], triggered_events: list[dict]
    ) -> tuple[dict, str, str]:
        """Step 4: Update metrics and generate narrative.

        Args:
            turn: Current turn number
            actor_outputs: Dict of actor outputs
            triggered_events: List of events that occurred

        Returns:
            Tuple of (metrics dict, narrative string, notepad string)
        """
        system, user = self.prompt_builder.build_metrics_prompt(
            turn, actor_outputs, triggered_events
        )
        response = self.llm_clients["metrics"].complete(system, user)
        self._record_llm_call(turn, "metrics", response)

        try:
            metrics, narrative, notepad = response.extract_metrics_and_narrative()
        except (json.JSONDecodeError, ValueError, LLMParseError) as e:
            print(f"  Warning: Could not parse metrics response: {e}")
            print(f"  Response was: {response.content[:200]}...")

            # Retry once with format-fix prompt
            try:
                fix_system, fix_user = self.prompt_builder.build_format_fix_metrics_prompt(
                    turn, response.content
                )
                fix_response = self.llm_clients["metrics"].complete(fix_system, fix_user)
                self._record_llm_call(turn, "metrics:format_fix", fix_response)
                metrics, narrative, notepad = fix_response.extract_metrics_and_narrative()
                print("  ✓ Metrics format fixed on retry")
            except Exception as fix_e:
                print(f"  Warning: Metrics format-fix retry failed: {fix_e}")

                # Return previous metrics with error narrative
                current_metrics = {m.id: m.value for m in self.scenario.metrics.metrics.values()}
                error_narrative = (
                    "[ERROR: Could not parse metrics response. Keeping previous values.]\n\n"
                    + response.content
                )
                return current_metrics, error_narrative, self.scenario.notepad

        return self._validate_and_clamp_metrics(metrics), narrative, notepad

    def _run_constitutional_referee_step(
        self, turn: int, proposed_metrics: dict, narrative: str
    ) -> tuple[dict, str]:
        """Step 5: Validate metrics against constitutional constraints (optional).

        Args:
            turn: Current turn number
            proposed_metrics: Proposed new metrics
            narrative: Narrative explaining the changes

        Returns:
            Tuple of (final_metrics, final_narrative) - may be corrected if violations found
        """
        # Get previous metrics for comparison
        previous_metrics = {m.id: m.value for m in self.scenario.metrics.metrics.values()}

        violations_log = []
        max_iterations = self.scenario.config.constitutional_enforcement.max_attempts
        on_failure = self.scenario.config.constitutional_enforcement.on_failure

        def _normalize_referee_result(raw_result: str) -> str:
            stripped = raw_result.strip()
            fenced_match = re.match(r"^```[^\n]*\n(?P<body>.*)\n```$", stripped, re.DOTALL)
            if fenced_match:
                return fenced_match.group("body").strip()
            if stripped.startswith("```"):
                first_newline = stripped.find("\n")
                if first_newline != -1:
                    body = stripped[first_newline + 1 :].strip()
                    if body.endswith("```"):
                        body = body[:-3].rstrip()
                    return body.strip()
            return stripped

        for iteration in range(max_iterations):
            # Build referee prompt
            system, user = self.prompt_builder.build_constitutional_referee_prompt(
                turn, previous_metrics, proposed_metrics, narrative
            )

            # Use dedicated referee client (cheaper/faster model)
            client = self.llm_clients.get("referee", self.llm_clients["metrics"])
            response = client.complete(system, user)
            self._record_llm_call(turn, f"constitutional_referee:attempt_{iteration+1}", response)

            # Parse response
            result = _normalize_referee_result(response.content)

            if result.startswith("APPROVED"):
                if iteration > 0:
                    print(f"  ✓ Constitution validated (after {iteration+1} attempts)")

                # Save metadata about validation
                if self.output_manager:
                    metadata = {
                        "status": "approved",
                        "iterations": iteration + 1,
                        "violations_found": violations_log,
                        "final_action": (
                            "approved"
                            if not violations_log
                            else "corrected_and_approved"
                        ),
                    }
                    self.output_manager.save_constitutional_metadata(turn, metadata)

                return proposed_metrics, narrative

            elif result.startswith("VIOLATIONS:"):
                violations = result[len("VIOLATIONS:"):].strip()
                violations_log.append({
                    "iteration": iteration + 1,
                    "violations": violations,
                })

                print(f"  ⚠️  Constitutional violations found:")
                for line in violations.split('\n'):
                    if line.strip():
                        print(f"     {line.strip()}")

                if iteration < max_iterations - 1:
                    print(f"  🔄 Requesting corrected metrics (attempt {iteration+2}/{max_iterations})...")
                    corrected = self._request_constitutional_correction(
                        turn, previous_metrics, proposed_metrics, narrative, violations
                    )
                    if corrected is None:
                        print("  ⚠️  Correction could not be parsed")
                        final_metrics, final_narrative, final_action = self._apply_constitutional_failure_policy(
                            previous_metrics, proposed_metrics, narrative
                        )
                        if self.output_manager:
                            metadata = {
                                "status": "violations_found",
                                "iterations": iteration + 1,
                                "violations_found": violations_log,
                                "final_action": final_action,
                            }
                            self.output_manager.save_constitutional_metadata(turn, metadata)
                        return final_metrics, final_narrative

                    proposed_metrics, narrative = corrected
                    continue
                else:
                    print(f"  ⚠️  Max correction attempts reached")
                    final_metrics, final_narrative, final_action = self._apply_constitutional_failure_policy(
                        previous_metrics, proposed_metrics, narrative
                    )

                    # Save metadata
                    if self.output_manager:
                        metadata = {
                            "status": "max_attempts_reached",
                            "iterations": iteration + 1,
                            "violations_found": violations_log,
                            "final_action": final_action,
                        }
                        self.output_manager.save_constitutional_metadata(turn, metadata)

                    return final_metrics, final_narrative
            else:
                print(f"  ⚠️  Unexpected referee response format: {result[:100]}...")

                # Save metadata
                if self.output_manager:
                    metadata = {
                        "status": "parse_error",
                        "iterations": iteration + 1,
                        "violations_found": violations_log,
                        "error": "Unexpected response format",
                        "response_preview": result[:200],
                    }
                    self.output_manager.save_constitutional_metadata(turn, metadata)

                break

        return proposed_metrics, narrative

    def _apply_constitutional_failure_policy(
        self,
        previous_metrics: dict,
        proposed_metrics: dict,
        narrative: str,
    ) -> tuple[dict, str, str]:
        """Apply configured fallback when the referee cannot obtain a compliant update."""
        on_failure = self.scenario.config.constitutional_enforcement.on_failure
        if on_failure == "keep_previous":
            print("  ↩️  Keeping previous state because no compliant update was produced")
            return previous_metrics, self.scenario.world_state.narrative, "kept_previous_state"

        print("  ⚠️  Continuing with proposed metrics despite remaining violations")
        return proposed_metrics, narrative, "accepted_with_violations"

    def _request_constitutional_correction(
        self,
        turn: int,
        previous_metrics: dict,
        proposed_metrics: dict,
        narrative: str,
        violations: str,
    ) -> Optional[tuple[dict, str]]:
        """Request a minimal metrics/narrative correction after constitutional violations."""
        system, user = self.prompt_builder.build_constitutional_correction_prompt(
            turn, previous_metrics, proposed_metrics, narrative, violations
        )
        client = self.llm_clients.get("metrics", self.llm_clients["events"])
        response = client.complete(system, user)
        self._record_llm_call(turn, "constitutional_correction", response)

        try:
            corrected_metrics, corrected_narrative, _ = response.extract_metrics_and_narrative()
        except (json.JSONDecodeError, ValueError, LLMParseError) as e:
            print(f"  Warning: Could not parse constitutional correction response: {e}")
            print(f"  Response was: {response.content[:200]}...")

            try:
                fix_system, fix_user = self.prompt_builder.build_format_fix_metrics_prompt(
                    turn, response.content
                )
                fix_response = client.complete(fix_system, fix_user)
                self._record_llm_call(turn, "constitutional_correction:format_fix", fix_response)
                corrected_metrics, corrected_narrative, _ = fix_response.extract_metrics_and_narrative()
                print("  ✓ Constitutional correction format fixed on retry")
            except Exception as fix_e:
                print(f"  Warning: Constitutional correction format-fix retry failed: {fix_e}")
                return None

        corrected_metrics = self._validate_and_clamp_metrics(corrected_metrics)
        if not corrected_narrative.strip():
            corrected_narrative = narrative

        return corrected_metrics, corrected_narrative

    def _validate_and_clamp_metrics(self, metrics: dict) -> dict:
        """Validate metric IDs/types and clamp out-of-range values."""
        for metric_id, value in list(metrics.items()):
            if metric_id in self.scenario.metrics.metrics:
                metric = self.scenario.metrics.metrics[metric_id]
                if not isinstance(value, (int, float)):
                    print(f"  Warning: Invalid value type for {metric_id}: {type(value)}")
                    metrics[metric_id] = metric.value
                elif not metric.min_value <= value <= metric.max_value:
                    print(
                        f"  Warning: Value {value} out of bounds for {metric_id} "
                        f"({metric.min_value}-{metric.max_value}), clamping"
                    )
                    metrics[metric_id] = max(metric.min_value, min(metric.max_value, value))
            else:
                print(f"  Warning: Unknown metric '{metric_id}' in response, skipping")
                del metrics[metric_id]

        return metrics

    def _run_summarization_step(self, turn: int, current_narrative: str) -> str:
        """Step 6: Update historical summary.

        Args:
            turn: Current turn number
            current_narrative: Narrative of the current turn

        Returns:
            Updated historical summary
        """
        current_summary = self.scenario.world_state.historical_summary

        # If no history yet, the current narrative becomes the start of history (or we summarize it immediately)
        # For consistency, let's summarize even the first turn if it's long

        system, user = self.prompt_builder.build_summary_prompt(current_summary, current_narrative)
        response = self.llm_clients["summary"].complete(system, user)
        self._record_llm_call(turn, "summary", response)
        return response.content

    def _mark_event_occurred(self, event_id: str):
        """Mark event as occurred (for non-repeatable events)."""
        for event in self.scenario.events:
            if event.id == event_id and not event.can_repeat:
                event.occurred = True
                self.scenario.occurred_events.add(event_id)

    def _update_scenario_state(
        self, new_metrics: dict, narrative: str, historical_summary: str, notepad: str, turn: int, time_period: str
    ):
        """Update scenario with turn results."""
        self.scenario.metrics.update_from_dict(new_metrics)
        self.scenario.world_state.narrative = narrative
        self.scenario.world_state.historical_summary = historical_summary
        self.scenario.notepad = notepad
        self.scenario.world_state.turn = turn
        self.scenario.world_state.time_period = time_period


def run_simulation(
    scenario: Scenario,
    llm_client: Optional[Union[LLMClientProtocol, dict[str, LLMClientProtocol]]] = None,
    num_turns: int = None,
    output_manager: Optional["OutputManager"] = None,
    start_turn: int = 1,
    progress_tracker: Optional["ProgressTracker"] = None,
) -> list[TurnResult]:
    """Run a complete simulation.

    Args:
        scenario: Loaded scenario
        llm_client: Either:
            - Single LLM client (backward compatible)
            - Dict of clients for per-task usage
            - None (creates clients based on scenario.config.llm)
        num_turns: Number of turns to run (default: from config)
        output_manager: Optional OutputManager for incremental writing
        start_turn: Turn number to start from (default: 1, for resume: N+1)
        progress_tracker: Optional ProgressTracker for progress display

    Returns:
        List of TurnResults
    """
    orchestrator = Orchestrator(scenario, llm_client, output_manager, progress_tracker)
    max_turns = num_turns or scenario.config.max_turns
    results = []

    # Start simulation tracking
    if progress_tracker:
        progress_tracker.start_simulation()

    try:
        for turn in range(start_turn, max_turns + 1):
            result = orchestrator.run_turn(turn)
            results.append(result)
            scenario.turn_history.append(result)

        # Display final cost summary
        run_costs = orchestrator.get_run_costs()
        if run_costs and run_costs.total_tokens > 0:
            if progress_tracker:
                progress_tracker.complete_simulation(run_costs.total_cost_usd, run_costs.total_tokens)
            else:
                print(f"\n{'='*60}")
                print(f"SIMULATION COMPLETE")
                print(f"{'='*60}")
                print(f"Total cost: ${run_costs.total_cost_usd:.4f} ({run_costs.total_tokens:,} tokens)")
                if len(results) > 0:
                    avg_cost = run_costs.total_cost_usd / len(results)
                    avg_tokens = run_costs.total_tokens / len(results)
                    print(f"Average per turn: ${avg_cost:.4f} ({avg_tokens:,.0f} tokens)")

        # Save costs if output manager is available
        if output_manager and run_costs:
            output_manager.save_costs(run_costs)
            if output_manager.run_dir:
                print(f"\nCost report saved: {output_manager.run_dir / 'costs.json'}")

    finally:
        # Close orchestrator's owned clients if any
        orchestrator.close()

    return results
