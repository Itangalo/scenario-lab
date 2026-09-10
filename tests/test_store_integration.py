"""End-to-end tests for the store: orchestrator, artifacts, resume, branch.

`test_store.py` tests the mechanism in isolation. These test the seams -- that
the orchestrator actually applies commands, that the prompts actually render
the records, that a resumed run continues from them, and that a scenario which
declares no store is untouched by any of it.

The scenario built here is deliberately minimal rather than a copy of
europe-2032: what is under test is the framework, and a fixture that needs the
scenario's 33 events to be right would be testing the wrong thing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scenario_lab.llm import MockLLMClient
from scenario_lab.loader import load_scenario
from scenario_lab.orchestrator import Orchestrator
from scenario_lab.output import OutputManager
from scenario_lab.prompts import PromptBuilder
from scenario_lab.resume import load_run_state
from scenario_lab.store import StoreView

SCENARIO_YAML = """
name: "Store Test"
description: "A scenario that declares persistent state"
start_date: "2026-01"
time_scale: "6 months per turn"
max_turns: 5
actors:
  - gov
rule_evolution:
  freeze_until_turn: 6
  max_changes_per_turn: 0
store:
  measures:
    scope: actor
    columns:
      id:            {owner: system,  type: text}
      name:          {owner: actor,   type: text, required: true}
      size:          {owner: actor,   type: enum, values: [large, small], required: true}
      started_turn:  {owner: system,  type: turn}
      finish_turn:   {owner: actor,   type: turn, required: true}
      cost_per_turn: {owner: derived, type: integer, from: size, map: {large: 3, small: 2}}
      status:        {owner: derived, type: text, from: finish_turn,
                      when_reached: finished, else: running}
"""

METRIC_RULES = """# Metric Rules

## Rules

1. In flight this turn:

{{ store.rows('measures', status='running') }}

   Charge {{ store.sum('measures', 'cost_per_turn', status='running') }} capital.
"""

ACTOR_PROMPT = """It is now turn {{turn}}.

## Your portfolio

{{ store.rows('measures', status='running') }}

Write a `## Store changes` section.
"""


@pytest.fixture
def scenario_dir(tmp_path: Path) -> Path:
    """A minimal scenario that declares a store."""
    directory = tmp_path / "scenarios" / "store-test"
    (directory / "background" / "actors").mkdir(parents=True)
    (directory / "user-prompts").mkdir()

    (directory / "scenario.yaml").write_text(SCENARIO_YAML)
    (directory / "metric-rules.md").write_text(METRIC_RULES)
    (directory / "events.md").write_text("# Events\n")
    (directory / "metrics.md").write_text(
        "# Metrics\n\n## capital\n**Description:** Political capital\n"
        "**ID:** capital\n**Starting value:** 50\n**Min:** 0\n**Max:** 100\n**Unit:** points\n"
    )
    (directory / "background" / "context.md").write_text("# Context\n\nThe world.")
    (directory / "background" / "actors" / "gov.md").write_text(
        "# Government\n## Short description\nA government.\n"
        "## Long description\nIt governs.\n"
    )
    (directory / "user-prompts" / "actor.md").write_text(ACTOR_PROMPT)
    return directory


def actor_response(body: str) -> str:
    return f"## Actions\n\nWe act.\n\n## Store changes\n\n{body}\n"


def writes(*entries: dict) -> str:
    """A fenced JSON write block for a mocked actor answer."""
    return "```json\n" + json.dumps({"store": list(entries)}) + "\n```"


def add(name: str, size: str = "small", finish_turn: int = 9, **extra) -> dict:
    return {
        "op": "add", "table": "measures",
        "fields": {"name": name, "size": size, "finish_turn": finish_turn, **extra},
    }


def mock_client(actor_by_turn: dict[int, str]) -> MockLLMClient:
    """A client whose actor reply depends on which turn's prompt it is given."""
    responses = {
        f"It is now turn {turn}.": actor_response(body)
        for turn, body in actor_by_turn.items()
    }
    responses.update(
        {
            "external events": "[]",
            "Metric Rules": "# Metric Rules v2 (Turn 1)\n\n"
            "## Changelog from v1\n\n- No material rule changes.\n"
            "  - **Motivation:** frozen\n  - **Expected impact:** none\n\n"
            "## Rules\n\n1. Test rule\n",
            "JSON object describing all metrics": '## Metrics\n\n```json\n{"capital": 50}\n```\n\n'
            "## Narrative\n\nThings happened.\n\n## Notepad\n\nNotes.",
            "CURRENT NARRATIVE": "A summary.",
        }
    )
    return MockLLMClient(responses)


