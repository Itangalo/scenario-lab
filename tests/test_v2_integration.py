"""
Integration tests for Scenario Lab V2

Tests end-to-end V2 scenario execution with mock LLM responses.
Verifies that orchestrator, phase services, and state management work correctly.
"""
import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from scenario_lab.runners import SyncRunner
from scenario_lab.core.events import EventBus, Event, EventType
from scenario_lab.models.state import ScenarioState, ScenarioStatus
from scenario_lab.utils.state_persistence import StatePersistence


class MockLLMProvider:
    """
    Mock LLM provider for deterministic testing

    Returns pre-scripted responses based on call sequence and context.
    """

    def __init__(self):
        self.call_count = 0
        self.calls_log: List[Dict[str, Any]] = []
        self.responses: Dict[str, str] = {}
        self.default_responses = {
            'decision': '''{
                "goals": ["Complete test successfully"],
                "reasoning": "This is a test decision made by the mock LLM",
                "action": "Take a measured approach to achieve the testing goal"
            }''',
            'world_state': '''The world has progressed by one turn.

Actors have taken their actions and the situation has evolved accordingly.

**Key Changes:**
- Test actor 1 took action
- Test actor 2 took action
- The simulation continues as expected''',
            'communication': '''{
                "should_communicate": false,
                "reasoning": "No communication needed at this time"
            }''',
            'metrics': '''{
                "cooperation_level": 7,
                "progress": 5
            }'''
        }

    def set_response(self, key: str, response: str):
        """Set a specific response for a key"""
        self.responses[key] = response

    def make_call(self, model: str, messages: list, temperature: float = 0.7, **kwargs):
        """
        Mock LLM call that returns deterministic responses

        Returns:
            Tuple of (content_string, tokens_int)
        """
        self.call_count += 1

        # Log the call
        prompt = messages[-1]['content'] if messages else ""
        self.calls_log.append({
            'count': self.call_count,
            'model': model,
            'prompt_length': len(prompt),
            'temperature': temperature
        })

        # Determine response type from prompt content
        response_type = 'decision'  # default
        if 'world state' in prompt.lower() or 'synthesize' in prompt.lower():
            response_type = 'world_state'
        elif 'communicate' in prompt.lower() or 'bilateral' in prompt.lower():
            response_type = 'communication'
        elif 'metrics' in prompt.lower():
            response_type = 'metrics'

        # Get response
        response = self.responses.get(
            f"{response_type}_{self.call_count}",
            self.responses.get(response_type, self.default_responses[response_type])
        )

        # Calculate token count (rough estimate)
        tokens = len(response.split()) * 2

        return response, tokens


@pytest.fixture
def temp_scenario_dir():
    """Create a temporary directory for test scenarios"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider"""
    return MockLLMProvider()


@pytest.fixture
def test_scenario(temp_scenario_dir):
    """
    Create a minimal test scenario

    Returns path to scenario directory
    """
    scenario_dir = Path(temp_scenario_dir) / 'test-scenario'
    scenario_dir.mkdir()

    # Create scenario.yaml
    scenario_yaml = """name: V2 Integration Test Scenario
description: Minimal scenario for testing V2 components
num_turns: 3
turn_duration: "1 week"
initial_world_state: |
  This is the initial world state for V2 integration testing.
  The scenario will run for 3 turns with 2 actors.

  **Current Status:**
  - Turn duration: 1 week
  - Actors: Test Actor 1, Test Actor 2
  - Goal: Validate V2 execution engine

world_state_model: "test/mock-model"
context_window: 2
"""

    with open(scenario_dir / 'scenario.yaml', 'w') as f:
        f.write(scenario_yaml)

    # Create actors directory
    actors_dir = scenario_dir / 'actors'
    actors_dir.mkdir()

    # Create actor1.yaml
    actor1_yaml = """name: Test Actor 1
short_name: actor1
llm_model: "test/mock-model"
system_prompt: |
  You are Test Actor 1, a cooperative participant in integration tests.

  Your goal is to help validate the V2 execution engine.

  Always respond with valid JSON containing goals, reasoning, and action.

goals:
  - Complete integration tests successfully
  - Validate V2 components

constraints:
  - Must use valid JSON format
  - Must provide reasoning

expertise: Integration Testing
decision_style: Methodical
"""

    with open(actors_dir / 'actor1.yaml', 'w') as f:
        f.write(actor1_yaml)

    # Create actor2.yaml
    actor2_yaml = """name: Test Actor 2
short_name: actor2
llm_model: "test/mock-model"
system_prompt: |
  You are Test Actor 2, a diligent participant in integration tests.

  Your goal is to complement Actor 1 in validating the V2 execution engine.

  Always respond with valid JSON containing goals, reasoning, and action.

goals:
  - Support integration test completion
  - Verify component interactions

constraints:
  - Must use valid JSON format
  - Must provide reasoning

expertise: Component Testing
decision_style: Thorough
"""

    with open(actors_dir / 'actor2.yaml', 'w') as f:
        f.write(actor2_yaml)

    return str(scenario_dir)


