"""Aggregate the comparison statistics behind the story reader's compare popup.

For every written turn node the popup shows two things, both derived and never
edited by hand:

1. Sibling events -- what fired in the block's other repetitions of this turn.
   Common events (in at least COMMON_OF siblings) are listed first with counts,
   then notable ones fill up to BOX_CAP entries. Catastrophes always make it.
2. Corpus percentiles -- where this turn's metric values stand against the
   same turn across the full-run reference corpus (arm-blind by design: the
   page never names arms or counts per arm).

Usage:
    python scenarios/europe-2032/story/build_compare.py
    python scenarios/europe-2032/story/build_compare.py --check   # report, write nothing
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path
from typing import Any

STORY = Path(__file__).resolve().parent
SCENARIO = STORY.parent
RUNS = SCENARIO / "runs"
TREE = STORY / "tree"

sys.path.insert(0, str(STORY))
from extract_tree import METRIC_LABELS, scenario_events  # noqa: E402

# Common means firing in at least this many of the 9 siblings. Measured 94%
# hit rate across a 36-turn sample of all stages and arms (bar was 50%).
COMMON_OF = 3
# The box lists common events first, then notable ones fill up to this many.
BOX_CAP = 6

CATASTROPHIC = {
    "catastrophic_great_power_conflict",
    "catastrophic_loss_of_control_incident",
    "catastrophic_bio_incident",
}

# Catalogue events rare enough per turn and load-bearing enough to always be
# worth a reader's attention at a single occurrence. Judgement call, reviewed
# against the sibling distribution (each fires in only a low dozens of the
# 1,512 sibling turn-slots, and each changes what the Union can do next).
WATCHLIST = [
    "rsi_onset",
    "taiwan_blockade",
    "us_labs_nationalised",
    "washington_takes_labs",
    "frontier_access_denied",
    "eu_frontier_access_denied",
]

# Near-duplicate emergent events: at most one per family per turn. Ordered
# most telling first, so the survivor is the representative, not the residue.
DUP_FAMILIES: list[list[str]] = [
    ["emergent_siting_backlash_freeze", "emergent_siting_blockade_pause",
     "emergent_siting_blockade_wave", "emergent_siting_backlash"],
    ["emergent_anti_datacentre_sabotage", "emergent_anti_infrastructure_sabotage",
     "emergent_anti_ai_sabotage_wave", "emergent_site_sabotage_escalation"],
    ["emergent_grid_forensics_leak", "emergent_grid_toolkit_leak",
     "emergent_grid_forensics_fallout", "emergent_grid_forensics_disclosure"],
    ["emergent_cyber_insurance_crunch", "emergent_utility_insurance_crunch",
     "emergent_cyber_insurance_repricing", "emergent_municipal_insurance_retreat",
     "emergent_ot_insurance_pullback", "emergent_insurer_market_exit",
     "emergent_grid_insurance_crunch"],
    ["emergent_datacentre_backlash", "emergent_energy_backlash_blocks",
     "emergent_datacentre_siting_freeze", "emergent_energy_siting_backlash",
     "emergent_grid_siting_backlash"],
    ["emergent_gigafactory_siting_backlash", "emergent_gigafactory_siting_block",
     "emergent_gigafactory_siting_blockade", "emergent_siting_backlash"],
]

# Emergent events read cold, so the ranking decides what fills scarce slots:
# sabotage and strikes first, then proliferation and geopolitical offers,
# then revelations, then the insurance micro-variants last.
EMERGENT_RANK = [
    "emergent_infrastructure_sabotage_wave",
    "emergent_care_substitution_strike",
    "emergent_fallback_sabotage",
    "emergent_ics_toolkit_proliferation",
    "emergent_swarm_toolkit_proliferation",
    "emergent_gulf_compute_offer",
    "emergent_synthesis_screening_crisis",
    "emergent_opaque_agent_proliferation",
    "emergent_neutral_data_sanctuary_bid",
    "emergent_pathogen_escape_variant",
]


def first_sentence(text: str) -> str:
    """One reader-facing sentence. Catalogue and run prose both open with the
    summary sentence, so truncation is extraction, not rewriting."""
    text = re.sub(r"`([^`]+)`", r"\1", (text or "").strip())
    text = re.sub(r"\s+", " ", text)
    m = re.match(r"(.+?[.!?])(?:\s|$)", text)
    return (m.group(1) if m else text[:220]).strip()


def pretty_title(event_id: str) -> str:
    return re.sub(r"^emergent_", "", event_id).replace("_", " ").capitalize()


def load_tree() -> dict[str, Any]:
    return json.loads((STORY / "tree.json").read_text(encoding="utf-8"))


def block_reps() -> dict[str, list[str]]:
    """All ten run dirs per story block, rep 1 first."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for name in ("stage-1-blocks-rerun.json", "stage-2-blocks-rerun.json",
                 "stage-3-blocks-rerun.json"):
        for e in json.loads((STORY / name).read_text(encoding="utf-8")):
            grouped.setdefault(e["path"], []).append(e)
    return {path: [e["dir"] for e in sorted(es, key=lambda e: e["rep"])]
            for path, es in grouped.items()}


