"""
Parameter Variator - Generates scenario variations from batch configuration (V2)

Supports Cartesian product generation of parameter combinations for batch execution.

V2 Design:
- No V1 dependencies
- Works with V2 schema validation
- Pure functions for variation generation
"""
import itertools
import copy
from typing import Dict, List, Any, Tuple
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)


class ParameterVariator:
    """
    Generates variations of scenario parameters for batch execution (V2)

    Supports:
    - Actor model variations (different LLM models per actor)
    - Scenario parameter overrides
    - Cartesian product generation for full factorial designs
    """

    def __init__(self, base_scenario_path: str, variations_config: List[Dict[str, Any]]):
        """
        Initialize parameter variator

        Args:
            base_scenario_path: Path to base scenario directory
            variations_config: List of variation specifications from batch config
        """
        self.base_scenario_path = Path(base_scenario_path)
        self.variations_config = variations_config
        self.variation_dimensions = []

        # Parse variations into dimensions
        self._parse_variations()

    def _parse_variations(self):
        """Parse variation configuration into dimensions for combinatorial generation"""
        for variation in self.variations_config:
            variation_type = variation.get('type')

            if variation_type == 'actor_model':
                actor_name = variation.get('actor')
                values = variation.get('values', [])
                self.variation_dimensions.append({
                    'type': 'actor_model',
                    'actor': actor_name,
                    'values': values
                })

            elif variation_type == 'scenario_parameter':
                # Support for scenario-level parameter variations
                parameter_name = variation.get('parameter')
                values = variation.get('values', [])
                self.variation_dimensions.append({
                    'type': 'scenario_parameter',
                    'parameter': parameter_name,
                    'values': values
                })

            # Future: Add support for other variation types
            # elif variation_type == 'initial_state_modifier':
            #     ...
            # elif variation_type == 'turn_count':
            #     ...

    def generate_variations(self) -> List[Dict[str, Any]]:
        """
        Generate all combinations of variations using Cartesian product

        Returns:
            List of variation dictionaries, each representing a unique parameter combination

        Example:
            [
                {
                    'variation_id': 1,
                    'description': 'Actor1=gpt-4o, Actor2=claude-3-haiku',
                    'modifications': {
                        'actor_models': {'Actor1': 'openai/gpt-4o', ...},
                        'scenario_overrides': {}
                    }
                },
                ...
            ]
        """
        if not self.variation_dimensions:
            # No variations specified - return single base configuration
            return [{'variation_id': 1, 'description': 'Base configuration', 'modifications': {}}]

        # Extract values from each dimension
        dimension_values = []
        dimension_metadata = []

        for dimension in self.variation_dimensions:
            dimension_values.append(dimension['values'])
            dimension_metadata.append({
                'type': dimension['type'],
                'actor': dimension.get('actor'),
                'parameter': dimension.get('parameter')
            })

        # Generate all combinations using Cartesian product
        variations = []
        for idx, combination in enumerate(itertools.product(*dimension_values), start=1):
            variation = {
                'variation_id': idx,
                'description': self._generate_description(combination, dimension_metadata),
                'modifications': self._generate_modifications(combination, dimension_metadata)
            }
            variations.append(variation)

        return variations

    def _generate_description(self, combination: Tuple, metadata: List[Dict]) -> str:
        """Generate human-readable description of a variation"""
        parts = []
        for value, meta in zip(combination, metadata):
            if meta['type'] == 'actor_model':
                # Extract short model name (e.g., "gpt-4o-mini" from "openai/gpt-4o-mini")
                model_name = value.split('/')[-1] if '/' in value else value
                parts.append(f"{meta['actor']}={model_name}")
            elif meta['type'] == 'scenario_parameter':
                parts.append(f"{meta['parameter']}={value}")

        return ", ".join(parts)

    def _generate_modifications(self, combination: Tuple, metadata: List[Dict]) -> Dict[str, Any]:
        """
        Generate modification dictionary for applying a variation

        Returns:
            Dict with structure: {
                'actor_models': {actor_name: model_name},
                'scenario_overrides': {param_name: value},
                ...
            }
        """
        modifications = {
            'actor_models': {},
            'scenario_overrides': {}
        }

        for value, meta in zip(combination, metadata):
            if meta['type'] == 'actor_model':
                modifications['actor_models'][meta['actor']] = value
            elif meta['type'] == 'scenario_parameter':
                modifications['scenario_overrides'][meta['parameter']] = value

        return modifications

    def apply_variation_to_scenario(
        self,
        variation: Dict[str, Any],
        temp_scenario_path: str
    ) -> str:
        """
        Apply a variation to the base scenario by creating a modified copy

        Args:
            variation: Variation dictionary from generate_variations()
            temp_scenario_path: Path where temporary modified scenario should be created

        Returns:
            Path to the modified scenario directory
        """
        temp_path = Path(temp_scenario_path)
        temp_path.mkdir(parents=True, exist_ok=True)

        # Copy scenario.yaml
        base_scenario_file = self.base_scenario_path / 'scenario.yaml'
        with open(base_scenario_file, 'r') as f:
            scenario_config = yaml.safe_load(f)

        # Apply scenario-level modifications
        if 'scenario_overrides' in variation['modifications']:
            for key, value in variation['modifications']['scenario_overrides'].items():
                scenario_config[key] = value

        # Write modified scenario.yaml
        temp_scenario_file = temp_path / 'scenario.yaml'
        with open(temp_scenario_file, 'w') as f:
            yaml.safe_dump(scenario_config, f, default_flow_style=False, sort_keys=False)

        # Copy and modify actor files
        actors_dir = self.base_scenario_path / 'actors'
        temp_actors_dir = temp_path / 'actors'
        temp_actors_dir.mkdir(exist_ok=True)

        # Track which actor modifications were applied
        applied_modifications = set()
        requested_modifications = set(variation['modifications'].get('actor_models', {}).keys())

        if actors_dir.exists():
            for actor_file in actors_dir.glob('*.yaml'):
                # Load actor config
                with open(actor_file, 'r') as f:
                    actor_config = yaml.safe_load(f)

                # Apply actor model modifications
                actor_name = actor_config.get('short_name', actor_config.get('name', ''))
                if actor_name in variation['modifications'].get('actor_models', {}):
                    new_model = variation['modifications']['actor_models'][actor_name]
                    actor_config['llm_model'] = new_model
                    applied_modifications.add(actor_name)

                # Write modified actor file
                dest_path = temp_actors_dir / actor_file.name
                with open(dest_path, 'w') as f:
                    yaml.safe_dump(actor_config, f, default_flow_style=False, sort_keys=False)

        # Warn about modifications that didn't match any actors
        unapplied_modifications = requested_modifications - applied_modifications
        if unapplied_modifications:
            logger.warning(
                f"Variation {variation['variation_id']}: Actor model modifications for "
                f"{unapplied_modifications} did not match any actors in scenario"
            )

        # Copy other scenario files (metrics.yaml, validation-rules.yaml, etc.)
        for filename in ['metrics.yaml', 'validation-rules.yaml']:
            source = self.base_scenario_path / filename
            if source.exists():
                dest = temp_path / filename
                with open(source, 'r') as f:
                    content = f.read()
                with open(dest, 'w') as f:
                    f.write(content)

        return str(temp_path)

    def get_variation_count(self) -> int:
        """
        Get total number of variations that will be generated

        Returns:
            Number of unique variations
        """
        if not self.variation_dimensions:
            return 1

        count = 1
        for dimension in self.variation_dimensions:
            count *= len(dimension['values'])

        return count

    def estimate_total_runs(self, runs_per_variation: int) -> int:
        """
        Estimate total number of runs for a batch

        Args:
            runs_per_variation: Number of times each variation will be run

        Returns:
            Total number of scenario runs
        """
        return self.get_variation_count() * runs_per_variation
