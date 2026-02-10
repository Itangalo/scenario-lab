"""Tests for scenario run calibration analysis."""

import json
from pathlib import Path

from scenario_lab.calibration import analyze_runs, format_analysis_report


def _create_run(base_dir: Path, run_name: str, history: list[dict], events_by_turn: dict[int, list[dict]]):
    run_dir = base_dir / "runs" / run_name
    run_dir.mkdir(parents=True)

    total_turns = history[-1]["turn"] if history else 0
    final_metrics = history[-1]["metrics"] if history else {}

    summary = {
        "scenario": "Test Scenario",
        "total_turns": total_turns,
        "final_metrics": final_metrics,
        "history": history,
        "occurred_events": [],
        "status": "completed",
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    for turn, events in events_by_turn.items():
        turn_dir = run_dir / f"turn-{turn:02d}"
        turn_dir.mkdir(parents=True, exist_ok=True)
        (turn_dir / "1-events.json").write_text(json.dumps(events, indent=2), encoding="utf-8")


def test_analyze_runs_aggregates_metrics_and_event_rates(tmp_path):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()

    _create_run(
        scenario_dir,
        "run-20250101-000001",
        history=[
            {"turn": 1, "metrics": {"m1": 10, "m2": 5}},
            {"turn": 2, "metrics": {"m1": 20, "m2": 7}},
        ],
        events_by_turn={
            1: [{"id": "e1", "probability": 0.1}],
            2: [{"id": "e2", "probability": 0.2}],
        },
    )

    _create_run(
        scenario_dir,
        "run-20250102-000002",
        history=[
            {"turn": 1, "metrics": {"m1": 30, "m2": 9}},
            {"turn": 2, "metrics": {"m1": 40, "m2": 11}},
        ],
        events_by_turn={
            1: [{"id": "e1", "probability": 0.15}],
            2: [],
        },
    )

    analysis = analyze_runs(scenario_dir)
    assert analysis["runs_analyzed"] == 2
    assert analysis["turns_seen"] == [1, 2]

    turn1_m1 = analysis["metric_stats_by_turn"][1]["m1"]
    assert turn1_m1["mean"] == 20.0
    assert turn1_m1["min"] == 10.0
    assert turn1_m1["max"] == 30.0

    # e1 appears in both runs at turn 1 -> rate 1.0
    assert analysis["event_rates_by_turn"][1]["e1"]["count"] == 2
    assert analysis["event_rates_by_turn"][1]["e1"]["rate"] == 1.0

    # e2 appears once out of two runs at turn 2 -> rate 0.5
    assert analysis["event_rates_by_turn"][2]["e2"]["count"] == 1
    assert analysis["event_rates_by_turn"][2]["e2"]["rate"] == 0.5


def test_format_analysis_report_contains_sections(tmp_path):
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    _create_run(
        scenario_dir,
        "run-20250101-000001",
        history=[{"turn": 1, "metrics": {"m1": 10}}],
        events_by_turn={1: [{"id": "e1", "probability": 0.1}]},
    )

    analysis = analyze_runs(scenario_dir)
    report = format_analysis_report(analysis)

    assert "SCENARIO CALIBRATION REPORT" in report
    assert "Metric Distributions by Turn" in report
    assert "Event Trigger Rates by Turn" in report
