"""
Tests for scenario creation wizard
"""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import yaml

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from create_scenario import (
    Colors, print_header, ask_question, ask_yes_no,
    get_common_models, select_model
)


class TestScenarioWizardHelpers(unittest.TestCase):
    """Test helper functions"""

    def test_colors_defined(self):
        """Test that color codes are defined"""
        self.assertTrue(hasattr(Colors, 'BLUE'))
        self.assertTrue(hasattr(Colors, 'GREEN'))
        self.assertTrue(hasattr(Colors, 'RED'))
        self.assertTrue(hasattr(Colors, 'YELLOW'))
        self.assertTrue(hasattr(Colors, 'BOLD'))
        self.assertTrue(hasattr(Colors, 'END'))

    def test_get_common_models(self):
        """Test that common models are returned"""
        models = get_common_models()
        self.assertIsInstance(models, dict)
        self.assertGreater(len(models), 0)
        self.assertIn("openai/gpt-4o-mini", models)
        self.assertIn("anthropic/claude-3-haiku", models)


class TestScenarioCreation(unittest.TestCase):
    """Test scenario file creation"""

    def setUp(self):
        """Create temporary directory for test scenarios"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_minimal_scenario_structure(self):
        """Test creating minimal scenario directory structure"""
        scenario_path = os.path.join(self.test_dir, "test-scenario")
        os.makedirs(scenario_path)
        os.makedirs(os.path.join(scenario_path, 'actors'))

        # Create minimal scenario.yaml
        scenario = {
            'name': 'Test Scenario',
            'description': 'Test description',
            'system_prompt': 'Test system prompt',
            'initial_world_state': 'Test initial state',
            'turns': 3,
            'turn_duration': '1 day',
            'world_state_model': 'openai/gpt-4o-mini',
            'actors': ['actor1', 'actor2']
        }

        scenario_file = os.path.join(scenario_path, 'scenario.yaml')
        with open(scenario_file, 'w') as f:
            yaml.dump(scenario, f)

        # Verify file exists and can be loaded
        self.assertTrue(os.path.exists(scenario_file))

        with open(scenario_file, 'r') as f:
            loaded = yaml.safe_load(f)

        self.assertEqual(loaded['name'], 'Test Scenario')
        self.assertEqual(loaded['turns'], 3)
        self.assertEqual(len(loaded['actors']), 2)

    def test_create_minimal_actor(self):
        """Test creating minimal actor YAML file"""
        scenario_path = os.path.join(self.test_dir, "test-scenario")
        os.makedirs(os.path.join(scenario_path, 'actors'))

        actor = {
            'name': 'Test Actor',
            'short_name': 'test-actor',
            'llm_model': 'openai/gpt-4o-mini',
            'system_prompt': 'You are a test actor',
            'description': 'Test actor description',
            'goals': ['Goal 1', 'Goal 2'],
            'constraints': ['Constraint 1'],
            'expertise': {'policy': 'expert'},
            'decision_style': 'Pragmatic and analytical'
        }

        actor_file = os.path.join(scenario_path, 'actors', 'test-actor.yaml')
        with open(actor_file, 'w') as f:
            yaml.dump(actor, f)

        # Verify file exists and can be loaded
        self.assertTrue(os.path.exists(actor_file))

        with open(actor_file, 'r') as f:
            loaded = yaml.safe_load(f)

        self.assertEqual(loaded['name'], 'Test Actor')
        self.assertEqual(loaded['short_name'], 'test-actor')
        self.assertEqual(len(loaded['goals']), 2)

    def test_create_metrics_file(self):
        """Test creating metrics.yaml file"""
        scenario_path = os.path.join(self.test_dir, "test-scenario")
        os.makedirs(scenario_path)

        metrics = {
            'scenario_name': 'Test Scenario',
            'metrics': {
                'test_metric': {
                    'description': 'Test metric',
                    'type': 'integer',
                    'unit': 'hours',
                    'extraction_method': 'regex',
                    'pattern': r'(\d+)\s*hours?',
                    'actor_specific': False
                }
            }
        }

        metrics_file = os.path.join(scenario_path, 'metrics.yaml')
        with open(metrics_file, 'w') as f:
            yaml.dump(metrics, f)

        # Verify file exists and can be loaded
        self.assertTrue(os.path.exists(metrics_file))

        with open(metrics_file, 'r') as f:
            loaded = yaml.safe_load(f)

        self.assertEqual(loaded['scenario_name'], 'Test Scenario')
        self.assertIn('test_metric', loaded['metrics'])
        self.assertEqual(loaded['metrics']['test_metric']['type'], 'integer')

    def test_full_scenario_structure(self):
        """Test creating complete scenario structure"""
        scenario_path = os.path.join(self.test_dir, "complete-scenario")
        os.makedirs(os.path.join(scenario_path, 'actors'))

        # Scenario file
        scenario = {
            'name': 'Complete Test Scenario',
            'description': 'A complete test scenario',
            'system_prompt': 'System prompt here',
            'initial_world_state': 'Initial state here',
            'turns': 5,
            'turn_duration': '1 week',
            'world_state_model': 'openai/gpt-4o',
            'actors': ['actor-one', 'actor-two']
        }

        with open(os.path.join(scenario_path, 'scenario.yaml'), 'w') as f:
            yaml.dump(scenario, f)

        # Actor files
        for actor_name in ['actor-one', 'actor-two']:
            actor = {
                'name': actor_name.replace('-', ' ').title(),
                'short_name': actor_name,
                'llm_model': 'openai/gpt-4o-mini',
                'system_prompt': f'You are {actor_name}',
                'description': f'{actor_name} description',
                'goals': ['Goal 1'],
                'constraints': ['Constraint 1'],
                'expertise': {'domain': 'expert'},
                'decision_style': 'Analytical'
            }

            actor_file = os.path.join(scenario_path, 'actors', f'{actor_name}.yaml')
            with open(actor_file, 'w') as f:
                yaml.dump(actor, f)

        # Metrics file
        metrics = {
            'scenario_name': scenario['name'],
            'metrics': {
                'metric1': {
                    'description': 'First metric',
                    'type': 'integer',
                    'extraction_method': 'manual',
                    'actor_specific': False
                }
            }
        }

        with open(os.path.join(scenario_path, 'metrics.yaml'), 'w') as f:
            yaml.dump(metrics, f)

        # Verify all files exist
        self.assertTrue(os.path.exists(os.path.join(scenario_path, 'scenario.yaml')))
        self.assertTrue(os.path.exists(os.path.join(scenario_path, 'actors', 'actor-one.yaml')))
        self.assertTrue(os.path.exists(os.path.join(scenario_path, 'actors', 'actor-two.yaml')))
        self.assertTrue(os.path.exists(os.path.join(scenario_path, 'metrics.yaml')))

        # Verify structure is loadable
        with open(os.path.join(scenario_path, 'scenario.yaml'), 'r') as f:
            loaded_scenario = yaml.safe_load(f)

        self.assertEqual(len(loaded_scenario['actors']), 2)


if __name__ == '__main__':
    unittest.main()
