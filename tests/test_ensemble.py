"""Tests for ensemble analysis module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scenario_lab.ensemble import analyze_ensemble, format_ensemble_report


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _write_run(
    scenario_dir: Path,
    run_name: str,
    history: list[dict],
    events_by_turn: dict[int, list[dict]],
    evaluations_by_turn: dict[int, list[dict]] | None = None,
    occurred_events: list[str] | None = None,
    status: str = "completed",
    config_llm: dict | None = None,
    cost_usd: float | None = None,
    historical_summary: str | None = None,
    config_extra: dict | None = None,
) -> Path:
    """Write a synthetic run directory under <scenario_dir>/runs/<run_name>/."""
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

    llm_block = config_llm or {"events": "openrouter:model-a", "actors": "openrouter:model-a"}
    config: dict = {"name": "Test Scenario", "llm": llm_block}
    if config_extra:
        config.update(config_extra)
    (run_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    if cost_usd is not None:
        costs: dict = {"total_cost_usd": cost_usd, "total_tokens": 1000}
        (run_dir / "costs.json").write_text(json.dumps(costs, indent=2), encoding="utf-8")

    max_turn = max(events_by_turn.keys()) if events_by_turn else total_turns
    for turn in range(1, max_turn + 1):
        turn_dir = run_dir / f"turn-{turn:02d}"
        turn_dir.mkdir(parents=True, exist_ok=True)

        events = events_by_turn.get(turn, [])
        (turn_dir / "1-events.json").write_text(json.dumps(events, indent=2), encoding="utf-8")

        if evaluations_by_turn and turn in evaluations_by_turn:
            (turn_dir / "1-event-evaluations.json").write_text(
                json.dumps(evaluations_by_turn[turn], indent=2), encoding="utf-8"
            )

        metrics = next(
            (entry["metrics"] for entry in history if entry.get("turn") == turn), {}
        )
        (turn_dir / "4-metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        if historical_summary is not None and turn == max_turn:
            (turn_dir / "6-historical-summary.md").write_text(
                historical_summary, encoding="utf-8"
            )

    return run_dir


# ---------------------------------------------------------------------------
# Core analysis tests
# ---------------------------------------------------------------------------

def test_analyze_ensemble_happy_path(tmp_path):
    """Happy path: 3 runs, 2 turns, 2 metrics, 2 events."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    _write_run(
        scenario_dir, "run-20250101-000001",
        history=[
            {"turn": 1, "metrics": {"gdp": 100, "sentiment": 50}},
            {"turn": 2, "metrics": {"gdp": 110, "sentiment": 55}},
        ],
        events_by_turn={
            1: [{"id": "boom"}],
            2: [],
        },
        occurred_events=["boom"],
        cost_usd=0.10,
    )
    _write_run(
        scenario_dir, "run-20250102-000002",
        history=[
            {"turn": 1, "metrics": {"gdp": 90, "sentiment": 45}},
            {"turn": 2, "metrics": {"gdp": 95, "sentiment": 40}},
        ],
        events_by_turn={
            1: [],
            2: [{"id": "crisis"}],
        },
        occurred_events=["crisis"],
        cost_usd=0.12,
    )
    _write_run(
        scenario_dir, "run-20250103-000003",
        history=[
            {"turn": 1, "metrics": {"gdp": 105, "sentiment": 48}},
            {"turn": 2, "metrics": {"gdp": 115, "sentiment": 60}},
        ],
        events_by_turn={
            1: [{"id": "boom"}],
            2: [],
        },
        occurred_events=["boom"],
        cost_usd=0.11,
    )

    result = analyze_ensemble(scenario_dir)

    assert result["scenario"] == "scenario"
    assert result["run_overview"]["num_runs"] == 3
    assert result["run_overview"]["status_mix"] == {"completed": 3}

    traj = result["metric_trajectories"]
    assert "gdp" in traj
    assert "sentiment" in traj

    turn1_gdp = traj["gdp"][1]
    assert turn1_gdp["n"] == 3.0
    assert turn1_gdp["min"] == 90.0
    assert turn1_gdp["max"] == 105.0

    ev_stats = result["event_statistics"]
    assert "boom" in ev_stats
    assert ev_stats["boom"]["overall_occurrence_count"] == 2
    assert ev_stats["boom"]["overall_occurrence_rate"] == pytest.approx(2 / 3, abs=0.01)

    assert "crisis" in ev_stats
    assert ev_stats["crisis"]["overall_occurrence_count"] == 1

    # cost summary
    assert result["run_overview"]["total_cost_usd"] == pytest.approx(0.33, abs=0.01)


