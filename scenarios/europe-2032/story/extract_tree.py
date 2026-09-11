"""Scaffold `story/tree/` from the story tree and the runs behind it.

The story is written by hand; the numbers in it are not. This script builds one
directory per story node and writes the machine part of it — `data.json`, pulled
straight out of the path run's artifacts — so no metric value, event id or
portfolio state is ever retyped into prose. `story/check_tree.py` then verifies
the prose against these files.

It also scaffolds the prose file itself, so a writer starts from the verified
stage summary rather than a blank page:

- turn nodes get `narrative.md`, seeded with that turn's paragraph from
  `story/stage-N/<block>.md`
- choice nodes get `choice.md`, seeded from the pool sample the option was
  drawn from

Scaffolding is idempotent and never overwrites work: a prose file whose front
matter says `status: written` is left alone, and so is any file whose body has
been edited away from the scaffold. `data.json` is always rewritten — it is
derived, and the runs are immutable.

Usage:
    python scenarios/europe-2032/story/extract_tree.py
    python scenarios/europe-2032/story/extract_tree.py --block A11
    python scenarios/europe-2032/story/extract_tree.py --check   # write nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

STORY = Path(__file__).resolve().parent
SCENARIO = STORY.parent
REPO = SCENARIO.parents[1]
RUNS = SCENARIO / "runs"
TREE = STORY / "tree"

sys.path.insert(0, str(REPO / "scripts"))
from build_dashboard import (  # noqa: E402
    Catalogue,
    metric_definitions,
    parse_actor_turn,
    scenario_event_text,
    section,
)

SCAFFOLD_NOTE = "<!-- scaffold: rewrite this, then set status: written -->"

# The reader lives in calendar time, not in turns. Every node carries the prose
# form of its own date, and every portfolio measure carries the date it lands,
# so no writer has to convert a turn number by hand.
US_ELECTIONS = {
    "election_consolidation": "consolidation — AI held as a strategic asset, "
                              "access to allies rationed from Washington",
    "election_alliance": "alliance — structured access for allied governments "
                         "on published terms, priced in alignment",
    "election_retrenchment": "retrenchment — the backlash wins and Washington "
                             "turns inward, slower and preoccupied",
}


def period_prose(turn: int) -> str:
    half = "first" if turn % 2 == 0 else "second"
    year = 2026 + turn // 2
    return f"the {half} half of {year}"

# metrics.md heads each metric with its bare id, so a reader-facing name has to
# come from somewhere. This is that somewhere.
METRIC_LABELS = {
    "ai_capability": "AI capability",
    "openweight_capability": "Open-weight capability",
    "ai_safety": "AI safety",
    "resilience": "Resilience",
    "eu_ai_sovereignty": "EU AI sovereignty",
    "eu_political_capital": "EU political capital",
    "public_sentiment": "Public sentiment",
}


def scenario_events(scenario_dir: Path) -> dict[str, dict[str, str]]:
    """Each event's heading and its **Description:** body, keyed by id.

    `scenario_event_text` in the dashboard returns only the heading, which
    reads as a bare label on a reader-facing page. The description is the
    sentence that says what actually happened.
    """
    path = scenario_dir / "events.md"
    if not path.is_file():
        return {}
    out: dict[str, dict[str, str]] = {}
    for block in re.split(r"^##\s+", path.read_text(encoding="utf-8"), flags=re.M)[1:]:
        head, _, body = block.partition("\n")
        mid = re.search(r"^\**ID:\**\s*`?([a-z0-9_]+)`?", body, re.M | re.I)
        if not mid:
            continue
        desc = re.search(r"^\*\*Description:\*\*\s*(.+?)(?=\n\*\*|\n##|\Z)",
                         body, re.M | re.S)
        out[mid.group(1)] = {
            "title": head.strip(),
            "description": desc.group(1).strip() if desc else "",
        }
    return out


def load_tree() -> dict[str, Any]:
    return json.loads((STORY / "tree.json").read_text(encoding="utf-8"))


def front_matter(text: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def stage_paragraphs(block: str, stage: int) -> dict[int, str]:
    """That block's per-turn paragraphs from the verified stage prose."""
    path = STORY / f"stage-{stage}" / f"{block}.md"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    out: dict[int, str] = {}
    parts = re.split(r"^\*\*Turn (\d+) \(", text, flags=re.M)
    for i in range(1, len(parts) - 1, 2):
        turn = int(parts[i])
        body = "**Turn " + parts[i] + " (" + parts[i + 1]
        out[turn] = body.strip()
    return out


