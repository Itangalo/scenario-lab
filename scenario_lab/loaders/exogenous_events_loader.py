"""
Loader for exogenous events configuration

Loads exogenous events from YAML files in scenario definition directories.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional, Set
import yaml

from scenario_lab.schemas.exogenous_events import ExogenousEventsConfig
from scenario_lab.services.exogenous_events_manager import ExogenousEventManager

logger = logging.getLogger(__name__)


def load_exogenous_events(
    scenario_path: Path,
    triggered_event_ids: Optional[Set[str]] = None,
    random_seed: Optional[int] = None,
) -> Optional[ExogenousEventManager]:
    """
    Load exogenous events from scenario definition directory

    Args:
        scenario_path: Path to scenario directory (containing definition/ folder)
        triggered_event_ids: Set of event IDs that have already triggered (for resume)
        random_seed: Optional seed for reproducible random events

    Returns:
        ExogenousEventManager instance, or None if no exogenous events file exists

    Raises:
        ValueError: If exogenous events configuration is invalid
        FileNotFoundError: If scenario_path doesn't exist
    """
    # Validate scenario path
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario path not found: {scenario_path}")

    # Look for exogenous-events.yaml in definition directory
    definition_dir = scenario_path / "definition"
    events_file = definition_dir / "exogenous-events.yaml"

    if not events_file.exists():
        logger.debug(f"No exogenous events file found at {events_file}")
        return None

    logger.info(f"Loading exogenous events from {events_file}")

    # Load YAML
    try:
        with open(events_file, 'r') as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in exogenous events file: {e}")
    except Exception as e:
        raise ValueError(f"Error reading exogenous events file: {e}")

    # Validate against schema
    try:
        config = ExogenousEventsConfig(**raw_data)
    except Exception as e:
        raise ValueError(f"Invalid exogenous events configuration: {e}")

    # Create event manager
    event_manager = ExogenousEventManager(
        events=config.exogenous_events,
        triggered_event_ids=triggered_event_ids,
        random_seed=random_seed,
    )

    logger.info(
        f"Loaded {len(config.exogenous_events)} exogenous events: "
        f"{sum(1 for e in config.exogenous_events if e.type == 'trend')} trends, "
        f"{sum(1 for e in config.exogenous_events if e.type == 'random')} random, "
        f"{sum(1 for e in config.exogenous_events if e.type == 'conditional')} conditional, "
        f"{sum(1 for e in config.exogenous_events if e.type == 'scheduled')} scheduled"
    )

    return event_manager
