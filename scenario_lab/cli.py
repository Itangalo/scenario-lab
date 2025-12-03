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
    parser.add_argument(
        "--override",
        action="append",
        help="Override scenario config (e.g. 'output_language=Swedish' or 'llm.temperature=0.5')",
    )

    args = parser.parse_args()

    # Load scenario
    print(f"Loading scenario from {args.scenario}...")
    scenario = load_scenario(args.scenario)
    
    # Apply overrides
    if args.override:
        for override in args.override:
            if "=" not in override:
                print(f"Warning: Invalid override format '{override}', skipping. Use 'key=value'.")
                continue
            
            key_path, value = override.split("=", 1)
            keys = key_path.split(".")
            
            # Try to convert value to int/float/bool
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            else:
                try:
                    if "." in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass  # Keep as string
            
            # Navigate to the correct object
            target = scenario.config
            for i, key in enumerate(keys[:-1]):
                if hasattr(target, key):
                    target = getattr(target, key)
                elif isinstance(target, dict) and key in target:
                    target = target[key]
                else:
                    print(f"Warning: Could not find key '{key}' in path '{key_path}', skipping override.")
                    target = None
                    break
            
            if target is not None:
                last_key = keys[-1]
                if hasattr(target, last_key):
                    setattr(target, last_key, value)
                    print(f"  → Overrode {key_path} = {value}")
                elif isinstance(target, dict):
                    target[last_key] = value
                    print(f"  → Overrode {key_path} = {value}")
                else:
                    # Special case for ScenarioConfig fields that might not be dicts but we want to set attr
                    try:
                        setattr(target, last_key, value)
                        print(f"  → Overrode {key_path} = {value}")
                    except Exception as e:
                        print(f"Warning: Could not set '{last_key}' on {type(target)}: {e}")

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
    elif isinstance(scenario.config.llm.actors, list):
        print(f"  Actors: {scenario.config.llm.actors} (all)")
    else:
        print(f"  Actors:")
        for actor_id, model in scenario.config.llm.actors.items():
            print(f"    {actor_id}: {model}")
    print(f"  Rules: {scenario.config.llm.rules}")
    print(f"  Metrics: {scenario.config.llm.metrics}")
    print(f"Turns: {args.turns or scenario.config.max_turns}")

    # Determine output directory (use parent dir if args.scenario is a .yaml file)
    output_base = args.scenario
    if Path(args.scenario).is_file():
        # For variant files, output to the base scenario directory
        output_base = Path(args.scenario).parent
        while output_base != output_base.parent:
            if (output_base / "metrics.md").exists():
                break
            output_base = output_base.parent

    output_manager = OutputManager(scenario, output_base)
    run_dir = output_manager.start_run()
    print(f"Output directory: {run_dir.name}\n")

    # run_simulation will create LLM clients and write incrementally
    results = run_simulation(
        scenario, llm_client=None, num_turns=args.turns, output_manager=output_manager
    )

    # Mark simulation as complete
    output_manager.finalize_summary(results)
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
