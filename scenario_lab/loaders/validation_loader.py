"""
Validation Config Loader for Scenario Lab V2

Loads and validates validation-rules.yaml files using Pydantic schemas.
"""
import yaml
import logging
from pathlib import Path
from typing import Optional

from scenario_lab.schemas.validation import ValidationConfig

logger = logging.getLogger(__name__)


def load_validation_config(validation_file: Path) -> Optional[ValidationConfig]:
    """
    Load and validate validation configuration from YAML file

    Args:
        validation_file: Path to validation-rules.yaml file

    Returns:
        Validated ValidationConfig object, or None if file doesn't exist or is invalid

    Raises:
        ValueError: If YAML is invalid or doesn't match schema
    """
    if not validation_file.exists():
        logger.debug(f"No validation file found at {validation_file}")
        return None

    try:
        with open(validation_file, 'r') as f:
            data = yaml.safe_load(f)

        if not data:
            logger.warning(f"Empty validation file: {validation_file}")
            return None

        # Validate with Pydantic
        config = ValidationConfig(**data)

        logger.info(
            f"Loaded validation config from {validation_file}: "
            f"{len(config.checks)} checks, model={config.validation_model}"
        )
        return config

    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in {validation_file}: {e}")
        raise ValueError(f"Invalid YAML in validation file: {e}")

    except Exception as e:
        logger.error(f"Failed to load validation config from {validation_file}: {e}")
        raise ValueError(f"Invalid validation configuration: {e}")
