"""Measure whether an actor's measure portfolio survives being restated.

**This measures the design the store replaced.** Where a scenario declares a
`store:` block, the portfolio is held by Python, the actor never restates it,
and the two failures below cannot happen -- so on such a run this script should
report zero of both, and anything else is a bug in the store rather than a
finding about the model. It is kept because the 570 runs already committed were
made under the old design and are still the evidence base for what that design
cost; see docs/proposals/persistent-state-custody.md and the *Declared
Persistent State* section of docs/ARCHITECTURE.md.

Under the old design the actor re-emitted the portfolio in its own output every
turn, so an entry persisted only if the model remembered to write it again.
This script measures how often that failed, in the two ways it could:

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
import json
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
    declined = unreadable = 0
    never_eg: list[str] = []
    vanished_eg: list[str] = []

    for rd in run_dirs:
        turns = turns_of(rd)
        parsed = {t: parse_actor_turn(rd / f"turn-{t:02d}" / "2-actors" / f"{actor}.md")
                  for t in turns}
        for t in turns:
            later = [x for x in turns if x > t]

            # -- proposed, and did it ever arrive? --------------------------
            # A turn the parser could not read is counted apart from one where
            # the actor named nothing. Folded together they made a total parse
            # failure print as "proposed measures: 0", which reads like a
            # perfect score; the muse-spark cohort of 2026-09-09 did exactly
            # that for 39 of 39 turns.
            status = parsed[t].get("new_measure_status", "named")
            if status == "declined":
                declined += 1
            elif status == "unreadable":
                unreadable += 1
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
            "never_eg": never_eg, "vanished_eg": vanished_eg,
            "declined": declined, "unreadable": unreadable}


def audit_store(run_dirs: list[Path], actor: str, limit: int) -> dict[str, Any]:
    """The same question, asked of runs whose portfolio the framework holds.

    Custody makes the two failures above impossible, so it is not what needs
    measuring here. What needs measuring is what custody does *not* fix: an
    actor that describes a measure in prose and never writes the command for
    it. That was the larger half of the defect (never-entered, 4.5%), and the
    re-ask hook that would close it is not built. Until it is, this counts the
    faults the store artifacts already record.
    """
    turns = missing = rejected = unparsed = applied = 0
    described_without_add = described_without_anything = 0
    examples: list[str] = []

    for rd in run_dirs:
        for t in turns_of(rd):
            artifact = rd / f"turn-{t:02d}" / "2-actors" / f"{actor}-store.md"
            if not artifact.is_file():
                continue
            turns += 1
            text = artifact.read_text(encoding="utf-8")
            changes = text.split("## Changes this turn", 1)[-1]
            if "No `## Store changes` section" in text:
                missing += 1
                if len(examples) < limit:
                    examples.append(f"{rd.name} turn {t}: no section written")
            rejected += changes.count("- **rejected**")
            unparsed += changes.count("- **unparsed**")
            applied += changes.count("- **applied**")

            # A measure argued for in prose but never entered by a command.
            #
            # Split in two, because the first number is not what it looks
            # like. The actor is told that broadening a measure already in
            # flight is not a new measure, and when it follows that
            # instruction it argues under `## New measure` and issues an
            # `update`, not an `add`. That is correct behaviour and it lands
            # in the first count. Only a turn that argued for a measure and
            # then recorded *nothing at all* is the failure custody does not
            # reach.
            prose = (rd / f"turn-{t:02d}" / "2-actors" / f"{actor}.md")
            parsed = parse_actor_turn(prose)
            described = parsed.get("new_measure_status") == "named" and (
                "## New measure" in prose.read_text(encoding="utf-8")
                if prose.is_file() else False
            )
            if described and "add measures" not in changes:
                described_without_add += 1
                wrote_nothing = "- **applied**" not in changes
                if wrote_nothing:
                    described_without_anything += 1
                if len(examples) < limit:
                    label = ("described, nothing recorded" if wrote_nothing
                             else "described, recorded as a change to an existing measure")
                    name = parsed.get("new_measure") or ""
                    examples.append(f"{rd.name} turn {t}: {label}: {name[:44]}")

    return {"turns": turns, "missing": missing, "rejected": rejected,
            "unparsed": unparsed, "applied": applied,
            "described_without_add": described_without_add,
            "described_without_anything": described_without_anything,
            "examples": examples}


def audit_charges(run_dirs: list[Path], actor: str, limit: int) -> dict[str, Any]:
    """Check the Game Master's portfolio-charge line against the store.

    This is a measurement the store makes possible and nothing made possible
    before. `design-notes.md` records that the sovereignty line's own terms
    summed to the total it stated in 51-70% of turns, and there was no
    independent figure to check the portfolio charge against -- the portfolio
    itself was whatever the actor had last written down. Now there is one.

    Two separate things are checked, because they fail for different reasons:

    * **terms match the store** -- the measures the Game Master charged are the
      measures actually in flight. A mismatch means it is charging from the
      narrative rather than from the rows it was given.
    * **the line adds up** -- the stated total equals its own terms. A mismatch
      is arithmetic, and it is the failure the itemised line exists to expose.
    """
    checked = terms_ok = arith_ok = 0
    examples: list[str] = []

    for rd in run_dirs:
        for t in turns_of(rd):
            state_file = rd / f"turn-{t:02d}" / "2-actors" / f"{actor}-store.json"
            notepad = rd / f"turn-{t:02d}" / "5-notepad.md"
            if not (state_file.is_file() and notepad.is_file()):
                continue
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue

            expected = 0
            for record in state.get("records", []):
                if record.get("table") != "measures" or record.get("removed_turn") is not None:
                    continue
                finish = record.get("fields", {}).get("finish_turn")
                if isinstance(finish, int) and t >= finish:
                    continue  # finished: paid this turn, not charged
                cost = record.get("derived", {}).get("cost_per_turn")
                if not isinstance(cost, int):
                    cost = 3 if record.get("fields", {}).get("size") == "large" else 2
                expected += cost

            lines = [l for l in notepad.read_text(encoding="utf-8").splitlines()
                     if "PORTFOLIO CHARGE" in l.upper()]
            if not lines:
                continue
            head, _, tail = lines[-1].rpartition("=")
            written = [int(x) for x in re.findall(r"[\u2212-](\d+)", head)]
            if not written:
                continue
            stated = re.findall(r"(\d+)", tail)
            stated_total = int(stated[0]) if stated else None
            # The priority is a further cost the framework cannot compute: it
            # does not know which measure was named.
            priority = 1 if "priorit" in head.lower() else 0
            measures = sum(written) - priority

            checked += 1
            matched = measures == expected
            adds_up = stated_total == sum(written)
            terms_ok += matched
            arith_ok += adds_up
            if not (matched and adds_up) and len(examples) < limit:
                faults = []
                if not matched:
                    faults.append(f"charged {measures}, store says {expected}")
                if not adds_up:
                    faults.append(f"terms sum to {sum(written)}, line states {stated_total}")
                examples.append(f"{rd.name} turn {t}: " + "; ".join(faults))

    return {"checked": checked, "terms_ok": terms_ok, "arith_ok": arith_ok,
            "examples": examples}


def pct(n: int, d: int) -> str:
    return f"{100 * n / d:.1f}%" if d else "—"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenario", type=Path)
    ap.add_argument("--actor", default="eu")
    ap.add_argument("--filter", help="substring that must appear in a run's config.json")
    ap.add_argument("--examples", type=int, default=5)
    ap.add_argument("--store", action="store_true",
                    help="audit runs whose portfolio the framework holds, instead")
    ap.add_argument("--charges", action="store_true",
                    help="check the Game Master's charge line against the store")
    args = ap.parse_args()

    runs_dir = args.scenario / "runs"
    runs = [d for d in sorted(runs_dir.iterdir())
            if d.is_dir() and (d / "config.json").is_file()]
    if args.filter:
        # Matched against the run's own name as well as its config, so a single
        # run can be picked out by directory without inventing a config key.
        runs = [d for d in runs
                if args.filter in d.name
                or args.filter in (d / "config.json").read_text(encoding="utf-8")]
    runs = [d for d in runs if turns_of(d)]
    if not runs:
        print("no runs matched", file=sys.stderr)
        return 2

    if args.charges:
        return report_charges(audit_charges(runs, args.actor, args.examples), len(runs), args.actor)

    if args.store:
        return report_store(audit_store(runs, args.actor, args.examples), len(runs), args.actor)

    r = audit(runs, args.actor, args.examples)
    print(f"{len(runs)} runs, actor '{args.actor}'\n")
    if r["unreadable"]:
        print(f"⚠️  {r['unreadable']} turn(s) had no readable 'New measure' section. "
              f"Those are NOT counted below as measures that were never proposed; "
              f"they are turns this instrument could not read, and every figure "
              f"here understates the truth by that much. Check the actor output's "
              f"format before reading the rest.\n")
    print(f"turns where the actor named no measure and said so: {r['declined']}")
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


def report_store(r: dict[str, Any], run_count: int, actor: str) -> int:
    if not r["turns"]:
        print("no store artifacts found -- these runs predate the store, "
              "or the scenario declares none. Run without --store.", file=sys.stderr)
        return 2
    print(f"{run_count} runs, actor '{actor}', {r['turns']} turns with a store artifact\n")
    print(f"commands applied:                            {r['applied']:5}")
    print(f"turns with NO '## Store changes' section:    {r['missing']:5}  "
          f"({pct(r['missing'], r['turns'])})")
    print(f"commands rejected:                           {r['rejected']:5}")
    print(f"lines the parser could not read:             {r['unparsed']:5}")
    print(f"argued under New measure, no `add` issued:   {r['described_without_add']:5}  "
          f"({pct(r['described_without_add'], r['turns'])})")
    print(f"  ...of which recorded nothing at all:       {r['described_without_anything']:5}  "
          f"({pct(r['described_without_anything'], r['turns'])})")
    print("\nEntries cannot be lost from the store, so there is no drift figure here.")
    print("The last line is the failure custody does not reach -- a measure argued for")
    print("and never recorded -- and is the case for the re-ask hook. The line above it")
    print("is mostly correct behaviour: the actor is told that broadening a measure")
    print("already in flight is an `update`, not a new measure, and this counts those too.")
    if r["examples"]:
        print("\nexamples:")
        for e in r["examples"]:
            print(f"  {e}")
    return 0


def report_charges(r: dict[str, Any], run_count: int, actor: str) -> int:
    if not r["checked"]:
        print("no charge lines found beside a store artifact. These runs predate "
              "the store, or the scenario writes no PORTFOLIO CHARGE line.", file=sys.stderr)
        return 2
    print(f"{run_count} runs, actor '{actor}', {r['checked']} charge lines\n")
    print(f"terms match the measures actually in flight:  {r['terms_ok']:5}  "
          f"({pct(r['terms_ok'], r['checked'])})")
    print(f"the line adds up to its own total:            {r['arith_ok']:5}  "
          f"({pct(r['arith_ok'], r['checked'])})")
    print("\nThe first is whether the Game Master charged from the rows it was given")
    print("or from the narrative. The second is arithmetic, which is what the itemised")
    print("line exists to expose. Neither was checkable before the store: the portfolio")
    print("was whatever the actor had last written down, so there was nothing to check")
    print("the charge against.")
    if r["examples"]:
        print("\nexamples:")
        for e in r["examples"]:
            print(f"  {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
