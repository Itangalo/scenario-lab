"""Tests for run-cohort bookkeeping (filtering and grouping by run metadata)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scenario_lab.cohorts import (
    UNKNOWN_GROUP,
    apply_filters,
    available_cohort_keys,
    between_group_stats,
    cohort_value,
    initial_state_pairs,
    load_run_config,
    mixed_scenario_warning,
    parse_filter,
    partition_runs,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _write_run(
    scenario_dir: Path,
    name: str,
    *,
    scenario_name: str = "Test Scenario",
    actors: list[str] | None = None,
    notes: str | None = None,
    source: str | None = None,
    final_metrics: dict | None = None,
    events: list[str] | None = None,
) -> Path:
    """Write a minimal completed run with configurable cohort metadata."""
    run_dir = scenario_dir / "runs" / name
    run_dir.mkdir(parents=True)

    config: dict = {"name": scenario_name}
    if actors is not None:
        config["actors"] = actors
    if notes is not None or source is not None:
        initial_state: dict = {}
        if notes is not None:
            initial_state["notes"] = notes
        if source is not None:
            initial_state["source"] = source
        config["initial_state"] = initial_state
    (run_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")

    summary = {
        "status": "completed",
        "total_turns": 1,
        "final_metrics": final_metrics or {},
        "history": [{"turn": 1, "metrics": final_metrics or {}}],
    }
    (run_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")

    turn_dir = run_dir / "turn-01"
    turn_dir.mkdir()
    (turn_dir / "4-metrics.json").write_text(json.dumps(final_metrics or {}), encoding="utf-8")
    (turn_dir / "1-events.json").write_text(
        json.dumps([{"id": eid} for eid in (events or [])]), encoding="utf-8"
    )
    return run_dir


@pytest.fixture
def runs(tmp_path: Path) -> list[Path]:
    """Three arms of one scenario plus one run from a variant identity."""
    scenario_dir = tmp_path / "scenario"
    scenario_dir.mkdir()
    return [
        _write_run(
            scenario_dir, "run-a", actors=["regulator"],
            notes="arm=fast; draw=001; regime fixed for the whole run",
            source="scenarios/scenario/draws/fast/draw-001.json",
            final_metrics={"trust": 40.0}, events=["scandal"],
        ),
        _write_run(
            scenario_dir, "run-b", actors=["regulator"],
            notes="arm=plateau; draw=002; regime fixed for the whole run",
            source="scenarios/scenario/draws/plateau/draw-002.json",
            final_metrics={"trust": 50.0},
        ),
        _write_run(
            scenario_dir, "run-c", actors=["regulator"],
            notes="arm=fast; draw=003; regime fixed for the whole run",
            source="scenarios/scenario/draws/fast/draw-003.json",
            final_metrics={"trust": 44.0},
        ),
        _write_run(
            scenario_dir, "run-d", scenario_name="Test Scenario — Urgent", actors=["regulator-urgent"],
            notes="arm=fast; draw=001; regime fixed for the whole run",
            source="scenarios/urgent/draws/fast/draw-001.json",
            final_metrics={"trust": 20.0},
        ),
    ]


# ---------------------------------------------------------------------------
# Filter spec parsing
# ---------------------------------------------------------------------------

def test_parse_filter_accepts_key_value():
    assert parse_filter("arm=fast") == ("arm", "fast")


def test_parse_filter_strips_whitespace_and_keeps_value_equals():
    assert parse_filter(" arm = fast ") == ("arm", "fast")
    assert parse_filter("q=a=b") == ("q", "a=b")


@pytest.mark.parametrize("spec", ["armfast", "=fast", "arm="])
def test_parse_filter_rejects_malformed(spec):
    # "arm=" is rejected because an empty value can never match a real cohort
    # value and would silently select nothing.
    with pytest.raises(ValueError):
        parse_filter(spec)


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def test_initial_state_pairs_parses_semicolon_notes():
    pairs = initial_state_pairs({"initial_state": {"notes": "arm=fast; draw=018; regime fixed"}})
    assert pairs == {"arm": "fast", "draw": "018"}


def test_initial_state_pairs_handles_missing_or_free_text():
    assert initial_state_pairs({}) == {}
    assert initial_state_pairs({"initial_state": {}}) == {}
    assert initial_state_pairs({"initial_state": {"notes": "no pairs here"}}) == {}


def test_cohort_value_builtin_scenario_and_actors(runs):
    config = load_run_config(runs[3])
    assert cohort_value(config, "scenario") == "Test Scenario — Urgent"
    assert cohort_value(config, "actors") == "regulator-urgent"


def test_cohort_value_from_notes_and_source(runs):
    config = load_run_config(runs[0])
    assert cohort_value(config, "arm") == "fast"
    assert cohort_value(config, "draw") == "001"
    assert cohort_value(config, "initial_state") == "fast"


def test_cohort_value_draw_falls_back_to_source_stem(tmp_path):
    run = _write_run(tmp_path, "run-x", source="scenarios/s/draws/fast/draw-007.json")
    config = load_run_config(run)
    assert cohort_value(config, "draw") == "draw-007"


def test_cohort_value_unknown_key_is_none(runs):
    config = load_run_config(runs[0])
    assert cohort_value(config, "regime") is None


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_apply_filters_selects_matching_runs_only(runs):
    kept, excluded = apply_filters(runs, [("arm", "fast")])
    # run-d belongs to the variant identity but carries the same arm, so it matches.
    assert [r.name for r in kept] == ["run-a", "run-c", "run-d"]
    assert [(r.name, reason) for r, reason in excluded] == [
        ("run-b", "arm=plateau"),
    ]


def test_apply_filters_requires_all_filters(runs):
    kept, _excluded = apply_filters(runs, [("arm", "fast"), ("actors", "regulator-urgent")])
    assert [r.name for r in kept] == ["run-d"]


def test_apply_filters_excludes_runs_missing_key(tmp_path, runs):
    bare = _write_run(tmp_path, "run-e")  # no initial_state at all
    kept, excluded = apply_filters([*runs, bare], [("arm", "fast")])
    assert bare not in kept
    assert any("no 'arm'" in reason for _, reason in excluded)


def test_apply_filters_noop_without_filters(runs):
    kept, excluded = apply_filters(runs, None)
    assert len(kept) == len(runs)
    assert excluded == []


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------

def test_partition_runs_groups_by_key_sorted_with_unknown_last(tmp_path, runs):
    bare = _write_run(tmp_path, "run-e")
    groups = partition_runs([*runs, bare], "arm")

    values = [value for value, _ in groups]
    assert values == ["fast", "plateau", UNKNOWN_GROUP]
    by_value = dict(groups)
    assert [r.name for r in by_value["fast"]] == ["run-a", "run-c", "run-d"]
    assert [r.name for r in by_value[UNKNOWN_GROUP]] == ["run-e"]


def test_available_cohort_keys_lists_discoverable_values(runs):
    available = available_cohort_keys(runs)
    assert available["arm"] == ["fast", "plateau"]
    assert set(available["scenario"]) == {"Test Scenario", "Test Scenario — Urgent"}
    assert "actors" in available


# ---------------------------------------------------------------------------
# Identity warnings
# ---------------------------------------------------------------------------

def test_mixed_scenario_warning_triggers_on_variant_identity(runs):
    warning = mixed_scenario_warning(runs)
    assert warning is not None
    assert "--filter" in warning
    assert "Test Scenario — Urgent" in warning


def test_mixed_scenario_warning_absent_for_single_identity(runs):
    same = [r for r in runs if r.name != "run-d"]
    assert mixed_scenario_warning(same) is None


# ---------------------------------------------------------------------------
# Between-group statistics
# ---------------------------------------------------------------------------

def test_between_group_stats_reports_means_and_rates(runs):
    groups = partition_runs(runs, "arm")
    stats = between_group_stats(groups)

    by_cohort = {g["cohort"]: g["n_runs"] for g in stats["groups"]}
    assert by_cohort == {"fast": 3, "plateau": 1}

    # trust mean across fast runs: (40 + 44 + 20) / 3
    assert stats["final_metrics_mean"]["trust"]["fast"] == pytest.approx(34.67, abs=0.01)
    assert stats["final_metrics_mean"]["trust"]["plateau"] == 50.0

    # scandal fired only in run-a
    assert stats["event_occurrence_rate"]["scandal"]["fast"] == pytest.approx(1 / 3, abs=0.01)
    assert stats["event_occurrence_rate"]["scandal"]["plateau"] == 0.0
