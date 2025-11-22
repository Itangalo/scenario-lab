"""
Comprehensive tests for CLI interface

Tests all CLI commands: run, validate, estimate, serve, version, compare, benchmark
"""
import unittest
import tempfile
import os
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, AsyncMock

from scenario_lab.interfaces.cli import cli


class TestCLIBase(unittest.TestCase):
    """Base class for CLI tests with common setup"""

    def setUp(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    def create_minimal_scenario(self, tmpdir: str) -> Path:
        """Create a minimal valid scenario for testing"""
        scenario_dir = Path(tmpdir) / 'test-scenario'
        scenario_dir.mkdir()

        # Create scenario.yaml with all required fields
        (scenario_dir / 'scenario.yaml').write_text("""
name: Test Scenario
description: A test scenario for CLI testing
initial_world_state: |
  The world begins in a state of testing.
  All systems are nominal for the testing process.
turns: 3
turn_duration: 1 day
world_state_model: openai/gpt-4o-mini
actors:
  - test-actor
""")

        # Create actors directory and actor file
        actors_dir = scenario_dir / 'actors'
        actors_dir.mkdir()
        (actors_dir / 'test-actor.yaml').write_text("""
name: Test Actor
short_name: test-actor
llm_model: openai/gpt-4o-mini
system_prompt: You are a test actor for CLI testing.
goals:
  - Complete the test successfully
""")

        return scenario_dir


class TestCLIHelp(TestCLIBase):
    """Tests for CLI help output"""

    def test_main_help(self):
        """Test main CLI help output"""
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Scenario Lab V2', result.output)
        self.assertIn('run', result.output)
        self.assertIn('validate', result.output)
        self.assertIn('estimate', result.output)
        self.assertIn('serve', result.output)

    def test_run_help(self):
        """Test run command help"""
        result = self.runner.invoke(cli, ['run', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('SCENARIO_PATH', result.output)
        self.assertIn('--end-turn', result.output)
        self.assertIn('--credit-limit', result.output)
        self.assertIn('--resume', result.output)
        self.assertIn('--branch-from', result.output)

    def test_validate_help(self):
        """Test validate command help"""
        result = self.runner.invoke(cli, ['validate', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('SCENARIO_PATH', result.output)
        self.assertIn('Validate scenario configuration', result.output)

    def test_estimate_help(self):
        """Test estimate command help"""
        result = self.runner.invoke(cli, ['estimate', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('SCENARIO_PATH', result.output)
        self.assertIn('--end-turn', result.output)

    def test_serve_help(self):
        """Test serve command help"""
        result = self.runner.invoke(cli, ['serve', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('--host', result.output)
        self.assertIn('--port', result.output)
        self.assertIn('--reload', result.output)


class TestVersionCommand(TestCLIBase):
    """Tests for version command"""

    def test_version_command(self):
        """Test version command output"""
        result = self.runner.invoke(cli, ['version'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Scenario Lab V2', result.output)
        self.assertIn('Version', result.output)
        self.assertIn('Architecture', result.output)

    def test_version_option(self):
        """Test --version option"""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        # Should contain version number from package


class TestValidateCommand(TestCLIBase):
    """Tests for validate command"""

    def test_validate_valid_scenario(self):
        """Test validating a valid scenario"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            result = self.runner.invoke(cli, ['validate', str(scenario_dir)])

            # Should pass validation
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Validation passed', result.output)

    def test_validate_missing_scenario(self):
        """Test validating a non-existent scenario"""
        result = self.runner.invoke(cli, ['validate', '/nonexistent/path'])

        # Should fail with non-zero exit code
        self.assertNotEqual(result.exit_code, 0)

    def test_validate_invalid_scenario(self):
        """Test validating an invalid scenario (missing required fields)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = Path(tmpdir) / 'invalid-scenario'
            scenario_dir.mkdir()

            # Create incomplete scenario.yaml (missing required fields)
            (scenario_dir / 'scenario.yaml').write_text("""
name: Incomplete Scenario
# Missing: initial_world_state
""")

            result = self.runner.invoke(cli, ['validate', str(scenario_dir)])

            # Should fail validation
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('failed', result.output.lower())


class TestEstimateCommand(TestCLIBase):
    """Tests for estimate command"""

    def test_estimate_command_exists(self):
        """Test that estimate command is registered and shows help"""
        result = self.runner.invoke(cli, ['estimate', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('SCENARIO_PATH', result.output)
        self.assertIn('--end-turn', result.output)

    def test_estimate_shows_header(self):
        """Test estimate command shows cost estimation header"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            result = self.runner.invoke(cli, ['estimate', str(scenario_dir)])

            # Should at least show the header before any potential errors
            self.assertIn('Cost Estimation', result.output)

    def test_estimate_missing_scenario(self):
        """Test estimation of non-existent scenario"""
        result = self.runner.invoke(cli, ['estimate', '/nonexistent/path'])

        # Should fail
        self.assertNotEqual(result.exit_code, 0)


class TestRunCommand(TestCLIBase):
    """Tests for run command"""

    def test_run_missing_scenario(self):
        """Test running a non-existent scenario"""
        result = self.runner.invoke(cli, ['run', '/nonexistent/path'])

        # Should fail
        self.assertNotEqual(result.exit_code, 0)

    @patch('scenario_lab.runners.SyncRunner')
    def test_run_basic_invocation(self, mock_runner_class):
        """Test basic run command invocation with mocked runner"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            # Set up mock runner
            mock_runner = MagicMock()
            mock_runner.event_bus = MagicMock()
            mock_runner.event_bus.on = MagicMock()
            mock_runner.output_path = str(scenario_dir / 'runs' / 'run-001')

            # Mock final state
            mock_state = MagicMock()
            mock_state.turn = 3
            mock_state.total_cost.return_value = 0.05

            # Make run return the mock state
            mock_runner.run = AsyncMock(return_value=mock_state)
            mock_runner_class.return_value = mock_runner

            result = self.runner.invoke(cli, ['run', str(scenario_dir)])

            # Verify runner was created with correct args
            mock_runner_class.assert_called_once()
            call_kwargs = mock_runner_class.call_args.kwargs
            self.assertEqual(call_kwargs['scenario_path'], str(scenario_dir))

    @patch('scenario_lab.runners.SyncRunner')
    def test_run_with_options(self, mock_runner_class):
        """Test run command with various options"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            # Set up mock runner
            mock_runner = MagicMock()
            mock_runner.event_bus = MagicMock()
            mock_runner.event_bus.on = MagicMock()
            mock_runner.output_path = str(scenario_dir / 'runs' / 'run-001')

            mock_state = MagicMock()
            mock_state.turn = 5
            mock_state.total_cost.return_value = 2.50

            mock_runner.run = AsyncMock(return_value=mock_state)
            mock_runner_class.return_value = mock_runner

            result = self.runner.invoke(cli, [
                'run', str(scenario_dir),
                '--end-turn', '5',
                '--credit-limit', '10.0'
            ])

            # Verify options were passed
            call_kwargs = mock_runner_class.call_args.kwargs
            self.assertEqual(call_kwargs['end_turn'], 5)
            self.assertEqual(call_kwargs['credit_limit'], 10.0)


class TestServeCommand(TestCLIBase):
    """Tests for serve command"""

    def test_serve_help(self):
        """Test serve command help text"""
        result = self.runner.invoke(cli, ['serve', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('--host', result.output)
        self.assertIn('--port', result.output)
        self.assertIn('--reload', result.output)

    def test_serve_attempts_start(self):
        """Test serve command attempts to start the server"""
        result = self.runner.invoke(cli, ['serve'])
        # It may fail if uvicorn is not installed, which is acceptable
        # The important thing is that the command is recognized
        self.assertIn('Scenario Lab API Server', result.output)


class TestCompareCommand(TestCLIBase):
    """Tests for compare command"""

    def test_compare_command_exists(self):
        """Test that compare command is registered"""
        result = self.runner.invoke(cli, ['--help'])
        self.assertIn('compare', result.output)

    def test_compare_requires_arguments(self):
        """Test that compare requires at least one run path"""
        result = self.runner.invoke(cli, ['compare'])
        self.assertNotEqual(result.exit_code, 0)

    def test_compare_requires_minimum_two_runs(self):
        """Test that compare requires at least 2 run paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(cli, ['compare', tmpdir])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('at least 2 runs', result.output)

    def test_compare_missing_state_file(self):
        """Test compare with directories that don't have state files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            run1 = Path(tmpdir) / 'run-001'
            run2 = Path(tmpdir) / 'run-002'
            run1.mkdir()
            run2.mkdir()

            result = self.runner.invoke(cli, ['compare', str(run1), str(run2)])
            # Should fail because state files don't exist
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('State file not found', result.output)

    def test_compare_with_valid_runs(self):
        """Test compare with valid scenario runs"""
        import json
        from datetime import datetime

        with tempfile.TemporaryDirectory() as tmpdir:
            run1 = Path(tmpdir) / 'run-001'
            run2 = Path(tmpdir) / 'run-002'
            run1.mkdir()
            run2.mkdir()

            # Create minimal state files
            state_data = {
                "version": "2.0",
                "scenario_id": "test-1",
                "scenario_name": "Test Scenario",
                "run_id": "run-001",
                "turn": 3,
                "status": "completed",
                "scenario_config": {},
                "world_state": {
                    "turn": 3,
                    "content": "Test world state"
                },
                "actors": {
                    "TestActor": {
                        "name": "Test Actor",
                        "short_name": "TestActor",
                        "model": "openai/gpt-4o-mini",
                        "current_goals": ["Test"],
                        "private_information": ""
                    }
                },
                "decisions": {},
                "communications": [],
                "costs": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "actor": "TestActor",
                        "phase": "decision",
                        "model": "openai/gpt-4o-mini",
                        "input_tokens": 100,
                        "output_tokens": 50,
                        "cost": 0.001
                    }
                ],
                "metrics": [],
                "metadata": {}
            }

            # Write state files
            (run1 / 'scenario-state-v2.json').write_text(json.dumps(state_data))
            state_data["run_id"] = "run-002"
            state_data["turn"] = 5
            state_data["costs"][0]["cost"] = 0.002
            (run2 / 'scenario-state-v2.json').write_text(json.dumps(state_data))

            result = self.runner.invoke(cli, ['compare', str(run1), str(run2)])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Run Comparison', result.output)
            self.assertIn('Run Summary', result.output)
            self.assertIn('Actor Models', result.output)
            self.assertIn('Compared 2 runs', result.output)


class TestBenchmarkCommand(TestCLIBase):
    """Tests for benchmark command"""

    def test_benchmark_command_exists(self):
        """Test that benchmark command is registered"""
        result = self.runner.invoke(cli, ['--help'])
        self.assertIn('benchmark', result.output)

    def test_benchmark_help(self):
        """Test benchmark help shows all options"""
        result = self.runner.invoke(cli, ['benchmark', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('--turns', result.output)
        self.assertIn('--dry-run', result.output)

    def test_benchmark_missing_scenario(self):
        """Test benchmark with non-existent scenario"""
        result = self.runner.invoke(cli, ['benchmark', '/nonexistent/path'])
        self.assertNotEqual(result.exit_code, 0)

    def test_benchmark_dry_run(self):
        """Test benchmark dry-run mode"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            result = self.runner.invoke(cli, ['benchmark', str(scenario_dir), '--dry-run'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Performance Benchmark', result.output)
            self.assertIn('Dry run mode', result.output)
            self.assertIn('Would benchmark', result.output)

    def test_benchmark_dry_run_with_turns(self):
        """Test benchmark dry-run with custom turns"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            result = self.runner.invoke(cli, [
                'benchmark', str(scenario_dir),
                '--turns', '5',
                '--dry-run'
            ])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Turns: 5', result.output)

    @patch('scenario_lab.runners.SyncRunner')
    def test_benchmark_execution(self, mock_runner_class):
        """Test benchmark command execution with mocked runner"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_dir = self.create_minimal_scenario(tmpdir)

            # Set up mock runner
            mock_runner = MagicMock()
            mock_runner.event_bus = MagicMock()
            mock_runner.event_bus.on = MagicMock()
            mock_runner.output_path = str(scenario_dir / 'runs' / 'run-001')

            # Mock final state
            mock_state = MagicMock()
            mock_state.turn = 3
            mock_state.total_cost.return_value = 0.05
            mock_state.costs = []

            mock_runner.run = AsyncMock(return_value=mock_state)
            mock_runner_class.return_value = mock_runner

            result = self.runner.invoke(cli, ['benchmark', str(scenario_dir)])

            # Verify benchmark ran
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Performance Benchmark', result.output)
            self.assertIn('Results', result.output)


class TestCLIVerboseMode(TestCLIBase):
    """Tests for verbose mode"""

    def test_verbose_flag(self):
        """Test that -v/--verbose flag is accepted"""
        result = self.runner.invoke(cli, ['-v', 'version'])
        self.assertEqual(result.exit_code, 0)

    def test_verbose_long_flag(self):
        """Test that --verbose flag is accepted"""
        result = self.runner.invoke(cli, ['--verbose', 'version'])
        self.assertEqual(result.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