def turn_events(run_dir: str, turn: int) -> list[dict[str, Any]]:
    """Triggered events with their pinned flag and run-record description."""
    tdir = RUNS / run_dir / f"turn-{turn:02d}"
    described = {}
    ev_path = tdir / "1-events.json"
    if ev_path.is_file():
        for e in json.loads(ev_path.read_text(encoding="utf-8")):
            described[e["id"]] = e
    out = []
    eval_path = tdir / "1-event-evaluations.json"
    if eval_path.is_file():
        for e in json.loads(eval_path.read_text(encoding="utf-8")):
            if e.get("triggered"):
                merged = {**described.get(e["id"], {}), **e}
                out.append({"id": e["id"], "emergent": bool(merged.get("emergent")),
                            "pinned": bool(merged.get("pinned")),
                            "description": (merged.get("description") or "").strip()})
    return out


def corpus_runs() -> list[str]:
    """Reference corpus: the 2026-09-10 Spark/store scaleup. Each batch log
    records the run dir it launched, which is the provenance grip `config.json`
    no longer carries."""
    out = []
    for log in sorted(glob.glob(str(RUNS / "batch-logs" / "batch-20260910-*.log"))):
        m = re.search(r"Output directory: (run-\S+)", Path(log).read_text(errors="replace"))
        if m:
            out.append(m.group(1).strip())
    return out


def corpus_metrics(runs: list[str], turn: int) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for d in runs:
        p = RUNS / d / f"turn-{turn:02d}" / "4-metrics.json"
        if not p.is_file():
            continue
        for mid, value in json.loads(p.read_text(encoding="utf-8")).items():
            if isinstance(value, (int, float)):
                out.setdefault(mid, []).append(float(value))
    return out


def dedup(notable: list[str]) -> list[str]:
    """One survivor per duplicate family: the first in curated family order."""
    drop: set[str] = set()
    for fams in DUP_FAMILIES:
        in_box = [e for e in fams if e in notable]
        drop.update(in_box[1:])
    return [e for e in notable if e not in drop]


def rank_emergent(ids: list[str]) -> list[str]:
    rank = {eid: i for i, eid in enumerate(EMERGENT_RANK)}
    return sorted(ids, key=lambda e: (rank.get(e, len(rank)), e))


def sibling_box(block: str, turn: int, reps: list[str],
                catalogue: dict[str, dict[str, str]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    info: dict[str, dict[str, Any]] = {}
    for d in reps[1:]:
        for e in turn_events(d, turn):
            counts[e["id"]] = counts.get(e["id"], 0) + 1
            info.setdefault(e["id"], e)
    path_pinned = {e["id"] for e in turn_events(reps[0], turn) if e["pinned"]}

    def entry(eid: str) -> dict[str, Any]:
        e = info[eid]
        title = (catalogue.get(eid, {}).get("title")
                 or (pretty_title(eid) if e["emergent"] else eid))
        desc = (catalogue.get(eid, {}).get("description") or e["description"])
        return {"id": eid, "title": title, "line": first_sentence(desc),
                "of_nine": counts[eid], "emergent": e["emergent"]}

    common = sorted([eid for eid, c in counts.items() if c >= COMMON_OF])
    rest = [eid for eid in counts if eid not in set(common)]
    catastrophic = sorted([e for e in rest if e in CATASTROPHIC])
    watch = [e for e in WATCHLIST if e in rest]
    emergent = rank_emergent([e for e in rest
                              if info[e]["emergent"] and e not in set(catastrophic)])
    emergent = dedup(emergent)
    notable = catastrophic + watch + emergent

    pinned = sorted(path_pinned)
    if pinned:
        # Pinned turns read 9/9 by construction; the pinned set is the story,
        # and only unpinned extras are comparative statistics.
        common = [e for e in common if e not in set(pinned)]
        notable = [e for e in notable if e not in set(pinned)]

    slots = max(0, BOX_CAP - len(common))
    shown_notable = notable[:slots]
    forced = [e for e in catastrophic if e not in shown_notable]
    shown_notable += [e for e in forced if e not in shown_notable]

    return {
        "siblings": len(reps) - 1,
        "pinned": [entry(e) for e in pinned],
        "common": [entry(e) for e in common],
        "notable": [entry(e) for e in shown_notable],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report, write nothing")
    args = ap.parse_args()

    tree = load_tree()
    catalogue = scenario_events(SCENARIO)
    reps = block_reps()
    corpus = corpus_runs()
    corpus_cache: dict[int, dict[str, list[float]]] = {}

    blocks = {b["block"]: b for b in tree["blocks"]}
    written = 0
    for block_id, blk in sorted(blocks.items()):
        for turn in blk["turns"]:
            name = f"turn-{turn:02d}-{block_id}"
            prose = TREE / name / "narrative.md"
            if not prose.is_file():
                continue
            node = json.loads((TREE / name / "data.json").read_text(encoding="utf-8"))
            box = sibling_box(block_id, turn, reps[block_id], catalogue)

            if turn not in corpus_cache:
                corpus_cache[turn] = corpus_metrics(corpus, turn)
            metrics = {}
            for mid, m in (node.get("metrics") or {}).items():
                values = sorted(corpus_cache[turn].get(mid, []))
                higher = sum(1 for v in values if v < m["value"])
                metrics[mid] = {"label": METRIC_LABELS.get(mid, mid),
                                "value": m["value"], "higher_than": higher,
                                "of_runs": len(values)}
            compare = {"node": name, "turn": turn,
                       "period_prose": node.get("period_prose", ""),
                       "events": box,
                       "corpus_runs": len(corpus),
                       "metrics": metrics}
            if not args.check:
                (TREE / name / "compare.json").write_text(
                    json.dumps(compare, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
            written += 1
    verb = "would write" if args.check else "wrote"
    print(f"{verb} {written} compare.json from {len(corpus)} corpus runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
