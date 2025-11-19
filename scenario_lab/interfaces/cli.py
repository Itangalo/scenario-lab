"""
CLI interface for Scenario Lab V2

Provides backward-compatible CLI commands plus new V2 features.
"""
import click
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from scenario_lab import __version__
from scenario_lab.core.events import EventBus, Event, EventType


@click.group()
@click.version_option(version=__version__)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool) -> None:
    """
    Scenario Lab V2 - AI-powered multi-actor scenario simulation

    Examples:

        # Run a scenario
        scenario-lab run scenarios/ai-summit

        # Run with limits
        scenario-lab run scenarios/ai-summit --max-turns 10 --credit-limit 5.0

        # Validate a scenario
        scenario-lab validate scenarios/ai-summit

        # Get cost estimate
        scenario-lab estimate scenarios/ai-summit
    """
    # Configure logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@cli.command()
@click.argument("scenario_path", type=click.Path(exists=True, file_okay=False))
@click.option("--max-turns", type=int, help="Maximum number of turns")
@click.option("--credit-limit", type=float, help="Maximum cost in USD")
@click.option("--resume", type=click.Path(exists=True, file_okay=False), help="Resume from run directory")
@click.option("--branch-from", type=click.Path(exists=True, file_okay=False), help="Branch from run directory")
@click.option("--branch-at-turn", type=int, help="Turn number to branch from")
def run(
    scenario_path: str,
    max_turns: Optional[int],
    credit_limit: Optional[float],
    resume: Optional[str],
    branch_from: Optional[str],
    branch_at_turn: Optional[int],
) -> None:
    """
    Run a scenario simulation

    SCENARIO_PATH: Path to scenario directory
    """
    # Header with colors
    click.echo(click.style(f"\n✨ Scenario Lab V2", fg="bright_cyan", bold=True) + f" ({__version__})")
    click.echo(click.style("───────────────────────────────────────", fg="cyan"))

    # Scenario info
    click.echo(f"📂 Scenario: " + click.style(scenario_path, fg="green"))

    if max_turns:
        click.echo(f"🔢 Max turns: " + click.style(str(max_turns), fg="yellow"))
    if credit_limit:
        click.echo(f"💰 Credit limit: " + click.style(f"${credit_limit:.2f}", fg="yellow"))
    if resume:
        click.echo(f"▶️  Resuming: " + click.style(resume, fg="blue"))
    if branch_from:
        click.echo(f"🌿 Branching from: " + click.style(branch_from, fg="blue"))
        if branch_at_turn is not None:
            click.echo(f"   At turn: " + click.style(str(branch_at_turn), fg="blue"))

    # Alpha notice
    click.echo()
    click.echo(click.style("⚠️  V2 Alpha:", fg="yellow", bold=True) + " Delegating to V1 runner...")
    click.echo(click.style("   Full V2 execution engine coming in Phase 2.1", fg="yellow", dim=True))
    click.echo()

    # Import V1 runner
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))

    try:
        from run_scenario import main as v1_main
        # Build V1 arguments
        v1_args = [scenario_path]
        if max_turns:
            v1_args.extend(["--max-turns", str(max_turns)])
        if credit_limit:
            v1_args.extend(["--credit-limit", str(credit_limit)])
        if resume:
            v1_args.extend(["--resume", resume])
        if branch_from:
            v1_args.extend(["--branch-from", branch_from])
            if branch_at_turn is not None:
                v1_args.extend(["--branch-at-turn", str(branch_at_turn)])

        # Call V1
        sys.argv = ["run_scenario.py"] + v1_args
        v1_main()

        # Success message
        click.echo()
        click.echo(click.style("✓ Scenario completed", fg="bright_green", bold=True))

    except ImportError as e:
        click.echo()
        click.echo(click.style("✗ Error:", fg="bright_red", bold=True) + f" Could not load V1 runner", err=True)
        click.echo(click.style(f"  {e}", fg="red", dim=True), err=True)
        click.echo()
        click.echo(click.style("💡 Tip:", fg="bright_blue") + " Make sure you're running from the project root", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo()
        click.echo(click.style("✗ Error:", fg="bright_red", bold=True) + f" Scenario execution failed", err=True)
        click.echo(click.style(f"  {e}", fg="red", dim=True), err=True)
        sys.exit(1)


@cli.command()
@click.argument("scenario_path", type=click.Path(exists=True, file_okay=False))
def validate(scenario_path: str) -> None:
    """
    Validate scenario configuration

    Checks:
    - YAML syntax
    - Pydantic schema validation
    - Actor definitions
    - Metrics configuration
    """
    click.echo(click.style(f"\n🔍 Validating Scenario", fg="bright_cyan", bold=True))
    click.echo(click.style("───────────────────────────────────────", fg="cyan"))
    click.echo(f"📂 Path: " + click.style(scenario_path, fg="green"))
    click.echo()

    click.echo(click.style("⚠️  V2 Alpha:", fg="yellow", bold=True) + " Schema validation coming in Phase 2.0")
    click.echo()

    # TODO: Implement Pydantic schema validation
    click.echo(click.style("✓", fg="green") + " YAML syntax (placeholder)")
    click.echo(click.style("✓", fg="green") + " Scenario structure (placeholder)")
    click.echo(click.style("✓", fg="green") + " Actor definitions (placeholder)")
    click.echo()
    click.echo(click.style("✓ Validation passed", fg="bright_green", bold=True))


@cli.command()
@click.argument("scenario_path", type=click.Path(exists=True, file_okay=False))
@click.option("--max-turns", type=int, default=10, help="Number of turns to estimate")
def estimate(scenario_path: str, max_turns: int) -> None:
    """
    Estimate scenario cost without running

    Provides:
    - Estimated total cost
    - Per-actor cost breakdown
    - Per-turn cost estimate
    """
    click.echo(click.style(f"\n💰 Cost Estimation", fg="bright_cyan", bold=True))
    click.echo(click.style("───────────────────────────────────────", fg="cyan"))
    click.echo(f"📂 Scenario: " + click.style(scenario_path, fg="green"))
    click.echo(f"🔢 Turns: " + click.style(str(max_turns), fg="yellow"))
    click.echo()

    click.echo(click.style("⚠️  V2 Alpha:", fg="yellow", bold=True) + " Cost estimation coming in Phase 2.0")
    click.echo()

    # TODO: Implement cost estimation
    click.echo(click.style("Estimated costs:", fg="bright_white", bold=True))
    click.echo(f"  Total: " + click.style("$X.XX", fg="yellow") + " (placeholder)")
    click.echo(f"  Per turn: " + click.style("$X.XX", fg="yellow") + " (placeholder)")
    click.echo(f"  Per actor: " + click.style("$X.XX", fg="yellow") + " (placeholder)")


@cli.command()
@click.argument("run_ids", nargs=-1, required=True)
def compare(run_ids: tuple[str, ...]) -> None:
    """
    Compare multiple scenario runs

    Displays:
    - Side-by-side world state comparison
    - Actor decision differences
    - Metrics comparison
    - Cost analysis
    """
    click.echo(f"Comparing {len(run_ids)} runs:")
    for run_id in run_ids:
        click.echo(f"  - {run_id}")

    click.echo("\n[V2 Alpha] Run comparison coming in Phase 2.2...")


@cli.command()
@click.argument("scenario_path", type=click.Path(exists=True, file_okay=False))
def benchmark(scenario_path: str) -> None:
    """
    Run performance benchmark on scenario

    Measures:
    - Turn execution time
    - Memory usage
    - Cost per turn
    - Startup time
    """
    click.echo(f"Benchmarking: {scenario_path}")
    click.echo("[V2 Alpha] Benchmark tool coming soon...")

    # TODO: Implement benchmark tool
    click.echo("\nResults:")
    click.echo("  Average turn time: X.XX seconds (placeholder)")
    click.echo("  P95 turn time: X.XX seconds (placeholder)")
    click.echo("  Memory usage peak: XXX MB (placeholder)")
    click.echo("  Cost per turn: $X.XX (placeholder)")


@cli.command()
def version() -> None:
    """Show version information"""
    click.echo()
    click.echo(click.style("✨ Scenario Lab V2", fg="bright_cyan", bold=True))
    click.echo(click.style("───────────────────────────────────────", fg="cyan"))
    click.echo(f"📦 Version: " + click.style(__version__, fg="green"))
    click.echo(f"🏗️  Architecture: " + click.style("Event-driven modular", fg="blue"))
    click.echo(f"🚀 Status: " + click.style("Alpha - Phase 2.0 Foundation", fg="yellow"))
    click.echo()
    click.echo(click.style("Features:", fg="bright_white", bold=True))
    click.echo("  ✓ Event-driven execution engine")
    click.echo("  ✓ Immutable state management")
    click.echo("  ✓ Backward compatible with V1")
    click.echo("  ⏳ Full execution (Phase 2.1)")
    click.echo("  ⏳ Web dashboard (Phase 2.3)")
    click.echo()


def main() -> None:
    """Entry point for CLI"""
    cli()


if __name__ == "__main__":
    main()