def run_turns(scenario_dir: Path, actor_by_turn: dict[int, str]):
    """Run the given turns for real, through the orchestrator, and return the
    live scenario and the run directory the artifacts landed in."""
    scenario = load_scenario(scenario_dir)
    output = OutputManager(scenario, scenario_dir)
    run_dir = output.start_run()
    orchestrator = Orchestrator(scenario, mock_client(actor_by_turn), output_manager=output)
    for turn in sorted(actor_by_turn):
        orchestrator.run_turn(turn)
    return scenario, run_dir


# ---------------------------------------------------------------------------
# The orchestrator seam
# ---------------------------------------------------------------------------


def test_commands_are_applied_and_records_persist(scenario_dir, tmp_path):
    """A record added in turn 1 is still there in turn 4, unmentioned since."""
    scenario, _run_dir = run_turns(
        scenario_dir,
        {
            1: writes(add("Compute build", size="large", finish_turn=6)),
            2: "No changes.",
            3: "No changes.",
            4: writes(add("Incident corps", finish_turn=4)),
        },
    )
    records = scenario.store.live_records("measures")
    assert [r.fields["name"] for r in records] == ["Compute build", "Incident corps"]
    assert records[0].fields["started_turn"] == 1
    assert records[1].fields["started_turn"] == 4


def test_a_turn_that_never_mentions_the_store_loses_nothing(scenario_dir, tmp_path):
    """The measured defect, reproduced as the failing case and now passing."""
    scenario, _run_dir = run_turns(
        scenario_dir,
        {1: writes(add("Kept", finish_turn=9))},
    )
    store = scenario.store
    # A later turn whose actor output has no section at all.
    store.begin_turn(2)
    assert len(store.live_records("measures")) == 1


def test_artifacts_are_written_every_turn(scenario_dir, tmp_path):
    _scenario, run_dir = run_turns(
        scenario_dir,
        {
            1: writes(add("Kept", finish_turn=9)),
            2: "No changes.",
        },
    )
    for turn in (1, 2):
        actors = run_dir / f"turn-{turn:02d}" / "2-actors"
        assert (actors / "gov-store.md").exists()
        assert (actors / "gov-store.json").exists()

    first = (run_dir / "turn-01" / "2-actors" / "gov-store.md").read_text()
    second = (run_dir / "turn-02" / "2-actors" / "gov-store.md").read_text()
    assert "**applied** `M1`" in first
    assert "No changes." in second
    # The records themselves are identical between the turns: a diff is empty
    # unless something was actually applied. Only the turn in the heading moves.
    def records(text: str) -> str:
        return text.split("## Changes this turn")[0].split("\n", 1)[1]

    assert records(first) == records(second)


def test_a_missing_section_is_recorded_as_a_fault(scenario_dir, tmp_path):
    scenario = load_scenario(scenario_dir)
    output = OutputManager(scenario, scenario_dir)
    run_dir = output.start_run()
    orchestrator = Orchestrator(scenario, mock_client({}), output_manager=output)
    orchestrator._process_store_changes(1, {"gov": "## Actions\n\nNo section here.\n"})
    text = (run_dir / "turn-01" / "2-actors" / "gov-store.md").read_text()
    assert "No `## Store changes` section" in text


def test_rejections_reach_the_artifact(scenario_dir, tmp_path):
    _scenario, run_dir = run_turns(
        scenario_dir,
        {1: writes(add("Nameless", size="enormous", finish_turn=3))},
    )
    text = (run_dir / "turn-01" / "2-actors" / "gov-store.md").read_text()
    assert "**rejected**" in text
    assert "must be one of large, small" in text


