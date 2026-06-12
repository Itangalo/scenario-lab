"""Model-sensitivity analysis: compare outcomes across runs with different LLM configs."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from .ensemble import (
    _discover_completed_runs,
    _distribution_stats,
    _load_json_safe,
    _read_triggered_events_by_turn,
    _round2,
)


# ---------------------------------------------------------------------------
# Grouping helpers
# ---------------------------------------------------------------------------

def _llm_group_key(config: dict[str, Any]) -> str:
    """Derive a stable group key from the llm block of a config.json.

    The key is the JSON-serialized, sorted set of task->model assignments,
    excluding non-model fields (temperature, max_tokens, etc.).
    """
    llm = config.get("llm") if isinstance(config, dict) else None
    if not isinstance(llm, dict):
        return "unknown"

    task_model_pairs: dict[str, str] = {}
    model_task_names = {"events", "actors", "rules", "metrics", "summary", "referee", "analysis"}
    for task in sorted(model_task_names):
        value = llm.get(task)
        if isinstance(value, str):
            task_model_pairs[task] = value
        elif isinstance(value, dict):
            # ModelRoute serialized as object – keep the string representation
            task_model_pairs[task] = json.dumps(value, sort_keys=True)

    return json.dumps(task_model_pairs, sort_keys=True)


def _group_label(key: str) -> str:
    """Return a compact human-readable label for a model group key."""
    try:
        parsed = json.loads(key)
        if isinstance(parsed, dict):
            models = sorted(set(parsed.values()))
            return ", ".join(models) if models else key
    except (json.JSONDecodeError, TypeError):
        pass
    return key


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def analyze_model_sensitivity(
    scenario_dir: Path,
    max_runs: int | None = None,
) -> dict[str, Any]:
    """Analyze how outcomes vary across different model configurations.

    Args:
        scenario_dir: Path to the scenario directory (must contain ``runs/``).
        max_runs: If given, consider only the most recent N completed runs.

    Returns:
        A dict with keys: scenario, groups, per_metric, per_event,
        robustness, caveats.
    """
    run_dirs = _discover_completed_runs(scenario_dir, max_runs)
    if not run_dirs:
        raise ValueError(f"No completed runs found in: {scenario_dir / 'runs'}")

    # ------------------------------------------------------------------
    # 1. Group runs by model config
    # ------------------------------------------------------------------
    group_runs: dict[str, list[Path]] = {}
    for run_dir in run_dirs:
        config = _load_json_safe(run_dir / "config.json") or {}
        key = _llm_group_key(config)
        group_runs.setdefault(key, []).append(run_dir)

    groups: list[dict[str, Any]] = []
    for key, dirs in sorted(group_runs.items()):
        groups.append({
            "group_key": key,
            "label": _group_label(key),
            "n_runs": len(dirs),
            "run_names": [d.name for d in dirs],
        })

    # ------------------------------------------------------------------
    # 2. Per-metric final-value distributions per group
    # ------------------------------------------------------------------
    # final_values[group_key][metric_id] = [values]
    final_values: dict[str, dict[str, list[float]]] = {k: {} for k in group_runs}
    # occurred_events[group_key][event_id] = count
    occurred_events: dict[str, dict[str, int]] = {k: {} for k in group_runs}

    for key, dirs in group_runs.items():
        for run_dir in dirs:
            summary = _load_json_safe(run_dir / "summary.json") or {}
            fm = summary.get("final_metrics", {})
            if isinstance(fm, dict):
                for mid, val in fm.items():
                    if isinstance(val, (int, float)):
                        final_values[key].setdefault(mid, []).append(float(val))

            # Derive occurrence from per-turn 1-events.json rather than
            # summary.json occurred_events, which only records non-repeatable
            # events and would undercount repeatable ones.
            events_in_run: set[str] = set()
            for event_set in _read_triggered_events_by_turn(run_dir).values():
                events_in_run |= event_set
            for eid in events_in_run:
                occurred_events[key][eid] = occurred_events[key].get(eid, 0) + 1

    # Collect all metric and event ids
    all_metric_ids = sorted(
        {mid for vals in final_values.values() for mid in vals}
    )
    all_event_ids = sorted(
        {eid for counts in occurred_events.values() for eid in counts}
    )

    per_metric: list[dict[str, Any]] = []
    for mid in all_metric_ids:
        group_stats: dict[str, dict[str, float]] = {}
        for key in group_runs:
            vals = final_values[key].get(mid, [])
            if vals:
                group_stats[key] = _distribution_stats(vals)
        per_metric.append({
            "metric": mid,
            "by_group": group_stats,
        })

    per_event: list[dict[str, Any]] = []
    for eid in all_event_ids:
        group_rates: dict[str, float] = {}
        for key, dirs in group_runs.items():
            n = len(dirs)
            count = occurred_events[key].get(eid, 0)
            group_rates[key] = _round2(count / n) if n > 0 else 0.0
        per_event.append({
            "event": eid,
            "by_group": group_rates,
        })

    # ------------------------------------------------------------------
    # 3. Robustness summary
    # ------------------------------------------------------------------
    group_keys = list(group_runs.keys())
    single_group = len(group_keys) == 1

    robust_metrics: list[str] = []
    sensitive_metrics: list[str] = []
    robust_events: list[str] = []
    sensitive_events: list[str] = []

    if not single_group:
        for entry in per_metric:
            mid = entry["metric"]
            group_means = [
                s["mean"] for s in entry["by_group"].values()
                if "mean" in s
            ]
            if len(group_means) < 2:
                continue
            # Use observed spread as the denominator
            all_vals_for_metric = [
                v for key in group_runs
                for v in final_values[key].get(mid, [])
            ]
            observed_range = max(all_vals_for_metric) - min(all_vals_for_metric) if all_vals_for_metric else 0.0
            mean_spread = max(group_means) - min(group_means)
            # Call "sensitive" if group means differ by more than 20% of observed range
            threshold = 0.20 * observed_range if observed_range > 0 else 1e-9
            if mean_spread > threshold:
                sensitive_metrics.append(mid)
            else:
                robust_metrics.append(mid)

        for entry in per_event:
            eid = entry["event"]
            rates = list(entry["by_group"].values())
            if len(rates) < 2:
                continue
            rate_diff = max(rates) - min(rates)
            if rate_diff > 0.3:
                sensitive_events.append(eid)
            else:
                robust_events.append(eid)

    robustness: dict[str, Any] = {
        "single_group": single_group,
        "robust_metrics": sorted(robust_metrics),
        "sensitive_metrics": sorted(sensitive_metrics),
        "robust_events": sorted(robust_events),
        "sensitive_events": sorted(sensitive_events),
    }

    # ------------------------------------------------------------------
    # 4. Caveats
    # ------------------------------------------------------------------
    caveats: list[str] = []

    if single_group:
        caveats.append(
            "All analyzed runs use the same model configuration – sensitivity cannot be assessed. "
            "To compare models, use 'batch-run' with different 'variants/' (each variant specifying "
            "a different model in scenario.yaml)."
        )

    total_runs = len(run_dirs)
    if total_runs < 6:
        caveats.append(
            f"Only {total_runs} completed run(s) total – per-group sample sizes are very small. "
            "Reported statistics are descriptive only."
        )

    for g in groups:
        if g["n_runs"] < 3:
            caveats.append(
                f"Group '{g['label']}' has only {g['n_runs']} run(s) – "
                "estimates for this group are unreliable."
            )

    return {
        "scenario": scenario_dir.name,
        "run_overview": {"num_runs": len(run_dirs)},
        "groups": groups,
        "per_metric": per_metric,
        "per_event": per_event,
        "robustness": robustness,
        "caveats": caveats,
    }


# ---------------------------------------------------------------------------
# Markdown report formatting
# ---------------------------------------------------------------------------

def format_model_sensitivity_report(report: dict[str, Any]) -> str:
    """Format a model-sensitivity analysis result as a markdown report."""
    lines: list[str] = []

    lines.append(f"# Model Sensitivity: {report['scenario']}")
    lines.append("")

    # ------------------------------------------------------------------
    # Groups
    # ------------------------------------------------------------------
    lines.append("## Model Groups")
    lines.append("")

    for i, group in enumerate(report["groups"], start=1):
        lines.append(f"**Group {i}** – {group['label']} (N={group['n_runs']})")
        lines.append("")

    # Early exit if single group
    robustness = report["robustness"]
    if robustness["single_group"]:
        lines.append("## Sensitivity Assessment")
        lines.append("")
        lines.append(
            "Only one model group found. Sensitivity cannot be assessed. "
            "Run the scenario with different model configurations via variants and batch-run."
        )
        lines.append("")
        if report["caveats"]:
            lines.append("## Caveats")
            lines.append("")
            for caveat in report["caveats"]:
                lines.append(f"- {caveat}")
            lines.append("")
        return "\n".join(lines)

    group_labels = {g["group_key"]: f"Group {i+1}" for i, g in enumerate(report["groups"])}

    # ------------------------------------------------------------------
    # Per-metric
    # ------------------------------------------------------------------
    lines.append("## Final Metric Distributions by Group")
    lines.append("")

    per_metric = report["per_metric"]
    if not per_metric:
        lines.append("No metric data available.")
        lines.append("")
    else:
        for entry in per_metric:
            mid = entry["metric"]
            by_group = entry["by_group"]
            lines.append(f"### {mid}")
            lines.append("")
            lines.append("| group | n | mean | min | p10 | p90 | max |")
            lines.append("|-------|---|------|-----|-----|-----|-----|")
            for key, stats in by_group.items():
                label = group_labels.get(key, key[:20])
                lines.append(
                    f"| {label}"
                    f" | {int(stats.get('n', 0))}"
                    f" | {stats.get('mean', 0):.1f}"
                    f" | {stats.get('min', 0):.1f}"
                    f" | {stats.get('p10', 0):.1f}"
                    f" | {stats.get('p90', 0):.1f}"
                    f" | {stats.get('max', 0):.1f} |"
                )
            lines.append("")

    # ------------------------------------------------------------------
    # Per-event
    # ------------------------------------------------------------------
    lines.append("## Event Occurrence Rates by Group")
    lines.append("")

    per_event = report["per_event"]
    if not per_event:
        lines.append("No event data available.")
        lines.append("")
    else:
        group_count = len(report["groups"])
        header_cols = " | ".join(f"Group {i+1}" for i in range(group_count))
        sep_cols = " | ".join("-----" for _ in range(group_count))
        lines.append(f"| event | {header_cols} |")
        lines.append(f"|-------|{sep_cols} |")
        for entry in per_event:
            eid = entry["event"]
            rate_cols = []
            for g in report["groups"]:
                rate = entry["by_group"].get(g["group_key"], 0.0)
                rate_cols.append(f"{rate:.2f}")
            lines.append(f"| {eid} | {' | '.join(rate_cols)} |")
        lines.append("")

    # ------------------------------------------------------------------
    # Robustness
    # ------------------------------------------------------------------
    lines.append("## Robustness Summary")
    lines.append("")
    lines.append(
        "Metrics are labeled 'sensitive' if group means differ by more than 20% of "
        "the observed value range. Events are labeled 'sensitive' if occurrence rates "
        "differ by more than 0.30. All labels are descriptive."
    )
    lines.append("")

    if robustness["sensitive_metrics"]:
        lines.append("Sensitive metrics (groups disagree):")
        lines.append("")
        for m in robustness["sensitive_metrics"]:
            lines.append(f"- {m}")
        lines.append("")

    if robustness["robust_metrics"]:
        lines.append("Robust metrics (groups agree):")
        lines.append("")
        for m in robustness["robust_metrics"]:
            lines.append(f"- {m}")
        lines.append("")

    if robustness["sensitive_events"]:
        lines.append("Sensitive events (rate difference > 0.30):")
        lines.append("")
        for e in robustness["sensitive_events"]:
            lines.append(f"- {e}")
        lines.append("")

    if robustness["robust_events"]:
        lines.append("Robust events (rate difference ≤ 0.30):")
        lines.append("")
        for e in robustness["robust_events"]:
            lines.append(f"- {e}")
        lines.append("")

    if not any([
        robustness["sensitive_metrics"],
        robustness["robust_metrics"],
        robustness["sensitive_events"],
        robustness["robust_events"],
    ]):
        lines.append("Insufficient data for robustness classification.")
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
