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


class TestStoreBackedRuns:
    """Runs whose portfolio the framework holds have no `## Portfolio` section.

    The actor stopped restating it, which is the point. Everything downstream
    of this parser -- the dashboard, the tree extractor, the sign-off renderer
    -- would otherwise report an empty portfolio for every turn of such a run,
    silently and forever. That is the exact shape of failure this repository
    keeps having to measure after the fact, so it is pinned here.
    """

    def write(self, tmp_path: Path, records: list[dict], turn: int = 3) -> Path:
        import json

        actors = tmp_path / f"turn-{turn:02d}" / "2-actors"
        actors.mkdir(parents=True)
        (actors / "eu.md").write_text(
            "## New measure\n\n**A Measure Name**\n\nIt does a thing.\n\n"
            "## Priority\n\nA Measure Name\n",
            encoding="utf-8",
        )
        (actors / "eu-store.json").write_text(
            json.dumps({"turn": turn, "counters": {"measures": len(records)},
                        "records": records}),
            encoding="utf-8",
        )
        return actors / "eu.md"

    def record(self, rid: str, name: str, **kw) -> dict:
        base = {
            "id": rid, "table": "measures", "actor": "eu",
            "fields": {"name": name, "category": 4, "size": "large",
                       "started_turn": kw.get("start", 1),
                       "finish_turn": kw.get("finish", 7),
                       "targeted_effect": "sovereignty up"},
            "derived": {"cost_per_turn": 3, "status": kw.get("status", "running")},
            "added_turn": kw.get("start", 1),
            "removed_turn": kw.get("removed"),
        }
        return base

    def test_portfolio_comes_from_the_store(self, tmp_path):
        path = self.write(tmp_path, [self.record("M1", "Gigafactories"),
                                     self.record("M2", "Sovereignty package", finish=6)])
        result = parse_actor_turn(path)
        assert [m["name"] for m in result["portfolio"]] == ["Gigafactories", "Sovereignty package"]
        assert result["portfolio"][0]["cost"] == 3
        assert result["portfolio"][0]["category"] == 4
        assert result["portfolio"][0]["start"] == 1
        assert result["portfolio"][0]["finish"] == 7

    def test_a_finished_measure_is_marked(self, tmp_path):
        path = self.write(tmp_path, [self.record("M1", "Done", status="finished")])
        assert parse_actor_turn(path)["portfolio"][0]["finished"] is True

    def test_a_deleted_measure_is_a_cancellation_in_its_own_turn(self, tmp_path):
        path = self.write(tmp_path, [self.record("M1", "Dropped", removed=3)])
        result = parse_actor_turn(path)
        assert result["portfolio"] == []
        assert [c["name"] for c in result["cancelled"]] == ["Dropped"]

    def test_a_measure_deleted_earlier_is_simply_absent(self, tmp_path):
        path = self.write(tmp_path, [self.record("M1", "Dropped", removed=2)])
        result = parse_actor_turn(path)
        assert result["portfolio"] == []
        assert result["cancelled"] == []

    def test_the_new_measure_is_the_record_added_this_turn(self, tmp_path):
        """The record names the measure; the prose only argues for it."""
        path = self.write(tmp_path, [self.record("M1", "Old", start=1),
                                     self.record("M2", "Newly added", start=3)])
        result = parse_actor_turn(path)
        assert result["new_measure"] == "Newly added"
        assert result["new_measure_status"] == "named"

    def test_prose_still_answers_when_nothing_was_added(self, tmp_path):
        """'Proposed nothing' and 'could not be read' stay opposite findings."""
        actors = tmp_path / "turn-03" / "2-actors"
        actors.mkdir(parents=True)
        (actors / "eu.md").write_text("## New measure\n\nNone this turn.\n", encoding="utf-8")
        (actors / "eu-store.json").write_text('{"turn": 3, "records": []}', encoding="utf-8")
        result = parse_actor_turn(actors / "eu.md")
        assert result["new_measure"] is None
        assert result["new_measure_status"] == "declined"

    def test_runs_without_a_store_still_parse_their_prose(self, tmp_path):
        """Every run committed before this change."""
        actors = tmp_path / "turn-03" / "2-actors"
        actors.mkdir(parents=True)
        (actors / "eu.md").write_text(
            "## Portfolio\n\n"
            "- Gigafactories (category 4, costs 3 per turn, started turn 1, "
            "finishes on turn 7): sites\n",
            encoding="utf-8",
        )
        result = parse_actor_turn(actors / "eu.md")
        assert [m["name"] for m in result["portfolio"]] == ["Gigafactories"]
