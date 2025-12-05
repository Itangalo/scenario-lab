"""Tests for branch functionality."""

import json
import pytest
from pathlib import Path
from scenario_lab.resume import create_branch


@pytest.fixture
def parent_run_dir(tmp_path):
    """Create a parent run directory with completed turns."""
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
        "total_turns": 3,
        "final_metrics": {"test_metric": 60},
        "history": [
            {"turn": 1, "metrics": {"test_metric": 50}},
            {"turn": 2, "metrics": {"test_metric": 55}},
            {"turn": 3, "metrics": {"test_metric": 60}}
        ],
        "occurred_events": ["event1"],
        "status": "completed"
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    # Create three complete turns
    for turn_num in range(1, 4):
        turn_dir = run_dir / f"turn-{turn_num:02d}"
        turn_dir.mkdir()

        (turn_dir / "1-events.json").write_text("[]")

        actors_dir = turn_dir / "2-actors"
        actors_dir.mkdir()
        (actors_dir / "actor1.md").write_text(f"# Actor 1 Turn {turn_num}\n")

        (turn_dir / "3-metric-rules.md").write_text("# Metric Rules\n\n1. Test rule\n")
        (turn_dir / "4-metrics.json").write_text(
            json.dumps({"test_metric": 50 + (turn_num - 1) * 5}, indent=2)
        )
        (turn_dir / "4-world-state.md").write_text(f"# World State Turn {turn_num}\n")
        (turn_dir / "5-notepad.md").write_text(f"# Notepad Turn {turn_num}\n")

        if turn_num > 1:
            (turn_dir / "6-historical-summary.md").write_text(f"# Summary up to Turn {turn_num}\n")

    return run_dir


@pytest.fixture
def output_base(tmp_path):
    """Create output base directory (scenario directory)."""
    return tmp_path / "scenarios" / "test-scenario"


