"""Tests for starting-state overrides (``--initial-state`` / ``--initial-states``).

These cover the Monte-Carlo-over-initial-conditions path: a batch of runs that
each start from a different sampled world, rather than only from different
event dice.
"""

import argparse
import json

import pytest

from scenario_lab.cli import (
    build_batch_run_command,
    build_batch_run_specs,
    resolve_initial_state_files,
)
from scenario_lab.loader import apply_initial_state, load_initial_state, load_scenario


@pytest.fixture
def scenario_dir(tmp_path):
    """Create a minimal scenario directory with two bounded metrics."""
    scenario_dir = tmp_path / "scenarios" / "test-scenario"
    scenario_dir.mkdir(parents=True)

    (scenario_dir / "scenario.yaml").write_text(
        """
name: "Test Scenario"
description: "Scenario for initial-state tests"
start_date: "2026-09"
time_scale: "1 week per turn"
max_turns: 5
actors:
  - actor1
""",
        encoding="utf-8",
    )

    (scenario_dir / "metrics.md").write_text(
        """# Metrics

## seats_a
**Description:** Seats for party A
**ID:** seats_a
**Starting value:** 100
**Min:** 0
**Max:** 349
**Unit:** seats

## seats_b
**Description:** Seats for party B
**ID:** seats_b
**Starting value:** 80
**Min:** 0
**Max:** 349
**Unit:** seats
""",
        encoding="utf-8",
    )

    (scenario_dir / "events.md").write_text("# Events\n", encoding="utf-8")
    (scenario_dir / "metric-rules.md").write_text(
        "# Metric Rules\n\n1. Test rule\n", encoding="utf-8"
    )

    bg_dir = scenario_dir / "background"
    bg_dir.mkdir()
    (bg_dir / "context.md").write_text(
        "# Context\n\nThe world before the draw.", encoding="utf-8"
    )

    actors_dir = bg_dir / "actors"
    actors_dir.mkdir()
    (actors_dir / "actor1.md").write_text(
        "# Actor 1\n## Short description\nTest actor.\n## Long description\nTest goal.\n",
        encoding="utf-8",
    )

    return scenario_dir


def write_state(path, payload):
    """Write an initial-state JSON file and return its path."""
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# --- load_initial_state -----------------------------------------------------


def test_load_initial_state_reads_all_fields(tmp_path):
    path = write_state(
        tmp_path / "draw.json",
        {
            "metrics": {"seats_a": 107, "seats_b": 61.0},
            "context": "## Result\n\nParty A won.",
            "notes": "draw 07, sampler seed 12345",
        },
    )

    state = load_initial_state(path)

    assert state.metrics == {"seats_a": 107.0, "seats_b": 61.0}
    assert state.context == "## Result\n\nParty A won."
    assert state.notes == "draw 07, sampler seed 12345"
    assert state.source == str(path)


def test_load_initial_state_allows_empty_object(tmp_path):
    state = load_initial_state(write_state(tmp_path / "draw.json", {}))

    assert state.metrics == {}
    assert state.context == ""
    assert state.notes == ""


def test_load_initial_state_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_initial_state(tmp_path / "absent.json")


def test_load_initial_state_rejects_invalid_json(tmp_path):
    path = tmp_path / "draw.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ValueError, match="not valid JSON"):
        load_initial_state(path)


def test_load_initial_state_rejects_non_object(tmp_path):
    with pytest.raises(ValueError, match="must contain a JSON object"):
        load_initial_state(write_state(tmp_path / "draw.json", [1, 2, 3]))


def test_load_initial_state_rejects_unknown_key(tmp_path):
    """A typo in a generated draw must fail loudly, not be ignored."""
    path = write_state(tmp_path / "draw.json", {"metric": {"seats_a": 1}})

    with pytest.raises(ValueError, match="unknown key"):
        load_initial_state(path)


def test_load_initial_state_rejects_non_object_metrics(tmp_path):
    path = write_state(tmp_path / "draw.json", {"metrics": [1, 2]})

    with pytest.raises(ValueError, match="'metrics' must be an object"):
        load_initial_state(path)


def test_load_initial_state_rejects_boolean_metric(tmp_path):
    """bool is a subclass of int; accepting it would set a metric to 0/1."""
    path = write_state(tmp_path / "draw.json", {"metrics": {"seats_a": True}})

    with pytest.raises(ValueError, match="must be a number"):
        load_initial_state(path)


def test_load_initial_state_rejects_string_metric(tmp_path):
    path = write_state(tmp_path / "draw.json", {"metrics": {"seats_a": "107"}})

    with pytest.raises(ValueError, match="must be a number"):
        load_initial_state(path)


def test_load_initial_state_rejects_non_string_context(tmp_path):
    path = write_state(tmp_path / "draw.json", {"context": 42})

    with pytest.raises(ValueError, match="'context' must be a string"):
        load_initial_state(path)


