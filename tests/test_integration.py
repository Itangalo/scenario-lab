"""
Integration tests for Scenario Lab

Tests end-to-end scenario execution with mock LLM responses.
These tests verify that all components work together correctly.
"""
import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from run_scenario import run_scenario, branch_scenario
from scenario_state_manager import ScenarioStateManager


class MockLLMProvider:
    """Mock LLM provider that returns deterministic responses"""

    def __init__(self):
        self.call_count = 0
        self.responses = {}

    def set_response(self, pattern: str, response: dict):
        """Set a canned response for a pattern in the prompt"""
        self.responses[pattern] = response

    def make_call(self, model: str, messages: list, temperature: float = 0.7, **kwargs):
        """
        Mock LLM call that returns deterministic responses in the format expected by make_llm_call.

        Returns:
            Tuple of (content_string, tokens_int) matching make_llm_call's return format
        """
        self.call_count += 1

        # Get the prompt text
        prompt = messages[-1]['content'] if messages else ""

        # Match patterns and return appropriate response
        for pattern, response_dict in self.responses.items():
            if pattern in prompt:
                content = response_dict['choices'][0]['message']['content']
                tokens = response_dict['usage']['total_tokens']
                return content, tokens

        # Default response
        default_content = """**REASONING:**
Default test reasoning

**ACTION:**
Default test action"""
        return default_content, 150


class TestBasicScenarioExecution(unittest.TestCase):
    """Test basic scenario execution with mocked LLM"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.mock_llm = MockLLMProvider()

        # Create minimal test scenario
        self.scenario_dir = os.path.join(self.test_dir, 'test-scenario')
        os.makedirs(self.scenario_dir)

        # Create scenario.yaml
        scenario_yaml = """
name: Integration Test Scenario
turns: 2
turn_duration: "1 week"
initial_world_state: |
  This is the initial world state for testing.
  Turn duration: 1 week
actors:
  - actor1
  - actor2
context_window_size: 2
world_state_model: test/mock-model
"""
        with open(os.path.join(self.scenario_dir, 'scenario.yaml'), 'w') as f:
            f.write(scenario_yaml)

        # Create actors directory
        actors_dir = os.path.join(self.scenario_dir, 'actors')
        os.makedirs(actors_dir)

        # Create actor1.yaml
        actor1_yaml = """
name: Test Actor 1
short_name: actor1
role: Test Role 1
expertise: Testing
llm_model: test/mock-model
long_term_goals: |
  - Complete the test successfully
decision_making_style: Cautious and methodical
constraints:
  - Must follow test protocols
"""
        with open(os.path.join(actors_dir, 'actor1.yaml'), 'w') as f:
            f.write(actor1_yaml)

        # Create actor2.yaml
        actor2_yaml = """
name: Test Actor 2
short_name: actor2
role: Test Role 2
expertise: Quality Assurance
llm_model: test/mock-model
long_term_goals: |
  - Verify test results
decision_making_style: Analytical
constraints:
  - Must be thorough
"""
        with open(os.path.join(actors_dir, 'actor2.yaml'), 'w') as f:
            f.write(actor2_yaml)

        # Set up mock responses
        self.mock_llm.set_response("Test Actor 1", {
            'choices': [{
                'message': {
                    'content': """**LONG-TERM GOALS:**
- Complete the test successfully
- Ensure quality

**SHORT-TERM PRIORITIES:**
- Execute current turn actions

**REASONING:**
This is test reasoning for Actor 1 in the current turn.

**ACTION:**
Actor 1 takes a test action for this turn."""
                }
            }],
            'usage': {'prompt_tokens': 200, 'completion_tokens': 100, 'total_tokens': 300}
        })

        self.mock_llm.set_response("Test Actor 2", {
            'choices': [{
                'message': {
                    'content': """**LONG-TERM GOALS:**
- Verify test results
- Maintain standards

**SHORT-TERM PRIORITIES:**
- Review actor 1 actions

