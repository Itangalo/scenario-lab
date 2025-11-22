"""
Metrics Config Loader for Scenario Lab V2

Loads and validates metrics.yaml files using Pydantic schemas.
Includes detection of V1 format with helpful migration guidance.
"""
import yaml
import logging
from pathlib import Path
from typing import Optional

from scenario_lab.schemas.metrics import MetricsConfig

logger = logging.getLogger(__name__)


def _detect_v1_format(data: dict) -> tuple[bool, list[str]]:
    """
    Detect if metrics data is in V1 format and identify V1 indicators.

    Returns:
        Tuple of (is_v1_format, list_of_v1_indicators)
    """
    if not isinstance(data, dict):
        return False, []

    v1_indicators = []

    # V1 has top-level extraction_model
    if "extraction_model" in data:
        v1_indicators.append("top-level 'extraction_model' field (move to extraction.model per metric)")

    # V1 has separate thresholds section
    if "thresholds" in data:
        v1_indicators.append("separate 'thresholds' section (move to warning_threshold/critical_threshold per metric)")

    # Check metrics structure
    metrics = data.get("metrics")

    # V1: metrics is a dict with metric names as keys
    if isinstance(metrics, dict):
        v1_indicators.append("'metrics' is a dictionary (should be a list of metric objects)")

    # V1: metrics is a list but with V1 fields
    if isinstance(metrics, list) and len(metrics) > 0:
        first_metric = metrics[0]
        if isinstance(first_metric, dict):
            if "extraction_type" in first_metric:
                v1_indicators.append("'extraction_type' field (use nested 'extraction.type' instead)")
            if "extraction_prompt" in first_metric:
                v1_indicators.append("'extraction_prompt' field (use nested 'extraction.prompt' instead)")
            if "data_type" in first_metric:
                v1_indicators.append("'data_type' field (use 'type: continuous|categorical|boolean' instead)")
            if "aggregation" in first_metric:
                v1_indicators.append("'aggregation' field (removed in V2, metrics are per-turn)")

    return len(v1_indicators) > 0, v1_indicators


def _format_v1_migration_error(v1_indicators: list[str], file_path: Path) -> str:
    """Format a helpful error message for V1 format detection"""
    lines = [
        f"V1 metrics format detected in {file_path}",
        "",
        "The metrics.yaml file uses V1 format which is no longer supported.",
        "V1 indicators found:",
    ]

    for indicator in v1_indicators:
        lines.append(f"  - {indicator}")

    lines.extend([
        "",
        "To migrate to V2 format:",
        "",
        "  Option 1: Use the automated migration tool:",
        f"    python -m scenario_lab.tools.migrate_metrics {file_path}",
        "",
        "  Option 2: Follow the manual migration guide:",
        "    See docs/METRICS_MIGRATION.md for step-by-step instructions",
        "",
        "Quick reference - V1 to V2 changes:",
        "  - extraction_type → extraction.type",
        "  - extraction_prompt → extraction.prompt",
        "  - data_type: float/integer → type: continuous + range: [min, max]",
        "  - data_type: string → type: categorical + categories: [...]",
        "  - thresholds.metric.warning → metric.warning_threshold",
    ])

    return "\n".join(lines)


def load_metrics_config(metrics_file: Path) -> Optional[MetricsConfig]:
    """
    Load and validate metrics configuration from YAML file

    Args:
        metrics_file: Path to metrics.yaml file

    Returns:
        Validated MetricsConfig object, or None if file doesn't exist or is invalid

    Raises:
        ValueError: If YAML is invalid, uses V1 format, or doesn't match V2 schema
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

        # Check for V1 format and provide helpful migration guidance
        is_v1, v1_indicators = _detect_v1_format(data)
        if is_v1:
            error_message = _format_v1_migration_error(v1_indicators, metrics_file)
            logger.error(f"V1 metrics format detected in {metrics_file}")
            raise ValueError(error_message)

        # Validate with Pydantic
        config = MetricsConfig(**data)

        logger.info(f"Loaded {len(config.metrics)} metrics from {metrics_file}")
        return config

    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in {metrics_file}: {e}")
        raise ValueError(f"Invalid YAML in metrics file: {e}")

    except ValueError:
        # Re-raise ValueError (including V1 format errors) without wrapping
        raise

    except Exception as e:
        logger.error(f"Failed to load metrics config from {metrics_file}: {e}")
        raise ValueError(f"Invalid metrics configuration: {e}")