def test_load_initial_state_rejects_non_string_notes(tmp_path):
    path = write_state(tmp_path / "draw.json", {"notes": ["a"]})

    with pytest.raises(ValueError, match="'notes' must be a string"):
        load_initial_state(path)


# --- apply_initial_state ----------------------------------------------------


def test_apply_initial_state_sets_metric_values(scenario_dir, tmp_path):
    scenario = load_scenario(scenario_dir)
    state = load_initial_state(
        write_state(tmp_path / "draw.json", {"metrics": {"seats_a": 107, "seats_b": 61}})
    )

    apply_initial_state(scenario, state)

    assert scenario.metrics.metrics["seats_a"].value == 107
    assert scenario.metrics.metrics["seats_b"].value == 61
    assert scenario.initial_state is state


def test_apply_initial_state_leaves_unmentioned_metrics_alone(scenario_dir, tmp_path):
    scenario = load_scenario(scenario_dir)
    state = load_initial_state(
        write_state(tmp_path / "draw.json", {"metrics": {"seats_a": 107}})
    )

    apply_initial_state(scenario, state)

    assert scenario.metrics.metrics["seats_b"].value == 80


def test_apply_initial_state_accepts_boundary_values(scenario_dir, tmp_path):
    scenario = load_scenario(scenario_dir)
    state = load_initial_state(
        write_state(tmp_path / "draw.json", {"metrics": {"seats_a": 0, "seats_b": 349}})
    )

    apply_initial_state(scenario, state)

    assert scenario.metrics.metrics["seats_a"].value == 0
    assert scenario.metrics.metrics["seats_b"].value == 349


def test_apply_initial_state_rejects_unknown_metric(scenario_dir, tmp_path):
    scenario = load_scenario(scenario_dir)
    state = load_initial_state(
        write_state(tmp_path / "draw.json", {"metrics": {"seats_c": 10}})
    )

    with pytest.raises(ValueError, match="unknown metric"):
        apply_initial_state(scenario, state)


def test_apply_initial_state_rejects_out_of_bounds(scenario_dir, tmp_path):
    """A draw outside the bounds means a broken sampler; clamping would hide it."""
    scenario = load_scenario(scenario_dir)
    state = load_initial_state(
        write_state(tmp_path / "draw.json", {"metrics": {"seats_a": 400}})
    )

    with pytest.raises(ValueError, match=r"outside its bounds"):
        apply_initial_state(scenario, state)


def test_apply_initial_state_rejects_below_minimum(scenario_dir, tmp_path):
    scenario = load_scenario(scenario_dir)
    state = load_initial_state(
        write_state(tmp_path / "draw.json", {"metrics": {"seats_a": -1}})
    )

    with pytest.raises(ValueError, match=r"outside its bounds"):
        apply_initial_state(scenario, state)


def test_apply_initial_state_appends_context_to_world_state(scenario_dir, tmp_path):
    """Turn 1 prompts read world_state.narrative, so both must carry the draw."""
    scenario = load_scenario(scenario_dir)
    state = load_initial_state(
        write_state(tmp_path / "draw.json", {"context": "## Result\n\nParty A won."})
    )

    apply_initial_state(scenario, state)

    assert "The world before the draw." in scenario.context
    assert "Party A won." in scenario.context
    assert scenario.world_state.narrative == scenario.context


def test_apply_initial_state_without_context_leaves_it_unchanged(scenario_dir, tmp_path):
    scenario = load_scenario(scenario_dir)
    original = scenario.context
    state = load_initial_state(
        write_state(tmp_path / "draw.json", {"metrics": {"seats_a": 107}})
    )

    apply_initial_state(scenario, state)

    assert scenario.context == original


# --- load_scenario integration ---------------------------------------------


def test_load_scenario_without_initial_state(scenario_dir):
    scenario = load_scenario(scenario_dir)

    assert scenario.initial_state is None
    assert scenario.metrics.metrics["seats_a"].value == 100


def test_load_scenario_applies_initial_state(scenario_dir, tmp_path):
    path = write_state(
        tmp_path / "draw.json",
        {"metrics": {"seats_a": 107}, "context": "Party A won.", "notes": "draw 07"},
    )

    scenario = load_scenario(scenario_dir, initial_state=path)

    assert scenario.metrics.metrics["seats_a"].value == 107
    assert "Party A won." in scenario.world_state.narrative
    assert scenario.initial_state.notes == "draw 07"


def test_load_scenario_propagates_initial_state_errors(scenario_dir, tmp_path):
    path = write_state(tmp_path / "draw.json", {"metrics": {"seats_c": 1}})

    with pytest.raises(ValueError, match="unknown metric"):
        load_scenario(scenario_dir, initial_state=path)


# --- resolve_initial_state_files -------------------------------------------


def test_resolve_initial_state_files_sorted(tmp_path):
    states = tmp_path / "draws"
    states.mkdir()
    for name in ["draw-03.json", "draw-01.json", "draw-02.json"]:
        write_state(states / name, {})

    resolved = resolve_initial_state_files(states, 3)

    assert [p.name for p in resolved] == ["draw-01.json", "draw-02.json", "draw-03.json"]