def test_config_records_the_resolved_schema(scenario_dir, tmp_path):
    _scenario, run_dir = run_turns(scenario_dir, {1: "No changes."})
    config = json.loads((run_dir / "config.json").read_text())
    assert config["store"]["measures"]["columns"]["started_turn"]["owner"] == "system"
    assert config["store"]["measures"]["columns"]["cost_per_turn"]["map"] == {
        "large": 3,
        "small": 2,
    }


# ---------------------------------------------------------------------------
# The prompt seam
# ---------------------------------------------------------------------------


def test_the_metrics_prompt_gets_totals_and_the_rules_step_gets_source(scenario_dir, tmp_path):
    scenario, _ = run_turns(
        scenario_dir,
        {1: writes(add("A", size="large"), add("B"))},
    )
    builder = PromptBuilder(scenario)

    _system, metrics_prompt = builder.build_metrics_prompt(2, {"gov": "x"}, [])
    assert "Charge 5 capital." in metrics_prompt
    assert "| A |" in metrics_prompt and "| B |" in metrics_prompt
    assert "{{ store" not in metrics_prompt

    # The step that rewrites the rules sees the expression, not its value, or
    # it would write the value back and the expression would be gone for good.
    _system, rules_prompt = builder.build_rules_prompt(2, {"gov": "x"}, [])
    assert "{{ store.sum('measures', 'cost_per_turn', status='running') }}" in rules_prompt


def test_the_actor_sees_its_own_records(scenario_dir, tmp_path):
    scenario, _run_dir = run_turns(
        scenario_dir,
        {1: writes(add("Visible", size="large"))},
    )
    _system, prompt = PromptBuilder(scenario).build_actor_prompt("gov", 2, [])
    assert "Visible" in prompt
    assert "M1" in prompt


def test_derived_status_tracks_the_turn_in_the_prompt(scenario_dir, tmp_path):
    scenario, _run_dir = run_turns(
        scenario_dir,
        {1: writes(add("Short", finish_turn=3))},
    )
    builder = PromptBuilder(scenario)
    _s, before = builder.build_metrics_prompt(2, {"gov": "x"}, [])
    assert "Charge 2 capital." in before
    _s, after = builder.build_metrics_prompt(3, {"gov": "x"}, [])
    assert "Charge 0 capital." in after


# ---------------------------------------------------------------------------
# Resume and branch
# ---------------------------------------------------------------------------


def test_resume_restores_the_records(scenario_dir, tmp_path):
    _scenario, run_dir = run_turns(
        scenario_dir,
        {
            1: writes(add("Carried", size="large")),
            2: writes(add("Also carried")),
        },
    )

    resumed, turn = load_run_state(run_dir)
    assert turn == 2
    names = [r.fields["name"] for r in resumed.store.live_records("measures")]
    assert names == ["Carried", "Also carried"]
    # And the counter, so the next id does not collide with a restored one.
    assert resumed.store.counters["measures"] == 2
    assert StoreView(resumed.store, "gov").sum("measures", "cost_per_turn") == 5


def test_a_resumed_run_does_not_reuse_ids(scenario_dir, tmp_path):
    _scenario, run_dir = run_turns(
        scenario_dir,
        {1: writes(add("First", size="large"))},
    )
    resumed, _turn = load_run_state(run_dir)
    output = OutputManager(resumed, scenario_dir)
    output.run_dir = run_dir
    orchestrator = Orchestrator(
        resumed,
        mock_client({2: writes(add("Second"))}),
        output_manager=output,
    )
    orchestrator.run_turn(2)
    assert [r.id for r in resumed.store.live_records("measures")] == ["M1", "M2"]


# ---------------------------------------------------------------------------
# World tables: the Game Master step writes, every step reads
# ---------------------------------------------------------------------------


