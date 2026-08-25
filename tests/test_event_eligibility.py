"""Tests for deterministic event eligibility gates."""

import json

import pytest

from scenario_lab.llm import MockLLMClient
from scenario_lab.loader import load_scenario
from scenario_lab.orchestrator import Orchestrator
from scenario_lab.output import OutputManager
from scenario_lab.prompts import PromptBuilder
from scenario_lab.validator import validate_metric_references


@pytest.fixture
def ff_scenario():
    return load_scenario("scenarios/forking-futures")


def test_loader_parses_eligible_gates(ff_scenario):
    gated = {e.id: e.eligible for e in ff_scenario.events if e.eligible}
    assert "datacenter_protest_wave" in gated
    assert gated["datacenter_protest_wave"] == "public_sentiment_to_ai < 30"
    assert "grid_capacity_crisis" in gated
    assert "and" in gated["talent_drain_to_labs"] and "or" in gated["ai_military_deployment"]


def test_events_list_hides_gate_false_events(ff_scenario):
    builder = PromptBuilder(ff_scenario)
    user = builder._format_events_list()

    # At starting values these gates are false, so the events are not shown.
    for event_id in ["labour_displacement_wave", "china_standards_export", "sovereign_ai_fund"]:
        assert f"**{event_id}**" not in user

    # Ungated events remain.
    assert "**cyber_mass_campaign**" in user


def test_broken_gate_expression_shows_event_with_warning(ff_scenario, capsys):
    ff_scenario.events[0].eligible = "this_is_not_a_metric > 5"
    user = PromptBuilder(ff_scenario)._format_events_list()
    assert "**" + ff_scenario.events[0].id + "**" in user
    assert "could not be evaluated" in capsys.readouterr().out


def test_orchestrator_rejects_candidate_for_closed_gate(ff_scenario, tmp_path):
    # grid_capacity_crisis is gated on economic_context > 70; force it closed.
    ff_scenario.metrics.metrics["economic_context"].value = 50
    payload = json.dumps(
        [{"id": "grid_capacity_crisis", "probability": 0.9}]
    )
    client = MockLLMClient({"list of potential external events looks like this": payload})
    om = OutputManager(ff_scenario, tmp_path)
    om.run_dir = tmp_path / "run-test"
    om.run_dir.mkdir(parents=True)
    orchestrator = Orchestrator(ff_scenario, client, output_manager=om)

    triggered = orchestrator._run_events_step(turn=1)

    assert triggered == []
    entry = json.loads((om.run_dir / "turn-01" / "1-event-evaluations.json").read_text())[0]
    assert entry["skipped"].startswith("Eligibility gate false")
    assert entry["triggered"] is False


def test_validator_flags_unknown_metric_in_gate(ff_scenario):
    ff_scenario.events[0].eligible = "not_a_real_metric < 10"
    errors = validate_metric_references(ff_scenario)
    assert any("eligibility gate references unknown metric" in e for e in errors)


def test_validator_flags_unevaluable_gate(ff_scenario):
    ff_scenario.events[0].eligible = "us_capability >"
    errors = validate_metric_references(ff_scenario)
    assert any("could not be evaluated" in e for e in errors)


def test_occurred_nonrepeatable_candidate_rejected(ff_scenario, tmp_path):
    """A re-proposed one-shot event is skipped, not re-rolled."""
    ff_scenario.metrics.metrics["economic_context"].value = 80  # gate open
    event = next(e for e in ff_scenario.events if e.id == "grid_capacity_crisis")
    event.can_repeat = False
    event.occurred = True
    payload = json.dumps([{"id": "grid_capacity_crisis", "probability": 0.9}])
    client = MockLLMClient({"list of potential external events looks like this": payload})
    om = OutputManager(ff_scenario, tmp_path)
    om.run_dir = tmp_path / "run-test"
    om.run_dir.mkdir(parents=True)
    orchestrator = Orchestrator(ff_scenario, client, output_manager=om)

    triggered = orchestrator._run_events_step(turn=5)

    assert triggered == []
    entry = json.loads((om.run_dir / "turn-05" / "1-event-evaluations.json").read_text())[0]
    assert entry["skipped"] == "Event already occurred and cannot repeat"
