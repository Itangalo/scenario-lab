"""
Main simulation engine for Scenario Lab V3.

Orchestrates the complete simulation loop:
- Pre-Turn: Event check, trigger check, AP reset, view generation
- Phase 1: Initiative & Communication
- Phase 2: Response & Final Negotiation
- Phase 3: Execution & Goal Adjustment
- Post-Turn: Validation, updates, narrative synthesis
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from .models import (
    WorldState,
    ActorView,
    Message,
    CommunicationRound,
    ActorAction,
    TurnActions,
    ScenarioConfig,
    MetricsConfig,
    EventsConfig,
    FunctionCall,
)
from .methods_base import ScenarioMethods
from .utils import (
    setup_logging,
    load_scenario_config,
    load_metrics_config,
    load_events_config,
    load_background_context,
    load_actor_background,
    get_visible_metrics,
    generate_run_id,
    save_turn_state,
)


logger = logging.getLogger(__name__)


class Simulation:
    """
    Main engine that orchestrates the scenario simulation.

    Handles:
    - Configuration loading
    - Turn loop execution
    - Actor communication and action phases
    - State management and persistence
    """

    def __init__(
        self,
        scenario_path: str,
        scenario_methods: Optional[ScenarioMethods] = None,
        run_id: Optional[str] = None,
        cli_provider: Optional[str] = None,
        cli_model: Optional[str] = None,
    ):
        """
        Initialize the simulation engine.

        Args:
            scenario_path: Path to scenario directory (string or Path)
            scenario_methods: Optional scenario-specific action methods
            run_id: Optional run identifier (auto-generated if not provided)
            cli_provider: Optional provider override from the CLI
            cli_model: Optional model override from the CLI
        """
        self.scenario_dir = Path(scenario_path)
        self.scenario_methods = scenario_methods
        self.run_id = run_id or generate_run_id()
        self.run_dir = self.scenario_dir / "runs" / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = setup_logging(self.scenario_dir.name, self.run_id, log_dir=self.run_dir)

        # Load configurations
        self.logger.info(f"Loading scenario from: {self.scenario_dir}")
        self.config = load_scenario_config(self.scenario_dir)
        self.metrics_config = load_metrics_config(self.scenario_dir)
        self.events_config = load_events_config(self.scenario_dir)
        if cli_model:
            self.config.llm.model = cli_model

        if self.scenario_methods is None:
            methods_path = self.scenario_dir / "methods.py"
            if methods_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("scenario_methods", methods_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Find the ScenarioMethods subclass and instantiate it
                for name, obj in vars(module).items():
                    if isinstance(obj, type) and issubclass(obj, ScenarioMethods) and obj is not ScenarioMethods:
                        self.scenario_methods = obj()
                        self.logger.info(f"Loaded scenario methods: {name}")
                        break

        # Load background context
        self.background_context = load_background_context(self.scenario_dir)
        self.actor_backgrounds = {
            actor: load_actor_background(self.scenario_dir, actor)
            for actor in self.config.actors
        }

        # Initialize LLM provider
        self.logger.info(f"Initializing LLM provider: {self.config.llm.provider}")
        from .llm_provider import get_provider
        self.llm_provider = get_provider(self.config.llm, self.config.model_dump(), cli_provider, str(self.run_dir))

        # Initialize world state
        self.world_state = self._initialize_world_state()

        # Track actor action points
        self.actor_ap: Dict[str, int] = {}
        self._reset_action_points()

        # Track actor goals
        self.actor_goals: Dict[str, List[str]] = {
            actor: [] for actor in self.config.actors
        }

        self.total_turns = 0
        self.logger.info(f"Engine initialized for run: {self.run_id}")

    def _initialize_world_state(self) -> WorldState:
        """
        Initialize world state from metrics config and background.

        Returns:
            Initial WorldState
        """
        self.logger.info("Initializing world state")

        # Import Metrics model
        from .models import Metrics

        # Initialize metrics from config
        metrics = Metrics(
            world=self.metrics_config.world,
            actors=self.metrics_config.actors
        )

        # Create initial narrative state from background
        narrative = f"# Background\n\n{self.background_context}\n\n# Turn 0: Initial State\n\n"
        narrative += "The scenario begins. Actors are assessing the situation.\n"

        return WorldState(
            narrative_state=narrative,
            metrics=metrics,
            fact_ledger=[],
            relationship_state={},
            outcome_flags={}
        )

    def _reset_action_points(self) -> None:
        """Reset action points for all actors at the start of a turn."""
        initial_ap = self.config.action_point_rules.initial_per_turn
        for actor in self.config.actors:
            self.actor_ap[actor] = initial_ap

        self.logger.debug(f"Reset action points: {self.actor_ap}")

    async def run(self, num_turns: int) -> None:
        """
        Run the simulation for a specified number of turns.

        Convenience method that delegates to run_simulation().

        Args:
            num_turns: Number of turns to simulate
        """
        await self.run_simulation(num_turns)

    async def run_simulation(self, max_turns: Optional[int] = None) -> None:
        """
        Run the complete simulation.

        Args:
            max_turns: Optional override for max turns
        """
        self.total_turns = max_turns or self.config.max_turns

        self.logger.info(f"Starting simulation: {self.total_turns} turns")

        for turn in range(1, self.total_turns + 1):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"TURN {turn}")
            self.logger.info(f"{'='*60}\n")

            await self.run_turn(turn)

            # Check for early termination conditions
            if self._should_terminate():
                self.logger.info("Simulation terminated early due to outcome flags")
                break

        self.logger.info("Simulation complete")
        self._save_run_summary()

    async def run_turn(self, turn: int) -> None:
        """
        Execute a single turn of the simulation.

        Args:
            turn: Turn number (1-indexed)
        """
        # === PRE-TURN ===
        self.logger.info("[PRE-TURN] Starting")
        self._check_events(turn)
        self._check_triggers(turn)
        self._reset_action_points()
        actor_views = self._generate_actor_views(turn)
        self.logger.info("[PRE-TURN] Complete")

        # === PHASE 1: Initiative & Communication ===
        self.logger.info("[PHASE 1] Initiative & Communication")
        comms_phase_1 = await self._run_communication_phase(turn, 1, actor_views, [])
        self.logger.info("[PHASE 1] Complete")

        # === PHASE 2: Response & Final Negotiation ===
        self.logger.info("[PHASE 2] Response & Final Negotiation")
        comms_phase_2 = await self._run_communication_phase(
            turn, 2, actor_views, comms_phase_1.messages
        )
        self.logger.info("[PHASE 2] Complete")

        # === PHASE 3: Execution & Goal Adjustment ===
        self.logger.info("[PHASE 3] Execution & Goal Adjustment")
        turn_actions = await self._run_execution_phase(
            turn, actor_views, comms_phase_1.messages + comms_phase_2.messages
        )
        self.logger.info("[PHASE 3] Complete")

        # === POST-TURN SYNTHESIS ===
        self.logger.info("[POST-TURN] Starting synthesis")
        self._validate_actions(turn_actions)
        interpretations = self._execute_actions(turn, turn_actions)
        await self._synthesize_narrative(turn, turn_actions, interpretations)
        self.logger.info("[POST-TURN] Complete")

        # Save turn state to disk
        save_turn_state(
            self.scenario_dir,
            self.run_id,
            turn,
            self.world_state,
            actor_views,
            comms_phase_1,
            comms_phase_2,
            turn_actions
        )

        self.logger.info(f"Turn {turn} complete\n")

    # === Pre-Turn Methods ===

    def _check_events(self, turn: int) -> None:
        """Check for and apply exogenous events."""
        events_this_turn = [
            event for event in self.events_config.events if event.turn == turn
        ]

        if not events_this_turn:
            return

        self.logger.info(f"Processing {len(events_this_turn)} event(s)")

        for event in events_this_turn:
            self.logger.info(f"Event: {event.name}")

            # Apply event effects to metrics
            # Path format: "world.metric_name" or "actors.ActorName.public.metric_name"
            for path, value in event.effects.items():
                parts = path.split(".")

                if parts[0] == "world":
                    # World metric
                    self.world_state.metrics.world[parts[1]] = value
                elif parts[0] == "actors" and len(parts) >= 4:
                    # Actor metric: actors.ActorName.public/private.metric_name
                    actor_name = parts[1]
                    visibility = parts[2]  # "public" or "private"
                    metric_name = ".".join(parts[3:])  # Handle nested metrics

                    if actor_name not in self.world_state.metrics.actors:
                        from .models import ActorMetricsData
                        self.world_state.metrics.actors[actor_name] = ActorMetricsData()

                    if visibility == "private":
                        self.world_state.metrics.actors[actor_name].private[metric_name] = value
                    else:
                        self.world_state.metrics.actors[actor_name].public[metric_name] = value
                else:
                    self.logger.warning(f"Unrecognized metric path: {path}")

            # Add to narrative
            event_text = f"\n## Exogenous Event: {event.name}\n\n{event.description}\n"
            self.world_state.narrative_state += event_text

            # Add fact
            from .models import FactLedgerEntry
            self.world_state.fact_ledger.append(
                FactLedgerEntry(
                    timestamp=f"Turn {turn}",
                    fact=f"Event: {event.name}",
                    source="exogenous_event"
                )
            )

    def _check_triggers(self, turn: int) -> None:
        """Check for world-altering triggers based on current state."""
        # TODO: Implement trigger checking logic
        # For MVP, this is a stub
        pass

    def _generate_actor_views(self, turn: int) -> Dict[str, ActorView]:
        """
        Generate filtered views for each actor.

        Args:
            turn: Current turn number

        Returns:
            Dictionary mapping actor name to their ActorView
        """
        self.logger.info("Generating actor views")

        views = {}

        for actor in self.config.actors:
            # Filter metrics based on information asymmetry
            visible_metrics = get_visible_metrics(self.world_state.metrics, actor)

            # Create view
            view = ActorView(
                actor_name=actor,
                narrative_state=self.world_state.narrative_state,
                visible_metrics=visible_metrics,
                fact_ledger=self.world_state.fact_ledger,
                relationship_state=self.world_state.relationship_state,
                current_goals=self.actor_goals.get(actor, []),
                action_points=self.actor_ap[actor]
            )

            views[actor] = view

        return views

    # === Communication Phase Methods ===

    async def _run_communication_phase(
        self,
        turn: int,
        phase: int,
        actor_views: Dict[str, ActorView],
        previous_messages: List[Message]
    ) -> CommunicationRound:
        """
        Run a communication phase using the LLM provider.
        """
        self.logger.info(f"Running communication phase {phase}")
        all_new_messages = []

        for actor_name, actor_view in actor_views.items():
            
            prompt_name = f"actor_phase{phase}.txt"
            system_prompt = self._construct_system_prompt(prompt_name, actor_view, previous_messages)

            messages = [
                {"role": "system", "content": system_prompt},
            ]

            response_str = await self.llm_provider.complete(messages, self.config.llm.model)
            
            try:
                import json
                response_data = json.loads(response_str)
                
                for msg_data in response_data.get("messages", []):
                    new_message = Message(
                        from_actor=actor_name,
                        to_actor=msg_data["to"],
                        content=msg_data["content"],
                        turn=turn,
                        phase=phase,
                    )
                    all_new_messages.append(new_message)
                    self.logger.info(f"Message from {actor_name} to {msg_data['to']}: {msg_data['content']}")

            except json.JSONDecodeError:
                self.logger.error(f"Failed to decode LLM response for {actor_name}: {response_str}")

        return CommunicationRound(phase=phase, messages=all_new_messages)

    def _construct_system_prompt(
        self,
        prompt_name: str,
        actor_view: ActorView,
        messages: List[Message] = [],
        world_altering_event: bool = False,
    ) -> str:
        """Constructs a system prompt using the Jinja2 templates."""
        from prompts.loader import load_prompt

        if self.scenario_methods:
            available_actions = list(self.scenario_methods.action_registry.keys())
        else:
            available_actions = []

        return load_prompt(
            prompt_name,
            actor_name=actor_view.actor_name,
            actor_description=self.actor_backgrounds.get(actor_view.actor_name, ""),
            current_goals=actor_view.current_goals,
            visible_metrics=actor_view.visible_metrics.model_dump(),
            relationships={k: v.model_dump() for k, v in actor_view.relationship_state.items()},
            fact_ledger=[fact.fact for fact in actor_view.fact_ledger],
            narrative=actor_view.narrative_state,
            action_points=actor_view.action_points,
            incoming_messages=messages,
            communication_summary="\n".join([f"{m.from_actor} to {m.to_actor}: {m.content}" for m in messages]),
            world_altering_event=world_altering_event,
            available_actions=available_actions,
        )

    # === Execution Phase Methods ===

    async def _run_execution_phase(
        self,
        turn: int,
        actor_views: Dict[str, ActorView],
        all_messages: List[Message]
    ) -> TurnActions:
        """
        Run the execution phase where actors take actions using the LLM provider.
        """
        self.logger.info("Running execution phase")
        all_actions = []

        for actor_name, actor_view in actor_views.items():
            system_prompt = self._construct_system_prompt("actor_phase3.txt", actor_view, all_messages)
            
            messages = [
                {"role": "system", "content": system_prompt},
            ]

            response_str = await self.llm_provider.complete(messages, self.config.llm.model, response_format={"type": "json_object"})
            
            try:
                import json
                response_data = json.loads(response_str)
                
                function_calls = [FunctionCall(**call) for call in response_data.get("actions", [])]

                new_action = ActorAction(
                    actor=actor_name,
                    narrative=response_data.get("reasoning", ""),
                    function_calls=function_calls,
                    updated_goals=response_data.get("next_turn_goals", []),
                )
                all_actions.append(new_action)
                self.logger.info(f"Action for {actor_name}: {new_action.narrative}")

            except json.JSONDecodeError:
                self.logger.error(f"Failed to decode LLM response for {actor_name}: {response_str}")

        return TurnActions(turn=turn, actions=all_actions)

    # === Post-Turn Methods ===

    def _validate_actions(self, turn_actions: TurnActions) -> None:
        """
        Validate all actions before execution.

        Args:
            turn_actions: Actions to validate

        Raises:
            ValueError: If validation fails
        """
        if self.scenario_methods is None:
            self.logger.info("No scenario methods configured, skipping")
            return
        self.logger.info("Validating actions")

        for action in turn_actions.actions:
            for function_call in action.function_calls:
                if not self.scenario_methods.validate_action(action.actor, function_call.model_dump(), self.world_state):
                    error_msg = f"Action validation failed for {action.actor}: {function_call.name}"
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)

        self.logger.info("All actions validated")

    def _execute_actions(self, turn: int, turn_actions: TurnActions) -> List[str]:
        """
        Execute all validated actions.

        Args:
            turn: Current turn number
            turn_actions: Actions to execute
            
        Returns:
            A list of interpretation strings.
        """
        if self.scenario_methods is None:
            self.logger.info("No scenario methods configured, skipping")
            return []
        self.logger.info("Executing actions")
        all_interpretations = []

        for action in turn_actions.actions:
            self.logger.info(f"Executing {len(action.function_calls)} action(s) for {action.actor}")

            for function_call in action.function_calls:
                try:
                    interpretations = self.scenario_methods.execute_action(
                        action.actor,
                        function_call.model_dump(),
                        self.world_state
                    )
                    all_interpretations.extend(interpretations)

                except Exception as e:
                    self.logger.error(f"Action execution failed: {e}")
                    raise

            # Update actor goals
            if action.updated_goals:
                self.actor_goals[action.actor] = action.updated_goals

        self.logger.info("All actions executed")
        return all_interpretations

    async def _synthesize_narrative(self, turn: int, turn_actions: TurnActions, interpretations: List[str]) -> None:
        """
        Use the Director to synthesize turn narrative.

        Args:
            turn: Current turn number
            turn_actions: Actions that occurred this turn
            interpretations: A list of interpretation strings from the action methods.
        """
        self.logger.info("Synthesizing narrative")
        from .director import Director

        director = Director(
            self.llm_provider,
            self.config.llm.model,
            self.config.time_scale,
            self.config.start_date
        )
        
        # For now, events_triggered is empty.
        # A more robust implementation would get this from _check_events
        summary = await director.synthesize_turn(
            turn_number=turn,
            turn_actions=turn_actions,
            interpretations=interpretations,
            events_triggered=[],
            previous_narrative=self.world_state.narrative_state,
        )
        
        self.world_state.narrative_state += f"\n\n## Turn {turn} Summary\n{summary}"

    def _should_terminate(self) -> bool:
        """
        Check if simulation should terminate early.

        Returns:
            True if simulation should end
        """
        # Check outcome flags for termination conditions
        # TODO: Make this configurable per scenario
        return False

    def _save_run_summary(self) -> None:
        """Save final run summary for analysis."""
        from .utils import save_json

        summary = {
            "scenario_name": self.config.name,
            "run_id": self.run_id,
            "total_turns": self.total_turns,
            "outcome_flags": self.world_state.outcome_flags,
            "final_metrics": self.world_state.metrics.model_dump()
        }

        summary_path = (
            self.scenario_dir / "runs" / self.run_id / "summary.json"
        )
        save_json(summary, summary_path)

        self.logger.info(f"Run summary saved: {summary_path}")