def test_analyze_ensemble_legacy_run_without_evaluations(tmp_path):
    """Legacy run without 1-event-evaluations.json should be handled gracefully."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    _write_run(
        scenario_dir, "run-20250101-000001",
        history=[{"turn": 1, "metrics": {"m1": 10}}],
        events_by_turn={1: [{"id": "e1"}]},
        evaluations_by_turn=None,  # no evaluation file – legacy
        occurred_events=["e1"],
    )
    _write_run(
        scenario_dir, "run-20250102-000002",
        history=[{"turn": 1, "metrics": {"m1": 20}}],
        events_by_turn={1: []},
        evaluations_by_turn=None,
        occurred_events=[],
    )

    result = analyze_ensemble(scenario_dir)
    assert result["run_overview"]["num_runs"] == 2

    # No eval prob data should be present
    for ev in result["event_statistics"].values():
        assert ev["mean_evaluated_probability_per_turn"] == {}

    caveats = result["caveats"]
    # Should warn about missing evaluations
    assert any("evaluations" in c.lower() or "1-event-evaluations" in c for c in caveats)


def test_analyze_ensemble_with_evaluations(tmp_path):
    """Runs with 1-event-evaluations.json should populate mean_evaluated_probability."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    evals_run1 = {
        1: [{"id": "e1", "probability": 0.4, "roll": 0.2, "triggered": True}],
    }
    evals_run2 = {
        1: [{"id": "e1", "probability": 0.6, "roll": 0.7, "triggered": False}],
    }

    _write_run(
        scenario_dir, "run-20250101-000001",
        history=[{"turn": 1, "metrics": {"m1": 10}}],
        events_by_turn={1: [{"id": "e1"}]},
        evaluations_by_turn=evals_run1,
        occurred_events=["e1"],
    )
    _write_run(
        scenario_dir, "run-20250102-000002",
        history=[{"turn": 1, "metrics": {"m1": 20}}],
        events_by_turn={1: []},
        evaluations_by_turn=evals_run2,
        occurred_events=[],
    )

    result = analyze_ensemble(scenario_dir)
    ev = result["event_statistics"]["e1"]
    # Mean of 0.4 and 0.6 = 0.5
    assert ev["mean_evaluated_probability_per_turn"][1] == pytest.approx(0.5, abs=0.01)


def test_analyze_ensemble_no_runs_raises(tmp_path):
    """Should raise ValueError if no completed runs exist."""
    scenario_dir = tmp_path / "empty"
    scenario_dir.mkdir()
    (scenario_dir / "runs").mkdir()

    with pytest.raises(ValueError, match="No completed runs"):
        analyze_ensemble(scenario_dir)


def test_analyze_ensemble_max_runs(tmp_path):
    """max_runs should limit to most recent N runs."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    for i in range(5):
        _write_run(
            scenario_dir, f"run-2025010{i}-00000{i}",
            history=[{"turn": 1, "metrics": {"m1": float(i * 10)}}],
            events_by_turn={1: []},
            occurred_events=[],
        )

    result = analyze_ensemble(scenario_dir, max_runs=2)
    assert result["run_overview"]["num_runs"] == 2


def test_analyze_ensemble_small_n_caveat(tmp_path):
    """Reports with fewer than 10 runs should include a small-N caveat."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    _write_run(
        scenario_dir, "run-20250101-000001",
        history=[{"turn": 1, "metrics": {"m1": 10}}],
        events_by_turn={1: []},
        occurred_events=[],
    )

    result = analyze_ensemble(scenario_dir)
    assert any("N" in c or "run" in c.lower() for c in result["caveats"])


