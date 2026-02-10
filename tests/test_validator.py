"""Tests for scenario validation."""

import pytest
from pathlib import Path
from scenario_lab.validator import (
    validate_scenario,
    validate_metric_references,
    validate_event_probabilities,
    validate_llm_config,
    validate_actor_references,
    validate_time_config,
    is_static_probability,
    parse_static_probability,
    is_formula_probability,
    is_valid_model_string,
)
from scenario_lab.models import Scenario, ScenarioConfig, Metrics, Metric, Event, Actor, WorldState, LLMConfig


def test_is_static_probability():
    """Test static probability detection."""
    assert is_static_probability("10%")
    assert is_static_probability("5 percent")
    assert is_static_probability("3 procent per runda")
    assert is_static_probability("0.15")
    assert not is_static_probability("unemployment / 100")
    assert not is_static_probability("Double the value of unemployment")


def test_parse_static_probability():
    """Test static probability parsing."""
    assert parse_static_probability("10%") == 0.10
    assert parse_static_probability("5 percent") == 0.05
    assert parse_static_probability("3 procent") == 0.03
    assert parse_static_probability("0.15") == 0.15
    assert parse_static_probability("100%") == 1.0


def test_is_formula_probability():
    """Test formula probability detection."""
    valid_metrics = {"unemployment", "ai_capability"}

    # Should be recognized as formulas
    assert is_formula_probability("unemployment / 100", valid_metrics)
    assert is_formula_probability("2 * unemployment / 100", valid_metrics)
    assert is_formula_probability("min(unemployment, 50) / 100", valid_metrics)

    # Should NOT be recognized as formulas (natural language)
    assert not is_formula_probability("Double the value of unemployment", valid_metrics)
    assert not is_formula_probability("15 percent rounds 1-2", valid_metrics)
    assert not is_formula_probability("Half of the unemployment rate", valid_metrics)


def test_is_valid_model_string():
    """Test model string validation."""
    # Valid models
    assert is_valid_model_string("anthropic/claude-sonnet-4")
    assert is_valid_model_string("openai/gpt-4o")
    assert is_valid_model_string("x-ai/grok-4-fast")

    # Invalid models
    assert not is_valid_model_string("claude-sonnet-4")  # Missing provider
    assert not is_valid_model_string("anthropic/")  # Missing model name
    assert not is_valid_model_string("/claude-sonnet-4")  # Missing provider
    assert not is_valid_model_string("invalid")  # No slash


def test_validate_llm_config_temperature():
    """Test LLM config temperature validation."""
    config = ScenarioConfig(
        name="Test",
        description="Test",
        start_date="2026-01",
        time_scale="6 months",
        max_turns=5,
        actor_ids=["actor1"],
        llm=LLMConfig(temperature=2.5)  # Invalid
    )

    scenario = Scenario(
        config=config,
        metrics=Metrics(metrics={}),
        events=[],
        actors={},
        metric_rules="",
        world_state=WorldState(narrative="", turn=0, time_period=""),
        context=""
    )

    errors = validate_llm_config(scenario)
    assert any("temperature" in e.lower() for e in errors)


def test_validate_llm_config_max_tokens():
    """Test LLM config max_tokens validation."""
    config = ScenarioConfig(
        name="Test",
        description="Test",
        start_date="2026-01",
        time_scale="6 months",
        max_turns=5,
        actor_ids=["actor1"],
        llm=LLMConfig(max_tokens=50)  # Too low
    )

    scenario = Scenario(
        config=config,
        metrics=Metrics(metrics={}),
        events=[],
        actors={},
        metric_rules="",
        world_state=WorldState(narrative="", turn=0, time_period=""),
        context=""
    )

    errors = validate_llm_config(scenario)
    assert any("max_tokens" in e for e in errors)


