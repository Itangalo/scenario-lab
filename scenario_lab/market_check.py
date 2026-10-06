"""Compare the Game Master's turn-1 event pricing against market anchors.

The planned first test for market anchors: for every event carrying a
``**Metaculus:**`` snapshot, set the snapshotted community figure beside the
probability the events step actually evaluated on turn 1. No API calls --
both sides are read from persisted artifacts. A gap is a question, not a
verdict: market odds are unconditional on the world and tied to a resolution
date, while the Game Master prices the event conditional on the simulated
state for one turn. Persistent overpricing against the market usually means
the event prose invites it; persistent underpricing, that the market knows
something the catalogue does not.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


def _parse_percent(figure: str) -> Optional[float]:
    try:
        return float(figure.rstrip("%").strip()) / 100.0
    except (ValueError, AttributeError):
        return None


def market_check(run_dir: Path) -> dict[str, Any]:
    """Compare turn-1 evaluated probabilities with snapshotted market figures.

    Returns ``{"comparisons": [...], "warnings": [...]}`` where each
    comparison holds the event id, the market figure (0-1), its retrieval
    date and URL, and the Game Master's turn-1 evaluated probability (or
    None when the events step never listed the event -- itself a finding).
    """
    from .resume import get_scenario_source_from_run
    from .loader import load_scenario

    run_dir = Path(run_dir)
    warnings: list[str] = []
    try:
        evaluations = json.loads(
            (run_dir / "turn-01" / "1-event-evaluations.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        return {"comparisons": [], "warnings": [f"cannot read turn-1 evaluations: {exc}"]}
    if not isinstance(evaluations, list):
        return {"comparisons": [], "warnings": ["turn-1 evaluations are not a list"]}

    gm: dict[str, float] = {}
    for entry in evaluations:
        if not isinstance(entry, dict) or entry.get("skipped"):
            continue
        event_id = entry.get("id")
        probability = entry.get("probability")
        if isinstance(event_id, str) and isinstance(probability, (int, float)):
            gm[event_id] = float(probability)

    try:
        scenario = load_scenario(get_scenario_source_from_run(run_dir))
    except ValueError as exc:
        return {"comparisons": [], "warnings": [str(exc)]}

    comparisons = []
    for event in scenario.events:
        if not event.metaculus_url:
            continue
        market = _parse_percent(event.metaculus_probability)
        if market is None:
            warnings.append(
                f"Event '{event.id}' has a Metaculus URL but no parseable "
                "community figure; record one to compare against"
            )
            continue
        gm_probability = gm.get(event.id)
        if gm_probability is None:
            warnings.append(
                f"Event '{event.id}' was never listed by the events step on "
                "turn 1, so there is no Game Master figure to compare"
            )
        comparisons.append(
            {
                "id": event.id,
                "market": market,
                "market_retrieved": event.metaculus_retrieved,
                "market_url": event.metaculus_url,
                "gm_turn_1": gm_probability,
                "gap": (
                    round(gm_probability - market, 4)
                    if gm_probability is not None
                    else None
                ),
            }
        )
    if not comparisons:
        warnings.append("No anchored events found in this scenario")
    return {"comparisons": comparisons, "warnings": warnings}


def format_market_check(report: dict[str, Any]) -> str:
    """Render a market-check report as human-readable text."""
    lines = ["MARKET CHECK (turn-1 Game Master pricing vs snapshots)", ""]
    for entry in report["comparisons"]:
        gm = "not listed" if entry["gm_turn_1"] is None else f"{entry['gm_turn_1']:.0%}"
        gap = "" if entry["gap"] is None else f" (gap {entry['gap']:+.0%})"
        lines.append(
            f"- {entry['id']}: market {entry['market']:.0%} "
            f"(retrieved {entry['market_retrieved'] or 'unknown'}) vs GM {gm}{gap}"
        )
    if report["warnings"]:
        lines += ["", "Warnings:"]
        lines.extend(f"- {warning}" for warning in report["warnings"])
    return "\n".join(lines) + "\n"
