"""Tests for the actor-output parser in `scripts/build_dashboard.py`.

`parse_actor_turn` has an unwritten contract with whatever the actor model
emits, and nothing enforced it. When `meta/muse-spark-1.3-contributor` was
benchmarked on 2026-09-09 it wrote each measure's name as a `###` sub-heading
under `## New measure`; `section()` treated that as the end of the section, so
the body was empty and the parser reported no measure for all 13 turns of all
three runs. `check_portfolio_drift.py` then printed "proposed measures: 0", which reads
like a perfect score and was a total parse failure. The same bug had been
silently eating `forking-futures` output for months.

Every shape below is one an actor has actually written. The point of pinning
them is that a parse failure must never again be indistinguishable from an
actor that proposed nothing: those are opposite findings.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "build_dashboard",
    Path(__file__).resolve().parent.parent / "scripts" / "build_dashboard.py",
)
build_dashboard = importlib.util.module_from_spec(_spec)
sys.modules["build_dashboard"] = build_dashboard
_spec.loader.exec_module(build_dashboard)

parse_actor_turn = build_dashboard.parse_actor_turn
section = build_dashboard.section


def parse(tmp_path: Path, text: str) -> dict:
    f = tmp_path / "eu.md"
    f.write_text(text, encoding="utf-8")
    return parse_actor_turn(f)


BOLD = """## New measure
**Open-Weight Safety Threshold**

We are establishing a binding ceiling.

## Priority
**Open-Weight Safety Threshold** — because it is urgent.
"""

LABELLED = """## New measure
**Measure:** Establish the European AI Assurance Directorate (EAAD)
A new public agency.

## Priority
**Priority:** InvestAI Gigafactories
Because compute comes first.
"""

SUBHEADING = """## New measure
### EU Chokepoint Leverage Defence
Joint EU response to Washington forcing ASML cuts.

## Priority
Sovereign Verification Regime, because sight comes first.
"""

DECLINED_PLAIN = """## New measure
None this turn.
Waiting for the legal adoption of the Response Corps.

## Priority
**Institutional Integrity Audit**
"""

DECLINED_BOLD = """## New measure
**None this turn.**

## Priority
**Institutional Integrity Audit**
"""

DECLINED_PROSE = """## New measure
No new measure is tabled while capital is this thin.

## Priority
**Institutional Integrity Audit**
"""

MISSING = """## Portfolio
`Thing (category 4, costs 3 per turn, started turn 1, finishes on turn 7): x`

## In practice
We did things.
"""


class TestNewMeasureShapes:
    def test_bold_name(self, tmp_path):
        r = parse(tmp_path, BOLD)
        assert r["new_measure"] == "Open-Weight Safety Threshold"
        assert r["new_measure_status"] == "named"

    def test_labelled_name(self, tmp_path):
        r = parse(tmp_path, LABELLED)
        assert r["new_measure"] == "Establish the European AI Assurance Directorate (EAAD)"
        assert r["new_measure_status"] == "named"

    def test_subheading_name(self, tmp_path):
        """The muse-spark shape. This is the regression that started it."""
        r = parse(tmp_path, SUBHEADING)
        assert r["new_measure"] == "EU Chokepoint Leverage Defence"
        assert r["new_measure_status"] == "named"

    def test_subheading_body_is_not_swallowed_by_the_boundary(self, tmp_path):
        body = section(SUBHEADING, "New measure")
        assert body, "a ### sub-heading must be content, not a section terminator"
        assert "Chokepoint" in body

    def test_priority_still_parses_alongside(self, tmp_path):
        assert parse(tmp_path, BOLD)["priority"] == "Open-Weight Safety Threshold"
        assert parse(tmp_path, LABELLED)["priority"] == "InvestAI Gigafactories"


class TestEmptyCasesAreDistinguished:
    """The whole point: "named nothing" and "could not read it" are opposites."""

    @pytest.mark.parametrize("text", [DECLINED_PLAIN, DECLINED_BOLD, DECLINED_PROSE])
    def test_declined_is_not_unreadable(self, tmp_path, text):
        r = parse(tmp_path, text)
        assert r["new_measure"] is None
        assert r["new_measure_status"] == "declined"

    def test_absent_section_is_unreadable(self, tmp_path):
        r = parse(tmp_path, MISSING)
        assert r["new_measure"] is None
        assert r["new_measure_status"] == "unreadable"

    def test_missing_file_is_unreadable(self, tmp_path):
        r = parse_actor_turn(tmp_path / "does-not-exist.md")
        assert r["new_measure_status"] == "unreadable"
        assert r["priority_status"] == "unreadable"

    def test_the_two_empty_cases_do_not_collide(self, tmp_path):
        declined = parse(tmp_path, DECLINED_PLAIN)["new_measure_status"]
        unreadable = parse(tmp_path, MISSING)["new_measure_status"]
        assert declined != unreadable


class TestSectionBoundary:
    def test_stops_at_same_level_heading(self):
        text = "## New measure\nalpha\n\n## Priority\nbeta\n"
        assert section(text, "New measure") == "alpha"

    def test_stops_at_top_level_heading(self):
        text = "## New measure\nalpha\n\n# Something\nbeta\n"
        assert section(text, "New measure") == "alpha"

    def test_does_not_stop_at_sub_heading(self):
        text = "## New measure\n### Name\nalpha\n\n## Priority\nbeta\n"
        body = section(text, "New measure")
        assert "Name" in body and "alpha" in body and "beta" not in body

    def test_portfolio_is_unaffected_by_the_wider_boundary(self, tmp_path):
        """Verified across 12 000 real actor files as byte-identical; pinned here."""
        text = ("## Portfolio\n"
                "`Alpha (category 4, costs 3 per turn, started turn 1, finishes on turn 7): x`\n"
                "\n## New measure\n### Beta\nbody\n")
        r = parse(tmp_path, text)
        assert [m["name"] for m in r["portfolio"]] == ["Alpha"]
