"""Run-set calibration analysis for scenario outputs."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any


def _round2(value: float) -> float:
    return round(value, 2)


def _metric_stats(values: list[float]) -> dict[str, float]:
    """Compute simple descriptive stats for a list of metric values."""
    if not values:
        return {}

    sorted_values = sorted(values)
    n = len(sorted_values)
    p10_idx = max(0, int(0.1 * (n - 1)))
    p90_idx = max(0, int(0.9 * (n - 1)))

    return {
        "count": n,
        "min": _round2(sorted_values[0]),
        "max": _round2(sorted_values[-1]),
        "mean": _round2(mean(sorted_values)),
        "p10": _round2(sorted_values[p10_idx]),
        "p90": _round2(sorted_values[p90_idx]),
    }


def analyze_runs(scenario_dir: Path, max_runs: int | None = None) -> dict[str, Any]:
    """Analyze completed runs for a scenario directory.

    Args:
        scenario_dir: Path to scenario directory containing runs/
        max_runs: Optional limit (most recent N runs)

    Returns:
        Analysis dictionary suitable for JSON export.
    """
    runs_dir = scenario_dir / "runs"
    if not runs_dir.exists():
        raise ValueError(f"No runs directory found: {runs_dir}")

    run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("run-")])
    if max_runs is not None:
        run_dirs = run_dirs[-max_runs:]

    if not run_dirs:
        raise ValueError(f"No run directories found in: {runs_dir}")

    metric_values_by_turn: dict[int, dict[str, list[float]]] = {}
    event_counts_by_turn: dict[int, dict[str, int]] = {}
    turns_seen = set()
    run_summaries = []

    for run_dir in run_dirs:
        summary_path = run_dir / "summary.json"
        if not summary_path.exists():
            continue

        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        run_summaries.append(
            {
                "run": run_dir.name,
                "status": summary.get("status"),
                "total_turns": summary.get("total_turns", 0),
            }
        )

        history = summary.get("history", [])
        for entry in history:
            turn = entry.get("turn")
            metrics = entry.get("metrics", {})
            if not isinstance(turn, int) or not isinstance(metrics, dict):
                continue

            turns_seen.add(turn)
            turn_metrics = metric_values_by_turn.setdefault(turn, {})
            for metric_id, value in metrics.items():
                if isinstance(value, (int, float)):
                    turn_metrics.setdefault(metric_id, []).append(float(value))

        # Event frequencies by turn from persisted turn files
        for turn_dir in [d for d in run_dir.iterdir() if d.is_dir() and d.name.startswith("turn-")]:
            try:
                turn = int(turn_dir.name.split("-")[1])
            except (ValueError, IndexError):
                continue

            events_file = turn_dir / "1-events.json"
            if not events_file.exists():
                continue

            try:
                events = json.loads(events_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue

            if not isinstance(events, list):
                continue

            turn_events = event_counts_by_turn.setdefault(turn, {})
            for event in events:
                if isinstance(event, dict) and "id" in event and isinstance(event["id"], str):
                    event_id = event["id"]
                    turn_events[event_id] = turn_events.get(event_id, 0) + 1

    if not run_summaries:
        raise ValueError(f"No readable summary.json found in runs: {runs_dir}")

    metric_stats_by_turn = {}
    for turn in sorted(metric_values_by_turn.keys()):
        metric_stats_by_turn[turn] = {
            metric_id: _metric_stats(values)
            for metric_id, values in metric_values_by_turn[turn].items()
        }

    event_rates_by_turn = {}
    num_runs = len(run_summaries)
    for turn in sorted(event_counts_by_turn.keys()):
        event_rates_by_turn[turn] = {
            event_id: {
                "count": count,
                "rate": _round2(count / num_runs),
            }
            for event_id, count in sorted(event_counts_by_turn[turn].items())
        }

    return {
        "scenario": scenario_dir.name,
        "runs_analyzed": num_runs,
        "run_summaries": run_summaries,
        "turns_seen": sorted(turns_seen),
        "metric_stats_by_turn": metric_stats_by_turn,
        "event_rates_by_turn": event_rates_by_turn,
    }


def format_analysis_report(analysis: dict[str, Any]) -> str:
    """Format run analysis as a human-readable text report."""
    lines = []
    lines.append("=" * 60)
    lines.append("SCENARIO CALIBRATION REPORT")
    lines.append("=" * 60)
    lines.append(f"Scenario: {analysis['scenario']}")
    lines.append(f"Runs analyzed: {analysis['runs_analyzed']}")
    lines.append(f"Turns seen: {analysis['turns_seen']}")
    lines.append("")

    lines.append("Metric Distributions by Turn")
    lines.append("-" * 60)
    for turn in analysis["metric_stats_by_turn"]:
        lines.append(f"Turn {turn}")
        for metric_id, stats in analysis["metric_stats_by_turn"][turn].items():
            lines.append(
                f"  {metric_id:24s} mean={stats['mean']:<8} "
                f"p10={stats['p10']:<8} p90={stats['p90']:<8} "
                f"min={stats['min']:<8} max={stats['max']:<8} n={stats['count']}"
            )
        lines.append("")

    lines.append("Event Trigger Rates by Turn")
    lines.append("-" * 60)
    for turn in analysis["event_rates_by_turn"]:
        lines.append(f"Turn {turn}")
        for event_id, data in analysis["event_rates_by_turn"][turn].items():
            lines.append(
                f"  {event_id:32s} count={data['count']:<4} rate={data['rate']:.2f}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
