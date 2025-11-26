#!/usr/bin/env python3
"""
Quick test to verify the test scenario loads and runs correctly.

This script tests:
- Configuration loading
- World state initialization
- Basic simulation loop with phase logging
"""

from pathlib import Path
from scenario_lab import Simulation


def test_scenario_loading():
    """Test that the test scenario loads without errors."""
    print("Testing scenario loading...")

    scenario_path = Path("examples/test-scenario")

    if not scenario_path.exists():
        print(f"Error: Test scenario not found at {scenario_path}")
        return False

    try:
        # Initialize simulation
        sim = Simulation(str(scenario_path))

        # Verify configuration loaded
        assert sim.config.name == "AI Governance Test Scenario"
        assert len(sim.config.actors) == 2
        assert "USA" in sim.config.actors
        assert "China" in sim.config.actors

        # Verify metrics loaded
        assert sim.world_state.metrics.world["global_ai_capability"] == 0.5
        assert "USA" in sim.world_state.metrics.actors
        assert "China" in sim.world_state.metrics.actors

        # Verify actor metrics
        usa_metrics = sim.world_state.metrics.actors["USA"]
        assert usa_metrics.public["gdp_trillion"] == 25.5
        assert usa_metrics.private["ai_research_capacity"] == 85

        china_metrics = sim.world_state.metrics.actors["China"]
        assert china_metrics.public["gdp_trillion"] == 17.9
        assert china_metrics.private["ai_research_capacity"] == 80

        # Verify background loaded
        assert "2025" in sim.background_context
        assert len(sim.actor_backgrounds) == 2

        print("✓ Scenario loaded successfully")
        print(f"  - Scenario: {sim.config.name}")
        print(f"  - Actors: {', '.join(sim.config.actors)}")
        print(f"  - Time scale: {sim.config.time_scale}")
        print(f"  - Run ID: {sim.run_id}")

        return True

    except Exception as e:
        print(f"✗ Error loading scenario: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simulation_run():
    """Test that the simulation runs without errors."""
    print("\nTesting simulation run...")

    try:
        sim = Simulation("examples/test-scenario")

        # Run for 2 turns
        print(f"Running simulation for 2 turns...\n")
        sim.run(2)

        # Verify simulation completed (check that run_id exists)
        assert sim.run_id is not None

        print(f"\n✓ Simulation completed successfully")
        print(f"  - Run ID: {sim.run_id}")
        print(f"  - Output dir: {sim.scenario_dir}/runs/{sim.run_id}/")

        return True

    except Exception as e:
        print(f"✗ Error running simulation: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Scenario Lab V3 - Test Scenario Verification")
    print("="*60 + "\n")

    # Test loading
    loading_ok = test_scenario_loading()

    if not loading_ok:
        print("\nTests failed at loading stage.")
        return 1

    # Test running
    running_ok = test_simulation_run()

    if not running_ok:
        print("\nTests failed at running stage.")
        return 1

    print("\n" + "="*60)
    print("All tests passed! ✓")
    print("="*60)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
