"""Check whether the event catalogue is being played the way it is written.

The events step is the one step where the model composes the *candidate list*
itself: it is asked for every eligible event with a probability, and Python
then rolls the dice. An event the model does not list is not a low roll, it is
a possibility that was silently removed, and the artefacts record it exactly
the same way as an event that was listed and did not fire. This has already
cost this scenario once -- the 2028 election group fired in only 22 of 30 runs
under a condition saying it always happens.

Three things are measured, one per phase 1 event gate:

* **listing** -- at a given turn, an event is either eligible or it is not, and
  eligibility is a property of the world, not of the draw. So an event listed
  in some runs of an arm at turn t and absent from others, where nothing in the
  run's own record disqualifies it, is a candidate list with a hole in it. No
  condition prose is parsed: the corpus supplies its own expectation, since one
  run listing the event at that turn establishes that it was listable.

* **balance** -- how often each event is listed, how often it fires, and in how
  many runs it fires at all. An event that never fires across the corpus is a
  catalogue entry that costs tokens and does nothing; one that fires in nearly
  every run is scenery rather than an event.

* **effect** -- what the metrics did on the turns an event fired, against what
  they do on an ordinary turn of the same arm. An event whose firing turns look
  like every other turn is inert, whatever its description says. This is a
  difference of means over few samples and is reported with its n; it says
  where to look, not what is true.

Usage:

    python scripts/check_events.py scenarios/europe-2032/runs/run-*/
    python scripts/check_events.py scenarios/europe-2032/runs --since 20260903
    python scripts/check_events.py <runs...> --arm acceleration --effects
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scenario_lab.loader import load_scenario  # noqa: E402
from scenario_lab.models import Event  # noqa: E402


# A difference of means smaller than this, on every metric, is what "the world
# did not notice" looks like. The metrics run 0-100 and an ordinary turn moves
# them by single digits, so one point is generous rather than strict.
INERT_THRESHOLD = 1.0

# Below this many firings a difference of means is not worth printing as
# evidence of anything.
MIN_FIRINGS_FOR_EFFECT = 4


@dataclass
class TurnRecord:
    """One turn of one run, as the event artefacts recorded it."""

    turn: int
    listed: dict[str, float] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    skipped: dict[str, str] = field(default_factory=dict)
    emergent: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)
    parse_failure: bool = False
    # A turn whose event list was pinned (story/pin-turn-1.py) never asked the
    # model for candidates, so it can be charged with neither an omission nor a
    # listing. Its metric movements are real and still count towards effects.
    pinned: bool = False


@dataclass
class RunRecord:
    """One run: its arm, its seed, and its turns in order."""

    path: Path
    arm: str
    seed: int | None
    scenario_source: str | None
    turns: list[TurnRecord] = field(default_factory=list)

    def fired_before(self, event_id: str, turn: int) -> bool:
        return any(event_id in t.fired for t in self.turns if t.turn < turn)


def read_run(run_dir: Path) -> RunRecord | None:
    """Read one run directory. Returns None if it holds no turns."""
    config_path = run_dir / "config.json"
    if not config_path.exists():
        return None
    config = json.loads(config_path.read_text(encoding="utf-8"))

    name = config.get("name") or run_dir.name
    # "Europe 2032 — Acceleration" -> "Acceleration", on the em dash only:
    # "Verification-bounded" is one arm name and must not be split on its
    # hyphen. A scenario that names no arm keeps its whole name, which groups
    # its runs together.
    arm = name.split("—")[-1].strip() if "—" in name else name.strip()

    run = RunRecord(
        path=run_dir,
        arm=arm,
        seed=config.get("random_seed"),
        scenario_source=config.get("scenario_source"),
    )

    for turn_dir in sorted(run_dir.glob("turn-*")):
        try:
            turn = int(turn_dir.name.split("-")[1])
        except (IndexError, ValueError):
            continue
        record = TurnRecord(turn=turn)

        evaluations_path = turn_dir / "1-event-evaluations.json"
        if not evaluations_path.exists():
            continue
        evaluations = json.loads(evaluations_path.read_text(encoding="utf-8"))

        for entry in evaluations:
            if not isinstance(entry, dict):
                continue
            if entry.get("parse_failure"):
                record.parse_failure = True
                continue
            if entry.get("pinned"):
                record.pinned = True
            event_id = entry.get("id")
            if not isinstance(event_id, str):
                continue
            probability = entry.get("probability")
            probability = float(probability) if isinstance(probability, (int, float)) else 0.0
            if entry.get("skipped"):
                record.skipped[event_id] = str(entry["skipped"])
            elif entry.get("emergent"):
                record.emergent[event_id] = probability
            else:
                record.listed[event_id] = probability
            if entry.get("triggered"):
                record.fired.add(event_id)

        metrics_path = turn_dir / "4-metrics.json"
        if metrics_path.exists():
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            record.metrics = {
                key: float(value)
                for key, value in metrics.items()
                if isinstance(value, (int, float))
            }

        run.turns.append(record)

    return run if run.turns else None


def collect(paths: list[Path], since: str | None) -> list[RunRecord]:
    """Read every run under the given paths, newest-name-last."""
    candidates: list[Path] = []
    for path in paths:
        if (path / "config.json").exists():
            candidates.append(path)
        else:
            candidates.extend(sorted(p for p in path.glob("run-*") if p.is_dir()))

    runs: list[RunRecord] = []
    for candidate in sorted(set(candidates)):
        if since and candidate.name < f"run-{since}":
            continue
        run = read_run(candidate)
        if run:
            runs.append(run)
    return runs


def load_catalogue(runs: list[RunRecord]) -> dict[str, Event]:
    """The union of the event catalogues the runs were played from.

    Arms patch the catalogue, so an id may carry different probability prose in
    different arms. The union is what the listing and balance tables need; the
    per-arm difference matters only for the probability column, which is
    reported per arm.
    """
    catalogue: dict[str, Event] = {}
    for source in sorted({run.scenario_source for run in runs if run.scenario_source}):
        if not Path(source).exists():
            continue
        try:
            scenario = load_scenario(source)
        except Exception as exc:  # a moved or renamed scenario should not stop the report
            print(f"  (could not load {source}: {exc})", file=sys.stderr)
            continue
        for event in scenario.events:
            catalogue.setdefault(event.id, event)
    return catalogue


def load_groups(runs: list[RunRecord]) -> list[dict]:
    """Mutually exclusive event families, as the scenarios declare them."""
    groups: dict[str, dict] = {}
    for source in sorted({run.scenario_source for run in runs if run.scenario_source}):
        if not Path(source).exists():
            continue
        try:
            scenario = load_scenario(source)
        except Exception:
            continue
        for group in getattr(scenario.config, "event_groups", []) or []:
            entry = {
                "id": getattr(group, "id", None),
                "members": list(getattr(group, "members", []) or []),
                "due_turns": list(getattr(group, "due_turns", []) or []),
            }
            if entry["id"]:
                groups.setdefault(entry["id"], entry)
    return list(groups.values())


# ---------------------------------------------------------------------------
# Listing: what the catalogue requires, and what the runs did
# ---------------------------------------------------------------------------

# The events prompt divides the catalogue in two, and the two halves need
# different measurements. Most entries are conditional: the model judges each
# turn whether the condition holds, and two runs of the same arm may honestly
# disagree because their worlds differ. A handful are not: their Condition says
# "Always eligible", the prompt names them, and omitting one is an error
# regardless of the world. Only the second kind can be scored.
ALWAYS_ELIGIBLE = "always eligible"


def mandatory_ids(catalogue: dict[str, Event]) -> list[str]:
    """Events the catalogue declares must be listed in every turn."""
    return sorted(
        event_id
        for event_id, event in catalogue.items()
        if ALWAYS_ELIGIBLE in (event.condition or "").lower()
    )


@dataclass
class Omission:
    """A turn where a mandatory event was neither listed nor skipped."""

    run: str
    arm: str
    turn: int
    event_id: str


def mandatory_omissions(
    runs: list[RunRecord], catalogue: dict[str, Event]
) -> list[Omission]:
    """Turns where an always-eligible event simply was not there.

    A Python-side skip is not an omission: `ai_investment_collapse` has fired
    and cannot repeat, or an eligibility expression was false, and the artefact
    says so. What is counted is silence -- the event absent from the array with
    no record of why, which is indistinguishable in the results from an event
    that was offered and did not fire.
    """
    required = mandatory_ids(catalogue)
    omissions: list[Omission] = []
    for run in runs:
        for record in run.turns:
            if record.parse_failure or record.pinned:
                continue
            for event_id in required:
                if event_id in record.listed or event_id in record.skipped:
                    continue
                omissions.append(Omission(run.path.name, run.arm, record.turn, event_id))
    return omissions


@dataclass
class GroupGap:
    """A due turn where a mutually exclusive family was listed incomplete."""

    run: str
    arm: str
    turn: int
    group_id: str
    missing: list[str]


def group_gaps(runs: list[RunRecord], groups: list[dict]) -> list[GroupGap]:
    """Due turns where not every member of an exclusive family was offered.

    An omitted member is a weight of zero: the outcome is removed from the
    world without anything recording that it was removed. This is the failure
    the 2028 election machinery was found to have.
    """
    gaps: list[GroupGap] = []
    for group in groups:
        members = list(group.get("members", []))
        due = set(group.get("due_turns", []) or [])
        if not members or not due:
            continue
        for run in runs:
            for record in run.turns:
                if record.turn not in due or record.parse_failure or record.pinned:
                    continue
                missing = [
                    member
                    for member in members
                    if member not in record.listed and member not in record.skipped
                ]
                if missing:
                    gaps.append(
                        GroupGap(run.path.name, run.arm, record.turn, group.get("id", "?"), missing)
                    )
    return gaps


@dataclass
class ListingSpread:
    """How consistently a conditional event was judged eligible."""

    event_id: str
    arm: str
    listed: int
    turns: int

    @property
    def rate(self) -> float:
        return self.listed / self.turns if self.turns else 0.0


def listing_spread(
    runs: list[RunRecord],
    catalogue: dict[str, Event],
    exclude: set[str] | None = None,
) -> list[ListingSpread]:
    """Listing rate per conditional event per arm, over eligible run-turns.

    This is description, not a verdict. A conditional event is meant to come
    and go with the world, so a rate strictly between 0 and 1 is the design
    working. What the number is for is the two ends: an event listed in
    essentially every turn is unconditional in practice, and one listed almost
    never is a catalogue entry that is not in play.
    """
    spreads: list[ListingSpread] = []
    # Family members are due on stated turns and absent by design on the rest,
    # so their rate measures the calendar rather than a judgement.
    required = set(mandatory_ids(catalogue)) | set(exclude or ())
    by_arm: dict[str, list[RunRecord]] = defaultdict(list)
    for run in runs:
        by_arm[run.arm].append(run)

    for arm, arm_runs in sorted(by_arm.items()):
        for event_id, event in sorted(catalogue.items()):
            if event_id in required:
                continue
            listed = 0
            eligible = 0
            for run in arm_runs:
                for record in run.turns:
                    if record.parse_failure or record.pinned:
                        continue
                    if event_id in record.skipped:
                        continue
                    if not event.can_repeat and run.fired_before(event_id, record.turn):
                        continue
                    eligible += 1
                    if event_id in record.listed:
                        listed += 1
            if eligible:
                spreads.append(ListingSpread(event_id, arm, listed, eligible))
    return spreads


# ---------------------------------------------------------------------------
# Balance: what the catalogue actually does
# ---------------------------------------------------------------------------


@dataclass
class EventStats:
    event_id: str
    listings: int = 0
    firings: int = 0
    runs_fired: int = 0
    runs_total: int = 0
    probabilities: list[float] = field(default_factory=list)

    @property
    def fire_rate(self) -> float:
        return self.firings / self.listings if self.listings else 0.0

    @property
    def run_rate(self) -> float:
        return self.runs_fired / self.runs_total if self.runs_total else 0.0

    @property
    def expected(self) -> float:
        return sum(self.probabilities)

    @property
    def mean_probability(self) -> float:
        return statistics.fmean(self.probabilities) if self.probabilities else 0.0

    @property
    def distinct_probabilities(self) -> int:
        return len({round(p, 4) for p in self.probabilities})


def balance(runs: list[RunRecord], catalogue: dict[str, Event]) -> dict[str, EventStats]:
    """Listings, firings and probability spread per catalogue event."""
    stats = {event_id: EventStats(event_id) for event_id in catalogue}
    for run in runs:
        fired_here: set[str] = set()
        for record in run.turns:
            if record.pinned:
                # A pinned list is not a judgement about what could happen.
                continue
            for event_id, probability in record.listed.items():
                if event_id not in stats:
                    continue
                stats[event_id].listings += 1
                stats[event_id].probabilities.append(probability)
            for event_id in record.fired:
                if event_id in stats:
                    stats[event_id].firings += 1
                    fired_here.add(event_id)
        for event_id, stat in stats.items():
            stat.runs_total += 1
            if event_id in fired_here:
                stat.runs_fired += 1
    return stats


# ---------------------------------------------------------------------------
# Effect: what fired events did to the metrics
# ---------------------------------------------------------------------------


def metric_deltas(run: RunRecord) -> dict[int, dict[str, float]]:
    """Per-turn change in each metric, keyed by turn."""
    deltas: dict[int, dict[str, float]] = {}
    previous: dict[str, float] = {}
    for record in sorted(run.turns, key=lambda t: t.turn):
        if previous:
            deltas[record.turn] = {
                key: value - previous[key]
                for key, value in record.metrics.items()
                if key in previous
            }
        previous = record.metrics or previous
    return deltas


def effect_profiles(
    runs: list[RunRecord], catalogue: dict[str, Event]
) -> dict[str, tuple[int, dict[str, float]]]:
    """For each event, how its firing turns differ from ordinary turns.

    The baseline is per arm, because the arms move the metrics at different
    speeds and pooling them would credit an event with its arm's trend.
    """
    by_arm_metric: dict[tuple[str, str], list[float]] = defaultdict(list)
    firing_turns: list[tuple[str, str, dict[str, float]]] = []

    for run in runs:
        deltas = metric_deltas(run)
        for record in sorted(run.turns, key=lambda t: t.turn):
            turn_deltas = deltas.get(record.turn)
            if not turn_deltas:
                continue
            for metric, delta in turn_deltas.items():
                by_arm_metric[(run.arm, metric)].append(delta)
            for event_id in record.fired:
                if event_id in catalogue:
                    firing_turns.append((event_id, run.arm, turn_deltas))

    baseline = {
        key: statistics.fmean(values) for key, values in by_arm_metric.items() if values
    }

    excess: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    firings: dict[str, int] = defaultdict(int)
    for event_id, arm, turn_deltas in firing_turns:
        firings[event_id] += 1
        for metric, delta in turn_deltas.items():
            excess[event_id][metric].append(delta - baseline.get((arm, metric), 0.0))

    profiles: dict[str, tuple[int, dict[str, float]]] = {}
    for event_id, metrics in excess.items():
        profiles[event_id] = (
            firings[event_id],
            {metric: statistics.fmean(values) for metric, values in metrics.items() if values},
        )
    return profiles


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def percent(value: float) -> str:
    return f"{value * 100:.0f}%"


def report(
    runs: list[RunRecord],
    catalogue: dict[str, Event],
    show_effects: bool,
    show_all: bool,
) -> None:
    arms = sorted({run.arm for run in runs})
    turns = sum(len(run.turns) for run in runs)
    print(f"{len(runs)} runs, {turns} turns, {len(catalogue)} catalogue events")
    for arm in arms:
        arm_runs = [r for r in runs if r.arm == arm]
        seeds = sorted(r.seed for r in arm_runs if r.seed is not None)
        span = f"{seeds[0]}-{seeds[-1]}" if seeds else "no seeds"
        print(f"  {arm}: {len(arm_runs)} runs ({span})")

    parse_failures = [
        (run.path.name, t.turn) for run in runs for t in run.turns if t.parse_failure
    ]
    if parse_failures:
        print(f"\n{len(parse_failures)} turns lost the events step to a parse failure:")
        for name, turn in parse_failures:
            print(f"  {name} turn {turn}")

    # -- listing ------------------------------------------------------------
    required = mandatory_ids(catalogue)
    omissions = mandatory_omissions(runs, catalogue)
    print("\n## Listing\n")
    print(
        f"{len(required)} events are declared always eligible and must appear in "
        f"every turn's array: " + ", ".join(f"`{e}`" for e in required)
    )
    if not omissions:
        print("\nNone was ever missing.")
    else:
        judged_turns = sum(
            1 for run in runs for t in run.turns if not (t.parse_failure or t.pinned)
        )
        turns_at_risk = judged_turns * len(required)
        print(
            f"\n**{len(omissions)} of {turns_at_risk} required listings are missing** "
            f"({percent(len(omissions) / turns_at_risk)}), with no skip recorded:\n"
        )
        by_event: dict[str, list[Omission]] = defaultdict(list)
        for omission in omissions:
            by_event[omission.event_id].append(omission)
        print("| event | missing | turns | arms |")
        print("|---|---|---|---|")
        for event_id, items in sorted(by_event.items(), key=lambda kv: -len(kv[1])):
            turns = sorted({item.turn for item in items})
            turn_text = ", ".join(str(t) for t in turns[:6]) + (" ..." if len(turns) > 6 else "")
            arms = ", ".join(sorted({item.arm for item in items}))
            print(f"| `{event_id}` | {len(items)} | {turn_text} | {arms} |")

        by_turn: dict[int, int] = defaultdict(int)
        for omission in omissions:
            by_turn[omission.turn] += 1
        worst = sorted(by_turn.items(), key=lambda kv: -kv[1])[:5]
        print(
            "\nWorst turns: "
            + ", ".join(f"turn {turn} ({count})" for turn, count in worst)
        )

    groups = load_groups(runs)
    gaps = group_gaps(runs, groups)
    if groups:
        due = {g["id"]: g.get("due_turns") for g in groups}
        print(f"\nExclusive families and their due turns: {due}")
        if gaps:
            print(f"\n**{len(gaps)} due turns listed the family incomplete:**\n")
            for gap in gaps[:20]:
                print(f"  {gap.run} ({gap.arm}) turn {gap.turn}: missing {', '.join(gap.missing)}")
        else:
            print("Every due turn listed every member.")

    family_members = {m for group in groups for m in group.get("members", [])}
    spreads = listing_spread(runs, catalogue, exclude=family_members)
    unconditional = [s for s in spreads if s.turns >= 20 and s.rate >= 0.98]
    rare = [s for s in spreads if s.turns >= 20 and s.rate <= 0.10]
    if unconditional or rare:
        print("\n### Conditional events at the ends of their range\n")
        print(
            "Conditional events are meant to come and go, so a middling rate is "
            "the design working. These are the two ends.\n"
        )
        print("| event | arm | listed / eligible turns | rate |")
        print("|---|---|---|---|")
        for spread in sorted(unconditional + rare, key=lambda s: (-s.rate, s.event_id)):
            print(
                f"| `{spread.event_id}` | {spread.arm} | {spread.listed}/{spread.turns} | "
                f"{percent(spread.rate)} |"
            )

    # -- balance ------------------------------------------------------------
    stats = balance(runs, catalogue)
    print("\n## Balance\n")
    print("| event | listings | fires | per listing | runs touched | mean p | distinct p |")
    print("|---|---|---|---|---|---|---|")
    for stat in sorted(stats.values(), key=lambda s: (-s.firings, s.event_id)):
        if not show_all and stat.listings == 0 and stat.firings == 0:
            continue
        print(
            f"| `{stat.event_id}` | {stat.listings} | {stat.firings} | "
            f"{percent(stat.fire_rate)} | {percent(stat.run_rate)} | "
            f"{stat.mean_probability:.3f} | {stat.distinct_probabilities} |"
        )

    never_listed = sorted(s.event_id for s in stats.values() if s.listings == 0)
    if never_listed:
        print(f"\n**Never listed at all** ({len(never_listed)}): " + ", ".join(f"`{e}`" for e in never_listed))

    never_fired = sorted(
        (s for s in stats.values() if s.listings and not s.firings),
        key=lambda s: -s.expected,
    )
    if never_fired:
        print(f"\n**Listed but never fired** ({len(never_fired)}):\n")
        print("| event | listings | expected fires | mean p |")
        print("|---|---|---|---|")
        for stat in never_fired:
            print(
                f"| `{stat.event_id}` | {stat.listings} | {stat.expected:.1f} | "
                f"{stat.mean_probability:.3f} |"
            )

    flat = sorted(
        s.event_id
        for s in stats.values()
        if s.listings >= 10 and s.distinct_probabilities == 1
    )
    if flat:
        print(
            f"\n**One probability in every turn it was listed** ({len(flat)}): "
            + ", ".join(f"`{e}`" for e in flat)
            + " — the modifiers in these entries never moved the figure."
        )

    # -- effect -------------------------------------------------------------
    if not show_effects:
        return
    profiles = effect_profiles(runs, catalogue)
    print("\n## Effect\n")
    print(
        "Mean metric change on the turns an event fired, minus the mean change "
        "over all turns. Few samples; read the n."
    )
    print("\n| event | fires | largest differences |")
    print("|---|---|---|")
    inert: list[str] = []
    for event_id, (n, differences) in sorted(profiles.items(), key=lambda kv: -kv[1][0]):
        ranked = sorted(differences.items(), key=lambda kv: -abs(kv[1]))[:3]
        shown = ", ".join(f"{metric} {delta:+.1f}" for metric, delta in ranked)
        print(f"| `{event_id}` | {n} | {shown} |")
        if n >= MIN_FIRINGS_FOR_EFFECT and all(
            abs(delta) < INERT_THRESHOLD for delta in differences.values()
        ):
            inert.append(event_id)
    if inert:
        print(
            f"\n**No metric moved differently on their firing turns** ({len(inert)}): "
            + ", ".join(f"`{e}`" for e in inert)
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--since", help="keep runs whose name sorts at or after run-<since>")
    parser.add_argument("--arm", help="keep only runs whose arm name contains this, case-insensitive")
    parser.add_argument("--effects", action="store_true", help="also report per-event metric effects")
    parser.add_argument("--all", action="store_true", help="include events with no listings in the balance table")
    args = parser.parse_args()

    runs = collect(args.paths, args.since)
    if args.arm:
        runs = [run for run in runs if args.arm.lower() in run.arm.lower()]
    if not runs:
        print("No runs with turn data found.", file=sys.stderr)
        return 1

    catalogue = load_catalogue(runs)
    if not catalogue:
        print("No event catalogue could be loaded for these runs.", file=sys.stderr)
        return 1

    report(runs, catalogue, show_effects=args.effects, show_all=args.all)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
