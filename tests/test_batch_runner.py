"""
Tests for batch runner components
"""
import unittest
import os
import tempfile
import shutil
import yaml
import json
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from parameter_variator import ParameterVariator
from batch_cost_manager import BatchCostManager


class TestParameterVariator(unittest.TestCase):
    """Tests for ParameterVariator"""

    def setUp(self):
        """Create a temporary scenario directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.scenario_dir = os.path.join(self.temp_dir, 'test-scenario')
        os.makedirs(self.scenario_dir)

        # Create minimal scenario.yaml
        scenario_config = {
            'name': 'Test Scenario',
            'initial_world_state': 'Test state',
            'turns': 3,
            'actors': ['actor1', 'actor2']
        }
        with open(os.path.join(self.scenario_dir, 'scenario.yaml'), 'w') as f:
            yaml.dump(scenario_config, f)

        # Create actors directory with actor files
        actors_dir = os.path.join(self.scenario_dir, 'actors')
        os.makedirs(actors_dir)

        actor1_config = {
            'name': 'Actor One',
            'short_name': 'actor1',
            'llm_model': 'openai/gpt-4o-mini',
            'goals': ['Test goal']
        }
        with open(os.path.join(actors_dir, 'actor1.yaml'), 'w') as f:
            yaml.dump(actor1_config, f)

        actor2_config = {
            'name': 'Actor Two',
            'short_name': 'actor2',
            'llm_model': 'openai/gpt-4o-mini',
            'goals': ['Test goal']
        }
        with open(os.path.join(actors_dir, 'actor2.yaml'), 'w') as f:
            yaml.dump(actor2_config, f)

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_single_dimension_variation(self):
        """Test generating variations with single dimension"""
        variations_config = [
            {
                'type': 'actor_model',
                'actor': 'actor1',
                'values': ['model-a', 'model-b', 'model-c']
            }
        ]

        variator = ParameterVariator(self.scenario_dir, variations_config)
        variations = variator.generate_variations()

        self.assertEqual(len(variations), 3)
        self.assertEqual(variations[0]['variation_id'], 1)
        self.assertEqual(variations[1]['variation_id'], 2)
        self.assertEqual(variations[2]['variation_id'], 3)

        # Check modifications
        self.assertEqual(
            variations[0]['modifications']['actor_models']['actor1'],
            'model-a'
        )
        self.assertEqual(
            variations[1]['modifications']['actor_models']['actor1'],
            'model-b'
        )

    def test_multi_dimension_variation(self):
        """Test generating variations with multiple dimensions (Cartesian product)"""
        variations_config = [
            {
                'type': 'actor_model',
                'actor': 'actor1',
                'values': ['model-a', 'model-b']
            },
            {
                'type': 'actor_model',
                'actor': 'actor2',
                'values': ['model-x', 'model-y']
            }
        ]

        variator = ParameterVariator(self.scenario_dir, variations_config)
        variations = variator.generate_variations()

        # Should generate 2x2 = 4 variations
        self.assertEqual(len(variations), 4)

        # Check first variation (model-a, model-x)
        self.assertEqual(
            variations[0]['modifications']['actor_models'],
            {'actor1': 'model-a', 'actor2': 'model-x'}
        )

        # Check last variation (model-b, model-y)
        self.assertEqual(
            variations[3]['modifications']['actor_models'],
            {'actor1': 'model-b', 'actor2': 'model-y'}
        )

    def test_no_variations(self):
        """Test with no variations specified"""
        variator = ParameterVariator(self.scenario_dir, [])
        variations = variator.generate_variations()

        self.assertEqual(len(variations), 1)
        self.assertEqual(variations[0]['description'], 'Base configuration')

    def test_apply_variation_to_scenario(self):
        """Test applying a variation to create modified scenario"""
        variations_config = [
            {
                'type': 'actor_model',
                'actor': 'actor1',
                'values': ['new-model']
            }
        ]

        variator = ParameterVariator(self.scenario_dir, variations_config)
        variations = variator.generate_variations()

        temp_scenario = os.path.join(self.temp_dir, 'modified-scenario')
        modified_path = variator.apply_variation_to_scenario(variations[0], temp_scenario)

        # Check that files were created
        self.assertTrue(os.path.exists(os.path.join(modified_path, 'scenario.yaml')))
        self.assertTrue(os.path.exists(os.path.join(modified_path, 'actors', 'actor1.yaml')))

        # Check that actor model was modified
        with open(os.path.join(modified_path, 'actors', 'actor1.yaml')) as f:
            actor_config = yaml.safe_load(f)
            self.assertEqual(actor_config['llm_model'], 'new-model')

        # Check that actor2 was not modified
        with open(os.path.join(modified_path, 'actors', 'actor2.yaml')) as f:
            actor_config = yaml.safe_load(f)
            self.assertEqual(actor_config['llm_model'], 'openai/gpt-4o-mini')

    def test_variation_count(self):
        """Test variation count calculation"""
        variations_config = [
            {'type': 'actor_model', 'actor': 'actor1', 'values': ['a', 'b', 'c']},
            {'type': 'actor_model', 'actor': 'actor2', 'values': ['x', 'y']}
        ]

        variator = ParameterVariator(self.scenario_dir, variations_config)
        self.assertEqual(variator.get_variation_count(), 6)  # 3 * 2

    def test_estimate_total_runs(self):
        """Test total runs estimation"""
        variations_config = [
            {'type': 'actor_model', 'actor': 'actor1', 'values': ['a', 'b']}
        ]

        variator = ParameterVariator(self.scenario_dir, variations_config)
        self.assertEqual(variator.estimate_total_runs(runs_per_variation=5), 10)  # 2 * 5


class TestBatchCostManager(unittest.TestCase):
    """Tests for BatchCostManager"""

    def test_initialization(self):
        """Test cost manager initialization"""
        manager = BatchCostManager(budget_limit=100.0, cost_per_run_limit=5.0)
        self.assertEqual(manager.budget_limit, 100.0)
        self.assertEqual(manager.cost_per_run_limit, 5.0)
        self.assertEqual(manager.total_spent, 0.0)

    def test_can_start_run_no_limit(self):
        """Test can_start_run with no budget limit"""
        manager = BatchCostManager()
        can_start, reason = manager.can_start_run()
        self.assertTrue(can_start)
        self.assertIsNone(reason)

    def test_can_start_run_within_budget(self):
        """Test can_start_run when within budget"""
        manager = BatchCostManager(budget_limit=100.0, cost_per_run_limit=5.0)
        manager.record_run_cost('run-1', 1, 10.0)

        can_start, reason = manager.can_start_run()
        self.assertTrue(can_start)
        self.assertIsNone(reason)

    def test_can_start_run_budget_exceeded(self):
        """Test can_start_run when budget exceeded"""
        manager = BatchCostManager(budget_limit=10.0)
        manager.record_run_cost('run-1', 1, 11.0)

        can_start, reason = manager.can_start_run()
        self.assertFalse(can_start)
        self.assertIn('Budget limit reached', reason)

    def test_can_start_run_insufficient_budget(self):
        """Test can_start_run when insufficient budget remaining"""
        manager = BatchCostManager(budget_limit=10.0, cost_per_run_limit=5.0)
        manager.record_run_cost('run-1', 1, 7.0)  # $3 remaining, but need $5

        can_start, reason = manager.can_start_run()
        self.assertFalse(can_start)
        self.assertIn('Insufficient budget', reason)

    def test_record_run_cost(self):
        """Test recording run costs"""
        manager = BatchCostManager()
        manager.record_run_cost('run-1', 1, 5.0, success=True)
        manager.record_run_cost('run-2', 1, 3.0, success=True)

        self.assertEqual(manager.total_spent, 8.0)
        self.assertEqual(manager.runs_completed, 2)
        self.assertEqual(len(manager.run_costs), 2)

    def test_check_run_cost(self):
        """Test checking individual run cost"""
        manager = BatchCostManager(cost_per_run_limit=5.0)

        within, reason = manager.check_run_cost(3.0)
        self.assertTrue(within)

        within, reason = manager.check_run_cost(6.0)
        self.assertFalse(within)
        self.assertIn('exceeds limit', reason)

    def test_get_remaining_budget(self):
        """Test getting remaining budget"""
        manager = BatchCostManager(budget_limit=100.0)
        manager.record_run_cost('run-1', 1, 30.0)

        remaining = manager.get_remaining_budget()
        self.assertEqual(remaining, 70.0)

    def test_get_average_cost_per_run(self):
        """Test calculating average cost"""
        manager = BatchCostManager()
        manager.record_run_cost('run-1', 1, 10.0)
        manager.record_run_cost('run-2', 1, 20.0)

        avg = manager.get_average_cost_per_run()
        self.assertEqual(avg, 15.0)

    def test_estimate_runs_remaining(self):
        """Test estimating remaining runs"""
        manager = BatchCostManager(budget_limit=100.0, cost_per_run_limit=10.0)
        manager.record_run_cost('run-1', 1, 10.0)

        # $90 remaining / $10 per run = 9 runs
        remaining = manager.estimate_runs_remaining()
        self.assertEqual(remaining, 9)

    def test_variation_statistics(self):
        """Test variation-level statistics"""
        manager = BatchCostManager()
        manager.record_run_cost('run-1', 1, 10.0, success=True)
        manager.record_run_cost('run-2', 1, 15.0, success=True)
        manager.record_run_cost('run-3', 2, 20.0, success=True)

        stats = manager.get_variation_statistics()

        self.assertEqual(stats[1]['total_cost'], 25.0)
        self.assertEqual(stats[1]['num_runs'], 2)
        self.assertEqual(stats[1]['avg_cost_per_run'], 12.5)

        self.assertEqual(stats[2]['total_cost'], 20.0)
        self.assertEqual(stats[2]['num_runs'], 1)

    def test_save_and_load(self):
        """Test saving and loading cost state"""
        manager = BatchCostManager(budget_limit=100.0)
        manager.start_batch()
        manager.record_run_cost('run-1', 1, 10.0)
        manager.record_run_cost('run-2', 2, 15.0)

        # Save
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file.close()
        manager.save_to_file(temp_file.name)

        # Load into new manager
        new_manager = BatchCostManager(budget_limit=100.0)
        new_manager.load_from_file(temp_file.name)

        self.assertEqual(new_manager.total_spent, 25.0)
        self.assertEqual(new_manager.runs_completed, 2)
        self.assertEqual(len(new_manager.run_costs), 2)

        os.unlink(temp_file.name)


if __name__ == '__main__':
    unittest.main()
