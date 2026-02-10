"""Tests for CLI module."""

import pytest
import sys
import json
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


def test_cli_resume_no_additional_turns_skips_simulation(tmp_path):
    """Resume should finalize immediately when start_turn is beyond requested turns."""
    run_dir = tmp_path / "scenarios" / "test-scenario" / "runs" / "run-123"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(json.dumps({"status": "completed"}), encoding="utf-8")

    mock_scenario = MagicMock()
    mock_scenario.config.max_turns = 5
    mock_scenario.config.llm.events = "model-e"
    mock_scenario.config.llm.actors = "model-a"
    mock_scenario.config.llm.rules = "model-r"
    mock_scenario.config.llm.metrics = "model-m"

    with patch("scenario_lab.resume.validate_run_directory", return_value=(True, [])):
        with patch("scenario_lab.resume.detect_last_turn", return_value=2):
            with patch("scenario_lab.resume.load_run_state", return_value=(mock_scenario, 2)):
                with patch("scenario_lab.cli.OutputManager") as MockOutputManager:
                    with patch("scenario_lab.cli.run_simulation") as mock_run:
                        with patch("sys.argv", ["scenario_lab", "resume", str(run_dir), "--turns", "2"]):
                            main()

                        mock_run.assert_not_called()
                        MockOutputManager.return_value.finalize_summary.assert_called_once_with([])


def test_cli_branch_no_additional_turns_skips_simulation(tmp_path):
    """Branch should finalize immediately when no turns remain after branch point."""
    parent_run = tmp_path / "scenarios" / "test-scenario" / "runs" / "run-parent"
    parent_run.mkdir(parents=True)
    new_run = tmp_path / "scenarios" / "test-scenario" / "runs" / "run-new"
    new_run.mkdir(parents=True)
    (new_run / "summary.json").write_text(json.dumps({"status": "running"}), encoding="utf-8")

    mock_scenario = MagicMock()
    mock_scenario.config.max_turns = 5
    mock_scenario.config.llm.events = "model-e"
    mock_scenario.config.llm.actors = "model-a"
    mock_scenario.config.llm.rules = "model-r"
    mock_scenario.config.llm.metrics = "model-m"
    mock_scenario.metrics.metrics = {}

    with patch("scenario_lab.resume.get_scenario_path_from_run", return_value=tmp_path / "scenarios" / "test-scenario"):
        with patch("scenario_lab.resume.create_branch", return_value=new_run):
            with patch("scenario_lab.resume.load_run_state", return_value=(mock_scenario, 2)):
                with patch("scenario_lab.resume.persist_scenario_state_at_turn") as mock_persist:
                    with patch("scenario_lab.resume.sync_summary_turn_state") as mock_sync:
                        with patch("scenario_lab.cli.OutputManager") as MockOutputManager:
                            with patch("scenario_lab.cli.run_simulation") as mock_run:
                                with patch("sys.argv", ["scenario_lab", "branch", str(parent_run), "--from-turn", "2", "--turns", "2"]):
                                    main()

                                mock_persist.assert_called_once()
                                mock_sync.assert_called_once()
                                mock_run.assert_not_called()
                                MockOutputManager.return_value.finalize_summary.assert_called_once_with([])
