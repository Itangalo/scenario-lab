"""Tests for event evaluation persistence, seeded rolls, forcing, and LLM I/O logs."""

import json
from pathlib import Path

import pytest

from scenario_lab.llm import LLMResponse, MockLLMClient
from scenario_lab.loader import load_scenario
from scenario_lab.models import EventOverrides
from scenario_lab.orchestrator import Orchestrator
from scenario_lab.output import OutputManager
from scenario_lab.regression import check_run_integrity


@pytest.fixture
def test_scenario():
    """Load the Sweden AI 2030 scenario for testing."""
    return load_scenario("scenarios/sweden-ai-2030")


def _events_client(payload: str) -> MockLLMClient:
    """Mock client that returns the given events payload for the events prompt."""
    return MockLLMClient(
        {"list of potential external events looks like this": payload}
    )


def _recording_output_manager(scenario, tmp_path) -> OutputManager:
    om = OutputManager(scenario, tmp_path)
    om.run_dir = tmp_path / "run-test"
    om.run_dir.mkdir(parents=True)
    return om


# ---------------------------------------------------------------------------
# A1: full event evaluations
# ---------------------------------------------------------------------------


def test_event_evaluations_record_all_candidates(test_scenario, tmp_path):
    """Every candidate event should appear in 1-event-evaluations.json."""
    payload = json.dumps(
        [
            {"id": "ai_breakthrough", "probability": 1.0, "reasoning": "very likely"},
            {"id": "ai_incident_sweden", "probability": 0.0},
            {"id": "not_a_real_event", "probability": 0.5},
            {"id": "strike", "probability": 5},
        ]
    )
    test_scenario.config.random_seed = 42
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(payload), output_manager=om)

    triggered = orchestrator._run_events_step(turn=1)

    evals_path = om.run_dir / "turn-01" / "1-event-evaluations.json"
    assert evals_path.exists()
    evaluations = json.loads(evals_path.read_text(encoding="utf-8"))

    by_id = {entry.get("id"): entry for entry in evaluations}

    # p=1.0 always triggers; extra field preserved.
    assert by_id["ai_breakthrough"]["triggered"] is True
    assert by_id["ai_breakthrough"]["reasoning"] == "very likely"
    assert "roll" in by_id["ai_breakthrough"]

    # p=0.0 never triggers.
    assert by_id["ai_incident_sweden"]["triggered"] is False

    # Unknown event -> skipped, not triggered.
    assert by_id["not_a_real_event"]["skipped"]
    assert by_id["not_a_real_event"]["triggered"] is False

    # Invalid probability -> skipped.
    assert by_id["strike"]["skipped"]
    assert by_id["strike"]["triggered"] is False

    # 1-events.json unchanged shape: only triggered raw dicts.
    triggered_ids = {event["id"] for event in triggered}
    assert triggered_ids == {"ai_breakthrough"}


def test_events_json_format_unchanged(test_scenario, tmp_path):
    """1-events.json still contains only triggered events in the legacy shape."""
    payload = json.dumps([{"id": "ai_breakthrough", "probability": 1.0}])
    test_scenario.config.random_seed = 7
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(payload), output_manager=om)

    triggered = orchestrator._run_events_step(turn=1)
    om.save_events(1, triggered)

    events = json.loads((om.run_dir / "turn-01" / "1-events.json").read_text(encoding="utf-8"))
    assert events == [{"id": "ai_breakthrough", "probability": 1.0}]


# ---------------------------------------------------------------------------
# A2: seeded, recorded randomness
# ---------------------------------------------------------------------------


def test_same_seed_produces_same_rolls(test_scenario):
    """Identical seeds yield identical rolls for the same turn/event."""
    test_scenario.config.random_seed = 12345
    orchestrator = Orchestrator(test_scenario, _events_client("[]"))

    roll_a = orchestrator._event_roll(3, "ai_breakthrough")
    roll_b = orchestrator._event_roll(3, "ai_breakthrough")
    assert roll_a == roll_b


def test_different_seed_generally_differs(test_scenario):
    """Different seeds yield different rolls across a set of events."""
    test_scenario.config.random_seed = 1
    orch1 = Orchestrator(test_scenario, _events_client("[]"))
    rolls1 = [orch1._event_roll(1, f"event_{i}") for i in range(20)]

    test_scenario.config.random_seed = 2
    orch2 = Orchestrator(test_scenario, _events_client("[]"))
    rolls2 = [orch2._event_roll(1, f"event_{i}") for i in range(20)]

    # Rolls should differ for the vast majority of events.
    differing = sum(1 for a, b in zip(rolls1, rolls2) if a != b)
    assert differing >= 18


