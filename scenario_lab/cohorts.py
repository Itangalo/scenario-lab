"""Cohort bookkeeping over completed runs.

A run's cohort is derived from metadata already persisted in its
``config.json`` – no new run-time state. Two axes are supported:

- **Scenario identity** – ``config.json``'s ``name`` and ``actors``, which
  separate a variant's runs from its base scenario's (variant runs land in the
  base scenario's ``runs/`` because output follows the resolved base).
- **Initial-state group** – ``key=value`` pairs recorded in
  ``initial_state.notes`` (for example ``"arm=fast; draw=018; ..."``), or the
  draw's directory name taken from ``initial_state.source``.

This module is deliberately bookkeeping only: which runs form a cohort is a
filesystem question. What the difference between cohorts *means* is an LLM
judgment and belongs in the prompts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


UNKNOWN_GROUP = "(unknown)"

# Keys every run can be filtered or grouped by, regardless of notes content.
BUILTIN_KEYS = ("scenario", "actors", "initial_state", "draw")

_NOTES_PAIR_RE = re.compile(r"(\w+)\s*=\s*([^;,]+)")


def _load_json_safe(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def parse_filter(spec: str) -> tuple[str, str]:
    """Parse a ``KEY=VALUE`` filter specification.

    Raises:
        ValueError: If the spec has no ``=``, an empty key, or an empty value.
    """
    if "=" not in spec:
        raise ValueError(
            f"Invalid --filter '{spec}': expected KEY=VALUE (for example 'arm=fast')"
        )
    key, value = spec.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        raise ValueError(f"Invalid --filter '{spec}': empty key")
    if not value:
        raise ValueError(f"Invalid --filter '{spec}': empty value")
    return key, value


def load_run_config(run_dir: Path) -> dict[str, Any]:
    """Return a run's config.json as a dict (empty when missing or unreadable)."""
    config = _load_json_safe(run_dir / "config.json")
    return config if isinstance(config, dict) else {}


def initial_state_pairs(config: dict[str, Any]) -> dict[str, str]:
    """Extract the ``key=value`` pairs from initial_state.notes.

    Notes look like ``"arm=fast; draw=018; regime fixed for the whole run"``.
    Free text without an ``=`` is ignored.
    """
    initial_state = config.get("initial_state")
    if not isinstance(initial_state, dict):
        return {}
    notes = initial_state.get("notes")
    if not isinstance(notes, str):
        return {}
    pairs: dict[str, str] = {}
    for match in _NOTES_PAIR_RE.finditer(notes):
        pairs[match.group(1)] = match.group(2).strip()
    return pairs


def draw_source(config: dict[str, Any]) -> str | None:
    """Return the recorded initial-state source path, if any."""
    initial_state = config.get("initial_state")
    if isinstance(initial_state, dict) and isinstance(initial_state.get("source"), str):
        return initial_state["source"]
    return None


def cohort_value(config: dict[str, Any], key: str) -> str | None:
    """Resolve one run's value for a cohort key.

    Resolution order:
      1. ``scenario`` – the scenario name from config.json
      2. ``actors`` – sorted actor ids joined with ","
      3. any ``key=value`` pair from initial_state.notes
      4. ``initial_state`` – the draw's directory name from source
      5. ``draw`` – the notes pair, else the draw file stem

    Returns None when the run carries no value for the key.
    """
    if key == "scenario":
        name = config.get("name")
        return name.strip() if isinstance(name, str) and name.strip() else None

    if key == "actors":
        actors = config.get("actors")
        if isinstance(actors, list) and actors:
            return ",".join(sorted(str(a) for a in actors))
        return None

    pairs = initial_state_pairs(config)
    if key in pairs:
        return pairs[key]

    source = draw_source(config)
    if key == "initial_state":
        if source:
            parent = Path(source).parent.name
            return parent if parent and parent != "." else None
        return None

    if key == "draw":
        if "draw" in pairs:
            return pairs["draw"]
        if source:
            return Path(source).stem
        return None

    return None


def available_cohort_keys(run_dirs: list[Path]) -> dict[str, list[str]]:
    """Map each resolvable cohort key to its distinct values across runs.

    Used for error messages when a requested key matches nothing.
    """
    found: dict[str, set[str]] = {}
    for run_dir in run_dirs:
        config = load_run_config(run_dir)
        for key in [*BUILTIN_KEYS, *initial_state_pairs(config)]:
            value = cohort_value(config, key)
            if value is not None:
                found.setdefault(key, set()).add(value)
    return {key: sorted(values) for key, values in sorted(found.items())}


