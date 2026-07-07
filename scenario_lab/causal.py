"""Causal impact estimation for events via forced/suppressed branch batches.

The existing primitives already support event counterfactuals: ``branch``
can force or suppress a specific event on its first executed turn, and the
batch machinery can run many children in parallel. This module glues them
into one workflow: plan matched pairs of forced/suppressed branches for an
event, discover the resulting runs, and compare final-metric distributions
between the two groups to estimate the event's causal effect at the branch
point.

Design notes:

- Each pair index gets one seed used for both the forced and the suppressed
  branch. The dice for all *other* events then match within a pair, so paired
  differences isolate the target event's effect much better than independent
  runs would (LLM outputs remain nondeterministic, so this reduces variance
  rather than eliminating it).
- Branch runs are grouped by inspecting ``event_overrides`` in each run's
  ``config.json``; no extra bookkeeping files are needed.
"""

from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Optional


@dataclass
class CausalJob:
    """One planned branch-child process for a causal-impact batch."""

    event_id: str
    mode: str  # "force" | "suppress"
    seed: int
    pair_index: int
    command: list[str] = field(default_factory=list)


def plan_causal_jobs(
    parent_run: Path,
    event_ids: list[str],
    *,
    repeats: int,
    from_turn: int,
    turns: Optional[int] = None,
    base_seed: Optional[int] = None,
) -> list[CausalJob]:
    """Plan matched forced/suppressed branch jobs for the given events.

    Args:
        parent_run: Completed run to branch from.
        event_ids: Events to estimate impact for (one force/suppress pair set each).
        repeats: Number of matched pairs per event.
        from_turn: Branch point; overrides apply to turn ``from_turn + 1``.
        turns: Optional total turn count for the branches.
        base_seed: Base for the derived pair seeds (random if omitted).

    Returns:
        List of CausalJob with ready-to-execute child commands.
    """
    if repeats < 1:
        raise ValueError(f"repeats must be >= 1, got {repeats}")
    if base_seed is None:
        base_seed = random.getrandbits(32)

    jobs: list[CausalJob] = []
    for event_id in event_ids:
        for pair_index in range(repeats):
            seed = base_seed + pair_index
            for mode in ("force", "suppress"):
                flag = "--force-event" if mode == "force" else "--suppress-event"
                command = [
                    sys.executable,
                    "-u",
                    "-m",
                    "scenario_lab.cli",
                    "branch",
                    str(parent_run),
                    "--from-turn",
                    str(from_turn),
                    flag,
                    event_id,
                    "--seed",
                    str(seed),
                ]
                if turns is not None:
                    command.extend(["--turns", str(turns)])
                jobs.append(
                    CausalJob(
                        event_id=event_id,
                        mode=mode,
                        seed=seed,
                        pair_index=pair_index,
                        command=command,
                    )
                )
    return jobs


def _load_json_safe(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _override_mode_for_event(config: dict, event_id: str) -> Optional[str]:
    """Return "force"/"suppress" if the run's overrides target exactly this event."""
    overrides = config.get("event_overrides")
    if not isinstance(overrides, dict):
        return None
    force = overrides.get("force") or []
    suppress = overrides.get("suppress") or []
    if force == [event_id] and not suppress:
        return "force"
    if suppress == [event_id] and not force:
        return "suppress"
    return None


def discover_causal_branches(
    scenario_dir: Path,
    event_id: str,
    *,
    parent_run: Optional[str] = None,
) -> dict[str, list[Path]]:
    """Find completed branch runs whose overrides force or suppress one event.

    Args:
        scenario_dir: Scenario directory containing ``runs/``.
        event_id: The target event id.
        parent_run: If given, only include branches of this parent run name.

    Returns:
        Dict with keys "force" and "suppress", each a list of run directories.
    """
    groups: dict[str, list[Path]] = {"force": [], "suppress": []}
    runs_dir = scenario_dir / "runs"
    if not runs_dir.is_dir():
        return groups

    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir() or not run_dir.name.startswith("run-"):
            continue
        config = _load_json_safe(run_dir / "config.json")
        if not isinstance(config, dict):
            continue
        mode = _override_mode_for_event(config, event_id)
        if mode is None:
            continue
        if parent_run is not None:
            parent = config.get("parent_run") or (config.get("metadata") or {}).get("parent_run")
            if parent is not None and Path(str(parent)).name != parent_run:
                continue
        summary = _load_json_safe(run_dir / "summary.json")
        if not isinstance(summary, dict) or summary.get("status") != "completed":
            continue
        groups[mode].append(run_dir)

    return groups


def _final_metrics(run_dir: Path) -> dict[str, float]:
    summary = _load_json_safe(run_dir / "summary.json") or {}
    metrics = summary.get("final_metrics") or {}
    return {
        k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))
    }


def _run_seed(run_dir: Path) -> Optional[int]:
    config = _load_json_safe(run_dir / "config.json") or {}
    seed = config.get("random_seed")
    return seed if isinstance(seed, int) else None


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    ordered = sorted(values)
    n = len(ordered)
    return {
        "n": n,
        "mean": round(mean(ordered), 2),
        "min": round(ordered[0], 2),
        "max": round(ordered[-1], 2),
    }