def test_analyze_ensemble_mixed_configs_caveat(tmp_path):
    """Runs with different model configs should trigger a caveat."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    _write_run(
        scenario_dir, "run-20250101-000001",
        history=[{"turn": 1, "metrics": {"m1": 10}}],
        events_by_turn={1: []},
        occurred_events=[],
        config_llm={"events": "openrouter:model-a"},
    )
    _write_run(
        scenario_dir, "run-20250102-000002",
        history=[{"turn": 1, "metrics": {"m1": 20}}],
        events_by_turn={1: []},
        occurred_events=[],
        config_llm={"events": "openrouter:model-b"},
    )

    result = analyze_ensemble(scenario_dir)
    assert any("model" in c.lower() for c in result["caveats"])


def test_format_ensemble_report_contains_sections(tmp_path):
    """format_ensemble_report should produce all required sections."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    _write_run(
        scenario_dir, "run-20250101-000001",
        history=[{"turn": 1, "metrics": {"m1": 10}}],
        events_by_turn={1: [{"id": "e1"}]},
        occurred_events=["e1"],
    )

    result = analyze_ensemble(scenario_dir)
    report = format_ensemble_report(result)

    assert "# Ensemble Analysis" in report
    assert "## Run Overview" in report
    assert "## Metric Trajectories" in report
    assert "## Event Statistics" in report
    assert "## Divergence Detection" in report


def test_analyze_ensemble_early_ended_run(tmp_path):
    """Runs that ended early should drop out of later turns gracefully."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    # Run 1: 3 turns
    _write_run(
        scenario_dir, "run-20250101-000001",
        history=[
            {"turn": 1, "metrics": {"m1": 10}},
            {"turn": 2, "metrics": {"m1": 20}},
            {"turn": 3, "metrics": {"m1": 30}},
        ],
        events_by_turn={1: [], 2: [], 3: []},
        occurred_events=[],
    )
    # Run 2: only 2 turns
    _write_run(
        scenario_dir, "run-20250102-000002",
        history=[
            {"turn": 1, "metrics": {"m1": 15}},
            {"turn": 2, "metrics": {"m1": 25}},
        ],
        events_by_turn={1: [], 2: []},
        occurred_events=[],
    )

    result = analyze_ensemble(scenario_dir)
    traj = result["metric_trajectories"]["m1"]

    # Turn 1 and 2 should have 2 runs each
    assert traj[1]["n"] == 2.0
    assert traj[2]["n"] == 2.0
    # Turn 3 should have only 1 run
    assert traj[3]["n"] == 1.0


# ---------------------------------------------------------------------------
# CLI-level tests
# ---------------------------------------------------------------------------

def test_cli_ensemble_command(tmp_path, capsys):
    """CLI ensemble command should print a report without API calls."""
    from scenario_lab.cli import main

    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    _write_run(
        scenario_dir, "run-20250101-000001",
        history=[{"turn": 1, "metrics": {"m1": 10}}],
        events_by_turn={1: []},
        occurred_events=[],
    )

    with patch("sys.argv", ["scenario_lab", "ensemble", str(scenario_dir)]):
        main()

    captured = capsys.readouterr()
    assert "Ensemble Analysis" in captured.out


def test_cli_ensemble_json_output(tmp_path, capsys):
    """CLI ensemble --json should produce valid JSON."""
    from scenario_lab.cli import main

    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    _write_run(
        scenario_dir, "run-20250101-000001",
        history=[{"turn": 1, "metrics": {"m1": 10}}],
        events_by_turn={1: []},
        occurred_events=[],
    )

    with patch("sys.argv", ["scenario_lab", "ensemble", str(scenario_dir), "--json"]):
        main()

    captured = capsys.readouterr()
    # The output after the "Analyzing ensemble" line should be valid JSON
    output_lines = captured.out.strip().splitlines()
    json_part = "\n".join(
        line for line in output_lines if not line.startswith("Analyzing")
    )
    parsed = json.loads(json_part)
    assert "scenario" in parsed


def test_cli_ensemble_output_file(tmp_path, capsys):
    """CLI ensemble --output should write report to file."""
    from scenario_lab.cli import main

    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    _write_run(
        scenario_dir, "run-20250101-000001",
        history=[{"turn": 1, "metrics": {"m1": 10}}],
        events_by_turn={1: []},
        occurred_events=[],
    )

    output_path = tmp_path / "report.md"

    with patch("sys.argv", ["scenario_lab", "ensemble", str(scenario_dir), "--output", str(output_path)]):
        main()

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Ensemble Analysis" in content


def test_cli_ensemble_no_runs_error(tmp_path, capsys):
    """CLI ensemble should print an error when no runs exist."""
    from scenario_lab.cli import main

    scenario_dir = tmp_path / "empty"
    scenario_dir.mkdir()
    (scenario_dir / "runs").mkdir()

    with patch("sys.argv", ["scenario_lab", "ensemble", str(scenario_dir)]):
        result = main()

    captured = capsys.readouterr()
    assert "failed" in captured.out.lower() or result == 1


# ---------------------------------------------------------------------------
# Narrative diversity
# ---------------------------------------------------------------------------

def test_narrative_diversity_distinct_texts(tmp_path):
    """Lexically different summaries give low similarity and no caveat."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    history = [{"turn": 1, "metrics": {"gdp": 100}}]
    _write_run(
        scenario_dir, "run-a", history, {1: []},
        historical_summary="Unemployment surged while protests spread through Stockholm suburbs.",
    )
    _write_run(
        scenario_dir, "run-b", history, {1: []},
        historical_summary="Exports boomed after semiconductor deals reshaped Nordic industry alliances.",
    )

    report = analyze_ensemble(scenario_dir)
    diversity = report["narrative_diversity"]
    assert diversity["n_texts"] == 2
    assert diversity["mean_pairwise_similarity"] < 0.2
    assert not any("monoculture" in c for c in report["caveats"])


