"""Tests for CLI module."""

import pytest
import sys
from unittest.mock import patch, MagicMock
from scenario_lab.cli import main

def test_cli_missing_args(capsys):
    """Test running CLI without arguments prints usage."""
    with patch("sys.argv", ["scenario_lab"]):
        # If main doesn't exit, it means it didn't find a command. 
        # We just check that it printed usage/help.
        try:
            main()
        except SystemExit:
            pass
        
        captured = capsys.readouterr()
        assert "usage:" in captured.err or "usage:" in captured.out

def test_cli_run_scenario(tmp_path):
    """Test running a scenario via CLI."""
    with patch("scenario_lab.cli.run_simulation") as mock_run:
        with patch("scenario_lab.cli.load_scenario") as mock_load:
            with patch("scenario_lab.cli.OutputManager") as MockOutputManager:
                # Setup mock scenario
                mock_scenario = MagicMock()
                mock_scenario.config.name = "Test Scenario"
                mock_load.return_value = mock_scenario
                
                # Setup mock output manager
                mock_output = MockOutputManager.return_value
                mock_output.start_run.return_value = tmp_path / "run_dir"
                
                # Mock LLM client
                with patch("scenario_lab.cli.LLMClient"):
                    # Run CLI
                    scenario_path = str(tmp_path / "scenarios/test-scenario")
                    with patch("sys.argv", ["scenario_lab", "run", scenario_path, "--turns", "5"]):
                        main()
                    
                    # Verify calls
                    mock_load.assert_called_once()
                    mock_run.assert_called_once()
                    _, kwargs = mock_run.call_args
                    assert kwargs["num_turns"] == 5

def test_cli_override_args():
    """Test --override arguments are parsed correctly."""
    with patch("scenario_lab.cli.run_simulation") as mock_run:
        with patch("scenario_lab.cli.load_scenario") as mock_load:
            with patch("scenario_lab.cli.OutputManager") as MockOutputManager:
                mock_scenario = MagicMock()
                mock_scenario.config.name = "Test Scenario"
                # Ensure config attributes exist so they can be set
                mock_scenario.config.foo = None 
                mock_scenario.config.baz = None
                mock_load.return_value = mock_scenario
                
                mock_output = MockOutputManager.return_value
                mock_output.start_run.return_value = MagicMock()

                with patch("scenario_lab.cli.LLMClient"):
                    with patch("sys.argv", ["scenario_lab", "run", "path", "--override", "foo=bar", "--override", "baz=qux"]):
                        main()
                    
                    # Check that overrides were applied
                    assert mock_scenario.config.foo == "bar"
                    assert mock_scenario.config.baz == "qux"
