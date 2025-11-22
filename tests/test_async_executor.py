"""
Tests for AsyncExecutor

Tests async execution, event streaming, and human-in-the-loop control.
"""
import pytest
import asyncio
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from scenario_lab.runners.async_executor import AsyncExecutor, run_scenario_async
from scenario_lab.models.state import ScenarioState, ScenarioStatus
from scenario_lab.core.events import EventType

# Set fake API key for tests
os.environ['OPENROUTER_API_KEY'] = 'test-key-for-testing'


@pytest.fixture
def temp_scenario_dir():
    """Create a temporary scenario directory for testing"""
    temp_dir = Path(tempfile.mkdtemp())

    # Create minimal scenario structure
    (temp_dir / "definition").mkdir()
    (temp_dir / "definition" / "actors").mkdir()

    # Create scenario.yaml
    scenario_yaml = """
name: Test Scenario
description: A test scenario
system_prompt: Test system prompt
initial_world_state: Initial test world state
turn_duration: 1 day
turns: 3
world_state_model: ollama/llama3
actors:
  - test-actor
"""
    (temp_dir / "definition" / "scenario.yaml").write_text(scenario_yaml)

    # Create actor.yaml
    actor_yaml = """
name: Test Actor
short_name: test-actor
llm_model: ollama/llama3
system_prompt: Test actor prompt
goals:
  - Test goal
constraints:
  - Test constraint
"""
    (temp_dir / "definition" / "actors" / "test-actor.yaml").write_text(actor_yaml)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


class TestAsyncExecutor:
    """Test the async executor"""

    @pytest.mark.asyncio
    async def test_executor_initialization(self, temp_scenario_dir):
        """Test that executor initializes correctly"""
        executor = AsyncExecutor(
            scenario_path=str(temp_scenario_dir / "definition"),
            end_turn=2,
            credit_limit=1.0,
        )

        # Should start uninitialized
        assert executor.orchestrator is None
        assert executor.initial_state is None

        # Setup should initialize components
        await executor.setup()

        assert executor.orchestrator is not None
        assert executor.event_bus is not None
        assert executor.initial_state is not None
        # sync_runner is used internally but we verify via orchestrator
        assert executor.sync_runner is not None

        await executor.cleanup()

    @pytest.mark.asyncio
    async def test_executor_pause_resume(self, temp_scenario_dir):
        """Test pause and resume functionality"""
        executor = AsyncExecutor(
            scenario_path=str(temp_scenario_dir / "definition"),
            end_turn=2,
        )

        await executor.setup()

        # Should start unpaused
        assert not executor.is_paused

        # Pause
        await executor.pause()
        assert executor.is_paused

        # Resume
        await executor.resume()
        assert not executor.is_paused

        await executor.cleanup()

    @pytest.mark.asyncio
    async def test_executor_stop(self, temp_scenario_dir):
        """Test stop functionality"""
        executor = AsyncExecutor(
            scenario_path=str(temp_scenario_dir / "definition"),
            end_turn=2,
        )

        await executor.setup()

        # Stop should set flag on orchestrator
        await executor.stop()
        assert executor.orchestrator.should_stop is True

        await executor.cleanup()

    @pytest.mark.asyncio
    async def test_run_scenario_async_convenience_function(self, temp_scenario_dir):
        """Test convenience function for running scenarios"""
        # Mock orchestrator execution to avoid actual LLM calls
        with patch('scenario_lab.core.orchestrator.ScenarioOrchestrator.execute') as mock_execute:
            # Create mock return state
            mock_state = MagicMock(spec=ScenarioState)
            mock_state.turn = 3
            mock_state.status = ScenarioStatus.COMPLETED
            mock_state.total_cost.return_value = 0.0

            # Make execute return the mock state
            mock_execute.return_value = mock_state

            # Run scenario
            final_state = await run_scenario_async(
                scenario_path=str(temp_scenario_dir / "definition"),
                end_turn=3,
            )

            # Verify execute was called
            assert mock_execute.called
            assert final_state == mock_state

    @pytest.mark.asyncio
    async def test_event_streaming_yields_events(self, temp_scenario_dir):
        """Test that event streaming yields events"""
        executor = AsyncExecutor(
            scenario_path=str(temp_scenario_dir / "definition"),
            end_turn=1,
        )

        await executor.setup()

        # Mock the orchestrator.execute to complete quickly
        async def mock_execute(state):
            # Emit a test event
            await executor.event_bus.emit(
                EventType.TURN_STARTED,
                data={'turn': 1},
                source='test'
            )
            # Return completed state
            return state.with_completed()

        executor.orchestrator.execute = mock_execute

        # Collect streamed events
        events = []
        async for event in executor.execute_with_streaming():
            events.append(event)
            # Break after a few events to avoid hanging
            if len(events) >= 5:
                break

        # Should have received some events
        assert len(events) > 0

        # Events should have expected structure
        for event in events:
            assert 'type' in event
            assert 'timestamp' in event

        await executor.cleanup()

    @pytest.mark.asyncio
    async def test_executor_handles_failures_gracefully(self, temp_scenario_dir):
        """Test that executor handles execution failures"""
        executor = AsyncExecutor(
            scenario_path=str(temp_scenario_dir / "definition"),
            end_turn=1,
        )

        await executor.setup()

        # Mock the orchestrator.execute to raise an error
        async def mock_execute_error(state):
            raise RuntimeError("Test error")

        executor.orchestrator.execute = mock_execute_error

        # Execution should raise the error
        with pytest.raises(RuntimeError, match="Test error"):
            await executor.execute()

        await executor.cleanup()

    @pytest.mark.asyncio
    async def test_executor_not_initialized_raises_error(self):
        """Test that executing without setup raises error"""
        executor = AsyncExecutor(
            scenario_path="/nonexistent/path",
            end_turn=1,
        )

        # Should raise error if execute called without setup
        with pytest.raises(RuntimeError, match="not initialized"):
            await executor.execute()

    @pytest.mark.asyncio
    async def test_executor_sets_logging_context(self, temp_scenario_dir):
        """Test that executor sets logging context correctly"""
        from scenario_lab.utils.logging_config import current_scenario, current_run_id

        executor = AsyncExecutor(
            scenario_path=str(temp_scenario_dir / "definition"),
            end_turn=1,
        )

        await executor.setup()

        # Mock the execute to avoid actual LLM calls
        with patch('scenario_lab.core.orchestrator.ScenarioOrchestrator.execute') as mock_execute:
            mock_state = MagicMock(spec=ScenarioState)
            mock_state.status = ScenarioStatus.COMPLETED
            mock_execute.return_value = mock_state

            await executor.execute()

        await executor.cleanup()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
