"""
Actor Loader for Scenario Lab V2

Loads actor configurations from YAML files using V2 schemas.
Creates temporary V1 Actor objects during migration period.
"""
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from pydantic import ValidationError

from scenario_lab.schemas.actor import ActorConfig
from scenario_lab.schemas.loader import load_and_validate_actor

logger = logging.getLogger(__name__)


def load_actor_yaml(actor_path: Path) -> Dict[str, Any]:
    """
    Load and validate an actor YAML file using V2 schemas

    Args:
        actor_path: Path to actor YAML file

    Returns:
        Dictionary with validated actor configuration

    Raises:
        FileNotFoundError: If actor file doesn't exist
        ValueError: If YAML is invalid or validation fails
    """
    logger.debug(f"Loading actor from: {actor_path}")

    # Use V2 loader with validation
    actor_config, validation_result = load_and_validate_actor(actor_path)

    if not validation_result.success:
        error_text = (
            f"Invalid actor configuration in {actor_path}:\n" +
            "\n".join(f"  - {error}" for error in validation_result.errors)
        )
        logger.error(error_text)
        raise ValueError(error_text)

    # Log warnings if any
    for warning in validation_result.warnings:
        logger.warning(f"{actor_path.name}: {warning}")

    # Return as dictionary for V1 Actor compatibility
    return actor_config.model_dump()


def load_all_actors(actors_dir: Path, scenario_system_prompt: str = "") -> Dict[str, Dict[str, Any]]:
    """
    Load all actor YAML files from a directory

    Args:
        actors_dir: Path to actors directory
        scenario_system_prompt: Optional system prompt from scenario config

    Returns:
        Dictionary mapping actor short_name to actor config dict

    Raises:
        FileNotFoundError: If actors directory doesn't exist
        ValueError: If no actors found or validation fails
    """
    if not actors_dir.exists():
        raise FileNotFoundError(
            f"Actors directory not found: {actors_dir}\n"
            f"Expected actors/ subdirectory"
        )

    if not actors_dir.is_dir():
        raise ValueError(f"Path is not a directory: {actors_dir}")

    actors = {}

    # Load each actor YAML file
    for actor_file in sorted(actors_dir.glob("*.yaml")):
        try:
            actor_config = load_actor_yaml(actor_file)

            # Store by short name for easy lookup
            short_name = actor_config['short_name']
            actors[short_name] = actor_config

            logger.debug(
                f"  Loaded actor: {actor_config['name']} ({short_name})"
            )

        except Exception as e:
            logger.error(f"Failed to load actor from {actor_file}: {e}")
            raise

    if not actors:
        raise ValueError(
            f"No actors found in {actors_dir}\n"
            f"Expected at least one actor YAML file (*.yaml)"
        )

    logger.info(f"Loaded {len(actors)} actors from {actors_dir}")
    return actors


def create_v1_actor_for_migration(actor_config: Dict[str, Any], scenario_system_prompt: str = "", json_mode: bool = False):
    """
    TEMPORARY: Create V1 Actor object from V2-validated config

    This function bridges V2 schema validation with V1 Actor objects during the migration period.
    It will be removed in Phase 2 when Actor is fully migrated to V2.

    Args:
        actor_config: Actor configuration dict (V2-validated)
        scenario_system_prompt: System prompt from scenario
        json_mode: Whether to use JSON response format

    Returns:
        V1 Actor object

    Note:
        This imports from V1 temporarily. Will be replaced in Phase 2 with V2 Actor.
    """
    import sys
    from pathlib import Path

    # Temporary V1 import (will be removed in Phase 2)
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
    from actor_engine import Actor

    # Create V1 Actor with V2-validated config
    return Actor(actor_config, scenario_system_prompt, json_mode)
