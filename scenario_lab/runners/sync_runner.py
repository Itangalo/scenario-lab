"""
Synchronous Runner for Scenario Lab V2

Pure V2 implementation using V2 phases and components.
"""
from __future__ import annotations
import os
import logging
import yaml
from pathlib import Path
from typing import Optional

from scenario_lab.loaders import ScenarioLoader, load_metrics_config, load_validation_config
from scenario_lab.core.orchestrator import ScenarioOrchestrator, PhaseType
from scenario_lab.core.events import EventBus
from scenario_lab.core.metrics_tracker_v2 import MetricsTrackerV2
from scenario_lab.core.qa_validator_v2 import QAValidatorV2
from scenario_lab.services.communication_phase import CommunicationPhase
from scenario_lab.services.decision_phase_v2 import DecisionPhaseV2
from scenario_lab.services.world_update_phase_v2 import WorldUpdatePhaseV2
from scenario_lab.services.persistence_phase import PersistencePhase
from scenario_lab.services.database_persistence_phase import DatabasePersistencePhase
from scenario_lab.models.state import ScenarioState
from scenario_lab.utils.state_persistence import StatePersistence

try:
    from scenario_lab.database import Database
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    Database = None

logger = logging.getLogger(__name__)


class SyncRunner:
    """
    Synchronous runner using pure V2 components

    This runner:
    1. Loads scenario configuration
    2. Initializes V2 components and phases
    3. Wires phases to orchestrator
    4. Executes scenario using V2 pipeline
    """

    def __init__(
        self,
        scenario_path: str,
        output_path: Optional[str] = None,
        end_turn: Optional[int] = None,
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
            end_turn: Turn number to stop at (e.g., end_turn=5 stops after turn 5)
            credit_limit: Maximum cost in USD
            database: Optional Database instance for persistence
            resume_from: Path to run directory to resume from
            branch_from: Path to run directory to branch from
            branch_at_turn: Turn number to branch at (required with branch_from)
            json_mode: Whether to use JSON response format for actors (default: False)
        """
        self.scenario_path = scenario_path
        self.output_path = output_path or self._default_output_path()
        self.end_turn = end_turn
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

        # V2 components
        self.event_bus: Optional[EventBus] = None
        self.orchestrator: Optional[ScenarioOrchestrator] = None
        self.metrics_tracker: Optional[MetricsTrackerV2] = None
        self.qa_validator: Optional[QAValidatorV2] = None

    def _default_output_path(self) -> str:
        """
        Generate default output path with auto-incrementing run number

        Finds the next available run-XXX directory number.
        """
        scenario_name = Path(self.scenario_path).name
        base_dir = Path(f"output/{scenario_name}")

        # If base directory doesn't exist, use run-001
        if not base_dir.exists():
            return f"output/{scenario_name}/run-001"

        # Find existing run directories
        existing_runs = []
        for path in base_dir.iterdir():
            if path.is_dir() and path.name.startswith("run-"):
                try:
                    run_num = int(path.name.split("-")[1])
                    existing_runs.append(run_num)
                except (ValueError, IndexError):
                    continue

        # Get next run number
        if not existing_runs:
            next_run = 1
        else:
            next_run = max(existing_runs) + 1

        return f"output/{scenario_name}/run-{next_run:03d}"

    def setup(self) -> None:
        """Setup all components"""
        logger.info("Setting up Scenario Lab V2 runner...")

        # Create output directory
        os.makedirs(self.output_path, exist_ok=True)

        # Set run-scoped cache: Use output_path as unique run identifier
        # This ensures each run gets its own cache directory, preventing
        # different runs from sharing cached responses (which would give identical results)
        run_id = self.output_path.replace('/', '_').replace('\\', '_')
        os.environ['SCENARIO_RUN_ID'] = run_id
        logger.debug(f"Set SCENARIO_RUN_ID={run_id} for run-scoped cache")

        # Reset global cache to pick up new run_id
        from scenario_lab.utils.response_cache import reset_global_cache
        reset_global_cache()

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

        # Initialize V2 components
        self._init_v2_components()

        # Wire phases to orchestrator
        self._wire_phases()

        logger.info("Setup complete")

    def _init_v2_components(self) -> None:
        """Initialize V2 components"""

        # Event bus
        self.event_bus = EventBus(keep_history=True)

        # Orchestrator
        self.orchestrator = ScenarioOrchestrator(
            event_bus=self.event_bus,
            end_turn=self.end_turn or self.scenario_config.get("num_turns", 10),
            credit_limit=self.credit_limit,
            output_dir=self.output_path,
            save_state_every_turn=True,
        )

        # Metrics tracker V2 (if metrics.yaml exists)
        metrics_file = Path(self.scenario_path) / "metrics.yaml"
        metrics_config = load_metrics_config(metrics_file)
        if metrics_config:
            api_key = os.getenv("OPENROUTER_API_KEY", "")
            self.metrics_tracker = MetricsTrackerV2(
                metrics_config=metrics_config,
                api_key=api_key
            )
        else:
            self.metrics_tracker = None

        # QA validator V2 (if validation-rules.yaml exists)
        validation_file = Path(self.scenario_path) / "validation-rules.yaml"
        validation_config = load_validation_config(validation_file)
        if validation_config:
            api_key = os.getenv("OPENROUTER_API_KEY", "")
            self.qa_validator = QAValidatorV2(
                validation_config=validation_config,
                api_key=api_key
            )
        else:
            self.qa_validator = None

    def _wire_phases(self) -> None:
        """Wire phase services to orchestrator"""

        # Communication phase (V2)
        communication_phase = CommunicationPhase(
            output_dir=self.output_path,
        )
        self.orchestrator.register_phase(PhaseType.COMMUNICATION, communication_phase)

        # Decision phase (V2)
        # Convert actors dict to actor_configs dict (V2 Actor → dict)
        actor_configs = {}
        for short_name, actor in self.actors.items():
            # Actor is a V2 Actor dataclass, convert to dict for DecisionPhaseV2
            actor_configs[short_name] = {
                "name": actor.name,
                "short_name": actor.short_name,
                "llm_model": actor.llm_model,
                "system_prompt": actor.system_prompt,
                "description": actor.description,
                "goals": actor.goals,
                "constraints": actor.constraints,
                "expertise": actor.expertise,
                "decision_style": actor.decision_style,
            }

        decision_phase = DecisionPhaseV2(
            actor_configs=actor_configs,
            scenario_system_prompt=self.scenario_config.get("system_prompt", ""),
            output_dir=self.output_path,
            json_mode=self.json_mode,
            context_window_size=self.scenario_config.get("context_window", 3),
            metrics_tracker=self.metrics_tracker,
        )
        self.orchestrator.register_phase(PhaseType.DECISION, decision_phase)

        # World update phase (V2)
        world_state_model = self.scenario_config.get(
            "world_state_model", "openai/gpt-4o-mini"
        )
        world_update_phase = WorldUpdatePhaseV2(
            scenario_name=self.scenario_config["name"],
            world_state_model=world_state_model,
            output_dir=self.output_path,
            metrics_tracker=self.metrics_tracker,
            qa_validator=self.qa_validator,
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
