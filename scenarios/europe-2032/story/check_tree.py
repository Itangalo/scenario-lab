"""Verify the story tree against the runs behind it.

The prose is written by hand and the numbers in it are not, so something has to
hold the two together. This is that something. It checks five things:

1. **Structure** — every node in `tree.json` exists on disk, every prev/next
   link resolves, the graph from `turn-01` reaches exactly 24 endings, and every
   ending is a turn-13 node.
2. **Numbers** — every figure in a `narrative.md` or `choice.md` body occurs
   either in that node's `data.json` or in the run artifacts for that turn.
   A number that appears in neither was invented while writing.
3. **Events** — every catalogued event named in prose fired that turn.
4. **Arm leakage** — no reader-visible text names an arm or carries a branch id.
   The reader must not learn which of the three worlds they are in.
5. **Provenance** — each `data.json` still matches the run on disk, so a
   re-generated run cannot silently orphan the prose written from it.

A wrong instrument looks exactly as authoritative as a right one, so this script
carries its own test: `--self-test` plants a wrong metric, an unfired event and
an arm leak in a temporary copy of one node and fails if the checks do not
catch all three.

Usage:
    python scenarios/europe-2032/story/check_tree.py
    python scenarios/europe-2032/story/check_tree.py --block A11
    python scenarios/europe-2032/story/check_tree.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

STORY = Path(__file__).resolve().parent
SCENARIO = STORY.parent
RUNS = SCENARIO / "runs"

# "Acceleration" also names a measure in this scenario (AI Acceleration Zones),
# so the bare word is not a leak. What leaks is the word used as a label for the
# world the reader is in, which is why the context window matters. The
# hyphenated variant names have no innocent reading and are always flagged.
ARM_WORDS = re.compile(r"\b(Acceleration|Plateau)\b")
ARM_NAMES = re.compile(r"\bVerification[- ]bound(?:ed)?\b", re.I)
ARM_CONTEXT = re.compile(
    r"\b(arm|arms|world|worlds|branch|branches|trajector\w+|scenario|path|paths|"
    r"variant|regime|timeline|track)\b", re.I)
ARM_WINDOW = 60
BRANCH_ID = re.compile(r"\b[AVP][12]{1,3}\b")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
COMMENT = re.compile(r"<!--.*?-->", re.S)
FRONT = re.compile(r"^---\n.*?\n---\n", re.S)


def numbers(text: str) -> set[str]:
    """Numeric literals, normalised so 30, 30.0 and 30,000 compare sensibly."""
    out = set()
    for raw in NUMBER.findall(text):
        cleaned = raw.replace(",", "")
        out.add(cleaned)
        try:
            value = float(cleaned)
        except ValueError:
            continue
        out.add(f"{value:g}")
        if value.is_integer():
            out.add(str(int(value)))
    return out


def body_of(text: str) -> str:
    """Reader-visible text: front matter and HTML comments are not."""
    return COMMENT.sub("", FRONT.sub("", text))


def data_numbers(data: dict[str, Any]) -> set[str]:
    out: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, bool) or value is None:
            return
        if isinstance(value, (int, float)):
            out.update(numbers(str(value)))
        elif isinstance(value, str):
            out.update(numbers(value))
        elif isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)

    walk(data)
    return out


def run_numbers(data: dict[str, Any]) -> set[str]:
    """Every figure the simulation itself wrote for this node.

    For a turn node that is the run's own turn directory. For a choice node it
    is the option file the choice was drawn from, which is equally a thing the
    simulation produced and equally not ours to alter.
    """
    if data.get("source"):
        path = STORY / data["source"]
        return numbers(path.read_text(encoding="utf-8")) if path.is_file() else set()
    prov = data.get("provenance") or {}
    turn_dir = prov.get("turn_dir")
    if not turn_dir:
        # The opening resolves no turn, so its facts come from the scenario's
        # own opening material rather than from a run.
        if data.get("node") == "turn-01":
            out: set[str] = set()
            for name in ("background/context.md", "events.md"):
                path = SCENARIO / name
                if path.is_file():
                    out |= numbers(path.read_text(encoding="utf-8"))
            return out
        return set()
    tdir = SCENARIO / turn_dir
    out: set[str] = set()
    for name in ("2-actors/eu.md", "4-world-state.md", "5-notepad.md",
                 "6-historical-summary.md", "4-metrics.json"):
        path = tdir / name
        if path.is_file():
            out.update(numbers(path.read_text(encoding="utf-8")))
    return out


def fired_through(turn_dir: str | None) -> set[str]:
    """Every event that fired in this run up to and including this turn.

    Prose may refer back to something that happened two years ago; that is not
    an error. Naming an event the run never produced is.
    """
    if not turn_dir:
        return set()
    path = SCENARIO / turn_dir
    run_dir, turn = path.parent, int(path.name.split("-")[1])
    out: set[str] = set()
    for n in range(1, turn + 1):
        evals = run_dir / f"turn-{n:02d}" / "1-event-evaluations.json"
        if evals.is_file():
            for e in json.loads(evals.read_text(encoding="utf-8")):
                if e.get("triggered"):
                    out.add(e["id"])
    return out


def check_node(node_dir: Path, data: dict[str, Any], event_ids: set[str],
               problems: list[str], fired: set[str] | None = None) -> None:
    prose_path = node_dir / ("choice.md" if (node_dir / "choice.md").is_file()
                             else "narrative.md")
    if not prose_path.is_file():
        problems.append(f"{node_dir.name}: no prose file")
        return
    text = prose_path.read_text(encoding="utf-8")
    body = body_of(text)
    name = node_dir.name

    # 2 — numbers
    allowed = data_numbers(data) | run_numbers(data)
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if fm:
        m = re.search(r"^allow:\s*(.+)$", fm.group(1), re.M)
        if m:
            allowed |= numbers(m.group(1))
    for figure in sorted(numbers(body)):
        if figure not in allowed:
            problems.append(f"{name}: figure {figure} is in the prose but in "
                            f"neither data.json nor the run")

    # 3 — events. Anything that has already happened in this run may be named;
    # anything the run never produced may not.
    if fired is None:
        fired = fired_through((data.get("provenance") or {}).get("turn_dir"))
    for eid in event_ids:
        if re.search(rf"\b{re.escape(eid)}\b", body) and eid not in fired:
            problems.append(f"{name}: names event {eid}, which did not fire this turn")

    # 4 — arm leakage
    for match in ARM_NAMES.finditer(body):
        problems.append(f"{name}: names the arm ({match.group(0)!r}) in reader text")
    for match in ARM_WORDS.finditer(body):
        lo = max(0, match.start() - ARM_WINDOW)
        window = body[lo:match.end() + ARM_WINDOW]
        if ARM_CONTEXT.search(window):
            problems.append(f"{name}: names the arm ({match.group(0)!r}) in reader "
                            f"text — {body[lo:match.end() + 30].strip()!r}")
    for match in BRANCH_ID.finditer(body):
        problems.append(f"{name}: carries branch id {match.group(0)!r} in reader text")


def check_provenance(name: str, data: dict[str, Any], problems: list[str]) -> None:
    prov = data.get("provenance") or {}
    turn_dir = prov.get("turn_dir")
    if not turn_dir:
        return
    path = SCENARIO / turn_dir / "4-metrics.json"
    if not path.is_file():
        problems.append(f"{name}: run artifact missing: {turn_dir}")
        return
    live = json.loads(path.read_text(encoding="utf-8"))
    for mid, entry in (data.get("metrics") or {}).items():
        if live.get(mid) != entry["value"]:
            problems.append(f"{name}: data.json has {mid}={entry['value']}, "
                            f"run now has {live.get(mid)} — re-extract")


def run_checks(tree_dir: Path, tree: dict[str, Any], only: str | None = None) -> list[str]:
    problems: list[str] = []
    event_ids = set()
    events_md = SCENARIO / "events.md"
    if events_md.is_file():
        event_ids = set(re.findall(r"^\**ID:\**\s*`?([a-z0-9_]+)`?",
                                   events_md.read_text(encoding="utf-8"), re.M | re.I))

    expected: list[str] = ["turn-01"]
    for block in tree["blocks"]:
        expected += [f"turn-{t:02d}-{block['block']}" for t in block["turns"]]
    for choice in tree["choices"]:
        expected += [o["node"] for o in choice["options"]]

    nodes: dict[str, dict[str, Any]] = {}
    for name in expected:
        node_dir = tree_dir / name
        if not node_dir.is_dir():
            problems.append(f"{name}: node directory missing")
            continue
        data_path = node_dir / "data.json"
        if not data_path.is_file():
            problems.append(f"{name}: data.json missing")
            continue
        nodes[name] = json.loads(data_path.read_text(encoding="utf-8"))

    extra = {p.name for p in tree_dir.iterdir() if p.is_dir()} - set(expected)
    for name in sorted(extra):
        problems.append(f"{name}: node on disk is not in tree.json")

    # 1 — links resolve
    for name, data in nodes.items():
        targets: list[str] = []
        for key in ("prev_node", "next_node", "next_choice"):
            value = data.get(key)
            if isinstance(value, str):
                targets.append(value)
            elif isinstance(value, list):
                targets += value
        for target in targets:
            if target and target not in nodes:
                problems.append(f"{name}: link to unknown node {target!r}")

    # 1 — the graph reaches exactly 24 endings, all at turn 13
    endings, seen, stack = set(), set(), ["turn-01"]
    while stack:
        name = stack.pop()
        if name in seen or name not in nodes:
            continue
        seen.add(name)
        data = nodes[name]
        onward = []
        for key in ("next_node", "next_choice"):
            value = data.get(key)
            if isinstance(value, str):
                onward.append(value)
            elif isinstance(value, list):
                onward += value
        if not onward:
            endings.add(name)
        stack += onward
    if len(endings) != 24:
        problems.append(f"graph reaches {len(endings)} endings, expected 24")
    for name in sorted(endings):
        if not name.startswith("turn-13-"):
            problems.append(f"{name}: is an ending but not a turn-13 node")
    unreached = set(nodes) - seen
    for name in sorted(unreached):
        problems.append(f"{name}: unreachable from turn-01")

    for name, data in sorted(nodes.items()):
        if only and only not in name:
            continue
        fired = None
        if data.get("source"):
            # An option was drawn against the pinned situation of the turn it
            # leads into, so it may name that turn's events as well as anything
            # already in the parent run's history.
            prev = nodes.get(data.get("prev_node") or "")
            fired = fired_through((prev.get("provenance") or {}).get("turn_dir")
                                  if prev else None)
            for target in (data.get("next_node") or []):
                fired |= {e["id"] for e in nodes.get(target, {}).get("events", [])}
        check_node(tree_dir / name, data, event_ids, problems, fired)
        check_provenance(name, data, problems)
    return problems


def self_test() -> int:
    """Plant three faults in a copy of one node; every one must be caught."""
    tree = json.loads((STORY / "tree.json").read_text(encoding="utf-8"))
    source = STORY / "tree" / "turn-07-A11"
    if not source.is_dir():
        print("self-test needs tree/turn-07-A11; run extract_tree.py first",
              file=sys.stderr)
        return 2
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        node = Path(tmp) / "turn-07-A11"
        shutil.copytree(source, node)
        data = json.loads((node / "data.json").read_text(encoding="utf-8"))
        prose = node / "narrative.md"
        clean = prose.read_text(encoding="utf-8")

        cases = [
            ("wrong metric",
             clean + "\n\nPolitical capital stands at 91.7 by the end of the half-year.\n",
             "91.7"),
            # bio_incident never fires in this run; rsi_onset does, several
            # turns earlier, and naming that would be legitimate.
            ("unfired event",
             clean + "\n\nA bio_incident is reported during the same weeks.\n",
             "bio_incident"),
            ("arm leak",
             clean + "\n\nThis is the Acceleration world, and it shows.\n",
             "Acceleration"),
        ]
        for label, text, needle in cases:
            prose.write_text(text, encoding="utf-8")
            problems: list[str] = []
            event_ids = set(re.findall(r"^\**ID:\**\s*`?([a-z0-9_]+)`?",
                                       (SCENARIO / "events.md").read_text(encoding="utf-8"),
                                       re.M | re.I))
            check_node(node, data, event_ids, problems)
            caught = any(needle in p for p in problems)
            print(f"  {'PASS' if caught else 'FAIL'}  planted {label}: "
                  f"{'caught' if caught else 'NOT CAUGHT'}")
            failures += 0 if caught else 1

        # and a clean node must produce nothing
        prose.write_text(clean, encoding="utf-8")
        problems = []
        check_node(node, data, set(), problems)
        ok = not problems
        print(f"  {'PASS' if ok else 'FAIL'}  clean node: "
              f"{'no complaints' if ok else problems}")
        failures += 0 if ok else 1
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--block", help="only nodes whose name contains this")
    ap.add_argument("--self-test", action="store_true",
                    help="verify the checker catches planted faults")
    args = ap.parse_args()

    if args.self_test:
        print("self-test:")
        return self_test()

    tree = json.loads((STORY / "tree.json").read_text(encoding="utf-8"))
    tree_dir = STORY / "tree"
    if not tree_dir.is_dir():
        print("no tree/ — run extract_tree.py first", file=sys.stderr)
        return 2
    problems = run_checks(tree_dir, tree, args.block)
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        return 1
    print("tree clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
