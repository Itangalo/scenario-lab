"""
CLI interface for Scenario Lab V2

Provides backward-compatible CLI commands plus new V2 features.
"""
import click
import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Optional

from scenario_lab import __version__
from scenario_lab.core.events import EventBus, Event, EventType
from scenario_lab.utils.cli_helpers import (
    print_header,
    print_info,
    print_success,
    print_error,
    print_warning,
    print_alpha_notice,
    print_section,
    print_checklist_item,
)


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
    # Print header
    print_header(f"Scenario Lab V2 ({__version__})")

    # Print scenario info
    print_info("Scenario", scenario_path)
    if max_turns:
        print_info("Max turns", str(max_turns), "yellow")
    if credit_limit:
        print_info("Credit limit", f"${credit_limit:.2f}", "yellow")
    if resume:
        print_info("Resuming", resume, "blue")
    if branch_from:
        print_info("Branching from", branch_from, "blue")
        if branch_at_turn is not None:
            click.echo(f"   At turn: {click.style(str(branch_at_turn), fg='blue')}")

    # Alpha notice
    print_alpha_notice()

    # Handle resume and branch via V1 for now (Phase 2.3 will migrate these)
    if resume or branch_from:
        print_warning("Resume and branch features currently using V1 engine")
        _run_v1(scenario_path, max_turns, credit_limit, resume, branch_from, branch_at_turn)
        return

    # Use V2 SyncRunner for standard execution
    try:
        from scenario_lab.runners import SyncRunner
        from scenario_lab.core.events import EventBus

        # Create runner
        runner = SyncRunner(
            scenario_path=scenario_path,
            max_turns=max_turns,
            credit_limit=credit_limit,
        )

        print_section("Initializing scenario...")
        runner.setup()

        # Setup event handlers for progress display
        event_bus = runner.event_bus

        @event_bus.on(EventType.TURN_STARTED)
        async def on_turn_start(event: Event):
            turn = event.data.get("turn", 0)
            click.echo()
            click.echo(click.style(f"━━━ Turn {turn} ━━━", fg="bright_cyan", bold=True))

        @event_bus.on(EventType.PHASE_COMPLETED)
        async def on_phase_complete(event: Event):
            phase = event.data.get("phase", "unknown")
            click.echo(f"  ✓ {phase.replace('_', ' ').title()} phase complete")

        @event_bus.on(EventType.CREDIT_LIMIT_WARNING)
        async def on_credit_warning(event: Event):
            remaining = event.data.get("remaining", 0)
            print_warning(f"Credit limit warning: ${remaining:.2f} remaining")

        @event_bus.on(EventType.SCENARIO_HALTED)
        async def on_halted(event: Event):
            reason = event.data.get("reason", "unknown")
            print_warning(f"Scenario halted: {reason}")

        # Run scenario
        print_section("Running scenario...")
        final_state = asyncio.run(runner.run())

        # Print summary
        click.echo()
        print_section("Scenario complete!")
        click.echo(f"  Turns: {click.style(str(final_state.turn), fg='green')}")
        click.echo(f"  Total cost: {click.style(f'${final_state.total_cost():.2f}', fg='green')}")
        click.echo(f"  Output: {click.style(runner.output_path, fg='blue')}")

        print_success("Scenario completed successfully")

    except ImportError as e:
        print_error(
            "Could not load V2 runner",
            str(e),
            "Make sure the scenario_lab package is installed"
        )
        sys.exit(1)
    except Exception as e:
        import traceback
        print_error("Scenario execution failed", str(e))
        if logging.getLogger().level == logging.DEBUG:
            traceback.print_exc()
        sys.exit(1)


def _run_v1(
    scenario_path: str,
    max_turns: Optional[int],
    credit_limit: Optional[float],
    resume: Optional[str],
    branch_from: Optional[str],
    branch_at_turn: Optional[int],
) -> None:
    """Run scenario using V1 engine (for resume/branch compatibility)"""
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

        print_success("Scenario completed")

    except ImportError as e:
        print_error(
            "Could not load V1 runner",
            str(e),
            "Make sure you're running from the project root"
        )
        sys.exit(1)
    except Exception as e:
        print_error("Scenario execution failed", str(e))
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
    print_header("Validating Scenario")
    print_info("Path", scenario_path)

    print_warning("V2 Alpha: Schema validation coming in Phase 2.0")
    click.echo()

    # TODO: Implement Pydantic schema validation
    print_checklist_item("YAML syntax (placeholder)")
    print_checklist_item("Scenario structure (placeholder)")
    print_checklist_item("Actor definitions (placeholder)")
    print_success("Validation passed")


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
    print_header("Cost Estimation")
    print_info("Scenario", scenario_path)
    print_info("Turns", str(max_turns), "yellow")

    print_warning("V2 Alpha: Cost estimation coming in Phase 2.0")
    click.echo()

    # TODO: Implement cost estimation
    print_section("Estimated costs:")
    click.echo(f"  Total: {click.style('$X.XX', fg='yellow')} (placeholder)")
    click.echo(f"  Per turn: {click.style('$X.XX', fg='yellow')} (placeholder)")
    click.echo(f"  Per actor: {click.style('$X.XX', fg='yellow')} (placeholder)")


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
    print_header("Scenario Lab V2")
    print_info("Version", __version__)
    print_info("Architecture", "Event-driven modular", "blue")
    print_info("Status", "Alpha - Phase 2.0 Foundation", "yellow")

    print_section("Features:")
    print_checklist_item("Event-driven execution engine")
    print_checklist_item("Immutable state management")
    print_checklist_item("Backward compatible with V1")
    print_checklist_item("Full execution (Phase 2.1)", "⏳")
    print_checklist_item("Web dashboard (Phase 2.3)", "⏳")
    click.echo()


def main() -> None:
    """Entry point for CLI"""
    cli()


if __name__ == "__main__":
    main()
