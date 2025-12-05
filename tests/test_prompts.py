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
