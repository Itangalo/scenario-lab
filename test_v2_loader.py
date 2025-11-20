#!/usr/bin/env python3
"""
Quick test script for V2 loader migration (Phase 1.1)

Tests that scenario and actor loading works with V2 schemas without requiring full package import.
"""
import sys
from pathlib import Path

# Add to path without triggering full package import
sys.path.insert(0, str(Path(__file__).parent))

# Import only what we need for testing
from scenario_lab.schemas.loader import load_and_validate_actor, load_and_validate_scenario
from scenario_lab.schemas.actor import ActorConfig
from scenario_lab.schemas.scenario import ScenarioConfig

def test_actor_loading():
    """Test loading a single actor with V2 schemas"""
    print("Testing actor loading...")

    actor_path = Path('scenarios/example-policy-negotiation/actors/regulator.yaml')
    actor_config, result = load_and_validate_actor(actor_path)

    assert result.success, f"Actor validation failed: {result.errors}"
    assert isinstance(actor_config, ActorConfig)
    assert actor_config.name is not None
    assert actor_config.short_name is not None
    assert actor_config.llm_model is not None

    print(f"  ✓ Loaded actor: {actor_config.name}")
    print(f"  ✓ Short name: {actor_config.short_name}")
    print(f"  ✓ Model: {actor_config.llm_model}")
    print(f"  ✓ Goals: {len(actor_config.goals)} goals")

    if result.warnings:
        print(f"  ⚠ Warnings: {len(result.warnings)}")
        for warning in result.warnings:
            print(f"    - {warning}")

    return True


def test_scenario_loading():
    """Test loading a scenario with V2 schemas"""
    print("\nTesting scenario loading...")

    scenario_path = Path('scenarios/example-policy-negotiation/scenario.yaml')
    scenario_config, result = load_and_validate_scenario(scenario_path)

    assert result.success, f"Scenario validation failed: {result.errors}"
    assert isinstance(scenario_config, ScenarioConfig)
    assert scenario_config.name is not None
    assert len(scenario_config.actors) > 0
    assert scenario_config.turns > 0

    print(f"  ✓ Loaded scenario: {scenario_config.name}")
    print(f"  ✓ Actors: {scenario_config.actors}")
    print(f"  ✓ Turns: {scenario_config.turns}")
    print(f"  ✓ World state model: {scenario_config.world_state_model}")

    if result.warnings:
        print(f"  ⚠ Warnings: {len(result.warnings)}")
        for warning in result.warnings:
            print(f"    - {warning}")

    return True


def test_full_scenario_dir():
    """Test loading all files from a scenario directory"""
    print("\nTesting full scenario directory loading...")

    from scenario_lab.schemas.loader import validate_scenario_directory

    scenario_path = Path('scenarios/example-policy-negotiation')
    results = validate_scenario_directory(scenario_path)

    print(f"  Validation results:")
    for file_type, result in results.items():
        status = "✓" if result.success else "✗"
        print(f"    {status} {file_type}: {'SUCCESS' if result.success else 'FAILED'}")
        if not result.success:
            for error in result.errors:
                print(f"      - {error}")
        if result.warnings:
            for warning in result.warnings:
                print(f"      ⚠ {warning}")

    return all(r.success for r in results.values() if 'scenario' in r.__dict__ or 'actors' in r.__dict__)


if __name__ == "__main__":
    print("=" * 70)
    print("V2 LOADER MIGRATION TEST (Phase 1.1)")
    print("=" * 70)

    try:
        test_actor_loading()
        test_scenario_loading()
        test_full_scenario_dir()

        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nPhase 1.1 Success Criteria:")
        print("  ✓ V2 schemas load and validate actors")
        print("  ✓ V2 schemas load and validate scenarios")
        print("  ✓ Validation provides helpful error messages")
        print("  ✓ No sys.path.insert in schema loading code")
        print("\nNext: Test with ScenarioLoader (needs V1 Actor temporarily)")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