def test_narrative_diversity_similar_texts_flagged(tmp_path):
    """Near-identical summaries raise the storyline-monoculture caveat."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    history = [{"turn": 1, "metrics": {"gdp": 100}}]
    text = "Tripartite cooperation delivered steady adoption gains while reskilling programs expanded."
    _write_run(scenario_dir, "run-a", history, {1: []}, historical_summary=text)
    _write_run(
        scenario_dir, "run-b", history, {1: []},
        historical_summary=text + " Momentum continued.",
    )

    report = analyze_ensemble(scenario_dir)
    diversity = report["narrative_diversity"]
    assert diversity["mean_pairwise_similarity"] > 0.5
    assert any("monoculture" in c for c in report["caveats"])

    rendered = format_ensemble_report(report)
    assert "## Narrative Diversity" in rendered


def test_narrative_diversity_absent_without_summaries(tmp_path):
    """Runs without historical summaries omit the section gracefully."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    history = [{"turn": 1, "metrics": {"gdp": 100}}]
    _write_run(scenario_dir, "run-a", history, {1: []})
    _write_run(scenario_dir, "run-b", history, {1: []})

    report = analyze_ensemble(scenario_dir)
    assert report["narrative_diversity"] is None
    rendered = format_ensemble_report(report)
    assert "## Narrative Diversity" not in rendered


# ---------------------------------------------------------------------------
# Cohort filtering and grouping
# ---------------------------------------------------------------------------

def _arm_extra(arm: str, draw: str) -> dict:
    return {
        "actors": ["regulator"],
        "initial_state": {
            "notes": f"arm={arm}; draw={draw}; regime fixed for the whole run",
            "source": f"scenarios/s/draws/{arm}/draw-{draw}.json",
        },
    }


def test_analyze_ensemble_without_grouping_has_no_comparison(tmp_path):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    history = [{"turn": 1, "metrics": {"m1": 10}}]
    _write_run(scenario_dir, "run-a", history, {1: []}, config_extra=_arm_extra("fast", "001"))
    _write_run(scenario_dir, "run-b", history, {1: []}, config_extra=_arm_extra("plateau", "002"))

    result = analyze_ensemble(scenario_dir)
    assert "cohort_comparison" not in result


def test_analyze_ensemble_with_filters_restricts_population(tmp_path):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    history = [{"turn": 1, "metrics": {"m1": 10}}]
    for name, arm in [("run-a", "fast"), ("run-b", "plateau"), ("run-c", "fast")]:
        _write_run(scenario_dir, name, history, {1: []}, config_extra=_arm_extra(arm, "0"))

    result = analyze_ensemble(scenario_dir, filters=[("arm", "fast")])
    assert result["run_overview"]["num_runs"] == 2
    assert any("excluded by filter" in c for c in result["caveats"])


