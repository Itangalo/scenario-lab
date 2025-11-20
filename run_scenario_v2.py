#!/usr/bin/env python3
"""
Scenario Lab V2 CLI Runner

Thin wrapper around V2 architecture demonstrating modular execution.
All complex logic is in phase services and orchestrator.

Usage:
    python run_scenario_v2.py scenarios/ai-2027
    python run_scenario_v2.py scenarios/ai-2027 --end-turn 5 --credit-limit 2.0
    python run_scenario_v2.py scenarios/ai-2027 --resume output/ai-2027/run-001
    python run_scenario_v2.py scenarios/ai-2027 --branch-from output/ai-2027/run-001 --branch-at-turn 3
"""
import sys
import asyncio
import argparse
from pathlib import Path

# Add src to path for V1 compatibility
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scenario_lab.runners import SyncRunner
from scenario_lab.utils import (
    print_header,
    print_info,
    print_success,
    print_error,
    print_warning,
    setup_logging,
)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Scenario Lab V2 - AI-Powered Multi-Actor Simulations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a scenario
  python run_scenario_v2.py scenarios/ai-2027

  # Run with limits
  python run_scenario_v2.py scenarios/ai-2027 --end-turn 5 --credit-limit 2.0

  # Resume a previous run
  python run_scenario_v2.py scenarios/ai-2027 --resume output/ai-2027/run-001

  # Branch from a turn
  python run_scenario_v2.py scenarios/ai-2027 --branch-from output/ai-2027/run-001 --branch-at-turn 3

  # Use JSON mode for agent outputs
  python run_scenario_v2.py scenarios/ai-2027 --json-mode
        """
    )

    parser.add_argument(
        "scenario_path",
        help="Path to scenario directory (contains scenario.yaml and actors/)"
    )

    parser.add_argument(
        "--end-turn",
        type=int,
        help="Turn number to stop at (e.g., --end-turn 5 stops after turn 5; default: from scenario.yaml)"
    )

    parser.add_argument(
        "--credit-limit",
        type=float,
        help="Maximum cost in USD before halting (default: unlimited)"
    )

    parser.add_argument(
        "--output-path",
        help="Path to output directory (default: auto-generated in output/)"
    )

    parser.add_argument(
        "--resume",
        metavar="RUN_DIR",
        help="Resume from a previous run directory"
    )

    parser.add_argument(
        "--branch-from",
        metavar="RUN_DIR",
        help="Branch from a previous run directory"
    )

    parser.add_argument(
        "--branch-at-turn",
        type=int,
        metavar="TURN",
        help="Turn number to branch at (required with --branch-from)"
    )

    parser.add_argument(
        "--json-mode",
        action="store_true",
        help="Use JSON format for agent outputs (more robust parsing)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    return parser.parse_args()


async def run_scenario(args) -> int:
    """
    Run scenario using V2 architecture

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup structured logging
    setup_logging(level=args.log_level, format_type="colored")

    # Display header
    print_header("Scenario Lab V2")
    print_info(f"Scenario: {args.scenario_path}")

    # Validate arguments
    if args.branch_from and args.branch_at_turn is None:
        print_error("--branch-at-turn is required when using --branch-from")
        return 1

    if args.resume and args.branch_from:
        print_error("Cannot use both --resume and --branch-from")
        return 1

    try:
        # Create runner with V2 architecture
        print_info("Initializing V2 runner...")

        runner = SyncRunner(
            scenario_path=args.scenario_path,
            output_path=args.output_path,
            end_turn=args.end_turn,
            credit_limit=args.credit_limit,
            resume_from=args.resume,
            branch_from=args.branch_from,
            branch_at_turn=args.branch_at_turn,
            json_mode=args.json_mode,
        )

        # Setup runner (loads scenario, initializes components)
        print_info("Loading scenario and initializing components...")
        runner.setup()

        # Display scenario info
        scenario_name = runner.scenario_config.get("name", "Unknown")
        num_actors = len(runner.actors)
        end_turn_display = args.end_turn or runner.scenario_config.get("turns", "unlimited")

        print_success(f"Loaded: {scenario_name}")
        print_info(f"Actors: {num_actors}")
        print_info(f"End turn: {end_turn_display}")

        if args.credit_limit:
            print_info(f"Credit limit: ${args.credit_limit:.2f}")

        if args.json_mode:
            print_info("JSON mode: enabled (robust agent output parsing)")

        # Run scenario using orchestrator
        print_info("Starting scenario execution...")
        print_info(f"Output directory: {runner.output_path}")
        print()

        final_state = await runner.run()

        # Display results
        print()
        print_success("Scenario execution completed!")
        print_info(f"Final turn: {final_state.turn}")
        print_info(f"Total cost: ${final_state.total_cost():.4f}")
        print_info(f"Status: {final_state.status.value}")
        print_info(f"Output: {runner.output_path}")

        # Check if paused (hit limits)
        if final_state.status.value == "paused":
            print_warning("Execution paused (credit limit or end turn reached)")
            print_info(f"Resume with: python run_scenario_v2.py {args.scenario_path} --resume {runner.output_path}")

        return 0

    except FileNotFoundError as e:
        print_error(f"File not found: {e}")
        return 1

    except ValueError as e:
        print_error(f"Invalid configuration: {e}")
        return 1

    except Exception as e:
        print_error(f"Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point"""
    args = parse_args()

    # Run async execution
    exit_code = asyncio.run(run_scenario(args))

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