WORLD_SCENARIO_YAML = """
name: "Store Test"
description: "A scenario that declares persistent state"
start_date: "2026-01"
time_scale: "6 months per turn"
max_turns: 5
actors:
  - gov
rule_evolution:
  freeze_until_turn: 6
  max_changes_per_turn: 0
store:
  measures:
    scope: actor
    columns:
      id:            {owner: system,  type: text}
      name:          {owner: actor,   type: text, required: true}
      size:          {owner: actor,   type: enum, values: [large, small], required: true}
      started_turn:  {owner: system,  type: turn}
      finish_turn:   {owner: actor,   type: turn, required: true}
      cost_per_turn: {owner: derived, type: integer, from: size, map: {large: 3, small: 2}}
      status:        {owner: derived, type: text, from: finish_turn,
                      when_reached: finished, else: running}
  alliances:
    scope: world
    columns:
      id:     {owner: system, type: text}
      name:   {owner: world,  type: text, required: true}
      standing: {owner: world, type: text}
"""


@pytest.fixture
def world_scenario_dir(tmp_path: Path, scenario_dir: Path) -> Path:
    """The minimal fixture plus one run-owned table."""
    import shutil

    directory = tmp_path / "world-store-test"
    shutil.copytree(scenario_dir, directory)
    (directory / "scenario.yaml").write_text(WORLD_SCENARIO_YAML)
    return directory


def world_metrics_response(alliance_name: str = "River Pact") -> str:
    return (
        '## Metrics\n\n```json\n{"capital": 50}\n```\n\n'
        "## Narrative\n\nThings happened.\n\n## Notepad\n\nNotes.\n\n"
        "## Store changes\n\n```json\n"
        + json.dumps(
            {
                "store": [
                    {
                        "op": "add", "table": "alliances",
                        "fields": {"name": alliance_name, "standing": "strong"},
                        "grounds": "the summit this turn",
                    }
                ]
            }
        )
        + "\n```\n"
    )


def test_the_game_master_step_writes_world_tables(world_scenario_dir, tmp_path):
    """World scope end to end: GM writes, actors read, artifacts persist it."""
    scenario = load_scenario(world_scenario_dir)
    output = OutputManager(scenario, world_scenario_dir)
    run_dir = output.start_run()
    responses = {
        "It is now turn 1.": actor_response(writes(add("Kept", finish_turn=9))),
        # Before "external events": the metrics prompt contains both phrases,
        # and the mock answers the first key that matches.
        "JSON object describing all metrics": world_metrics_response(),
        "external events": "[]",
        "Metric Rules": (
            "# Metric Rules v2 (Turn 1)\n\n## Changelog from v1\n\n"
            "- No material rule changes.\n  - **Motivation:** frozen\n"
            "  - **Expected impact:** none\n\n## Rules\n\n1. Test rule\n"
        ),
        "CURRENT NARRATIVE": "A summary.",
    }
    orchestrator = Orchestrator(
        scenario, MockLLMClient(responses), output_manager=output
    )
    orchestrator.run_turn(1)

    records = scenario.store.live_records("alliances")
    assert [r.fields["name"] for r in records] == ["River Pact"]
    # The actor's write landed in the same turn: one transaction, two writers.
    assert [r.fields["name"] for r in scenario.store.live_records("measures")] == ["Kept"]
    # Read by every step: the actor-scoped view sees the run-owned rows too.
    assert "River Pact" in str(StoreView(scenario.store, "gov").rows("alliances"))

    turn_dir = run_dir / "turn-01"
    assert (turn_dir / "4-world-store.md").exists()
    assert (turn_dir / "4-world-store.json").exists()
    assert "River Pact" in (turn_dir / "4-world-store.md").read_text()

    resumed, turn = load_run_state(run_dir)
    assert turn == 1
    assert [r.fields["name"] for r in resumed.store.live_records("alliances")] == ["River Pact"]
    assert [r.fields["name"] for r in resumed.store.live_records("measures")] == ["Kept"]


def test_an_actor_cannot_write_a_world_table(world_scenario_dir, tmp_path):
    scenario = load_scenario(world_scenario_dir)
    output = OutputManager(scenario, world_scenario_dir)
    output.start_run()
    orchestrator = Orchestrator(scenario, mock_client({}), output_manager=output)
    outcomes = orchestrator._process_store_changes(
        1,
        {
            "gov": "## Store changes\n" + writes(
                {
                    "op": "add", "table": "alliances",
                    "fields": {"name": "Sneaky Pact"},
                }
            )
        },
    )
    assert outcomes["gov"][0].verdict == "rejected"
    assert "world-scoped" in outcomes["gov"][0].reason
    assert scenario.store.live_records("alliances") == []


