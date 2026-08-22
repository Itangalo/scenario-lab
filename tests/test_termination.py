"""Tests for early termination conditions.

Scenarios with a definite finish (a government forms, a deadline passes) should
stop there rather than simulating a world whose answer is already settled.
"""

import json

import pytest

from scenario_lab.loader import parse_termination
from scenario_lab.models import Metric, Metrics, TerminationCondition
from scenario_lab.validator import eval_boolean_expression, validate_termination


def make_metrics(**values) -> Metrics:
    return Metrics(
        metrics={
            name: Metric(
                id=name,
                description=name,
                value=value,
                min_value=0,
                max_value=100,
                unit="index",
            )
            for name, value in values.items()
        }
    )


class FakeScenario:
    """Minimal stand-in carrying just what validate_termination reads."""

    def __init__(self, metrics, termination):
        self.metrics = metrics
        self.config = type("Config", (), {"termination": termination})()


# --- eval_boolean_expression ------------------------------------------------


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("risk >= 100", True),
        ("risk > 100", False),
        ("risk >= 100 or viability >= 100", True),
        ("risk >= 100 and viability >= 100", False),
        ("viability >= 40 and viability <= 60", True),
        ("max(risk, viability) >= 100", True),
    ],
)
def test_eval_boolean_expression(expression, expected):
    assert eval_boolean_expression(expression, {"risk": 100, "viability": 50}) is expected


def test_eval_boolean_expression_rejects_unknown_metric():
    with pytest.raises(NameError):
        eval_boolean_expression("nonexistent >= 1", {"risk": 100})


def test_eval_boolean_expression_rejects_code_execution():
    """Termination conditions must be no more powerful than probability formulas."""
    with pytest.raises(ValueError):
        eval_boolean_expression("__import__('os').system('true')", {})


def test_eval_boolean_expression_rejects_attribute_access():
    with pytest.raises(ValueError):
        eval_boolean_expression("risk.__class__", {"risk": 1})


# --- parse_termination ------------------------------------------------------


def test_parse_termination_absent_is_empty():
    assert parse_termination(None) == []


def test_parse_termination_reads_fields():
    parsed = parse_termination(
        [{"id": "done", "when": "risk >= 100", "description": "finished"}]
    )

    assert parsed == [TerminationCondition(id="done", when="risk >= 100", description="finished")]


def test_parse_termination_description_optional():
    parsed = parse_termination([{"id": "done", "when": "risk >= 100"}])

    assert parsed[0].description == ""


@pytest.mark.parametrize(
    "value",
    [
        "not a list",
        [["not", "a", "mapping"]],
        [{"when": "risk >= 100"}],
        [{"id": "", "when": "risk >= 100"}],
        [{"id": "done"}],
        [{"id": "done", "when": ""}],
        [{"id": "done", "when": "risk >= 100", "description": 42}],
    ],
)
def test_parse_termination_rejects_malformed(value):
    with pytest.raises(ValueError):
        parse_termination(value)


# --- validate_termination ---------------------------------------------------


def test_validate_termination_accepts_valid_condition():
    scenario = FakeScenario(
        make_metrics(risk=10),
        [TerminationCondition("done", "risk >= 100", "")],
    )

    errors, warnings = validate_termination(scenario)

    assert errors == []
    assert warnings == []


def test_validate_termination_rejects_unknown_metric():
    """Catching this before a paid batch is the whole point."""
    scenario = FakeScenario(
        make_metrics(risk=10),
        [TerminationCondition("done", "nonexistent >= 100", "")],
    )

    errors, _ = validate_termination(scenario)

    assert len(errors) == 1
    assert "cannot evaluate" in errors[0]
    assert "risk" in errors[0]  # names what is available


def test_validate_termination_warns_when_already_true_at_start():
    """A condition true at turn 0 would end every run immediately."""
    scenario = FakeScenario(
        make_metrics(risk=100),
        [TerminationCondition("done", "risk >= 100", "")],
    )

    errors, warnings = validate_termination(scenario)

    assert errors == []
    assert len(warnings) == 1
    assert "turn 1" in warnings[0]


def test_validate_termination_rejects_duplicate_ids():
    scenario = FakeScenario(
        make_metrics(risk=10),
        [
            TerminationCondition("done", "risk >= 100", ""),
            TerminationCondition("done", "risk >= 50", ""),
        ],
    )

    errors, _ = validate_termination(scenario)

    assert any("duplicate" in e for e in errors)


def test_validate_termination_empty_is_fine():
    assert validate_termination(FakeScenario(make_metrics(risk=10), [])) == ([], [])