class TestBasicV2Execution:
    """Test basic V2 scenario execution"""

    @pytest.mark.asyncio
    async def test_basic_scenario_execution(self, test_scenario, mock_llm, temp_scenario_dir, monkeypatch):
        """Test that a basic scenario executes successfully"""
        # Patch the LLM call function
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent / 'src'))

        from api_utils import make_llm_call
        monkeypatch.setattr('api_utils.make_llm_call', mock_llm.make_call)

        # Create runner
        output_dir = Path(temp_scenario_dir) / 'output'
        runner = SyncRunner(
            scenario_path=test_scenario,
            output_path=str(output_dir),
            max_turns=3
        )

        # Setup runner
        runner.setup()

        # Verify initial state
        assert runner.initial_state is not None
        assert runner.initial_state.turn == 0
        assert runner.initial_state.scenario_name == "V2 Integration Test Scenario"
        assert len(runner.initial_state.actors) == 2

        # Run scenario
        final_state = await runner.run()

        # Verify final state
        assert final_state.turn == 3
        assert final_state.status == ScenarioStatus.COMPLETED
        assert len(final_state.costs) > 0
        assert final_state.total_cost() > 0

        # Verify output files exist
        assert (output_dir / 'world-state-001.md').exists()
        assert (output_dir / 'world-state-002.md').exists()
        assert (output_dir / 'world-state-003.md').exists()
        assert (output_dir / 'scenario-state-v2.json').exists()

        # Verify LLM was called
        assert mock_llm.call_count > 0

    @pytest.mark.asyncio
    async def test_cost_tracking(self, test_scenario, mock_llm, temp_scenario_dir, monkeypatch):
        """Test that costs are tracked accurately"""
        # Patch the LLM call function
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent / 'src'))

        from api_utils import make_llm_call
        monkeypatch.setattr('api_utils.make_llm_call', mock_llm.make_call)

        # Create runner
        output_dir = Path(temp_scenario_dir) / 'output'
        runner = SyncRunner(
            scenario_path=test_scenario,
            output_path=str(output_dir),
            max_turns=2
        )

        runner.setup()
        final_state = await runner.run()

        # Verify cost tracking
        assert len(final_state.costs) > 0

        # Verify costs have required fields
        for cost in final_state.costs:
            assert cost.timestamp is not None
            assert cost.model is not None
            assert cost.input_tokens >= 0
            assert cost.output_tokens >= 0
            assert cost.cost >= 0

        # Verify total cost calculation
        manual_total = sum(c.cost for c in final_state.costs)
        assert abs(final_state.total_cost() - manual_total) < 0.001

    @pytest.mark.asyncio
    async def test_event_emission(self, test_scenario, mock_llm, temp_scenario_dir, monkeypatch):
        """Test that events are emitted correctly during execution"""
        # Patch the LLM call function
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent / 'src'))

        from api_utils import make_llm_call
        monkeypatch.setattr('api_utils.make_llm_call', mock_llm.make_call)

        # Track events
        events_received = []

        # Create runner
        output_dir = Path(temp_scenario_dir) / 'output'
        runner = SyncRunner(
            scenario_path=test_scenario,
            output_path=str(output_dir),
            max_turns=2
        )

        runner.setup()

        # Register event handlers
        @runner.event_bus.on(EventType.TURN_STARTED)
        async def on_turn_start(event: Event):
            events_received.append(('turn_started', event.data.get('turn')))

        @runner.event_bus.on(EventType.TURN_COMPLETED)
        async def on_turn_complete(event: Event):
            events_received.append(('turn_completed', event.data.get('turn')))

        @runner.event_bus.on(EventType.PHASE_STARTED)
        async def on_phase_start(event: Event):
            events_received.append(('phase_started', event.data.get('phase')))

        # Run scenario
        await runner.run()

        # Verify events were emitted
        assert len(events_received) > 0

        # Verify turn events
        turn_started = [e for e in events_received if e[0] == 'turn_started']
        turn_completed = [e for e in events_received if e[0] == 'turn_completed']

        assert len(turn_started) >= 2
        assert len(turn_completed) >= 2


