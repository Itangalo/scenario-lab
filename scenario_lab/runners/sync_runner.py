"""
Synchronous Runner for Scenario Lab V2

Wires together all V1 components with V2 architecture to execute scenarios.
"""
from __future__ import annotations
import sys
import os
import logging
from pathlib import Path
from typing import Optional

# Add V1 src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from world_state import WorldState as V1WorldState
from world_state_updater import WorldStateUpdater
from context_manager import ContextManager
from communication_manager import CommunicationManager
from cost_tracker import CostTracker
from metrics_tracker import MetricsTracker
from qa_validator import QAValidator
from exogenous_events import ExogenousEventManager
import yaml

from scenario_lab.loaders import ScenarioLoader
from scenario_lab.core.orchestrator import ScenarioOrchestrator, PhaseType
from scenario_lab.core.events import EventBus
from scenario_lab.services.communication_phase import CommunicationPhase
from scenario_lab.services.decision_phase import DecisionPhase
from scenario_lab.services.world_update_phase import WorldUpdatePhase
from scenario_lab.services.persistence_phase import PersistencePhase
from scenario_lab.services.database_persistence_phase import DatabasePersistencePhase
from scenario_lab.models.state import ScenarioState
from scenario_lab.database import Database
from scenario_lab.utils.state_persistence import StatePersistence

logger = logging.getLogger(__name__)


