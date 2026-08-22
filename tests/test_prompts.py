import pytest
from pathlib import Path
from scenario_lab.models import Scenario, ScenarioConfig, Metrics, Metric, Actor, WorldState, LLMConfig
from scenario_lab.prompts import PromptBuilder

# Mock data
@pytest.fixture
def mock_scenario(tmp_path):
    metrics = Metrics(metrics={
        "test_metric": Metric(id="test_metric", description="Test Metric", value=50, min_value=0, max_value=100, unit="units")
    })
    
    actors = {
        "actor1": Actor(id="actor1", name="Test Actor 1", short_description="Short Desc 1", long_description="Long Desc 1", initial_goals=[]),
        "actor2": Actor(id="actor2", name="Test Actor 2", short_description="Short Desc 2", long_description="Long Desc 2", initial_goals=[])
    }
    
    config = ScenarioConfig(
        name="Test Scenario",
        description="A test scenario description",
        start_date="2025-01",
        time_scale="1 month",
        max_turns=10,
        actor_ids=["actor1", "actor2"],
        llm=LLMConfig()
    )
    
    world_state = WorldState(narrative="Initial world", turn=0, time_period="Jan 2025")
    
    # Setup directories for custom prompts
    scenario_dir = tmp_path / "scenarios" / "test_scenario"
    (scenario_dir / "system-prompts").mkdir(parents=True, exist_ok=True)
    
    return Scenario(
        config=config,
        metrics=metrics,
        events=[],
        actors=actors,
        metric_rules="",
        world_state=world_state,
        context="Context",
        custom_system_prompts={},
        custom_user_prompts={}
    )

def test_default_template_placeholder_replacement(mock_scenario):
    """Test that default system templates have placeholders replaced."""
    builder = PromptBuilder(mock_scenario)
    
    # Get default actor prompt (using actor1)
    # This uses the template from templates/system-prompts/actor.md
    system_prompt = builder._get_system_prompt("actor", "actor1")
    
    # Check that placeholders are replaced
    assert "Test Actor 1" in system_prompt # {{actor_name}}
    assert "Long Desc 1" in system_prompt # {{actor_description}}
    assert "A test scenario description" in system_prompt # {{scenario_description}}
    assert "{{actor_name}}" not in system_prompt

def test_generic_actor_override(mock_scenario):
    """Test that a generic actor.md in custom prompts overrides the default."""
    
    # Simulate loading a generic actor.md
    custom_prompt_content = "Custom Generic Actor Prompt for {{actor_name}}"
    mock_scenario.custom_system_prompts["actor"] = custom_prompt_content
    
    builder = PromptBuilder(mock_scenario)
    
    # Get actor prompt for actor2
    system_prompt = builder._get_system_prompt("actor", "actor2")
    
    assert "Custom Generic Actor Prompt for Test Actor 2" == system_prompt
    assert "Custom Generic Actor Prompt" in system_prompt

def test_specific_actor_override_precedence(mock_scenario):
    """Test that actor_{id}.md takes precedence over generic actor.md."""
    
    # generic
    mock_scenario.custom_system_prompts["actor"] = "Generic Prompt"
    # specific for actor1
    mock_scenario.custom_system_prompts["actor_actor1"] = "Specific Prompt for {{actor_name}}"
    
    builder = PromptBuilder(mock_scenario)
    
    # actor1 should get specific
    prompt1 = builder._get_system_prompt("actor", "actor1")
    assert "Specific Prompt for Test Actor 1" == prompt1
    
    # actor2 should get generic
    prompt2 = builder._get_system_prompt("actor", "actor2")
    assert "Generic Prompt" in prompt2


def test_rules_prompt_includes_rule_evolution_policy(mock_scenario):
    """Rules prompts should include the active rule-evolution guardrails."""
    mock_scenario.config.rule_evolution.freeze_until_turn = 2
    mock_scenario.config.rule_evolution.max_changes_per_turn = 1

    builder = PromptBuilder(mock_scenario)
    system_prompt, user_prompt = builder.build_rules_prompt(
        turn=1,
        actor_actions={"actor1": "Action 1", "actor2": "Action 2"},
        triggered_events=[],
    )

    assert "No material rule changes" in system_prompt
    assert "Substantive rule changes are not allowed before turn 3" in user_prompt
    assert "Maximum substantive rule changes this turn: 1" in user_prompt


