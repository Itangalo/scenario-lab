#!/usr/bin/env python3
"""
Example script demonstrating how to run a Scenario Lab simulation.

Usage:
    python example_run.py <scenario_path> [num_turns]

Example:
    python example_run.py scenarios/ai-governance-crisis 5
"""

import sys
from pathlib import Path

from scenario_lab import Simulation


def main():
    """Run a scenario simulation."""
    if len(sys.argv) < 2:
        print("Usage: python example_run.py <scenario_path> [num_turns]")
        print("\nExample:")
        print("  python example_run.py scenarios/ai-governance-crisis 5")
        sys.exit(1)

    scenario_path = sys.argv[1]
    num_turns = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    # Verify scenario path exists
    if not Path(scenario_path).exists():
        print(f"Error: Scenario path not found: {scenario_path}")
        sys.exit(1)

    print(f"\nScenario Lab V3 - Simulation Runner")
    print(f"{'='*60}\n")
    print(f"Scenario: {scenario_path}")
    print(f"Turns: {num_turns}\n")

    # Create and run simulation
    sim = Simulation(scenario_path)
    sim.run(num_turns)

    print(f"\nSimulation complete!")
    print(f"Run ID: {sim.run_id}")
    print(f"Output: {sim.scenario_dir}/runs/{sim.run_id}/")


if __name__ == "__main__":
    main()
