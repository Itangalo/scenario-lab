"""
Utility functions for Scenario Lab V3.

Includes file loading, logging, and directory management helpers.
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .models import (
    ScenarioConfig,
    MetricsConfig,
    EventsConfig,
    WorldState,
    ActorView,
    TurnState,
    Metrics,
    ActorMetricsData,
)


# === Logging Setup ===

def setup_logging(scenario_name: str, run_id: str, log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Setup logging for a simulation run.

    Args:
        scenario_name: Name of the scenario
        run_id: Unique identifier for this run
        log_dir: Optional directory for logs (default: scenario/runs/run_id/)

    Returns:
        Configured logger instance
    """
    if log_dir is None:
        log_dir = Path(scenario_name) / "runs" / run_id

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "simulation.log"

    # Create logger
    logger = logging.getLogger(f"scenario_lab.{run_id}")
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers to prevent duplication
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # File handler (detailed)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler (less verbose)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# === File Loading ===

def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_markdown(file_path: Path) -> str:
    """Load a markdown file as text."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_scenario_config(scenario_dir: Path) -> ScenarioConfig:
    """Load scenario configuration from scenario.yaml."""
    config_path = scenario_dir / "scenario.yaml"
    data = load_yaml(config_path)
    return ScenarioConfig(**data)


def load_metrics_config(scenario_dir: Path) -> MetricsConfig:
    """Load metrics configuration from metrics.yaml."""
    config_path = scenario_dir / "metrics.yaml"
    data = load_yaml(config_path)
    return MetricsConfig(**data)


def parse_enhanced_metrics(data: dict):
    """
    Parse enhanced metrics format and extract values + metadata.

    Handles both simple (value only) and enhanced (value + metadata) formats.

    Args:
        data: Raw YAML data from metrics.yaml

    Returns:
        Tuple of (metrics_dict, metadata_registry)
        - metrics_dict: Simple {key: value} dict for MetricsConfig
        - metadata_registry: Dict mapping metric paths to MetricMetadata
    """
    from .models import MetricMetadata, ChangeMagnitude, MetricDependency

    metrics_dict = {}
    metadata_registry = {}

    def parse_metric_value(path: str, value_data):
        """Parse a single metric, handling both simple and enhanced formats."""
        if isinstance(value_data, (int, float)):
            # Simple format: just a number
            return float(value_data), None

        if isinstance(value_data, dict):
            # Enhanced format: extract value and metadata
            if "value" not in value_data:
                # Not enhanced format, could be nested dict
                return value_data, None

            metric_value = value_data["value"]

            # Extract metadata fields
            metadata_fields = {}
            if "min" in value_data:
                metadata_fields["min"] = value_data["min"]
            if "max" in value_data:
                metadata_fields["max"] = value_data["max"]
            if "unit" in value_data:
                metadata_fields["unit"] = value_data["unit"]
            if "description" in value_data:
                metadata_fields["description"] = value_data["description"]
            if "randomness" in value_data:
                metadata_fields["randomness"] = value_data["randomness"]

            # Parse change_magnitudes
            if "change_magnitudes" in value_data:
                cm_data = value_data["change_magnitudes"]
                metadata_fields["change_magnitudes"] = ChangeMagnitude(
                    small=tuple(cm_data.get("small", [0.01, 0.05])),
                    medium=tuple(cm_data.get("medium", [0.05, 0.15])),
                    large=tuple(cm_data.get("large", [0.15, 0.5])),
                )

            # Parse dependencies
            if "dependencies" in value_data:
                deps = []
                for dep_data in value_data["dependencies"]:
                    deps.append(MetricDependency(**dep_data))
                metadata_fields["dependencies"] = deps

            metadata = MetricMetadata(**metadata_fields) if metadata_fields else None
            return float(metric_value), metadata

        return value_data, None

    # Parse world metrics
    world_metrics = {}
    if "world" in data:
        for key, value in data["world"].items():
            metric_path = f"world.{key}"
            parsed_value, metadata = parse_metric_value(metric_path, value)
            world_metrics[key] = parsed_value
            if metadata:
                metadata_registry[metric_path] = metadata

    metrics_dict["world"] = world_metrics

    # Parse actor metrics
    from .models import ActorMetricsData
    actors_dict = {}

    if "actors" in data:
        for actor_name, actor_data in data["actors"].items():
            actor_metrics = ActorMetricsData()

            # Parse public metrics
            if "public" in actor_data:
                for key, value in actor_data["public"].items():
                    metric_path = f"actors.{actor_name}.public.{key}"
                    parsed_value, metadata = parse_metric_value(metric_path, value)
                    actor_metrics.public[key] = parsed_value
                    if metadata:
                        metadata_registry[metric_path] = metadata

            # Parse private metrics
            if "private" in actor_data:
                for key, value in actor_data["private"].items():
                    metric_path = f"actors.{actor_name}.private.{key}"
                    parsed_value, metadata = parse_metric_value(metric_path, value)
                    actor_metrics.private[key] = parsed_value
                    if metadata:
                        metadata_registry[metric_path] = metadata

            actors_dict[actor_name] = actor_metrics

    metrics_dict["actors"] = actors_dict

    return metrics_dict, metadata_registry


def load_events_config(scenario_dir: Path) -> EventsConfig:
    """Load events configuration from events.yaml."""
    config_path = scenario_dir / "events.yaml"
    data = load_yaml(config_path)
    return EventsConfig(**data)


def load_background_context(scenario_dir: Path) -> str:
    """Load background context from background/context.md."""
    context_path = scenario_dir / "background" / "context.md"
    return load_markdown(context_path)


def load_actor_background(scenario_dir: Path, actor_name: str) -> str:
    """Load actor-specific background from background/actors/{actor}.md."""
    actor_path = scenario_dir / "background" / "actors" / f"{actor_name}.md"
    return load_markdown(actor_path)


# === File Saving ===

def save_json(data: Any, file_path: Path, indent: int = 2) -> None:
    """Save data as JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, default=str)


