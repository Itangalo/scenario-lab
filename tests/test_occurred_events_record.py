"""The occurred-events record is history, not the one-shot suppression flag.

Before these tests, `occurred_events` held only non-repeatable events, so a
run's record silently omitted every repeatable one -- precursors included, since
all of them repeat. Analysis then reasoned about escalations whose precursors
were invisible to it. The record and the suppression flag are separate concerns
and are asserted separately here.
"""

import json
from pathlib import Path

import pytest

from scenario_lab.llm import MockLLMClient
from scenario_lab.loader import load_scenario
from scenario_lab.orchestrator import Orchestrator
from scenario_lab.output import OutputManager


@pytest.fixture
def scenario():
    s = load_scenario("scenarios/sweden-ai-2030")
    s.config.random_seed = 42
    return s


def _output_manager(scenario, tmp_path) -> OutputManager:
    om = OutputManager(scenario, tmp_path)
    om.run_dir = tmp_path / "run-test"
    om.run_dir.mkdir(parents=True)
    return om


def _client_firing(event_ids: list[str]) -> MockLLMClient:
    payload = json.dumps([{"id": eid, "probability": 1.0} for eid in event_ids])
    return MockLLMClient({"list of potential external events looks like this": payload})


def _event(scenario, event_id):
    return next(e for e in scenario.events if e.id == event_id)


def test_repeatable_event_enters_the_record(scenario, tmp_path):
    """A repeatable event that fires is recorded as having happened."""
    repeatable = next(e for e in scenario.events if e.can_repeat)
    orchestrator = Orchestrator(
        scenario, _client_firing([repeatable.id]), output_manager=_output_manager(scenario, tmp_path)
    )

    triggered = orchestrator._run_events_step(turn=1)

    assert [e["id"] for e in triggered] == [repeatable.id]
    assert repeatable.id in scenario.occurred_events


def test_repeatable_event_is_not_marked_occurred(scenario, tmp_path):
    """Being in the record must not suppress it: it can still fire again."""
    repeatable = next(e for e in scenario.events if e.can_repeat)
    orchestrator = Orchestrator(
        scenario, _client_firing([repeatable.id]), output_manager=_output_manager(scenario, tmp_path)
    )

    orchestrator._run_events_step(turn=1)

    assert _event(scenario, repeatable.id).occurred is False

    # Fires again next turn rather than being skipped as already-occurred.
    om2 = _output_manager(scenario, tmp_path / "second")
    orchestrator2 = Orchestrator(scenario, _client_firing([repeatable.id]), output_manager=om2)
    assert [e["id"] for e in orchestrator2._run_events_step(turn=2)] == [repeatable.id]


def test_one_shot_event_still_recorded_and_suppressed(scenario, tmp_path):
    """The existing one-shot discipline is unchanged."""
    one_shot = next(e for e in scenario.events if not e.can_repeat)
    orchestrator = Orchestrator(
        scenario, _client_firing([one_shot.id]), output_manager=_output_manager(scenario, tmp_path)
    )

    orchestrator._run_events_step(turn=1)

    assert one_shot.id in scenario.occurred_events
    assert _event(scenario, one_shot.id).occurred is True

    om2 = _output_manager(scenario, tmp_path / "second")
    orchestrator2 = Orchestrator(scenario, _client_firing([one_shot.id]), output_manager=om2)
    assert orchestrator2._run_events_step(turn=2) == []


def test_resume_does_not_mark_repeatables_occurred(scenario, tmp_path):
    """Restoring a record containing repeatables must not suppress them."""
    from scenario_lab.resume import load_run_state

    repeatable = next(e for e in scenario.events if e.can_repeat)
    one_shot = next(e for e in scenario.events if not e.can_repeat)

    # get_scenario_path_from_run walks two levels up from the run directory, so
    # the run has to sit inside a scenario-shaped tree. Symlink the real
    # scenario's resources rather than copying them.
    scen_dir = tmp_path / "sweden-ai-2030"
    (scen_dir / "background").mkdir(parents=True)
    real = Path("scenarios/sweden-ai-2030").resolve()
    for name in ("scenario.yaml", "metrics.md", "events.md", "metric-rules.md"):
        (scen_dir / name).symlink_to(real / name)
    for name in ("actors", "context.md"):
        (scen_dir / "background" / name).symlink_to(real / "background" / name)
    if (real / "constitution.md").exists():
        (scen_dir / "constitution.md").symlink_to(real / "constitution.md")

    run_dir = scen_dir / "runs" / "run-20260101-000000"
    (run_dir / "turn-01" / "2-actors").mkdir(parents=True)
    turn_dir = run_dir / "turn-01"
    (turn_dir / "1-events.json").write_text(
        json.dumps([{"id": repeatable.id}, {"id": one_shot.id}]), encoding="utf-8"
    )
    (turn_dir / "3-metric-rules.md").write_text("rules", encoding="utf-8")
    (turn_dir / "4-metrics.json").write_text(
        json.dumps({m.id: m.value for m in scenario.metrics.metrics.values()}), encoding="utf-8"
    )
    (turn_dir / "4-world-state.md").write_text("state", encoding="utf-8")
    (turn_dir / "5-notepad.md").write_text("notes", encoding="utf-8")
    (turn_dir / "2-actors" / "government.md").write_text("actions", encoding="utf-8")
    (run_dir / "config.json").write_text("{}", encoding="utf-8")
    (run_dir / "summary.json").write_text(
        json.dumps({"occurred_events": [repeatable.id, one_shot.id], "status": "completed"}),
        encoding="utf-8",
    )

    restored, _ = load_run_state(run_dir)

    assert repeatable.id in restored.occurred_events
    assert _event(restored, repeatable.id).occurred is False
    assert _event(restored, one_shot.id).occurred is True