# ---------------------------------------------------------------------------
# Regression: system prompt overrides are Jinja-rendered
#
# Scenario system prompts used to go through a plain string replace handling
# only a few space-free placeholders. A scenario override written as a Jinja
# template reached the model as raw source with every branch present at once,
# so an actor prompt that branched on actor_id made every actor play the first
# branch. Caught in ai-safety-race, where both the US and China played the US.
# ---------------------------------------------------------------------------

def test_system_prompt_override_renders_jinja_conditionals(mock_scenario):
    """Each actor must see only its own branch of a conditional override."""
    mock_scenario.custom_system_prompts["actor"] = (
        "You are {{ actor_name }}.\n"
        "{% if actor_id == 'actor1' %}\n"
        "SECRET_ONE: you believe the threshold is high.\n"
        "{% elif actor_id == 'actor2' %}\n"
        "SECRET_TWO: you believe the threshold is low.\n"
        "{% endif %}\n"
    )
    builder = PromptBuilder(mock_scenario)

    first = builder._get_system_prompt("actor", "actor1")
    second = builder._get_system_prompt("actor", "actor2")

    assert "SECRET_ONE" in first and "SECRET_TWO" not in first
    assert "SECRET_TWO" in second and "SECRET_ONE" not in second
    assert "Test Actor 1" in first and "Test Actor 2" in second
    for prompt in (first, second):
        assert "{%" not in prompt
        assert "{{" not in prompt


def test_system_prompt_override_renders_spaced_placeholders(mock_scenario):
    """Placeholders written with surrounding spaces must resolve."""
    mock_scenario.custom_system_prompts["actor"] = (
        "Name: {{ actor_name }} / {{actor_name}}\nMetric: {{ metric_test_metric }}\n"
    )
    builder = PromptBuilder(mock_scenario)

    prompt = builder._get_system_prompt("actor", "actor1")

    assert prompt.count("Test Actor 1") == 2
    assert "50" in prompt
    assert "{{" not in prompt


def test_legacy_space_free_placeholders_still_work(mock_scenario):
    """Existing overrides using {{actors_list}} must keep working unchanged."""
    mock_scenario.custom_system_prompts["events"] = (
        "Scenario: {{scenario_description}}\nActors:\n{{actors_list}}\nMetrics:\n{{metrics_list}}\n"
    )
    builder = PromptBuilder(mock_scenario)

    prompt = builder._get_system_prompt("events")

    assert "A test scenario description" in prompt
    assert "Test Actor 1: Short Desc 1" in prompt
    assert "test_metric" in prompt
    assert "{{" not in prompt


def test_actor_specific_override_also_renders(mock_scenario):
    """actor_<id>.md overrides take the same render path."""
    mock_scenario.custom_system_prompts["actor_actor2"] = (
        "I am {{ actor_name }} and my id is {{ actor_id }}."
    )
    builder = PromptBuilder(mock_scenario)

    prompt = builder._get_system_prompt("actor", "actor2")

    assert prompt == "I am Test Actor 2 and my id is actor2."


def test_validator_flags_undefined_variable_in_override(mock_scenario):
    """Undefined variables render as empty text, so validation must warn."""
    from scenario_lab.validator import validate_prompt_overrides

    mock_scenario.custom_system_prompts["actor"] = "You are {{ actro_name }}."
    errors, warnings = validate_prompt_overrides(mock_scenario)

    assert errors == []
    assert any("actro_name" in w for w in warnings)


def test_validator_accepts_known_variables(mock_scenario):
    """A correct override produces no warnings."""
    from scenario_lab.validator import validate_prompt_overrides

    mock_scenario.custom_system_prompts["actor"] = (
        "{{ actor_name }} ({{ actor_id }}) sees {{ metric_test_metric }} and {{actors_list}}."
    )
    errors, warnings = validate_prompt_overrides(mock_scenario)

    assert errors == []
    assert warnings == []


def test_validator_flags_broken_jinja_syntax(mock_scenario):
    """Malformed Jinja is an error, not a silent passthrough."""
    from scenario_lab.validator import validate_prompt_overrides

    mock_scenario.custom_system_prompts["actor"] = "{% if actor_id == 'x' %}unclosed"
    errors, _ = validate_prompt_overrides(mock_scenario)

    assert any("invalid Jinja syntax" in e for e in errors)


