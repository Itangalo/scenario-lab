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
        "llm": {
            "temperature": 0.7,
            "events": "model-base",
            "actors": "model-base",
            "summary": "model-summary-base",
            "referee": "model-referee-base",
        }
    }
    (scenario_dir / "scenario.yaml").write_text(yaml.dump(base_config))
    
    # Variant config (inheritance)
    variants_dir = scenario_dir / "variants"
    variants_dir.mkdir()
    
    variant_config = {
        "base": "../scenario.yaml",
        "max_turns": 5, # Override
        "llm": {
            "events": "model-variant", # Override
            "referee": "model-referee-variant", # Override
        }
    }
    (variants_dir / "variant.yaml").write_text(yaml.dump(variant_config))
    
    # Fine-grained config
    fine_grained_config = {
        "base": "../scenario.yaml",
        "llm": {
            "events": ["model-a", "model-b"], # Fallback list
            "rules": "model-rules",
            "metrics": "model-metrics",
            "summary": "model-summary-fine",
            "referee": "model-referee-fine",
            "actors": {
                "actor1": ["model-actor1-a", "model-actor1-b"],
                "default": "model-default"
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
    assert config.llm.temperature == 0.7
    assert config.llm.actors == "model-base"
    assert config.llm.summary == "model-summary-base"
    
    # Check overridden properties
    assert config.max_turns == 5
    assert config.llm.events == "model-variant"
    assert config.llm.referee == "model-referee-variant"

def test_fine_grained_llm_config(setup_scenarios):
    """Test loading of complex LLM configurations."""
    config_path = setup_scenarios / "variants" / "fine_grained.yaml"
    config = load_config(config_path)
    
    # Check events fallback list
    assert config.llm.events == ["model-a", "model-b"]
    
    # Check specific task models
    assert config.llm.rules == "model-rules"
    assert config.llm.metrics == "model-metrics"
    assert config.llm.summary == "model-summary-fine"
    assert config.llm.referee == "model-referee-fine"
    
    # Check actor specific models
    assert isinstance(config.llm.actors, dict)
    assert config.llm.actors["actor1"] == ["model-actor1-a", "model-actor1-b"]
    assert config.llm.actors["default"] == "model-default"

def test_llm_config_methods():
    """Test helper methods in LLMConfig class."""
    config = LLMConfig(actors={"actor1": "model1", "default": "model-def"})
    
    # get_actor_models
    assert config.get_actor_models("actor1") == "model1"
    assert config.get_actor_models("unknown_actor") == "model-def"
    
    # normalize_to_list
    assert config.normalize_to_list("model") == ["model"]
    assert config.normalize_to_list(["m1", "m2"]) == ["m1", "m2"]

def test_orchestrator_client_creation(setup_scenarios):
    """Test that Orchestrator creates clients according to config."""
    # Load the fine-grained scenario
    # We need to patch load_scenario or just load it directly if load_scenario supports the variant path
    # load_scenario supports .yaml path
    variant_path = setup_scenarios / "variants" / "fine_grained.yaml"
    scenario = load_scenario(variant_path)
    
    orchestrator = Orchestrator(scenario, llm_client=None)
    
    clients = orchestrator.llm_clients
    
    # Check events client
    assert clients["events"].models == ["model-a", "model-b"]
    
    # Check rules client
    assert clients["rules"].models == ["model-rules"]
    
    # Check actors client
    # actor1 should have its specific client
    assert clients["actors"]["actor1"].models == ["model-actor1-a", "model-actor1-b"]
    
    # Check reuse (optimization check)
    # If we had another actor using the same model, they should share client.
    # Let's test that manually.
    
    orchestrator.close()


def test_old_style_model_config_sets_summary_and_referee(tmp_path):
    """Legacy llm.model configs should still configure summary/referee deterministically."""
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
                    "model": "legacy-model",
                },
            }
        )
    )

    config = load_config(config_path)
    assert config.llm.events == "legacy-model"
    assert config.llm.actors == "legacy-model"
    assert config.llm.rules == "legacy-model"
    assert config.llm.metrics == "legacy-model"
    assert config.llm.summary == "legacy-model"
    assert config.llm.referee == "x-ai/grok-4.1-fast"
