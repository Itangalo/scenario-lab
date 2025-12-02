"""Command-line interface for Scenario Lab V4."""

import argparse
from pathlib import Path
from dotenv import load_dotenv

from .loader import load_scenario
from .llm import LLMClient
from .orchestrator import run_simulation
from .output import OutputManager


def main():
    """CLI entry point."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Scenario Lab V4 - LLM-driven scenario simulation"
    )
    parser.add_argument("scenario", type=Path, help="Path to scenario directory")
    parser.add_argument(
        "--turns",
        type=int,
        default=None,
        help="Number of turns to run (default: from config)",
    )
    parser.add_argument(
        "--model", type=str, default=None, help="Override LLM model"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print prompts without calling LLM"
    )

    args = parser.parse_args()

    # Load scenario
    print(f"Loading scenario from {args.scenario}...")
    scenario = load_scenario(args.scenario)
    print(f"✓ Loaded: {scenario.config.name}")
    print(f"  Actors: {len(scenario.actors)}")
    print(f"  Metrics: {len(scenario.metrics.metrics)}")
    print(f"  Events: {len(scenario.events)}")

    if args.model:
        # Override all task models if --model is specified
        scenario.config.llm.events = args.model
        scenario.config.llm.actors = args.model
        scenario.config.llm.rules = args.model
        scenario.config.llm.metrics = args.model

    if args.dry_run:
        run_dry(scenario)
        return

    # Run simulation
    print(f"\nRunning simulation: {scenario.config.name}")
    print(f"LLM Configuration:")
    print(f"  Events: {scenario.config.llm.events}")
    if isinstance(scenario.config.llm.actors, str):
        print(f"  Actors: {scenario.config.llm.actors} (all)")
    else:
        print(f"  Actors:")
        for actor_id, model in scenario.config.llm.actors.items():
            print(f"    {actor_id}: {model}")
    print(f"  Rules: {scenario.config.llm.rules}")
    print(f"  Metrics: {scenario.config.llm.metrics}")
    print(f"Turns: {args.turns or scenario.config.max_turns}")

    output_manager = OutputManager(scenario, args.scenario)
    run_dir = output_manager.start_run()
    print(f"Output directory: {run_dir.name}\n")

    # run_simulation will create LLM clients based on scenario.config.llm
    results = run_simulation(scenario, llm_client=None, num_turns=args.turns)

    # Save results as we go (already printed in orchestrator)
    for result in results:
        output_manager.save_turn(result)

    output_manager.save_summary(results)
    print(f"\n{'='*60}")
    print(f"SIMULATION COMPLETE")
    print(f"{'='*60}")
    print(f"Results saved to: {run_dir}")


def run_dry(scenario):
    """Print prompts without calling LLM."""
    from .prompts import PromptBuilder

    builder = PromptBuilder(scenario)

    print("\n" + "=" * 60)
    print("DRY RUN - PROMPT PREVIEW")
    print("=" * 60)

    print("\n=== EVENTS PROMPT (Turn 1) ===")
    system, user = builder.build_events_prompt(1)
    print("\nSYSTEM PROMPT:")
    print(system[:500] + "..." if len(system) > 500 else system)
    print("\nUSER PROMPT:")
    print(user[:500] + "..." if len(user) > 500 else user)

    if scenario.actors:
        first_actor_id = list(scenario.actors.keys())[0]
        actor_name = scenario.actors[first_actor_id].name
        print(f"\n=== ACTOR PROMPT ({actor_name}, Turn 1) ===")
        system, user = builder.build_actor_prompt(first_actor_id, 1, [])
        print("\nSYSTEM PROMPT:")
        print(system[:500] + "..." if len(system) > 500 else system)
        print("\nUSER PROMPT:")
        print(user[:500] + "..." if len(user) > 500 else user)

    print("\n" + "=" * 60)
    print("Dry run complete. Use without --dry-run to execute.")
    print("=" * 60)


if __name__ == "__main__":
    main()