**REASONING:**
This is test reasoning for Actor 2 in the current turn.

**ACTION:**
Actor 2 takes a test action for this turn."""
                }
            }],
            'usage': {'prompt_tokens': 200, 'completion_tokens': 100, 'total_tokens': 300}
        })

        self.mock_llm.set_response("world state", {
            'choices': [{
                'message': {
                    'content': """The world state has been updated based on the actions taken.

Actor 1 has performed their test action.
Actor 2 has performed their test action.

The test scenario continues to progress normally."""
                }
            }],
            'usage': {'prompt_tokens': 300, 'completion_tokens': 80, 'total_tokens': 380}
        })

        # Set up bilateral communication responses
        self.mock_llm.set_response("bilateral communication", {
            'choices': [{
                'message': {
                    'content': """**INITIATE_BILATERAL:** no"""
                }
            }],
            'usage': {'prompt_tokens': 150, 'completion_tokens': 10, 'total_tokens': 160}
        })

        # Set up coalition responses
        self.mock_llm.set_response("coalition formation", {
            'choices': [{
                'message': {
                    'content': """**PROPOSE_COALITION:** no"""
                }
            }],
            'usage': {'prompt_tokens': 150, 'completion_tokens': 10, 'total_tokens': 160}
        })

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)

    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'})
    @patch('actor_engine.make_llm_call')
    @patch('world_state_updater.make_llm_call')
    @patch('context_manager.make_llm_call')
    def test_basic_scenario_execution(self, mock_ctx_call, mock_wsu_call, mock_actor_call):
        """Test that a basic scenario executes successfully"""
        # Set up mocks to use our MockLLMProvider
        mock_actor_call.side_effect = lambda *args, **kwargs: self.mock_llm.make_call(*args, **kwargs)
        mock_wsu_call.side_effect = lambda *args, **kwargs: self.mock_llm.make_call(*args, **kwargs)
        mock_ctx_call.side_effect = lambda *args, **kwargs: self.mock_llm.make_call(*args, **kwargs)

        # Run the scenario
        output_dir = os.path.join(self.test_dir, 'output')

        try:
            run_scenario(
                scenario_path=self.scenario_dir,
                output_path=output_dir,
                max_turns=None,  # Let it complete all turns
                verbose=False
            )
        except Exception as e:
            self.fail(f"Scenario execution failed with exception: {e}")

        # Verify output files were created
        self.assertTrue(os.path.exists(output_dir), "Output directory should exist")
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'world-state-000.md')), "Initial world state should exist")
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'world-state-001.md')), "Turn 1 world state should exist")
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'world-state-002.md')), "Turn 2 world state should exist")

        # Verify actor decision files
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'actor1-001.md')), "Actor1 turn 1 decision should exist")
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'actor2-001.md')), "Actor2 turn 1 decision should exist")
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'actor1-002.md')), "Actor1 turn 2 decision should exist")
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'actor2-002.md')), "Actor2 turn 2 decision should exist")

        # Verify costs.json was created
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'costs.json')), "Costs file should exist")

        # Verify scenario-state.json was created
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'scenario-state.json')), "Scenario state should exist")

        # Verify scenario.log was created (from structured logging)
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'scenario.log')), "Scenario log should exist")

        # Verify state is marked as completed
        state_manager = ScenarioStateManager(output_dir)
        state = state_manager.load_state()
        self.assertEqual(state['status'], 'completed', "Scenario should be marked as completed")
        self.assertEqual(state['current_turn'], 2, "Should have completed 2 turns")


class TestScenarioResume(unittest.TestCase):
    """Test scenario resume functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.mock_llm = MockLLMProvider()

        # Create minimal test scenario (same as above)
        self.scenario_dir = os.path.join(self.test_dir, 'test-scenario')
        os.makedirs(self.scenario_dir)

        scenario_yaml = """
name: Resume Test Scenario
turns: 3
turn_duration: "1 week"
initial_world_state: |
  This is the initial world state for resume testing.
actors:
  - actor1
context_window_size: 2
world_state_model: test/mock-model
"""
        with open(os.path.join(self.scenario_dir, 'scenario.yaml'), 'w') as f:
            f.write(scenario_yaml)

        actors_dir = os.path.join(self.scenario_dir, 'actors')
        os.makedirs(actors_dir)

        actor1_yaml = """
name: Test Actor
short_name: actor1
role: Test Role
expertise: Testing
llm_model: test/mock-model
long_term_goals: |
  - Complete all turns
decision_making_style: Efficient
constraints: []
"""
        with open(os.path.join(actors_dir, 'actor1.yaml'), 'w') as f:
            f.write(actor1_yaml)

        # Set up mock responses
        self.mock_llm.set_response("Test Actor", {
            'choices': [{
                'message': {
                    'content': """**LONG-TERM GOALS:**
- Complete all turns

**SHORT-TERM PRIORITIES:**
- Execute action

**REASONING:**
Test reasoning

**ACTION:**
Test action"""
                }
            }],
            'usage': {'prompt_tokens': 200, 'completion_tokens': 50, 'total_tokens': 250}
        })

        self.mock_llm.set_response("world state", {
            'choices': [{
                'message': {
                    'content': "World state updated for testing."
                }
            }],
            'usage': {'prompt_tokens': 300, 'completion_tokens': 30, 'total_tokens': 330}
        })

        self.mock_llm.set_response("bilateral", {
            'choices': [{'message': {'content': "**INITIATE_BILATERAL:** no"}}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 10, 'total_tokens': 110}
        })

        self.mock_llm.set_response("coalition", {
            'choices': [{'message': {'content': "**PROPOSE_COALITION:** no"}}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 10, 'total_tokens': 110}
        })

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)

    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'})
    @patch('actor_engine.make_llm_call')
    @patch('world_state_updater.make_llm_call')
    @patch('context_manager.make_llm_call')
    def test_resume_after_max_turns(self, mock_ctx_call, mock_wsu_call, mock_actor_call):
        """Test resuming a scenario after hitting max_turns"""
        mock_actor_call.side_effect = lambda *args, **kwargs: self.mock_llm.make_call(*args, **kwargs)
        mock_wsu_call.side_effect = lambda *args, **kwargs: self.mock_llm.make_call(*args, **kwargs)
        mock_ctx_call.side_effect = lambda *args, **kwargs: self.mock_llm.make_call(*args, **kwargs)

        output_dir = os.path.join(self.test_dir, 'output')

        # Run scenario with max_turns=2 (should halt after 2 turns)
        run_scenario(
            scenario_path=self.scenario_dir,
            output_path=output_dir,
            max_turns=2,
            verbose=False
        )

        # Verify it stopped at turn 2
        state_manager = ScenarioStateManager(output_dir)
        state = state_manager.load_state()
        self.assertEqual(state['status'], 'halted')
        self.assertEqual(state['current_turn'], 2)
        self.assertEqual(state['halt_reason'], 'max_turns')

        # Resume the scenario
        run_scenario(
            scenario_path=None,
            output_path=output_dir,
            max_turns=None,
            resume_mode=True,
            verbose=False
        )

        # Verify it completed all 3 turns
        state = state_manager.load_state()
        self.assertEqual(state['status'], 'completed')
        self.assertEqual(state['current_turn'], 3)

        # Verify turn 3 files exist
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'world-state-003.md')))
        self.assertTrue(os.path.exists(os.path.join(output_dir, 'actor1-003.md')))


