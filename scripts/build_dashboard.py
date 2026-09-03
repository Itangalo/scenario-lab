"""Build a self-contained HTML dashboard for a batch of Scenario Lab runs.

A batch's findings live in three places that are never on screen together: the
metric values in `turn-XX/4-metrics.json`, the events that fired in
`turn-XX/1-events.json`, and the actor's measure portfolio in
`turn-XX/2-actors/<actor>.md`. Reading a run means opening thirteen directories
and holding the rest of the batch in your head. This collects them into one
page: the arms side by side, then any single run turn by turn with its events,
its portfolio and the narrative that came out of them.

The page embeds its own data and needs no server. `runs/` is gitignored, so
regenerate rather than commit the output.

Usage:

    python scripts/build_dashboard.py scenarios/europe-2032 --seeds 9101-9312
    python scripts/build_dashboard.py scenarios/europe-2032 --out /tmp/dash.html
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TEMPLATE = Path(__file__).with_name("dashboard-template.html")

# `- `Name (category 4, costs 3 per turn, started turn 1, finishes on turn 7): text``
# The backticks are optional, the trailing finished-marker comes in two spellings,
# and the Game Master writes "costs"/"cost" interchangeably.
MEASURE = re.compile(
    r"^[-*]\s*`?\s*(?P<name>.+?)\s*\(category\s*(?P<category>\d+)\s*,\s*"
    r"costs?\s*(?P<cost>\d+)\s*per turn,\s*started turn\s*(?P<start>\d+)\s*,\s*"
    r"finishes on turn\s*(?P<finish>\d+)\s*\)\s*:\s*(?P<description>.*?)\s*`?\s*"
    r"(?:[—–-]+\s*\*\*finished(?:\s+this\s+turn)?\*\*\s*)?$",
    re.IGNORECASE,
)
CANCELLED = re.compile(r"^[-*]\s*Cancell?ed measure:\s*`?(?P<name>[^`.]+)`?\.?\s*(?P<reason>.*)$", re.IGNORECASE)
FINISHED_MARK = re.compile(r"\*\*finished(?:\s+this\s+turn)?\*\*", re.IGNORECASE)
BOLD_NAME = re.compile(r"\*\*(?P<name>[^*]+)\*\*")


def section(text: str, heading: str) -> str:
    """The body under a `## heading`, up to the next heading of any level."""
    match = re.search(rf"^##\s*{re.escape(heading)}\s*$(.*?)(?=^#{{1,3}}\s|\Z)",
                      text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def parse_actor_turn(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"portfolio": [], "new_measure": None, "priority": None, "cancelled": []}
    text = path.read_text(encoding="utf-8")

    portfolio, cancelled = [], []
    for line in section(text, "Portfolio").splitlines():
        line = line.strip()
        if not line:
            continue
        if (m := MEASURE.match(line)):
            portfolio.append({
                "name": m["name"].strip(" `"),
                "category": int(m["category"]),
                "cost": int(m["cost"]),
                "start": int(m["start"]),
                "finish": int(m["finish"]),
                "description": m["description"].strip(" `"),
                "finished": bool(FINISHED_MARK.search(line)),
            })
        elif (m := CANCELLED.match(line)):
            cancelled.append({"name": m["name"].strip(" `"), "reason": m["reason"].strip()})

    def first_bold(heading: str) -> str | None:
        """The measure named under a heading, or None when none was named.

        The Game Master writes the empty case as `**None this turn.**`, as
        `None this turn.`, and occasionally as prose beginning "no new"; all
        three mean the same thing and none of them is a measure name.
        """
        body = section(text, heading)
        bare = body.lstrip("*_ \t")
        if not body or re.match(r"(?:none|no new|nothing)\b", bare, re.IGNORECASE):
            return None
        if (m := BOLD_NAME.search(body)):
            return m["name"].strip()
        # No bold name: take the clause before the reason, not a fixed slice.
        first = body.split("\n")[0]
        return re.split(r"\s+[—–-]{1,2}\s+|(?<=[.;:])\s", first)[0].strip()[:140] or None

    return {
        "portfolio": portfolio,
        "cancelled": cancelled,
        "new_measure": first_bold("New measure"),
        "priority": first_bold("Priority"),
        "reasoning": section(text, "In practice"),
    }


@dataclass
class Catalogue:
    """Event descriptions are long and repeat across runs; store each once."""
    events: dict[str, dict[str, Any]] = field(default_factory=dict)

    def note(self, event: dict[str, Any], fallback: dict[str, str] | None = None) -> str:
        eid = event["id"]
        text = (event.get("description") or "").strip()
        if not text and fallback:
            text = fallback.get(eid, "")
        existing = self.events.get(eid)
        if existing is None:
            self.events[eid] = {"id": eid, "emergent": bool(event.get("emergent")), "description": text}
        elif text and not existing["description"]:
            existing["description"] = text
        return eid


def scenario_event_text(scenario_dir: Path) -> dict[str, str]:
    """Each event's one-line description from events.md, keyed by id.

    Only emergent events carry their description in the run record; the rest are
    defined in the scenario and would otherwise show on the page as a bare id.
    """
    path = scenario_dir / "events.md"
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for block in re.split(r"^##\s+", path.read_text(encoding="utf-8"), flags=re.MULTILINE)[1:]:
        head, _, body = block.partition("\n")
        mid = re.search(r"^[-*]?\s*\*\*ID:\*\*\s*`?([a-z0-9_]+)`?", body, re.MULTILINE | re.IGNORECASE)
        if not mid:
            mid = re.search(r"^\s*[-*]?\s*ID:\s*`?([a-z0-9_]+)`?", body, re.MULTILINE | re.IGNORECASE)
        if mid:
            out[mid.group(1)] = head.strip()
    return out


def read_run(run_dir: Path, actor: str, catalogue: Catalogue,
             catalogue_text: dict[str, str] | None = None) -> dict[str, Any] | None:
    config_path = run_dir / "config.json"
    if not config_path.exists():
        return None
    config = json.loads(config_path.read_text(encoding="utf-8"))
    turn_dirs = sorted(run_dir.glob("turn-*"))
    if not turn_dirs:
        return None

    turns, series = [], {}
    for turn_dir in turn_dirs:
        metrics_path = turn_dir / "4-metrics.json"
        if not metrics_path.exists():
            continue
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        for key, value in metrics.items():
            series.setdefault(key, []).append(value)

        # `1-event-evaluations.json` carries the dice and the `triggered` flag;
        # `1-events.json` carries the descriptions, and is the only place an
        # emergent event's text exists. Neither file alone says what happened.
        described = {}
        events_path = turn_dir / "1-events.json"
        if events_path.exists():
            for event in json.loads(events_path.read_text(encoding="utf-8")):
                described[event["id"]] = event
        fired = []
        evaluations_path = turn_dir / "1-event-evaluations.json"
        if evaluations_path.exists():
            for evaluation in json.loads(evaluations_path.read_text(encoding="utf-8")):
                if evaluation.get("triggered"):
                    merged = {**described.get(evaluation["id"], {}), **evaluation}
                    fired.append(catalogue.note(merged, catalogue_text))

        world = turn_dir / "4-world-state.md"
        notepad = turn_dir / "5-notepad.md"
        turns.append({
            "turn": int(turn_dir.name.split("-")[1]),
            "metrics": metrics,
            "events": fired,
            "narrative": world.read_text(encoding="utf-8").strip() if world.exists() else "",
            "notepad": notepad.read_text(encoding="utf-8").strip() if notepad.exists() else "",
            **parse_actor_turn(turn_dir / "2-actors" / f"{actor}.md"),
        })

    name = config.get("name", run_dir.name)
    return {
        "id": run_dir.name,
        "seed": config.get("random_seed"),
        "arm": name.split("—")[-1].strip() if "—" in name else name,
        "series": series,
        "turns": turns,
    }


def parse_seed_range(spec: str | None) -> tuple[int, int] | None:
    if not spec:
        return None
    lo, _, hi = spec.partition("-")
    return int(lo), int(hi or lo)


def metric_definitions(scenario_dir: Path) -> list[dict[str, Any]]:
    """Metric ids, ranges and start values, read from metrics.md."""
    path = scenario_dir / "metrics.md"
    if not path.exists():
        return []
    out = []
    for block in re.split(r"^##\s+", path.read_text(encoding="utf-8"), flags=re.MULTILINE)[1:]:
        head, _, body = block.partition("\n")
        mid = re.search(r"^\*\*ID:\*\*\s*(\S+)", body, re.MULTILINE)
        if not mid:
            continue

        def field_value(label: str) -> float | None:
            m = re.search(rf"^\*\*{label}:\*\*\s*([-\d.]+)", body, re.MULTILINE)
            return float(m.group(1)) if m else None

        out.append({
            "id": mid.group(1).strip(),
            "label": head.strip(),
            "min": field_value("Min"),
            "max": field_value("Max"),
            "start": field_value("Start value"),
            "description": (re.search(r"^\*\*Description:\*\*\s*(.+)", body, re.MULTILINE) or [None, ""])[1],
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scenario", type=Path, help="scenario directory, e.g. scenarios/europe-2032")
    parser.add_argument("--seeds", help="restrict to a seed range, e.g. 9101-9312")
    parser.add_argument("--actor", default="eu", help="actor whose portfolio is read (default: eu)")
    parser.add_argument("--out", type=Path, help="output HTML (default: <scenario>/dashboard.html)")
    parser.add_argument("--title", default=None, help="title shown on the page")
    args = parser.parse_args()

    seeds = parse_seed_range(args.seeds)
    event_text = scenario_event_text(args.scenario)
    catalogue = Catalogue()
    runs = []
    for run_dir in sorted((args.scenario / "runs").glob("run-*")):
        config = run_dir / "config.json"
        if not config.exists():
            continue
        if seeds:
            seed = json.loads(config.read_text(encoding="utf-8")).get("random_seed", 0)
            if not seeds[0] <= seed <= seeds[1]:
                continue
        run = read_run(run_dir, args.actor, catalogue, event_text)
        if run and run["turns"]:
            runs.append(run)

    if not runs:
        print("no runs matched", flush=True)
        return 1

    payload = {
        "title": args.title or f"{args.scenario.name} — {len(runs)} runs",
        "scenario": args.scenario.name,
        "metrics": metric_definitions(args.scenario),
        "events": list(catalogue.events.values()),
        "runs": runs,
    }
    out = args.out or (args.scenario / "dashboard.html")
    html = TEMPLATE.read_text(encoding="utf-8").replace(
        "/*__DATA__*/null", json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
    out.write_text(html, encoding="utf-8")
    size = out.stat().st_size / 1_000_000
    arms = {}
    for r in runs:
        arms[r["arm"]] = arms.get(r["arm"], 0) + 1
    print(f"{out}  ({size:.1f} MB)")
    print(f"{len(runs)} runs: " + ", ".join(f"{k} {v}" for k, v in sorted(arms.items())))
    print(f"{len(catalogue.events)} distinct events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
