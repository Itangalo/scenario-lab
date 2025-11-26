"""
Command-line interface for Scenario Lab V3.
"""
import argparse
import asyncio
import json
from pathlib import Path
import logging

from .engine import Simulation

logger = logging.getLogger(__name__)

def run_simulation(args):
    """Handler for the 'run' command."""
    asyncio.run(
        Simulation(
            args.scenario_path,
            run_id=args.run_id,
            cli_provider="mock" if args.dry_run else args.provider,
        ).run(num_turns=args.turns)
    )

def analyze_runs(args):
    """Handler for the 'analyze' command."""
    scenario_path = Path(args.scenario_path)
    runs_dir = scenario_path / "runs"
    
    if not runs_dir.exists():
        print(f"No runs found for scenario: {scenario_path}")
        return

    all_runs = sorted(runs_dir.iterdir(), key=os.path.getmtime, reverse=True)
    runs_to_analyze = all_runs[:args.runs]

    print(f"Analyzing last {len(runs_to_analyze)} runs for scenario: {scenario_path.name}")
    
    # This is a very basic analysis. A real implementation would be more sophisticated.
    for run_dir in runs_to_analyze:
        summary_path = run_dir / "summary.json"
        if summary_path.exists():
            with open(summary_path, 'r') as f:
                summary = json.load(f)
                print(f"\nRun: {summary['run_id']}")
                print(f"  Total Turns: {summary['total_turns']}")
                print(f"  Outcome Flags: {summary['outcome_flags']}")
        else:
            print(f"\nRun: {run_dir.name}")
            print("  Summary not found.")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Scenario Lab V3 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a scenario simulation.")
    run_parser.add_argument("scenario_path", help="Path to the scenario directory.")
    run_parser.add_argument("--turns", type=int, help="Number of turns to run.")
    run_parser.add_argument("--run-id", help="Custom run ID.")
    run_parser.add_argument("--provider", help="Override LLM provider.")
    run_parser.add_argument("--model", help="Override LLM model.")
    run_parser.add_argument("--verbose", action="store_true", help="Print detailed progress.")
    run_parser.add_argument("--dry-run", action="store_true", help="Run with MockProvider.")
    run_parser.set_defaults(func=run_simulation)

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze scenario runs.")
    analyze_parser.add_argument("scenario_path", help="Path to the scenario directory.")
    analyze_parser.add_argument("--runs", type=int, default=5, help="Number of recent runs to analyze.")
    analyze_parser.set_defaults(func=analyze_runs)

    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    args.func(args)

if __name__ == "__main__":
    main()