def test_analysis_timeline_is_turn_stamped_and_complete(tmp_path):
    """The analysis context sees every event with its turn, not a flat set."""
    from scenario_lab.analysis import _event_timeline
    from scenario_lab.analysis import RunAnalysisBundle, RunTurnArtifacts

    turns = [
        RunTurnArtifacts(
            turn=1, time_period="2026", events=[{"id": "cyber_recon_wave"}],
            actor_outputs={}, metric_rules="", metric_rules_metadata=None,
            world_state="", metrics={}, constitutional_check=None, notepad="",
            historical_summary="",
        ),
        RunTurnArtifacts(
            turn=3, time_period="2027", events=[
                {"id": "cyber_mass_campaign"}, {"id": "emergent_thing", "emergent": True}
            ],
            actor_outputs={}, metric_rules="", metric_rules_metadata=None,
            world_state="", metrics={}, constitutional_check=None, notepad="",
            historical_summary="",
        ),
    ]
    bundle = RunAnalysisBundle(
        run_dir=tmp_path, scenario_dir=tmp_path, scenario=None, config={},
        summary={"occurred_events": []}, costs=None, turns=turns, metric_overview={},
    )

    timeline = _event_timeline(bundle)

    assert timeline == [
        {"turn": 1, "id": "cyber_recon_wave"},
        {"turn": 3, "id": "cyber_mass_campaign"},
        {"turn": 3, "id": "emergent_thing", "emergent": True},
    ]


def test_event_history_reaches_the_events_prompt(scenario):
    """Gate windows are judged from the record, so it must be in the prompt."""
    from scenario_lab.prompts import PromptBuilder

    scenario.event_log = [
        {"turn": 1, "id": "cyber_recon_wave"},
        {"turn": 3, "id": "cyber_mass_campaign"},
        {"turn": 3, "id": "cyber_mass_campaign"},  # deduplicated within a turn
        {"turn": 5, "id": "not_yet_completed"},
    ]
    _, user_prompt = PromptBuilder(scenario).build_events_prompt(turn=5)

    assert "What has actually fired so far" in user_prompt
    assert "Turn 1 (4 turn(s) ago): cyber_recon_wave" in user_prompt
    assert "Turn 3 (2 turn(s) ago): cyber_mass_campaign" in user_prompt
    # The current turn is not a completed turn and must not count for windows.
    assert "not_yet_completed" not in user_prompt


def test_event_history_absent_on_first_turn(scenario):
    """Nothing has fired yet, so the block is omitted rather than left empty."""
    from scenario_lab.prompts import PromptBuilder

    _, user_prompt = PromptBuilder(scenario).build_events_prompt(turn=1)
    assert "What has actually fired so far" not in user_prompt


def test_branch_truncates_the_event_log(scenario, tmp_path):
    """A branch inherits only what had happened by its branch point."""
    from scenario_lab.resume import load_run_state

    scen_dir = tmp_path / "sweden-ai-2030"
    (scen_dir / "background").mkdir(parents=True)
    real = Path("scenarios/sweden-ai-2030").resolve()
    for name in ("scenario.yaml", "metrics.md", "events.md", "metric-rules.md"):
        (scen_dir / name).symlink_to(real / name)
    for name in ("actors", "context.md"):
        (scen_dir / "background" / name).symlink_to(real / "background" / name)

    run_dir = scen_dir / "runs" / "run-20260101-000000"
    for turn in (1, 2):
        td = run_dir / f"turn-{turn:02d}" / "2-actors"
        td.mkdir(parents=True)
        (td.parent / "1-events.json").write_text("[]", encoding="utf-8")
        (td.parent / "3-metric-rules.md").write_text("rules", encoding="utf-8")
        (td.parent / "4-metrics.json").write_text(
            json.dumps({m.id: m.value for m in scenario.metrics.metrics.values()}), encoding="utf-8"
        )
        (td.parent / "4-world-state.md").write_text("state", encoding="utf-8")
        (td.parent / "5-notepad.md").write_text("notes", encoding="utf-8")
        (td.parent / "6-historical-summary.md").write_text("summary", encoding="utf-8")
        (td / "government.md").write_text("actions", encoding="utf-8")
    (run_dir / "config.json").write_text("{}", encoding="utf-8")
    (run_dir / "summary.json").write_text(json.dumps({
        "occurred_events": [], "status": "completed",
        "event_log": [{"turn": 1, "id": "early"}, {"turn": 2, "id": "late"}],
    }), encoding="utf-8")

    restored, _ = load_run_state(run_dir, from_turn=1)

    assert [e["id"] for e in restored.event_log] == ["early"]