# --- orchestrator integration -----------------------------------------------


class FakeOrchestratorScenario:
    def __init__(self, metrics, termination):
        self.metrics = metrics
        self.config = type("Config", (), {"termination": termination})()


def check(metrics, termination):
    """Call Orchestrator.check_termination without constructing a full run."""
    from scenario_lab.orchestrator import Orchestrator

    fake = FakeOrchestratorScenario(metrics, termination)
    return Orchestrator.check_termination(type("O", (), {"scenario": fake})())


def test_check_termination_returns_none_when_not_met():
    assert check(make_metrics(risk=50), [TerminationCondition("done", "risk >= 100", "")]) is None


def test_check_termination_returns_the_met_condition():
    triggered = check(
        make_metrics(risk=100), [TerminationCondition("done", "risk >= 100", "finished")]
    )

    assert triggered is not None
    assert triggered.id == "done"


def test_check_termination_returns_first_match_in_order():
    triggered = check(
        make_metrics(risk=100, viability=100),
        [
            TerminationCondition("first", "viability >= 100", ""),
            TerminationCondition("second", "risk >= 100", ""),
        ],
    )

    assert triggered.id == "first"


def test_check_termination_survives_a_broken_condition(capsys):
    """A bad expression must not end every run; it warns and is treated as unmet."""
    result = check(make_metrics(risk=50), [TerminationCondition("bad", "nonexistent >= 1", "")])

    assert result is None
    assert "could not be evaluated" in capsys.readouterr().out


def test_check_termination_without_conditions_is_none():
    assert check(make_metrics(risk=100), []) is None


# --- persistence ------------------------------------------------------------


def test_record_termination_writes_to_summary(tmp_path):
    from scenario_lab.output import OutputManager

    manager = OutputManager.__new__(OutputManager)
    manager.run_dir = tmp_path
    (tmp_path / "summary.json").write_text(json.dumps({"scenario": "test"}), encoding="utf-8")

    manager.record_termination(7, TerminationCondition("done", "risk >= 100", "finished"))

    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["scenario"] == "test"  # existing content preserved
    assert summary["termination"] == {
        "turn": 7,
        "condition_id": "done",
        "when": "risk >= 100",
        "description": "finished",
    }


# --- run_simulation integration ---------------------------------------------


@pytest.fixture
def mock_client():
    """Mock LLM whose metrics update pushes ai_adoption_sweden to 48."""
    from scenario_lab.llm import MockLLMClient

    return MockLLMClient(
        {
            "list of potential external events looks like this": "[]",
            "which actions you want to take during the turn": (
                "## Goals\n\n* Something\n\n## Actions\n\nThe actor acts."
            ),
            "Respond with an updated list of Metric Rules": "1. A rule",
            "A JSON object describing all metrics": (
                '## Metrics\n\n```json\n{"ai_capability": 6, "ai_adoption_sweden": 48, '
                '"unemployment": 7, "public_sentiment_to_ai": 1}\n```\n\n'
                "## Narrative\n\nThings happened.\n\n## Notepad\n\nNotes."
            ),
            "CURRENT NARRATIVE": "Summary.",
            "Constitutional Referee": "APPROVED",
        }
    )


def test_run_simulation_stops_when_condition_is_met(mock_client):
    """Three turns requested, but the finish line is crossed after the first."""
    from scenario_lab.loader import load_scenario
    from scenario_lab.orchestrator import run_simulation

    scenario = load_scenario("scenarios/sweden-ai-2030")
    scenario.config.termination = [
        TerminationCondition("adopted", "ai_adoption_sweden >= 40", "Adoption target reached")
    ]

    results = run_simulation(scenario, mock_client, num_turns=3)

    assert len(results) == 1
    assert results[0].turn == 1


def test_run_simulation_runs_on_when_condition_not_met(mock_client):
    from scenario_lab.loader import load_scenario
    from scenario_lab.orchestrator import run_simulation

    scenario = load_scenario("scenarios/sweden-ai-2030")
    scenario.config.termination = [
        TerminationCondition("never", "ai_adoption_sweden >= 999", "")
    ]

    results = run_simulation(scenario, mock_client, num_turns=2)

    assert len(results) == 2


def test_run_simulation_without_termination_runs_all_turns(mock_client):
    from scenario_lab.loader import load_scenario
    from scenario_lab.orchestrator import run_simulation

    scenario = load_scenario("scenarios/sweden-ai-2030")
    scenario.config.termination = []

    results = run_simulation(scenario, mock_client, num_turns=2)

    assert len(results) == 2
