"""Test scenario inheritance and LLM fallback lists (Issues #114 and #121)."""

from pathlib import Path
from scenario_lab.loader import load_scenario, load_config

print("="*60)
print("Testing Scenario Inheritance (#121) and LLM Fallback (#114)")
print("="*60)

# Test 1: Load base scenario
print("\n[Test 1] Loading base scenario...")
scenario_base = load_scenario("scenarios/sweden-ai-2030")
print(f"✓ Loaded: {scenario_base.config.name}")
print(f"  Max turns: {scenario_base.config.max_turns}")
print(f"  Events model: {scenario_base.config.llm.events}")

# Test 2: Load variant with inheritance
print("\n[Test 2] Loading variant with inheritance...")
# For variants, we need to load the config directly, then construct scenario
config_variant = load_config(Path("scenarios/sweden-ai-2030/variants/quick-test.yaml"))
print(f"✓ Loaded variant config: {config_variant.name}")
print(f"  Max turns (should be 2): {config_variant.max_turns}")
assert config_variant.max_turns == 2, "Turns should be overridden to 2"
print(f"  ✓ Inheritance works - max_turns overridden")

# Verify it inherited other properties
assert config_variant.name == scenario_base.config.name, "Name should be inherited"
assert config_variant.start_date == scenario_base.config.start_date, "Start date should be inherited"
print(f"  ✓ Base properties inherited (name, start_date, etc.)")

# Test 3: Load variant with fallback lists
print("\n[Test 3] Loading variant with fallback lists...")
config_fallback = load_config(Path("scenarios/sweden-ai-2030/variants/cheap-with-fallback.yaml"))
print(f"✓ Loaded fallback config")
print(f"  Events models: {config_fallback.llm.events}")
assert isinstance(config_fallback.llm.events, list), "Events should be a fallback list"
assert len(config_fallback.llm.events) == 3, "Events should have 3 fallback models"
print(f"  ✓ Fallback list loaded correctly ({len(config_fallback.llm.events)} models)")

# Test 4: Verify deep merge
print("\n[Test 4] Testing deep merge of LLM config...")
# The variant overrides llm.events but should keep other llm settings from base
assert config_fallback.llm.temperature == 0.7, "Temperature should be inherited"
assert config_fallback.llm.max_tokens == 2000, "Max tokens should be inherited"
print(f"  ✓ Deep merge works - temperature and max_tokens inherited")

# Test 5: Test LLMConfig.normalize_to_list()
print("\n[Test 5] Testing LLMConfig helper methods...")
single_model = "anthropic/claude-sonnet-4"
model_list = ["model1", "model2", "model3"]

from scenario_lab.models import LLMConfig
config = LLMConfig()

normalized_single = config.normalize_to_list(single_model)
normalized_list = config.normalize_to_list(model_list)

assert normalized_single == ["anthropic/claude-sonnet-4"], "Single model should become list"
assert normalized_list == model_list, "List should stay as list"
print(f"  ✓ normalize_to_list() works correctly")

# Test 6: Test get_actor_models()
print("\n[Test 6] Testing get_actor_models()...")
# Test with string
config_str = LLMConfig(actors="anthropic/claude-sonnet-4")
assert config_str.get_actor_models("government") == "anthropic/claude-sonnet-4"
print(f"  ✓ get_actor_models() works with string")

# Test with list
config_list = LLMConfig(actors=["model1", "model2"])
assert config_list.get_actor_models("government") == ["model1", "model2"]
print(f"  ✓ get_actor_models() works with list")

# Test with dict
config_dict = LLMConfig(actors={"government": ["model1", "model2"], "default": "model3"})
assert config_dict.get_actor_models("government") == ["model1", "model2"]
assert config_dict.get_actor_models("unknown") == "model3"
print(f"  ✓ get_actor_models() works with dict")

print("\n" + "="*60)
print("All tests passed!")
print("="*60)
print("\nFeatures implemented:")
print("  ✓ Scenario inheritance via 'base' field (#121)")
print("  ✓ Deep merge of configurations")
print("  ✓ LLM fallback lists (#114)")
print("  ✓ Per-task and per-actor model selection (#113)")
print("\nExample usage:")
print("  python -m scenario_lab.cli scenarios/sweden-ai-2030/variants/quick-test.yaml")
print("  python -m scenario_lab.cli scenarios/sweden-ai-2030/variants/cheap-with-fallback.yaml")