def test_roll_independent_of_call_order(test_scenario):
    """A roll depends only on (seed, turn, event_id), not on evaluation order."""
    test_scenario.config.random_seed = 999
    orchestrator = Orchestrator(test_scenario, _events_client("[]"))

    direct = orchestrator._event_roll(2, "strike")
    # Evaluate other events first; the strike roll must be unchanged.
    _ = orchestrator._event_roll(2, "ai_breakthrough")
    _ = orchestrator._event_roll(2, "taiwan_blockade")
    assert orchestrator._event_roll(2, "strike") == direct


def test_seed_generated_when_absent(test_scenario):
    """If no seed is configured, the orchestrator generates and records one."""
    test_scenario.config.random_seed = None
    orchestrator = Orchestrator(test_scenario, _events_client("[]"))
    assert isinstance(orchestrator.random_seed, int)
    assert test_scenario.config.random_seed == orchestrator.random_seed


# ---------------------------------------------------------------------------
# A3: event forcing/suppression
# ---------------------------------------------------------------------------


def test_force_event_triggers_regardless_of_probability(test_scenario, tmp_path):
    """A forced event triggers even when probability is 0."""
    payload = json.dumps([{"id": "ai_incident_sweden", "probability": 0.0}])
    test_scenario.config.random_seed = 5
    test_scenario.config.event_overrides = EventOverrides(
        turn=1, force=["ai_incident_sweden"]
    )
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(payload), output_manager=om)

    triggered = orchestrator._run_events_step(turn=1)
    assert {e["id"] for e in triggered} == {"ai_incident_sweden"}

    evaluations = json.loads(
        (om.run_dir / "turn-01" / "1-event-evaluations.json").read_text(encoding="utf-8")
    )
    entry = next(e for e in evaluations if e.get("id") == "ai_incident_sweden")
    assert entry["forced"] is True
    assert entry["triggered"] is True


def test_suppress_event_never_triggers(test_scenario, tmp_path):
    """A suppressed event never triggers even when probability is 1."""
    payload = json.dumps([{"id": "ai_breakthrough", "probability": 1.0}])
    test_scenario.config.random_seed = 5
    test_scenario.config.event_overrides = EventOverrides(
        turn=1, suppress=["ai_breakthrough"]
    )
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(payload), output_manager=om)

    triggered = orchestrator._run_events_step(turn=1)
    assert triggered == []

    evaluations = json.loads(
        (om.run_dir / "turn-01" / "1-event-evaluations.json").read_text(encoding="utf-8")
    )
    entry = next(e for e in evaluations if e.get("id") == "ai_breakthrough")
    assert entry["suppressed"] is True
    assert entry["triggered"] is False


def test_overrides_only_apply_to_their_turn(test_scenario, tmp_path):
    """Overrides scoped to turn N do not affect other turns."""
    payload = json.dumps([{"id": "ai_breakthrough", "probability": 0.0}])
    test_scenario.config.random_seed = 5
    test_scenario.config.event_overrides = EventOverrides(
        turn=1, force=["ai_breakthrough"]
    )
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(payload), output_manager=om)

    # Turn 2 is not the override turn, so p=0.0 must not trigger.
    triggered = orchestrator._run_events_step(turn=2)
    assert triggered == []


# ---------------------------------------------------------------------------
# A4: LLM I/O transcripts
# ---------------------------------------------------------------------------


def test_llm_io_transcripts_written_when_enabled(test_scenario, tmp_path):
    """Enabling llm_io writes a transcript per LLM call."""
    payload = json.dumps([{"id": "ai_breakthrough", "probability": 1.0}])
    test_scenario.config.random_seed = 1
    test_scenario.config.logging.llm_io = True
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(payload), output_manager=om)

    orchestrator._run_events_step(turn=1)

    io_dir = om.run_dir / "turn-01" / "llm-io"
    assert io_dir.exists()
    files = sorted(io_dir.iterdir())
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert files[0].name == "01-events.md"
    assert "## System prompt" in content
    assert "## User prompt" in content
    assert "## Raw response" in content