class TestResumeAndBranch:
    """Test resume and branch functionality"""

    @pytest.mark.asyncio
    async def test_state_persistence(self, test_scenario, mock_llm, temp_scenario_dir, monkeypatch):
        """Test that state is saved after each turn"""
        # Patch the LLM call function
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent / 'src'))

        from api_utils import make_llm_call
        monkeypatch.setattr('api_utils.make_llm_call', mock_llm.make_call)

        # Create runner
        output_dir = Path(temp_scenario_dir) / 'output'
        runner = SyncRunner(
            scenario_path=test_scenario,
            output_path=str(output_dir),
            max_turns=2
        )

        runner.setup()
        final_state = await runner.run()

        # Verify state file exists
        state_file = output_dir / 'scenario-state-v2.json'
        assert state_file.exists()

        # Load and verify state
        with open(state_file) as f:
            saved_state = json.load(f)

        assert saved_state['version'] == '2.0'
        assert saved_state['turn'] == 2
        assert saved_state['scenario_name'] == 'V2 Integration Test Scenario'
        assert len(saved_state['actors']) == 2
        assert len(saved_state['costs']) > 0

    @pytest.mark.asyncio
    async def test_resume_functionality(self, test_scenario, mock_llm, temp_scenario_dir, monkeypatch):
        """Test that scenarios can be resumed from saved state"""
        # Patch the LLM call function
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent / 'src'))

        from api_utils import make_llm_call
        monkeypatch.setattr('api_utils.make_llm_call', mock_llm.make_call)

        # First run: execute 2 turns
        output_dir = Path(temp_scenario_dir) / 'output' / 'run-001'
        runner1 = SyncRunner(
            scenario_path=test_scenario,
            output_path=str(output_dir),
            max_turns=2
        )

        runner1.setup()
        state1 = await runner1.run()

        assert state1.turn == 2
        initial_cost = state1.total_cost()

        # Second run: resume and execute 1 more turn
        runner2 = SyncRunner(
            scenario_path=test_scenario,
            output_path=str(output_dir),
            resume_from=str(output_dir),
            max_turns=3
        )

        runner2.setup()
        state2 = await runner2.run()

        # Verify resumed state
        assert state2.turn == 3
        assert state2.total_cost() > initial_cost

        # Verify world state files
        assert (output_dir / 'world-state-001.md').exists()
        assert (output_dir / 'world-state-002.md').exists()
        assert (output_dir / 'world-state-003.md').exists()

    @pytest.mark.asyncio
    async def test_branch_functionality(self, test_scenario, mock_llm, temp_scenario_dir, monkeypatch):
        """Test that scenarios can be branched at specific turns"""
        # Patch the LLM call function
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent / 'src'))

        from api_utils import make_llm_call
        monkeypatch.setattr('api_utils.make_llm_call', mock_llm.make_call)

        # First run: execute 3 turns
        output_dir = Path(temp_scenario_dir) / 'output' / 'run-001'
        runner1 = SyncRunner(
            scenario_path=test_scenario,
            output_path=str(output_dir),
            max_turns=3
        )

        runner1.setup()
        state1 = await runner1.run()

        assert state1.turn == 3

        # Branch at turn 2
        branch_dir = Path(temp_scenario_dir) / 'output' / 'run-002'
        runner2 = SyncRunner(
            scenario_path=test_scenario,
            output_path=str(branch_dir),
            branch_from=str(output_dir),
            branch_at_turn=2,
            max_turns=3
        )

        runner2.setup()

        # Verify branched initial state
        assert runner2.initial_state.turn == 2
        assert 'branched_from' in runner2.initial_state.execution_metadata
        assert runner2.initial_state.execution_metadata['branch_point'] == 2

        # Execute branch
        state2 = await runner2.run()

        assert state2.turn == 3

        # Verify branch has its own state file
        assert (branch_dir / 'scenario-state-v2.json').exists()


