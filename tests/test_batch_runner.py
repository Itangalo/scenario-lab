"""
Tests for Batch Runner module

Tests batch configuration, variation generation, execution modes, and state management.
"""
import pytest
import tempfile
import os
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from scenario_lab.batch.batch_runner import BatchRunner


class TestBatchRunnerInit:
    """Tests for BatchRunner initialization"""

    def test_init_with_valid_config(self):
        """Test initialization with valid configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test scenario
            scenario_dir = Path(tmpdir) / 'test-scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("""
name: Test Scenario
initial_world_state: Test state
turns: 3
""")
            actors_dir = scenario_dir / 'actors'
            actors_dir.mkdir()
            (actors_dir / 'actor1.yaml').write_text("""
name: Actor 1
short_name: a1
llm_model: openai/gpt-4o-mini
""")

            # Create config
            config_path = Path(tmpdir) / 'batch-config.yaml'
            config_path.write_text(f"""
experiment_name: Test Experiment
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
runs_per_variation: 2
max_parallel: 1
variations: []
""")

            runner = BatchRunner(str(config_path))

            assert runner.experiment_name == "Test Experiment"
            assert runner.base_scenario == str(scenario_dir)
            assert runner.runs_per_variation == 2
            assert runner.max_parallel == 1

    def test_init_missing_config_file(self):
        """Test that missing config file raises error"""
        with pytest.raises(FileNotFoundError):
            BatchRunner("/nonexistent/config.yaml")

    def test_init_missing_required_fields(self):
        """Test that missing required fields raise error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'batch-config.yaml'
            config_path.write_text("""
experiment_name: Test
# Missing base_scenario and output_dir
""")

            with pytest.raises(ValueError, match="Missing required field"):
                BatchRunner(str(config_path))

    def test_init_missing_base_scenario(self):
        """Test that missing base scenario raises error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'batch-config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: /nonexistent/scenario
output_dir: {tmpdir}/output
""")

            with pytest.raises(FileNotFoundError, match="Base scenario not found"):
                BatchRunner(str(config_path))


class TestBatchRunnerRunId:
    """Tests for run ID generation"""

    def test_generate_run_id_format(self):
        """Test run ID format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal valid setup
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
""")

            runner = BatchRunner(str(config_path))

            run_id = runner._generate_run_id(1, 1)
            assert run_id == "var-001-run-001"

            run_id = runner._generate_run_id(5, 10)
            assert run_id == "var-005-run-010"

            run_id = runner._generate_run_id(123, 456)
            assert run_id == "var-123-run-456"


class TestBatchRunnerStateManagement:
    """Tests for batch state save/load"""

    def test_save_and_load_state(self):
        """Test saving and loading batch state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
""")

            runner = BatchRunner(str(config_path))
            runner._setup_output_directory()

            # Set some state
            runner.completed_runs = {"var-001-run-001", "var-001-run-002"}
            runner.failed_runs = [{"run_id": "var-002-run-001", "error": "Test error"}]
            runner.variations = [{"variation_id": 1, "description": "Test"}]
            runner.start_time = datetime.now()

            # Save state
            runner._save_batch_state()

            # Verify files exist
            assert os.path.exists(os.path.join(runner.output_dir, 'batch-state.json'))
            assert os.path.exists(os.path.join(runner.output_dir, 'batch-costs.json'))

            # Create new runner and load state
            runner2 = BatchRunner(str(config_path))
            loaded = runner2._load_batch_state()

            assert loaded is True
            assert runner2.completed_runs == {"var-001-run-001", "var-001-run-002"}
            assert len(runner2.failed_runs) == 1

    def test_load_state_no_previous_state(self):
        """Test loading state when no previous state exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
""")

            runner = BatchRunner(str(config_path))
            loaded = runner._load_batch_state()

            assert loaded is False


class TestBatchRunnerSetup:
    """Tests for output directory setup"""

    def test_setup_output_directory(self):
        """Test output directory creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            output_dir = Path(tmpdir) / 'output'
            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {output_dir}
""")

            runner = BatchRunner(str(config_path))
            runner._setup_output_directory()

            assert output_dir.exists()
            assert (output_dir / 'runs').exists()
            assert (output_dir / 'batch-config.yaml').exists()


class TestBatchRunnerDryRun:
    """Tests for dry-run preview mode"""

    @patch('builtins.print')
    def test_dry_run_shows_preview(self, mock_print):
        """Test that dry-run mode shows preview without executing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("""
name: Test Scenario
initial_world_state: Test state
turns: 3
""")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("""
name: Actor 1
short_name: a1
llm_model: openai/gpt-4o-mini
""")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test Experiment
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
runs_per_variation: 2
variations: []
""")

            runner = BatchRunner(str(config_path), dry_run=True)
            runner.run()

            # Should have printed preview info
            assert mock_print.called
            # Get all printed content
            printed = ' '.join(str(call) for call in mock_print.call_args_list)
            assert 'BATCH PREVIEW' in printed or 'Experiment' in printed


class TestBatchRunnerVariations:
    """Tests for variation handling"""

    def test_variations_list_format(self):
        """Test variations in list format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
variations:
  - type: actor_model
    actor: a
    values:
      - openai/gpt-4o-mini
      - openai/gpt-4o
""")

            runner = BatchRunner(str(config_path))
            # Variator should be initialized
            assert runner.variator is not None

    def test_variations_dict_format(self):
        """Test variations in dict format (converted to list)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
variations:
  actor_models:
    a:
      - openai/gpt-4o-mini
      - openai/gpt-4o
""")

            runner = BatchRunner(str(config_path))
            assert runner.variator is not None