# ---------------------------------------------------------------------------
# reporting_required: the orchestrator re-asks once instead of only warning
# ---------------------------------------------------------------------------


REPORTING_SCENARIO_YAML = """
name: "Store Test"
description: "A scenario that declares persistent state"
start_date: "2026-01"
time_scale: "6 months per turn"
max_turns: 5
actors:
  - gov
rule_evolution:
  freeze_until_turn: 6
  max_changes_per_turn: 0
store:
  measures:
    scope: actor
    columns:
      id:            {owner: system,  type: text}
      name:          {owner: actor,   type: text, required: true}
      size:          {owner: actor,   type: enum, values: [large, small], required: true}
      started_turn:  {owner: system,  type: turn}
      finish_turn:   {owner: actor,   type: turn, required: true, reporting_required: true}
      cost_per_turn: {owner: derived, type: integer, from: size, map: {large: 3, small: 2}}
      status:        {owner: derived, type: text, from: finish_turn,
                      when_reached: finished, else: running}
"""


@pytest.fixture
def reporting_scenario_dir(tmp_path: Path, scenario_dir: Path) -> Path:
    """The minimal fixture with one column the writer must report every turn."""
    import shutil

    directory = tmp_path / "reporting-store-test"
    shutil.copytree(scenario_dir, directory)
    (directory / "scenario.yaml").write_text(REPORTING_SCENARIO_YAML)
    return directory


def test_a_missing_required_report_is_reasked_not_just_warned(
    reporting_scenario_dir, tmp_path
):
    """Omission is a fault with a repair attempt, recorded either way."""
    scenario = load_scenario(reporting_scenario_dir)
    output = OutputManager(scenario, reporting_scenario_dir)
    run_dir = output.start_run()
    repair = (
        "## Store changes\n```json\n"
        + json.dumps(
            {"store": [{"op": "update", "table": "measures", "id": "M1",
                        "fields": {"finish_turn": 9}}]}
        )
        + "\n```\n"
    )
    responses = {
        "It is now turn 1.": actor_response(writes(add("Kept", finish_turn=9))),
        "required reports were omitted": repair,
        "external events": "[]",
        "Metric Rules": (
            "# Metric Rules v2 (Turn 1)\n\n## Changelog from v1\n\n"
            "- No material rule changes.\n  - **Motivation:** frozen\n"
            "  - **Expected impact:** none\n\n## Rules\n\n1. Test rule\n"
        ),
        "JSON object describing all metrics": (
            '## Metrics\n\n```json\n{"capital": 50}\n```\n\n'
            "## Narrative\n\nThings happened.\n\n## Notepad\n\nNotes."
        ),
        "CURRENT NARRATIVE": "A summary.",
    }
    orchestrator = Orchestrator(
        scenario, MockLLMClient(responses), output_manager=output
    )
    # Turn 2 reports nothing: finish_turn is required every turn, so the
    # orchestrator re-asks once and the repair lands in the same turn.
    orchestrator._process_store_changes(1, {"gov": actor_response(writes(add("Kept", finish_turn=9)))})
    orchestrator._process_store_changes(2, {"gov": "## Store changes\nNo changes.\n"})

    record = scenario.store.find("measures", "M1", "gov")
    assert record is not None
    assert record.fields["finish_turn"] == 9
    text = (run_dir / "turn-02" / "2-actors" / "gov-store.md").read_text()
    assert "on re-ask" in text


# ---------------------------------------------------------------------------
# Scenarios that declare nothing
# ---------------------------------------------------------------------------


def test_a_scenario_without_a_store_is_untouched(tmp_path):
    """Every scenario in the repository predates this mechanism."""
    scenario = load_scenario("scenarios/sweden-ai-2030")
    assert scenario.store is None
    assert not scenario.config.store

    builder = PromptBuilder(scenario)
    _system, prompt = builder.build_metrics_prompt(1, {}, [])
    assert prompt  # renders, with metric_rules passed through untouched
    assert scenario.metric_rules in prompt

    orchestrator = Orchestrator(scenario, mock_client({}))
    assert orchestrator._process_store_changes(1, {"government": "anything"}) == {}