class TestCreateBranch:
    """Tests for create_branch function."""

    def test_basic_branch_creation(self, parent_run_dir, output_base):
        """Test creating a basic branch without modifications."""
        new_run_dir = create_branch(
            parent_run_dir,
            from_turn=2,
            output_base=output_base
        )

        # Verify new directory was created
        assert new_run_dir.exists()
        assert new_run_dir.is_dir()
        assert new_run_dir.name.startswith("run-")

        # Verify turn directories were copied
        assert (new_run_dir / "turn-01").exists()
        assert (new_run_dir / "turn-02").exists()
        assert not (new_run_dir / "turn-03").exists()  # Should not copy future turns

        # Verify files in turn directories
        assert (new_run_dir / "turn-01" / "1-events.json").exists()
        assert (new_run_dir / "turn-01" / "2-actors" / "actor1.md").exists()
        assert (new_run_dir / "turn-02" / "4-metrics.json").exists()

    def test_branch_config_metadata(self, parent_run_dir, output_base):
        """Test that branch metadata is added to config.json."""
        new_run_dir = create_branch(
            parent_run_dir,
            from_turn=2,
            output_base=output_base
        )

        # Read new config
        config = json.loads((new_run_dir / "config.json").read_text())

        # Check metadata
        assert "metadata" in config
        assert config["metadata"]["parent_run"] == parent_run_dir.name
        assert config["metadata"]["branch_turn"] == 2
        assert "branch_created_at" in config["metadata"]

    def test_branch_with_config_overrides(self, parent_run_dir, output_base):
        """Test branch with config overrides."""
        config_overrides = {
            "llm.events": "anthropic/claude-opus-4",
            "llm.temperature": "0.3"
        }

        new_run_dir = create_branch(
            parent_run_dir,
            from_turn=2,
            output_base=output_base,
            config_overrides=config_overrides
        )

        # Read new config
        config = json.loads((new_run_dir / "config.json").read_text())

        # Check overrides were applied
        assert config["llm"]["events"] == "anthropic/claude-opus-4"
        assert config["llm"]["temperature"] == "0.3"

        # Check metadata includes overrides
        assert config["metadata"]["config_overrides"] == config_overrides

    def test_branch_with_state_modifications(self, parent_run_dir, output_base):
        """Test branch with state modifications metadata."""
        state_mods = {
            "metrics": {"test_metric": 100},
            "narrative": "Modified narrative"
        }

        new_run_dir = create_branch(
            parent_run_dir,
            from_turn=2,
            output_base=output_base,
            state_modifications=state_mods
        )

        # Read new config
        config = json.loads((new_run_dir / "config.json").read_text())

        # Check metadata includes modifications
        assert config["metadata"]["state_modifications"] == state_mods

    def test_branch_summary_json(self, parent_run_dir, output_base):
        """Test that summary.json is created correctly for branch."""
        new_run_dir = create_branch(
            parent_run_dir,
            from_turn=2,
            output_base=output_base
        )

        # Read new summary
        summary = json.loads((new_run_dir / "summary.json").read_text())

        # Check history only includes up to branch point
        assert len(summary["history"]) == 2
        assert summary["history"][0]["turn"] == 1
        assert summary["history"][1]["turn"] == 2

        # Check final metrics are from turn 2
        assert summary["final_metrics"]["test_metric"] == 55
        assert summary["total_turns"] == 2

        # Check occurred events were copied
        assert summary["occurred_events"] == ["event1"]

        # Check status
        assert summary["status"] == "running"

        # Check metadata
        assert summary["metadata"]["parent_run"] == parent_run_dir.name
        assert summary["metadata"]["branch_turn"] == 2

    def test_branch_from_turn_1(self, parent_run_dir, output_base):
        """Test branching from turn 1."""
        new_run_dir = create_branch(
            parent_run_dir,
            from_turn=1,
            output_base=output_base
        )

        # Verify only turn 1 was copied
        assert (new_run_dir / "turn-01").exists()
        assert not (new_run_dir / "turn-02").exists()

        # Check summary
        summary = json.loads((new_run_dir / "summary.json").read_text())
        assert len(summary["history"]) == 1
        assert summary["total_turns"] == 1

    def test_branch_from_invalid_turn(self, parent_run_dir, output_base):
        """Test error when branching from turn that doesn't exist."""
        with pytest.raises(ValueError, match="Turn 10 does not exist"):
            create_branch(
                parent_run_dir,
                from_turn=10,
                output_base=output_base
            )

    def test_branch_from_turn_zero(self, parent_run_dir, output_base):
        """Test error when branching from turn 0."""
        with pytest.raises(ValueError, match="Cannot branch from turn 0"):
            create_branch(
                parent_run_dir,
                from_turn=0,
                output_base=output_base
            )

    def test_branch_from_invalid_parent(self, tmp_path, output_base):
        """Test error when parent directory is invalid."""
        invalid_dir = tmp_path / "invalid"
        invalid_dir.mkdir()

        with pytest.raises(ValueError, match="Invalid parent run directory"):
            create_branch(
                invalid_dir,
                from_turn=1,
                output_base=output_base
            )

    def test_branch_preserves_actor_files(self, parent_run_dir, output_base):
        """Test that actor files are preserved in branch."""
        new_run_dir = create_branch(
            parent_run_dir,
            from_turn=2,
            output_base=output_base
        )

        # Check actor files exist
        actor_file_t1 = new_run_dir / "turn-01" / "2-actors" / "actor1.md"
        actor_file_t2 = new_run_dir / "turn-02" / "2-actors" / "actor1.md"

        assert actor_file_t1.exists()
        assert actor_file_t2.exists()

        # Check content
        assert "Turn 1" in actor_file_t1.read_text()
        assert "Turn 2" in actor_file_t2.read_text()

    def test_branch_creates_runs_directory_if_needed(self, tmp_path):
        """Test that branch creates runs/ directory if it doesn't exist."""
        output_base = tmp_path / "scenarios" / "new-scenario"
        output_base.mkdir(parents=True)

        # Create a minimal parent run for testing
        parent_run_dir = tmp_path / "scenarios" / "test" / "runs" / "run-123"
        parent_run_dir.mkdir(parents=True)

        # Add minimal required files
        (parent_run_dir / "config.json").write_text(json.dumps({
            "name": "Test",
            "llm": {}
        }))
        (parent_run_dir / "summary.json").write_text(json.dumps({
            "scenario": "Test",
            "history": [{"turn": 1, "metrics": {}}],
            "occurred_events": [],
            "status": "completed"
        }))

        # Create turn 1
        turn_dir = parent_run_dir / "turn-01"
        turn_dir.mkdir()
        (turn_dir / "1-events.json").write_text("[]")
        actors_dir = turn_dir / "2-actors"
        actors_dir.mkdir()
        (actors_dir / "actor1.md").write_text("Test")
        (turn_dir / "3-metric-rules.md").write_text("Rules")
        (turn_dir / "4-metrics.json").write_text("{}")
        (turn_dir / "4-world-state.md").write_text("State")
        (turn_dir / "5-notepad.md").write_text("Notes")

        new_run_dir = create_branch(
            parent_run_dir,
            from_turn=1,
            output_base=output_base
        )

        # Verify runs directory was created
        assert (output_base / "runs").exists()
        assert new_run_dir.parent == output_base / "runs"
