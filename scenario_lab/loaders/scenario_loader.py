"""
Scenario Loader for Scenario Lab V2

Loads scenario and actor configurations from YAML files and creates initial V2 state.
"""
from __future__ import annotations
import sys
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add V1 src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from actor_engine import Actor, load_actor
from schemas import load_scenario_config, load_actor_config
from pydantic import ValidationError

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

    def __init__(self, scenario_path: str):
        """
        Initialize scenario loader

        Args:
            scenario_path: Path to scenario directory
        """
        self.scenario_path = Path(scenario_path)
        self.scenario_config: Dict[str, Any] = {}
        self.actors: Dict[str, Actor] = {}

    def load(self) -> tuple[ScenarioState, Dict[str, Actor], Dict[str, Any]]:
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
        """Load and validate scenario.yaml"""
        scenario_file = self.scenario_path / "scenario.yaml"

        try:
            if not scenario_file.exists():
                raise FileNotFoundError(
                    f"Scenario file not found: {scenario_file}\n"
                    f"Expected scenario.yaml in {self.scenario_path}"
                )

            with open(scenario_file, "r") as f:
                yaml_data = yaml.safe_load(f)

            # Validate using Pydantic schema
            scenario_config = load_scenario_config(yaml_data)

            # Return as dict
            return scenario_config.dict()

        except FileNotFoundError as e:
            logger.error(f"Scenario file not found: {scenario_file}")
            raise

        except ValidationError as e:
            # Format Pydantic validation errors nicely
            error_messages = []
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                message = error["msg"]
                error_messages.append(f"  - {field}: {message}")

            error_text = (
                f"Invalid scenario configuration in {scenario_file}:\n"
                + "\n".join(error_messages)
            )

            logger.error(error_text)
            raise ValueError(error_text) from e

        except yaml.YAMLError as e:
            error_text = f"Invalid YAML syntax in {scenario_file}:\n{str(e)}"
            logger.error(error_text)
            raise ValueError(error_text) from e

    def _load_actors(self) -> Dict[str, Actor]:
        """Load all actor YAML files and create Actor objects"""
        actors_dir = self.scenario_path / "actors"

        if not actors_dir.exists():
            raise FileNotFoundError(
                f"Actors directory not found: {actors_dir}\n"
                f"Expected actors/ subdirectory in {self.scenario_path}"
            )

        actors = {}
        scenario_system_prompt = self.scenario_config.get("system_prompt", "")

        # Load each actor YAML file
        for actor_file in actors_dir.glob("*.yaml"):
            try:
                logger.debug(f"Loading actor from: {actor_file}")

                # Use V1's load_actor function
                actor = load_actor(str(actor_file), scenario_system_prompt)

                # Store by short name for easy lookup
                actors[actor.short_name] = actor

                logger.debug(f"  Loaded actor: {actor.name} ({actor.short_name})")

            except ValidationError as e:
                # Format Pydantic validation errors nicely
                error_messages = []
                for error in e.errors():
                    field = ".".join(str(x) for x in error["loc"])
                    message = error["msg"]
                    error_messages.append(f"    - {field}: {message}")

                error_text = (
                    f"Invalid actor configuration in {actor_file}:\n"
                    + "\n".join(error_messages)
                )

                logger.error(error_text)
                raise ValueError(error_text) from e

            except Exception as e:
                logger.error(f"Failed to load actor from {actor_file}: {e}")
                raise

        if not actors:
            raise ValueError(
                f"No actors found in {actors_dir}\n"
                f"Expected at least one actor YAML file in actors/ subdirectory"
            )

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
                goals=actor.goals,
                constraints=actor.constraints,
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
            scenario_config=self.scenario_config,
            status=ScenarioStatus.INITIALIZED,
        )

        return initial_state
