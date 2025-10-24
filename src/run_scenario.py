"""
Run Scenario - Main script to execute a scenario simulation
"""
import os
import yaml
import argparse
import requests
from pathlib import Path
from actor_engine import load_actor, Actor
from world_state import WorldState
from world_state_updater import WorldStateUpdater
from cost_tracker import CostTracker
from metrics_tracker import MetricsTracker
from scenario_state_manager import ScenarioStateManager


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


def run_scenario(scenario_path: str, output_path: str = None, max_turns: int = None, credit_limit: float = None, resume_mode: bool = False):
    """
    Run a complete scenario simulation

    Args:
        scenario_path: Path to the scenario directory
        output_path: Path to output directory (default: output/<scenario-name>/run-001)
        max_turns: Optional maximum number of turns to execute before halting
        credit_limit: Optional cost limit - halt if exceeded
        resume_mode: If True, resume from existing state in output_path
    """
    if not resume_mode:
        print(f"Loading scenario from: {scenario_path}")
    else:
        print(f"Resuming scenario from: {output_path}")

    # Initialize state manager first (needed for resume check)
    state_manager = None
    saved_state = None
    start_turn = 1
    started_at = None

    # Handle resume mode
    if resume_mode:
        if output_path is None:
            raise ValueError("--resume requires the run directory path")

        state_manager = ScenarioStateManager(output_path)

        if not state_manager.state_exists():
            raise ValueError(f"No scenario state found in {output_path}")

        saved_state = state_manager.load_state()

        if saved_state['status'] == 'completed':
            print("This scenario run is already completed.")
            return

        # Override scenario_path and other params from saved state
        scenario_path = saved_state['scenario_path']
        start_turn = saved_state['current_turn'] + 1
        started_at = saved_state['execution_metadata']['started_at']

        print(f"  Status: {saved_state['status']}")
        if saved_state['halt_reason']:
            print(f"  Previous halt reason: {saved_state['halt_reason']}")
        print(f"  Resuming from turn {start_turn} of {saved_state['total_turns']}")

    # Load scenario definition
    scenario = load_scenario(scenario_path)
    scenario_name = scenario['name']

    if not resume_mode:
        print(f"Scenario: {scenario_name}")

    # Set up output directory
    if not resume_mode:
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

        # Create state manager for new run
        state_manager = ScenarioStateManager(output_path)

    # Initialize Phase 1 components
    if not resume_mode:
        print("\nInitializing Phase 1 components...")

    # Cost tracker - restore or create new
    if resume_mode and saved_state:
        cost_tracker = CostTracker()
        cost_tracker.total_cost = saved_state['cost_tracker_state']['total_cost']
        cost_tracker.total_tokens = saved_state['cost_tracker_state']['total_tokens']
        cost_tracker.costs_by_actor = saved_state['cost_tracker_state']['costs_by_actor']
        cost_tracker.costs_by_turn = saved_state['cost_tracker_state']['costs_by_turn']
        cost_tracker.world_state_costs = saved_state['cost_tracker_state']['world_state_costs']
        cost_tracker.start_time = saved_state['execution_metadata']['started_at']
        print(f"  Restored cost tracker (${cost_tracker.total_cost:.4f}, {cost_tracker.total_tokens:,} tokens)")
    else:
        cost_tracker = CostTracker()

    # Metrics tracker - restore or create new
    metrics_config_path = os.path.join(scenario_path, 'metrics.yaml')
    if resume_mode and saved_state:
        metrics_tracker = MetricsTracker(metrics_config_path if os.path.exists(metrics_config_path) else None)
        metrics_tracker.metrics_by_turn = saved_state['metrics_tracker_state']['metrics_by_turn']
        metrics_tracker.final_metrics = saved_state['metrics_tracker_state']['final_metrics']
        print(f"  Restored metrics tracker ({len(metrics_tracker.metrics_by_turn)} turns)")
    else:
        metrics_tracker = MetricsTracker(metrics_config_path if os.path.exists(metrics_config_path) else None)

    # World state updater
    world_state_model = scenario.get('world_state_model', 'alibaba/tongyi-deepresearch-30b-a3b:free')
    world_state_updater = WorldStateUpdater(world_state_model)
    if not resume_mode:
        print(f"  World state model: {world_state_model}")

    # World state - restore or create new
    if resume_mode and saved_state:
        # Create WorldState with initial state
        world_state = WorldState(
            initial_state=saved_state['world_state']['states']['0'],
            scenario_name=saved_state['world_state']['scenario_name'],
            turn_duration=saved_state['world_state']['turn_duration']
        )
        # Restore saved data
        world_state.current_turn = saved_state['world_state']['current_turn']
        world_state.states = {int(k): v for k, v in saved_state['world_state']['states'].items()}  # Convert string keys to int
        world_state.actor_decisions = {int(k): v for k, v in saved_state['world_state']['actor_decisions'].items()}  # Convert string keys to int
        print(f"  Restored world state (turn {world_state.current_turn})")
    else:
        world_state = WorldState(
            initial_state=scenario['initial_world_state'],
            scenario_name=scenario_name,
            turn_duration=scenario['turn_duration']
        )

    # Get scenario system prompt
    scenario_system_prompt = scenario.get('system_prompt', '')

    # Load actors - restore or create new
    actors = {}
    actor_models = {}
    if resume_mode and saved_state:
        # Recreate actors from saved state
        for short_name, actor_data in saved_state['actors'].items():
            actor = load_actor(scenario_path, short_name, scenario_system_prompt)
            actors[short_name] = actor
            actor_models[actor.name] = actor.llm_model
        print(f"  Restored {len(actors)} actors")
    else:
        # Load actors from scenario definition
        for actor_short_name in scenario['actors']:
            actor = load_actor(scenario_path, actor_short_name, scenario_system_prompt)
            actors[actor_short_name] = actor
            actor_models[actor.name] = actor.llm_model
            print(f"Loaded actor: {actor.name} ({actor_short_name}) - {actor.llm_model}")

    # Estimate costs (only for new runs)
    num_turns = scenario['turns']
    if not resume_mode:
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

    # Write initial world state (only for new runs)
    if not resume_mode:
        initial_state_md = world_state.to_markdown(0)
        with open(os.path.join(output_path, 'world-state-000.md'), 'w') as f:
            f.write(initial_state_md)
        print("Wrote initial world state")

        # Start cost tracking for new runs
        cost_tracker.start_tracking()
    else:
        print(f"\nResuming execution...")

    # Run simulation for specified number of turns
    if not resume_mode:
        print(f"\nRunning {num_turns} turns...\n")
    else:
        remaining_turns = num_turns - start_turn + 1
        print(f"Continuing for {remaining_turns} more turn(s)...\n")

    for turn in range(start_turn, num_turns + 1):
        try:
            print(f"{'='*60}")
            print(f"TURN {turn}")
            print(f"{'='*60}\n")

            # Check credit limit before processing turn
            if credit_limit and cost_tracker.total_cost >= credit_limit:
                print(f"\n⚠️  Credit limit reached: ${cost_tracker.total_cost:.4f} >= ${credit_limit:.4f}")
                state_manager.save_state(
                    scenario_name=scenario_name,
                    scenario_path=scenario_path,
                    status='halted',
                    current_turn=turn - 1,  # Last completed turn
                    total_turns=num_turns,
                    world_state=world_state,
                    actors=actors,
                    cost_tracker=cost_tracker,
                    metrics_tracker=metrics_tracker,
                    halt_reason='credit_limit',
                    started_at=started_at
                )
                print(f"\nScenario halted. Resume with:")
                print(f"  python src/run_scenario.py --resume {output_path}\n")
                return

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

            # Save state after successful turn completion
            state_manager.save_state(
                scenario_name=scenario_name,
                scenario_path=scenario_path,
                status='running',
                current_turn=turn,
                total_turns=num_turns,
                world_state=world_state,
                actors=actors,
                cost_tracker=cost_tracker,
                metrics_tracker=metrics_tracker,
                halt_reason=None,
                started_at=started_at
            )

            # Check if max_turns reached
            if max_turns and turn >= max_turns:
                print(f"\n⚠️  Reached maximum turns limit: {max_turns}")
                state_manager.mark_halted('max_turns')
                print(f"\nScenario halted after {max_turns} turn(s). Resume with:")
                print(f"  python src/run_scenario.py --resume {output_path}\n")
                return

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Rate limit error - save state and exit gracefully
                print(f"\n⚠️  Rate limit error encountered")
                state_manager.save_state(
                    scenario_name=scenario_name,
                    scenario_path=scenario_path,
                    status='halted',
                    current_turn=turn - 1,  # Last completed turn
                    total_turns=num_turns,
                    world_state=world_state,
                    actors=actors,
                    cost_tracker=cost_tracker,
                    metrics_tracker=metrics_tracker,
                    halt_reason='rate_limit',
                    started_at=started_at
                )
                print(f"\nScenario halted due to API rate limit.")
                print(f"Last completed turn: {turn - 1}")
                print(f"\nWait a few minutes, then resume with:")
                print(f"  python src/run_scenario.py --resume {output_path}\n")
                return
            else:
                # Re-raise other HTTP errors
                raise

    # End cost tracking
    cost_tracker.end_tracking()

    # Set final metrics
    metrics_tracker.set_final_metrics()

    # Mark scenario as completed
    state_manager.mark_completed()

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
    print(f"  - scenario-state.json: Execution state")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description='Run a Scenario Lab simulation')
    parser.add_argument('scenario', nargs='?', help='Path to scenario directory')
    parser.add_argument('--output', '-o', help='Output directory path', default=None)
    parser.add_argument('--resume', help='Resume from run directory path')
    parser.add_argument('--max-turns', type=int, help='Stop after this many turns')
    parser.add_argument('--credit-limit', type=float, help='Halt if cost exceeds this amount')

    args = parser.parse_args()

    # Handle resume mode
    if args.resume:
        run_scenario(
            scenario_path=None,  # Will be loaded from state
            output_path=args.resume,
            max_turns=args.max_turns,
            credit_limit=args.credit_limit,
            resume_mode=True
        )
    else:
        if not args.scenario:
            parser.error("scenario path is required unless using --resume")

        run_scenario(
            scenario_path=args.scenario,
            output_path=args.output,
            max_turns=args.max_turns,
            credit_limit=args.credit_limit,
            resume_mode=False
        )


if __name__ == '__main__':
    main()
