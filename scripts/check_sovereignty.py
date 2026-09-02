"""Check whether the notepad's SOVEREIGNTY line binds the applied metric.

The Game Master is asked to account for every point of `eu_ai_sovereignty` it
moves, on its own Notepad line, before it moves it. Nothing in the pipeline
reconciles that line against the value it then writes into the metrics JSON, so
a line that is pure decoration looks exactly like one that is load-bearing.
This script reads both and says which it is.

Three things are measured per turn:

* **arithmetic** – do the line's own terms sum to the total it states?
* **binding** – does the stated total equal the change actually applied?
* **legality** – metric rule 5 gives sovereignty two sources, and only a
  category 4 measure in the turn it finishes pays more than +2. A turn that
  applies more than that while naming no completion has broken the rule
  whatever the line says.

Usage:

    python scripts/check_sovereignty.py scenarios/europe-2032/runs/run-*/
    python scripts/check_sovereignty.py scenarios/europe-2032/runs --since 20260902
    python scripts/check_sovereignty.py <runs...> --per-turn
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

METRIC = "eu_ai_sovereignty"
LINE_PREFIX = "SOVEREIGNTY:"

# The Game Master writes minus signs as U+2212 and dashes as U+2013 about as
# often as it writes ASCII.
MINUSES = "−–—‐‑"
NUMBER = re.compile(rf"([+\-{MINUSES}]?)\s?(\d+(?:\.\d+)?)")

# A completion is the only source worth more than +2. "in flight" appears in
# the same lines and must not be read as one.
FINISHED = re.compile(r"\bfinish(?:ed|es|ing)\b", re.IGNORECASE)
IN_FLIGHT = re.compile(r"\bin flight\b", re.IGNORECASE)

LEGAL_WITHOUT_COMPLETION = 2.0

# Names that carry no measure: `no measure finished`, `no category 4 finish`.
NOT_A_MEASURE = re.compile(r"^(?:and\s+)?(?:no|nothing|none)\b", re.IGNORECASE)

# `SOVEREIGNTY: 31 last turn, ... = 36` anchors the line to a level and ends at
# one. The earlier form named terms and ended at a delta; both are read, so a
# batch run before the change stays comparable with one run after it.
ANCHOR = re.compile(rf"^\s*([+\-{MINUSES}]?\s?\d+(?:\.\d+)?)\s*(?:last turn|start|starting|at start)", re.IGNORECASE)


def _to_float(sign: str, digits: str) -> float:
    value = float(digits)
    return -value if sign and sign in f"-{MINUSES}" else value


@dataclass
class TurnCheck:
    run: str
    turn: int
    line: str | None
    terms: list[float]
    stated: float | None
    applied: float | None
    names_completion: bool
    completions: list[str]
    anchor: float | None = None
    before: float | None = None
    # The change the line claims when read against its own anchor rather than
    # against the metric. Binding asks whether the line matches the world;
    # arithmetic asks whether the line matches itself, and conflating the two
    # makes a wrong anchor look like a wrong sum.
    stated_self: float | None = None

    @property
    def anchored(self) -> bool:
        return self.anchor is not None

    @property
    def anchor_ok(self) -> bool | None:
        """Whether the line started from the value it was actually given."""
        if self.anchor is None or self.before is None:
            return None
        return abs(self.anchor - self.before) < 0.01

    @property
    def arithmetic_ok(self) -> bool | None:
        claimed = self.stated_self if self.stated_self is not None else self.stated
        if claimed is None or not self.terms:
            return None
        return abs(sum(self.terms) - claimed) < 0.01

    @property
    def binds(self) -> bool | None:
        if self.stated is None or self.applied is None:
            return None
        return abs(self.stated - self.applied) < 0.01

    @property
    def legal(self) -> bool | None:
        if self.applied is None:
            return None
        if self.names_completion:
            return True
        return self.applied <= LEGAL_WITHOUT_COMPLETION


def parse_line(line: str) -> tuple[list[float], list[float], float | None]:
    """Split a SOVEREIGNTY line into its terms, its claims, and its anchor.

    A claim is left unresolved here because the line does not say whether it is
    a level or a change. The anchored form ends at a level (`= 36`) but may
    append a change (`(net +1)`); the earlier form ends at a change (`= +9`)
    but may append a level (`(net 37.0)`). `resolve_claim` decides, using the
    value the metric actually held going in.
    """
    body = line.split(LINE_PREFIX, 1)[1].strip()
    if "=" not in body:
        # `SOVEREIGNTY: no change` and other prose-only forms.
        return [], [0.0] if "no change" in body.lower() else [], None

    head, _, tail = body.rpartition("=")

    anchor: float | None = None
    match = ANCHOR.match(head)
    if match:
        number = NUMBER.match(match.group(1).strip())
        if number:
            anchor = _to_float(*number.groups())
        head = head[match.end():]

    terms = [_to_float(s, d) for s, d in NUMBER.findall(_strip_prose(head))]

    # Everything the line claims after its last `=`: the total itself, then any
    # restatement of it (`-> net +1`, `rounded to +1`, `(net 37.0)`). The last
    # claim is the number the model was looking at when it wrote the metric.
    claims = [_to_float(s, d) for s, d in NUMBER.findall(tail)]
    return terms, claims, anchor


def resolve_claim(claim: float, reference: float | None) -> float:
    """Turn a claim into the change it asserts.

    The Game Master mixes levels and changes freely, within one line and
    between turns, and the shape of the line does not reliably say which is
    which. What does say is the value the metric held going in: a claim nearer
    to that value than to zero is a level, and anything else is a change. A
    line reading `= 33` after 32 is claiming a level; `= −1` after 22 is
    claiming a change; and `= 0` after 22 is claiming a change of nothing,
    which the same test gets right because 0 is nearer zero than 22.

    Without a reference — turn 1 — a claim can only be read as a change.
    """
    if reference is None:
        return claim
    return claim - reference if abs(claim - reference) < abs(claim) else claim


def completions(line: str) -> list[str]:
    """The measures a line credits with finishing money, by name.

    A measure finishes once. One credited in two turns has been paid twice, and
    that is invisible in any single turn's line — it only shows up by reading a
    run's turns against each other.
    """
    names: list[str] = []
    for chunk in re.split(r"[,;]", line.split(LINE_PREFIX, 1)[1]):
        if not FINISHED.search(chunk) or IN_FLIGHT.search(chunk):
            continue
        name = chunk[: FINISHED.search(chunk).start()].strip()
        name = re.sub(r"\((?:cat|category)[^)]*\)", "", name, flags=re.IGNORECASE).strip()
        if name and not NOT_A_MEASURE.match(name):
            names.append(name.lower().strip(" -–—"))
    return names


def same_measure(a: str, b: str) -> bool:
    """Whether two credited names are the same measure.

    The Game Master shortens a long title freely between turns — `Secure and
    Scale EU-Controlled Inference Infrastructure` becomes `Secure and Scale` —
    so a prefix match is the honest comparison.
    """
    return a.startswith(b) or b.startswith(a)


def _strip_prose(head: str) -> str:
    """Drop numbers that are not terms.

    `capability rose 2.5 −1` carries the size of the rise and then the cost it
    triggers; only the second is a term. Measure names and categories bring
    their own digits — `(cat 4)`, `Article 6` — and none of those are terms
    either.
    """
    head = re.sub(r"\brose\s+(?:by\s+)?[≥≤<>~]*\s*\d+(?:\.\d+)?", "rose", head, flags=re.IGNORECASE)
    # `capability rose 1.5 -> no -1` is rule 5's decay declining to fire, because
    # the rise was under 2. The -1 named there is the term that does NOT apply.
    head = re.sub(rf"\bno\s+[+\-{MINUSES}]\s?\d+(?:\.\d+)?", "", head, flags=re.IGNORECASE)
    # The threshold rule 5 is being checked against -- `(under 2)`, `< 2`,
    # `(less than 2)` -- is a citation of the condition, never a term.
    head = re.sub(
        r"\(?\b(?:under|over|above|below|less than|more than|at least|at most)\s*\d+(?:\.\d+)?\)?",
        "",
        head,
        flags=re.IGNORECASE,
    )
    head = re.sub(r"[<>≥≤]\s*\d+(?:\.\d+)?", "", head)
    head = re.sub(r"\(cat(?:egory)?\.?\s*\d+[^)]*\)", "", head, flags=re.IGNORECASE)
    head = re.sub(r"\bcat(?:egory)?\.?\s*\d+\b", "", head, flags=re.IGNORECASE)
    head = re.sub(r"\bturn\s+\d+\b", "", head, flags=re.IGNORECASE)
    # `finishes t7 +5` names the turn a measure completes; only the +5 is a term.
    head = re.sub(r"\bt\d+\b", "", head, flags=re.IGNORECASE)
    return head


def read_turn(run: Path, turn_dir: Path) -> TurnCheck | None:
    metrics_path = turn_dir / "4-metrics.json"
    notepad_path = turn_dir / "5-notepad.md"
    if not metrics_path.exists():
        return None
    turn = int(turn_dir.name.split("-")[1])

    metrics = json.loads(metrics_path.read_text())
    previous = run / f"turn-{turn - 1:02d}" / "4-metrics.json"
    applied: float | None = None
    before: float | None = None
    if previous.exists() and METRIC in metrics:
        before = json.loads(previous.read_text()).get(METRIC)
        if before is not None:
            applied = metrics[METRIC] - before

    line = None
    if notepad_path.exists():
        for candidate in notepad_path.read_text().splitlines():
            if candidate.strip().startswith(LINE_PREFIX):
                line = candidate.strip()
                break

    terms: list[float] = []
    stated: float | None = None
    stated_self: float | None = None
    anchor: float | None = None
    names_completion = False
    if line:
        terms, claims, anchor = parse_line(line)
        names_completion = bool(FINISHED.search(line))
        if claims:
            stated = resolve_claim(claims[-1], before if before is not None else anchor)
            stated_self = resolve_claim(claims[-1], anchor if anchor is not None else before)

    credited = completions(line) if line else []
    return TurnCheck(
        run.name, turn, line, terms, stated, applied, names_completion, credited,
        anchor, before, stated_self,
    )


def collect(paths: list[Path], since: str | None) -> list[TurnCheck]:
    runs: list[Path] = []
    for path in paths:
        if (path / "config.json").exists():
            runs.append(path)
        else:
            runs.extend(sorted(p for p in path.glob("run-*") if p.is_dir()))
    if since:
        runs = [r for r in runs if r.name >= f"run-{since}"]

    checks: list[TurnCheck] = []
    for run in sorted(set(runs)):
        for turn_dir in sorted(run.glob("turn-*")):
            check = read_turn(run, turn_dir)
            if check is not None:
                checks.append(check)
    return checks


def rate(hits: int, total: int) -> str:
    if not total:
        return "n/a"
    return f"{hits}/{total} ({hits / total:.0%})"


def summarise(label: str, checks: list[TurnCheck], detail: bool) -> None:
    runs = sorted({c.run for c in checks})
    written = [c for c in checks if c.line]
    comparable = [c for c in checks if c.binds is not None]
    arithmetic = [c for c in checks if c.arithmetic_ok is not None]
    legality = [c for c in checks if c.legal is not None]
    anchored = [c for c in written if c.anchored]

    print(f"{label}: {len(runs)} run(s), {len(checks)} turn(s)\n")
    print(f"  line written        {rate(len(written), len(checks))}")
    print(f"  terms sum to total  {rate(sum(1 for c in arithmetic if c.arithmetic_ok), len(arithmetic))}")
    print(f"  total is applied    {rate(sum(1 for c in comparable if c.binds), len(comparable))}")
    print(f"  rule 5 respected    {rate(sum(1 for c in legality if c.legal), len(legality))}")
    if anchored:
        checkable = [c for c in anchored if c.anchor_ok is not None]
        print(f"  line anchored       {rate(len(anchored), len(written))}")
        print(f"  starts from last    {rate(sum(1 for c in checkable if c.anchor_ok), len(checkable))}")

    drift = [c.applied - c.stated for c in comparable if c.binds is False]
    if drift:
        over = sum(1 for d in drift if d > 0)
        print(
            f"\n  where it does not bind: {len(drift)} turn(s), "
            f"{over} applied more than stated, {len(drift) - over} less; "
            f"largest gap {max(drift, key=abs):+.1f}"
        )

    repeats: list[tuple[str, str, list[int]]] = []
    for run in runs:
        seen: dict[str, list[int]] = {}
        for c in (c for c in checks if c.run == run):
            for name in c.completions:
                key = next((k for k in seen if same_measure(k, name)), name)
                seen.setdefault(key, []).append(c.turn)
        repeats.extend((run, name, turns) for name, turns in seen.items() if len(turns) > 1)
    if repeats:
        affected = len({run for run, _, _ in repeats})
        print(
            f"\n  measures credited with finishing in more than one turn: "
            f"{len(repeats)} in {affected} of {len(runs)} run(s)"
        )
        if detail:
            for run, name, turns in repeats:
                print(f"    {run}: {name} paid on turns {', '.join(str(t) for t in turns)}")

    illegal = [c for c in legality if c.legal is False]
    if illegal:
        biggest = max(illegal, key=lambda c: c.applied or 0)
        print(
            f"  moves above +{LEGAL_WITHOUT_COMPLETION:.0f} with no completion named: "
            f"{len(illegal)} turn(s), largest {biggest.applied:+.1f} "
            f"({biggest.run} turn {biggest.turn})"
        )


def show_turns(checks: list[TurnCheck]) -> None:
    for c in checks:
        flags = "".join(
            [
                " " if c.arithmetic_ok is not False else "A",
                " " if c.binds is not False else "B",
                " " if c.legal is not False else "L",
            ]
        )
        stated = f"{c.stated:+.1f}" if c.stated is not None else "  -  "
        applied = f"{c.applied:+.1f}" if c.applied is not None else "  -  "
        print(f"  [{flags}] {c.run} t{c.turn:>2}  stated {stated}  applied {applied}  {c.line or '(no line)'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--since", help="keep runs whose name sorts at or after run-<since>")
    parser.add_argument("--per-turn", action="store_true", help="list every turn, not just the summary")
    parser.add_argument("--failures", action="store_true", help="list the turns that failed a check")
    parser.add_argument(
        "--all-runs",
        action="store_true",
        help="include runs that never write the line; by default they are skipped, "
        "because they predate the rule and would only dilute the rates",
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="report the anchored form and the older delta form as separate cohorts, "
        "which is how a change to the line is compared against what it replaced",
    )
    args = parser.parse_args()

    checks = collect(args.paths, args.since)
    if not checks:
        print("no turns found", file=sys.stderr)
        return 1

    accounted = {c.run for c in checks if c.line}
    skipped = sorted({c.run for c in checks} - accounted)
    if not args.all_runs and accounted:
        checks = [c for c in checks if c.run in accounted]
    if skipped and not args.all_runs:
        print(f"{len(skipped)} run(s) skipped: no SOVEREIGNTY line anywhere, so they predate the rule\n")

    if args.split:
        # A run belongs to whichever form its lines are written in, so that a
        # run started before the change is not half-counted against it.
        anchored_runs = {c.run for c in checks if c.anchored}
        cohorts = [
            ("anchored, `N last turn ... = M`", [c for c in checks if c.run in anchored_runs]),
            ("earlier form, terms then a delta", [c for c in checks if c.run not in anchored_runs]),
        ]
        for i, (label, cohort) in enumerate(c for c in cohorts if c[1]):
            if i:
                print()
            summarise(label, cohort, detail=True)
    else:
        summarise("all", checks, detail=True)

    if args.per_turn:
        print()
        show_turns(checks)
    elif args.failures:
        print()
        show_turns([c for c in checks if c.binds is False or c.arithmetic_ok is False or c.legal is False])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
