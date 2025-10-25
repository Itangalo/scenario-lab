"""
Unit tests for WorldStateUpdater
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from world_state_updater import WorldStateUpdater
from world_state import WorldState


class TestWorldStateUpdater(unittest.TestCase):
    """Test WorldStateUpdater functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # WorldStateUpdater doesn't take world_state or api_key in __init__
        # It only takes model parameter
        # Need to set OPENROUTER_API_KEY in environment
        import os
        os.environ['OPENROUTER_API_KEY'] = 'test-key'
        self.updater = WorldStateUpdater(model="test-model")

    @patch('world_state_updater.make_llm_call')
    def test_update_world_state_returns_tokens(self, mock_llm_call):
        """Test that update_world_state correctly handles tokens_used from make_llm_call"""
        # Mock make_llm_call to return (content, tokens) tuple
        mock_content = """
**UPDATED STATE:**
The world has changed.

**KEY CHANGES:**
- Change 1
- Change 2

**CONSEQUENCES:**
- Consequence 1
"""
        mock_llm_call.return_value = (mock_content, 1500)

        # Mock actor decisions - correct format
        actor_decisions = {
            'Test Actor': {
                'reasoning': 'Test reasoning',
                'action': 'Test action'
            }
        }

        # This should NOT raise NameError: name 'result' is not defined
        result = self.updater.update_world_state(
            current_state="Test state",
            turn=1,
            total_turns=5,
            actor_decisions=actor_decisions,
            scenario_name="Test Scenario"
        )

        # Verify tokens_used is returned correctly (in metadata)
        self.assertEqual(result['metadata']['tokens_used'], 1500)
        self.assertIn('updated_state', result)
        self.assertIn('metadata', result)

    @patch('world_state_updater.make_llm_call')
    def test_regression_no_result_variable_error(self, mock_llm_call):
        """Regression test: Ensure no NameError for undefined 'result' variable"""
        # This is the bug we fixed: code referenced 'result' variable that didn't exist
        # after switching to make_llm_call which returns (content, tokens) tuple

        mock_llm_call.return_value = ("**UPDATED STATE:**\nTest state", 100)

        # Should not raise NameError
        try:
            result = self.updater.update_world_state(
                current_state="Test state",
                turn=1,
                total_turns=3,
                actor_decisions={},
                scenario_name="Regression Test"
            )
            # If we get here, the bug is fixed
            self.assertIsNotNone(result)
        except NameError as e:
            if 'result' in str(e):
                self.fail("NameError for 'result' variable - regression bug!")
            else:
                raise

    @patch('world_state_updater.make_llm_call')
    def test_local_model_call(self, mock_llm_call):
        """Test that local models are called correctly"""
        # Create updater with local model
        import os
        os.environ['OPENROUTER_API_KEY'] = 'test-key'
        local_updater = WorldStateUpdater(model="ollama/deepseek-r1:8b")

        mock_llm_call.return_value = ("**UPDATED STATE:**\nLocal LLM response", 500)

        result = local_updater.update_world_state(
            current_state="Local test",
            turn=1,
            total_turns=2,
            actor_decisions={},
            scenario_name="Local Test"
        )

        # Verify make_llm_call was called with local model
        self.assertTrue(mock_llm_call.called)
        call_args = mock_llm_call.call_args
        self.assertEqual(call_args[1]['model'], 'ollama/deepseek-r1:8b')
        self.assertEqual(result['metadata']['tokens_used'], 500)

    @patch('world_state_updater.make_llm_call')
    def test_parse_updated_state_sections(self, mock_llm_call):
        """Test parsing of UPDATED STATE, KEY CHANGES, and CONSEQUENCES sections"""
        mock_content = """
**UPDATED STATE:**
This is the new world state.

**KEY CHANGES:**
- First change
- Second change
- Third change

**CONSEQUENCES:**
- First consequence
- Second consequence
"""
        mock_llm_call.return_value = (mock_content, 2000)

        result = self.updater.update_world_state(
            current_state="Parse test",
            turn=1,
            total_turns=3,
            actor_decisions={},
            scenario_name="Parse Test"
        )

        # Verify parsing (key_changes and consequences are in metadata)
        self.assertIn('This is the new world state', result['updated_state'])
        self.assertEqual(len(result['metadata']['key_changes']), 3)
        self.assertEqual(len(result['metadata']['consequences_identified']), 2)
        self.assertIn('First change', result['metadata']['key_changes'][0])
        self.assertIn('Second consequence', result['metadata']['consequences_identified'][1])

    @patch('world_state_updater.make_llm_call')
    def test_fallback_parsing(self, mock_llm_call):
        """Test fallback when LLM doesn't follow expected format"""
        # LLM returns unformatted content
        mock_content = "Just some random text without sections."
        mock_llm_call.return_value = (mock_content, 100)

        result = self.updater.update_world_state(
            current_state="Fallback test",
            turn=1,
            total_turns=2,
            actor_decisions={},
            scenario_name="Fallback Test"
        )

        # Should fall back to using entire content as updated_state
        self.assertEqual(result['updated_state'], mock_content)
        self.assertEqual(len(result['metadata']['key_changes']), 0)
        self.assertEqual(len(result['metadata']['consequences_identified']), 0)


if __name__ == '__main__':
    unittest.main()
