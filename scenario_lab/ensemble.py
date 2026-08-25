"""Ensemble analysis across many runs of the same scenario."""

from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _round2(value: float) -> float:
    return round(value, 2)


def _percentile(sorted_values: list[float], p: float) -> float:
    """Return the p-th percentile (0–100) of a pre-sorted list."""
    n = len(sorted_values)
    if n == 0:
        return 0.0
    idx = max(0, min(n - 1, int(p / 100 * (n - 1))))
    return sorted_values[idx]


def _distribution_stats(values: list[float]) -> dict[str, float]:
    """Compute descriptive stats used in ensemble reporting."""
    if not values:
        return {}
    sv = sorted(values)
    n = len(sv)
    stats: dict[str, float] = {
        "n": float(n),
        "mean": _round2(mean(sv)),
        "min": _round2(sv[0]),
        "max": _round2(sv[-1]),
        "p10": _round2(_percentile(sv, 10)),
        "p50": _round2(_percentile(sv, 50)),
        "p90": _round2(_percentile(sv, 90)),
        "stddev": _round2(pstdev(sv)) if n > 1 else 0.0,
        "iqr": _round2(_percentile(sv, 75) - _percentile(sv, 25)),
    }
    return stats


def _load_json_safe(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _discover_completed_runs(scenario_dir: Path, max_runs: int | None = None) -> list[Path]:
    """Return sorted run-* directories from <scenario_dir>/runs/ that have summary.json."""
    runs_dir = scenario_dir / "runs"
    if not runs_dir.exists():
        return []
    candidates = sorted(
        d for d in runs_dir.iterdir()
        if d.is_dir() and d.name.startswith("run-")
    )
    if max_runs is not None:
        candidates = candidates[-max_runs:]
    completed: list[Path] = []
    for run_dir in candidates:
        summary = _load_json_safe(run_dir / "summary.json")
        if isinstance(summary, dict) and summary.get("status") == "completed":
            completed.append(run_dir)
    return completed


def _read_turn_metrics(run_dir: Path) -> dict[int, dict[str, float]]:
    """Read per-turn metric values from turn-XX/4-metrics.json files."""
    result: dict[int, dict[str, float]] = {}
    for turn_dir in sorted(run_dir.iterdir()):
        if not turn_dir.is_dir() or not turn_dir.name.startswith("turn-"):
            continue
        try:
            turn = int(turn_dir.name.split("-")[1])
        except (IndexError, ValueError):
            continue
        metrics = _load_json_safe(turn_dir / "4-metrics.json")
        if isinstance(metrics, dict):
            result[turn] = {
                k: float(v) for k, v in metrics.items()
                if isinstance(v, (int, float))
            }
    return result


def _read_triggered_events_by_turn(run_dir: Path) -> dict[int, set[str]]:
    """Return {turn: {event_id, ...}} from 1-events.json files."""
    result: dict[int, set[str]] = {}
    for turn_dir in sorted(run_dir.iterdir()):
        if not turn_dir.is_dir() or not turn_dir.name.startswith("turn-"):
            continue
        try:
            turn = int(turn_dir.name.split("-")[1])
        except (IndexError, ValueError):
            continue
        events = _load_json_safe(turn_dir / "1-events.json")
        if isinstance(events, list):
            result[turn] = {
                item["id"] for item in events
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            }
        else:
            result[turn] = set()
    return result


def _read_event_evaluations_by_turn(run_dir: Path) -> dict[int, list[dict[str, Any]]]:
    """Return per-turn evaluations from 1-event-evaluations.json (optional, new runs only)."""
    result: dict[int, list[dict[str, Any]]] = {}
    for turn_dir in sorted(run_dir.iterdir()):
        if not turn_dir.is_dir() or not turn_dir.name.startswith("turn-"):
            continue
        try:
            turn = int(turn_dir.name.split("-")[1])
        except (IndexError, ValueError):
            continue
        evals = _load_json_safe(turn_dir / "1-event-evaluations.json")
        if isinstance(evals, list):
            result[turn] = evals
    return result


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def _read_final_historical_summary(run_dir: Path) -> str | None:
    """Return the historical summary of the last completed turn, if present."""
    turn_dirs = sorted(
        (d for d in run_dir.iterdir() if d.is_dir() and d.name.startswith("turn-")),
        key=lambda d: d.name,
    )
    for turn_dir in reversed(turn_dirs):
        summary_path = turn_dir / "6-historical-summary.md"
        if summary_path.exists():
            try:
                text = summary_path.read_text(encoding="utf-8").strip()
            except OSError:
                return None
            return text or None
    return None


def _lexical_profile(text: str) -> set[str]:
    """Reduce a narrative text to a set of content words for similarity comparison.

    Tokens shorter than 4 characters are dropped, which removes most function
    words in both English and Swedish without a language-specific stopword list.
    """
    words = re.findall(r"[a-zA-ZåäöÅÄÖüÜéÉ]+", text.lower())
    return {w for w in words if len(w) >= 4}


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def analyze_ensemble(
    scenario_dir: Path,
    max_runs: int | None = None,
    filters: list[tuple[str, str]] | None = None,
    group_by: str | None = None,
) -> dict[str, Any]:
    """Analyze completed runs for a scenario and return a structured report dict.

    Args:
        scenario_dir: Path to the scenario directory (must contain a ``runs/`` subdirectory).
        max_runs: If given, analyze only the most recent N run directories
            (recency is applied before cohort filtering).
        filters: Optional ``KEY=VALUE`` cohort filters applied to each run's
            config.json metadata (see ``cohorts.py`` for key resolution).
        group_by: Optional cohort key. When given, the report gains a
            ``cohort_comparison`` block with per-group statistics; the pooled
            sections cover the whole filtered population.

    Returns:
        A dict with keys: scenario, run_overview, metric_trajectories,
        event_statistics, divergence, narrative_diversity, caveats – plus
        ``cohort_comparison`` when grouping.
    """
    from .cohorts import (
        apply_filters,
        available_cohort_keys,
        between_group_stats,
        mixed_scenario_warning,
        partition_runs,
    )

    run_dirs = _discover_completed_runs(scenario_dir, max_runs)
    if not run_dirs:
        raise ValueError(f"No completed runs found in: {scenario_dir / 'runs'}")

    excluded_note: str | None = None
    if filters:
        run_dirs, excluded = apply_filters(run_dirs, filters)
        if not run_dirs:
            available = available_cohort_keys(_discover_completed_runs(scenario_dir))
            raise ValueError(
                "No runs match filter "
                f"{' AND '.join(f'{k}={v}' for k, v in filters)}. "
                f"Available keys/values: {available}"
            )
        if excluded:
            excluded_note = (
                f"{len(excluded)} of {len(excluded) + len(run_dirs)} runs excluded by "
                f"filter {' AND '.join(f'{k}={v}' for k, v in filters)}"
            )

    report = _analyze_run_set(scenario_dir, run_dirs)

    caveats = report["caveats"]
    mixed = mixed_scenario_warning(run_dirs)
    if mixed:
        caveats.append(mixed)
    if excluded_note:
        caveats.append(excluded_note)

    if group_by:
        groups = partition_runs(run_dirs, group_by)
        report["cohort_comparison"] = {
            "group_by": group_by,
            **between_group_stats(groups),
        }
        small_groups = [value for value, dirs in groups if len(dirs) < 3]
        if small_groups:
            quoted = ", ".join("'" + value + "'" for value in small_groups)
            caveats.append(
                f"Cohort(s) with fewer than 3 runs: {quoted} – "
                "per-cohort estimates are unreliable."
            )
        if any(value == "(unknown)" for value, _ in groups):
            caveats.append(
                f"Some runs carry no '{group_by}' value in their metadata; they are "
                "reported under '(unknown)'."
            )

    return report


def _analyze_run_set(scenario_dir: Path, run_dirs: list[Path]) -> dict[str, Any]:
    """Analyze one explicit set of run directories (no discovery here)."""
    if not run_dirs:
        raise ValueError("No runs to analyze")
    # ------------------------------------------------------------------
    # 1. Per-run metadata
    # ------------------------------------------------------------------
    run_records: list[dict[str, Any]] = []
    all_llm_configs: list[str] = []  # serialized for comparison

    for run_dir in run_dirs:
        summary = _load_json_safe(run_dir / "summary.json") or {}
        costs = _load_json_safe(run_dir / "costs.json") or {}
        config = _load_json_safe(run_dir / "config.json") or {}

        total_cost = costs.get("total_cost_usd")
        run_records.append({
            "run": run_dir.name,
            "status": summary.get("status", "unknown"),
            "total_turns": int(summary.get("total_turns", 0) or 0),
            "total_cost_usd": float(total_cost) if isinstance(total_cost, (int, float)) else None,
        })

        llm_block = config.get("llm") if isinstance(config, dict) else None
        all_llm_configs.append(json.dumps(llm_block, sort_keys=True) if llm_block else "")

    num_runs = len(run_records)
    status_mix: dict[str, int] = {}
    for rec in run_records:
        status_mix[rec["status"]] = status_mix.get(rec["status"], 0) + 1

    valid_costs = [r["total_cost_usd"] for r in run_records if r["total_cost_usd"] is not None]
    total_cost_sum = _round2(sum(valid_costs)) if valid_costs else None
    mean_cost = _round2(mean(valid_costs)) if valid_costs else None

    run_overview: dict[str, Any] = {
        "num_runs": num_runs,
        "status_mix": status_mix,
        "turn_counts": [r["total_turns"] for r in run_records],
        "total_cost_usd": total_cost_sum,
        "mean_cost_usd": mean_cost,
    }

    # ------------------------------------------------------------------
    # 2. Metric trajectories
    # ------------------------------------------------------------------
    # metric_values_by_turn[turn][metric_id] = [values across runs]
    metric_values_by_turn: dict[int, dict[str, list[float]]] = {}

    for run_dir in run_dirs:
        turn_metrics = _read_turn_metrics(run_dir)
        for turn, metrics in turn_metrics.items():
            turn_bucket = metric_values_by_turn.setdefault(turn, {})
            for metric_id, value in metrics.items():
                turn_bucket.setdefault(metric_id, []).append(value)

    metric_trajectories: dict[str, dict[int, dict[str, float]]] = {}
    all_turns = sorted(metric_values_by_turn.keys())

    for turn in all_turns:
        for metric_id, values in metric_values_by_turn[turn].items():
            if metric_id not in metric_trajectories:
                metric_trajectories[metric_id] = {}
            metric_trajectories[metric_id][turn] = _distribution_stats(values)

    # ------------------------------------------------------------------
    # 3. Event statistics
    # ------------------------------------------------------------------
    # triggered_by_run[run_dir] = {turn: {event_id, ...}}
    triggered_by_run: dict[Path, dict[int, set[str]]] = {}
    # evaluations_by_run[run_dir] = {turn: [eval_entries]}
    evaluations_by_run: dict[Path, dict[int, list[dict[str, Any]]]] = {}

    for run_dir in run_dirs:
        triggered_by_run[run_dir] = _read_triggered_events_by_turn(run_dir)
        evaluations_by_run[run_dir] = _read_event_evaluations_by_turn(run_dir)

    # aggregate: per event_id: overall_count, per_turn_count, mean_evaluated_probability_by_turn
    event_overall_count: dict[str, int] = {}
    event_per_turn_count: dict[str, dict[int, int]] = {}
    # evaluated probability: event_id -> turn -> [probabilities across runs]
    eval_probs: dict[str, dict[int, list[float]]] = {}

    for run_dir in run_dirs:
        # Overall occurrence is derived from per-turn 1-events.json, not from
        # summary.json occurred_events: the latter only records non-repeatable
        # events and would undercount repeatable ones.
        events_in_run: set[str] = set()
        for event_set in triggered_by_run[run_dir].values():
            events_in_run |= event_set
        for eid in events_in_run:
            event_overall_count[eid] = event_overall_count.get(eid, 0) + 1

        for turn, event_set in triggered_by_run[run_dir].items():
            for eid in event_set:
                event_per_turn_count.setdefault(eid, {})[turn] = (
                    event_per_turn_count.get(eid, {}).get(turn, 0) + 1
                )

        for turn, evals in evaluations_by_run[run_dir].items():
            for entry in evals:
                if not isinstance(entry, dict):
                    continue
                if entry.get("skipped"):
                    continue
                eid = entry.get("id")
                prob = entry.get("probability")
                if isinstance(eid, str) and isinstance(prob, (int, float)):
                    eval_probs.setdefault(eid, {}).setdefault(turn, []).append(float(prob))

    # Build final event stats
    all_event_ids = sorted(
        set(event_overall_count) | set(event_per_turn_count)
    )
    event_statistics: dict[str, Any] = {}
    for eid in all_event_ids:
        overall_count = event_overall_count.get(eid, 0)
        per_turn = dict(sorted(event_per_turn_count.get(eid, {}).items()))
        mean_eval_prob_by_turn: dict[int, float] = {}
        for turn, probs in sorted(eval_probs.get(eid, {}).items()):
            if probs:
                mean_eval_prob_by_turn[turn] = _round2(mean(probs))
        event_statistics[eid] = {
            "overall_occurrence_rate": _round2(overall_count / num_runs),
            "overall_occurrence_count": overall_count,
            "occurrence_per_turn": per_turn,
            "mean_evaluated_probability_per_turn": mean_eval_prob_by_turn,
        }

    # ------------------------------------------------------------------
    # 4. Divergence detection
    # ------------------------------------------------------------------
    # For each metric, find the turn with the largest IQR jump.
    divergence: list[dict[str, Any]] = []

    for metric_id, traj in metric_trajectories.items():
        turns_sorted = sorted(traj.keys())
        if len(turns_sorted) < 2:
            continue

        max_iqr_jump = 0.0
        max_jump_turn = turns_sorted[1]
        prev_iqr = traj[turns_sorted[0]].get("iqr", 0.0)
        for t in turns_sorted[1:]:
            curr_iqr = traj[t].get("iqr", 0.0)
            jump = curr_iqr - prev_iqr
            if jump > max_iqr_jump:
                max_iqr_jump = jump
                max_jump_turn = t
            prev_iqr = curr_iqr

        if max_iqr_jump <= 0:
            continue

        # Check event association for this metric at max_jump_turn
        event_associations: list[dict[str, Any]] = []
        for eid in all_event_ids:
            # For each run: did event E occur by turn max_jump_turn?
            with_event: list[float] = []
            without_event: list[float] = []
            for run_dir in run_dirs:
                # Check if event occurred by or at max_jump_turn
                triggered = triggered_by_run[run_dir]
                occurred_by_turn = any(
                    eid in triggered.get(t, set())
                    for t in range(1, max_jump_turn + 1)
                )
                turn_metrics = _read_turn_metrics(run_dir)
                value = turn_metrics.get(max_jump_turn, {}).get(metric_id)
                if value is None:
                    continue
                if occurred_by_turn:
                    with_event.append(value)
                else:
                    without_event.append(value)

            if len(with_event) >= 2 and len(without_event) >= 2:
                diff = _round2(mean(with_event) - mean(without_event))
                event_associations.append({
                    "event_id": eid,
                    "mean_with_event": _round2(mean(with_event)),
                    "mean_without_event": _round2(mean(without_event)),
                    "mean_diff": diff,
                    "n_with": len(with_event),
                    "n_without": len(without_event),
                    "note": "association, small N" if len(with_event) + len(without_event) < 10 else "association",
                })

        event_associations.sort(key=lambda x: abs(x["mean_diff"]), reverse=True)

        divergence.append({
            "metric": metric_id,
            "max_iqr_jump": _round2(max_iqr_jump),
            "divergence_turn": max_jump_turn,
            "event_associations": event_associations[:5],
        })

    divergence.sort(key=lambda x: x["max_iqr_jump"], reverse=True)

    # ------------------------------------------------------------------
    # 5. Narrative diversity
    # ------------------------------------------------------------------
    # Metric spread can hide storyline monoculture: runs may reach different
    # numbers through near-identical narratives. Compare the final historical
    # summaries lexically (pairwise Jaccard over content words) as a cheap,
    # local proxy for how different the storylines actually are.
    narrative_diversity: dict[str, Any] | None = None
    profiles: list[tuple[str, set[str]]] = []
    for run_dir in run_dirs:
        text = _read_final_historical_summary(run_dir)
        if text:
            profiles.append((run_dir.name, _lexical_profile(text)))

    if len(profiles) >= 2:
        similarities: list[tuple[float, str, str]] = []
        for (name_a, prof_a), (name_b, prof_b) in combinations(profiles, 2):
            similarities.append((_jaccard(prof_a, prof_b), name_a, name_b))
        sims = [s for s, _, _ in similarities]
        most_similar = max(similarities, key=lambda x: x[0])
        most_distinct = min(similarities, key=lambda x: x[0])
        narrative_diversity = {
            "n_texts": len(profiles),
            "mean_pairwise_similarity": _round2(mean(sims)),
            "min_pairwise_similarity": _round2(min(sims)),
            "max_pairwise_similarity": _round2(max(sims)),
            "most_similar_pair": [most_similar[1], most_similar[2]],
            "most_distinct_pair": [most_distinct[1], most_distinct[2]],
            "method": (
                "Jaccard similarity over content words (length >= 4) of each run's "
                "final historical summary. Lexical only; does not capture paraphrase."
            ),
        }

    # ------------------------------------------------------------------
    # 6. Caveats
    # ------------------------------------------------------------------
    caveats: list[str] = []

    if narrative_diversity and narrative_diversity["mean_pairwise_similarity"] >= 0.5:
        caveats.append(
            f"Final narratives are lexically similar across runs (mean pairwise Jaccard "
            f"{narrative_diversity['mean_pairwise_similarity']:.2f}). Metric spread may hide "
            "storyline monoculture – inspect a few historical summaries side by side."
        )

    if num_runs < 10:
        caveats.append(
            f"Only {num_runs} completed run(s) analyzed – results may not be representative "
            f"(recommended: 10+)."
        )

    unique_llm_configs = set(all_llm_configs)
    if len(unique_llm_configs) > 1:
        caveats.append(
            "Runs use different model configurations (llm blocks in config.json differ). "
            "Outcome variation may reflect model differences rather than scenario stochasticity. "
            "Use 'model-sensitivity' for a dedicated breakdown."
        )

    has_evaluations = any(bool(evals) for evals in evaluations_by_run.values())
    if not has_evaluations:
        caveats.append(
            "No 1-event-evaluations.json files found – these are only produced by newer runs. "
            "Mean evaluated probability column is absent from event statistics."
        )

    return {
        "scenario": scenario_dir.name,
        "run_overview": run_overview,
        "metric_trajectories": metric_trajectories,
        "event_statistics": event_statistics,
        "divergence": divergence,
        "narrative_diversity": narrative_diversity,
        "caveats": caveats,
    }


# ---------------------------------------------------------------------------
# Markdown report formatting
# ---------------------------------------------------------------------------

def format_ensemble_report(report: dict[str, Any]) -> str:
    """Format an ensemble analysis result as a markdown report."""
    lines: list[str] = []

    lines.append(f"# Ensemble Analysis: {report['scenario']}")
    lines.append("")

    # ------------------------------------------------------------------
    # Run overview
    # ------------------------------------------------------------------
    overview = report["run_overview"]
    lines.append("## Run Overview")
    lines.append("")
    lines.append(f"- Runs analyzed: {overview['num_runs']}")

    status_mix = overview["status_mix"]
    if status_mix:
        mix_str = ", ".join(f"{k}: {v}" for k, v in sorted(status_mix.items()))
        lines.append(f"- Status mix: {mix_str}")

    turn_counts = overview["turn_counts"]
    if turn_counts:
        lines.append(f"- Turn counts: min {min(turn_counts)}, max {max(turn_counts)}, mean {_round2(mean(turn_counts))}")

    if overview["total_cost_usd"] is not None:
        lines.append(f"- Total cost: ${overview['total_cost_usd']:.4f} USD")
    if overview["mean_cost_usd"] is not None:
        lines.append(f"- Mean cost per run: ${overview['mean_cost_usd']:.4f} USD")

    lines.append("")

    # ------------------------------------------------------------------
    # Metric trajectories
    # ------------------------------------------------------------------
    lines.append("## Metric Trajectories")
    lines.append("")

    traj = report["metric_trajectories"]
    if not traj:
        lines.append("No metric data found.")
        lines.append("")
    else:
        for metric_id, turns_data in sorted(traj.items()):
            lines.append(f"### {metric_id}")
            lines.append("")

            header = "| turn |   n | mean   | min    | p10    | p50    | p90    | max    |"
            sep    = "|------|-----|--------|--------|--------|--------|--------|--------|"
            lines.append(header)
            lines.append(sep)

            for turn in sorted(turns_data.keys()):
                s = turns_data[turn]
                if not s:
                    continue
                lines.append(
                    f"| {turn:4d} | {int(s.get('n', 0)):3d}"
                    f" | {s.get('mean', 0):6.1f}"
                    f" | {s.get('min', 0):6.1f}"
                    f" | {s.get('p10', 0):6.1f}"
                    f" | {s.get('p50', 0):6.1f}"
                    f" | {s.get('p90', 0):6.1f}"
                    f" | {s.get('max', 0):6.1f} |"
                )
            lines.append("")

    # ------------------------------------------------------------------
    # Event statistics
    # ------------------------------------------------------------------
    lines.append("## Event Statistics")
    lines.append("")

    ev_stats = report["event_statistics"]
    if not ev_stats:
        lines.append("No event data found.")
        lines.append("")
    else:
        has_eval_probs = any(
            bool(v.get("mean_evaluated_probability_per_turn"))
            for v in ev_stats.values()
        )

        for eid, stats in sorted(ev_stats.items()):
            rate = stats["overall_occurrence_rate"]
            count = stats["overall_occurrence_count"]
            per_turn = stats.get("occurrence_per_turn", {})
            eval_probs_by_turn = stats.get("mean_evaluated_probability_per_turn", {})

            lines.append(f"**{eid}** – overall rate: {rate:.2f} ({count} of {report['run_overview']['num_runs']} runs)")

            if per_turn:
                turn_str = ", ".join(f"turn {t}: {c}" for t, c in sorted(per_turn.items()))
                lines.append(f"  Occurrences by turn: {turn_str}")

            if has_eval_probs and eval_probs_by_turn:
                prob_str = ", ".join(
                    f"turn {t}: {p:.2f}" for t, p in sorted(eval_probs_by_turn.items())
                )
                lines.append(f"  Mean evaluated probability: {prob_str}")
            elif has_eval_probs:
                lines.append("  Mean evaluated probability: (no evaluation data for this event)")

            lines.append("")

    # ------------------------------------------------------------------
    # Cohort comparison (when grouped)
    # ------------------------------------------------------------------
    cohorts = report.get("cohort_comparison")
    if cohorts:
        lines.append(f"## Cohort Comparison (group-by: {cohorts['group_by']})")
        lines.append("")
        lines.append("Per-cohort aggregates over each group's runs. Pooled sections above mix all cohorts.")
        lines.append("")

        group_names = [g["cohort"] for g in cohorts["groups"]]
        header = "| cohort | n |"
        sep = "|--------|---|"
        lines.append(header)
        lines.append(sep)
        for g in cohorts["groups"]:
            lines.append(f"| {g['cohort']} | {g['n_runs']} |")
        lines.append("")

        finals = cohorts.get("final_metrics_mean") or {}
        if finals:
            lines.append("### Final metric mean per cohort")
            lines.append("")
            header = "| metric | " + " | ".join(group_names) + " |"
            sep = "|--------|" + "|".join(["------"] * len(group_names)) + "|"
            lines.append(header)
            lines.append(sep)
            for mid, by_group in sorted(finals.items()):
                cols = " | ".join(
                    f"{by_group.get(name, float('nan')):.1f}" if name in by_group else "–"
                    for name in group_names
                )
                lines.append(f"| {mid} | {cols} |")
            lines.append("")

        rates = cohorts.get("event_occurrence_rate") or {}
        if rates:
            lines.append("### Event occurrence rate per cohort")
            lines.append("")
            header = "| event | " + " | ".join(group_names) + " |"
            sep = "|-------|" + "|".join(["------"] * len(group_names)) + "|"
            lines.append(header)
            lines.append(sep)
            for eid, by_group in sorted(rates.items()):
                cols = " | ".join(
                    f"{by_group.get(name, 0.0):.2f}" if name in by_group else "–"
                    for name in group_names
                )
                lines.append(f"| {eid} | {cols} |")
            lines.append("")

    # ------------------------------------------------------------------
    # Divergence
    # ------------------------------------------------------------------
    lines.append("## Divergence Detection")
    lines.append("")

    divergence = report["divergence"]
    if not divergence:
        lines.append("No divergence detected across metrics.")
        lines.append("")
    else:
        lines.append(
            "Metrics ranked by largest IQR jump between consecutive turns. "
            "Event associations show mean metric value split by whether the event "
            "had occurred by that turn (descriptive only)."
        )
        lines.append("")

        for entry in divergence:
            lines.append(
                f"### {entry['metric']} – divergence at turn {entry['divergence_turn']} "
                f"(IQR jump: +{entry['max_iqr_jump']:.2f})"
            )
            lines.append("")

            assocs = entry.get("event_associations", [])
            if assocs:
                lines.append("| event | mean (with) | mean (without) | diff | n_with | n_without | note |")
                lines.append("|-------|-------------|----------------|------|--------|-----------|------|")
                for a in assocs:
                    lines.append(
                        f"| {a['event_id']}"
                        f" | {a['mean_with_event']:.1f}"
                        f" | {a['mean_without_event']:.1f}"
                        f" | {a['mean_diff']:+.1f}"
                        f" | {a['n_with']}"
                        f" | {a['n_without']}"
                        f" | {a['note']} |"
                    )
                lines.append("")
            else:
                lines.append("No event associations with sufficient split (need ≥2 runs in each group).")
                lines.append("")

    # ------------------------------------------------------------------
    # Narrative diversity
    # ------------------------------------------------------------------
    diversity = report.get("narrative_diversity")
    if diversity:
        lines.append("## Narrative Diversity")
        lines.append("")
        lines.append(
            f"- Final historical summaries compared: {diversity['n_texts']}"
        )
        lines.append(
            f"- Mean pairwise similarity: {diversity['mean_pairwise_similarity']:.2f} "
            f"(min {diversity['min_pairwise_similarity']:.2f}, "
            f"max {diversity['max_pairwise_similarity']:.2f})"
        )
        lines.append(
            f"- Most similar pair: {diversity['most_similar_pair'][0]} / {diversity['most_similar_pair'][1]}"
        )
        lines.append(
            f"- Most distinct pair: {diversity['most_distinct_pair'][0]} / {diversity['most_distinct_pair'][1]}"
        )
        lines.append(f"- Method: {diversity['method']}")
        lines.append("")

    # ------------------------------------------------------------------
    # Caveats
    # ------------------------------------------------------------------
    caveats = report["caveats"]
    if caveats:
        lines.append("## Caveats")
        lines.append("")
        for caveat in caveats:
            lines.append(f"- {caveat}")
        lines.append("")

    return "\n".join(lines)
