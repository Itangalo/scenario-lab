"""Tests for the SOVEREIGNTY-line parser in `scripts/check_sovereignty.py`.

The script exists to say whether a Game Master's accounting line binds the
metric it claims to explain, and its answers get written into the scenario's
design notes as findings. A parser that mis-reads a line produces a number that
looks exactly as authoritative as a correct one, so the shapes the Game Master
actually writes are pinned here.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "check_sovereignty",
    Path(__file__).resolve().parent.parent / "scripts" / "check_sovereignty.py",
)
check_sovereignty = importlib.util.module_from_spec(_spec)
# Registered before execution because `dataclass` resolves a field's type by
# looking its module up in sys.modules, and fails on a module that is not there.
sys.modules[_spec.name] = check_sovereignty
_spec.loader.exec_module(check_sovereignty)

parse_line = check_sovereignty.parse_line
completions = check_sovereignty.completions
same_measure = check_sovereignty.same_measure
resolve_claim = check_sovereignty.resolve_claim


def test_anchored_line_yields_terms_total_and_anchor():
    terms, claims, anchor = parse_line(
        "SOVEREIGNTY: 31 last turn, Sovereign Compute Corridor finishes t6 +5, "
        "Gigafactories in flight +1, capability rose 2.5 −1 = 36"
    )
    assert anchor == 31.0
    assert terms == [5.0, 1.0, -1.0]
    assert claims[-1] == 36.0


def test_size_of_a_capability_rise_is_not_a_term():
    """`capability rose 2.5 −1` states the rise, then the cost it triggers."""
    terms, claims, _ = parse_line(
        "SOVEREIGNTY: no measure finished, capability rose 2.5 −1 = −1"
    )
    assert terms == [-1.0]
    assert claims[-1] == -1.0


@pytest.mark.parametrize("rise", ["rose 2.5", "rose ≥2", "rose by 3.0"])
def test_the_rise_is_stripped_however_it_is_written(rise):
    terms, _, _ = parse_line(f"SOVEREIGNTY: 22 last turn, capability {rise} −1 = 21")
    assert terms == [-1.0]


def test_a_declined_decay_is_not_a_term():
    """`rose 1.5 -> no -1` is rule 5's decay refusing to fire, not a -1 applied.

    The decay costs a point only when capability rose at least 2. Below that the
    Game Master writes the term it is not charging, and reading it as charged
    makes a correct line look like an arithmetic error.
    """
    terms, claims, anchor = parse_line(
        "SOVEREIGNTY: 21 last turn, EASL finishes t5 +3, Red-Teaming Network in flight +2, "
        "capability rose 1.5 → no −1 = 26"
    )
    assert (terms, claims[-1], anchor) == ([3.0, 2.0], 26.0, 21.0)


@pytest.mark.parametrize(
    "threshold", ["(under 2)", "(less than 2)", "< 2", "(at least 2)"]
)
def test_the_threshold_being_checked_is_not_a_term(threshold):
    """Rule 5's decay applies only above a rise of 2, and the line says so.

    The 2 it cites is the condition it is testing, not a figure it is adding.
    """
    terms, _, _ = parse_line(
        f"SOVEREIGNTY: 23 last turn, Gigafactories in flight +1, "
        f"capability rose 1.5 {threshold} → no penalty = 24"
    )
    assert terms == [1.0]


def test_a_category_tag_is_not_a_term():
    terms, claims, _ = parse_line(
        "SOVEREIGNTY: Autonomous Resilience Corps finished +0 (cat 6), "
        "capability rose 4.0 −1 = −1"
    )
    assert terms == [0.0, -1.0]
    assert claims[-1] == -1.0


def test_a_restatement_after_the_total_is_what_counts():
    """The model sometimes reaches a total and then overrides it.

    The override is the number it was looking at when it wrote the metric, so
    that is the claim to hold it to.
    """
    _, claims, _ = parse_line(
        "SOVEREIGNTY: Compute Guarantee in flight +1, capability rose 2.5 −1 = +0 "
        "→ net +1 from prior institutional momentum"
    )
    assert claims[-1] == 1.0


def test_no_change_is_a_stated_zero():
    terms, claims, anchor = parse_line("SOVEREIGNTY: no change")
    assert (terms, claims, anchor) == ([], [0.0], None)


def test_completions_names_only_measures_that_finished():
    line = (
        "SOVEREIGNTY: InvestAI Gigafactories finished +5, "
        "Sovereign Evaluation Capacity in flight +1, "
        "no category 4 measure finished, capability rose 1 −1 = +4"
    )
    assert completions(line) == ["investai gigafactories"]


def test_completions_reads_the_finishes_form():
    line = "SOVEREIGNTY: 31 last turn, Tech Sovereignty Package finishes t7 +5 = 36"
    assert completions(line) == ["tech sovereignty package"]


def test_a_shortened_title_is_the_same_measure():
    assert same_measure(
        "secure and scale eu-controlled inference infrastructure", "secure and scale"
    )
    assert not same_measure("investai gigafactories", "tech sovereignty package")


@pytest.mark.parametrize(
    "claim, reference, expected",
    [
        (33.0, 32.0, 1.0),    # anchored form ends at a level
        (-1.0, 22.0, -1.0),   # earlier form ends at a change
        (0.0, 22.0, 0.0),     # a change of nothing, not a level of nothing
        (37.0, 32.5, 4.5),    # earlier form appending a level: `= +9 (net 37.0)`
        (30.0, 30.0, 0.0),    # a level restated unchanged
        (-1.0, None, -1.0),   # turn 1, nothing to compare against
    ],
)
def test_resolve_claim_tells_a_level_from_a_change(claim, reference, expected):
    """The line mixes the two freely, and its shape does not say which is which.

    What says is the value the metric held going in: a claim nearer that value
    than nearer zero is a level. Getting this wrong invents drift that is not
    there — it put a spurious 32-point gap in both cohorts before it was fixed.
    """
    assert resolve_claim(claim, reference) == expected


@pytest.mark.parametrize(
    "prefix, suffix",
    [("", ""), ("- ", ""), ("* ", ""), ("  - ", ""), ("1. ", ""),
     ("`", "`"), ("- `", "`"), ("**", "**")],
)
def test_the_line_is_found_however_the_notepad_formats_it(tmp_path, prefix, suffix):
    """A run that bullets its notepad is not a run that skipped the rule.

    Anchoring the detector to the start of the line once read seven runs of
    eight as having written the line in only 80% of turns, when every one of
    them had written it.
    """
    run = tmp_path / "run-x"
    (run / "turn-01").mkdir(parents=True)
    (run / "config.json").write_text("{}")
    (run / "turn-01" / "4-metrics.json").write_text('{"eu_ai_sovereignty": 21.0}')
    (run / "turn-01" / "5-notepad.md").write_text(
        f"{prefix}SOVEREIGNTY: 22 last turn, capability rose 2.5 −1 = 21{suffix}\n"
    )

    check = check_sovereignty.read_turn(run, run / "turn-01")

    assert check is not None and check.line is not None
    assert check.anchor == 22.0
