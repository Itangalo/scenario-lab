"""
Metrics Config Loader for Scenario Lab V2

Loads and validates metrics.yaml files using Pydantic schemas.
"""
import yaml
import logging
from pathlib import Path
from typing import Optional

from scenario_lab.schemas.metrics import MetricsConfig

logger = logging.getLogger(__name__)


def load_metrics_config(metrics_file: Path) -> Optional[MetricsConfig]:
    """
    Load and validate metrics configuration from YAML file

    Args:
        metrics_file: Path to metrics.yaml file

    Returns:
        Validated MetricsConfig object, or None if file doesn't exist or is invalid

    Raises:
        ValueError: If YAML is invalid or doesn't match schema
    """
    if not metrics_file.exists():
        logger.debug(f"No metrics file found at {metrics_file}")
        return None

    try:
        with open(metrics_file, 'r') as f:
            data = yaml.safe_load(f)

        if not data:
            logger.warning(f"Empty metrics file: {metrics_file}")
            return None

        # Validate with Pydantic
        config = MetricsConfig(**data)

        logger.info(f"Loaded {len(config.metrics)} metrics from {metrics_file}")
        return config

    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in {metrics_file}: {e}")
        raise ValueError(f"Invalid YAML in metrics file: {e}")

    except Exception as e:
        logger.error(f"Failed to load metrics config from {metrics_file}: {e}")
        raise ValueError(f"Invalid metrics configuration: {e}")