def commitment_of(actor_text: str) -> str | None:
    body = section(actor_text, "Two-year commitment")
    return body.strip() or None if body else None


def commitment_from_statements(tdir: Path) -> str | None:
    """The live two-year commitment from the statements ledger.

    Under framework custody the actor writes the commitment only when it
    changes it, so most turn responses carry no commitment section. The
    ledger always does. Falls back to None only if the file is absent.
    """
    for name in ("2-actors/eu-statements.md",):
        path = tdir / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^- `two_year_commitment` \(commitment\):\s*(.+)$", line.strip())
            if m:
                return m.group(1).strip()
    return None


def portfolio_status(measure: dict[str, Any], turn: int) -> str:
    if measure.get("finished"):
        return "finished"
    if measure.get("start") == turn:
        return "new"
    return "running"


def read_turn(run_dir: Path, turn: int, catalogue: Catalogue,
              catalogue_text: dict[str, str], metrics_meta: dict[str, dict],
              events_meta: dict[str, dict[str, str]]) -> dict[str, Any]:
    tdir = run_dir / f"turn-{turn:02d}"
    prev = run_dir / f"turn-{turn - 1:02d}" / "4-metrics.json"
    metrics = json.loads((tdir / "4-metrics.json").read_text(encoding="utf-8"))
    previous = json.loads(prev.read_text(encoding="utf-8")) if prev.is_file() else {}

    out_metrics = {}
    for mid, value in metrics.items():
        was = previous.get(mid)
        meta = metrics_meta.get(mid, {})
        out_metrics[mid] = {
            "label": METRIC_LABELS.get(mid, mid),
            "value": value,
            "previous": was,
            "delta": round(value - was, 2) if isinstance(was, (int, float)) else None,
            "min": meta.get("min"),
            "max": meta.get("max"),
        }

    described = {}
    ev_path = tdir / "1-events.json"
    if ev_path.is_file():
        for event in json.loads(ev_path.read_text(encoding="utf-8")):
            described[event["id"]] = event
    events = []
    ev_eval = tdir / "1-event-evaluations.json"
    if ev_eval.is_file():
        for evaluation in json.loads(ev_eval.read_text(encoding="utf-8")):
            if not evaluation.get("triggered"):
                continue
            merged = {**described.get(evaluation["id"], {}), **evaluation}
            eid = catalogue.note(merged, catalogue_text)
            defined = events_meta.get(eid, {})
            # Emergent events exist only in the run record; catalogued ones take
            # their text from events.md, where the full description lives.
            description = defined.get("description") or (merged.get("description") or "").strip()
            events.append({
                "id": eid,
                "title": defined.get("title") or eid,
                "description": description,
                "emergent": bool(merged.get("emergent")),
                "pinned": bool(merged.get("pinned")),
            })

    actor_path = tdir / "2-actors" / "eu.md"
    actor = parse_actor_turn(actor_path)
    actor_text = actor_path.read_text(encoding="utf-8") if actor_path.is_file() else ""
    commitment = commitment_of(actor_text) or commitment_from_statements(tdir)
    portfolio = [{**m, "status": portfolio_status(m, turn),
                   "finish_period": period_prose(m["finish"]) if m.get("finish") else None,
                   "start_period": period_prose(m["start"]) if m.get("start") else None}
                  for m in actor["portfolio"]]

    return {
        "metrics": out_metrics,
        "events": events,
        "portfolio": portfolio,
        "cancelled": actor["cancelled"],
        "new_measure": actor["new_measure"],
        "priority": actor["priority"],
        "commitment": commitment,
    }


RECORD_NOTE = ("<!-- record: machine-extracted from the run, always rewritten. "
               "Never edit by hand, never quote figures from anywhere else. -->")


def write_record(node: Path, body: str, check: bool) -> None:
    """Write the artifact layer. Always rewritten, like data.json."""
    if not check:
        (node / "record.md").write_text(RECORD_NOTE + "\n\n" + body,
                                        encoding="utf-8")


