"""
Run Scenario - Main script to execute a scenario simulation
"""
import os
import yaml
import argparse
from pathlib import Path
from actor_engine import load_actor
from world_state import WorldState
from world_state_updater import WorldStateUpdater
from cost_tracker import CostTracker
from metrics_tracker import MetricsTracker


def load_scenario(scenario_path: str):
    """Load scenario definition from YAML"""
    scenario_file = os.path.join(scenario_path, 'scenario.yaml')

    with open(scenario_file, 'r') as f:
        return yaml.safe_load(f)


def find_next_run_number(scenario_output_dir: str) -> int:
    """
    Find the next available run number by checking existing run folders

    Args:
        scenario_output_dir: Path to scenario output directory (e.g., output/test-regulation-negotiation)

    Returns:
        Next available run number (e.g., if run-001 and run-002 exist, returns 3)
    """
    if not os.path.exists(scenario_output_dir):
        return 1

    # Find all run-XXX directories
    existing_runs = []
    for item in os.listdir(scenario_output_dir):
        if item.startswith('run-') and os.path.isdir(os.path.join(scenario_output_dir, item)):
            try:
                # Extract number from run-XXX
                run_num = int(item.split('-')[1])
                existing_runs.append(run_num)
            except (ValueError, IndexError):
                # Skip directories that don't match pattern
                continue

    if not existing_runs:
        return 1

    # Return highest + 1
    return max(existing_runs) + 1


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
        scenario_output_dir = os.path.join(project_root, 'output', scenario_dir_name)

        # Find next available run number
        run_number = find_next_run_number(scenario_output_dir)
        output_path = os.path.join(scenario_output_dir, f'run-{run_number:03d}')

    os.makedirs(output_path, exist_ok=True)
    print(f"Output directory: {output_path}")

    # Initialize Phase 1 components
    print("\nInitializing Phase 1 components...")

    # Cost tracker
    cost_tracker = CostTracker()

    # Metrics tracker
    metrics_config_path = os.path.join(scenario_path, 'metrics.yaml')
    metrics_tracker = MetricsTracker(metrics_config_path if os.path.exists(metrics_config_path) else None)

    # World state updater
    world_state_model = scenario.get('world_state_model', 'alibaba/tongyi-deepresearch-30b-a3b:free')
    world_state_updater = WorldStateUpdater(world_state_model)
    print(f"  World state model: {world_state_model}")

    # Initialize world state
    world_state = WorldState(
        initial_state=scenario['initial_world_state'],
        scenario_name=scenario_name,
        turn_duration=scenario['turn_duration']
    )

    # Get scenario system prompt
    scenario_system_prompt = scenario.get('system_prompt', '')

    # Load actors
    actors = {}
    actor_models = {}
    for actor_short_name in scenario['actors']:
        actor = load_actor(scenario_path, actor_short_name, scenario_system_prompt)
        actors[actor_short_name] = actor
        actor_models[actor.name] = actor.llm_model
        print(f"Loaded actor: {actor.name} ({actor_short_name}) - {actor.llm_model}")

    # Estimate costs
    num_turns = scenario['turns']
    print("\nEstimating costs...")
    cost_estimate = cost_tracker.estimate_scenario_cost(
        num_actors=len(actors),
        num_turns=num_turns,
        actor_models=actor_models,
        world_state_model=world_state_model
    )

    print(f"\nCost Estimate:")
    print(f"  Actors: ${cost_estimate['total'] - cost_estimate['world_state']:.4f}")
    print(f"  World State: ${cost_estimate['world_state']:.4f}")
    print(f"  Total Estimated: ${cost_estimate['total']:.4f}")
    print(f"  Total Tokens (est): {cost_estimate['total_tokens_estimated']:,}\n")

    # Write initial world state
    initial_state_md = world_state.to_markdown(0)
    with open(os.path.join(output_path, 'world-state-000.md'), 'w') as f:
        f.write(initial_state_md)
    print("Wrote initial world state")

    # Start cost tracking
    cost_tracker.start_tracking()

    # Run simulation for specified number of turns
    print(f"\nRunning {num_turns} turns...\n")

    for turn in range(1, num_turns + 1):
        print(f"{'='*60}")
        print(f"TURN {turn}")
        print(f"{'='*60}\n")

        current_state = world_state.get_current_state()

        # Each actor makes a decision simultaneously
        turn_decisions = {}
        actor_decisions_for_world_update = {}

        for actor_short_name, actor in actors.items():
            print(f"  {actor.name} is deciding...")

            decision = actor.make_decision(current_state, turn, num_turns)
            turn_decisions[actor_short_name] = decision

            # Record decision in world state
            world_state.record_actor_decision(turn, actor.name, decision)

            # Track costs
            cost_tracker.record_actor_decision(
                actor_name=actor.name,
                turn=turn,
                model=actor.llm_model,
                tokens_used=decision.get('tokens_used', 0)
            )

            # Extract metrics from actor decision
            metrics_tracker.extract_metrics_from_text(
                turn=turn,
                text=decision['action'],
                actor_name=actor.name
            )

            # Prepare for world state update
            actor_decisions_for_world_update[actor.name] = {
                'reasoning': decision['reasoning'],
                'action': decision['action']
            }

            # Write actor decision to file
            actor_md = world_state.actor_decision_to_markdown(turn, actor.name, decision)
            filename = f"{actor_short_name}-{turn:03d}.md"
            with open(os.path.join(output_path, filename), 'w') as f:
                f.write(actor_md)

            print(f"    ✓ Decision recorded (tokens: {decision.get('tokens_used', 0):,})")

        # Update world state using LLM synthesis
        print(f"\n  Synthesizing world state update...")
        world_update_result = world_state_updater.update_world_state(
            current_state=current_state,
            turn=turn,
            total_turns=num_turns,
            actor_decisions=actor_decisions_for_world_update,
            scenario_name=scenario_name
        )

        new_state = world_update_result['updated_state']
        world_state.update_state(new_state)

        # Track world state update costs
        cost_tracker.record_world_state_update(
            turn=turn,
            model=world_state_model,
            tokens_used=world_update_result['metadata'].get('tokens_used', 0)
        )

        # Extract metrics from world state
        metrics_tracker.extract_metrics_from_text(
            turn=turn,
            text=new_state
        )

        # Write updated world state
        world_state_md = world_state.to_markdown(turn)
        with open(os.path.join(output_path, f'world-state-{turn:03d}.md'), 'w') as f:
            f.write(world_state_md)

        print(f"    ✓ World state updated (tokens: {world_update_result['metadata'].get('tokens_used', 0):,})\n")

    # End cost tracking
    cost_tracker.end_tracking()

    # Set final metrics
    metrics_tracker.set_final_metrics()

    # Print summaries
    cost_tracker.print_summary()
    metrics_tracker.print_summary()

    # Save cost and metrics data
    cost_tracker.save_to_file(os.path.join(output_path, 'costs.json'))
    metrics_tracker.save_to_file(os.path.join(output_path, 'metrics.json'))

    print(f"{'='*60}")
    print(f"Scenario complete!")
    print(f"Output saved to: {output_path}")
    print(f"  - Markdown files: world-state and actor decisions")
    print(f"  - costs.json: Cost breakdown")
    print(f"  - metrics.json: Metrics data")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Run a Scenario Lab simulation')
    parser.add_argument('scenario', help='Path to scenario directory')
    parser.add_argument('--output', '-o', help='Output directory path', default=None)

    args = parser.parse_args()

    run_scenario(args.scenario, args.output)


if __name__ == '__main__':
    main()