class TestBatchRunnerBudget:
    """Tests for budget management"""

    def test_budget_limit_configuration(self):
        """Test budget limit from configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
budget_limit: 10.00
cost_per_run_limit: 1.00
""")

            runner = BatchRunner(str(config_path))

            assert runner.cost_manager.budget_limit == 10.00
            assert runner.cost_manager.cost_per_run_limit == 1.00

    def test_no_budget_limit(self):
        """Test with no budget limit"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
""")

            runner = BatchRunner(str(config_path))

            assert runner.cost_manager.budget_limit is None


class TestBatchRunnerSummary:
    """Tests for summary generation"""

    def test_generate_summary(self):
        """Test summary generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test Summary
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
runs_per_variation: 2
""")

            runner = BatchRunner(str(config_path))
            runner._setup_output_directory()

            # Set up state
            runner.variations = [
                {"variation_id": 1, "description": "Test 1"},
                {"variation_id": 2, "description": "Test 2"}
            ]
            runner.completed_runs = {"var-001-run-001", "var-001-run-002"}
            runner.failed_runs = [{"run_id": "var-002-run-001", "error": "Test error", "status": "failed"}]
            runner.start_time = datetime.now()
            runner.end_time = datetime.now()

            runner._generate_summary()

            # Check summary file was created
            summary_file = os.path.join(runner.output_dir, 'batch-summary.json')
            assert os.path.exists(summary_file)

            with open(summary_file, 'r') as f:
                summary = json.load(f)

            assert summary['experiment_name'] == 'Test Summary'
            assert summary['runs_completed'] == 2
            assert summary['runs_failed'] == 1


class TestBatchRunnerExecution:
    """Tests for batch execution"""

    @pytest.mark.asyncio
    @patch('scenario_lab.batch.batch_runner.run_scenario_async')
    async def test_run_single_scenario_success(self, mock_run_scenario):
        """Test successful single scenario execution"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
""")

            runner = BatchRunner(str(config_path))
            runner._setup_output_directory()

            # Mock the scenario execution
            mock_state = MagicMock()
            mock_state.total_cost.return_value = 0.05
            mock_run_scenario.return_value = mock_state

            variation = {
                "variation_id": 1,
                "description": "Test variation",
                "modifications": {}
            }

            # Mock apply_variation_to_scenario
            with patch.object(runner.variator, 'apply_variation_to_scenario', return_value=str(scenario_dir)):
                result = await runner._run_single_scenario("var-001-run-001", variation, 1)

            assert result['status'] == 'success'
            assert result['cost'] == 0.05

    @pytest.mark.asyncio
    @patch('scenario_lab.batch.batch_runner.run_scenario_async')
    async def test_run_single_scenario_failure(self, mock_run_scenario):
        """Test failed single scenario execution"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
""")

            runner = BatchRunner(str(config_path))
            runner._setup_output_directory()

            # Mock the scenario execution to fail
            mock_run_scenario.side_effect = RuntimeError("Test error")

            variation = {
                "variation_id": 1,
                "description": "Test variation",
                "modifications": {}
            }

            with patch.object(runner.variator, 'apply_variation_to_scenario', return_value=str(scenario_dir)):
                result = await runner._run_single_scenario("var-001-run-001", variation, 1)

            assert result['status'] == 'failed'
            assert "Test error" in result['error']


class TestBatchRunnerExecutionModes:
    """Tests for sequential and parallel execution modes"""

    def test_max_parallel_configuration(self):
        """Test max_parallel configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            # Sequential mode (default)
            config_path = Path(tmpdir) / 'config1.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output1
""")

            runner1 = BatchRunner(str(config_path))
            assert runner1.max_parallel == 1

            # Parallel mode
            config_path2 = Path(tmpdir) / 'config2.yaml'
            config_path2.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output2
max_parallel: 4
""")

            runner2 = BatchRunner(str(config_path2))
            assert runner2.max_parallel == 4


class TestBatchRunnerResumeMode:
    """Tests for resume mode"""

    def test_resume_mode_flag(self):
        """Test resume mode flag"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
""")

            runner = BatchRunner(str(config_path), resume=True)
            assert runner.resume_mode is True

            runner2 = BatchRunner(str(config_path), resume=False)
            assert runner2.resume_mode is False


class TestBatchRunnerProgressDisplay:
    """Tests for progress display options"""

    def test_progress_display_flag(self):
        """Test progress display flag"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'scenario'
            scenario_dir.mkdir()
            (scenario_dir / 'scenario.yaml').write_text("name: Test\ninitial_world_state: Test\nturns: 1")
            (scenario_dir / 'actors').mkdir()
            (scenario_dir / 'actors' / 'a.yaml').write_text("name: A\nshort_name: a\nllm_model: m")

            config_path = Path(tmpdir) / 'config.yaml'
            config_path.write_text(f"""
experiment_name: Test
base_scenario: {scenario_dir}
output_dir: {tmpdir}/output
""")

            runner = BatchRunner(str(config_path), progress_display=True)
            assert runner.progress_display is True

            runner2 = BatchRunner(str(config_path), progress_display=False)
            assert runner2.progress_display is False