def test_resolve_initial_state_files_takes_only_what_is_needed(tmp_path):
    states = tmp_path / "draws"
    states.mkdir()
    for index in range(5):
        write_state(states / f"draw-{index:02d}.json", {})

    assert len(resolve_initial_state_files(states, 2)) == 2


def test_resolve_initial_state_files_ignores_non_json(tmp_path):
    states = tmp_path / "draws"
    states.mkdir()
    write_state(states / "draw-01.json", {})
    (states / "README.md").write_text("notes", encoding="utf-8")

    assert [p.name for p in resolve_initial_state_files(states, 1)] == ["draw-01.json"]


def test_resolve_initial_state_files_rejects_too_few(tmp_path):
    """Cycling draws would silently narrow the distribution the batch reports."""
    states = tmp_path / "draws"
    states.mkdir()
    write_state(states / "draw-01.json", {})

    with pytest.raises(ValueError, match="Generate more draws"):
        resolve_initial_state_files(states, 3)


def test_resolve_initial_state_files_rejects_missing_directory(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        resolve_initial_state_files(tmp_path / "absent", 1)


def test_resolve_initial_state_files_rejects_empty_directory(tmp_path):
    states = tmp_path / "draws"
    states.mkdir()

    with pytest.raises(ValueError, match="No .json initial-state files"):
        resolve_initial_state_files(states, 1)


# --- batch wiring -----------------------------------------------------------


def batch_args(**overrides):
    """Build an argparse namespace shaped like batch-run's."""
    defaults = dict(
        turns=None,
        model=None,
        validate=False,
        seed=None,
        log_llm_io=False,
        override=None,
        initial_states=None,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def test_build_batch_run_command_includes_initial_state(tmp_path):
    command = build_batch_run_command(
        tmp_path / "scenario", batch_args(), tmp_path / "draw-01.json"
    )

    assert "--initial-state" in command
    assert command[command.index("--initial-state") + 1] == str(tmp_path / "draw-01.json")


def test_build_batch_run_command_omits_initial_state_when_absent(tmp_path):
    command = build_batch_run_command(tmp_path / "scenario", batch_args())

    assert "--initial-state" not in command


def test_build_batch_run_specs_assigns_a_distinct_draw_per_job(scenario_dir, tmp_path):
    states = tmp_path / "draws"
    states.mkdir()
    for index in range(3):
        write_state(states / f"draw-{index:02d}.json", {})

    specs = build_batch_run_specs(
        [scenario_dir] * 3, batch_args(initial_states=str(states)), "20260913-120000"
    )

    assigned = [
        spec.command[spec.command.index("--initial-state") + 1] for spec in specs
    ]
    assert assigned == [str(states / f"draw-{i:02d}.json") for i in range(3)]
    assert len(set(assigned)) == 3


def test_build_batch_run_specs_without_initial_states(scenario_dir):
    specs = build_batch_run_specs([scenario_dir] * 2, batch_args(), "20260913-120000")

    assert all("--initial-state" not in spec.command for spec in specs)


# --- describe integration ---------------------------------------------------


def test_describe_applies_the_draw(scenario_dir, tmp_path):
    """Lets a draw be eyeballed before a batch is launched, at zero cost."""
    from scenario_lab.describe import describe_scenario

    path = write_state(tmp_path / "draw.json", {"metrics": {"seats_a": 107}})

    overview = describe_scenario(scenario_dir, initial_state=path)

    values = {m["id"]: m["start_value"] for m in overview["metrics"]}
    assert values["seats_a"] == 107
    assert values["seats_b"] == 80


def test_describe_without_draw_shows_declared_values(scenario_dir):
    from scenario_lab.describe import describe_scenario

    overview = describe_scenario(scenario_dir)

    values = {m["id"]: m["start_value"] for m in overview["metrics"]}
    assert values["seats_a"] == 100


# --- persistence ------------------------------------------------------------


def test_run_config_records_the_draw(scenario_dir, tmp_path):
    """Without this, a batch over sampled worlds cannot be attributed afterwards."""
    from scenario_lab.output import OutputManager

    path = write_state(
        tmp_path / "draw.json",
        {"metrics": {"seats_a": 107}, "notes": "draw 07, sampler seed 12345"},
    )
    scenario = load_scenario(scenario_dir, initial_state=path)

    output_manager = OutputManager(scenario, scenario_dir)
    run_dir = output_manager.start_run()

    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    assert config["initial_state"]["metrics"] == {"seats_a": 107.0}
    assert config["initial_state"]["notes"] == "draw 07, sampler seed 12345"
    assert config["initial_state"]["source"] == str(path)


def test_run_config_omits_initial_state_when_unused(scenario_dir):
    from scenario_lab.output import OutputManager

    scenario = load_scenario(scenario_dir)
    run_dir = OutputManager(scenario, scenario_dir).start_run()

    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    assert "initial_state" not in config