def test_llm_io_transcripts_absent_when_disabled(test_scenario, tmp_path):
    """Without llm_io, no transcript directory is created."""
    payload = json.dumps([{"id": "ai_breakthrough", "probability": 1.0}])
    test_scenario.config.random_seed = 1
    test_scenario.config.logging.llm_io = False
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(test_scenario, _events_client(payload), output_manager=om)

    orchestrator._run_events_step(turn=1)

    assert not (om.run_dir / "turn-01" / "llm-io").exists()


def test_llm_io_task_name_sanitized(test_scenario, tmp_path):
    """A task name with a colon is sanitized for the filename."""
    # Force the events parse to fail so a `events:format_fix` retry call happens.
    responses = {
        "list of potential external events looks like this": "not json at all",
        "Rewrite it to be a valid JSON array": json.dumps(
            [{"id": "ai_breakthrough", "probability": 1.0}]
        ),
    }
    test_scenario.config.random_seed = 1
    test_scenario.config.logging.llm_io = True
    om = _recording_output_manager(test_scenario, tmp_path)
    orchestrator = Orchestrator(
        test_scenario, MockLLMClient(responses), output_manager=om
    )

    orchestrator._run_events_step(turn=1)

    io_dir = om.run_dir / "turn-01" / "llm-io"
    names = sorted(f.name for f in io_dir.iterdir())
    assert any("events-format_fix" in name for name in names)
    assert all(":" not in name for name in names)


# ---------------------------------------------------------------------------
# Integrity check: optional evaluations file
# ---------------------------------------------------------------------------


def _write_minimal_run(run_dir: Path, *, with_evaluations, evaluations_payload=None):
    run_dir.mkdir(parents=True)
    (run_dir / "config.json").write_text(
        json.dumps({"name": "Test Scenario", "random_seed": 123}), encoding="utf-8"
    )
    metrics = {"gdp": 100}
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "scenario": "Test Scenario",
                "status": "completed",
                "total_turns": 1,
                "final_metrics": metrics,
                "history": [{"turn": 1, "metrics": metrics}],
                "occurred_events": [],
            }
        ),
        encoding="utf-8",
    )
    turn_dir = run_dir / "turn-01"
    turn_dir.mkdir()
    (turn_dir / "1-events.json").write_text(json.dumps([]), encoding="utf-8")
    if with_evaluations:
        (turn_dir / "1-event-evaluations.json").write_text(
            json.dumps(evaluations_payload), encoding="utf-8"
        )
    actors_dir = turn_dir / "2-actors"
    actors_dir.mkdir()
    (actors_dir / "actor.md").write_text("output", encoding="utf-8")
    (turn_dir / "3-metric-rules.md").write_text("# Metric Rules v1\n\nRules", encoding="utf-8")
    (turn_dir / "4-metrics.json").write_text(json.dumps(metrics), encoding="utf-8")
    (turn_dir / "4-world-state.md").write_text("narrative", encoding="utf-8")
    (turn_dir / "5-notepad.md").write_text("notes", encoding="utf-8")


def test_integrity_accepts_run_without_evaluations(tmp_path):
    """Legacy runs lacking the evaluations file remain valid."""
    run_dir = tmp_path / "runs" / "legacy"
    _write_minimal_run(run_dir, with_evaluations=False)
    report = check_run_integrity(run_dir)
    assert report["is_valid"] is True


def test_integrity_accepts_valid_evaluations(tmp_path):
    """A well-formed evaluations file passes validation."""
    run_dir = tmp_path / "runs" / "modern"
    _write_minimal_run(
        run_dir,
        with_evaluations=True,
        evaluations_payload=[
            {"id": "e1", "probability": 0.5, "roll": 0.4, "triggered": True},
            {"id": "e2", "skipped": "Unknown event", "triggered": False},
        ],
    )
    report = check_run_integrity(run_dir)
    assert report["is_valid"] is True


def test_integrity_rejects_malformed_evaluations(tmp_path):
    """A non-skipped entry missing roll is flagged as invalid."""
    run_dir = tmp_path / "runs" / "broken"
    _write_minimal_run(
        run_dir,
        with_evaluations=True,
        evaluations_payload=[{"id": "e1", "probability": 0.5, "triggered": True}],
    )
    report = check_run_integrity(run_dir)
    assert report["is_valid"] is False
    assert any("probability" in err or "roll" in err for err in report["errors"])
