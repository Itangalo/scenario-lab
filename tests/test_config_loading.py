"""Test configuration loading, inheritance, and LLM setup."""

import pytest
import yaml
from pathlib import Path
from scenario_lab.loader import load_scenario, load_config
from scenario_lab.models import LLMConfig, ScenarioConfig
from scenario_lab.orchestrator import Orchestrator
from scenario_lab.models import Metric, Metrics

@pytest.fixture
def setup_scenarios(tmp_path):
    """Create a base scenario and variants in a temporary directory."""
    scenario_dir = tmp_path / "base_scenario"
    scenario_dir.mkdir()
    
    # Create dummy resources
    (scenario_dir / "metrics.md").write_text("""## metric1
**ID:** metric1
**Min:** 0
**Max:** 100
**Value:** 50
**Unit:** points
""")
    (scenario_dir / "events.md").write_text("")
    (scenario_dir / "metric-rules.md").write_text("")
    
    bg_dir = scenario_dir / "background"
    bg_dir.mkdir()
    (bg_dir / "context.md").write_text("Context")
    
    actors_dir = bg_dir / "actors"
    actors_dir.mkdir()
    (actors_dir / "actor1.md").write_text("# Actor 1\n## Short description\nShort\n## Long description\nLong")
    
    # Base config
    base_config = {
        "name": "Base Scenario",
        "description": "Base description",
        "start_date": "2025-01",
        "time_scale": "1 month",
        "max_turns": 10,
        "actors": ["actor1"],
        "rule_evolution": {
            "freeze_until_turn": 2,
            "max_changes_per_turn": 3,
        },
        "constitutional_enforcement": {
            "max_attempts": 3,
            "on_failure": "keep_previous",
        },
        "llm": {
            "temperature": 0.7,
            "events": "openrouter:model-base",
            "actors": "openrouter:model-base",
            "summary": "openrouter:model-summary-base",
            "analysis": "openrouter:model-analysis-base",
            "referee": "openrouter:model-referee-base",
            "max_tokens": 2000,
            "max_tokens_by_task": {
                "rules": 2800,
            },
        }
    }
    (scenario_dir / "scenario.yaml").write_text(yaml.dump(base_config))

    # Variant config (inheritance)
    variants_dir = scenario_dir / "variants"
    variants_dir.mkdir()

    variant_config = {
        "base": "../scenario.yaml",
        "max_turns": 5,  # Override
        "llm": {
            "events": "openrouter:model-variant",  # Override
            "referee": "openrouter:model-referee-variant",  # Override
            "max_tokens_by_task": {
                "rules": 3600,  # Override
            },
        }
    }
    (variants_dir / "variant.yaml").write_text(yaml.dump(variant_config))

    # Fine-grained config
    fine_grained_config = {
        "base": "../scenario.yaml",
        "llm": {
            "events": ["openrouter:model-a", "openrouter:model-b"],  # Fallback list
            "rules": "openrouter:model-rules",
            "metrics": "openrouter:model-metrics",
            "summary": "openrouter:model-summary-fine",
            "analysis": "openrouter:model-analysis-fine",
            "referee": "openrouter:model-referee-fine",
            "max_tokens_by_task": {
                "rules": 3500,
            },
            "actors": {
                "actor1": ["openrouter:model-actor1-a", "openrouter:model-actor1-b"],
                "default": "openrouter:model-default"
            }
        }
    }
    (variants_dir / "fine_grained.yaml").write_text(yaml.dump(fine_grained_config))
    
    return scenario_dir

def test_scenario_inheritance(setup_scenarios):
    """Test that variant inherits and overrides properties correctly."""
    variant_path = setup_scenarios / "variants" / "variant.yaml"
    config = load_config(variant_path)
    
    # Check inherited properties
    assert config.name == "Base Scenario"
    assert config.start_date == "2025-01"
    assert config.actor_ids == ["actor1"]
    from scenario_lab.models import ModelRoute
    assert config.llm.temperature == 0.7
    assert config.llm.actors == ModelRoute("openrouter", "model-base")
    assert config.llm.summary == ModelRoute("openrouter", "model-summary-base")
    assert config.llm.analysis == ModelRoute("openrouter", "model-analysis-base")
    assert config.rule_evolution.freeze_until_turn == 2
    assert config.rule_evolution.max_changes_per_turn == 3
    assert config.constitutional_enforcement.max_attempts == 3
    assert config.constitutional_enforcement.on_failure == "keep_previous"

    # Check overridden properties
    assert config.max_turns == 5
    assert config.llm.events == ModelRoute("openrouter", "model-variant")
    assert config.llm.referee == ModelRoute("openrouter", "model-referee-variant")
    assert config.llm.max_tokens_by_task["rules"] == 3600

