"""
Scenario Loader for Scenario Lab V2

Loads scenario and actor configurations from YAML files and creates initial V2 state.
Uses V2 schemas for validation.
"""
from __future__ import annotations
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from scenario_lab.schemas.loader import load_and_validate_scenario
from scenario_lab.loaders.actor_loader import load_all_actors, create_v1_actor_for_migration
from scenario_lab.models.state import ScenarioState, ActorState, WorldState, ScenarioStatus

logger = logging.getLogger(__name__)


class ScenarioLoader:
    """
    Loads scenario configuration from YAML files

    This loader:
    1. Loads and validates scenario.yaml
    2. Loads and validates actor YAML files
    3. Creates V1 Actor objects for phase services
    4. Creates initial V2 ScenarioState
    """

    def __init__(self, scenario_path: str, json_mode: bool = False):
        """
        Initialize scenario loader

        Args:
            scenario_path: Path to scenario directory
            json_mode: Whether to use JSON response format for actors (default: False for V1 compatibility)
        """
        self.scenario_path = Path(scenario_path)
        self.scenario_config: Dict[str, Any] = {}
        self.actors: Dict[str, Any] = {}  # V1 Actor objects temporarily during migration
        self.json_mode = json_mode

    def load(self) -> tuple[ScenarioState, Dict[str, Any], Dict[str, Any]]:
        """
        Load complete scenario configuration

        Returns:
            Tuple of (initial_state, v1_actors, scenario_config)
        """
        logger.info(f"Loading scenario from: {self.scenario_path}")

        # Load scenario configuration
        self.scenario_config = self._load_scenario_config()

        # Load actors
        self.actors = self._load_actors()

        # Create initial V2 state
        initial_state = self._create_initial_state()

        logger.info(
            f"Scenario loaded: {self.scenario_config['name']} with {len(self.actors)} actors"
        )

        return initial_state, self.actors, self.scenario_config

    def _load_scenario_config(self) -> Dict[str, Any]:
        """Load and validate scenario.yaml using V2 schemas"""
        scenario_file = self.scenario_path / "scenario.yaml"

        # Use V2 loader with validation
        scenario_config, validation_result = load_and_validate_scenario(scenario_file)

        if not validation_result.success:
            error_text = (
                f"Invalid scenario configuration in {scenario_file}:\n" +
                "\n".join(f"  - {error}" for error in validation_result.errors)
            )
            logger.error(error_text)
            raise ValueError(error_text)

        # Log warnings if any
        for warning in validation_result.warnings:
            logger.warning(f"Scenario config: {warning}")

        # Return as dict for compatibility
        return scenario_config.model_dump()

    def _load_actors(self) -> Dict[str, Any]:
        """
        Load all actor YAML files and create Actor objects using V2 schemas

        Note: Currently creates V1 Actor objects for compatibility with existing phases.
        Will be updated to V2 Actor in Phase 2.
        """
        actors_dir = self.scenario_path / "actors"
        scenario_system_prompt = self.scenario_config.get("system_prompt", "")

        # Load all actor configs using V2 schemas
        actor_configs = load_all_actors(actors_dir, scenario_system_prompt)

        # Create V1 Actor objects for compatibility (temporary during migration)
        actors = {}
        for short_name, actor_config in actor_configs.items():
            actor = create_v1_actor_for_migration(
                actor_config,
                scenario_system_prompt,
                json_mode=self.json_mode
            )
            actors[short_name] = actor

        return actors

    def _create_initial_state(self) -> ScenarioState:
        """Create initial V2 ScenarioState from loaded configuration"""

        # Create initial world state from scenario config
        initial_world_content = self.scenario_config.get("initial_world_state", "")
        initial_world_state = WorldState(turn=0, content=initial_world_content)

        # Create actor states
        actor_states = {}
        for short_name, actor in self.actors.items():
            actor_state = ActorState(
                name=actor.name,
                short_name=actor.short_name,
                model=actor.llm_model,
                current_goals=actor.goals,
            )
            actor_states[actor.name] = actor_state

        # Generate run_id
        run_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Create initial state
        initial_state = ScenarioState(
            scenario_id=self.scenario_config["name"],
            scenario_name=self.scenario_config["name"],
            run_id=run_id,
            world_state=initial_world_state,
            actors=actor_states,
            status=ScenarioStatus.CREATED,
        )

        return initial_state
