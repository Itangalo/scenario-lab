"""Measure what a scenario's event catalogue actually did across a set of runs.

The events step is the one step where the model composes the *candidate list*
itself: it is asked for every eligible event with a probability, and Python
then rolls the dice. That makes the artefacts worth reading directly, because
an event the model never listed and an event that was listed and did not fire
look identical in the results.

Three things are measured, and only the first is scored:

* **listing** -- the members of a declared exclusive family (`event_groups` in
  scenario.yaml) must all appear on the family's due turns, because the
  orchestrator resolves exactly one of them and an omitted member is a weight
  of zero: an outcome removed with nothing recording that it was removed. This
  has cost a scenario once already, when a three-way election group fired in 22
  of 30 runs under a condition saying it always happens. Ordinary events are
  conditional and are not scored -- the events prompt asks the model to omit
  any whose condition fails, so runs disagreeing about one is the design
  working. Their listing rates are reported as description, for the two ends:
  an event listed every turn is unconditional in practice, one listed almost
  never is not in play.

* **balance** -- how often each event is listed, how often it fires, and in how
  many runs it fires at all. An event that never fires across a corpus is a
  catalogue entry that costs tokens and does nothing; one that fires in nearly
  every run is scenery rather than an event.

* **effect** -- what the metrics did on the turns an event fired, against what
  they do on an ordinary turn of the same cohort. An event whose firing turns
  look like every other turn is inert, whatever its description says. This is a
  difference of means over few samples and is reported with its n; it says
  where to look, not what is true.

Runs are grouped by cohort, taken from the run config's name: the part after an
em dash where a scenario names variants that way, and otherwise the whole name.

Usage:

    python scripts/check_events.py scenarios/<scenario>/runs/run-*/
    python scripts/check_events.py scenarios/<scenario>/runs --since 20260903
    python scripts/check_events.py <runs...> --cohort acceleration --effects
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
    # Runs made before 1-event-evaluations.json existed record only what fired.
    # Their firings are real and feed the effect table; their listings are not
    # merely empty, they are unknown, and counting them as empty would report
    # every event in such a run as firing on every listing it ever had.
    listings_recorded: bool = True


@dataclass
class RunRecord:
    """One run: its cohort, its seed, and its turns in order."""

    path: Path
    cohort: str
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
    # Runs are grouped by cohort, which is whatever the run's config calls it.
    # A scenario that runs variants under one name conventionally writes them
    # as "Base name — Variant", so the part after an em dash is the cohort and
    # everything else is one cohort named for the scenario. The split is on the
    # em dash only: a variant called "Verification-bounded" is one name and
    # must not be broken at its hyphen.
    cohort = name.split("—")[-1].strip() if "—" in name else name.strip()

    run = RunRecord(
        path=run_dir,
        cohort=cohort,
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
        fired_path = turn_dir / "1-events.json"
        if evaluations_path.exists():
            evaluations = json.loads(evaluations_path.read_text(encoding="utf-8"))
        elif fired_path.exists():
            # Everything in this file fired; nothing here says what else was on
            # offer, so the turn carries firings and no listings.
            evaluations = [
                {**entry, "triggered": True}
                for entry in json.loads(fired_path.read_text(encoding="utf-8"))
                if isinstance(entry, dict)
            ]
            record.listings_recorded = False
        else:
            continue

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
            elif record.listings_recorded:
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


def scenario_sources(runs: list[RunRecord]) -> list[str]:
    """Where each run's scenario definition can be found.

    `scenario_source` is an absolute path recorded at run time and is missing
    from runs made before it was added; either way the definition may since
    have moved. The layout `scenarios/<name>/runs/run-*` puts it two levels up
    from the run, which is checked as a fallback so the report works on a
    scenario's own runs whatever produced them.
    """
    sources: list[str] = []
    for run in runs:
        candidates = []
        if run.scenario_source:
            candidates.append(Path(run.scenario_source))
        if run.path.parent.name == "runs":
            candidates.append(run.path.parent.parent)
        for candidate in candidates:
            if candidate.exists():
                sources.append(str(candidate))
                break
    return sorted(set(sources))


def load_catalogue(runs: list[RunRecord]) -> dict[str, Event]:
    """The union of the event catalogues the runs were played from.

    Arms patch the catalogue, so an id may carry different probability prose in
    cohorts. The union is what the listing and balance tables need; a
    per-cohort difference matters only for probabilities, which are not scored.
    """
    catalogue: dict[str, Event] = {}
    for source in scenario_sources(runs):
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
    for source in scenario_sources(runs):
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
# Listing: the one contract the framework itself declares
# ---------------------------------------------------------------------------

# A scenario's ordinary events are conditional: the events prompt asks the
# model to omit any whose condition does not hold this turn, so two runs
# disagreeing about one is the design working rather than a fault, and there is
# nothing here to score. The exception is a declared exclusive family. Its
# members are due on stated turns, the orchestrator resolves exactly one of
# them, and a member left out of the array is a weight of zero -- an outcome
# removed from the world with nothing recording that it was removed. That
# contract lives in scenario.yaml as `event_groups`, so it can be checked for
# any scenario without reading a word of anyone's prose.


@dataclass
class GroupGap:
    """A due turn where a mutually exclusive family was listed incomplete."""

    run: str
    cohort: str
    turn: int
    group_id: str
    missing: list[str]


def group_gaps(runs: list[RunRecord], groups: list[dict]) -> list[GroupGap]:
    """Due turns where not every member of an exclusive family was offered."""
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
                if not record.listings_recorded:
                    continue
                missing = [
                    member
                    for member in members
                    if member not in record.listed and member not in record.skipped
                ]
                if missing:
                    gaps.append(
                        GroupGap(run.path.name, run.cohort, record.turn, group.get("id", "?"), missing)
                    )
    return gaps


@dataclass
class ListingSpread:
    """How consistently an event was judged eligible."""

    event_id: str
    cohort: str
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
    """Listing rate per event per cohort, over the turns it could have been listed.

    This is description, not a verdict. An event is meant to come and go with
    the world, so a rate strictly between 0 and 1 is ordinary. What the number
    is for is the two ends: an event listed in essentially every turn is
    unconditional in practice whatever its condition says, and one listed almost
    never is a catalogue entry that is not in play.
    """
    spreads: list[ListingSpread] = []
    # Family members are due on stated turns and absent by design on the rest,
    # so their rate measures the calendar rather than a judgement.
    skip = set(exclude or ())
    by_cohort: dict[str, list[RunRecord]] = defaultdict(list)
    for run in runs:
        by_cohort[run.cohort].append(run)

    for cohort, cohort_runs in sorted(by_cohort.items()):
        for event_id, event in sorted(catalogue.items()):
            if event_id in skip:
                continue
            listed = 0
            eligible = 0
            for run in cohort_runs:
                for record in run.turns:
                    if record.parse_failure or record.pinned or not record.listings_recorded:
                        continue
                    if event_id in record.skipped:
                        continue
                    if not event.can_repeat and run.fired_before(event_id, record.turn):
                        continue
                    eligible += 1
                    if event_id in record.listed:
                        listed += 1
            if eligible:
                spreads.append(ListingSpread(event_id, cohort, listed, eligible))
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
            if record.pinned or not record.listings_recorded:
                # A pinned list is not a judgement about what could happen, and
                # a turn with no candidate list recorded cannot say what its
                # firings were drawn from.
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

    The baseline is per cohort, because cohorts may move the metrics at
    different speeds and pooling them would credit an event with its cohort's
    trend.
    """
    by_cohort_metric: dict[tuple[str, str], list[float]] = defaultdict(list)
    firing_turns: list[tuple[str, str, dict[str, float]]] = []

    for run in runs:
        deltas = metric_deltas(run)
        for record in sorted(run.turns, key=lambda t: t.turn):
            turn_deltas = deltas.get(record.turn)
            if not turn_deltas:
                continue
            for metric, delta in turn_deltas.items():
                by_cohort_metric[(run.cohort, metric)].append(delta)
            for event_id in record.fired:
                if event_id in catalogue:
                    firing_turns.append((event_id, run.cohort, turn_deltas))

    baseline = {
        key: statistics.fmean(values) for key, values in by_cohort_metric.items() if values
    }

    excess: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    firings: dict[str, int] = defaultdict(int)
    for event_id, cohort, turn_deltas in firing_turns:
        firings[event_id] += 1
        for metric, delta in turn_deltas.items():
            excess[event_id][metric].append(delta - baseline.get((cohort, metric), 0.0))

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
    cohorts = sorted({run.cohort for run in runs})
    turns = sum(len(run.turns) for run in runs)
    print(f"{len(runs)} runs, {turns} turns, {len(catalogue)} catalogue events")
    for cohort in cohorts:
        cohort_runs = [r for r in runs if r.cohort == cohort]
        print(f"  {cohort}: {len(cohort_runs)} runs")

    legacy = [
        (run.path.name, r.turn) for run in runs for r in run.turns if not r.listings_recorded
    ]
    if legacy:
        print(
            f"\n{len(legacy)} turns predate `1-event-evaluations.json` and record only what "
            "fired. Their firings feed the effect table; their listings are unknown, so they "
            "are left out of listing and balance rather than counted as empty."
        )

    parse_failures = [
        (run.path.name, t.turn) for run in runs for t in run.turns if t.parse_failure
    ]
    if parse_failures:
        print(f"\n{len(parse_failures)} turns lost the events step to a parse failure:")
        for name, turn in parse_failures:
            print(f"  {name} turn {turn}")

    # -- listing ------------------------------------------------------------
    groups = load_groups(runs)
    print("\n## Listing\n")
    if not groups:
        print("This scenario declares no exclusive event families, so nothing here is scored.")
    else:
        due = {g["id"]: g.get("due_turns") for g in groups}
        print(f"Exclusive families and their due turns: {due}")
        gaps = group_gaps(runs, groups)
        if gaps:
            print(f"\n**{len(gaps)} due turns listed the family incomplete:**\n")
            for gap in gaps[:20]:
                print(f"  {gap.run} ({gap.cohort}) turn {gap.turn}: missing {', '.join(gap.missing)}")
        else:
            print("\nEvery due turn listed every member.")

    family_members = {m for group in groups for m in group.get("members", [])}
    spreads = listing_spread(runs, catalogue, exclude=family_members)
    unconditional = [s for s in spreads if s.turns >= 20 and s.rate >= 0.98]
    rare = [s for s in spreads if s.turns >= 20 and s.rate <= 0.10]
    if unconditional or rare:
        print("\n### Events at the ends of their listing range\n")
        print(
            "An event is meant to come and go with the world, so a middling rate "
            "is ordinary. These are the two ends.\n"
        )
        print("| event | cohort | listed / eligible turns | rate |")
        print("|---|---|---|---|")
        for spread in sorted(unconditional + rare, key=lambda s: (-s.rate, s.event_id)):
            print(
                f"| `{spread.event_id}` | {spread.cohort} | {spread.listed}/{spread.turns} | "
                f"{percent(spread.rate)} |"
            )

    # -- balance ------------------------------------------------------------
    stats = balance(runs, catalogue)
    listing_turns = sum(
        1
        for run in runs
        for r in run.turns
        if r.listings_recorded and not (r.pinned or r.parse_failure)
    )
    print("\n## Balance\n")
    if not listing_turns:
        print(
            "No turn in this corpus recorded a candidate list, so there is nothing to "
            "count. What each event did on the turns it fired is still in the effect table."
        )
        if not show_effects:
            return

    if listing_turns:
        print("| event | listings | fires | per listing | runs touched | mean p | distinct p |")
        print("|---|---|---|---|---|---|---|")
    for stat in sorted(stats.values(), key=lambda s: (-s.firings, s.event_id)):
        if not listing_turns:
            break
        if not show_all and stat.listings == 0 and stat.firings == 0:
            continue
        print(
            f"| `{stat.event_id}` | {stat.listings} | {stat.firings} | "
            f"{percent(stat.fire_rate)} | {percent(stat.run_rate)} | "
            f"{stat.mean_probability:.3f} | {stat.distinct_probabilities} |"
        )

    never_listed = sorted(s.event_id for s in stats.values() if s.listings == 0)
    if never_listed and listing_turns:
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
    parser.add_argument("--cohort", help="keep only runs whose cohort name contains this, case-insensitive")
    parser.add_argument("--effects", action="store_true", help="also report per-event metric effects")
    parser.add_argument("--all", action="store_true", help="include events with no listings in the balance table")
    args = parser.parse_args()

    runs = collect(args.paths, args.since)
    if args.cohort:
        runs = [run for run in runs if args.cohort.lower() in run.cohort.lower()]
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
