"""Tests for model-sensitivity analysis module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scenario_lab.model_sensitivity import (
    analyze_model_sensitivity,
    format_model_sensitivity_report,
)


# ---------------------------------------------------------------------------
# Fixture helper (same pattern as test_ensemble.py)
# ---------------------------------------------------------------------------

def _write_run(
    scenario_dir: Path,
    run_name: str,
    history: list[dict],
    occurred_events: list[str] | None = None,
    status: str = "completed",
    config_llm: dict | None = None,
) -> Path:
    run_dir = scenario_dir / "runs" / run_name
    run_dir.mkdir(parents=True)

    total_turns = history[-1]["turn"] if history else 0
    final_metrics = history[-1]["metrics"] if history else {}

    summary: dict = {
        "scenario": "Test Scenario",
        "total_turns": total_turns,
        "final_metrics": final_metrics,
        "history": history,
        "occurred_events": occurred_events or [],
        "status": status,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    llm_block = config_llm or {
        "events": "openrouter:model-a",
        "actors": "openrouter:model-a",
        "rules": "openrouter:model-a",
        "metrics": "openrouter:model-a",
        "summary": "openrouter:model-a",
        "referee": "openrouter:model-a",
    }
    config: dict = {"name": "Test Scenario", "llm": llm_block}
    (run_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    # Write minimal turn directories so the run loads cleanly. Occurrence is
    # derived from per-turn 1-events.json, so triggered events go there
    # (on the first turn) rather than only in summary.json.
    for i, entry in enumerate(history):
        turn = entry["turn"]
        turn_dir = run_dir / f"turn-{turn:02d}"
        turn_dir.mkdir(parents=True, exist_ok=True)
        triggered = (
            [{"id": eid, "probability": 0.5} for eid in (occurred_events or [])]
            if i == 0
            else []
        )
        (turn_dir / "1-events.json").write_text(
            json.dumps(triggered, indent=2), encoding="utf-8"
        )
        (turn_dir / "4-metrics.json").write_text(
            json.dumps(entry["metrics"], indent=2), encoding="utf-8"
        )

    return run_dir


_LLM_A = {
    "events": "openrouter:model-a",
    "actors": "openrouter:model-a",
    "rules": "openrouter:model-a",
    "metrics": "openrouter:model-a",
    "summary": "openrouter:model-a",
    "referee": "openrouter:model-a",
}

_LLM_B = {
    "events": "openrouter:model-b",
    "actors": "openrouter:model-b",
    "rules": "openrouter:model-b",
    "metrics": "openrouter:model-b",
    "summary": "openrouter:model-b",
    "referee": "openrouter:model-b",
}


# ---------------------------------------------------------------------------
# Core analysis tests
# ---------------------------------------------------------------------------

def test_analyze_model_sensitivity_two_groups(tmp_path):
    """Two model groups should be detected and compared."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    # Group A: higher gdp outcomes
    _write_run(
        scenario_dir, "run-A-001",
        history=[{"turn": 2, "metrics": {"gdp": 200, "sentiment": 70}}],
        occurred_events=["boom"],
        config_llm=_LLM_A,
    )
    _write_run(
        scenario_dir, "run-A-002",
        history=[{"turn": 2, "metrics": {"gdp": 220, "sentiment": 75}}],
        occurred_events=["boom"],
        config_llm=_LLM_A,
    )
    _write_run(
        scenario_dir, "run-A-003",
        history=[{"turn": 2, "metrics": {"gdp": 210, "sentiment": 72}}],
        occurred_events=["boom"],
        config_llm=_LLM_A,
    )

    # Group B: lower gdp outcomes
    _write_run(
        scenario_dir, "run-B-001",
        history=[{"turn": 2, "metrics": {"gdp": 100, "sentiment": 40}}],
        occurred_events=["crisis"],
        config_llm=_LLM_B,
    )
    _write_run(
        scenario_dir, "run-B-002",
        history=[{"turn": 2, "metrics": {"gdp": 90, "sentiment": 35}}],
        occurred_events=["crisis"],
        config_llm=_LLM_B,
    )
    _write_run(
        scenario_dir, "run-B-003",
        history=[{"turn": 2, "metrics": {"gdp": 95, "sentiment": 38}}],
        occurred_events=["crisis"],
        config_llm=_LLM_B,
    )

    result = analyze_model_sensitivity(scenario_dir)

    assert len(result["groups"]) == 2
    assert result["robustness"]["single_group"] is False

    # gdp means: group A ~210, group B ~95 – should be sensitive
    assert "gdp" in result["robustness"]["sensitive_metrics"]

    # events: boom rate 1.0 in A, 0.0 in B – difference 1.0 > 0.3
    assert "boom" in result["robustness"]["sensitive_events"]

    # per_metric entries exist for gdp and sentiment
    metric_ids = {e["metric"] for e in result["per_metric"]}
    assert "gdp" in metric_ids
    assert "sentiment" in metric_ids


