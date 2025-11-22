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
        scenario-lab run scenarios/ai-summit --end-turn 10 --credit-limit 5.0

        # Validate a scenario
        scenario-lab validate scenarios/ai-summit

        # Get cost estimate
        scenario-lab estimate scenarios/ai-summit
    """
    # Configure logging
    # Default: INFO level with clean format (no timestamps/module names)
    # Verbose: DEBUG level with full technical details
    level = logging.DEBUG if verbose else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" if verbose else "%(message)s"
    logging.basicConfig(
        level=level,
        format=format_str,
    )


@cli.command()
@click.argument("scenario_path", type=click.Path(exists=True, file_okay=False))
@click.option("--end-turn", type=int, help="Number of turns to execute (e.g., --end-turn 5 runs 5 actor decision rounds)")
@click.option("--credit-limit", type=float, help="Maximum cost in USD")
@click.option("--resume", type=click.Path(exists=True, file_okay=False), help="Resume from run directory")
@click.option("--branch-from", type=click.Path(exists=True, file_okay=False), help="Branch from run directory")
@click.option("--branch-at-turn", type=int, help="Turn number to branch from")
def run(
    scenario_path: str,
    end_turn: Optional[int],
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
    if end_turn:
        print_info("End turn", str(end_turn), "yellow")
    if credit_limit:
        print_info("Credit limit", f"${credit_limit:.2f}", "yellow")
    if resume:
        print_info("Resuming", resume, "blue")
    if branch_from:
        print_info("Branching from", branch_from, "blue")
        if branch_at_turn is not None:
            click.echo(f"   At turn: {click.style(str(branch_at_turn), fg='blue')}")

    # Use V2 SyncRunner for all operations (including resume/branch)
    try:
        from scenario_lab.runners import SyncRunner
        from scenario_lab.core.events import EventBus

        # Create runner
        runner = SyncRunner(
            scenario_path=scenario_path,
            end_turn=end_turn,
            credit_limit=credit_limit,
            resume_from=resume,
            branch_from=branch_from,
            branch_at_turn=branch_at_turn,
        )

        print_section("Initializing scenario...")
        runner.setup()

        # Setup event handlers for progress display
        event_bus = runner.event_bus

        async def on_turn_start(event: Event):
            turn = event.data.get("turn", 0)
            click.echo()
            click.echo(click.style(f"━━━ Turn {turn} ━━━", fg="bright_cyan", bold=True))

        async def on_phase_complete(event: Event):
            phase = event.data.get("phase", "unknown")
            click.echo(f"  ✓ {phase.replace('_', ' ').title()} phase complete")

        async def on_credit_warning(event: Event):
            remaining = event.data.get("remaining", 0)
            print_warning(f"Credit limit warning: ${remaining:.2f} remaining")

        async def on_halted(event: Event):
            reason = event.data.get("reason", "unknown")
            print_warning(f"Scenario halted: {reason}")

        # Register handlers
        event_bus.on(EventType.TURN_STARTED, on_turn_start)
        event_bus.on(EventType.PHASE_COMPLETED, on_phase_complete)
        event_bus.on(EventType.CREDIT_LIMIT_WARNING, on_credit_warning)
        event_bus.on(EventType.SCENARIO_HALTED, on_halted)

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


@cli.command()
@click.argument("scenario_path", type=click.Path(exists=True, file_okay=False))
def validate(scenario_path: str) -> None:
    """
    Validate scenario configuration

    Checks:
    - YAML syntax
    - Pydantic schema validation
    - Actor definitions
    - Metrics configuration (optional)
    - Validation rules (optional)
    """
    from pathlib import Path
    from scenario_lab.schemas import validate_scenario_directory

    print_header("Validating Scenario")
    print_info("Path", scenario_path)
    click.echo()

    # Validate all configuration files
    scenario_path_obj = Path(scenario_path)
    results = validate_scenario_directory(scenario_path_obj)

    # Track overall success
    all_success = True
    total_errors = 0
    total_warnings = 0

    # Display results for each file type
    for file_type, result in results.items():
        if result.success:
            if result.warnings:
                print_checklist_item(f"{file_type.capitalize()}", status="⚠")
                for warning in result.warnings:
                    click.echo(f"    {click.style('⚠', fg='yellow')} {warning}")
                total_warnings += len(result.warnings)
            else:
                print_checklist_item(f"{file_type.capitalize()}", status="✓")
        else:
            print_checklist_item(f"{file_type.capitalize()}", status="✗")
            for error in result.errors:
                click.echo(f"    {click.style('✗', fg='red')} {error}")
            total_errors += len(result.errors)
            all_success = False

    # Summary
    click.echo()
    if all_success:
        if total_warnings > 0:
            print_warning(f"Validation passed with {total_warnings} warning(s)")
            click.echo()
            click.echo("Consider addressing warnings for best practices.")
        else:
            print_success("Validation passed")
            click.echo()
            click.echo("Scenario is ready to run!")
    else:
        print_error(
            "Validation failed",
            f"Found {total_errors} error(s) and {total_warnings} warning(s)",
            "Fix the errors above and run validation again"
        )
        sys.exit(1)


@cli.command()
@click.argument("scenario_path", type=click.Path(exists=True, file_okay=False))
@click.option("--end-turn", type=int, help="Turn number to estimate up to (uses scenario default if not specified)")
def estimate(scenario_path: str, end_turn: Optional[int]) -> None:
    """
    Estimate scenario cost without running

    Provides:
    - Estimated total cost
    - Per-actor cost breakdown
    - Per-turn cost estimate
    - Warnings for expensive configurations
    """
    from pathlib import Path
    from scenario_lab.utils.cost_estimator import CostEstimator

    print_header("Cost Estimation")
    print_info("Scenario", scenario_path)
    if end_turn:
        print_info("Turns", str(end_turn), "yellow")
    click.echo()

    # Create estimator and load configs
    estimator = CostEstimator(Path(scenario_path))
    if not estimator.load_configs():
        print_error(
            "Failed to load scenario configuration",
            "Cannot estimate costs without valid scenario.yaml and actor files",
            "Run 'scenario-lab validate' to check configuration"
        )
        sys.exit(1)

    # Get estimate
    estimate_result = estimator.estimate(end_turn)

    # Display number of turns
    actual_turns = end_turn or estimator.scenario_config.turns or 10
    click.echo(f"📊 Estimating costs for {click.style(str(actual_turns), fg='cyan', bold=True)} turns")
    click.echo()

    # Display per-actor breakdown
    if estimate_result.actor_costs:
        print_section("Per-Actor Estimates:")
        for actor_name, cost in estimate_result.actor_costs.items():
            actor_config = estimator.actor_configs.get(actor_name)
            model = actor_config.llm_model if actor_config else "unknown"
            cost_per_turn = cost / actual_turns if actual_turns > 0 else 0

            # Color code based on cost
            if cost > 5.0:
                color = "red"
            elif cost > 1.0:
                color = "yellow"
            else:
                color = "green"

            click.echo(
                f"  {actor_name} ({model}): "
                f"{click.style(f'${cost:.2f}', fg=color)} total "
                f"({click.style(f'${cost_per_turn:.3f}', fg=color)} per turn)"
            )
        click.echo()

    # Display other cost components
    if estimate_result.world_state_cost > 0:
        ws_model = estimator.scenario_config.world_state_model or "openai/gpt-4o-mini"
        click.echo(f"  World State Updates ({ws_model}): ${estimate_result.world_state_cost:.2f}")

    if estimate_result.communication_cost > 0:
        click.echo(f"  Communications: ${estimate_result.communication_cost:.2f}")

    if estimate_result.metrics_cost > 0:
        click.echo(f"  Metrics Extraction: ${estimate_result.metrics_cost:.2f}")

    if estimate_result.validation_cost > 0:
        click.echo(f"  QA Validation: ${estimate_result.validation_cost:.2f}")

    if any([
        estimate_result.world_state_cost,
        estimate_result.communication_cost,
        estimate_result.metrics_cost,
        estimate_result.validation_cost
    ]):
        click.echo()

    # Display total
    print_section("Total Estimate:")
    total_color = "red" if estimate_result.total_cost > 10.0 else "green" if estimate_result.total_cost < 1.0 else "yellow"

    click.echo(
        f"  Total: {click.style(f'${estimate_result.total_cost:.2f}', fg=total_color, bold=True)} "
        f"for {actual_turns} turns"
    )
    click.echo(
        f"  Per turn: {click.style(f'${estimate_result.per_turn_cost:.3f}', fg=total_color)}"
    )
    click.echo()

    # Display warnings
    if estimate_result.warnings:
        print_section("Warnings:")
        for warning in estimate_result.warnings:
            click.echo(f"  {click.style('⚠', fg='yellow')} {warning}")
        click.echo()

    # Summary message
    if estimate_result.total_cost > 50.0:
        print_warning("This scenario is expensive - consider reducing turns or using cheaper models")
    elif estimate_result.total_cost == 0.0:
        print_success("This scenario uses free/local models - zero estimated cost!")
    else:
        click.echo(click.style("💡 Tip:", fg="bright_blue") + " Use --credit-limit to cap spending during execution")
        click.echo()


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


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve(host: str, port: int, reload: bool) -> None:
    """
    Start the Scenario Lab API server

    Provides REST API and WebSocket endpoints for:
    - Programmatic scenario execution
    - Real-time monitoring
    - Run analytics and comparison
    - WebSocket streaming
    """
    print_header("Scenario Lab API Server")
    print_info("Host", host)
    print_info("Port", str(port), "green")
    print_info("Reload", "enabled" if reload else "disabled", "yellow" if reload else "blue")

    print_section("Starting server...")
    click.echo()
    click.echo(f"🌐 API Documentation: {click.style(f'http://{host}:{port}/docs', fg='blue', underline=True)}")
    click.echo(f"📊 OpenAPI Schema: {click.style(f'http://{host}:{port}/openapi.json', fg='blue')}")
    click.echo()

    try:
        import uvicorn
        from scenario_lab.api import app

        uvicorn.run(
            "scenario_lab.api:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
        )
    except ImportError as e:
        print_error(
            "FastAPI not installed",
            str(e),
            "Install with: pip install fastapi uvicorn"
        )
        sys.exit(1)
    except Exception as e:
        print_error("Failed to start server", str(e))
        sys.exit(1)


@cli.command()
@click.argument("output_dir", type=click.Path(), required=False)
def create(output_dir: Optional[str]) -> None:
    """
    Create a new scenario using interactive wizard

    OUTPUT_DIR: Optional directory to create scenario in (defaults to ./scenarios/<name>)

    The wizard will guide you through:
    - Scenario name and description
    - System prompt configuration
    - Initial world state
    - Turn settings (count and duration)
    - World state model selection
    - Actor creation (unlimited actors)
    - Metrics configuration (optional)
    - Validation rules setup (optional)

    This typically takes 5-10 minutes to complete.
    """
    print_header("Scenario Creation Wizard")
    click.echo()

    # V2 wizard not yet implemented - provide guidance
    print_warning("Interactive wizard not yet available in V2")
    click.echo()
    click.echo("To create a scenario manually:")
    click.echo()
    click.echo("  1. Create a scenario directory:")
    click.echo(f"     {click.style('mkdir -p scenarios/my-scenario/actors', fg='cyan')}")
    click.echo()
    click.echo("  2. Create scenario.yaml with:")
    click.echo(f"     {click.style('name, description, initial_world_state, turns', fg='yellow')}")
    click.echo()
    click.echo("  3. Create actor files in actors/:")
    click.echo(f"     {click.style('name, llm_model, system_prompt, goals', fg='yellow')}")
    click.echo()
    click.echo("  4. Validate your scenario:")
    click.echo(f"     {click.style('scenario-lab validate scenarios/my-scenario', fg='cyan')}")
    click.echo()
    click.echo("For complete documentation, see:")
    click.echo(f"  {click.style('AGENTS.md', fg='blue')} - Full YAML schema reference")
    click.echo(f"  {click.style('scenarios/', fg='blue')} - Example scenarios")
    click.echo()


@cli.command()
@click.argument("output_path", type=click.Path(), required=False)
def create_batch(output_path: Optional[str]) -> None:
    """
    Create a batch configuration using interactive wizard

    OUTPUT_PATH: Optional path to save config (defaults to ./batch-configs/<name>.yaml)

    The wizard will guide you through:
    - Experiment name and description
    - Base scenario selection
    - Parameter variations (actor models, scenario parameters)
    - Execution settings (parallel workers, runs per variation)
    - Budget limits (total and per-run)
    - Output directory configuration

    This typically takes 3-5 minutes to complete.
    """
    print_header("Batch Configuration Wizard")
    click.echo()

    # V2 wizard not yet implemented - provide guidance
    print_warning("Interactive wizard not yet available in V2")
    click.echo()
    click.echo("To create a batch configuration manually:")
    click.echo()
    click.echo("  1. Create a YAML file with batch configuration:")
    click.echo(f"     {click.style('experiment_name, base_scenario, variations', fg='yellow')}")
    click.echo()
    click.echo("  2. Define parameter variations:")
    click.echo(f"     {click.style('actor_models, scenario_parameters, runs_per_variation', fg='yellow')}")
    click.echo()
    click.echo("  3. Set execution limits:")
    click.echo(f"     {click.style('max_parallel_workers, total_budget, per_run_budget', fg='yellow')}")
    click.echo()
    click.echo("  4. Run with dry-run to preview:")
    click.echo(f"     {click.style('python -m scenario_lab.batch.batch_runner config.yaml --dry-run', fg='cyan')}")
    click.echo()
    click.echo("For examples, see:")
    click.echo(f"  {click.style('examples/', fg='blue')} - Example batch configurations")
    click.echo()


def main() -> None:
    """Entry point for CLI"""
    cli()


if __name__ == "__main__":
    main()
