"""Tests for resume functionality."""

import json
import pytest
from pathlib import Path
from scenario_lab.resume import (
    detect_last_turn,
    validate_run_directory,
    get_scenario_path_from_run,
    load_run_state,
)


@pytest.fixture
def temp_run_dir(tmp_path):
    """Create a temporary run directory structure."""
    run_dir = tmp_path / "scenarios" / "test-scenario" / "runs" / "run-20251205-120000"
    run_dir.mkdir(parents=True)

    # Create config.json
    config = {
        "name": "Test Scenario",
        "description": "Test",
        "start_date": "2026-01",
        "time_scale": "6 months per turn",
        "max_turns": 5,
        "actors": ["actor1"],
        "llm": {
            "events": "anthropic/claude-sonnet-4",
            "actors": "anthropic/claude-sonnet-4",
            "rules": "anthropic/claude-sonnet-4",
            "metrics": "anthropic/claude-sonnet-4",
            "temperature": 0.7,
            "max_tokens": 2000
        }
    }
    (run_dir / "config.json").write_text(json.dumps(config, indent=2))

    # Create summary.json
    summary = {
        "scenario": "Test Scenario",
        "total_turns": 0,
        "final_metrics": {},
        "history": [],
        "occurred_events": [],
        "status": "running"
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    return run_dir


@pytest.fixture
def scenario_dir(tmp_path):
    """Create a minimal scenario directory structure."""
    scenario_dir = tmp_path / "scenarios" / "test-scenario"
    scenario_dir.mkdir(parents=True, exist_ok=True)

    # Create scenario.yaml
    scenario_yaml = """
name: "Test Scenario"
description: "Test scenario for resume functionality"
start_date: "2026-01"
time_scale: "6 months per turn"
max_turns: 5
actors:
  - actor1
"""
    (scenario_dir / "scenario.yaml").write_text(scenario_yaml)

    # Create metrics.md
    metrics = """# Metrics

## test_metric
**Beskrivning:** Test metric
**ID:** test_metric
**Startvärde:** 50
**Min:** 0
**Max:** 100
**Enhet:** percent
"""
    (scenario_dir / "metrics.md").write_text(metrics)

    # Create events.md
    (scenario_dir / "events.md").write_text("# Events\n")

    # Create metric-rules.md
    (scenario_dir / "metric-rules.md").write_text("# Metric Rules\n\n1. Test rule\n")

    # Create background directory
    bg_dir = scenario_dir / "background"
    bg_dir.mkdir()

    (bg_dir / "context.md").write_text("# Context\n\nInitial world state.")

    # Create actors directory
    actors_dir = bg_dir / "actors"
    actors_dir.mkdir()

    actor1 = """# Actor 1

**Beskrivning:** Test actor
**Mål:** Test goal
"""
    (actors_dir / "actor1.md").write_text(actor1)

    return scenario_dir


def create_complete_turn(run_dir: Path, turn_num: int):
    """Helper to create a complete turn directory."""
    turn_dir = run_dir / f"turn-{turn_num:02d}"
    turn_dir.mkdir(exist_ok=True)

    # Create all required files
    (turn_dir / "1-events.json").write_text("[]")

    actors_dir = turn_dir / "2-actors"
    actors_dir.mkdir(exist_ok=True)
    (actors_dir / "actor1.md").write_text("# Actor 1 Actions\n")

    (turn_dir / "3-metric-rules.md").write_text("# Metric Rules\n\n1. Test rule\n")
    (turn_dir / "4-metrics.json").write_text(json.dumps({"test_metric": 50}, indent=2))
    (turn_dir / "4-world-state.md").write_text("# World State\n")
    (turn_dir / "5-notepad.md").write_text("# Notepad\n")

    if turn_num > 1:
        (turn_dir / "6-historical-summary.md").write_text("# Historical Summary\n")


def create_incomplete_turn(run_dir: Path, turn_num: int):
    """Helper to create an incomplete turn directory (missing some files)."""
    turn_dir = run_dir / f"turn-{turn_num:02d}"
    turn_dir.mkdir(exist_ok=True)

    # Only create some files (incomplete turn)
    (turn_dir / "1-events.json").write_text("[]")
    (turn_dir / "4-metrics.json").write_text(json.dumps({"test_metric": 50}, indent=2))


class TestDetectLastTurn:
    """Tests for detect_last_turn function."""

    def test_empty_run_returns_zero(self, temp_run_dir):
        """Test that a run with no turns returns 0."""
        assert detect_last_turn(temp_run_dir) == 0

    def test_single_complete_turn(self, temp_run_dir):
        """Test detection of a single complete turn."""
        create_complete_turn(temp_run_dir, 1)
        assert detect_last_turn(temp_run_dir) == 1

    def test_multiple_complete_turns(self, temp_run_dir):
        """Test detection with multiple complete turns."""
        create_complete_turn(temp_run_dir, 1)
        create_complete_turn(temp_run_dir, 2)
        create_complete_turn(temp_run_dir, 3)
        assert detect_last_turn(temp_run_dir) == 3

    def test_incomplete_turn_ignored(self, temp_run_dir):
        """Test that incomplete turns are ignored."""
        create_complete_turn(temp_run_dir, 1)
        create_complete_turn(temp_run_dir, 2)
        create_incomplete_turn(temp_run_dir, 3)  # Incomplete
        assert detect_last_turn(temp_run_dir) == 2

    def test_nonexistent_directory_raises_error(self, tmp_path):
        """Test that nonexistent directory raises ValueError."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(ValueError, match="does not exist"):
            detect_last_turn(nonexistent)

    def test_file_instead_of_directory_raises_error(self, tmp_path):
        """Test that a file path raises ValueError."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        with pytest.raises(ValueError, match="not a directory"):
            detect_last_turn(file_path)


class TestValidateRunDirectory:
    """Tests for validate_run_directory function."""

    def test_valid_directory(self, temp_run_dir):
        """Test validation of a valid run directory."""
        create_complete_turn(temp_run_dir, 1)
        is_valid, errors = validate_run_directory(temp_run_dir)
        assert is_valid
        assert len(errors) == 0

    def test_missing_config(self, temp_run_dir):
        """Test validation fails when config.json is missing."""
        (temp_run_dir / "config.json").unlink()
        is_valid, errors = validate_run_directory(temp_run_dir)
        assert not is_valid
        assert "Missing config.json" in errors

    def test_missing_summary(self, temp_run_dir):
        """Test validation fails when summary.json is missing."""
        (temp_run_dir / "summary.json").unlink()
        is_valid, errors = validate_run_directory(temp_run_dir)
        assert not is_valid
        assert "Missing summary.json" in errors

    def test_no_turn_directories(self, temp_run_dir):
        """Test validation fails when no turn directories exist."""
        is_valid, errors = validate_run_directory(temp_run_dir)
        assert not is_valid
        assert "No turn directories found" in errors

    def test_nonexistent_directory(self, tmp_path):
        """Test validation fails for nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"
        is_valid, errors = validate_run_directory(nonexistent)
        assert not is_valid
        assert "does not exist" in errors[0]


class TestGetScenarioPathFromRun:
    """Tests for get_scenario_path_from_run function."""

    def test_correct_path_navigation(self, temp_run_dir, scenario_dir):
        """Test that function correctly navigates to scenario directory."""
        result = get_scenario_path_from_run(temp_run_dir)
        assert result == scenario_dir

    def test_nonexistent_run_directory(self, tmp_path):
        """Test error when run directory doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(ValueError, match="does not exist"):
            get_scenario_path_from_run(nonexistent)

    def test_invalid_structure(self, tmp_path):
        """Test error when directory structure is invalid."""
        # Create a run dir without proper parent structure
        invalid_dir = tmp_path / "not-runs" / "run-123"
        invalid_dir.mkdir(parents=True)

        with pytest.raises(ValueError, match="Expected parent directory to be 'runs'"):
            get_scenario_path_from_run(invalid_dir)


class TestLoadRunState:
    """Tests for load_run_state function."""

    def test_load_basic_state(self, temp_run_dir, scenario_dir):
        """Test loading basic run state."""
        create_complete_turn(temp_run_dir, 1)

        # Update summary.json with turn data
        summary = json.loads((temp_run_dir / "summary.json").read_text())
        summary["history"] = [{"turn": 1, "metrics": {"test_metric": 50}}]
        summary["total_turns"] = 1
        (temp_run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

        scenario, turn = load_run_state(temp_run_dir)

        assert turn == 1
        assert scenario.config.name == "Test Scenario"
        assert "test_metric" in scenario.metrics.metrics
        assert scenario.metrics.metrics["test_metric"].value == 50

    def test_load_with_from_turn(self, temp_run_dir, scenario_dir):
        """Test loading from a specific turn."""
        create_complete_turn(temp_run_dir, 1)
        create_complete_turn(temp_run_dir, 2)

        # Update metrics for turn 2
        (temp_run_dir / "turn-02" / "4-metrics.json").write_text(
            json.dumps({"test_metric": 75}, indent=2)
        )

        scenario, turn = load_run_state(temp_run_dir, from_turn=2)

        assert turn == 2
        assert scenario.metrics.metrics["test_metric"].value == 75

    def test_load_with_state_modifications(self, temp_run_dir, scenario_dir):
        """Test loading with metric modifications."""
        create_complete_turn(temp_run_dir, 1)

        state_mods = {
            "metrics": {"test_metric": 90},
            "narrative": "Modified narrative"
        }

        scenario, turn = load_run_state(temp_run_dir, state_modifications=state_mods)

        assert scenario.metrics.metrics["test_metric"].value == 90
        assert scenario.world_state.narrative == "Modified narrative"

    def test_invalid_run_directory(self, tmp_path):
        """Test error when run directory is invalid."""
        invalid_dir = tmp_path / "invalid"
        invalid_dir.mkdir()

        with pytest.raises(ValueError, match="Invalid run directory"):
            load_run_state(invalid_dir)

    def test_no_completed_turns(self, temp_run_dir, scenario_dir):
        """Test error when no completed turns exist."""
        with pytest.raises(ValueError, match="Invalid run directory"):
            load_run_state(temp_run_dir)

    def test_turn_does_not_exist(self, temp_run_dir, scenario_dir):
        """Test error when specified turn doesn't exist."""
        create_complete_turn(temp_run_dir, 1)

        with pytest.raises(ValueError, match="Turn 5 does not exist"):
            load_run_state(temp_run_dir, from_turn=5)

    def test_load_occurred_events(self, temp_run_dir, scenario_dir):
        """Test that occurred events are loaded correctly."""
        create_complete_turn(temp_run_dir, 1)

        # Add occurred events to summary
        summary = json.loads((temp_run_dir / "summary.json").read_text())
        summary["occurred_events"] = ["event1", "event2"]
        (temp_run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

        scenario, _ = load_run_state(temp_run_dir)

        assert "event1" in scenario.occurred_events
        assert "event2" in scenario.occurred_events
