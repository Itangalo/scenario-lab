"""
Unit tests for WorldState
"""
import unittest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from world_state import WorldState


class TestWorldState(unittest.TestCase):
    """Test WorldState functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.initial_state = "Test initial state"
        self.scenario_name = "Test Scenario"
        self.turn_duration = "1 day"
        self.world_state = WorldState(
            self.initial_state,
            self.scenario_name,
            self.turn_duration
        )

    def test_initialization(self):
        """Test WorldState initializes correctly"""
        self.assertEqual(self.world_state.scenario_name, self.scenario_name)
        self.assertEqual(self.world_state.turn_duration, self.turn_duration)
        self.assertEqual(self.world_state.current_turn, 0)
        self.assertEqual(self.world_state.states[0], self.initial_state)

    def test_get_current_state(self):
        """Test getting current state"""
        current = self.world_state.get_current_state()
        self.assertEqual(current, self.initial_state)

    def test_update_state(self):
        """Test updating world state"""
        new_state = "Updated state for turn 1"
        self.world_state.update_state(new_state)

        self.assertEqual(self.world_state.current_turn, 1)
        self.assertEqual(self.world_state.states[1], new_state)
        self.assertEqual(self.world_state.get_current_state(), new_state)

    def test_record_actor_decision(self):
        """Test recording actor decisions"""
        decision = {
            'reasoning': 'Test reasoning',
            'action': 'Test action'
        }

        self.world_state.record_actor_decision(1, "Test Actor", decision)

        turn_decisions = self.world_state.get_actor_decisions_for_turn(1)
        self.assertIn("Test Actor", turn_decisions)
        self.assertEqual(turn_decisions["Test Actor"], decision)

    def test_multiple_actors_same_turn(self):
        """Test multiple actors can record decisions for same turn"""
        decision1 = {'reasoning': 'Reasoning 1', 'action': 'Action 1'}
        decision2 = {'reasoning': 'Reasoning 2', 'action': 'Action 2'}

        self.world_state.record_actor_decision(1, "Actor 1", decision1)
        self.world_state.record_actor_decision(1, "Actor 2", decision2)

        turn_decisions = self.world_state.get_actor_decisions_for_turn(1)
        self.assertEqual(len(turn_decisions), 2)
        self.assertEqual(turn_decisions["Actor 1"], decision1)
        self.assertEqual(turn_decisions["Actor 2"], decision2)

    def test_to_markdown(self):
        """Test markdown generation"""
        md = self.world_state.to_markdown(0)

        self.assertIn("# World State - Turn 0", md)
        self.assertIn(self.scenario_name, md)
        self.assertIn(self.turn_duration, md)
        self.assertIn(self.initial_state, md)

    def test_actor_decision_to_markdown(self):
        """Test actor decision markdown generation"""
        decision = {
            'reasoning': 'Test reasoning',
            'action': 'Test action'
        }

        md = self.world_state.actor_decision_to_markdown(1, "Test Actor", decision)

        self.assertIn("# Test Actor - Turn 1", md)
        self.assertIn("Test reasoning", md)
        self.assertIn("Test action", md)


if __name__ == '__main__':
    unittest.main()
