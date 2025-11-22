"""
Batch Configuration - Configuration loading and validation

Handles batch configuration YAML loading, validation, and normalization.
"""
import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional


@dataclass
class BatchConfig:
    """
    Batch execution configuration

    Immutable configuration for batch execution loaded from YAML.
    """
    # Required fields
    experiment_name: str
    base_scenario: str
    output_dir: str

    # Optional fields with defaults
    runs_per_variation: int = 1
    max_parallel: int = 1
    budget_limit: Optional[float] = None
    cost_per_run_limit: Optional[float] = None
    description: Optional[str] = None

    # Variations (normalized to list format)
    variations: List[Dict[str, Any]] = field(default_factory=list)

    # Derived paths
    runs_dir: str = field(init=False)

    def __post_init__(self):
        """Compute derived fields after initialization"""
        self.runs_dir = os.path.join(self.output_dir, 'runs')

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'BatchConfig':
        """
        Create BatchConfig from a dictionary

        Args:
            config: Configuration dictionary

        Returns:
            BatchConfig instance
        """
        # Normalize variations format
        variations = _normalize_variations(config.get('variations', []))

        return cls(
            experiment_name=config['experiment_name'],
            base_scenario=config['base_scenario'],
            output_dir=config['output_dir'],
            runs_per_variation=config.get('runs_per_variation', 1),
            max_parallel=config.get('max_parallel', 1),
            budget_limit=config.get('budget_limit'),
            cost_per_run_limit=config.get('cost_per_run_limit'),
            description=config.get('description'),
            variations=variations
        )


def _normalize_variations(variations_config: Any) -> List[Dict[str, Any]]:
    """
    Normalize variations config to list format

    Supports both list format (preferred) and dict format (legacy).

    Args:
        variations_config: Variations configuration (list or dict)

    Returns:
        Normalized list of variation configs
    """
    if isinstance(variations_config, list):
        return variations_config

    if isinstance(variations_config, dict):
        # Convert dict format to list format
        variations_list = []
        if 'actor_models' in variations_config:
            for actor, models in variations_config['actor_models'].items():
                variations_list.append({
                    'type': 'actor_model',
                    'actor': actor,
                    'values': models
                })
        return variations_list

    return []


def load_batch_config(config_path: str) -> BatchConfig:
    """
    Load and validate batch configuration from YAML file

    Args:
        config_path: Path to batch configuration YAML

    Returns:
        Validated BatchConfig instance

    Raises:
        FileNotFoundError: If config file or base scenario doesn't exist
        ValueError: If required fields are missing
    """
    # Check config file exists
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load YAML
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Validate required fields
    _validate_required_fields(config)

    # Create config object
    batch_config = BatchConfig.from_dict(config)

    # Validate base scenario exists
    if not os.path.exists(batch_config.base_scenario):
        raise FileNotFoundError(f"Base scenario not found: {batch_config.base_scenario}")

    return batch_config


def _validate_required_fields(config: Dict[str, Any]) -> None:
    """
    Validate that all required fields are present

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If a required field is missing
    """
    required = ['experiment_name', 'base_scenario', 'output_dir']
    for field_name in required:
        if field_name not in config:
            raise ValueError(f"Missing required field in config: {field_name}")


def save_config_copy(config: BatchConfig, config_path: str, output_dir: str) -> None:
    """
    Save a copy of the batch configuration to the output directory

    Args:
        config: BatchConfig instance
        config_path: Original config file path
        output_dir: Output directory to save copy to
    """
    config_copy_path = os.path.join(output_dir, 'batch-config.yaml')
    if not os.path.exists(config_copy_path):
        # Read original and copy to output
        with open(config_path, 'r') as f:
            original = yaml.safe_load(f)
        with open(config_copy_path, 'w') as f:
            yaml.dump(original, f, default_flow_style=False)
