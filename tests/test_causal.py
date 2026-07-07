"""Tests for causal-impact planning, discovery, analysis, and CLI."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scenario_lab.causal import (
    analyze_causal_impact,
    discover_causal_branches,
    format_causal_report,
    plan_causal_jobs,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _write_branch_run(
    scenario_dir: Path,
    run_name: str,
    *,
    event_id: str,
    mode: str,
    seed: int,
    final_metrics: dict[str, float],
    status: str = "completed",
    parent_run: str = "run-parent",
) -> Path:
    run_dir = scenario_dir / "runs" / run_name
    run_dir.mkdir(parents=True)
    overrides = {
        "turn": 2,
        "force": [event_id] if mode == "force" else [],
        "suppress": [event_id] if mode == "suppress" else [],
    }
    config = {
        "name": "Test Scenario",
        "random_seed": seed,
        "event_overrides": overrides,
        "parent_run": f"scenarios/test/runs/{parent_run}",
    }
    (run_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")
    summary = {
        "scenario": "Test Scenario",
        "status": status,
        "total_turns": 3,
        "final_metrics": final_metrics,
        "history": [],
        "occurred_events": [],
    }
    (run_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return run_dir


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------

def test_plan_causal_jobs_matched_pairs(tmp_path):
    jobs = plan_causal_jobs(
        tmp_path / "run-parent",
        ["strike"],
        repeats=3,
        from_turn=2,
        turns=8,
        base_seed=100,
    )
    assert len(jobs) == 6  # 3 pairs x (force + suppress)

    forced = [j for j in jobs if j.mode == "force"]
    suppressed = [j for j in jobs if j.mode == "suppress"]
    assert sorted(j.seed for j in forced) == [100, 101, 102]
    # Each pair shares one seed across force and suppress.
    assert sorted(j.seed for j in forced) == sorted(j.seed for j in suppressed)

    command = forced[0].command
    assert "branch" in command
    assert "--force-event" in command and "strike" in command
    assert "--from-turn" in command and "2" in command
    assert "--turns" in command and "8" in command


def test_plan_causal_jobs_rejects_bad_repeats(tmp_path):
    with pytest.raises(ValueError):
        plan_causal_jobs(tmp_path, ["e"], repeats=0, from_turn=1)


# ---------------------------------------------------------------------------
# Discovery and analysis
# ---------------------------------------------------------------------------

def test_discover_groups_by_override_mode(tmp_path):
    scenario_dir = tmp_path / "scenario"
    _write_branch_run(scenario_dir, "run-f1", event_id="strike", mode="force",
                      seed=1, final_metrics={"gdp": 90})
    _write_branch_run(scenario_dir, "run-s1", event_id="strike", mode="suppress",
                      seed=1, final_metrics={"gdp": 110})
    # Different event and incomplete run should be excluded.
    _write_branch_run(scenario_dir, "run-other", event_id="boom", mode="force",
                      seed=2, final_metrics={"gdp": 100})
    _write_branch_run(scenario_dir, "run-crashed", event_id="strike", mode="force",
                      seed=3, final_metrics={"gdp": 80}, status="crashed")

    groups = discover_causal_branches(scenario_dir, "strike")
    assert [d.name for d in groups["force"]] == ["run-f1"]
    assert [d.name for d in groups["suppress"]] == ["run-s1"]


def test_analyze_causal_impact_paired_effects(tmp_path):
    scenario_dir = tmp_path / "scenario"
    _write_branch_run(scenario_dir, "run-f1", event_id="strike", mode="force",
                      seed=1, final_metrics={"gdp": 90, "sentiment": 40})
    _write_branch_run(scenario_dir, "run-f2", event_id="strike", mode="force",
                      seed=2, final_metrics={"gdp": 80, "sentiment": 30})
    _write_branch_run(scenario_dir, "run-s1", event_id="strike", mode="suppress",
                      seed=1, final_metrics={"gdp": 100, "sentiment": 50})
    _write_branch_run(scenario_dir, "run-s2", event_id="strike", mode="suppress",
                      seed=2, final_metrics={"gdp": 110, "sentiment": 60})

    report = analyze_causal_impact(scenario_dir, "strike")
    assert report["n_forced"] == 2
    assert report["n_suppressed"] == 2
    assert report["n_pairs"] == 2

    gdp = report["metrics"]["gdp"]
    assert gdp["mean_effect"] == pytest.approx(-20.0)
    assert gdp["paired_mean_effect"] == pytest.approx(-20.0)
    assert sorted(gdp["paired_diffs"]) == [-30.0, -10.0]

    rendered = format_causal_report(report)
    assert "Causal Impact: strike" in rendered
    assert "-20.00" in rendered


def test_analyze_requires_both_groups(tmp_path):
    scenario_dir = tmp_path / "scenario"
    _write_branch_run(scenario_dir, "run-f1", event_id="strike", mode="force",
                      seed=1, final_metrics={"gdp": 90})

    with pytest.raises(ValueError, match="suppressed"):
        analyze_causal_impact(scenario_dir, "strike")


def test_unpaired_runs_get_caveat(tmp_path):
    scenario_dir = tmp_path / "scenario"
    _write_branch_run(scenario_dir, "run-f1", event_id="strike", mode="force",
                      seed=1, final_metrics={"gdp": 90})
    _write_branch_run(scenario_dir, "run-s1", event_id="strike", mode="suppress",
                      seed=99, final_metrics={"gdp": 110})

    report = analyze_causal_impact(scenario_dir, "strike")
    assert report["n_pairs"] == 0
    assert any("seed-matched" in c.lower() for c in report["caveats"])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_causal_impact_report_only(capsys):
    """--report-only analyzes existing branches without launching jobs."""
    import shutil
    import tempfile

    from scenario_lab.cli import main

    with tempfile.TemporaryDirectory() as tmp:
        scenario_dir = Path(tmp) / "sweden-ai-2030"
        source = Path("scenarios/sweden-ai-2030")
        for item in source.iterdir():
            if item.name == "runs":
                continue
            if item.is_dir():
                shutil.copytree(item, scenario_dir / item.name)
            else:
                shutil.copy2(item, scenario_dir / item.name)

        _write_branch_run(scenario_dir, "run-f1", event_id="strike", mode="force",
                          seed=1, final_metrics={"unemployment": 12})
        _write_branch_run(scenario_dir, "run-s1", event_id="strike", mode="suppress",
                          seed=1, final_metrics={"unemployment": 9})

        with patch(
            "sys.argv",
            ["scenario_lab", "causal-impact", str(scenario_dir),
             "--event", "strike", "--report-only"],
        ):
            result = main()

        captured = capsys.readouterr()
        assert result == 0
        assert "Causal Impact: strike" in captured.out


def test_cli_causal_impact_dry_run(capsys):
    """--dry-run prints planned branch commands without executing."""
    import shutil
    import tempfile

    from scenario_lab.cli import main

    with tempfile.TemporaryDirectory() as tmp:
        scenario_dir = Path(tmp) / "sweden-ai-2030"
        source = Path("scenarios/sweden-ai-2030")
        for item in source.iterdir():
            if item.name == "runs":
                continue
            if item.is_dir():
                shutil.copytree(item, scenario_dir / item.name)
            else:
                shutil.copy2(item, scenario_dir / item.name)

        # A baseline completed parent run for planning.
        parent = scenario_dir / "runs" / "run-parent"
        parent.mkdir(parents=True)
        (parent / "config.json").write_text(
            json.dumps({"name": "Test", "random_seed": 7}), encoding="utf-8"
        )
        (parent / "summary.json").write_text(
            json.dumps({"status": "completed", "total_turns": 3,
                        "final_metrics": {}, "history": []}),
            encoding="utf-8",
        )

        with patch(
            "sys.argv",
            ["scenario_lab", "causal-impact", str(scenario_dir),
             "--event", "strike", "--repeats", "2", "--seed", "50", "--dry-run"],
        ):
            result = main()

        captured = capsys.readouterr()
        assert result == 0
        assert "Planned branches: 4" in captured.out
        assert "--force-event" in captured.out
        assert "--suppress-event" in captured.out
        assert "seed=50" in captured.out


def test_cli_causal_impact_unknown_event(capsys):
    from scenario_lab.cli import main

    with patch(
        "sys.argv",
        ["scenario_lab", "causal-impact", "scenarios/sweden-ai-2030",
         "--event", "not_a_real_event", "--report-only"],
    ):
        result = main()

    captured = capsys.readouterr()
    assert result == 1
    assert "Unknown event" in captured.out


def test_cli_causal_impact_lists_events_without_event_arg(capsys):
    from scenario_lab.cli import main

    with patch(
        "sys.argv",
        ["scenario_lab", "causal-impact", "scenarios/sweden-ai-2030", "--report-only"],
    ):
        result = main()

    captured = capsys.readouterr()
    assert result == 1
    assert "Available events" in captured.out
    assert "strike" in captured.out