def test_referee_prompt_includes_the_notepad(mock_scenario):
    """The referee judges constraints that depend on what already happened.

    Without the persistent record it sees only this turn's delta, so a constraint
    phrased "once X has occurred" is unjudgeable -- it will read a narrative that
    does not mention X and conclude X never happened.
    """
    mock_scenario.notepad = "- Speaker granted an exploratory mandate in turn 7."
    builder = PromptBuilder(mock_scenario)

    _, user = builder.build_constitutional_referee_prompt(
        turn=11, previous_metrics={"test_metric": 50}, new_metrics={"test_metric": 60},
        narrative="Nothing procedural happened this week.",
    )

    assert "exploratory mandate in turn 7" in user


def test_referee_correction_prompt_includes_the_notepad(mock_scenario):
    mock_scenario.notepad = "- Formal negotiations began in turn 4."
    builder = PromptBuilder(mock_scenario)

    _, user = builder.build_constitutional_correction_prompt(
        turn=11, previous_metrics={"test_metric": 50}, new_metrics={"test_metric": 60},
        narrative="n", violations="v",
    )

    assert "Formal negotiations began in turn 4" in user


def test_referee_prompt_handles_an_empty_notepad(mock_scenario):
    mock_scenario.notepad = "   "
    builder = PromptBuilder(mock_scenario)

    _, user = builder.build_constitutional_referee_prompt(
        turn=1, previous_metrics={}, new_metrics={}, narrative="n",
    )

    assert "(Empty)" in user


def test_referee_prompt_prefers_this_turns_notepad(mock_scenario):
    """scenario.notepad is only updated after the referee runs.

    Relying on it shows the referee the *previous* turn's record, so a milestone
    recorded this turn is invisible exactly when it matters -- the referee then
    blocks a change that the run's own notes justify.
    """
    mock_scenario.notepad = "- Mandate expected next turn."  # last turn's record
    builder = PromptBuilder(mock_scenario)

    _, user = builder.build_constitutional_referee_prompt(
        turn=10, previous_metrics={}, new_metrics={}, narrative="n",
        notepad="- Speaker has granted the mandate.",
    )

    assert "Speaker has granted the mandate" in user
    assert "Mandate expected next turn" not in user


def test_referee_correction_prompt_prefers_this_turns_notepad(mock_scenario):
    mock_scenario.notepad = "- Stale."
    builder = PromptBuilder(mock_scenario)

    _, user = builder.build_constitutional_correction_prompt(
        turn=10, previous_metrics={}, new_metrics={}, narrative="n", violations="v",
        notepad="- Fresh milestone this turn.",
    )

    assert "Fresh milestone this turn" in user
    assert "Stale" not in user


def test_referee_prompt_falls_back_to_scenario_notepad(mock_scenario):
    """Callers that do not pass one still get the scenario's record."""
    mock_scenario.notepad = "- Recorded earlier."
    builder = PromptBuilder(mock_scenario)

    _, user = builder.build_constitutional_referee_prompt(
        turn=3, previous_metrics={}, new_metrics={}, narrative="n",
    )

    assert "Recorded earlier" in user


def test_metrics_prompt_shows_the_constitution(mock_scenario):
    """The Game Master wrote metrics and narrative blind to the constraints.

    The referee only gates afterwards, so every violation cost an extra round
    trip and the narrative was built on reasoning the constraints forbid --
    the referee could patch the numbers but not the story's logic.
    """
    mock_scenario.constitution = "1. Seats never change.\n2. A bloc with 175 cannot be blocked."
    builder = PromptBuilder(mock_scenario)

    system, _ = builder.build_metrics_prompt(1, {"actor1": "acted"}, [])

    assert "Constitutional Constraints" in system
    assert "A bloc with 175 cannot be blocked" in system


def test_metrics_prompt_omits_the_section_without_a_constitution(mock_scenario):
    mock_scenario.constitution = None
    builder = PromptBuilder(mock_scenario)

    system, _ = builder.build_metrics_prompt(1, {"actor1": "acted"}, [])

    assert "Constitutional Constraints" not in system

