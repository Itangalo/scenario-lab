"""
Unit tests for ContextManager
"""
import unittest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from world_state import WorldState
from context_manager import ContextManager


class TestContextManager(unittest.TestCase):
    """Test ContextManager functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.world_state = WorldState(
            "Initial state",
            "Test Scenario",
            "1 day"
        )

        # Add some turns
        self.world_state.update_state("State after turn 1")
        self.world_state.record_actor_decision(1, "Actor A", {
            'reasoning': 'Reasoning 1',
            'action': 'Action 1'
        })

        self.world_state.update_state("State after turn 2")
        self.world_state.record_actor_decision(2, "Actor A", {
            'reasoning': 'Reasoning 2',
            'action': 'Action 2'
        })

        self.context_manager = ContextManager(window_size=2)

    def test_initialization(self):
        """Test ContextManager initializes correctly"""
        self.assertEqual(self.context_manager.window_size, 2)
        self.assertEqual(len(self.context_manager.summaries_cache), 0)

    def test_full_history_within_window(self):
        """Test full history provided when within window"""
        context = self.context_manager.get_context_for_actor(
            "Actor A",
            self.world_state,
            turn=1
        )

        # Should contain initial state
        self.assertIn("Initial state", context)
        # Should contain turn 1 marker
        self.assertIn("Turn 1", context)

    def test_current_turn_only_shows_current_state(self):
        """Test current turn shows state but not decisions yet"""
        context = self.context_manager.get_context_for_actor(
            "Actor A",
            self.world_state,
            turn=2
        )

        # Should have current turn marker
        self.assertIn("Turn 2 (Current)", context)
        # Should have turn 1 (completed)
        self.assertIn("Turn 1", context)

    def test_clear_cache(self):
        """Test cache clearing"""
        # This would require mocking LLM calls for full test
        # For now just test the method exists and works
        self.context_manager.summaries_cache['test'] = 'value'
        self.assertEqual(len(self.context_manager.summaries_cache), 1)

        self.context_manager.clear_cache()
        self.assertEqual(len(self.context_manager.summaries_cache), 0)

    def test_get_summary_cost_estimation(self):
        """Test cost estimation for summaries"""
        cost_info = self.context_manager.get_summary_cost(
            self.world_state,
            start_turn=0,
            end_turn=5
        )

        self.assertIn('estimated_cost', cost_info)
        self.assertIn('estimated_input_tokens', cost_info)
        self.assertIn('estimated_output_tokens', cost_info)
        self.assertGreater(cost_info['estimated_cost'], 0)


if __name__ == '__main__':
    unittest.main()
