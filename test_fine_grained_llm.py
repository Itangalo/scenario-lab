"""Test fine-grained LLM configuration (Issue #113)."""

from pathlib import Path
from scenario_lab.loader import load_scenario, load_config
from scenario_lab.orchestrator import Orchestrator

print("="*60)
print("Testing Fine-Grained LLM Configuration (Issue #113)")
print("="*60)

# Test 1: Load old format (backward compatibility)
print("\n[Test 1] Loading old format scenario...")
scenario_old = load_scenario("scenarios/sweden-ai-2030")
print(f"✓ Loaded: {scenario_old.config.name}")
print(f"  LLM Config:")
print(f"    Events: {scenario_old.config.llm.events}")
print(f"    Actors: {scenario_old.config.llm.actors}")
print(f"    Rules: {scenario_old.config.llm.rules}")
print(f"    Metrics: {scenario_old.config.llm.metrics}")

# Test 2: Load new format with per-task models
print("\n[Test 2] Loading fine-grained config...")
config_path = Path("scenarios/sweden-ai-2030/scenario-fine-grained.yaml")
config = load_config(config_path)
print(f"✓ Loaded fine-grained config")
print(f"  LLM Config:")
print(f"    Events: {config.llm.events}")
print(f"    Actors:")
for actor_id, model in config.llm.actors.items():
    print(f"      {actor_id}: {model}")
print(f"    Rules: {config.llm.rules}")
print(f"    Metrics: {config.llm.metrics}")

# Test 3: Verify Orchestrator creates clients correctly
print("\n[Test 3] Creating Orchestrator with fine-grained config...")
scenario_new = load_scenario("scenarios/sweden-ai-2030")
scenario_new.config = config  # Use fine-grained config

orchestrator = Orchestrator(scenario_new, llm_client=None)
print(f"✓ Orchestrator created")
print(f"  Created {len(orchestrator._owned_clients)} LLM clients:")

# Check that correct clients were created
unique_models = set()
unique_models.add(orchestrator.llm_clients["events"].model)
unique_models.add(orchestrator.llm_clients["rules"].model)
unique_models.add(orchestrator.llm_clients["metrics"].model)
for actor_id, client in orchestrator.llm_clients["actors"].items():
    unique_models.add(client.model)

print(f"  Unique models in use:")
for model in sorted(unique_models):
    print(f"    - {model}")

# Verify specific clients
assert orchestrator.llm_clients["events"].model == "x-ai/grok-2-1212", "Events should use grok"
assert orchestrator.llm_clients["rules"].model == "anthropic/claude-3.5-haiku-20241022", "Rules should use haiku"
assert orchestrator.llm_clients["metrics"].model == "anthropic/claude-sonnet-4", "Metrics should use sonnet-4"
assert orchestrator.llm_clients["actors"]["government"].model == "anthropic/claude-3.5-haiku-20241022", "Actors should use haiku"

print("\n✓ All clients configured correctly!")

# Test 4: Verify client reuse (optimization)
print("\n[Test 4] Verifying client reuse optimization...")
events_client = orchestrator.llm_clients["events"]
rules_client = orchestrator.llm_clients["rules"]
metrics_client = orchestrator.llm_clients["metrics"]
actor_clients = [orchestrator.llm_clients["actors"][aid] for aid in scenario_new.config.actor_ids]

# All actors should share the same client (same model)
assert len(set(id(c) for c in actor_clients)) == 1, "All actors should share one client"
print(f"✓ Actor clients are reused (all 4 actors share 1 client instance)")

# Rules client should be same as actor clients (same model)
assert id(rules_client) == id(actor_clients[0]), "Rules should reuse actor client"
print(f"✓ Rules client reuses actor client (same model)")

print(f"\nTotal clients created: {len(orchestrator._owned_clients)}")
print(f"Expected: 3 (grok for events, haiku for actors+rules, sonnet-4 for metrics)")
assert len(orchestrator._owned_clients) == 3, f"Should create exactly 3 clients, created {len(orchestrator._owned_clients)}"
print(f"✓ Optimal number of clients created!")

# Cleanup
orchestrator.close()

print("\n" + "="*60)
print("All tests passed! Issue #113 is implemented correctly.")
print("="*60)
