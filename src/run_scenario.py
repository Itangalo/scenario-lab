"""
Run Scenario - Main script to execute a scenario simulation
"""
import os
import yaml
import argparse
from pathlib import Path
from actor_engine import load_actor
from world_state import WorldState


def load_scenario(scenario_path: str):
    """Load scenario definition from YAML"""
    scenario_file = os.path.join(scenario_path, 'scenario.yaml')

    with open(scenario_file, 'r') as f:
        return yaml.safe_load(f)


def run_scenario(scenario_path: str, output_path: str = None):
    """
    Run a complete scenario simulation

    Args:
        scenario_path: Path to the scenario directory
        output_path: Path to output directory (default: output/<scenario-name>/run-001)
    """
    print(f"Loading scenario from: {scenario_path}")

    # Load scenario definition
    scenario = load_scenario(scenario_path)
    scenario_name = scenario['name']
    print(f"Scenario: {scenario_name}")

    # Set up output directory
    if output_path is None:
        # Find project root (where this script's parent directory is)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        scenario_dir_name = os.path.basename(scenario_path)
        output_path = os.path.join(project_root, 'output', scenario_dir_name, 'run-001')

    os.makedirs(output_path, exist_ok=True)
    print(f"Output directory: {output_path}")

    # Initialize world state
    world_state = WorldState(
        initial_state=scenario['initial_world_state'],
        scenario_name=scenario_name,
        turn_duration=scenario['turn_duration']
    )

    # Load actors
    actors = {}
    for actor_short_name in scenario['actors']:
        actor = load_actor(scenario_path, actor_short_name)
        actors[actor_short_name] = actor
        print(f"Loaded actor: {actor.name} ({actor_short_name})")

    # Write initial world state
    initial_state_md = world_state.to_markdown(0)
    with open(os.path.join(output_path, 'world-state-000.md'), 'w') as f:
        f.write(initial_state_md)
    print("\nWrote initial world state")

    # Run simulation for specified number of turns
    num_turns = scenario['turns']
    print(f"\nRunning {num_turns} turns...\n")

    for turn in range(1, num_turns + 1):
        print(f"{'='*60}")
        print(f"TURN {turn}")
        print(f"{'='*60}\n")

        current_state = world_state.get_current_state()

        # Each actor makes a decision simultaneously
        turn_decisions = {}

        for actor_short_name, actor in actors.items():
            print(f"  {actor.name} is deciding...")

            decision = actor.make_decision(current_state, turn)
            turn_decisions[actor_short_name] = decision

            # Record decision
            world_state.record_actor_decision(turn, actor.name, decision)

            # Write actor decision to file
            actor_md = world_state.actor_decision_to_markdown(turn, actor.name, decision)
            filename = f"{actor_short_name}-{turn:03d}.md"
            with open(os.path.join(output_path, filename), 'w') as f:
                f.write(actor_md)

            print(f"    ✓ Decision recorded")

        # Update world state based on all actors' decisions
        print(f"\n  Updating world state...")
        new_state = update_world_state(current_state, turn_decisions, actors, turn)
        world_state.update_state(new_state)

        # Write updated world state
        world_state_md = world_state.to_markdown(turn)
        with open(os.path.join(output_path, f'world-state-{turn:03d}.md'), 'w') as f:
            f.write(world_state_md)

        print(f"    ✓ World state updated\n")

    print(f"{'='*60}")
    print(f"Scenario complete!")
    print(f"Output saved to: {output_path}")
    print(f"{'='*60}")


def update_world_state(current_state: str, turn_decisions: dict, actors: dict, turn: int) -> str:
    """
    Generate updated world state based on actor decisions

    For the PoC, this is a simple text summary. In the full version,
    this would use an LLM to generate a rich narrative update.
    """
    # Simple approach: concatenate current state with actions
    new_state = f"{current_state}\n\n## Turn {turn} Actions\n\n"

    for actor_short_name, decision in turn_decisions.items():
        actor = actors[actor_short_name]
        new_state += f"**{actor.name}:**\n{decision['action']}\n\n"

    new_state += "\n## Current Status\n\n"
    new_state += "The negotiation continues. Both parties have taken their positions for this turn."

    return new_state


def main():
    parser = argparse.ArgumentParser(description='Run a Scenario Lab simulation')
    parser.add_argument('scenario', help='Path to scenario directory')
    parser.add_argument('--output', '-o', help='Output directory path', default=None)

    args = parser.parse_args()

    run_scenario(args.scenario, args.output)


if __name__ == '__main__':
    main()
