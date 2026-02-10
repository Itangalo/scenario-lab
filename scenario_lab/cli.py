"""Command-line interface for Scenario Lab V4."""

import argparse
import json
from pathlib import Path
from dotenv import load_dotenv

from .loader import load_scenario
from .llm import LLMClient
from .orchestrator import run_simulation
from .output import OutputManager
from .validator import validate_scenario


def apply_model_override(llm_config, model: str):
    """Apply a single model override to all LLM task slots."""
    llm_config.events = model
    llm_config.actors = model
    llm_config.rules = model
    llm_config.metrics = model
    llm_config.summary = model
    llm_config.referee = model


def main():
    """CLI entry point."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Scenario Lab V4 - LLM-driven scenario simulation"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command (default)
    run_parser = subparsers.add_parser("run", help="Run a simulation")
    run_parser.add_argument("scenario", type=Path, help="Path to scenario directory")
    run_parser.add_argument(
        "--turns",
        type=int,
        default=None,
        help="Number of turns to run (default: from config)",
    )
    run_parser.add_argument(
        "--model", type=str, default=None, help="Override LLM model"
    )
    run_parser.add_argument(
        "--dry-run", action="store_true", help="Print prompts without calling LLM"
    )
    run_parser.add_argument(
        "--override",
        action="append",
        help="Override scenario config (e.g. 'output_language=Swedish' or 'llm.temperature=0.5')",
    )
    run_parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress display"
    )
    run_parser.add_argument(
        "--quiet", action="store_true", help="Minimal output mode"
    )
    run_parser.add_argument(
        "--validate", action="store_true", help="Validate scenario before running"
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a scenario")
    validate_parser.add_argument("scenario", type=Path, help="Path to scenario directory")

    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume an interrupted or completed run")
    resume_parser.add_argument("run_dir", type=Path, help="Path to run directory")
    resume_parser.add_argument("--turns", type=int, default=None, help="Total turns to run")
    resume_parser.add_argument("--model", type=str, default=None, help="Override all LLM models")
    resume_parser.add_argument("--override", action="append", help="Override config (e.g., 'llm.temperature=0.5')")
    resume_parser.add_argument("--from-turn", type=int, default=None, help="Resume from specific turn")

    # Branch command
    branch_parser = subparsers.add_parser("branch", help="Create a branch from an existing run")
    branch_parser.add_argument("run_dir", type=Path, help="Path to parent run directory")
    branch_parser.add_argument("--from-turn", type=int, required=True, help="Turn number to branch from")
    branch_parser.add_argument("--turns", type=int, default=None, help="Total turns to run from branch point")
    branch_parser.add_argument("--modify-metric", action="append", help="Modify metric: 'metric_id=value'")
    branch_parser.add_argument("--modify-narrative", type=str, help="Replace narrative text")
    branch_parser.add_argument("--model", type=str, help="Override all LLM models")
    branch_parser.add_argument("--override", action="append", help="Override config values")

    # Visualize command
    viz_parser = subparsers.add_parser("visualize", help="Generate charts for a run")
    viz_parser.add_argument("run_dir", type=Path, help="Path to run directory (e.g. scenarios/x/runs/run-123)")

    # Costs command
    costs_parser = subparsers.add_parser("costs", help="Display cost report for a run")
    costs_parser.add_argument("run_dir", type=Path, help="Path to run directory")
    costs_parser.add_argument("--detailed", action="store_true", help="Show detailed breakdown by turn")

    # Estimate command
    estimate_parser = subparsers.add_parser("estimate", help="Estimate costs before running")
    estimate_parser.add_argument("scenario", type=Path, help="Path to scenario directory")
    estimate_parser.add_argument("--turns", type=int, help="Number of turns (default: from config)")
    estimate_parser.add_argument("--model", type=str, help="Override all LLM models for estimation")

    # Calibrate command
    calibrate_parser = subparsers.add_parser(
        "calibrate",
        help="Analyze existing runs for scenario calibration (no API calls)",
    )
    calibrate_parser.add_argument("scenario", type=Path, help="Path to scenario directory")
    calibrate_parser.add_argument("--max-runs", type=int, default=None, help="Analyze most recent N runs")
    calibrate_parser.add_argument("--json", action="store_true", help="Print JSON instead of text report")
    calibrate_parser.add_argument("--output", type=Path, default=None, help="Write report to file")

    args = parser.parse_args()

    # Default to run if no command specified (backward compatibility)
    if args.command is None and hasattr(args, "scenario"):
        args.command = "run"
    elif args.command is None:
        parser.print_help()
        return

    if args.command == "visualize":
        try:
            # Import here to avoid dependency requirement for basic runs if plotly missing
            from .visualizer import create_visualization
            print(f"Generating visualization for: {args.run_dir}")
            output_path = create_visualization(args.run_dir)
            print(f"✅ Visualization saved to: {output_path}")
        except ImportError:
            print("❌ Error: 'plotly' not installed. Run 'pip install plotly' to use this feature.")
        except Exception as e:
            print(f"❌ Error generating visualization: {e}")
        return

    if args.command == "validate":
        print(f"Validating scenario: {args.scenario}...")
        result = validate_scenario(args.scenario)

        if result.errors:
            print("\n❌ Validation FAILED with the following errors:")
            for error in result.errors:
                print(f"  - {error}")
        else:
            print("\n✅ Scenario is valid!")

        if result.warnings:
            print("\n⚠️ Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        return

    if args.command == "costs":
        costs_file = args.run_dir / "costs.json"

        if not costs_file.exists():
            print(f"❌ No costs.json found in {args.run_dir}")
            print("   This run may not have cost tracking enabled.")
            return

        try:
            costs_data = json.loads(costs_file.read_text())
        except json.JSONDecodeError as e:
            print(f"❌ Error reading costs.json: {e}")
            return

        # Display cost report
        print("=" * 60)
        print("COST REPORT")
        print("=" * 60)
        print(f"Run: {args.run_dir.name}")
        print(f"\nTotal cost: ${costs_data['total_cost_usd']:.4f}")
        print(f"Total tokens: {costs_data['total_tokens']:,}")

        num_turns = len(costs_data.get('by_turn', []))
        if num_turns > 0:
            avg_cost = costs_data['total_cost_usd'] / num_turns
            avg_tokens = costs_data['total_tokens'] / num_turns
            print(f"Average per turn: ${avg_cost:.4f} ({avg_tokens:,.0f} tokens)")

        # By task summary
        if 'by_task_total' in costs_data:
            print("\nBy Task (Total):")
            sorted_tasks = sorted(
                costs_data['by_task_total'].items(),
                key=lambda x: x[1]['cost_usd'],
                reverse=True
            )
            for task_name, task_data in sorted_tasks:
                print(
                    f"  {task_name:20s}: ${task_data['cost_usd']:.4f} "
                    f"({task_data['tokens']:,} tokens, {task_data['calls']} calls)"
                )

        # By model summary
        if 'by_model' in costs_data:
            print("\nBy Model:")
            sorted_models = sorted(
                costs_data['by_model'].items(),
                key=lambda x: x[1]['cost_usd'],
                reverse=True
            )
            for model, data in sorted_models:
                print(
                    f"  {model:40s}: ${data['cost_usd']:.4f} "
                    f"({data['tokens']:,} tokens, {data['calls']} calls)"
                )

        # Detailed: by turn
        if args.detailed and 'by_turn' in costs_data:
            print("\nBy Turn:")
            for turn_data in costs_data['by_turn']:
                turn = turn_data['turn']
                print(
                    f"  Turn {turn:2d}: ${turn_data['cost_usd']:.4f} "
                    f"({turn_data['tokens']:,} tokens)"
                )

                # Task breakdown for this turn
                if 'by_task' in turn_data:
                    for task_name, task_data in sorted(turn_data['by_task'].items()):
                        print(
                            f"    {task_name:18s}: ${task_data['cost_usd']:.4f} "
                            f"({task_data['tokens']:,} tokens)"
                        )

        print("=" * 60)
        return

    if args.command == "estimate":
        from .estimator import CostEstimator, format_estimate_report

        print(f"Loading scenario: {args.scenario}...")
        try:
            scenario = load_scenario(args.scenario)
        except Exception as e:
            print(f"❌ Error loading scenario: {e}")
            return

        # Override model if specified
        if args.model:
            apply_model_override(scenario.config.llm, args.model)

        # Determine number of turns
        num_turns = args.turns or scenario.config.max_turns

        # Estimate costs
        print(f"Estimating costs for {num_turns} turns...\n")
        estimator = CostEstimator(scenario)
        estimate = estimator.estimate_costs(num_turns)

        # Display report
        report = format_estimate_report(estimate, scenario.config.name, num_turns)
        print(report)
        return

    if args.command == "calibrate":
        from .calibration import analyze_runs, format_analysis_report

        scenario_dir = args.scenario if args.scenario.is_dir() else args.scenario.parent
        print(f"Analyzing runs for: {scenario_dir}")

        try:
            analysis = analyze_runs(scenario_dir, max_runs=args.max_runs)
        except Exception as e:
            print(f"❌ Calibration analysis failed: {e}")
            return

        if args.json:
            report = json.dumps(analysis, indent=2, ensure_ascii=False)
        else:
            report = format_analysis_report(analysis)

        if args.output:
            args.output.write_text(report, encoding="utf-8")
            print(f"✅ Calibration report written to: {args.output}")
        else:
            print(report)
        return

    if args.command == "resume":
        from .resume import load_run_state, detect_last_turn, validate_run_directory
        from datetime import datetime

        print(f"Resuming run: {args.run_dir}")

        # Validate
        is_valid, errors = validate_run_directory(args.run_dir)
        if not is_valid:
            print(f"❌ Invalid run directory:")
            for error in errors:
                print(f"  - {error}")
            return

        # Determine resume point
        from_turn = args.from_turn or detect_last_turn(args.run_dir)
        if from_turn == 0:
            print("❌ No completed turns found")
            return
        print(f"  Resuming from turn {from_turn}")

        # Load state
        scenario, loaded_turn = load_run_state(args.run_dir, from_turn)
        print(f"  ✓ Loaded scenario state from turn {loaded_turn}")

        # Apply overrides (reuse existing logic from run command)
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
                        try:
                            setattr(target, last_key, value)
                            print(f"  → Overrode {key_path} = {value}")
                        except Exception as e:
                            print(f"Warning: Could not set '{last_key}' on {type(target)}: {e}")

        if args.model:
            apply_model_override(scenario.config.llm, args.model)
            print(f"  → Overrode all models to: {args.model}")

        # Setup OutputManager for existing directory
        scenario_dir = args.run_dir.parent.parent
        output_manager = OutputManager(scenario, scenario_dir)
        output_manager.run_dir = args.run_dir  # Use existing directory

        num_turns = args.turns or scenario.config.max_turns
        start_turn = loaded_turn + 1

        # Update summary.json resume metadata
        summary_path = args.run_dir / "summary.json"
        summary = json.loads(summary_path.read_text())
        summary["resumed_at"] = datetime.now().isoformat()
        summary["resumed_from_turn"] = loaded_turn
        if start_turn <= num_turns:
            summary["status"] = "running"
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

        # Run simulation
        print(f"\nContinuing simulation from turn {start_turn}")
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
        print(f"Turns: {start_turn} to {num_turns}")

        if start_turn > num_turns:
            print("No additional turns to run. Finalizing existing run state.")
            output_manager.finalize_summary([])
            print(f"\n{'='*60}")
            print(f"RESUMED SIMULATION COMPLETE")
            print(f"{'='*60}")
            print(f"Results saved to: {args.run_dir}")
            return

        results = run_simulation(
            scenario,
            llm_client=None,
            num_turns=num_turns,
            output_manager=output_manager,
            start_turn=start_turn
        )

        # Finalize
        output_manager.finalize_summary(results)
        print(f"\n{'='*60}")
        print(f"RESUMED SIMULATION COMPLETE")
        print(f"{'='*60}")
        print(f"Results saved to: {args.run_dir}")
        return

    if args.command == "branch":
        from .resume import (
            load_run_state,
            create_branch,
            get_scenario_path_from_run,
            persist_scenario_state_at_turn,
            sync_summary_turn_state,
        )

        print(f"Creating branch from: {args.run_dir}")
        print(f"  Branch point: Turn {args.from_turn}")

        # Parse state modifications
        state_mods = {}
        if args.modify_metric:
            state_mods["metrics"] = {}
            for mod in args.modify_metric:
                if "=" not in mod:
                    print(f"Warning: Invalid metric modification format '{mod}', skipping. Use 'metric_id=value'.")
                    continue
                metric_id, value = mod.split("=", 1)
                try:
                    state_mods["metrics"][metric_id] = float(value)
                except ValueError:
                    print(f"Warning: Invalid metric value '{value}' for metric '{metric_id}', skipping.")
                    continue

        if args.modify_narrative:
            state_mods["narrative"] = args.modify_narrative

        # Parse config overrides
        config_overrides = {}
        if args.override:
            for override in args.override:
                if "=" not in override:
                    print(f"Warning: Invalid override format '{override}', skipping. Use 'key=value'.")
                    continue
                key, value = override.split("=", 1)
                config_overrides[key] = value

        if args.model:
            config_overrides["llm.events"] = args.model
            config_overrides["llm.actors"] = args.model
            config_overrides["llm.rules"] = args.model
            config_overrides["llm.metrics"] = args.model
            config_overrides["llm.summary"] = args.model
            config_overrides["llm.referee"] = args.model

        # Determine output location
        try:
            scenario_path = get_scenario_path_from_run(args.run_dir)
            output_base = scenario_path if scenario_path.is_dir() else scenario_path.parent
        except Exception as e:
            print(f"❌ Error determining scenario path: {e}")
            return

        # Create branch
        try:
            new_run_dir = create_branch(
                args.run_dir,
                args.from_turn,
                output_base,
                state_modifications=state_mods if state_mods else None,
                config_overrides=config_overrides if config_overrides else None
            )
            print(f"  ✓ Created branch: {new_run_dir.name}")
        except Exception as e:
            print(f"❌ Error creating branch: {e}")
            return

        # Load branched state
        try:
            scenario, loaded_turn = load_run_state(
                new_run_dir,
                from_turn=args.from_turn,
                state_modifications=state_mods if state_mods else None
            )
            print(f"  ✓ Loaded scenario state from turn {loaded_turn}")
        except Exception as e:
            print(f"❌ Error loading branched state: {e}")
            return

        # Apply config overrides to scenario
        if args.override:
            for override in args.override:
                if "=" not in override:
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
                        try:
                            setattr(target, last_key, value)
                            print(f"  → Overrode {key_path} = {value}")
                        except Exception as e:
                            print(f"Warning: Could not set '{last_key}' on {type(target)}: {e}")

        if args.model:
            apply_model_override(scenario.config.llm, args.model)
            print(f"  → Overrode all models to: {args.model}")

        # Run from branch point
        output_manager = OutputManager(scenario, output_base)
        output_manager.run_dir = new_run_dir

        # Persist branched state at branch point so modifications are durable on disk.
        persist_scenario_state_at_turn(new_run_dir, loaded_turn, scenario)
        branch_point_metrics = {m.id: m.value for m in scenario.metrics.metrics.values()}
        sync_summary_turn_state(new_run_dir, loaded_turn, branch_point_metrics)

        start_turn = loaded_turn + 1
        num_turns = args.turns or scenario.config.max_turns
        print(f"\nRunning simulation from turn {start_turn}")
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
        print(f"Turns: {start_turn} to {num_turns}")

        if start_turn > num_turns:
            print("No additional turns to run from branch point. Finalizing branch state.")
            output_manager.finalize_summary([])
            print(f"\n{'='*60}")
            print(f"BRANCH SIMULATION COMPLETE")
            print(f"{'='*60}")
            print(f"Results saved to: {new_run_dir}")
            return

        results = run_simulation(
            scenario,
            llm_client=None,
            num_turns=num_turns,
            output_manager=output_manager,
            start_turn=start_turn
        )

        # Finalize
        output_manager.finalize_summary(results)
        print(f"\n{'='*60}")
        print(f"BRANCH SIMULATION COMPLETE")
        print(f"{'='*60}")
        print(f"Results saved to: {new_run_dir}")
        return

    # Run logic starts here
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

    # Validate scenario if requested
    if hasattr(args, 'validate') and args.validate:
        print("\nValidating scenario...")
        result = validate_scenario(args.scenario)

        if result.warnings:
            print("⚠️  Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        if result.errors:
            print("\n❌ Validation FAILED with the following errors:")
            for error in result.errors:
                print(f"  - {error}")
            print("\nFix the errors above before running the simulation.")
            return
        else:
            print("✅ Scenario validation passed!\n")

    if args.model:
        # Override all task models if --model is specified
        apply_model_override(scenario.config.llm, args.model)

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

    # Create progress tracker
    from .progress import ProgressTracker

    num_turns = args.turns or scenario.config.max_turns
    progress_tracker = ProgressTracker(
        total_turns=num_turns,
        actors=scenario.config.actor_ids,
        enabled=not args.no_progress,
        quiet=args.quiet
    )

    # run_simulation will create LLM clients and write incrementally
    results = run_simulation(
        scenario,
        llm_client=None,
        num_turns=args.turns,
        output_manager=output_manager,
        progress_tracker=progress_tracker
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