class TestScenarioBranching(unittest.TestCase):
    """Test scenario branching functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.mock_llm = MockLLMProvider()

        # Create minimal test scenario
        self.scenario_dir = os.path.join(self.test_dir, 'test-scenario')
        os.makedirs(self.scenario_dir)

        scenario_yaml = """
name: Branch Test Scenario
turns: 3
turn_duration: "1 week"
initial_world_state: |
  Initial state for branching test
actors:
  - actor1
context_window_size: 2
world_state_model: test/mock-model
"""
        with open(os.path.join(self.scenario_dir, 'scenario.yaml'), 'w') as f:
            f.write(scenario_yaml)

        actors_dir = os.path.join(self.scenario_dir, 'actors')
        os.makedirs(actors_dir)

        actor1_yaml = """
name: Test Actor
short_name: actor1
role: Test
expertise: Testing
llm_model: test/mock-model
long_term_goals: |
  - Test branching
decision_making_style: Adaptive
constraints: []
"""
        with open(os.path.join(actors_dir, 'actor1.yaml'), 'w') as f:
            f.write(actor1_yaml)

        # Mock responses
        self.mock_llm.set_response("Test Actor", {
            'choices': [{'message': {'content': "**REASONING:**\nTest\n\n**ACTION:**\nTest action"}}],
            'usage': {'prompt_tokens': 200, 'completion_tokens': 30, 'total_tokens': 230}
        })

        self.mock_llm.set_response("world state", {
            'choices': [{'message': {'content': "Updated state"}}],
            'usage': {'prompt_tokens': 250, 'completion_tokens': 20, 'total_tokens': 270}
        })

        self.mock_llm.set_response("bilateral", {
            'choices': [{'message': {'content': "**INITIATE_BILATERAL:** no"}}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 10, 'total_tokens': 110}
        })

        self.mock_llm.set_response("coalition", {
            'choices': [{'message': {'content': "**PROPOSE_COALITION:** no"}}],
            'usage': {'prompt_tokens': 100, 'completion_tokens': 10, 'total_tokens': 110}
        })

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)

    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-key'})
    @patch('actor_engine.make_llm_call')
    @patch('world_state_updater.make_llm_call')
    @patch('context_manager.make_llm_call')
    def test_branch_from_turn(self, mock_ctx_call, mock_wsu_call, mock_actor_call):
        """Test branching a scenario from a specific turn"""
        mock_actor_call.side_effect = lambda *args, **kwargs: self.mock_llm.make_call(*args, **kwargs)
        mock_wsu_call.side_effect = lambda *args, **kwargs: self.mock_llm.make_call(*args, **kwargs)
        mock_ctx_call.side_effect = lambda *args, **kwargs: self.mock_llm.make_call(*args, **kwargs)

        output_dir = os.path.join(self.test_dir, 'output', 'branch-test', 'run-001')
        os.makedirs(output_dir)

        # Run initial scenario
        run_scenario(
            scenario_path=self.scenario_dir,
            output_path=output_dir,
            max_turns=2,
            verbose=False
        )

        # Branch from turn 1
        branch_path = branch_scenario(
            source_run_path=output_dir,
            branch_at_turn=1,
            verbose=False
        )

        # Verify branch was created
        self.assertTrue(os.path.exists(branch_path))
        self.assertTrue('run-002' in branch_path)

        # Verify branch has files up to turn 1
        self.assertTrue(os.path.exists(os.path.join(branch_path, 'world-state-000.md')))
        self.assertTrue(os.path.exists(os.path.join(branch_path, 'world-state-001.md')))
        self.assertTrue(os.path.exists(os.path.join(branch_path, 'actor1-001.md')))

        # Verify branch does not have turn 2 files
        self.assertFalse(os.path.exists(os.path.join(branch_path, 'world-state-002.md')))
        self.assertFalse(os.path.exists(os.path.join(branch_path, 'actor1-002.md')))

        # Verify branch state
        branch_state_manager = ScenarioStateManager(branch_path)
        branch_state = branch_state_manager.load_state()
        self.assertEqual(branch_state['status'], 'halted')
        self.assertEqual(branch_state['current_turn'], 1)
        self.assertIn('branched_from', branch_state['execution_metadata'])


if __name__ == '__main__':
    unittest.main()
