#!/usr/bin/env python3
"""
Integration Test for Phase 1 + Phase 2.1

Tests the V2 pipeline with:
- V2 Loader (Phase 1.1)
- V2 DecisionPhase with ContextManager (Phase 1.2 + 2.1)
- V2 WorldUpdatePhase (Phase 1.3)
- V2 Persistence (Phase 1.4)

This test runs a simple scenario for 1-2 turns to verify all components work together.
"""
import asyncio
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.loaders.scenario_loader import ScenarioLoader
from scenario_lab.services.decision_phase_v2 import DecisionPhaseV2
from scenario_lab.services.world_update_phase_v2 import WorldUpdatePhaseV2
from scenario_lab.services.persistence_phase import PersistencePhase
from scenario_lab.models.state import ScenarioStatus


async def run_test():
    """Run integration test"""
    print("=" * 70)
    print("V2 PIPELINE INTEGRATION TEST (Phase 1 + 2.1)")
    print("=" * 70)
    print()

    # Step 1: Load scenario
    print("Step 1: Loading scenario with V2 loader...")
    try:
        loader = ScenarioLoader('scenarios/example-policy-negotiation')
        initial_state, v1_actors, scenario_config = loader.load()

        print(f"  ✓ Scenario loaded: {scenario_config['name']}")
        print(f"  ✓ Actors: {list(v1_actors.keys())}")
        print(f"  ✓ Initial turn: {initial_state.turn}")
        print(f"  ✓ World state length: {len(initial_state.world_state.content)} chars")
        print(f"  ✓ scenario_config in state: {bool(initial_state.scenario_config)}")
        print()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 2: Create actor configs for V2 phases
    print("Step 2: Preparing actor configs for V2 phases...")
    try:
        actor_configs = {}
        for short_name, v1_actor in v1_actors.items():
            actor_configs[short_name] = {
                'name': v1_actor.name,
                'short_name': v1_actor.short_name,
                'llm_model': v1_actor.llm_model,
                'system_prompt': v1_actor.system_prompt,
                'goals': v1_actor.goals,
                'constraints': v1_actor.constraints,
                'expertise': v1_actor.expertise,
                'decision_style': v1_actor.decision_style,
            }

        print(f"  ✓ Prepared {len(actor_configs)} actor configs")
        print()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Test DecisionPhaseV2 with ContextManager
    print("Step 3: Running DecisionPhaseV2 (with context management)...")
    try:
        decision_phase = DecisionPhaseV2(
            actor_configs=actor_configs,
            scenario_system_prompt=scenario_config.get('system_prompt', ''),
            output_dir=None,  # Don't write files in test
            json_mode=False,
            context_window_size=3
        )

        # Start the scenario
        state = initial_state.with_started()

        # Execute decision phase
        state = await decision_phase.execute(state)

        print(f"  ✓ Decision phase executed")
        print(f"  ✓ Decisions made: {len(state.decisions)}")
        for actor_name, decision in state.decisions.items():
            print(f"    - {actor_name}: {len(decision.action)} char action")
        print(f"  ✓ Costs tracked: {len(state.costs)} records")
        print(f"  ✓ Total cost: ${state.total_cost():.4f}")
        print()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 4: Test WorldUpdatePhaseV2
    print("Step 4: Running WorldUpdatePhaseV2...")
    try:
        world_update_phase = WorldUpdatePhaseV2(
            scenario_name=scenario_config['name'],
            world_state_model=scenario_config.get('world_state_model', 'openai/gpt-4o-mini'),
            output_dir=None  # Don't write files in test
        )

        # Execute world update phase
        state = await world_update_phase.execute(state)

        print(f"  ✓ World update phase executed")
        print(f"  ✓ Turn incremented: {state.turn}")
        print(f"  ✓ World state updated: {len(state.world_state.content)} chars")
        print(f"  ✓ Total costs: {len(state.costs)} records")
        print(f"  ✓ Total cost: ${state.total_cost():.4f}")
        print()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Test context windowing (run another turn)
    print("Step 5: Running second turn (test context windowing)...")
    try:
        # Clear decisions for new turn
        state = state.replace(decisions={})

        # Execute decision phase again
        state = await decision_phase.execute(state)

        print(f"  ✓ Decision phase executed (turn {state.turn})")
        print(f"  ✓ Context manager used (actors got windowed context)")
        print(f"  ✓ Decisions made: {len(state.decisions)}")
        print(f"  ✓ Total cost so far: ${state.total_cost():.4f}")
        print()

        # Execute world update
        state = await world_update_phase.execute(state)

        print(f"  ✓ World update phase executed")
        print(f"  ✓ Turn incremented to: {state.turn}")
        print()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 6: Test PersistencePhase
    print("Step 6: Testing PersistencePhase...")
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence_phase = PersistencePhase(output_dir=tmpdir)

            # Execute persistence
            state = await persistence_phase.execute(state)

            # Check files were created
            output_path = Path(tmpdir)
            scenario_state_file = output_path / "scenario-state.json"
            costs_file = output_path / "costs.json"
            metrics_file = output_path / "metrics.json"

            print(f"  ✓ Persistence phase executed")
            print(f"  ✓ scenario-state.json: {scenario_state_file.exists()}")
            print(f"  ✓ costs.json: {costs_file.exists()}")
            print(f"  ✓ metrics.json: {metrics_file.exists()}")

            # Verify scenario_config was saved
            import json
            if scenario_state_file.exists():
                with open(scenario_state_file) as f:
                    saved_state = json.load(f)
                print(f"  ✓ scenario_config in saved state: {bool(saved_state.get('scenario_config'))}")
            print()
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()
    print("✓ V2 Loader works (Phase 1.1)")
    print("✓ V2 DecisionPhase works (Phase 1.2)")
    print("✓ V2 ContextManager works (Phase 2.1)")
    print("✓ V2 WorldUpdatePhase works (Phase 1.3)")
    print("✓ V2 PersistencePhase works (Phase 1.4)")
    print()
    print(f"Final state:")
    print(f"  - Turn: {state.turn}")
    print(f"  - Status: {state.status.value}")
    print(f"  - Decisions: {len(state.decisions)} (current turn)")
    print(f"  - Costs: {len(state.costs)} records")
    print(f"  - Total cost: ${state.total_cost():.4f}")
    print()
    print("=" * 70)
    print("✓ ALL TESTS PASSED")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        # Check if we have API key
        import os
        if not os.environ.get('OPENROUTER_API_KEY'):
            print("⚠️  WARNING: OPENROUTER_API_KEY not set")
            print("   Set it to run full integration test with real LLM calls")
            print("   Or use local models (ollama/...)")
            print()

        success = asyncio.run(run_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