def test_validate_llm_config_model_string():
    """Test LLM config model string validation."""
    config = ScenarioConfig(
        name="Test",
        description="Test",
        start_date="2026-01",
        time_scale="6 months",
        max_turns=5,
        actor_ids=["actor1"],
        llm=LLMConfig(events="invalid-model")  # Invalid format
    )

    scenario = Scenario(
        config=config,
        metrics=Metrics(metrics={}),
        events=[],
        actors={},
        metric_rules="",
        world_state=WorldState(narrative="", turn=0, time_period=""),
        context=""
    )

    errors = validate_llm_config(scenario)
    assert any("invalid model string" in e.lower() for e in errors)


def test_validate_time_config_start_date():
    """Test start_date validation."""
    config = ScenarioConfig(
        name="Test",
        description="Test",
        start_date="2026-13",  # Invalid month
        time_scale="6 months",
        max_turns=5,
        actor_ids=["actor1"]
    )

    scenario = Scenario(
        config=config,
        metrics=Metrics(metrics={}),
        events=[],
        actors={},
        metric_rules="",
        world_state=WorldState(narrative="", turn=0, time_period=""),
        context=""
    )

    errors = validate_time_config(scenario)
    assert any("start_date" in e for e in errors)


def test_validate_time_config_max_turns():
    """Test max_turns validation."""
    config = ScenarioConfig(
        name="Test",
        description="Test",
        start_date="2026-01",
        time_scale="6 months",
        max_turns=0,  # Invalid
        actor_ids=["actor1"]
    )

    scenario = Scenario(
        config=config,
        metrics=Metrics(metrics={}),
        events=[],
        actors={},
        metric_rules="",
        world_state=WorldState(narrative="", turn=0, time_period=""),
        context=""
    )

    errors = validate_time_config(scenario)
    assert any("max_turns" in e for e in errors)


def test_validate_actor_references():
    """Test actor reference validation."""
    config = ScenarioConfig(
        name="Test",
        description="Test",
        start_date="2026-01",
        time_scale="6 months",
        max_turns=5,
        actor_ids=["actor1", "actor2"]  # actor2 missing
    )

    scenario = Scenario(
        config=config,
        metrics=Metrics(metrics={}),
        events=[],
        actors={"actor1": Actor(
            id="actor1",
            name="Actor 1",
            short_description="Short",
            long_description="Long",
            initial_goals=[]
        )},
        metric_rules="",
        world_state=WorldState(narrative="", turn=0, time_period=""),
        context=""
    )

    errors = validate_actor_references(scenario)
    assert any("actor2" in e for e in errors)


def test_validate_event_probabilities_static():
    """Test validation of static event probabilities."""
    metrics = Metrics(metrics={
        "unemployment": Metric(
            id="unemployment",
            description="Test metric",
            value=5.0,
            min_value=0,
            max_value=100,
            unit="percent"
        )
    })

    events = [
        Event(
            id="event1",
            description="Test",
            condition="No conditions",
            probability="10 percent",
            can_repeat=True
        )
    ]

    scenario = Scenario(
        config=ScenarioConfig(
            name="Test",
            description="Test",
            start_date="2026-01",
            time_scale="6 months",
            max_turns=5,
            actor_ids=[]
        ),
        metrics=metrics,
        events=events,
        actors={},
        metric_rules="",
        world_state=WorldState(narrative="", turn=0, time_period=""),
        context=""
    )

    errors, warnings = validate_event_probabilities(scenario)
    assert len(errors) == 0  # Should pass
    assert len(warnings) == 0


def test_validate_event_probabilities_formula():
    """Test validation of formula event probabilities."""
    metrics = Metrics(metrics={
        "unemployment": Metric(
            id="unemployment",
            description="Test metric",
            value=5.0,
            min_value=0,
            max_value=100,
            unit="percent"
        )
    })

    events = [
        Event(
            id="event1",
            description="Test",
            condition="No conditions",
            probability="unemployment / 100",
            can_repeat=True
        )
    ]

    scenario = Scenario(
        config=ScenarioConfig(
            name="Test",
            description="Test",
            start_date="2026-01",
            time_scale="6 months",
            max_turns=5,
            actor_ids=[]
        ),
        metrics=metrics,
        events=events,
        actors={},
        metric_rules="",
        world_state=WorldState(narrative="", turn=0, time_period=""),
        context=""
    )

    errors, warnings = validate_event_probabilities(scenario)
    assert len(errors) == 0  # Should pass
    assert len(warnings) == 0


