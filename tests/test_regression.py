"""Tests for run regression comparison helpers."""

import json

from scenario_lab.regression import (
    check_run_integrity,
    compare_distributions,
    compare_runs,
    run_regression_suite,
    summarize_run,
)


def _write_run(
    run_dir,
    *,
    final_metrics,
    history,
    occurred_events,
    turn_events,
    rule_versions,
    costs=None,
    status="completed",
):
    run_dir.mkdir(parents=True)
    (run_dir / "config.json").write_text(json.dumps({"name": "Test Scenario"}), encoding="utf-8")
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "scenario": "Test Scenario",
                "status": status,
                "total_turns": len(history),
                "final_metrics": final_metrics,
                "history": history,
                "occurred_events": occurred_events,
            }
        ),
        encoding="utf-8",
    )

    if costs is not None:
        (run_dir / "costs.json").write_text(json.dumps(costs), encoding="utf-8")

    for turn, metrics in enumerate([entry["metrics"] for entry in history], start=1):
        turn_dir = run_dir / f"turn-{turn:02d}"
        turn_dir.mkdir()
        (turn_dir / "1-events.json").write_text(
            json.dumps([{"id": event_id} for event_id in turn_events.get(turn, [])]),
            encoding="utf-8",
        )
        actors_dir = turn_dir / "2-actors"
        actors_dir.mkdir()
        (actors_dir / "actor.md").write_text("actor output", encoding="utf-8")
        (turn_dir / "3-metric-rules.md").write_text(
            f"# Metric Rules v{rule_versions[turn]}\n\nRules",
            encoding="utf-8",
        )
        (turn_dir / "3-metric-rules-metadata.json").write_text(
            json.dumps({"version": rule_versions[turn]}),
            encoding="utf-8",
        )
        (turn_dir / "4-metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
        (turn_dir / "4-world-state.md").write_text("narrative", encoding="utf-8")
        (turn_dir / "5-notepad.md").write_text("notes", encoding="utf-8")
        if turn > 1:
            (turn_dir / "6-historical-summary.md").write_text("history", encoding="utf-8")


def test_summarize_run_collects_turn_artifacts(tmp_path):
    run_dir = tmp_path / "runs" / "run-a"
    _write_run(
        run_dir,
        final_metrics={"gdp": 120, "employment": 80},
        history=[
            {"turn": 1, "metrics": {"gdp": 100, "employment": 90}},
            {"turn": 2, "metrics": {"gdp": 120, "employment": 80}},
        ],
        occurred_events=["shock-a"],
        turn_events={1: ["shock-a"], 2: []},
        rule_versions={1: 1, 2: 2},
        costs={"total_cost_usd": 1.25, "total_tokens": 1234},
    )

    summary = summarize_run(run_dir)

    assert summary["scenario"] == "Test Scenario"
    assert summary["status"] == "completed"
    assert summary["final_metrics"] == {"gdp": 120, "employment": 80}
    assert summary["turns"][1]["events"] == ["shock-a"]
    assert summary["turns"][2]["rules_version"] == 2
    assert summary["costs"]["total_cost_usd"] == 1.25


def test_check_run_integrity_catches_history_mismatch(tmp_path):
    run_dir = tmp_path / "runs" / "run-bad"
    _write_run(
        run_dir,
        final_metrics={"gdp": 120},
        history=[
            {"turn": 1, "metrics": {"gdp": 100}},
            {"turn": 2, "metrics": {"gdp": 120}},
        ],
        occurred_events=["shock-a"],
        turn_events={1: ["shock-a"], 2: []},
        rule_versions={1: 1, 2: 2},
    )

    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "scenario": "Test Scenario",
                "status": "completed",
                "total_turns": 2,
                "final_metrics": {"gdp": 999},
                "history": [
                    {"turn": 1, "metrics": {"gdp": 100}},
                    {"turn": 2, "metrics": {"gdp": 120}},
                ],
                "occurred_events": ["shock-a"],
            }
        ),
        encoding="utf-8",
    )

    report = check_run_integrity(run_dir)

    assert report["is_valid"] is False
    assert any("final_metrics does not match" in error for error in report["errors"])


def test_compare_runs_reports_regressions(tmp_path):
    baseline_run = tmp_path / "runs" / "run-baseline"
    candidate_run = tmp_path / "runs" / "run-candidate"

    _write_run(
        baseline_run,
        final_metrics={"gdp": 120, "employment": 80},
        history=[
            {"turn": 1, "metrics": {"gdp": 100, "employment": 90}},
            {"turn": 2, "metrics": {"gdp": 120, "employment": 80}},
        ],
        occurred_events=["shock-a"],
        turn_events={1: ["shock-a"], 2: []},
        rule_versions={1: 1, 2: 2},
        costs={"total_cost_usd": 1.25, "total_tokens": 1000},
    )
    _write_run(
        candidate_run,
        final_metrics={"gdp": 118, "employment": 82},
        history=[
            {"turn": 1, "metrics": {"gdp": 99, "employment": 91}},
            {"turn": 2, "metrics": {"gdp": 118, "employment": 82}},
        ],
        occurred_events=["shock-b"],
        turn_events={1: ["shock-b"], 2: []},
        rule_versions={1: 1, 2: 3},
        costs={"total_cost_usd": 1.55, "total_tokens": 1200},
    )

    report = compare_runs(baseline_run, candidate_run)

    assert report["has_differences"] is True
    assert report["cost_delta_usd"] == 0.30000000000000004
    assert report["occurred_events_only_in_baseline"] == ["shock-a"]
    assert report["occurred_events_only_in_candidate"] == ["shock-b"]
    assert report["rule_version_diffs"] == [{"turn": 2, "baseline": 2, "candidate": 3}]
    assert any(entry["metric"] == "gdp" and entry["delta"] == -2 for entry in report["final_metric_deltas"])
    assert any(
        entry["turn"] == 1 and entry["metric"] == "employment" and entry["delta"] == 1
        for entry in report["turn_metric_regressions"]
    )