def turn_record(run_dir: Path, turn: int) -> str:
    """The full simulation record behind one turn node for the writer.

    data.json carries the figures; this carries the words they came from --
    the actor's response, the world state, and the Game Master's notepad
    with its charge line. A prose writer works from here, not from summaries.
    """
    tdir = run_dir / f"turn-{turn:02d}"
    parts = [f"Source: `{tdir.relative_to(REPO)}`. Figures live in `data.json`; "
             f"do not retype them from below, cross-check against it."]
    for title, rel in (("Actor response (EU)", "2-actors/eu.md"),
                       ("World state", "4-world-state.md"),
                       ("Game-master notepad", "5-notepad.md")):
        path = tdir / rel
        text = path.read_text(encoding="utf-8").strip() if path.is_file() else "(missing)"
        parts.append(f"## {title}\n\n{text}")
    return "\n\n".join(parts) + "\n"


def write_prose(path: Path, body: str, meta: dict[str, str], check: bool) -> str:
    """Write a scaffold unless the file exists and has been worked on."""
    if path.is_file():
        existing = path.read_text(encoding="utf-8")
        fm = front_matter(existing)
        if fm.get("status") == "written" or SCAFFOLD_NOTE not in existing:
            return "kept"
    head = "---\n" + "\n".join(f"{k}: {v}" for k, v in meta.items()) + "\n---\n\n"
    if not check:
        path.write_text(head + body, encoding="utf-8")
    return "scaffolded"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--block", help="only this block (e.g. A11)")
    ap.add_argument("--check", action="store_true", help="report, write nothing")
    args = ap.parse_args()

    tree = load_tree()
    catalogue = Catalogue()
    catalogue_text = scenario_event_text(SCENARIO)
    events_meta = scenario_events(SCENARIO)
    metrics_meta = {m["id"]: m for m in metric_definitions(SCENARIO)}
    periods = tree["turn_periods"]
    blocks = {b["block"]: b for b in tree["blocks"]}

    def situation_of(block_id: str, turn: int) -> list[dict[str, Any]]:
        run = RUNS / blocks[block_id]["run"] / f"turn-{turn:02d}"
        described = {}
        ev = run / "1-events.json"
        if ev.is_file():
            for e in json.loads(ev.read_text(encoding="utf-8")):
                described[e["id"]] = e
        out = []
        evals = run / "1-event-evaluations.json"
        if evals.is_file():
            for e in json.loads(evals.read_text(encoding="utf-8")):
                if not e.get("triggered"):
                    continue
                merged = {**described.get(e["id"], {}), **e}
                defined = events_meta.get(e["id"], {})
                out.append({
                    "id": e["id"],
                    "title": defined.get("title") or e["id"],
                    "description": (defined.get("description")
                                    or (merged.get("description") or "").strip()),
                    "emergent": bool(merged.get("emergent")),
                })
        return out

    def us_election(block_id: str) -> dict[str, Any] | None:
        """The 2028 result, read from the stage-1 ancestor's turn 5.

        The posture stands from 2029 onward, so every block below that turn
        inherits it; a reader who is told the result must keep being told what
        follows from it.
        """
        root = block_id[:2]
        run = RUNS / blocks[root]["run"] / "turn-05" / "1-event-evaluations.json"
        if not run.is_file():
            return None
        for e in json.loads(run.read_text(encoding="utf-8")):
            if e.get("triggered") and e["id"] in US_ELECTIONS:
                return {"id": e["id"], "reading": US_ELECTIONS[e["id"]],
                        "decided": period_prose(5)}
        return None
    choice_after = {c["after_block"]: c for c in tree["choices"]}

    if not args.check:
        TREE.mkdir(exist_ok=True)

    tally = {"scaffolded": 0, "kept": 0, "data": 0}

    # --- the shared opening ---------------------------------------------------
    if not args.block:
        node = TREE / "turn-01"
        if not args.check:
            node.mkdir(exist_ok=True)
        opening = tree["opening"]
        events_meta = scenario_events(SCENARIO)
        start_metrics = {
            m["id"]: {"label": METRIC_LABELS.get(m["id"], m["id"]),
                      "value": m["start"], "previous": None,
                      "delta": None, "min": m["min"], "max": m["max"]}
            for m in metric_definitions(SCENARIO)
        }
        # Turn 1's inherited portfolio is the same in both option files.
        opt1 = (STORY / opening["options"][0]["file"]).read_text(encoding="utf-8")
        inherited = parse_actor_turn(STORY / opening["options"][0]["file"])["portfolio"]
        eid = opening["pinned_event"]
        data = {
            "node": "turn-01", "turn": 1, "period": periods["1"],
            "period_prose": period_prose(1), "block": None,
            "arm": None, "stage": 0, "us_election": None,
            "provenance": {"pinned_event": eid, "pin_runs": opening["pin_runs"],
                           "note": "The opening is arm-independent: it shows the "
                                   "scenario's start values, not a resolved turn. "
                                   "Turn 1 resolves differently per arm, which the "
                                   "reader sees at turn 2."},
            "metrics": start_metrics,
            "events": [{"id": eid,
                        "title": events_meta.get(eid, {}).get("title", eid),
                        "description": events_meta.get(eid, {}).get("description", ""),
                        "emergent": False, "pinned": True}],
            "portfolio": [{**m, "status": "running"} for m in inherited],
            "cancelled": [], "new_measure": None, "priority": None,
            "commitment": None,
            "prev_node": None, "next_node": None,
            "next_choice": [o["node"] for o in opening["options"]],
            "alternatives": {},
        }
        if not args.check:
            (node / "data.json").write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            opt_texts = []
            for o in opening["options"]:
                src = (STORY / o["file"]).read_text(encoding="utf-8").strip()
                opt_texts.append(f"## {o['node']} ({o['file']})\n\n{src}")
            write_record(node,
                         f"Shared frame: `turn-01/opening.md`. Both options below "
                         f"are verbatim draws; turn 1 resolves per arm.\n\n" +
                         "\n\n".join(opt_texts) + "\n",
                         args.check)
        tally["data"] += 1
        body = (f"{SCAFFOLD_NOTE}\n\nSee [`../../turn-01/opening.md`](../../turn-01/opening.md) "
                f"for what is fixed here.\n")
        tally[write_prose(node / "narrative.md", body,
                          {"node": "turn-01", "turn": "1", "period": periods["1"],
                           "status": "drafted", "prev": "", "next": "option-02-1, option-02-2"},
                          args.check)] += 1

    # --- turn nodes -----------------------------------------------------------
    for block in tree["blocks"]:
        if args.block and block["block"] != args.block:
            continue
        run_dir = RUNS / block["run"]
        paragraphs = stage_paragraphs(block["block"], block["stage"])
        turns = block["turns"]
        for turn in turns:
            name = f"turn-{turn:02d}-{block['block']}"
            node = TREE / name
            if not args.check:
                node.mkdir(exist_ok=True)
            core = read_turn(run_dir, turn, catalogue, catalogue_text, metrics_meta,
                             events_meta)

            if turn == turns[0]:
                prev = (f"turn-{turn - 1:02d}-{block['parent_block']}"
                        if block["parent_block"] else "turn-01")
                prev = block["option_node"]
            else:
                prev = f"turn-{turn - 1:02d}-{block['block']}"
            if turn != turns[-1]:
                nxt, nxt_choice = f"turn-{turn + 1:02d}-{block['block']}", None
            else:
                choice = choice_after.get(block["block"])
                nxt = None
                nxt_choice = [o["node"] for o in choice["options"]] if choice else None

            data = {
                "node": name, "turn": turn, "period": periods[str(turn)],
                "period_prose": period_prose(turn),
                "block": block["block"], "arm": block["arm"], "stage": block["stage"],
                "us_election": us_election(block["block"]) if turn >= 5 else None,
                "provenance": {"run": block["run"], "seed": block["seed"],
                               "turn_dir": f"runs/{block['run']}/turn-{turn:02d}",
                               "pinned_turn": block["pinned_turn"],
                               "option_file": block["option_file"],
                               "path_rep": block["path_rep"],
                               "promotion_reason": block["promotion_reason"]},
                **core,
                "prev_node": prev, "next_node": nxt, "next_choice": nxt_choice,
                "alternatives": {},
            }
            if not args.check:
                (node / "data.json").write_text(
                    json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                write_record(node, turn_record(run_dir, turn), args.check)
            tally["data"] += 1

            draft = paragraphs.get(turn, "")
            if draft:
                body = f"{SCAFFOLD_NOTE}\n\n{draft}\n"
            else:
                body = (f"{SCAFFOLD_NOTE}\n\nWrite from `record.md` (the "
                        f"simulation record) with figures from `data.json`. "
                        f"Rules in `story/README.md`.\n")
            tally[write_prose(node / "narrative.md", body,
                              {"node": name, "turn": str(turn),
                               "period": periods[str(turn)], "block": block["block"],
                               "status": "drafted", "prev": prev,
                               "next": nxt or ", ".join(nxt_choice or [])},
                              args.check)] += 1

    # --- choice nodes ---------------------------------------------------------
    for choice in tree["choices"]:
        for opt in choice["options"]:
            leads = opt["leads_to_block"]
            leads_list = leads if isinstance(leads, list) else [leads]
            if args.block and args.block not in leads_list:
                continue
            node = TREE / opt["node"]
            if not args.check:
                node.mkdir(exist_ok=True)
            if choice["after_block"] == "turn-01":
                src = STORY / [o for o in tree["opening"]["options"]
                               if o["node"] == opt["node"]][0]["file"]
                prev = "turn-01"
            else:
                # An option from an extension pool carries its own `pool`.
                src = STORY / opt.get("pool", choice["pool"]) / f"{opt['sample']}.md"
                prev = f"turn-{choice['choice_turn'] - 1:02d}-{choice['after_block']}"
            src_text = src.read_text(encoding="utf-8")
            data = {
                "node": opt["node"], "choice_turn": choice["choice_turn"],
                "after_block": choice["after_block"],
                "leads_to_block": leads_list,
                "source": str(src.relative_to(STORY)),
                "pool": opt.get("pool", choice["pool"]), "draws": choice["draws"],
                "split": choice["split"], "split_note": choice["note"],
                "stance": opt["stance"], "standing": opt["standing"],
                "support": opt["support"],
                # The options were drawn against a fixed situation: the events
                # pinned in the turn they lead into. The reader has to be told
                # what has happened before choosing how to answer it, so the
                # situation belongs to the choice, shared by both options.
                "situation": situation_of(leads_list[0], choice["choice_turn"]),
                "period_prose": period_prose(choice["choice_turn"]),
                "finishes_period": (period_prose(opt["finishes_turn"])
                                    if opt["finishes_turn"] else None),
                "measure": opt["measure"], "category": opt["category"],
                "finishes_turn": opt["finishes_turn"],
                "commitment": commitment_of(src_text),
                "prev_node": prev,
                "next_node": [f"turn-{choice['choice_turn']:02d}-{b}" for b in leads_list],
                "alternatives": {},
            }
            if not args.check:
                (node / "data.json").write_text(
                    json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                sit = "\n".join(f"- **{e['id']}** ({e['title']}): {e['description']}"
                                for e in data["situation"]) or "(no events pinned)"
                write_record(node,
                             f"Source option: `{data['source']}` "
                             f"(verbatim draw; the reader's choice text is written from it).\n\n"
                             f"## Option response (full)\n\n{src_text.strip()}\n\n"
                             f"## Situation (events pinned in the turn this choice leads into)\n\n{sit}\n",
                             args.check)
            tally["data"] += 1
            measure = opt["measure"] or "no new measure"
            body = (f"{SCAFFOLD_NOTE}\n"
                    f"<!-- stance: {opt['stance']} | source: {data['source']} "
                    f"| {opt['standing']}, {opt['support']} -->\n\n"
                    f"**{measure}**\n\n"
                    f"{section(src_text, 'New measure') or '(no new measure)'}\n")
            tally[write_prose(node / "choice.md", body,
                              {"node": opt["node"], "choice_turn": str(choice["choice_turn"]),
                               "status": "drafted", "prev": prev,
                               "next": ", ".join(data["next_node"])},
                              args.check)] += 1

    verb = "would write" if args.check else "wrote"
    print(f"{verb} {tally['data']} data.json; "
          f"{tally['scaffolded']} prose scaffolds, {tally['kept']} kept as written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
