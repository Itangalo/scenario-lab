"""Helpers for run integrity checks, regressions, and distribution analysis."""

from __future__ import annotations

import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import yaml

from .resume import validate_run_directory


def _load_json(path: Path) -> Any:
    """Load a JSON file using UTF-8."""
    return json.loads(path.read_text(encoding="utf-8"))


def _round2(value: float) -> float:
    """Round to two decimals for reporting."""
    return round(value, 2)


def _numeric_stats(values: list[float]) -> dict[str, float]:
    """Compute simple descriptive stats for a numeric series."""
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
        "stddev": _round2(pstdev(sorted_values)) if n > 1 else 0.0,
        "p10": _round2(sorted_values[p10_idx]),
        "p90": _round2(sorted_values[p90_idx]),
    }


def _extract_rules_version(turn_dir: Path) -> int | None:
    """Read the rules version for one turn if available."""
    metadata_path = turn_dir / "3-metric-rules-metadata.json"
    if metadata_path.exists():
        try:
            metadata = _load_json(metadata_path)
        except json.JSONDecodeError:
            metadata = {}
        version = metadata.get("version")
        if isinstance(version, int):
            return version
        if isinstance(version, str):
            match = re.search(r"(\d+)", version)
            if match:
                return int(match.group(1))

    rules_path = turn_dir / "3-metric-rules.md"
    if not rules_path.exists():
        return None

    content = rules_path.read_text(encoding="utf-8")
    match = re.search(r"Metric Rules v(\d+)", content, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _extract_event_ids(turn_dir: Path) -> list[str]:
    """Read normalized event ids for one turn."""
    events_path = turn_dir / "1-events.json"
    if not events_path.exists():
        return []

    try:
        payload = _load_json(events_path)
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []

    event_ids: list[str] = []
    for item in payload:
        if isinstance(item, dict):
            event_id = item.get("id")
            if isinstance(event_id, str):
                event_ids.append(event_id)
    return sorted(event_ids)


def _resolve_manifest_path(manifest_dir: Path, path_value: str) -> Path:
    """Resolve a path relative to a manifest file."""
    path = Path(path_value)
    if not path.is_absolute():
        path = manifest_dir / path
    return path.resolve()


def _resolve_glob_paths(manifest_dir: Path, pattern: str) -> list[Path]:
    """Resolve a glob pattern relative to a manifest directory."""
    if Path(pattern).is_absolute():
        matched = sorted(Path(path).resolve() for path in glob.glob(pattern))
    else:
        matched = sorted(path.resolve() for path in manifest_dir.glob(pattern))
    return [path for path in matched if path.is_dir()]


def _resolve_run_group(manifest_dir: Path, group: Any) -> list[Path]:
    """Resolve a run group from manifest syntax."""
    if not isinstance(group, dict):
        raise ValueError("Run group must be a mapping with either glob or runs")

    if "glob" in group:
        pattern = group["glob"]
        if not isinstance(pattern, str) or not pattern.strip():
            raise ValueError("Run group glob must be a non-empty string")
        paths = _resolve_glob_paths(manifest_dir, pattern)
    elif "runs" in group:
        runs = group["runs"]
        if not isinstance(runs, list) or not runs:
            raise ValueError("Run group runs must be a non-empty list")
        paths = []
        for item in runs:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("Run group run paths must be non-empty strings")
            paths.append(_resolve_manifest_path(manifest_dir, item))
    else:
        raise ValueError("Run group must define either glob or runs")

    if not paths:
        raise ValueError("Run group resolved to zero run directories")

    deduped: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        deduped.append(path)
    return deduped


def check_run_integrity(run_dir: Path) -> dict[str, Any]:
    """Perform strict structural validation of a saved run directory."""
    errors: list[str] = []
    warnings: list[str] = []

    is_valid, base_errors = validate_run_directory(run_dir)
    if not is_valid:
        errors.extend(base_errors)
        return {
            "run_dir": str(run_dir),
            "run_name": run_dir.name,
            "is_valid": False,
            "errors": errors,
            "warnings": warnings,
        }

    config: dict[str, Any] = {}
    summary: dict[str, Any] = {}

    try:
        config = _load_json(run_dir / "config.json")
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid config.json: {exc}")

    try:
        summary = _load_json(run_dir / "summary.json")
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid summary.json: {exc}")

    turn_dirs: dict[int, Path] = {}
    malformed_turn_dirs: list[str] = []
    for path in sorted(run_dir.iterdir()):
        if not path.is_dir() or not path.name.startswith("turn-"):
            continue
        try:
            turn = int(path.name.split("-")[1])
        except (IndexError, ValueError):
            malformed_turn_dirs.append(path.name)
            continue
        turn_dirs[turn] = path

    if malformed_turn_dirs:
        errors.append(f"Malformed turn directories: {', '.join(malformed_turn_dirs)}")

    if turn_dirs:
        expected_turns = list(range(1, max(turn_dirs) + 1))
        missing_turns = [turn for turn in expected_turns if turn not in turn_dirs]
        if missing_turns:
            errors.append(
                "Missing turn directories in sequence: "
                + ", ".join(str(turn) for turn in missing_turns)
            )

    turn_metrics: dict[int, dict[str, Any]] = {}
    for turn, turn_dir in sorted(turn_dirs.items()):
        required_files = [
            "1-events.json",
            "3-metric-rules.md",
            "4-metrics.json",
            "4-world-state.md",
            "5-notepad.md",
        ]
        if turn > 1:
            required_files.append("6-historical-summary.md")

        missing = [name for name in required_files if not (turn_dir / name).exists()]
        if missing:
            errors.append(
                f"Turn {turn} missing required files: {', '.join(missing)}"
            )

        actors_dir = turn_dir / "2-actors"
        if not actors_dir.exists() or not actors_dir.is_dir():
            errors.append(f"Turn {turn} missing 2-actors directory")
        elif not any(actors_dir.iterdir()):
            errors.append(f"Turn {turn} has empty 2-actors directory")

        events_file = turn_dir / "1-events.json"
        if events_file.exists():
            try:
                events = _load_json(events_file)
                if not isinstance(events, list):
                    errors.append(f"Turn {turn} events payload must be a list")
            except json.JSONDecodeError as exc:
                errors.append(f"Turn {turn} has invalid 1-events.json: {exc}")

        metrics_file = turn_dir / "4-metrics.json"
        if metrics_file.exists():
            try:
                metrics = _load_json(metrics_file)
                if not isinstance(metrics, dict):
                    errors.append(f"Turn {turn} metrics payload must be an object")
                else:
                    turn_metrics[turn] = metrics
            except json.JSONDecodeError as exc:
                errors.append(f"Turn {turn} has invalid 4-metrics.json: {exc}")

        if (turn_dir / "3-metric-rules.md").exists():
            rules_text = (turn_dir / "3-metric-rules.md").read_text(encoding="utf-8").strip()
            if not rules_text:
                errors.append(f"Turn {turn} has empty 3-metric-rules.md")

        for filename in ["4-world-state.md", "5-notepad.md"]:
            file_path = turn_dir / filename
            if file_path.exists() and not file_path.read_text(encoding="utf-8").strip():
                warnings.append(f"Turn {turn} has empty {filename}")

        if turn > 1:
            history_path = turn_dir / "6-historical-summary.md"
            if history_path.exists() and not history_path.read_text(encoding="utf-8").strip():
                warnings.append(f"Turn {turn} has empty 6-historical-summary.md")

    if summary:
        status = summary.get("status")
        if not isinstance(status, str):
            errors.append("summary.json field 'status' must be a string")

        total_turns = summary.get("total_turns")
        if not isinstance(total_turns, int):
            errors.append("summary.json field 'total_turns' must be an integer")
        elif turn_dirs and total_turns != max(turn_dirs):
            errors.append(
                f"summary.json total_turns={total_turns} does not match highest turn directory={max(turn_dirs)}"
            )

        history = summary.get("history")
        history_by_turn: dict[int, dict[str, Any]] = {}
        if not isinstance(history, list):
            errors.append("summary.json field 'history' must be a list")
        else:
            seen_turns: set[int] = set()
            for entry in history:
                if not isinstance(entry, dict):
                    errors.append("summary.json history entries must be objects")
                    continue
                turn = entry.get("turn")
                metrics = entry.get("metrics")
                if not isinstance(turn, int):
                    errors.append("summary.json history entry turn must be an integer")
                    continue
                if turn in seen_turns:
                    errors.append(f"summary.json history has duplicate turn {turn}")
                    continue
                seen_turns.add(turn)
                if not isinstance(metrics, dict):
                    errors.append(f"summary.json history turn {turn} metrics must be an object")
                    continue
                history_by_turn[turn] = metrics

            if history_by_turn:
                expected_history_turns = list(range(1, max(history_by_turn) + 1))
                missing_history_turns = [
                    turn for turn in expected_history_turns if turn not in history_by_turn
                ]
                if missing_history_turns:
                    errors.append(
                        "summary.json history is missing turns: "
                        + ", ".join(str(turn) for turn in missing_history_turns)
                    )

        final_metrics = summary.get("final_metrics")
        if not isinstance(final_metrics, dict):
            errors.append("summary.json field 'final_metrics' must be an object")
        else:
            if history_by_turn:
                last_history_turn = max(history_by_turn)
                if final_metrics != history_by_turn[last_history_turn]:
                    errors.append(
                        "summary.json final_metrics does not match the last history entry"
                    )
            if turn_metrics:
                last_turn = max(turn_metrics)
                if final_metrics != turn_metrics[last_turn]:
                    errors.append(
                        f"summary.json final_metrics does not match turn-{last_turn:02d}/4-metrics.json"
                    )

        occurred_events = summary.get("occurred_events")
        if not isinstance(occurred_events, list) or not all(
            isinstance(item, str) for item in occurred_events
        ):
            errors.append("summary.json field 'occurred_events' must be a list of strings")

        for turn, metrics in history_by_turn.items():
            if turn in turn_metrics and metrics != turn_metrics[turn]:
                errors.append(
                    f"summary.json history turn {turn} does not match turn-{turn:02d}/4-metrics.json"
                )

    costs_path = run_dir / "costs.json"
    if costs_path.exists():
        try:
            costs = _load_json(costs_path)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid costs.json: {exc}")
        else:
            if not isinstance(costs, dict):
                errors.append("costs.json must be an object")
            else:
                total_cost = costs.get("total_cost_usd")
                total_tokens = costs.get("total_tokens")
                if total_cost is not None and not isinstance(total_cost, (int, float)):
                    errors.append("costs.json field 'total_cost_usd' must be numeric")
                if total_tokens is not None and not isinstance(total_tokens, int):
                    errors.append("costs.json field 'total_tokens' must be an integer")

    scenario_name = "unknown"
    if isinstance(summary, dict) and isinstance(summary.get("scenario"), str):
        scenario_name = summary["scenario"]
    elif isinstance(config, dict) and isinstance(config.get("name"), str):
        scenario_name = config["name"]

    return {
        "run_dir": str(run_dir),
        "run_name": run_dir.name,
        "scenario": scenario_name,
        "turn_count": max(turn_dirs) if turn_dirs else 0,
        "is_valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def format_run_integrity(report: dict[str, Any]) -> str:
    """Render a compact text report for run integrity."""
    lines = [
        "=" * 60,
        "RUN INTEGRITY CHECK",
        "=" * 60,
        f"Run      : {report['run_name']}",
        f"Scenario : {report.get('scenario', 'unknown')}",
        f"Turns    : {report.get('turn_count', 0)}",
        f"Valid    : {'yes' if report['is_valid'] else 'no'}",
    ]

    if report["errors"]:
        lines.extend(["", "Errors:"])
        lines.extend(f"  - {error}" for error in report["errors"])

    if report["warnings"]:
        lines.extend(["", "Warnings:"])
        lines.extend(f"  - {warning}" for warning in report["warnings"])

    if not report["errors"] and not report["warnings"]:
        lines.extend(["", "No integrity issues detected."])

    return "\n".join(lines)


def summarize_run(run_dir: Path) -> dict[str, Any]:
    """Build a normalized summary for a saved run."""
    integrity = check_run_integrity(run_dir)
    if not integrity["is_valid"]:
        raise ValueError(
            "Invalid run directory: " + "; ".join(integrity["errors"])
        )

    summary = _load_json(run_dir / "summary.json")
    config = _load_json(run_dir / "config.json")

    costs_path = run_dir / "costs.json"
    costs = _load_json(costs_path) if costs_path.exists() else {}

    turns: dict[int, dict[str, Any]] = {}
    for turn_dir in sorted(path for path in run_dir.iterdir() if path.is_dir() and path.name.startswith("turn-")):
        turn = int(turn_dir.name.split("-")[1])
        rules_version = _extract_rules_version(turn_dir)
        event_ids = _extract_event_ids(turn_dir)
        turn_entry: dict[str, Any] = {
            "events": event_ids,
            "event_count": len(event_ids),
        }
        metrics_path = turn_dir / "4-metrics.json"
        if metrics_path.exists():
            turn_entry["metrics"] = _load_json(metrics_path)
        if rules_version is not None:
            turn_entry["rules_version"] = rules_version
        turns[turn] = turn_entry

    history = summary.get("history", [])
    history_by_turn: dict[int, dict[str, Any]] = {}
    for entry in history:
        if isinstance(entry, dict) and isinstance(entry.get("turn"), int) and isinstance(entry.get("metrics"), dict):
            history_by_turn[entry["turn"]] = entry["metrics"]

    for turn, turn_entry in turns.items():
        if "metrics" not in turn_entry and turn in history_by_turn:
            turn_entry["metrics"] = history_by_turn[turn]

    return {
        "run_dir": str(run_dir),
        "run_name": run_dir.name,
        "scenario": summary.get("scenario") or config.get("name") or "unknown",
        "status": summary.get("status", "unknown"),
        "total_turns": int(summary.get("total_turns", 0) or 0),
        "final_metrics": summary.get("final_metrics", {}),
        "occurred_events": sorted(summary.get("occurred_events", [])),
        "turns": turns,
        "costs": {
            "total_cost_usd": costs.get("total_cost_usd"),
            "total_tokens": costs.get("total_tokens"),
        },
    }


def compare_runs(baseline_run: Path, candidate_run: Path) -> dict[str, Any]:
    """Compare two saved run directories and return structured differences."""
    baseline = summarize_run(baseline_run)
    candidate = summarize_run(candidate_run)

    final_metric_deltas: list[dict[str, Any]] = []
    metric_ids = sorted(set(baseline["final_metrics"]) | set(candidate["final_metrics"]))
    for metric_id in metric_ids:
        baseline_value = baseline["final_metrics"].get(metric_id)
        candidate_value = candidate["final_metrics"].get(metric_id)
        if baseline_value == candidate_value:
            continue

        delta = None
        if isinstance(baseline_value, (int, float)) and isinstance(candidate_value, (int, float)):
            delta = candidate_value - baseline_value

        final_metric_deltas.append(
            {
                "metric": metric_id,
                "baseline": baseline_value,
                "candidate": candidate_value,
                "delta": delta,
            }
        )

    turn_metric_regressions: list[dict[str, Any]] = []
    shared_turns = sorted(set(baseline["turns"]) & set(candidate["turns"]))
    for turn in shared_turns:
        baseline_metrics = baseline["turns"][turn].get("metrics", {})
        candidate_metrics = candidate["turns"][turn].get("metrics", {})
        metric_ids = sorted(set(baseline_metrics) | set(candidate_metrics))
        for metric_id in metric_ids:
            baseline_value = baseline_metrics.get(metric_id)
            candidate_value = candidate_metrics.get(metric_id)
            if baseline_value == candidate_value:
                continue
            delta = None
            if isinstance(baseline_value, (int, float)) and isinstance(candidate_value, (int, float)):
                delta = candidate_value - baseline_value
            turn_metric_regressions.append(
                {
                    "turn": turn,
                    "metric": metric_id,
                    "baseline": baseline_value,
                    "candidate": candidate_value,
                    "delta": delta,
                }
            )

    baseline_events = set(baseline["occurred_events"])
    candidate_events = set(candidate["occurred_events"])

    baseline_cost = baseline["costs"].get("total_cost_usd")
    candidate_cost = candidate["costs"].get("total_cost_usd")
    cost_delta = None
    if isinstance(baseline_cost, (int, float)) and isinstance(candidate_cost, (int, float)):
        cost_delta = candidate_cost - baseline_cost

    rule_version_diffs: list[dict[str, Any]] = []
    for turn in shared_turns:
        baseline_version = baseline["turns"][turn].get("rules_version")
        candidate_version = candidate["turns"][turn].get("rules_version")
        if baseline_version != candidate_version:
            rule_version_diffs.append(
                {
                    "turn": turn,
                    "baseline": baseline_version,
                    "candidate": candidate_version,
                }
            )

    event_diffs_by_turn: list[dict[str, Any]] = []
    for turn in shared_turns:
        baseline_turn_events = set(baseline["turns"][turn].get("events", []))
        candidate_turn_events = set(candidate["turns"][turn].get("events", []))
        only_in_baseline = sorted(baseline_turn_events - candidate_turn_events)
        only_in_candidate = sorted(candidate_turn_events - baseline_turn_events)
        if only_in_baseline or only_in_candidate:
            event_diffs_by_turn.append(
                {
                    "turn": turn,
                    "only_in_baseline": only_in_baseline,
                    "only_in_candidate": only_in_candidate,
                }
            )

    has_differences = any(
        [
            baseline["scenario"] != candidate["scenario"],
            baseline["status"] != candidate["status"],
            baseline["total_turns"] != candidate["total_turns"],
            bool(final_metric_deltas),
            bool(turn_metric_regressions),
            bool(rule_version_diffs),
            bool(event_diffs_by_turn),
            baseline_events != candidate_events,
            baseline_cost != candidate_cost,
        ]
    )

    return {
        "baseline": baseline,
        "candidate": candidate,
        "has_differences": has_differences,
        "status_changed": baseline["status"] != candidate["status"],
        "turn_count_changed": baseline["total_turns"] != candidate["total_turns"],
        "final_metric_deltas": final_metric_deltas,
        "turn_metric_regressions": turn_metric_regressions,
        "rule_version_diffs": rule_version_diffs,
        "event_diffs_by_turn": event_diffs_by_turn,
        "occurred_events_only_in_baseline": sorted(baseline_events - candidate_events),
        "occurred_events_only_in_candidate": sorted(candidate_events - baseline_events),
        "cost_delta_usd": cost_delta,
    }


def format_run_comparison(report: dict[str, Any]) -> str:
    """Render a compact text report for a run comparison."""
    baseline = report["baseline"]
    candidate = report["candidate"]

    lines = [
        "=" * 60,
        "RUN COMPARISON",
        "=" * 60,
        f"Baseline : {baseline['run_name']}",
        f"Candidate: {candidate['run_name']}",
        f"Scenario : {baseline['scenario']} -> {candidate['scenario']}",
        f"Status   : {baseline['status']} -> {candidate['status']}",
        f"Turns    : {baseline['total_turns']} -> {candidate['total_turns']}",
    ]

    if not report["has_differences"]:
        lines.extend(["", "No differences detected in compared run artifacts."])
        return "\n".join(lines)

    if report["final_metric_deltas"]:
        lines.extend(["", "Final metric deltas:"])
        for entry in report["final_metric_deltas"]:
            delta = entry["delta"]
            delta_text = f" (delta {delta:+g})" if isinstance(delta, (int, float)) else ""
            lines.append(
                f"  - {entry['metric']}: {entry['baseline']} -> {entry['candidate']}{delta_text}"
            )

    if report["turn_metric_regressions"]:
        lines.extend(["", "Per-turn metric differences:"])
        for entry in report["turn_metric_regressions"][:12]:
            delta = entry["delta"]
            delta_text = f" (delta {delta:+g})" if isinstance(delta, (int, float)) else ""
            lines.append(
                f"  - Turn {entry['turn']}: {entry['metric']} {entry['baseline']} -> {entry['candidate']}{delta_text}"
            )
        remaining = len(report["turn_metric_regressions"]) - 12
        if remaining > 0:
            lines.append(f"  - ... {remaining} more per-turn metric differences")

    if report["event_diffs_by_turn"]:
        lines.extend(["", "Per-turn event differences:"])
        for entry in report["event_diffs_by_turn"]:
            if entry["only_in_baseline"]:
                lines.append(
                    f"  - Turn {entry['turn']} only in baseline: {', '.join(entry['only_in_baseline'])}"
                )
            if entry["only_in_candidate"]:
                lines.append(
                    f"  - Turn {entry['turn']} only in candidate: {', '.join(entry['only_in_candidate'])}"
                )

    if report["occurred_events_only_in_baseline"] or report["occurred_events_only_in_candidate"]:
        lines.extend(["", "Occurred event set differences:"])
        if report["occurred_events_only_in_baseline"]:
            lines.append(
                "  - Only in baseline: "
                + ", ".join(report["occurred_events_only_in_baseline"])
            )
        if report["occurred_events_only_in_candidate"]:
            lines.append(
                "  - Only in candidate: "
                + ", ".join(report["occurred_events_only_in_candidate"])
            )

    if report["rule_version_diffs"]:
        lines.extend(["", "Rule version differences:"])
        for entry in report["rule_version_diffs"]:
            lines.append(
                f"  - Turn {entry['turn']}: v{entry['baseline']} -> v{entry['candidate']}"
            )

    cost_delta = report["cost_delta_usd"]
    if isinstance(cost_delta, (int, float)):
        lines.extend(
            [
                "",
                "Cost difference:",
                f"  - Total cost delta: {cost_delta:+.4f} USD",
            ]
        )

    return "\n".join(lines)


def load_regression_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load and validate a pairwise regression manifest."""
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("Regression manifest must contain a top-level mapping")

    comparisons = payload.get("comparisons")
    if not isinstance(comparisons, list) or not comparisons:
        raise ValueError("Regression manifest must define a non-empty comparisons list")

    normalized: list[dict[str, Any]] = []
    manifest_dir = manifest_path.parent
    for index, item in enumerate(comparisons, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Comparison #{index} must be a mapping")

        baseline = item.get("baseline")
        candidate = item.get("candidate")
        if not isinstance(baseline, str) or not isinstance(candidate, str):
            raise ValueError(f"Comparison #{index} must include string baseline and candidate paths")

        label = item.get("label") or f"comparison-{index}"
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"Comparison #{index} label must be a non-empty string")

        normalized.append(
            {
                "label": label.strip(),
                "baseline": _resolve_manifest_path(manifest_dir, baseline),
                "candidate": _resolve_manifest_path(manifest_dir, candidate),
            }
        )

    return {
        "manifest_path": str(manifest_path.resolve()),
        "comparisons": normalized,
    }


def run_regression_suite(manifest_path: Path) -> dict[str, Any]:
    """Run all pairwise comparisons from a manifest and summarize the results."""
    manifest = load_regression_manifest(manifest_path)

    comparisons: list[dict[str, Any]] = []
    error_count = 0
    differing_count = 0

    for item in manifest["comparisons"]:
        try:
            comparison = compare_runs(item["baseline"], item["candidate"])
        except Exception as exc:
            comparisons.append(
                {
                    "label": item["label"],
                    "baseline": str(item["baseline"]),
                    "candidate": str(item["candidate"]),
                    "status": "error",
                    "error": str(exc),
                }
            )
            error_count += 1
            continue

        has_differences = comparison["has_differences"]
        if has_differences:
            differing_count += 1

        comparisons.append(
            {
                "label": item["label"],
                "baseline": str(item["baseline"]),
                "candidate": str(item["candidate"]),
                "status": "different" if has_differences else "ok",
                "has_differences": has_differences,
                "final_metric_diff_count": len(comparison["final_metric_deltas"]),
                "turn_metric_diff_count": len(comparison["turn_metric_regressions"]),
                "event_diff_turn_count": len(comparison["event_diffs_by_turn"]),
                "rule_version_diff_count": len(comparison["rule_version_diffs"]),
                "comparison": comparison,
            }
        )

    return {
        "manifest_path": manifest["manifest_path"],
        "comparison_count": len(comparisons),
        "differing_count": differing_count,
        "error_count": error_count,
        "has_differences": differing_count > 0,
        "has_errors": error_count > 0,
        "comparisons": comparisons,
    }


def format_regression_suite(report: dict[str, Any]) -> str:
    """Render a compact text report for a manifest-based regression suite."""
    lines = [
        "=" * 60,
        "REGRESSION CHECK",
        "=" * 60,
        f"Manifest    : {report['manifest_path']}",
        f"Comparisons : {report['comparison_count']}",
        f"With diffs  : {report['differing_count']}",
        f"Errors      : {report['error_count']}",
    ]

    if not report["comparisons"]:
        lines.extend(["", "No comparisons were defined."])
        return "\n".join(lines)

    lines.append("")
    lines.append("Results:")
    for item in report["comparisons"]:
        status = item["status"].upper()
        lines.append(f"  - {item['label']}: {status}")
        if item["status"] == "error":
            lines.append(f"    {item['error']}")
            continue

        lines.append(
            "    "
            f"final metrics={item['final_metric_diff_count']}, "
            f"per-turn metrics={item['turn_metric_diff_count']}, "
            f"event turns={item['event_diff_turn_count']}, "
            f"rule versions={item['rule_version_diff_count']}"
        )

    return "\n".join(lines)


def _summarize_run_group(run_dirs: list[Path]) -> dict[str, Any]:
    """Summarize a set of runs for distribution comparison."""
    run_summaries: list[dict[str, Any]] = []
    final_metric_values: dict[str, list[float]] = defaultdict(list)
    occurred_event_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    total_turns_values: list[float] = []
    total_cost_values: list[float] = []

    for run_dir in run_dirs:
        summary = summarize_run(run_dir)
        run_summaries.append(
            {
                "run_name": summary["run_name"],
                "status": summary["status"],
                "total_turns": summary["total_turns"],
            }
        )
        status_counts[summary["status"]] += 1
        total_turns_values.append(float(summary["total_turns"]))

        for metric_id, value in summary["final_metrics"].items():
            if isinstance(value, (int, float)):
                final_metric_values[metric_id].append(float(value))

        for event_id in summary["occurred_events"]:
            occurred_event_counts[event_id] += 1

        total_cost = summary["costs"].get("total_cost_usd")
        if isinstance(total_cost, (int, float)):
            total_cost_values.append(float(total_cost))

    run_count = len(run_summaries)
    final_metric_stats = {
        metric_id: _numeric_stats(values)
        for metric_id, values in sorted(final_metric_values.items())
    }
    occurred_event_rates = {
        event_id: {
            "count": count,
            "rate": _round2(count / run_count) if run_count else 0.0,
        }
        for event_id, count in sorted(occurred_event_counts.items())
    }

    return {
        "run_count": run_count,
        "runs": run_summaries,
        "status_counts": dict(sorted(status_counts.items())),
        "turn_count_stats": _numeric_stats(total_turns_values),
        "cost_stats": _numeric_stats(total_cost_values),
        "final_metric_stats": final_metric_stats,
        "occurred_event_rates": occurred_event_rates,
    }


def load_distribution_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load and validate a distribution-comparison manifest."""
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("Distribution manifest must contain a top-level mapping")

    comparisons = payload.get("comparisons")
    if not isinstance(comparisons, list) or not comparisons:
        raise ValueError("Distribution manifest must define a non-empty comparisons list")

    normalized: list[dict[str, Any]] = []
    manifest_dir = manifest_path.parent
    for index, item in enumerate(comparisons, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Distribution comparison #{index} must be a mapping")

        label = item.get("label") or f"distribution-{index}"
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"Distribution comparison #{index} label must be a non-empty string")

        baseline = item.get("baseline")
        candidate = item.get("candidate")
        normalized.append(
            {
                "label": label.strip(),
                "baseline_runs": _resolve_run_group(manifest_dir, baseline),
                "candidate_runs": _resolve_run_group(manifest_dir, candidate),
            }
        )

    return {
        "manifest_path": str(manifest_path.resolve()),
        "comparisons": normalized,
    }


def compare_distributions(manifest_path: Path) -> dict[str, Any]:
    """Compare distributions across sets of saved runs."""
    manifest = load_distribution_manifest(manifest_path)

    comparisons: list[dict[str, Any]] = []
    error_count = 0

    for item in manifest["comparisons"]:
        try:
            baseline = _summarize_run_group(item["baseline_runs"])
            candidate = _summarize_run_group(item["candidate_runs"])
        except Exception as exc:
            comparisons.append(
                {
                    "label": item["label"],
                    "status": "error",
                    "error": str(exc),
                }
            )
            error_count += 1
            continue

        metric_deltas: list[dict[str, Any]] = []
        metric_ids = sorted(
            set(baseline["final_metric_stats"]) | set(candidate["final_metric_stats"])
        )
        for metric_id in metric_ids:
            baseline_stats = baseline["final_metric_stats"].get(metric_id, {})
            candidate_stats = candidate["final_metric_stats"].get(metric_id, {})
            baseline_mean = baseline_stats.get("mean")
            candidate_mean = candidate_stats.get("mean")
            mean_delta = None
            if isinstance(baseline_mean, (int, float)) and isinstance(candidate_mean, (int, float)):
                mean_delta = _round2(candidate_mean - baseline_mean)
            metric_deltas.append(
                {
                    "metric": metric_id,
                    "baseline": baseline_stats,
                    "candidate": candidate_stats,
                    "mean_delta": mean_delta,
                }
            )

        event_rate_deltas: list[dict[str, Any]] = []
        event_ids = sorted(
            set(baseline["occurred_event_rates"]) | set(candidate["occurred_event_rates"])
        )
        for event_id in event_ids:
            baseline_rate = baseline["occurred_event_rates"].get(event_id, {}).get("rate", 0.0)
            candidate_rate = candidate["occurred_event_rates"].get(event_id, {}).get("rate", 0.0)
            event_rate_deltas.append(
                {
                    "event": event_id,
                    "baseline_rate": baseline_rate,
                    "candidate_rate": candidate_rate,
                    "rate_delta": _round2(candidate_rate - baseline_rate),
                }
            )

        comparisons.append(
            {
                "label": item["label"],
                "status": "ok",
                "baseline": baseline,
                "candidate": candidate,
                "metric_deltas": metric_deltas,
                "event_rate_deltas": event_rate_deltas,
            }
        )

    return {
        "manifest_path": manifest["manifest_path"],
        "comparison_count": len(comparisons),
        "error_count": error_count,
        "comparisons": comparisons,
    }


def format_distribution_comparison(report: dict[str, Any]) -> str:
    """Render a compact text report for distribution comparisons."""
    lines = [
        "=" * 60,
        "DISTRIBUTION COMPARISON",
        "=" * 60,
        f"Manifest    : {report['manifest_path']}",
        f"Comparisons : {report['comparison_count']}",
        f"Errors      : {report['error_count']}",
    ]

    for item in report["comparisons"]:
        lines.extend(["", f"{item['label']}:"])
        if item["status"] == "error":
            lines.append(f"  error: {item['error']}")
            continue

        lines.append(
            f"  runs: baseline={item['baseline']['run_count']} candidate={item['candidate']['run_count']}"
        )

        metric_deltas = sorted(
            item["metric_deltas"],
            key=lambda entry: abs(entry["mean_delta"]) if isinstance(entry["mean_delta"], (int, float)) else -1,
            reverse=True,
        )
        if metric_deltas:
            lines.append("  final metric mean shifts:")
            for entry in metric_deltas[:8]:
                delta = entry["mean_delta"]
                if delta is None:
                    continue
                lines.append(
                    f"    - {entry['metric']}: {entry['baseline'].get('mean')} -> {entry['candidate'].get('mean')} (delta {delta:+g})"
                )

        event_deltas = sorted(
            item["event_rate_deltas"],
            key=lambda entry: abs(entry["rate_delta"]),
            reverse=True,
        )
        if event_deltas:
            lines.append("  occurred event rate shifts:")
            for entry in event_deltas[:8]:
                if entry["rate_delta"] == 0:
                    continue
                lines.append(
                    f"    - {entry['event']}: {entry['baseline_rate']:.2f} -> {entry['candidate_rate']:.2f} (delta {entry['rate_delta']:+.2f})"
                )

    return "\n".join(lines)