class SyncRunner:
    """
    Synchronous runner that wires V1 and V2 components together

    This runner:
    1. Loads scenario configuration
    2. Initializes V1 components (for backwards compatibility)
    3. Initializes V2 phase services
    4. Wires phases to orchestrator
    5. Executes scenario
    """

    def __init__(
        self,
        scenario_path: str,
        output_path: Optional[str] = None,
        max_turns: Optional[int] = None,
        credit_limit: Optional[float] = None,
        database: Optional[Database] = None,
        resume_from: Optional[str] = None,
        branch_from: Optional[str] = None,
        branch_at_turn: Optional[int] = None,
        json_mode: bool = False,
    ):
        """
        Initialize sync runner

        Args:
            scenario_path: Path to scenario directory
            output_path: Path to output directory
            max_turns: Maximum number of turns to execute
            credit_limit: Maximum cost in USD
            database: Optional Database instance for persistence
            resume_from: Path to run directory to resume from
            branch_from: Path to run directory to branch from
            branch_at_turn: Turn number to branch at (required with branch_from)
            json_mode: Whether to use JSON response format for actors (default: False)
        """
        self.scenario_path = scenario_path
        self.output_path = output_path or self._default_output_path()
        self.max_turns = max_turns
        self.credit_limit = credit_limit
        self.database = database
        self.resume_from = resume_from
        self.branch_from = branch_from
        self.branch_at_turn = branch_at_turn
        self.json_mode = json_mode

        # Will be initialized in setup()
        self.loader: Optional[ScenarioLoader] = None
        self.initial_state: Optional[ScenarioState] = None
        self.scenario_config: Optional[dict] = None
        self.actors: Optional[dict] = None

        # V1 components
        self.v1_world_state: Optional[V1WorldState] = None
        self.context_manager: Optional[ContextManager] = None
        self.communication_manager: Optional[CommunicationManager] = None
        self.world_state_updater: Optional[WorldStateUpdater] = None
        self.cost_tracker: Optional[CostTracker] = None
        self.metrics_tracker: Optional[MetricsTracker] = None
        self.qa_validator: Optional[QAValidator] = None
        self.exogenous_event_manager: Optional[ExogenousEventManager] = None

        # V2 components
        self.event_bus: Optional[EventBus] = None
        self.orchestrator: Optional[ScenarioOrchestrator] = None

    def _default_output_path(self) -> str:
        """Generate default output path"""
        scenario_name = Path(self.scenario_path).name
        return f"output/{scenario_name}/run-001"

    def setup(self) -> None:
        """Setup all components"""
        logger.info("Setting up Scenario Lab V2 runner...")

        # Create output directory
        os.makedirs(self.output_path, exist_ok=True)

        # Load scenario configuration
        self.loader = ScenarioLoader(self.scenario_path, json_mode=self.json_mode)
        self.initial_state, self.actors, self.scenario_config = self.loader.load()

        # Handle resume/branch modes
        if self.resume_from:
            logger.info(f"Resuming from {self.resume_from}")
            self._load_resume_state()
        elif self.branch_from:
            logger.info(f"Branching from {self.branch_from} at turn {self.branch_at_turn}")
            self._load_branch_state()

        # Initialize V1 components
        self._init_v1_components()

        # Initialize V2 components
        self._init_v2_components()

        # Wire phases to orchestrator
        self._wire_phases()

        logger.info("Setup complete")

    def _init_v1_components(self) -> None:
        """Initialize V1 components for backwards compatibility"""

        # World state
        self.v1_world_state = V1WorldState(
            initial_state=self.scenario_config["initial_world_state"]
        )

        # Communication manager
        actor_names = [actor.name for actor in self.actors.values()]
        self.communication_manager = CommunicationManager(actor_names)

        # Context manager
        self.context_manager = ContextManager(
            context_window_turns=self.scenario_config.get("context_window", 3)
        )

        # World state updater
        world_state_model = self.scenario_config.get(
            "world_state_model", "alibaba/tongyi-deepresearch-30b-a3b:free"
        )
        self.world_state_updater = WorldStateUpdater(model=world_state_model)

        # Cost tracker
        self.cost_tracker = CostTracker()

        # Metrics tracker (if metrics.yaml exists)
        metrics_file = Path(self.scenario_path) / "metrics.yaml"
        if metrics_file.exists():
            with open(metrics_file, "r") as f:
                metrics_config = yaml.safe_load(f)
            self.metrics_tracker = MetricsTracker(metrics_config)
        else:
            self.metrics_tracker = MetricsTracker({"metrics": []})

        # QA validator (if validation-rules.yaml exists)
        validation_file = Path(self.scenario_path) / "validation-rules.yaml"
        if validation_file.exists():
            self.qa_validator = QAValidator(validation_file_path=str(validation_file))
        else:
            self.qa_validator = QAValidator()

        # Exogenous events manager (if exogenous-events.yaml exists)
        events_file = Path(self.scenario_path) / "exogenous-events.yaml"
        if events_file.exists():
            with open(events_file, "r") as f:
                events_data = yaml.safe_load(f)
            events_config = events_data.get("exogenous_events", [])
            self.exogenous_event_manager = ExogenousEventManager(events_config)
        else:
            self.exogenous_event_manager = None

    def _init_v2_components(self) -> None:
        """Initialize V2 components"""

        # Event bus
        self.event_bus = EventBus(keep_history=True)

        # Orchestrator
        self.orchestrator = ScenarioOrchestrator(
            event_bus=self.event_bus,
            max_turns=self.max_turns or self.scenario_config.get("num_turns", 10),
            credit_limit=self.credit_limit,
            output_dir=self.output_path,
            save_state_every_turn=True,
        )

    def _wire_phases(self) -> None:
        """Wire phase services to orchestrator"""

        # Communication phase
        communication_phase = CommunicationPhase(
            actors=self.actors,
            context_manager=self.context_manager,
            v1_world_state=self.v1_world_state,
            communication_manager=self.communication_manager,
            cost_tracker=self.cost_tracker,
        )
        self.orchestrator.register_phase(PhaseType.COMMUNICATION, communication_phase)

        # Decision phase
        decision_phase = DecisionPhase(
            actors=self.actors,
            context_manager=self.context_manager,
            v1_world_state=self.v1_world_state,
            communication_manager=self.communication_manager,
            metrics_tracker=self.metrics_tracker,
            qa_validator=self.qa_validator,
            output_dir=self.output_path,
        )
        self.orchestrator.register_phase(PhaseType.DECISION, decision_phase)

        # World update phase
        world_update_phase = WorldUpdatePhase(
            world_state_updater=self.world_state_updater,
            v1_world_state=self.v1_world_state,
            scenario_name=self.scenario_config["name"],
            world_state_model=self.scenario_config.get(
                "world_state_model", "alibaba/tongyi-deepresearch-30b-a3b:free"
            ),
            metrics_tracker=self.metrics_tracker,
            qa_validator=self.qa_validator,
            exogenous_event_manager=self.exogenous_event_manager,
            output_dir=self.output_path,
        )
        self.orchestrator.register_phase(PhaseType.WORLD_UPDATE, world_update_phase)

        # File persistence phase (always enabled)
        persistence_phase = PersistencePhase(output_dir=self.output_path)
        self.orchestrator.register_phase(PhaseType.PERSISTENCE, persistence_phase)

        # Database persistence phase (optional)
        if self.database:
            logger.info("Database persistence enabled")
            db_persistence_phase = DatabasePersistencePhase(database=self.database)
            # Use a custom phase type for database persistence
            self.orchestrator.register_phase("database_persistence", db_persistence_phase)

    async def run(self) -> ScenarioState:
        """
        Run the scenario

        Returns:
            Final scenario state
        """
        logger.info(f"Starting scenario execution: {self.scenario_config['name']}")

        # Setup if not already done
        if not self.orchestrator:
            self.setup()

        # Execute scenario
        final_state = await self.orchestrator.execute(self.initial_state)

        logger.info(
            f"Scenario execution complete: {final_state.turn} turns, "
            f"${final_state.total_cost():.2f} total cost"
        )

        return final_state

    def _load_resume_state(self) -> None:
        """Load state for resuming from a previous run"""
        state_file = Path(self.resume_from) / "scenario-state-v2.json"
        if not state_file.exists():
            raise FileNotFoundError(
                f"State file not found: {state_file}\n"
                f"Cannot resume from {self.resume_from}"
            )

        # Load the state
        loaded_state = StatePersistence.load_state(str(state_file))

        # Override initial state
        self.initial_state = loaded_state
        logger.info(f"Loaded resume state from turn {loaded_state.turn}")

    def _load_branch_state(self) -> None:
        """Load state for branching from a previous run"""
        if self.branch_at_turn is None:
            raise ValueError("branch_at_turn must be specified when branching")

        state_file = Path(self.branch_from) / "scenario-state-v2.json"
        if not state_file.exists():
            raise FileNotFoundError(
                f"State file not found: {state_file}\n"
                f"Cannot branch from {self.branch_from}"
            )

        # Create branched state
        branched_state = StatePersistence.create_branch(
            source_state_file=str(state_file),
            branch_at_turn=self.branch_at_turn,
            new_output_dir=self.output_path,
        )

        # Override initial state
        self.initial_state = branched_state
        logger.info(
            f"Created branch from {self.branch_from} at turn {self.branch_at_turn}"
        )