def test_analyze_model_sensitivity_single_group(tmp_path):
    """When all runs use the same model, sensitivity cannot be assessed."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    for i in range(3):
        _write_run(
            scenario_dir, f"run-A-00{i}",
            history=[{"turn": 1, "metrics": {"m1": float(i * 10)}}],
            occurred_events=[],
            config_llm=_LLM_A,
        )

    result = analyze_model_sensitivity(scenario_dir)

    assert len(result["groups"]) == 1
    assert result["robustness"]["single_group"] is True
    assert result["robustness"]["sensitive_metrics"] == []
    assert result["robustness"]["sensitive_events"] == []

    caveats = result["caveats"]
    assert any("one model group" in c.lower() or "same model" in c.lower() for c in caveats)


def test_analyze_model_sensitivity_no_runs_raises(tmp_path):
    """Should raise ValueError when no completed runs exist."""
    scenario_dir = tmp_path / "empty"
    scenario_dir.mkdir()
    (scenario_dir / "runs").mkdir()

    with pytest.raises(ValueError, match="No completed runs"):
        analyze_model_sensitivity(scenario_dir)


def test_analyze_model_sensitivity_legacy_run(tmp_path):
    """Legacy runs without 1-event-evaluations.json should load without error."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    # Write a run without any turn-level evaluation files (legacy)
    run_dir = scenario_dir / "runs" / "run-legacy-001"
    run_dir.mkdir(parents=True)
    summary = {
        "scenario": "Test",
        "total_turns": 1,
        "final_metrics": {"m1": 10},
        "history": [{"turn": 1, "metrics": {"m1": 10}}],
        "occurred_events": ["e1"],
        "status": "completed",
    }
    (run_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    config = {"name": "Test", "llm": _LLM_A}
    (run_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")

    result = analyze_model_sensitivity(scenario_dir)
    assert result["run_overview"]["num_runs"] == 1 if "run_overview" in result else result["groups"][0]["n_runs"] == 1


def test_analyze_model_sensitivity_max_runs(tmp_path):
    """max_runs should be forwarded to run discovery."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    for i in range(5):
        _write_run(
            scenario_dir, f"run-A-00{i}",
            history=[{"turn": 1, "metrics": {"m1": float(i * 10)}}],
            occurred_events=[],
            config_llm=_LLM_A,
        )

    result = analyze_model_sensitivity(scenario_dir, max_runs=2)
    total = sum(g["n_runs"] for g in result["groups"])
    assert total == 2


# ---------------------------------------------------------------------------
# Report formatting tests
# ---------------------------------------------------------------------------

def test_format_single_group_report(tmp_path):
    """Single-group report should contain the sensitivity-unavailable message."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    _write_run(
        scenario_dir, "run-A-001",
        history=[{"turn": 1, "metrics": {"m1": 10}}],
        occurred_events=[],
        config_llm=_LLM_A,
    )

    result = analyze_model_sensitivity(scenario_dir)
    report = format_model_sensitivity_report(result)

    assert "# Model Sensitivity" in report
    assert "one model group" in report.lower() or "cannot be assessed" in report.lower()


def test_format_two_group_report_contains_sections(tmp_path):
    """Two-group report should include all required sections."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    for llm, prefix in [(_LLM_A, "A"), (_LLM_B, "B")]:
        for i in range(2):
            _write_run(
                scenario_dir, f"run-{prefix}-00{i}",
                history=[{"turn": 1, "metrics": {"m1": 10 if prefix == "A" else 100}}],
                occurred_events=["e1" if prefix == "A" else "e2"],
                config_llm=llm,
            )

    result = analyze_model_sensitivity(scenario_dir)
    report = format_model_sensitivity_report(result)

    assert "# Model Sensitivity" in report
    assert "## Model Groups" in report
    assert "## Final Metric Distributions by Group" in report
    assert "## Event Occurrence Rates by Group" in report
    assert "## Robustness Summary" in report


# ---------------------------------------------------------------------------
# CLI-level tests
# ---------------------------------------------------------------------------

def test_cli_model_sensitivity_command(tmp_path, capsys):
    """CLI model-sensitivity command should print a report without API calls."""
    from scenario_lab.cli import main

    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    for llm, prefix in [(_LLM_A, "A"), (_LLM_B, "B")]:
        _write_run(
            scenario_dir, f"run-{prefix}-001",
            history=[{"turn": 1, "metrics": {"m1": 10 if prefix == "A" else 50}}],
            occurred_events=[],
            config_llm=llm,
        )

    with patch("sys.argv", ["scenario_lab", "model-sensitivity", str(scenario_dir)]):
        main()

    captured = capsys.readouterr()
    assert "Model Sensitivity" in captured.out


def test_cli_model_sensitivity_json_output(tmp_path, capsys):
    """CLI model-sensitivity --json should produce valid JSON."""
    from scenario_lab.cli import main

    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    _write_run(
        scenario_dir, "run-A-001",
        history=[{"turn": 1, "metrics": {"m1": 10}}],
        occurred_events=[],
        config_llm=_LLM_A,
    )

    with patch("sys.argv", ["scenario_lab", "model-sensitivity", str(scenario_dir), "--json"]):
        main()

    captured = capsys.readouterr()
    output_lines = captured.out.strip().splitlines()
    json_part = "\n".join(
        line for line in output_lines if not line.startswith("Analyzing")
    )
    parsed = json.loads(json_part)
    assert "scenario" in parsed
    assert "groups" in parsed


def test_cli_model_sensitivity_output_file(tmp_path):
    """CLI model-sensitivity --output should write report to file."""
    from scenario_lab.cli import main

    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    _write_run(
        scenario_dir, "run-A-001",
        history=[{"turn": 1, "metrics": {"m1": 10}}],
        occurred_events=[],
        config_llm=_LLM_A,
    )

    output_path = tmp_path / "sensitivity.md"

    with patch("sys.argv", ["scenario_lab", "model-sensitivity", str(scenario_dir), "--output", str(output_path)]):
        main()

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Model Sensitivity" in content


def test_cli_model_sensitivity_no_runs_error(tmp_path, capsys):
    """CLI model-sensitivity should print an error when no runs exist."""
    from scenario_lab.cli import main

    scenario_dir = tmp_path / "empty"
    scenario_dir.mkdir()
    (scenario_dir / "runs").mkdir()

    with patch("sys.argv", ["scenario_lab", "model-sensitivity", str(scenario_dir)]):
        result = main()

    captured = capsys.readouterr()
    assert "failed" in captured.out.lower() or result == 1
