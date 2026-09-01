"""Tests for scenario validation."""

import pytest
from datetime import date
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
from scenario_lab.model_audit import (
    choose_replacement_model,
    collect_model_hygiene_warnings,
    evaluate_model_hygiene,
    load_model_policy,
)
from scenario_lab.models import Scenario, ScenarioConfig, Metrics, Metric, Event, Actor, WorldState, LLMConfig, Statement


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
    assert is_valid_model_string("google/gemini-3-flash-preview")
    assert is_valid_model_string("google/gemini-3-flash-preview")
    assert is_valid_model_string("qwen/qwen3-235b-a22b-2507")

    # Invalid models
    assert not is_valid_model_string("claude-sonnet-4")  # Missing provider
    assert not is_valid_model_string("google/")  # Missing model name
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

    errors, _ = validate_llm_config(scenario)
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

    errors, _ = validate_llm_config(scenario)
    assert any("max_tokens" in e for e in errors)


def test_validate_llm_config_max_tokens_by_task():
    """Test LLM config per-task max_tokens validation."""
    config = ScenarioConfig(
        name="Test",
        description="Test",
        start_date="2026-01",
        time_scale="6 months",
        max_turns=5,
        actor_ids=["actor1"],
        llm=LLMConfig(max_tokens_by_task={"analysis": 50, "unknown": 500})  # Too low + invalid task
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

    errors, _ = validate_llm_config(scenario)
    assert any("max_tokens_by_task['analysis']" in e for e in errors)
    assert any("invalid task 'unknown'" in e for e in errors)


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

    errors, _ = validate_llm_config(scenario)
    assert any("invalid model string" in e.lower() for e in errors)


def test_evaluate_model_hygiene_warns_for_legacy_and_old_snapshot():
    """Model hygiene checks should flag legacy families and old dated snapshots."""
    warnings = evaluate_model_hygiene(
        "openai/gpt-3.5-turbo-2024-01-15",
        today=date(2026, 3, 4),
    )

    assert len(warnings) >= 2
    assert any("legacy GPT-3.5 family" in warning for warning in warnings)
    assert any("2024-01-15" in warning for warning in warnings)


def test_evaluate_model_hygiene_does_not_warn_for_preview_name_alone():
    """The word 'preview' alone should not trigger a model hygiene warning."""
    warnings = evaluate_model_hygiene(
        "google/gemini-3-flash-preview",
        today=date(2026, 3, 4),
    )

    assert warnings == []


def test_load_model_policy_reads_repo_local_overrides(tmp_path):
    """Model policy YAML should override age threshold and pattern lists."""
    policy_path = tmp_path / "model-policy.yaml"
    policy_path.write_text(
        "\n".join(
            [
                "max_snapshot_age_days: 30",
                "allowed_patterns:",
                "  - '^x-ai/'",
                "blocked_patterns:",
                "  - 'grok-4.1-fast'",
            ]
        ),
        encoding="utf-8",
    )

    policy = load_model_policy(policy_path)

    assert policy.max_snapshot_age_days == 30
    assert policy.allowed_patterns == ["^x-ai/"]
    assert policy.blocked_patterns == ["grok-4.1-fast"]


def test_evaluate_model_hygiene_applies_policy_allowlist_and_blocklist(tmp_path):
    """Policy allowlist/blocklist should add warnings without code changes."""
    policy_path = tmp_path / "model-policy.yaml"
    # Synthetic patterns: this exercises the policy mechanism, so it must not
    # break whenever the project changes which real model it recommends.
    policy_path.write_text(
        "\n".join(
            [
                "max_snapshot_age_days: 365",
                "allowed_patterns:",
                "  - '^qwen/'",
                "blocked_patterns:",
                "  - 'qwen3-235b'",
            ]
        ),
        encoding="utf-8",
    )
    policy = load_model_policy(policy_path)

    blocked_warnings = evaluate_model_hygiene(
        "qwen/qwen3-235b-a22b-2507",
        today=date(2026, 3, 4),
        policy=policy,
    )
    outside_allowlist_warnings = evaluate_model_hygiene(
        "google/gemini-2.0-flash",
        today=date(2026, 3, 4),
        policy=policy,
    )

    assert any("blocked pattern" in warning for warning in blocked_warnings)
    assert any("outside the repository allowlist" in warning for warning in outside_allowlist_warnings)


def test_collect_model_hygiene_warnings_reports_task_names():
    """Scenario-level model hygiene warnings should identify task and scope."""
    config = LLMConfig(
        events="qwen/qwen3-235b-a22b-2507",
        actors="qwen/qwen3-235b-a22b-2507",
        rules="qwen/qwen3-235b-a22b-2507",
        metrics="openai/gpt-3.5-turbo-2024-01-15",
        summary="qwen/qwen3-235b-a22b-2507",
        referee="qwen/qwen3-235b-a22b-2507",
    )

    warnings = collect_model_hygiene_warnings(
        config,
        scope="test-scope",
        today=date(2026, 3, 4),
    )

    assert any("Task 'metrics'" in warning and "2024-01-15" in warning for warning in warnings)
    assert all("Task 'events'" not in warning for warning in warnings)


def test_choose_replacement_model_prefers_newer_and_cheaper_candidate():
    """Replacement selection should prefer a candidate that is both newer and cheaper."""
    catalog = [
        {
            "id": "google/gemini-3-flash-preview",
            "created": 1735689600,
            "context_length": 1000000,
            "pricing": {"prompt": "0.000003", "completion": "0.000004"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
        },
        {
            "id": "google/gemini-2.5-flash",
            "created": 1771113600,
            "context_length": 1000000,
            "pricing": {"prompt": "0.000001", "completion": "0.000002"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
        },
        {
            "id": "qwen/qwen3-235b-a22b-2507",
            "created": 1771113600,
            "context_length": 1000000,
            "pricing": {"prompt": "0.000004", "completion": "0.000005"},
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
        },
    ]
    catalog_by_id = {model["id"]: model for model in catalog}

    suggestion = choose_replacement_model(
        "google/gemini-3-flash-preview",
        catalog,
        catalog_by_id,
        today=date(2026, 3, 4),
    )

    assert suggestion is not None
    assert suggestion["id"] == "google/gemini-2.5-flash"
    assert "newer and cheaper" in suggestion["reason"]


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


def test_validate_time_config_start_date_day_precision_valid():
    """YYYY-MM-DD start dates should be accepted."""
    config = ScenarioConfig(
        name="Test",
        description="Test",
        start_date="2026-03-09",
        time_scale="2 weeks per turn",
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
    assert not any("start_date" in e for e in errors)


def test_validate_time_config_time_scale_parseable():
    """time_scale should include a quantity and supported unit."""
    config = ScenarioConfig(
        name="Test",
        description="Test",
        start_date="2026-01",
        time_scale="fortnight cadence",  # Invalid format
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
    assert any("time_scale" in e for e in errors)


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
            initial_statements=[]
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
    assert result.is_valid
    assert isinstance(result.warnings, list)


# ---------------------------------------------------------------------------
# Regression: model validation after the ModelRoute migration
#
# validate_llm_config was written before config values became ModelRoute
# objects and was never updated. Single models matched neither the str nor the
# list branch and went unchecked; every fallback list failed regardless of its
# contents. Both went unnoticed because one is silent and the other looked like
# a scenario error.
# ---------------------------------------------------------------------------

class TestModelRouteValidation:
    def test_fallback_list_of_routes_is_accepted(self):
        from scenario_lab.models import LLMConfig, ModelRoute
        from scenario_lab.validator import validate_llm_config
        from scenario_lab.models import Scenario, ScenarioConfig, Metrics, WorldState

        config = LLMConfig(
            events=[
                ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507"),
                ModelRoute("openrouter", "google/gemini-3-flash-preview"),
            ]
        )
        scenario = Scenario(
            config=ScenarioConfig(
                name="t", description="d", start_date="2026-01",
                time_scale="1 month", max_turns=5, actor_ids=[], llm=config,
            ),
            metrics=Metrics(metrics={}), events=[], actors={}, metric_rules="",
            world_state=WorldState(narrative="", turn=0, time_period=""), context="",
        )

        errors, _ = validate_llm_config(scenario)
        assert not any("fallback list" in e for e in errors)

    def test_anthropic_model_without_slash_is_accepted(self):
        """vendor/model is an OpenRouter convention, not a universal one."""
        from scenario_lab.validator import is_valid_model_route
        from scenario_lab.models import ModelRoute

        assert is_valid_model_route(ModelRoute("anthropic", "claude-sonnet-4-6"))
        assert is_valid_model_route(ModelRoute("openrouter", "qwen/qwen3-235b-a22b-2507"))

    def test_openrouter_model_without_vendor_is_rejected(self):
        from scenario_lab.validator import is_valid_model_route
        from scenario_lab.models import ModelRoute

        assert not is_valid_model_route(ModelRoute("openrouter", "bare-name"))

    def test_empty_provider_or_model_is_rejected(self):
        from scenario_lab.validator import is_valid_model_route
        from scenario_lab.models import ModelRoute

        assert not is_valid_model_route(ModelRoute("", "qwen/q"))
        assert not is_valid_model_route(ModelRoute("openrouter", ""))
        assert not is_valid_model_route(None)


def make_reference_scenario(metric_rules: str):
    """Minimal scenario for exercising the cross-reference check."""
    from scenario_lab.models import Actor, Event, Metric, Metrics, Scenario, ScenarioConfig, WorldState

    return Scenario(
        config=ScenarioConfig(
            name="t", description="d", start_date="2026-01",
            time_scale="1 week per turn", max_turns=3, actor_ids=["a"],
        ),
        metrics=Metrics(metrics={
            "risk_level": Metric(id="risk_level", description="d", value=10,
                                 min_value=0, max_value=100, unit="index")
        }),
        events=[Event(id="vote_failed", description="d", condition="c", probability="10%")],
        actors={"a": Actor(id="a", name="A", short_description="s",
                           long_description="l", initial_statements=[Statement("g", "position", "g")])},
        metric_rules=metric_rules,
        world_state=WorldState(narrative="n", turn=0, time_period="p"),
        context="c",
    )


def test_metric_rules_may_reference_an_event_by_id():
    """A rule saying "once vote_failed has fired" is exactly what events are for."""
    from scenario_lab.validator import validate_metric_references

    scenario = make_reference_scenario("1. Once `vote_failed` has fired, raise `risk_level`.")

    assert validate_metric_references(scenario) == []


def test_metric_rules_still_reject_unknown_identifiers():
    from scenario_lab.validator import validate_metric_references

    scenario = make_reference_scenario("1. Raise `no_such_thing` when things happen.")

    errors = validate_metric_references(scenario)
    assert len(errors) == 1
    assert "no_such_thing" in errors[0]



def test_validate_event_fields_warns_on_discarded_fields(tmp_path):
    """A field the parser drops is a warning, not a silent no-op."""
    from scenario_lab.validator import validate_event_fields

    (tmp_path / "metrics.md").write_text("## m\n**ID:** m\n**Min:** 0\n**Max:** 10\n**Starting value:** 5\n")
    (tmp_path / "events.md").write_text(
        "## E\n**ID:** e1\n**Condition:** Always\n**Probability:** 0.1\n"
        "**Can repeat:** No\n**Makes the case for:** category 4\n**Description:** x\n"
    )

    warnings = validate_event_fields(tmp_path)

    assert len(warnings) == 1
    assert "Makes the case for" in warnings[0]
    assert "reach no prompt" in warnings[0]


def test_validate_event_fields_silent_when_all_fields_parsed(tmp_path):
    from scenario_lab.validator import validate_event_fields

    (tmp_path / "metrics.md").write_text("## m\n**ID:** m\n**Min:** 0\n**Max:** 10\n**Starting value:** 5\n")
    (tmp_path / "events.md").write_text(
        "## E\n**ID:** e1\n**Condition:** Always\n**Probability:** 0.1\n"
        "**Can repeat:** No\n**Description:** x\n"
    )

    assert validate_event_fields(tmp_path) == []
