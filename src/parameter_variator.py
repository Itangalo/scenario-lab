"""
Parameter Variator - Generates scenario variations from batch configuration
"""
import itertools
import copy
from typing import Dict, List, Any, Tuple
import yaml
import os


class ParameterVariator:
    """
    Generates variations of scenario parameters for batch execution
    """

    def __init__(self, base_scenario_path: str, variations_config: List[Dict[str, Any]]):
        """
        Initialize parameter variator

        Args:
            base_scenario_path: Path to base scenario directory
            variations_config: List of variation specifications from batch config
        """
        self.base_scenario_path = base_scenario_path
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

            # Future: Add support for other variation types
            # elif variation_type == 'initial_state_modifier':
            #     ...
            # elif variation_type == 'turn_count':
            #     ...

    def generate_variations(self) -> List[Dict[str, Any]]:
        """
        Generate all combinations of variations

        Returns:
            List of variation dictionaries, each representing a unique parameter combination
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
                'actor': dimension.get('actor')
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

        return ", ".join(parts)

    def _generate_modifications(self, combination: Tuple, metadata: List[Dict]) -> Dict[str, Any]:
        """
        Generate modification dictionary for applying a variation

        Returns:
            Dict with structure: {
                'actor_models': {actor_name: model_name},
                'scenario_overrides': {...},
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
        # Create temp scenario directory
        os.makedirs(temp_scenario_path, exist_ok=True)

        # Copy scenario.yaml
        base_scenario_file = os.path.join(self.base_scenario_path, 'scenario.yaml')
        with open(base_scenario_file, 'r') as f:
            scenario_config = yaml.safe_load(f)

        # Apply scenario-level modifications
        if 'scenario_overrides' in variation['modifications']:
            for key, value in variation['modifications']['scenario_overrides'].items():
                scenario_config[key] = value

        # Write modified scenario.yaml
        temp_scenario_file = os.path.join(temp_scenario_path, 'scenario.yaml')
        with open(temp_scenario_file, 'w') as f:
            yaml.safe_dump(scenario_config, f, default_flow_style=False, sort_keys=False)

        # Copy and modify actor files
        actors_dir = os.path.join(self.base_scenario_path, 'actors')
        temp_actors_dir = os.path.join(temp_scenario_path, 'actors')
        os.makedirs(temp_actors_dir, exist_ok=True)

        # Track which actor modifications were applied
        applied_modifications = set()
        requested_modifications = set(variation['modifications'].get('actor_models', {}).keys())

        if os.path.exists(actors_dir):
            for actor_file in os.listdir(actors_dir):
                if actor_file.endswith('.yaml'):
                    # Load actor config
                    source_path = os.path.join(actors_dir, actor_file)
                    with open(source_path, 'r') as f:
                        actor_config = yaml.safe_load(f)

                    # Apply actor model modifications
                    actor_name = actor_config.get('short_name', actor_config.get('name', ''))
                    if actor_name in variation['modifications'].get('actor_models', {}):
                        new_model = variation['modifications']['actor_models'][actor_name]
                        actor_config['llm_model'] = new_model
                        applied_modifications.add(actor_name)

                    # Write modified actor file
                    dest_path = os.path.join(temp_actors_dir, actor_file)
                    with open(dest_path, 'w') as f:
                        yaml.safe_dump(actor_config, f, default_flow_style=False, sort_keys=False)

        # Warn about modifications that didn't match any actors
        unapplied_modifications = requested_modifications - applied_modifications
        if unapplied_modifications:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Variation {variation['variation_id']}: Actor model modifications for "
                f"{unapplied_modifications} did not match any actors in scenario"
            )

        # Copy other scenario files (metrics.yaml, validation-rules.yaml, etc.)
        for filename in ['metrics.yaml', 'validation-rules.yaml']:
            source = os.path.join(self.base_scenario_path, filename)
            if os.path.exists(source):
                dest = os.path.join(temp_scenario_path, filename)
                with open(source, 'r') as f:
                    content = f.read()
                with open(dest, 'w') as f:
                    f.write(content)

        return temp_scenario_path

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