def test_run_regression_suite_reads_manifest_and_resolves_relative_paths(tmp_path):
    baseline_run = tmp_path / "fixtures" / "run-baseline"
    candidate_run = tmp_path / "fixtures" / "run-candidate"

    _write_run(
        baseline_run,
        final_metrics={"gdp": 120},
        history=[
            {"turn": 1, "metrics": {"gdp": 100}},
            {"turn": 2, "metrics": {"gdp": 120}},
        ],
        occurred_events=["shock-a"],
        turn_events={1: ["shock-a"], 2: []},
        rule_versions={1: 1, 2: 2},
        costs={"total_cost_usd": 1.0, "total_tokens": 900},
    )
    _write_run(
        candidate_run,
        final_metrics={"gdp": 121},
        history=[
            {"turn": 1, "metrics": {"gdp": 101}},
            {"turn": 2, "metrics": {"gdp": 121}},
        ],
        occurred_events=["shock-a"],
        turn_events={1: ["shock-a"], 2: []},
        rule_versions={1: 1, 2: 2},
        costs={"total_cost_usd": 1.1, "total_tokens": 950},
    )

    manifest = tmp_path / "regressions.yaml"
    manifest.write_text(
        "\n".join(
            [
                "comparisons:",
                "  - label: quick-check",
                "    baseline: fixtures/run-baseline",
                "    candidate: fixtures/run-candidate",
            ]
        ),
        encoding="utf-8",
    )

    report = run_regression_suite(manifest)

    assert report["comparison_count"] == 1
    assert report["differing_count"] == 1
    assert report["comparisons"][0]["label"] == "quick-check"
    assert report["comparisons"][0]["status"] == "different"
    assert report["comparisons"][0]["comparison"]["candidate"]["run_name"] == "run-candidate"


def test_compare_distributions_reports_metric_and_event_shifts(tmp_path):
    baseline_a = tmp_path / "baseline" / "run-a"
    baseline_b = tmp_path / "baseline" / "run-b"
    candidate_a = tmp_path / "candidate" / "run-a"
    candidate_b = tmp_path / "candidate" / "run-b"

    _write_run(
        baseline_a,
        final_metrics={"gdp": 100, "employment": 90},
        history=[
            {"turn": 1, "metrics": {"gdp": 95, "employment": 92}},
            {"turn": 2, "metrics": {"gdp": 100, "employment": 90}},
        ],
        occurred_events=["shock-a"],
        turn_events={1: ["shock-a"], 2: []},
        rule_versions={1: 1, 2: 2},
        costs={"total_cost_usd": 1.0, "total_tokens": 900},
    )
    _write_run(
        baseline_b,
        final_metrics={"gdp": 102, "employment": 88},
        history=[
            {"turn": 1, "metrics": {"gdp": 96, "employment": 91}},
            {"turn": 2, "metrics": {"gdp": 102, "employment": 88}},
        ],
        occurred_events=["shock-a"],
        turn_events={1: ["shock-a"], 2: []},
        rule_versions={1: 1, 2: 2},
        costs={"total_cost_usd": 1.1, "total_tokens": 920},
    )
    _write_run(
        candidate_a,
        final_metrics={"gdp": 120, "employment": 80},
        history=[
            {"turn": 1, "metrics": {"gdp": 110, "employment": 86}},
            {"turn": 2, "metrics": {"gdp": 120, "employment": 80}},
        ],
        occurred_events=["shock-b"],
        turn_events={1: ["shock-b"], 2: []},
        rule_versions={1: 1, 2: 3},
        costs={"total_cost_usd": 1.4, "total_tokens": 1100},
    )
    _write_run(
        candidate_b,
        final_metrics={"gdp": 118, "employment": 82},
        history=[
            {"turn": 1, "metrics": {"gdp": 108, "employment": 87}},
            {"turn": 2, "metrics": {"gdp": 118, "employment": 82}},
        ],
        occurred_events=["shock-b"],
        turn_events={1: ["shock-b"], 2: []},
        rule_versions={1: 1, 2: 3},
        costs={"total_cost_usd": 1.5, "total_tokens": 1120},
    )

    manifest = tmp_path / "distribution.yaml"
    manifest.write_text(
        "\n".join(
            [
                "comparisons:",
                "  - label: macro-shift",
                "    baseline:",
                "      glob: baseline/run-*",
                "    candidate:",
                "      glob: candidate/run-*",
            ]
        ),
        encoding="utf-8",
    )

    report = compare_distributions(manifest)

    assert report["comparison_count"] == 1
    comparison = report["comparisons"][0]
    assert comparison["status"] == "ok"
    assert comparison["baseline"]["run_count"] == 2
    assert comparison["candidate"]["run_count"] == 2
    assert any(entry["metric"] == "gdp" and entry["mean_delta"] == 18.0 for entry in comparison["metric_deltas"])
    assert any(
        entry["event"] == "shock-b" and entry["rate_delta"] == 1.0
        for entry in comparison["event_rate_deltas"]
    )