def apply_filters(
    run_dirs: list[Path],
    filters: list[tuple[str, str]] | None,
) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Restrict runs to those matching every filter.

    Returns (kept, excluded_with_reason). A run is excluded when its value for
    a filtered key is missing outright or differs from the requested value.
    """
    if not filters:
        return list(run_dirs), []

    kept: list[Path] = []
    excluded: list[tuple[Path, str]] = []
    for run_dir in run_dirs:
        config = load_run_config(run_dir)
        reason: str | None = None
        for key, expected in filters:
            actual = cohort_value(config, key)
            if actual is None:
                reason = f"no '{key}' in run metadata"
                break
            if actual != expected:
                reason = f"{key}={actual}"
                break
        if reason is None:
            kept.append(run_dir)
        else:
            excluded.append((run_dir, reason))
    return kept, excluded


def partition_runs(
    run_dirs: list[Path],
    key: str,
) -> list[tuple[str, list[Path]]]:
    """Group runs by their value for a cohort key.

    Runs lacking the key land in a single ``(unknown)`` bucket, sorted last;
    real values sort alphabetically so group order is deterministic.
    """
    groups: dict[str, list[Path]] = {}
    for run_dir in run_dirs:
        value = cohort_value(load_run_config(run_dir), key) or UNKNOWN_GROUP
        groups.setdefault(value, []).append(run_dir)

    def sort_key(item: tuple[str, list[Path]]) -> tuple[int, str]:
        return (1 if item[0] == UNKNOWN_GROUP else 0, item[0])

    return sorted(groups.items(), key=sort_key)


def mixed_scenario_warning(run_dirs: list[Path]) -> str | None:
    """Describe mixed scenario identities in a run population, if present.

    Variant runs share the base scenario's ``runs/`` directory, so an
    unfiltered population can silently mix conditions. Returns None when every
    run carries the same identity (name + actors).
    """
    identities: dict[str, int] = {}
    for run_dir in run_dirs:
        config = load_run_config(run_dir)
        name = cohort_value(config, "scenario") or UNKNOWN_GROUP
        actors = cohort_value(config, "actors") or UNKNOWN_GROUP
        identities[f"{name} [{actors}]"] = identities.get(f"{name} [{actors}]", 0) + 1

    if len(identities) <= 1:
        return None

    parts = ", ".join(f"'{identity}' ({count})" for identity, count in sorted(identities.items()))
    return (
        f"Runs carry different scenario identities: {parts}. Pooled statistics mix "
        "these populations. Use --filter scenario=<name> (and/or actors=<ids>) to "
        "restrict the analysis to one."
    )


def between_group_stats(
    groups: list[tuple[str, list[Path]]],
) -> dict[str, Any]:
    """Compute compact per-cohort statistics for comparison prompts/reports.

    Returns final-metric means per cohort (from summary.json) and event
    occurrence rates per cohort (from per-turn 1-events.json artifacts, which
    also cover repeatable events).
    """
    metric_sums: dict[str, dict[str, float]] = {}
    metric_counts: dict[str, dict[str, int]] = {}
    event_counts: dict[str, dict[str, int]] = {}

    for value, dirs in groups:
        for run_dir in dirs:
            summary = _load_json_safe(run_dir / "summary.json") or {}
            finals = summary.get("final_metrics")
            if isinstance(finals, dict):
                for mid, val in finals.items():
                    if isinstance(val, (int, float)):
                        bucket = metric_sums.setdefault(mid, {})
                        bucket[value] = bucket.get(value, 0.0) + float(val)
                        metric_counts.setdefault(mid, {})
                        metric_counts[mid][value] = metric_counts[mid].get(value, 0) + 1

            events_in_run: set[str] = set()
            for turn_dir in sorted(run_dir.iterdir()):
                if not turn_dir.is_dir() or not turn_dir.name.startswith("turn-"):
                    continue
                events = _load_json_safe(turn_dir / "1-events.json")
                if isinstance(events, list):
                    for item in events:
                        if isinstance(item, dict) and isinstance(item.get("id"), str):
                            events_in_run.add(item["id"])
            for eid in events_in_run:
                counts = event_counts.setdefault(eid, {})
                counts[value] = counts.get(value, 0) + 1

    final_metrics: dict[str, dict[str, float]] = {}
    for mid, sums in metric_sums.items():
        final_metrics[mid] = {
            value: round(sums[value] / metric_counts[mid][value], 2) for value in sums
        }

    event_rates: dict[str, dict[str, float]] = {}
    for eid, counts in event_counts.items():
        rates = {
            value: round(counts.get(value, 0) / len(dirs), 2) for value, dirs in groups
        }
        event_rates[eid] = rates

    return {
        "groups": [{"cohort": value, "n_runs": len(dirs)} for value, dirs in groups],
        "final_metrics_mean": final_metrics,
        "event_occurrence_rate": event_rates,
    }