def save_markdown(content: str, file_path: Path) -> None:
    """Save content as markdown file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


# === Turn Directory Management ===

def create_turn_directory(scenario_dir: Path, run_id: str, turn: int) -> Path:
    """Create and return the directory for a specific turn."""
    turn_dir = scenario_dir / "runs" / run_id / f"turn-{turn:02d}"
    turn_dir.mkdir(parents=True, exist_ok=True)

    # Create views subdirectory
    (turn_dir / "views").mkdir(exist_ok=True)

    return turn_dir


def save_turn_state(
    scenario_dir: Path,
    run_id: str,
    turn: int,
    world_state: WorldState,
    actor_views: Dict[str, ActorView],
    comms_phase_1: Any,
    comms_phase_2: Any,
    actions: Any,
) -> None:
    """
    Save all state for a turn to disk.

    Saves:
    - world_state.md (narrative)
    - metrics.json
    - relationships.json
    - fact_ledger.json
    - views/{actor}.json for each actor
    - comms_phase_1.json
    - comms_phase_2.json
    - actions.json
    """
    turn_dir = create_turn_directory(scenario_dir, run_id, turn)

    # Save world state narrative
    save_markdown(world_state.narrative_state, turn_dir / "world_state.md")

    # Save metrics
    save_json(world_state.metrics.model_dump(), turn_dir / "metrics.json")

    # Save relationships
    relationships_dict = {
        key: rel.model_dump() for key, rel in world_state.relationship_state.items()
    }
    save_json(relationships_dict, turn_dir / "relationships.json")

    # Save fact ledger
    fact_ledger_list = [entry.model_dump() for entry in world_state.fact_ledger]
    save_json(fact_ledger_list, turn_dir / "fact_ledger.json")

    # Save actor views
    for actor_name, view in actor_views.items():
        save_json(view.model_dump(), turn_dir / "views" / f"{actor_name}.json")

    # Save communications
    save_json(comms_phase_1.model_dump(), turn_dir / "comms_phase_1.json")
    save_json(comms_phase_2.model_dump(), turn_dir / "comms_phase_2.json")

    # Save actions
    save_json(actions.model_dump(), turn_dir / "actions.json")


# === Run Management ===

def generate_run_id() -> str:
    """Generate a unique run ID based on timestamp."""
    return f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def create_run_directory(scenario_dir: Path, run_id: str) -> Path:
    """Create and return the directory for a simulation run."""
    run_dir = scenario_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


# === Metrics Filtering ===

def get_visible_metrics(
    full_metrics: Metrics,
    actor_name: str
) -> Metrics:
    """
    Filter metrics to show only what an actor can see.

    Rules:
    - World metrics: visible to all
    - Actor's own private metrics: visible
    - Actor's own public metrics: visible
    - Other actors' public metrics: visible
    - Other actors' private metrics: NOT visible

    Args:
        full_metrics: Complete Metrics object
        actor_name: Name of the actor viewing the metrics

    Returns:
        Filtered Metrics object
    """
    # Create new metrics object with visible data
    visible = Metrics(
        world=full_metrics.world.copy(),
        actors={}
    )

    for actor, actor_metrics in full_metrics.actors.items():
        if actor == actor_name:
            # Own actor: see both private and public
            visible.actors[actor] = ActorMetricsData(
                private=actor_metrics.private.copy(),
                public=actor_metrics.public.copy()
            )
        else:
            # Other actors: only see public
            visible.actors[actor] = ActorMetricsData(
                private={},  # No access to private metrics
                public=actor_metrics.public.copy()
            )

    return visible


# === Prompt Loading ===

def load_prompt_template(prompt_name: str) -> str:
    """
    Load a prompt template from the prompts directory.

    Args:
        prompt_name: Name of the prompt file (without .md extension)

    Returns:
        Prompt template as string
    """
    # Look for prompts in the package directory
    package_dir = Path(__file__).parent
    prompt_path = package_dir / "prompts" / f"{prompt_name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")

    return load_markdown(prompt_path)