class TestCreditLimits:
    """Test credit limit enforcement"""

    @pytest.mark.asyncio
    async def test_credit_limit_enforcement(self, test_scenario, mock_llm, temp_scenario_dir, monkeypatch):
        """Test that execution stops when credit limit is reached"""
        # Patch the LLM call function to return expensive costs
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent / 'src'))

        def expensive_llm_call(model: str, messages: list, temperature: float = 0.7, **kwargs):
            """Mock LLM that returns expensive responses"""
            response, _ = mock_llm.make_call(model, messages, temperature, **kwargs)
            # Return high token count to simulate expensive calls
            return response, 10000

        from api_utils import make_llm_call
        monkeypatch.setattr('api_utils.make_llm_call', expensive_llm_call)

        # Create runner with very low credit limit
        output_dir = Path(temp_scenario_dir) / 'output'
        runner = SyncRunner(
            scenario_path=test_scenario,
            output_path=str(output_dir),
            max_turns=10,
            credit_limit=0.01  # Very low limit
        )

        # Track halt events
        halt_events = []

        runner.setup()

        @runner.event_bus.on(EventType.SCENARIO_HALTED)
        async def on_halt(event: Event):
            halt_events.append(event.data)

        # Run scenario
        final_state = await runner.run()

        # Verify execution was halted due to credit limit
        assert final_state.status == ScenarioStatus.HALTED
        assert len(halt_events) > 0
        assert 'credit limit' in halt_events[0].get('reason', '').lower()


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_invalid_resume_path(self, test_scenario, temp_scenario_dir):
        """Test that resume fails gracefully with invalid path"""
        output_dir = Path(temp_scenario_dir) / 'output'

        # Try to resume from non-existent directory
        runner = SyncRunner(
            scenario_path=test_scenario,
            output_path=str(output_dir),
            resume_from='/nonexistent/path'
        )

        # Should raise FileNotFoundError during setup
        with pytest.raises(FileNotFoundError):
            runner.setup()

    @pytest.mark.asyncio
    async def test_invalid_branch_turn(self, test_scenario, mock_llm, temp_scenario_dir, monkeypatch):
        """Test that branching fails gracefully with invalid turn number"""
        # Patch the LLM call function
        import sys
        from pathlib import Path as P
        sys.path.insert(0, str(P(__file__).parent.parent / 'src'))

        from api_utils import make_llm_call
        monkeypatch.setattr('api_utils.make_llm_call', mock_llm.make_call)

        # First run: execute 2 turns
        output_dir = Path(temp_scenario_dir) / 'output' / 'run-001'
        runner1 = SyncRunner(
            scenario_path=test_scenario,
            output_path=str(output_dir),
            max_turns=2
        )

        runner1.setup()
        await runner1.run()

        # Try to branch at turn 5 (beyond available turns)
        branch_dir = Path(temp_scenario_dir) / 'output' / 'run-002'
        runner2 = SyncRunner(
            scenario_path=test_scenario,
            output_path=str(branch_dir),
            branch_from=str(output_dir),
            branch_at_turn=5
        )

        # Should raise ValueError during setup
        with pytest.raises(ValueError):
            runner2.setup()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