def test_fine_grained_llm_config(setup_scenarios):
    """Test loading of complex LLM configurations."""
    config_path = setup_scenarios / "variants" / "fine_grained.yaml"
    config = load_config(config_path)
    
    from scenario_lab.models import ModelRoute
    # Check events fallback list
    assert config.llm.events == [ModelRoute("openrouter", "model-a"), ModelRoute("openrouter", "model-b")]

    # Check specific task models
    assert config.llm.rules == ModelRoute("openrouter", "model-rules")
    assert config.llm.metrics == ModelRoute("openrouter", "model-metrics")
    assert config.llm.summary == ModelRoute("openrouter", "model-summary-fine")
    assert config.llm.analysis == ModelRoute("openrouter", "model-analysis-fine")
    assert config.llm.referee == ModelRoute("openrouter", "model-referee-fine")
    assert config.llm.max_tokens_by_task["rules"] == 3500

    # Check actor specific models
    assert isinstance(config.llm.actors, dict)
    assert config.llm.actors["actor1"] == [
        ModelRoute("openrouter", "model-actor1-a"),
        ModelRoute("openrouter", "model-actor1-b"),
    ]
    assert config.llm.actors["default"] == ModelRoute("openrouter", "model-default")

def test_llm_config_methods():
    """Test helper methods in LLMConfig class."""
    from scenario_lab.models import ModelRoute
    route1 = ModelRoute("openrouter", "model1")
    route_def = ModelRoute("openrouter", "model-def")
    config = LLMConfig(actors={"actor1": route1, "default": route_def})

    # get_actor_routes
    assert config.get_actor_routes("actor1") == route1
    assert config.get_actor_routes("unknown_actor") == route_def

    # normalize_to_list
    route = ModelRoute("openrouter", "model")
    assert config.normalize_to_list(route) == [route]
    r1, r2 = ModelRoute("openrouter", "m1"), ModelRoute("openrouter", "m2")
    assert config.normalize_to_list([r1, r2]) == [r1, r2]

def test_orchestrator_client_creation(setup_scenarios):
    """Test that Orchestrator creates clients according to config."""
    # Load the fine-grained scenario
    # We need to patch load_scenario or just load it directly if load_scenario supports the variant path
    # load_scenario supports .yaml path
    variant_path = setup_scenarios / "variants" / "fine_grained.yaml"
    scenario = load_scenario(variant_path)
    
    orchestrator = Orchestrator(scenario, llm_client=None)
    
    from scenario_lab.models import ModelRoute
    clients = orchestrator.llm_clients

    # Check events router has both routes in its fallback chain
    assert clients["events"].primary_route == ModelRoute("openrouter", "model-a")

    # Check rules router uses the right route
    assert clients["rules"].primary_route == ModelRoute("openrouter", "model-rules")
    assert clients["rules"]._max_tokens == 3500

    # Check actors router for actor1
    assert clients["actors"]["actor1"].primary_route == ModelRoute("openrouter", "model-actor1-a")

    orchestrator.close()


def test_old_style_model_config_sets_summary_and_referee(tmp_path):
    """Legacy llm.model configs should still configure summary/analysis/referee deterministically."""
    config_path = tmp_path / "scenario.yaml"
    config_path.write_text(
        yaml.dump(
            {
                "name": "Legacy Config",
                "description": "Legacy llm.model style",
                "start_date": "2025-01",
                "time_scale": "1 month",
                "max_turns": 2,
                "actors": ["actor1"],
                "llm": {
                    "model": "openrouter:legacy-model",
                },
            }
        )
    )

    from scenario_lab.models import ModelRoute
    config = load_config(config_path)
    assert config.llm.events == ModelRoute("openrouter", "legacy-model")
    assert config.llm.actors == ModelRoute("openrouter", "legacy-model")
    assert config.llm.rules == ModelRoute("openrouter", "legacy-model")
    assert config.llm.metrics == ModelRoute("openrouter", "legacy-model")
    assert config.llm.summary == ModelRoute("openrouter", "legacy-model")
    assert config.llm.analysis == ModelRoute("openrouter", "legacy-model")
    assert config.llm.referee == ModelRoute("openrouter", "x-ai/grok-4.1-fast")