def test_analyze_ensemble_filter_no_match_lists_available_keys(tmp_path):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    history = [{"turn": 1, "metrics": {"m1": 10}}]
    _write_run(scenario_dir, "run-a", history, {1: []}, config_extra=_arm_extra("fast", "001"))

    with pytest.raises(ValueError, match="Available keys"):
        analyze_ensemble(scenario_dir, filters=[("arm", "rlvr-limited")])


def test_analyze_ensemble_group_by_adds_comparison(tmp_path):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    _write_run(
        scenario_dir, "run-a", [{"turn": 1, "metrics": {"m1": 10}}], {1: [{"id": "e1"}]},
        occurred_events=["e1"], config_extra=_arm_extra("fast", "001"),
    )
    _write_run(
        scenario_dir, "run-b", [{"turn": 1, "metrics": {"m1": 30}}], {1: []},
        config_extra=_arm_extra("plateau", "002"),
    )
    _write_run(
        scenario_dir, "run-c", [{"turn": 1, "metrics": {"m1": 20}}], {1: []},
        config_extra=_arm_extra("fast", "003"),
    )

    result = analyze_ensemble(scenario_dir, group_by="arm")
    comparison = result["cohort_comparison"]
    assert comparison["group_by"] == "arm"

    by_cohort = {g["cohort"]: g["n_runs"] for g in comparison["groups"]}
    assert by_cohort == {"fast": 2, "plateau": 1}

    # fast final m1 mean: (10 + 20) / 2; plateau: 30
    assert comparison["final_metrics_mean"]["m1"]["fast"] == pytest.approx(15.0)
    assert comparison["final_metrics_mean"]["m1"]["plateau"] == pytest.approx(30.0)
    assert comparison["event_occurrence_rate"]["e1"]["fast"] == pytest.approx(0.5)
    assert comparison["event_occurrence_rate"]["e1"]["plateau"] == pytest.approx(0.0)

    # Pooled sections still cover all three runs
    assert result["run_overview"]["num_runs"] == 3


def test_analyze_ensemble_group_by_warns_on_small_groups(tmp_path):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    history = [{"turn": 1, "metrics": {"m1": 10}}]
    for name, arm in [("run-a", "fast"), ("run-b", "plateau"), ("run-c", "plateau")]:
        _write_run(scenario_dir, name, history, {1: []}, config_extra=_arm_extra(arm, "0"))

    result = analyze_ensemble(scenario_dir, group_by="arm")
    assert any("'fast'" in c and "fewer than 3" in c for c in result["caveats"])


def test_analyze_ensemble_flags_mixed_scenario_identities(tmp_path):
    """A variant's runs sharing runs/ must be surfaced, not silently pooled."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    history = [{"turn": 1, "metrics": {"m1": 10}}]
    _write_run(scenario_dir, "run-a", history, {1: []})
    _write_run(
        scenario_dir, "run-b", history, {1: []},
        config_extra={"name": "Test Scenario — Urgent", "actors": ["regulator-urgent"]},
    )

    result = analyze_ensemble(scenario_dir)
    caveat = next(c for c in result["caveats"] if "different scenario identities" in c)
    assert "--filter" in caveat
    assert "Test Scenario — Urgent" in caveat


def test_format_ensemble_report_renders_cohort_section(tmp_path):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    _write_run(
        scenario_dir, "run-a", [{"turn": 1, "metrics": {"m1": 10}}], {1: [{"id": "e1"}]},
        occurred_events=["e1"], config_extra=_arm_extra("fast", "001"),
    )
    _write_run(
        scenario_dir, "run-b", [{"turn": 1, "metrics": {"m1": 30}}], {1: []},
        config_extra=_arm_extra("plateau", "002"),
    )

    result = analyze_ensemble(scenario_dir, group_by="arm")
    report = format_ensemble_report(result)

    assert "## Cohort Comparison (group-by: arm)" in report
    assert "| fast | 1 |" in report
    assert "Final metric mean per cohort" in report
    assert "Event occurrence rate per cohort" in report
