"""Pin the event checker's readings against runs whose answer is known.

`check_events.py` is a measuring instrument, and this repo has already been
told three different wrong answers by one that looked authoritative. These
tests build small run directories where the right answer is arithmetic, so a
regression in the reader shows up as a wrong number rather than as a plausible
one.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_events  # noqa: E402
from scenario_lab.models import Event  # noqa: E402


def write_run(
    root: Path,
    name: str,
    arm: str,
    turns: list[dict],
    seed: int = 1,
) -> Path:
    """Build a run directory from a compact description of its turns.

    Each turn is {"listed": {id: p}, "fired": [ids], "skipped": {id: why},
    "emergent": {id: p}, "metrics": {...}} -- every key optional.
    """
    run_dir = root / name
    run_dir.mkdir(parents=True)
    (run_dir / "config.json").write_text(
        json.dumps({"name": f"Test — {arm}", "random_seed": seed}), encoding="utf-8"
    )
    for index, turn in enumerate(turns, start=1):
        turn_dir = run_dir / f"turn-{index:02d}"
        turn_dir.mkdir()
        evaluations = []
        for event_id, probability in turn.get("listed", {}).items():
            evaluations.append(
                {
                    "id": event_id,
                    "probability": probability,
                    "triggered": event_id in turn.get("fired", []),
                }
            )
        for event_id, probability in turn.get("emergent", {}).items():
            evaluations.append(
                {
                    "id": event_id,
                    "probability": probability,
                    "emergent": True,
                    "triggered": event_id in turn.get("fired", []),
                }
            )
        for event_id, why in turn.get("skipped", {}).items():
            evaluations.append(
                {"id": event_id, "probability": 0.0, "skipped": why, "triggered": False}
            )
        if turn.get("pinned"):
            for entry in evaluations:
                entry["pinned"] = True
        if turn.get("parse_failure"):
            evaluations = [{"parse_failure": True, "triggered": False}]
        (turn_dir / "1-event-evaluations.json").write_text(
            json.dumps(evaluations), encoding="utf-8"
        )
        if "metrics" in turn:
            (turn_dir / "4-metrics.json").write_text(
                json.dumps(turn["metrics"]), encoding="utf-8"
            )
    return run_dir


def catalogue(*ids: str, repeat: bool = True) -> dict[str, Event]:
    return {
        event_id: Event(
            id=event_id,
            description="",
            condition="",
            probability="10%",
            can_repeat=repeat,
        )
        for event_id in ids
    }


# ---------------------------------------------------------------------------
# Reading a run
# ---------------------------------------------------------------------------


def test_arm_name_survives_its_own_hyphen(tmp_path):
    """"Verification-bounded" is one arm, not an arm called "bounded"."""
    write_run(tmp_path, "run-a", "Verification-bounded", [{"listed": {"e": 0.1}}])
    (runs) = check_events.collect([tmp_path], since=None)
    assert [run.arm for run in runs] == ["Verification-bounded"]


def test_skipped_and_emergent_are_not_counted_as_listings(tmp_path):
    """Only what the model actually offered as a catalogue event is a listing."""
    write_run(
        tmp_path,
        "run-a",
        "A",
        [
            {
                "listed": {"real": 0.2},
                "skipped": {"spent": "Event already occurred and cannot repeat"},
                "emergent": {"emergent_thing": 0.3},
                "fired": ["real", "emergent_thing"],
            }
        ],
    )
    runs = check_events.collect([tmp_path], since=None)
    stats = check_events.balance(runs, catalogue("real", "spent"))
    assert stats["real"].listings == 1
    assert stats["real"].firings == 1
    assert stats["spent"].listings == 0
    # The emergent proposal is not a catalogue entry and must not appear as one.
    assert "emergent_thing" not in stats


def test_parse_failure_turn_is_reported_not_read_as_an_empty_world(tmp_path):
    write_run(tmp_path, "run-a", "A", [{"parse_failure": True}])
    runs = check_events.collect([tmp_path], since=None)
    assert runs[0].turns[0].parse_failure
    assert runs[0].turns[0].listed == {}


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------


def mandatory_catalogue(*ids: str, repeat: bool = True) -> dict[str, Event]:
    """A catalogue whose events carry the always-eligible declaration."""
    cat = catalogue(*ids, repeat=repeat)
    for event in cat.values():
        event.condition = "Always eligible; list this event every turn."
    return cat


def test_a_missing_mandatory_event_is_an_omission(tmp_path):
    """An always-eligible event absent from a turn is counted, once per turn."""
    write_run(
        tmp_path,
        "run-a",
        "A",
        [{"listed": {"must": 0.1}}, {"listed": {}}, {"listed": {"must": 0.1}}],
    )
    runs = check_events.collect([tmp_path], since=None)

    omissions = check_events.mandatory_omissions(runs, mandatory_catalogue("must"))

    assert [(o.turn, o.event_id) for o in omissions] == [(2, "must")]


def test_a_recorded_skip_is_not_an_omission(tmp_path):
    """Python skipping a spent one-shot is a reason, and the artefact holds it."""
    write_run(
        tmp_path,
        "run-a",
        "A",
        [
            {"listed": {"must": 0.9}, "fired": ["must"]},
            {"skipped": {"must": "Event already occurred and cannot repeat"}},
        ],
    )
    runs = check_events.collect([tmp_path], since=None)

    assert check_events.mandatory_omissions(runs, mandatory_catalogue("must", repeat=False)) == []


def test_conditional_events_are_never_counted_as_omissions(tmp_path):
    """Absence is how a conditional event says its condition did not hold."""
    write_run(tmp_path, "run-a", "A", [{"listed": {}}, {"listed": {}}])
    runs = check_events.collect([tmp_path], since=None)

    assert check_events.mandatory_omissions(runs, catalogue("conditional")) == []


def test_a_parse_failure_turn_is_not_charged_as_an_omission(tmp_path):
    """The events step produced nothing at all; that is its own finding."""
    write_run(tmp_path, "run-a", "A", [{"parse_failure": True}])
    runs = check_events.collect([tmp_path], since=None)

    assert check_events.mandatory_omissions(runs, mandatory_catalogue("must")) == []


def test_a_pinned_turn_is_charged_with_nothing(tmp_path):
    """A pinned opening never asked for candidates, so it omitted nothing."""
    write_run(
        tmp_path,
        "run-a",
        "A",
        [{"listed": {"fixed": 1.0}, "fired": ["fixed"], "pinned": True}],
    )
    runs = check_events.collect([tmp_path], since=None)
    cat = mandatory_catalogue("must")
    cat.update(catalogue("fixed"))

    assert runs[0].turns[0].pinned
    assert check_events.mandatory_omissions(runs, cat) == []
    # Nor is the pinned event itself a listing anyone chose to make.
    assert check_events.balance(runs, cat)["fixed"].listings == 0


def test_an_incomplete_exclusive_family_is_a_gap(tmp_path):
    """One outcome left out of a due turn is a future removed without a record."""
    write_run(
        tmp_path,
        "run-a",
        "A",
        [{"listed": {}}, {"listed": {"win": 0.5, "lose": 0.5}, "fired": ["win"]}],
    )
    runs = check_events.collect([tmp_path], since=None)
    groups = [{"id": "vote", "members": ["win", "lose", "draw"], "due_turns": [2]}]

    gaps = check_events.group_gaps(runs, groups)

    assert [(g.turn, g.missing) for g in gaps] == [(2, ["draw"])]


def test_a_family_is_only_checked_on_its_due_turns(tmp_path):
    write_run(tmp_path, "run-a", "A", [{"listed": {}}, {"listed": {"win": 0.5, "lose": 0.5, "draw": 0.1}}])
    runs = check_events.collect([tmp_path], since=None)
    groups = [{"id": "vote", "members": ["win", "lose", "draw"], "due_turns": [2]}]

    assert check_events.group_gaps(runs, groups) == []


def test_listing_spread_measures_conditional_events_only(tmp_path):
    """The spread describes the events whose absence is a judgement."""
    cat = catalogue("conditional")
    cat.update(mandatory_catalogue("must"))
    write_run(
        tmp_path,
        "run-a",
        "A",
        [{"listed": {"must": 0.1, "conditional": 0.1}}, {"listed": {"must": 0.1}}],
    )
    runs = check_events.collect([tmp_path], since=None)

    spreads = check_events.listing_spread(runs, cat)

    assert [(s.event_id, s.listed, s.turns) for s in spreads] == [("conditional", 1, 2)]


def test_listing_spread_stops_counting_a_spent_one_shot(tmp_path):
    """Turns after a non-repeating event fired are not turns it was skipped in."""
    write_run(
        tmp_path,
        "run-a",
        "A",
        [
            {"listed": {"one_shot": 0.9}, "fired": ["one_shot"]},
            {"listed": {}},
            {"listed": {}},
        ],
    )
    runs = check_events.collect([tmp_path], since=None)

    spreads = check_events.listing_spread(runs, catalogue("one_shot", repeat=False))

    assert [(s.listed, s.turns) for s in spreads] == [(1, 1)]


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------


def test_balance_counts_runs_touched_not_just_firings(tmp_path):
    """Ten firings in one run is a different fact from one firing in ten."""
    write_run(
        tmp_path,
        "run-a",
        "A",
        [
            {"listed": {"noisy": 0.5}, "fired": ["noisy"]},
            {"listed": {"noisy": 0.5}, "fired": ["noisy"]},
        ],
    )
    write_run(tmp_path, "run-b", "A", [{"listed": {"noisy": 0.5}}, {"listed": {"noisy": 0.5}}], seed=2)
    runs = check_events.collect([tmp_path], since=None)

    stats = check_events.balance(runs, catalogue("noisy"))["noisy"]

    assert stats.listings == 4
    assert stats.firings == 2
    assert stats.fire_rate == 0.5
    assert stats.runs_fired == 1
    assert stats.run_rate == 0.5
    assert stats.expected == pytest.approx(2.0)


def test_distinct_probabilities_shows_a_figure_that_never_moved(tmp_path):
    write_run(
        tmp_path,
        "run-a",
        "A",
        [
            {"listed": {"flat": 0.1, "responsive": 0.1}},
            {"listed": {"flat": 0.1, "responsive": 0.3}},
        ],
    )
    runs = check_events.collect([tmp_path], since=None)
    stats = check_events.balance(runs, catalogue("flat", "responsive"))

    assert stats["flat"].distinct_probabilities == 1
    assert stats["responsive"].distinct_probabilities == 2


# ---------------------------------------------------------------------------
# Effect
# ---------------------------------------------------------------------------


def test_effect_is_measured_against_the_arm_not_the_corpus(tmp_path):
    """An arm that moves fast must not lend its trend to an event.

    Arm F gains 10 a turn and arm S gains nothing. The event fires once in F,
    on a turn that gains exactly what every other F turn gains. Measured
    against F it did nothing, which is the truth; measured against the pooled
    mean of both arms it would look worth +5.
    """
    write_run(
        tmp_path,
        "run-f",
        "F",
        [
            {"listed": {"e": 0.5}, "metrics": {"m": 0.0}},
            {"listed": {"e": 0.5}, "metrics": {"m": 10.0}},
            {"listed": {"e": 0.5}, "fired": ["e"], "metrics": {"m": 20.0}},
        ],
    )
    write_run(
        tmp_path,
        "run-s",
        "S",
        [
            {"listed": {"e": 0.5}, "metrics": {"m": 0.0}},
            {"listed": {"e": 0.5}, "metrics": {"m": 0.0}},
            {"listed": {"e": 0.5}, "metrics": {"m": 0.0}},
        ],
        seed=2,
    )
    runs = check_events.collect([tmp_path], since=None)

    n, differences = check_events.effect_profiles(runs, catalogue("e"))["e"]

    assert n == 1
    assert differences["m"] == pytest.approx(0.0)


def test_effect_reports_the_excess_over_an_ordinary_turn(tmp_path):
    """A firing turn that moves the metric more than usual shows the excess."""
    write_run(
        tmp_path,
        "run-a",
        "A",
        [
            {"listed": {"e": 0.5}, "metrics": {"m": 0.0}},
            {"listed": {"e": 0.5}, "metrics": {"m": 1.0}},
            {"listed": {"e": 0.5}, "metrics": {"m": 2.0}},
            {"listed": {"e": 0.5}, "fired": ["e"], "metrics": {"m": 12.0}},
        ],
    )
    runs = check_events.collect([tmp_path], since=None)

    n, differences = check_events.effect_profiles(runs, catalogue("e"))["e"]

    # Deltas are +1, +1, +10; the mean turn is +4, so the firing turn is +6.
    assert n == 1
    assert differences["m"] == pytest.approx(6.0)