def test_validate_event_probabilities_natural_language():
    """Test validation of natural language event probabilities."""
    metrics = Metrics(metrics={
        "unemployment": Metric(
            id="unemployment",
            description="Test metric",
            value=5.0,
            min_value=0,
            max_value=100,
            unit="percent"
        )
    })

    events = [
        Event(
            id="event1",
            description="Test",
            condition="No conditions",
            probability="Double the value of unemployment, in percent",
            can_repeat=True
        )
    ]

    scenario = Scenario(
        config=ScenarioConfig(
            name="Test",
            description="Test",
            start_date="2026-01",
            time_scale="6 months",
            max_turns=5,
            actor_ids=[]
        ),
        metrics=metrics,
        events=events,
        actors={},
        metric_rules="",
        world_state=WorldState(narrative="", turn=0, time_period=""),
        context=""
    )

    errors, warnings = validate_event_probabilities(scenario)
    assert len(errors) == 0  # Natural language should be accepted
    assert len(warnings) == 0


def test_validate_event_probabilities_invalid_formula():
    """Test validation catches invalid formula syntax."""
    metrics = Metrics(metrics={
        "unemployment": Metric(
            id="unemployment",
            description="Test metric",
            value=5.0,
            min_value=0,
            max_value=100,
            unit="percent"
        )
    })

    events = [
        Event(
            id="event1",
            description="Test",
            condition="No conditions",
            probability="unemployment / / 100",  # Syntax error
            can_repeat=True
        )
    ]

    scenario = Scenario(
        config=ScenarioConfig(
            name="Test",
            description="Test",
            start_date="2026-01",
            time_scale="6 months",
            max_turns=5,
            actor_ids=[]
        ),
        metrics=metrics,
        events=events,
        actors={},
        metric_rules="",
        world_state=WorldState(narrative="", turn=0, time_period=""),
        context=""
    )

    errors, warnings = validate_event_probabilities(scenario)
    assert any("syntax" in e.lower() or "error" in e.lower() for e in errors)
    assert len(warnings) == 0


def test_validate_event_probabilities_formula_warning_is_not_error():
    """Formula values over 1 should produce warnings, not hard errors."""
    metrics = Metrics(metrics={
        "unemployment": Metric(
            id="unemployment",
            description="Test metric",
            value=5.0,
            min_value=0,
            max_value=100,
            unit="percent"
        )
    })

    events = [
        Event(
            id="event1",
            description="Test",
            condition="No conditions",
            probability="unemployment * 2",  # Evaluates to 100 with test context
            can_repeat=True
        )
    ]

    scenario = Scenario(
        config=ScenarioConfig(
            name="Test",
            description="Test",
            start_date="2026-01",
            time_scale="6 months",
            max_turns=5,
            actor_ids=[]
        ),
        metrics=metrics,
        events=events,
        actors={},
        metric_rules="",
        world_state=WorldState(narrative="", turn=0, time_period=""),
        context=""
    )

    errors, warnings = validate_event_probabilities(scenario)
    assert len(errors) == 0
    assert any("value > 1" in w for w in warnings)


def test_validate_scenario_sweden_ai_2030():
    """Test validation on real sweden-ai-2030 scenario."""
    scenario_path = Path("scenarios/sweden-ai-2030")
    if not scenario_path.exists():
        pytest.skip("sweden-ai-2030 scenario not found")

    result = validate_scenario(scenario_path)
    # Should have warnings about missing short descriptions, but no errors
    assert result.is_valid
    assert len(result.warnings) > 0  # Expected warnings about short descriptions
