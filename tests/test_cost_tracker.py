"""
Unit tests for CostTracker
"""
import unittest
import sys
import os
import json
import tempfile

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cost_tracker import CostTracker


class TestCostTracker(unittest.TestCase):
    """Test CostTracker functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.tracker = CostTracker()

    def test_initialization(self):
        """Test CostTracker initializes correctly"""
        self.assertEqual(self.tracker.total_cost, 0.0)
        self.assertEqual(self.tracker.total_tokens, 0)
        self.assertEqual(len(self.tracker.costs_by_actor), 0)

    def test_record_actor_decision(self):
        """Test recording actor decision costs"""
        self.tracker.record_actor_decision(
            actor_name="Test Actor",
            turn=1,
            model="test-model",
            tokens_used=1000
        )

        self.assertGreater(self.tracker.total_cost, 0)
        self.assertEqual(self.tracker.total_tokens, 1000)
        self.assertIn("Test Actor", self.tracker.costs_by_actor)

    def test_record_world_state_update(self):
        """Test recording world state update costs"""
        self.tracker.record_world_state_update(
            turn=1,
            model="test-model",
            tokens_used=2000
        )

        self.assertEqual(self.tracker.total_tokens, 2000)
        self.assertEqual(len(self.tracker.world_state_costs), 1)

    def test_multiple_turns_same_actor(self):
        """Test tracking multiple turns for same actor"""
        self.tracker.record_actor_decision("Actor A", 1, "test-model", 1000)
        self.tracker.record_actor_decision("Actor A", 2, "test-model", 1500)

        actor_costs = self.tracker.costs_by_actor["Actor A"]
        self.assertEqual(len(actor_costs['turns']), 2)
        self.assertEqual(actor_costs['total_tokens'], 2500)

    def test_multiple_actors_same_turn(self):
        """Test tracking multiple actors in same turn"""
        self.tracker.record_actor_decision("Actor A", 1, "test-model", 1000)
        self.tracker.record_actor_decision("Actor B", 1, "test-model", 1500)

        self.assertIn("Actor A", self.tracker.costs_by_actor)
        self.assertIn("Actor B", self.tracker.costs_by_actor)

        turn_costs = self.tracker.costs_by_turn[1]
        self.assertGreater(turn_costs['total'], 0)

    def test_save_to_file(self):
        """Test saving costs to JSON file"""
        self.tracker.record_actor_decision("Actor A", 1, "test-model", 1000)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            self.tracker.save_to_file(temp_path)

            # Verify file was created and contains data
            with open(temp_path, 'r') as f:
                data = json.load(f)

            self.assertIn('totals', data)
            self.assertIn('total_cost_usd', data['totals'])
            self.assertIn('total_tokens', data['totals'])
            self.assertEqual(data['totals']['total_tokens'], 1000)
        finally:
            os.unlink(temp_path)

    def test_estimate_scenario_cost(self):
        """Test scenario cost estimation"""
        actor_models = {
            "Actor A": "test-model",
            "Actor B": "test-model"
        }

        estimate = self.tracker.estimate_scenario_cost(
            num_actors=2,
            num_turns=3,
            actor_models=actor_models,
            world_state_model="test-model"
        )

        self.assertIn('total', estimate)
        self.assertIn('world_state', estimate)
        self.assertIn('total_tokens_estimated', estimate)
        self.assertGreater(estimate['total'], 0)


if __name__ == '__main__':
    unittest.main()
