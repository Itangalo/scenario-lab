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
from .llm_provider import LLMProvider, create_provider
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
    Simplified simulation orchestrator for Scenario Lab V3.

    Provides a clean interface for running scenario simulations with
    clear phase separation and logging.
    """

    def __init__(self, scenario_path: str):
        """
        Initialize simulation from scenario directory.

        Args:
            scenario_path: Path to scenario directory containing:
                - scenario.yaml
                - metrics.yaml
                - events.yaml
                - background/
        """
        self.scenario_path = Path(scenario_path)
        self.current_turn = 0
        self.run_id = generate_run_id()

        # Setup logging
        self.logger = setup_logging(
            self.scenario_path.name,
            self.run_id,
            self.scenario_path / "runs" / self.run_id
        )

        self.logger.info(f"Initializing simulation from: {self.scenario_path}")

        # Load configuration files
        self._load_configs()

        # Initialize world state
        self._initialize_world_state()

        self.logger.info(f"Simulation initialized (run_id: {self.run_id})")

    def _load_configs(self) -> None:
        """Load all configuration YAML files."""
        self.logger.info("Loading configuration files...")

        # Load scenario configuration
        self.config = load_scenario_config(self.scenario_path)
        self.logger.info(f"Loaded scenario: {self.config.name}")

        # Load metrics configuration
        self.metrics_config = load_metrics_config(self.scenario_path)
        self.logger.info(f"Loaded metrics for {len(self.metrics_config.actors)} actors")

        # Load events configuration
        self.events_config = load_events_config(self.scenario_path)
        self.logger.info(f"Loaded {len(self.events_config.events)} events")

        # Load background context
        self.background_context = load_background_context(self.scenario_path)
        self.logger.info("Loaded background context")

        # Load actor backgrounds
        self.actor_backgrounds = {}
        for actor in self.config.actors:
            self.actor_backgrounds[actor] = load_actor_background(self.scenario_path, actor)
        self.logger.info(f"Loaded backgrounds for {len(self.actor_backgrounds)} actors")

    def _initialize_world_state(self) -> None:
        """Initialize the world state from configuration."""
        from .models import Metrics

        self.logger.info("Initializing world state...")

        # Create metrics structure
        metrics = Metrics(
            world=self.metrics_config.world,
            actors=self.metrics_config.actors
        )

        # Create initial narrative
        narrative = f"# {self.config.name}\n\n"
        narrative += f"## Background\n\n{self.background_context}\n\n"
        narrative += "## Turn 0: Initial State\n\n"
        narrative += "The scenario begins. Actors are assessing the situation.\n"

        # Create world state
        self.world_state = WorldState(
            narrative_state=narrative,
            metrics=metrics,
            fact_ledger=[],
            relationship_state={},
            outcome_flags={}
        )

        self.logger.info("World state initialized")

    def run_turn(self) -> None:
        """
        Execute a single turn of the simulation.

        Phases:
        1. Pre-turn: Events, triggers, AP reset, view generation
        2. Phase 1: Initiative & Communication
        3. Phase 2: Response & Final Negotiation
        4. Phase 3: Execution & Goal Adjustment
        5. Post-turn: Validation, synthesis, state saving
        """
        self.current_turn += 1

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"TURN {self.current_turn} - {self.config.name}")
        self.logger.info(f"{'='*60}\n")

        # === PRE-TURN ===
        self.logger.info("[PRE-TURN] Checking events, resetting action points, generating views")
        # TODO: Implement pre-turn logic
        # - Check for exogenous events
        # - Check world-altering triggers
        # - Reset actor action points
        # - Generate filtered actor views

        # === PHASE 1: Initiative & Communication ===
        self.logger.info("[PHASE 1] Initiative & Communication")
        # TODO: Implement Phase 1
        # - Actors receive their filtered world view
        # - Actors can send messages (1 AP per new recipient)

        # === PHASE 2: Response & Final Negotiation ===
        self.logger.info("[PHASE 2] Response & Final Negotiation")
        # TODO: Implement Phase 2
        # - Actors receive incoming messages
        # - Reply to sender: 0 AP
        # - New message/forward: 1 AP

        # === PHASE 3: Execution & Goal Adjustment ===
        self.logger.info("[PHASE 3] Execution & Goal Adjustment")
        # TODO: Implement Phase 3
        # - Diplomacy complete
        # - Actors take actions (max 2 major initiatives)
        # - Actors update their goals

        # === POST-TURN ===
        self.logger.info("[POST-TURN] Validating actions, synthesizing narrative, saving state")
        # TODO: Implement post-turn logic
        # - Validate all actions via methods.py
        # - Update metrics
        # - Update relationships
        # - Update fact ledger
        # - Director synthesizes narrative
        # - Save turn state to disk

        self.logger.info(f"Turn {self.current_turn} complete\n")

    def run(self, num_turns: int) -> None:
        """
        Run the simulation for a specified number of turns.

        Args:
            num_turns: Number of turns to simulate
        """
        self.logger.info(f"Starting simulation run: {num_turns} turns")
        self.logger.info(f"Scenario: {self.config.name}")
        self.logger.info(f"Time scale: {self.config.time_scale}")
        self.logger.info(f"Actors: {', '.join(self.config.actors)}\n")

        for turn in range(num_turns):
            self.run_turn()

            # Check for early termination
            # TODO: Implement termination conditions based on outcome_flags

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"SIMULATION COMPLETE")
        self.logger.info(f"{'='*60}\n")
        self.logger.info(f"Total turns: {self.current_turn}")
        self.logger.info(f"Scenario: {self.config.name}")
        self.logger.info(f"Run ID: {self.run_id}")

        # TODO: Save final run summary


class SimulationEngine:
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
        scenario_dir: Path,
        scenario_methods: ScenarioMethods,
        run_id: Optional[str] = None
    ):
        """
        Initialize the simulation engine.

        Args:
            scenario_dir: Path to scenario directory
            scenario_methods: Scenario-specific action methods
            run_id: Optional run identifier (auto-generated if not provided)
        """
        self.scenario_dir = scenario_dir
        self.scenario_methods = scenario_methods
        self.run_id = run_id or generate_run_id()

        # Setup logging
        self.logger = setup_logging(scenario_dir.name, self.run_id)

        # Load configurations
        self.logger.info(f"Loading scenario from: {scenario_dir}")
        self.config = load_scenario_config(scenario_dir)
        self.metrics_config = load_metrics_config(scenario_dir)
        self.events_config = load_events_config(scenario_dir)

        # Load background context
        self.background_context = load_background_context(scenario_dir)
        self.actor_backgrounds = {
            actor: load_actor_background(scenario_dir, actor)
            for actor in self.config.actors
        }

        # Initialize LLM provider
        self.logger.info(f"Initializing LLM provider: {self.config.llm.provider}")
        self.llm_provider = create_provider(self.config.llm)

        # Initialize world state
        self.world_state = self._initialize_world_state()

        # Track actor action points
        self.actor_ap: Dict[str, int] = {}
        self._reset_action_points()

        # Track actor goals
        self.actor_goals: Dict[str, List[str]] = {
            actor: [] for actor in self.config.actors
        }

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

    def run_simulation(self, max_turns: Optional[int] = None) -> None:
        """
        Run the complete simulation.

        Args:
            max_turns: Optional override for max turns
        """
        total_turns = max_turns or self.config.max_turns

        self.logger.info(f"Starting simulation: {total_turns} turns")

        for turn in range(1, total_turns + 1):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"TURN {turn}")
            self.logger.info(f"{'='*60}\n")

            self.run_turn(turn)

            # Check for early termination conditions
            if self._should_terminate():
                self.logger.info("Simulation terminated early due to outcome flags")
                break

        self.logger.info("Simulation complete")
        self._save_run_summary()

    def run_turn(self, turn: int) -> None:
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
        comms_phase_1 = self._run_communication_phase(turn, 1, actor_views, [])
        self.logger.info("[PHASE 1] Complete")

        # === PHASE 2: Response & Final Negotiation ===
        self.logger.info("[PHASE 2] Response & Final Negotiation")
        comms_phase_2 = self._run_communication_phase(
            turn, 2, actor_views, comms_phase_1.messages
        )
        self.logger.info("[PHASE 2] Complete")

        # === PHASE 3: Execution & Goal Adjustment ===
        self.logger.info("[PHASE 3] Execution & Goal Adjustment")
        turn_actions = self._run_execution_phase(
            turn, actor_views, comms_phase_1.messages + comms_phase_2.messages
        )
        self.logger.info("[PHASE 3] Complete")

        # === POST-TURN SYNTHESIS ===
        self.logger.info("[POST-TURN] Starting synthesis")
        self._validate_actions(turn_actions)
        self._execute_actions(turn, turn_actions)
        self._synthesize_narrative(turn, turn_actions)
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
            self.logger.info(f"Event: {event.title}")

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
            event_text = f"\n## Exogenous Event: {event.title}\n\n{event.description}\n"
            self.world_state.narrative_state += event_text

            # Add fact
            from .models import FactLedgerEntry
            self.world_state.fact_ledger.append(
                FactLedgerEntry(
                    timestamp=f"Turn {turn}",
                    fact=f"Event: {event.title}",
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

    def _run_communication_phase(
        self,
        turn: int,
        phase: int,
        actor_views: Dict[str, ActorView],
        previous_messages: List[Message]
    ) -> CommunicationRound:
        """
        Run a communication phase.

        Args:
            turn: Current turn number
            phase: Phase number (1 or 2)
            actor_views: Actor views for this turn
            previous_messages: Messages from previous phase (for phase 2)

        Returns:
            CommunicationRound with all messages
        """
        # TODO: Implement LLM-based communication
        # For MVP, return empty communication round
        self.logger.info(f"Communication phase {phase} (stub)")

        return CommunicationRound(phase=phase, messages=[])

    # === Execution Phase Methods ===

    def _run_execution_phase(
        self,
        turn: int,
        actor_views: Dict[str, ActorView],
        all_messages: List[Message]
    ) -> TurnActions:
        """
        Run the execution phase where actors take actions.

        Args:
            turn: Current turn number
            actor_views: Actor views for this turn
            all_messages: All messages from both communication phases

        Returns:
            TurnActions with all actor actions
        """
        # TODO: Implement LLM-based action generation
        # For MVP, return empty actions
        self.logger.info("Execution phase (stub)")

        return TurnActions(turn=turn, actions=[])

    # === Post-Turn Methods ===

    def _validate_actions(self, turn_actions: TurnActions) -> None:
        """
        Validate all actions before execution.

        Args:
            turn_actions: Actions to validate

        Raises:
            ValueError: If validation fails
        """
        self.logger.info("Validating actions")

        for action in turn_actions.actions:
            is_valid, error_msg = self.scenario_methods.validate_actor_actions(
                action.actor,
                action.function_calls,
                self.world_state
            )

            if not is_valid:
                self.logger.error(f"Validation failed: {error_msg}")
                raise ValueError(f"Action validation failed: {error_msg}")

        self.logger.info("All actions validated")

    def _execute_actions(self, turn: int, turn_actions: TurnActions) -> None:
        """
        Execute all validated actions.

        Args:
            turn: Current turn number
            turn_actions: Actions to execute
        """
        self.logger.info("Executing actions")

        for action in turn_actions.actions:
            self.logger.info(f"Executing {len(action.function_calls)} action(s) for {action.actor}")

            for function_call in action.function_calls:
                try:
                    interpretations = self.scenario_methods.execute_action(
                        action.actor,
                        function_call,
                        self.world_state
                    )

                    # Store interpretations for Director
                    # TODO: Pass to Director for narrative synthesis

                except Exception as e:
                    self.logger.error(f"Action execution failed: {e}")
                    raise

            # Update actor goals
            if action.updated_goals:
                self.actor_goals[action.actor] = action.updated_goals

        self.logger.info("All actions executed")

    def _synthesize_narrative(self, turn: int, turn_actions: TurnActions) -> None:
        """
        Use the Director to synthesize turn narrative.

        Args:
            turn: Current turn number
            turn_actions: Actions that occurred this turn
        """
        # TODO: Implement Director narrative synthesis
        # For MVP, add a simple summary
        self.logger.info("Synthesizing narrative (stub)")

        summary = f"\n## Turn {turn} Summary\n\n"
        summary += f"Actions taken by {len(turn_actions.actions)} actor(s).\n"

        self.world_state.narrative_state += summary

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
            "outcome_flags": self.world_state.outcome_flags,
            "final_metrics": self.world_state.metrics.model_dump()
        }

        summary_path = (
            self.scenario_dir / "runs" / self.run_id / "summary.json"
        )
        save_json(summary, summary_path)

        self.logger.info(f"Run summary saved: {summary_path}")
