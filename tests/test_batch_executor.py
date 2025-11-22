"""
Tests for Batch Executor module

Tests execution logic for batch scenario runs.
"""
import pytest
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from scenario_lab.batch.batch_config import BatchConfig
from scenario_lab.batch.batch_executor import BatchExecutor
from scenario_lab.batch.parameter_variator import ParameterVariator
from scenario_lab.batch.batch_cost_manager import BatchCostManager
from scenario_lab.utils.error_handler import ErrorHandler


def create_test_scenario(tmpdir: str) -> Path:
    """Helper to create a minimal test scenario"""
    scenario_dir = Path(tmpdir) / 'scenario'
    scenario_dir.mkdir()
    (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
    (scenario_dir / 'actors').mkdir()
    (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")
    return scenario_dir


class TestBatchExecutorInit:
    """Tests for BatchExecutor initialization"""

    def test_init_creates_executor(self):
        """Test executor initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = create_test_scenario(tmpdir)

            config = BatchConfig(
                experiment_name='Test',
                base_scenario=str(scenario_dir),
                output_dir=f'{tmpdir}/output'
            )

            variator = ParameterVariator(str(scenario_dir), [])
            cost_manager = BatchCostManager()
            error_handler = ErrorHandler()

            executor = BatchExecutor(
                config=config,
                variator=variator,
                cost_manager=cost_manager,
                error_handler=error_handler
            )

            assert executor.config == config
            assert executor.variator == variator
            assert executor.cost_manager == cost_manager
            assert len(executor.completed_runs) == 0
            assert len(executor.failed_runs) == 0


class TestBatchExecutorRunId:
    """Tests for run ID generation"""

    def test_generate_run_id_format(self):
        """Test run ID format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = create_test_scenario(tmpdir)
            config = BatchConfig(
                experiment_name='Test',
                base_scenario=str(scenario_dir),
                output_dir=f'{tmpdir}/output'
            )

            executor = BatchExecutor(
                config=config,
                variator=ParameterVariator(str(scenario_dir), []),
                cost_manager=BatchCostManager(),
                error_handler=ErrorHandler()
            )

            assert executor.generate_run_id(1, 1) == "var-001-run-001"
            assert executor.generate_run_id(5, 10) == "var-005-run-010"
            assert executor.generate_run_id(123, 456) == "var-123-run-456"


class TestBatchExecutorState:
    """Tests for state save/load"""

    def test_save_and_load_state(self):
        """Test saving and loading execution state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = create_test_scenario(tmpdir)
            output_dir = Path(tmpdir) / 'output'
            output_dir.mkdir()

            config = BatchConfig(
                experiment_name='Test',
                base_scenario=str(scenario_dir),
                output_dir=str(output_dir)
            )

            executor = BatchExecutor(
                config=config,
                variator=ParameterVariator(str(scenario_dir), []),
                cost_manager=BatchCostManager(),
                error_handler=ErrorHandler()
            )

            # Set some state
            executor.completed_runs = {"var-001-run-001", "var-001-run-002"}
            executor.failed_runs = [{"run_id": "var-002-run-001", "error": "Test"}]
            executor.variations = [{"variation_id": 1, "description": "Test"}]
            executor.start_time = datetime.now()

            # Save state
            executor.save_state()

            # Create new executor and load state
            executor2 = BatchExecutor(
                config=config,
                variator=ParameterVariator(str(scenario_dir), []),
                cost_manager=BatchCostManager(),
                error_handler=ErrorHandler()
            )

            loaded = executor2.load_state()

            assert loaded is True
            assert executor2.completed_runs == {"var-001-run-001", "var-001-run-002"}
            assert len(executor2.failed_runs) == 1
            assert len(executor2.variations) == 1

    def test_load_state_no_previous(self):
        """Test loading state when no previous state exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = create_test_scenario(tmpdir)
            output_dir = Path(tmpdir) / 'output'
            output_dir.mkdir()

            config = BatchConfig(
                experiment_name='Test',
                base_scenario=str(scenario_dir),
                output_dir=str(output_dir)
            )

            executor = BatchExecutor(
                config=config,
                variator=ParameterVariator(str(scenario_dir), []),
                cost_manager=BatchCostManager(),
                error_handler=ErrorHandler()
            )

            loaded = executor.load_state()
            assert loaded is False


class TestBatchExecutorSingleScenario:
    """Tests for single scenario execution"""

    @pytest.mark.asyncio
    @patch('scenario_lab.batch.batch_executor.run_scenario_async')
    async def test_run_single_scenario_success(self, mock_run_scenario):
        """Test successful single scenario execution"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = create_test_scenario(tmpdir)
            output_dir = Path(tmpdir) / 'output'
            output_dir.mkdir()
            runs_dir = output_dir / 'runs'
            runs_dir.mkdir()

            config = BatchConfig(
                experiment_name='Test',
                base_scenario=str(scenario_dir),
                output_dir=str(output_dir)
            )

            variator = ParameterVariator(str(scenario_dir), [])
            cost_manager = BatchCostManager()
            error_handler = ErrorHandler()

            executor = BatchExecutor(
                config=config,
                variator=variator,
                cost_manager=cost_manager,
                error_handler=error_handler
            )

            # Mock the scenario execution
            mock_state = MagicMock()
            mock_state.total_cost.return_value = 0.05
            mock_run_scenario.return_value = mock_state

            variation = {
                "variation_id": 1,
                "description": "Test variation",
                "modifications": {}
            }

            with patch.object(variator, 'apply_variation_to_scenario', return_value=str(scenario_dir)):
                result = await executor.run_single_scenario("var-001-run-001", variation, 1)

            assert result['status'] == 'success'
            assert result['cost'] == 0.05

    @pytest.mark.asyncio
    @patch('scenario_lab.batch.batch_executor.run_scenario_async')
    async def test_run_single_scenario_failure(self, mock_run_scenario):
        """Test failed single scenario execution"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = create_test_scenario(tmpdir)
            output_dir = Path(tmpdir) / 'output'
            output_dir.mkdir()
            runs_dir = output_dir / 'runs'
            runs_dir.mkdir()

            config = BatchConfig(
                experiment_name='Test',
                base_scenario=str(scenario_dir),
                output_dir=str(output_dir)
            )

            variator = ParameterVariator(str(scenario_dir), [])
            executor = BatchExecutor(
                config=config,
                variator=variator,
                cost_manager=BatchCostManager(),
                error_handler=ErrorHandler()
            )

            # Mock to fail
            mock_run_scenario.side_effect = RuntimeError("Test error")

            variation = {
                "variation_id": 1,
                "description": "Test variation",
                "modifications": {}
            }

            with patch.object(variator, 'apply_variation_to_scenario', return_value=str(scenario_dir)):
                result = await executor.run_single_scenario("var-001-run-001", variation, 1)

            assert result['status'] == 'failed'
            assert "Test error" in result['error']

    @pytest.mark.asyncio
    async def test_run_single_scenario_budget_exceeded(self):
        """Test scenario execution when budget exceeded"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = create_test_scenario(tmpdir)
            output_dir = Path(tmpdir) / 'output'
            output_dir.mkdir()
            runs_dir = output_dir / 'runs'
            runs_dir.mkdir()

            config = BatchConfig(
                experiment_name='Test',
                base_scenario=str(scenario_dir),
                output_dir=str(output_dir)
            )

            # Create cost manager that won't allow runs
            cost_manager = BatchCostManager(budget_limit=0.01)
            cost_manager.total_spent = 0.02  # Already over budget

            executor = BatchExecutor(
                config=config,
                variator=ParameterVariator(str(scenario_dir), []),
                cost_manager=cost_manager,
                error_handler=ErrorHandler()
            )

            variation = {
                "variation_id": 1,
                "description": "Test variation",
                "modifications": {}
            }

            result = await executor.run_single_scenario("var-001-run-001", variation, 1)

            assert result['status'] == 'budget_exceeded'
