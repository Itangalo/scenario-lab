"""Orchestrator for executing simulation turns."""

import random
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Protocol, Optional, Union, TYPE_CHECKING
from .models import Scenario, TurnResult, WorldState
from .prompts import PromptBuilder
from .llm import LLMResponse, LLMClient, LLMParseError

if TYPE_CHECKING:
    from .output import OutputManager


class LLMClientProtocol(Protocol):
    """Protocol for LLM clients (real or mock)."""

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        ...

    def close(self):
        ...


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
        self._owned_clients = []  # Clients we created and need to close

        # Initialize cost tracking
        from .cost import CostTracker
        self.cost_tracker = CostTracker()

        # Setup LLM clients
        if llm_client is None:
            # Create clients based on config
            self.llm_clients = self._create_clients_from_config()
        elif isinstance(llm_client, dict):
            # Use provided dict of clients
            self.llm_clients = llm_client
        else:
            # Single client for all tasks (backward compatible)
            self.llm_clients = {
                "events": llm_client,
                "actors": {},  # Will use events client as fallback
                "rules": llm_client,
                "metrics": llm_client,
                "summary": llm_client,
            }

    def _normalize_model(self, model: Union[str, list]) -> str:
        """Get primary model string from model or fallback list."""
        return model[0] if isinstance(model, list) else model

    def _models_match(self, model1: Union[str, list], model2: Union[str, list]) -> bool:
        """Check if two model specifications match (same primary model)."""
        return self._normalize_model(model1) == self._normalize_model(model2)

    def _create_clients_from_config(self) -> dict:
        """Create LLM clients based on scenario configuration with fallback support."""
        config = self.scenario.config.llm

        # Create client for events (supports fallback list)
        events_client = LLMClient(
            model=config.events,  # Can be str or List[str]
            temperature=config.temperature,
            max_tokens=config.get_task_max_tokens("events"),
        )
        self._owned_clients.append(events_client)

        # Create clients for actors
        actor_clients = {}
        for actor_id in self.scenario.config.actor_ids:
            models = config.get_actor_models(actor_id)  # Can be str or List[str]

            # Reuse existing client if same primary model
            primary_model = self._normalize_model(models)
            existing = next(
                (
                    c
                    for c in [events_client] + list(actor_clients.values())
                    if self._normalize_model(c.models) == primary_model
                ),
                None,
            )
            if existing:
                actor_clients[actor_id] = existing
            else:
                client = LLMClient(
                    model=models, temperature=config.temperature, max_tokens=config.get_task_max_tokens("actors")
                )
                self._owned_clients.append(client)
                actor_clients[actor_id] = client

        # Create client for rules
        if self._models_match(config.rules, config.events):
            rules_client = events_client
        else:
            # Check if any actor client matches
            primary_model = self._normalize_model(config.rules)
            existing = next(
                (
                    c
                    for c in actor_clients.values()
                    if self._normalize_model(c.models) == primary_model
                ),
                None,
            )
            if existing:
                rules_client = existing
            else:
                rules_client = LLMClient(
                    model=config.rules, temperature=config.temperature, max_tokens=config.get_task_max_tokens("rules")
                )
                self._owned_clients.append(rules_client)

        # Create client for metrics
        primary_model = self._normalize_model(config.metrics)
        if self._models_match(config.metrics, config.events):
            metrics_client = events_client
        elif self._models_match(config.metrics, config.rules):
            metrics_client = rules_client
        else:
            # Check if any actor client matches
            existing = next(
                (
                    c
                    for c in actor_clients.values()
                    if self._normalize_model(c.models) == primary_model
                ),
                None,
            )
            if existing:
                metrics_client = existing
            else:
                metrics_client = LLMClient(
                    model=config.metrics, temperature=config.temperature, max_tokens=config.get_task_max_tokens("metrics")
                )
                self._owned_clients.append(metrics_client)

        # Create client for summary
        # Use a simpler logic for summary: reuse events client if it matches, else create new
        if self._models_match(config.summary, config.events):
            summary_client = events_client
        else:
            summary_client = LLMClient(
                model=config.summary, temperature=0.3, max_tokens=config.get_task_max_tokens("summary")  # Lower temp for summary
            )
            self._owned_clients.append(summary_client)

        # Create client for constitutional referee (cheap, fast model)
        # Check if any existing client matches
        primary_model = self._normalize_model(config.referee)
        existing = next(
            (
                c
                for c in [events_client, rules_client, metrics_client, summary_client]
                + list(actor_clients.values())
                if self._normalize_model(c.models) == primary_model
            ),
            None,
        )
        if existing:
            referee_client = existing
        else:
            referee_client = LLMClient(
                model=config.referee, temperature=0.3, max_tokens=config.get_task_max_tokens("referee", default=1000)  # Low temp, short output
            )
            self._owned_clients.append(referee_client)

        return {
            "events": events_client,
            "actors": actor_clients,
            "rules": rules_client,
            "metrics": metrics_client,
            "summary": summary_client,
            "referee": referee_client,
        }

    def close(self):
        """Close all owned LLM clients."""
        for client in self._owned_clients:
            client.close()

    def _record_llm_call(self, turn: int, task_name: str, response: LLMResponse):
        """Record token usage and cost from an LLM call.

        Args:
            turn: Turn number
            task_name: Task identifier (e.g., "events", "actor:government", "rules")
            response: LLM response with usage data
        """
        from .cost import CostCalculator

        usage = response.get_usage()
        if usage:
            cost_details = CostCalculator.calculate_cost(usage)
            self.cost_tracker.record_call(turn, task_name, cost_details)

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

    def _run_events_step(self, turn: int) -> list[dict]:
        """Step 1: Determine which events occur.

        Returns:
            List of triggered events with their probabilities
        """
        system, user = self.prompt_builder.build_events_prompt(turn)
        response = self.llm_clients["events"].complete(system, user)
        self._record_llm_call(turn, "events", response)

        try:
            candidate_events = response.extract_json_array()
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
            except Exception as fix_e:
                print(f"  Warning: Events format-fix retry failed: {fix_e}")
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

        system, user = self.prompt_builder.build_rules_prompt(turn, actor_outputs, triggered_events)
        response = self.llm_clients["rules"].complete(system, user)
        self._record_llm_call(turn, "rules", response)

        def _analyze_rules_output(raw_content: str) -> tuple[Optional[object], list[str], Optional[ValueError]]:
            try:
                parsed_rules = parse_versioned_rules(raw_content, turn)
                _, parsed_warnings = validate_rules_format(raw_content, turn)
                return parsed_rules, parsed_warnings, None
            except ValueError as err:
                return None, [], err

        parsed, warnings, parse_error = _analyze_rules_output(response.content)

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

            retry_parsed, retry_warnings, retry_parse_error = _analyze_rules_output(retry_response.content)
            if retry_parse_error is None and "Rules content is empty or too short" not in retry_warnings:
                response = retry_response
                parsed = retry_parsed
                warnings = retry_warnings
                parse_error = retry_parse_error

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
                })

        except ValueError as e:
            print(f"  ⚠️  Could not parse rules version/changelog: {e}")
            print(f"  Continuing with raw content...")

        return response.content

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
        max_iterations = 2

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
            result = response.content.strip()

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
                        print("  ⚠️  Correction could not be parsed, continuing with current proposal")
                        if self.output_manager:
                            metadata = {
                                "status": "violations_found",
                                "iterations": iteration + 1,
                                "violations_found": violations_log,
                                "final_action": "accepted_with_violations",
                            }
                            self.output_manager.save_constitutional_metadata(turn, metadata)
                        break

                    proposed_metrics, narrative = corrected
                    continue
                else:
                    print(f"  ⚠️  Max correction attempts reached, continuing with proposed metrics")

                    # Save metadata
                    if self.output_manager:
                        metadata = {
                            "status": "max_attempts_reached",
                            "iterations": iteration + 1,
                            "violations_found": violations_log,
                            "final_action": "accepted_with_violations",
                        }
                        self.output_manager.save_constitutional_metadata(turn, metadata)

                    break
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
