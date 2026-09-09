"""Measure whether an actor's measure portfolio survives being restated.

The portfolio is not held by the framework. The actor re-emits it in its own
output every turn, so an entry persists only if the model remembers to write it
again. This script measures how often that fails, in the two ways it can:

* **never entered** -- a measure is proposed and never appears in the portfolio
  at any later turn. Invisible from the first moment.
* **vanished** -- a measure is in the portfolio at turn N and gone at N+1
  without having finished and without a cancellation line.

Both are split into explained and unexplained. A non-entry is explained when the
turn's world state or notepad says why (portfolio saturation, deferral, not
formally tabled, rejection); a departure is explained when the measure was
marked finished, reached its finish turn, or was cancelled.

Contrast this with `<actor>-statements.md` in the same runs: statements are
carried forward verbatim by Python and never restated by the model, and they do
not drift. Same actor, same turn, two custody models.

Usage:
    python scripts/check_ledger.py scenarios/europe-2032
    python scripts/check_ledger.py scenarios/europe-2032 --filter batch=stats-20260908
    python scripts/check_ledger.py scenarios/europe-2032 --actor eu --examples 10
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dashboard import parse_actor_turn  # noqa: E402

# Words too generic to identify a measure. The Game Master paraphrases names
# between turns, so matching is on distinctive words rather than equality.
STOP = {"the", "of", "and", "for", "a", "an", "to", "in", "on", "eu", "european",
        "union", "initiative", "programme", "program", "directive", "framework",
        "regime", "measure", "establish", "launch", "new", "act", "system",
        "systems", "ai"}

DEFERRED = re.compile(
    r"portfolio saturation|not formally (?:introduced|proposed|tabled|adopted)|"
    r"remains? in (?:drafting|preparation|consultation|pre-legislative|review)|"
    r"deferred|one[- ]measure limit|at most one new measure|cannot introduce a new|"
    r"held back|no new measure|not yet (?:tabled|adopted|introduced|launched)|"
    r"delayed (?:to|until)|awaits? portfolio|withdrawn|rejected|blocked by|"
    r"does not (?:enter|count)|is not counted|shelved|postponed|stalls? in|"
    r"fails? to (?:launch|proceed)|no additional measure", re.I)


def words(name: str | None) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", (name or "").lower())
            if w not in STOP and len(w) > 3}


def same(a: str | None, b: str | None) -> bool:
    wa, wb = words(a), words(b)
    return bool(wa and wb and (wa & wb))


def turns_of(run_dir: Path) -> list[int]:
    return sorted(int(d.name.split("-")[1]) for d in run_dir.glob("turn-*"))


def audit(run_dirs: list[Path], actor: str, limit: int) -> dict[str, Any]:
    entered = non_entry_ok = non_entry_bad = 0
    carried = left_ok = left_bad = 0
    never_eg: list[str] = []
    vanished_eg: list[str] = []

    for rd in run_dirs:
        turns = turns_of(rd)
        parsed = {t: parse_actor_turn(rd / f"turn-{t:02d}" / "2-actors" / f"{actor}.md")
                  for t in turns}
        for t in turns:
            later = [x for x in turns if x > t]

            # -- proposed, and did it ever arrive? --------------------------
            proposal = parsed[t]["new_measure"]
            if words(proposal) and later:
                if any(any(words(proposal) & words(m["name"]) for m in parsed[x]["portfolio"])
                       for x in later):
                    entered += 1
                else:
                    blob = ""
                    for name in ("4-world-state.md", "5-notepad.md"):
                        f = rd / f"turn-{t:02d}" / name
                        if f.is_file():
                            blob += f.read_text(encoding="utf-8")
                    if DEFERRED.search(blob):
                        non_entry_ok += 1
                    else:
                        non_entry_bad += 1
                        if len(never_eg) < limit:
                            never_eg.append(f"{rd.name} turn {t}: {proposal[:52]}")

            # -- present, and did it survive the next turn? -----------------
            if t + 1 not in turns:
                continue
            nxt = parsed[t + 1]
            gone_names = [c["name"] for c in nxt["cancelled"]] + \
                         [c["name"] for c in parsed[t]["cancelled"]]
            for m in parsed[t]["portfolio"]:
                if any(same(m["name"], n["name"]) for n in nxt["portfolio"]):
                    carried += 1
                elif m.get("finished") or (m.get("finish") is not None and m["finish"] <= t) \
                        or any(same(m["name"], c) for c in gone_names):
                    left_ok += 1
                else:
                    left_bad += 1
                    if len(vanished_eg) < limit:
                        vanished_eg.append(
                            f"{rd.name} turn {t}->{t+1}: {m['name'][:46]} "
                            f"(finishes {m.get('finish')})")

    return {"proposals": entered + non_entry_ok + non_entry_bad, "entered": entered,
            "non_entry_ok": non_entry_ok, "non_entry_bad": non_entry_bad,
            "transitions": carried + left_ok + left_bad, "carried": carried,
            "left_ok": left_ok, "left_bad": left_bad,
            "never_eg": never_eg, "vanished_eg": vanished_eg}


def pct(n: int, d: int) -> str:
    return f"{100 * n / d:.1f}%" if d else "—"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenario", type=Path)
    ap.add_argument("--actor", default="eu")
    ap.add_argument("--filter", help="substring that must appear in a run's config.json")
    ap.add_argument("--examples", type=int, default=5)
    args = ap.parse_args()

    runs_dir = args.scenario / "runs"
    runs = [d for d in sorted(runs_dir.iterdir())
            if d.is_dir() and (d / "config.json").is_file()]
    if args.filter:
        runs = [d for d in runs
                if args.filter in (d / "config.json").read_text(encoding="utf-8")]
    runs = [d for d in runs if turns_of(d)]
    if not runs:
        print("no runs matched", file=sys.stderr)
        return 2

    r = audit(runs, args.actor, args.examples)
    print(f"{len(runs)} runs, actor '{args.actor}'\n")
    print(f"proposed measures: {r['proposals']}")
    print(f"  entered the portfolio at some later turn: {r['entered']:5}  "
          f"({pct(r['entered'], r['proposals'])})")
    print(f"  never entered, reason stated:             {r['non_entry_ok']:5}  "
          f"({pct(r['non_entry_ok'], r['proposals'])})")
    print(f"  never entered, NO reason stated:          {r['non_entry_bad']:5}  "
          f"({pct(r['non_entry_bad'], r['proposals'])})")
    print(f"\nmeasure-turn transitions: {r['transitions']}")
    print(f"  carried forward:                          {r['carried']:5}  "
          f"({pct(r['carried'], r['transitions'])})")
    print(f"  left with a stated cause:                 {r['left_ok']:5}  "
          f"({pct(r['left_ok'], r['transitions'])})")
    print(f"  vanished, NO stated cause:                {r['left_bad']:5}  "
          f"({pct(r['left_bad'], r['transitions'])})")
    if r["never_eg"]:
        print("\nnever entered, examples:")
        for e in r["never_eg"]:
            print(f"  {e}")
    if r["vanished_eg"]:
        print("\nvanished, examples:")
        for e in r["vanished_eg"]:
            print(f"  {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