def analyze_causal_impact(
    scenario_dir: Path,
    event_id: str,
    *,
    parent_run: Optional[str] = None,
) -> dict[str, Any]:
    """Compare final metrics between forced and suppressed branches of one event.

    Returns:
        Report dict with group sizes, per-metric group stats, mean differences
        (force − suppress), paired differences where seeds match, and caveats.
    """
    groups = discover_causal_branches(scenario_dir, event_id, parent_run=parent_run)
    forced, suppressed = groups["force"], groups["suppress"]

    if not forced or not suppressed:
        raise ValueError(
            f"Need at least one completed forced and one suppressed branch for "
            f"'{event_id}' (found {len(forced)} forced, {len(suppressed)} suppressed)."
        )

    forced_metrics = {run: _final_metrics(run) for run in forced}
    suppressed_metrics = {run: _final_metrics(run) for run in suppressed}

    metric_ids = sorted(
        {m for metrics in forced_metrics.values() for m in metrics}
        & {m for metrics in suppressed_metrics.values() for m in metrics}
    )

    # Pair runs by seed for matched-dice comparison.
    forced_by_seed: dict[int, Path] = {}
    for run in forced:
        seed = _run_seed(run)
        if seed is not None and seed not in forced_by_seed:
            forced_by_seed[seed] = run
    pairs: list[tuple[Path, Path]] = []
    for run in suppressed:
        seed = _run_seed(run)
        if seed is not None and seed in forced_by_seed:
            pairs.append((forced_by_seed[seed], run))

    metrics_report: dict[str, Any] = {}
    for metric_id in metric_ids:
        f_values = [m[metric_id] for m in forced_metrics.values() if metric_id in m]
        s_values = [m[metric_id] for m in suppressed_metrics.values() if metric_id in m]
        entry: dict[str, Any] = {
            "forced": _stats(f_values),
            "suppressed": _stats(s_values),
            "mean_effect": round(mean(f_values) - mean(s_values), 2),
        }
        if pairs:
            paired_diffs = []
            for f_run, s_run in pairs:
                fm, sm = forced_metrics[f_run], suppressed_metrics[s_run]
                if metric_id in fm and metric_id in sm:
                    paired_diffs.append(fm[metric_id] - sm[metric_id])
            if paired_diffs:
                entry["paired_mean_effect"] = round(mean(paired_diffs), 2)
                entry["paired_diffs"] = [round(d, 2) for d in paired_diffs]
        metrics_report[metric_id] = entry

    caveats: list[str] = []
    n_total = len(forced) + len(suppressed)
    if n_total < 10:
        caveats.append(
            f"Only {len(forced)} forced + {len(suppressed)} suppressed runs – "
            "effect estimates are noisy (recommended: 5+ pairs)."
        )
    if not pairs:
        caveats.append(
            "No seed-matched pairs found – differences include dice noise from "
            "other events, not just the target event's effect."
        )
    caveats.append(
        "Effects are causal only with respect to the simulation at this branch "
        "point, and only as reliable as the underlying world-model."
    )

    return {
        "scenario": scenario_dir.name,
        "event_id": event_id,
        "n_forced": len(forced),
        "n_suppressed": len(suppressed),
        "n_pairs": len(pairs),
        "metrics": metrics_report,
        "caveats": caveats,
    }


def format_causal_report(report: dict[str, Any]) -> str:
    """Format a causal-impact analysis as a markdown report."""
    lines: list[str] = []
    lines.append(f"# Causal Impact: {report['event_id']} ({report['scenario']})")
    lines.append("")
    lines.append(
        f"Forced branches: {report['n_forced']} · Suppressed branches: "
        f"{report['n_suppressed']} · Seed-matched pairs: {report['n_pairs']}"
    )
    lines.append("")
    lines.append(
        "Mean effect = mean(final metric | event forced) − mean(final metric | "
        "event suppressed). Positive means the event pushes the metric up."
    )
    lines.append("")

    lines.append("| metric | forced mean | suppressed mean | mean effect | paired effect | n |")
    lines.append("|--------|-------------|-----------------|-------------|---------------|---|")
    for metric_id, entry in sorted(report["metrics"].items()):
        forced = entry.get("forced", {})
        suppressed = entry.get("suppressed", {})
        paired = entry.get("paired_mean_effect")
        paired_str = f"{paired:+.2f}" if paired is not None else "–"
        lines.append(
            f"| {metric_id}"
            f" | {forced.get('mean', 0):.2f}"
            f" | {suppressed.get('mean', 0):.2f}"
            f" | {entry['mean_effect']:+.2f}"
            f" | {paired_str}"
            f" | {int(forced.get('n', 0))}+{int(suppressed.get('n', 0))} |"
        )
    lines.append("")

    if report["caveats"]:
        lines.append("## Caveats")
        lines.append("")
        for caveat in report["caveats"]:
            lines.append(f"- {caveat}")
        lines.append("")

    return "\n".join(lines)
