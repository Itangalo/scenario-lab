"""
CLI interface for Scenario Lab V2

Provides backward-compatible CLI commands plus new V2 features.
Uses Rich for enhanced terminal output.
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.table import Table

from scenario_lab import __version__
from scenario_lab.core.events import Event, EventType
from scenario_lab.utils.cli_helpers import (
    print_header,
    print_info,
    print_success,
    print_error,
    print_warning,
    print_alpha_notice,
    print_section,
    print_checklist_item,
    print_turn_header,
    print_phase_complete,
    print_link,
)
from scenario_lab.utils.rich_console import console, get_cost_style


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

        # Benchmark performance
        scenario-lab benchmark scenarios/ai-summit --turns 5

        # Compare runs
        scenario-lab compare output/run-001 output/run-002
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
            console.print(f"   At turn: [blue]{branch_at_turn}[/]")

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
            print_turn_header(turn)

        async def on_phase_complete(event: Event):
            phase = event.data.get("phase", "unknown")
            print_phase_complete(phase)

        async def on_credit_warning(event: Event):
            remaining = event.data.get("remaining", 0)
            print_warning(f"Credit limit warning: ${remaining:.2f} remaining")

        async def on_halted(event: Event):
            reason = event.data.get("reason", "unknown")
            print_warning(f"Scenario halted: {reason}")

        async def on_exogenous_event(event: Event):
            name = event.data.get("name", "unknown")
            event_type = event.data.get("event_type", "unknown")
            console.print(f"  [yellow]\u26a1[/] Exogenous event triggered: [cyan]'{name}'[/] ({event_type})")

        # Register handlers
        event_bus.on(EventType.TURN_STARTED, on_turn_start)
        event_bus.on(EventType.PHASE_COMPLETED, on_phase_complete)
        event_bus.on(EventType.CREDIT_LIMIT_WARNING, on_credit_warning)
        event_bus.on(EventType.SCENARIO_HALTED, on_halted)
        event_bus.on(EventType.EXOGENOUS_EVENT_TRIGGERED, on_exogenous_event)

        # Run scenario
        print_section("Running scenario...")
        final_state = asyncio.run(runner.run())

        # Print summary
        console.print()
        print_section("Scenario complete!")
        console.print(f"  Turns: [green]{final_state.turn}[/]")
        console.print(f"  Total cost: [green]${final_state.total_cost():.2f}[/]")
        console.print(f"  Output: [path]{runner.output_path}[/]")

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
    console.print()

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
                print_checklist_item(f"{file_type.capitalize()}", status="\u26a0")
                for warning in result.warnings:
                    console.print(f"    [warning]\u26a0[/] {warning}")
                total_warnings += len(result.warnings)
            else:
                print_checklist_item(f"{file_type.capitalize()}", status="\u2713")
        else:
            print_checklist_item(f"{file_type.capitalize()}", status="\u2717")
            for error in result.errors:
                console.print(f"    [error]\u2717[/] {error}")
            total_errors += len(result.errors)
            all_success = False

    # Summary
    console.print()
    if all_success:
        if total_warnings > 0:
            print_warning(f"Validation passed with {total_warnings} warning(s)")
            console.print()
            console.print("Consider addressing warnings for best practices.")
        else:
            print_success("Validation passed")
            console.print()
            console.print("Scenario is ready to run!")
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
    console.print()

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
    console.print(f"\U0001f4ca Estimating costs for [cyan bold]{actual_turns}[/] turns")
    console.print()

    # Display per-actor breakdown using a table
    if estimate_result.actor_costs:
        print_section("Per-Actor Estimates:")
        actor_table = Table(show_header=True, header_style="bold cyan")
        actor_table.add_column("Actor", style="cyan")
        actor_table.add_column("Model", style="dim")
        actor_table.add_column("Total", justify="right")
        actor_table.add_column("Per Turn", justify="right")

        for actor_name, cost in estimate_result.actor_costs.items():
            actor_config = estimator.actor_configs.get(actor_name)
            model = actor_config.llm_model if actor_config else "unknown"
            cost_per_turn = cost / actual_turns if actual_turns > 0 else 0
            style = get_cost_style(cost)

            actor_table.add_row(
                actor_name,
                model,
                f"[{style}]${cost:.2f}[/]",
                f"[{style}]${cost_per_turn:.3f}[/]",
            )

        console.print(actor_table)
        console.print()

    # Display other cost components
    if estimate_result.world_state_cost > 0:
        ws_model = estimator.scenario_config.world_state_model or "openai/gpt-4o-mini"
        console.print(f"  World State Updates ({ws_model}): ${estimate_result.world_state_cost:.2f}")

    if estimate_result.communication_cost > 0:
        console.print(f"  Communications: ${estimate_result.communication_cost:.2f}")

    if estimate_result.metrics_cost > 0:
        console.print(f"  Metrics Extraction: ${estimate_result.metrics_cost:.2f}")

    if estimate_result.validation_cost > 0:
        console.print(f"  QA Validation: ${estimate_result.validation_cost:.2f}")

    if any([
        estimate_result.world_state_cost,
        estimate_result.communication_cost,
        estimate_result.metrics_cost,
        estimate_result.validation_cost
    ]):
        console.print()

    # Display total
    print_section("Total Estimate:")
    total_style = get_cost_style(estimate_result.total_cost)

    console.print(
        f"  Total: [{total_style} bold]${estimate_result.total_cost:.2f}[/] "
        f"for {actual_turns} turns"
    )
    console.print(
        f"  Per turn: [{total_style}]${estimate_result.per_turn_cost:.3f}[/]"
    )

    # Show if historical data was used
    if estimate_result.historical_data_used:
        console.print(
            "  [cyan]\U0001f4ca[/] Estimate improved using historical run data"
        )

    console.print()

    # Display warnings
    if estimate_result.warnings:
        print_section("Warnings:")
        for warning in estimate_result.warnings:
            console.print(f"  [warning]\u26a0[/] {warning}")
        console.print()

    # Summary message
    if estimate_result.total_cost > 50.0:
        print_warning("This scenario is expensive - consider reducing turns or using cheaper models")
    elif estimate_result.total_cost == 0.0:
        print_success("This scenario uses free/local models - zero estimated cost!")
    else:
        console.print("\U0001f4a1 [info.bright]Tip:[/] Use --credit-limit to cap spending during execution")
        console.print()


@cli.command()
@click.argument("run_paths", nargs=-1, required=True, type=click.Path(exists=True))
def compare(run_paths: tuple[str, ...]) -> None:
    """
    Compare multiple scenario runs

    RUN_PATHS: Paths to run directories (e.g., output/ai-summit/run-001 output/ai-summit/run-002)

    Displays:
    - Side-by-side world state comparison
    - Actor decision differences
    - Metrics comparison
    - Cost analysis
    """
    from pathlib import Path
    from scenario_lab.utils.state_persistence import StatePersistence

    print_header("Run Comparison")

    if len(run_paths) < 2:
        print_error(
            "Comparison requires at least 2 runs",
            f"Only {len(run_paths)} run(s) provided",
            "Provide 2 or more run directory paths"
        )
        sys.exit(1)

    # Load states from all runs
    states = []
    for run_path in run_paths:
        run_dir = Path(run_path)
        state_file = run_dir / "scenario-state-v2.json"

        if not state_file.exists():
            # Try legacy filename
            state_file = run_dir / "scenario-state.json"

        if not state_file.exists():
            print_error(
                f"State file not found in {run_path}",
                "No scenario-state-v2.json or scenario-state.json found",
                "Ensure the path points to a valid run directory"
            )
            sys.exit(1)

        try:
            state = StatePersistence.load_state(str(state_file))
            states.append((run_path, state))
            print_checklist_item(f"Loaded: {run_dir.name}", status="\u2713")
        except Exception as e:
            print_error(f"Failed to load {run_path}", str(e))
            sys.exit(1)

    console.print()

    # Summary section using Rich Table
    print_section("Run Summary")
    summary_table = Table(show_header=True, header_style="bold cyan")
    summary_table.add_column("Property", style="cyan")
    for rp in run_paths:
        summary_table.add_column(Path(rp).name)

    # Turns completed
    summary_table.add_row("Turns", *[str(s.turn) for _, s in states])

    # Status
    summary_table.add_row("Status", *[s.status.value for _, s in states])

    # Total cost
    costs = [s.total_cost() for _, s in states]
    summary_table.add_row("Total Cost", *[f"${c:.2f}" for c in costs])

    # Cost per turn
    cost_per_turn = [c / s.turn if s.turn > 0 else 0 for c, (_, s) in zip(costs, states)]
    summary_table.add_row("Cost/Turn", *[f"${c:.3f}" for c in cost_per_turn])

    console.print(summary_table)
    console.print()

    # Actor comparison using Rich Table
    print_section("Actor Models")
    all_actors = set()
    for _, state in states:
        all_actors.update(state.actors.keys())

    actor_table = Table(show_header=True, header_style="bold cyan")
    actor_table.add_column("Actor", style="cyan")
    for rp in run_paths:
        actor_table.add_column(Path(rp).name)

    for actor_name in sorted(all_actors):
        models = []
        for _, state in states:
            if actor_name in state.actors:
                models.append(state.actors[actor_name].model)
            else:
                models.append("[dim]N/A[/]")
        actor_table.add_row(actor_name, *models)

    console.print(actor_table)
    console.print()

    # Cost by actor using Rich Table
    print_section("Cost by Actor")
    cost_table = Table(show_header=True, header_style="bold cyan")
    cost_table.add_column("Actor", style="cyan")
    for rp in run_paths:
        cost_table.add_column(Path(rp).name, justify="right")

    for actor_name in sorted(all_actors):
        actor_costs = []
        for _, state in states:
            actor_cost = sum(c.cost for c in state.costs if c.actor == actor_name)
            actor_costs.append(f"${actor_cost:.2f}")
        cost_table.add_row(actor_name, *actor_costs)

    console.print(cost_table)
    console.print()

    # Metrics comparison (if available) using Rich Table
    all_metrics = set()
    for _, state in states:
        all_metrics.update(m.name for m in state.metrics)

    if all_metrics:
        print_section("Metrics (Final Turn)")
        metrics_table = Table(show_header=True, header_style="bold cyan")
        metrics_table.add_column("Metric", style="cyan")
        for rp in run_paths:
            metrics_table.add_column(Path(rp).name)

        for metric_name in sorted(all_metrics):
            metric_values = []
            for _, state in states:
                # Get the most recent value for this metric
                matching = [m for m in state.metrics if m.name == metric_name]
                if matching:
                    # Get the one from the highest turn
                    latest = max(matching, key=lambda m: m.turn)
                    value = latest.value
                    if isinstance(value, float):
                        metric_values.append(f"{value:.2f}")
                    else:
                        metric_values.append(str(value)[:17])
                else:
                    metric_values.append("[dim]N/A[/]")
            metrics_table.add_row(metric_name, *metric_values)

        console.print(metrics_table)
        console.print()

    # Cost difference summary
    if len(states) == 2:
        print_section("Comparison Summary")
        cost_diff = costs[1] - costs[0]
        cost_pct = (cost_diff / costs[0] * 100) if costs[0] > 0 else 0

        if cost_diff > 0:
            console.print(f"  {Path(run_paths[1]).name} costs [cost.danger]${abs(cost_diff):.2f}[/] more ({cost_pct:+.1f}%)")
        elif cost_diff < 0:
            console.print(f"  {Path(run_paths[1]).name} costs [cost]${abs(cost_diff):.2f}[/] less ({cost_pct:+.1f}%)")
        else:
            console.print("  Both runs have identical costs")

        turn_diff = states[1][1].turn - states[0][1].turn
        if turn_diff != 0:
            console.print(f"  Turn difference: {turn_diff:+d}")

        console.print()

    print_success(f"Compared {len(states)} runs")


@cli.command()
@click.argument("scenario_path", type=click.Path(exists=True, file_okay=False))
@click.option("--turns", type=int, default=3, help="Number of turns to benchmark (default: 3)")
@click.option("--dry-run", is_flag=True, help="Show what would be benchmarked without running")
def benchmark(scenario_path: str, turns: int, dry_run: bool) -> None:
    """
    Run performance benchmark on scenario

    SCENARIO_PATH: Path to scenario directory

    Measures:
    - Startup time (scenario loading and initialization)
    - Turn execution time (average and P95)
    - Memory usage (initial, peak, final)
    - Cost per turn
    """
    import time
    import statistics
    from pathlib import Path
    from scenario_lab.utils.memory_optimizer import get_memory_monitor, MemoryStats

    print_header("Performance Benchmark")
    print_info("Scenario", scenario_path)
    print_info("Turns", str(turns))

    if dry_run:
        console.print()
        print_warning("Dry run mode - no actual execution")
        console.print()
        console.print("Would benchmark:")
        console.print(f"  - Scenario: [path]{scenario_path}[/]")
        console.print(f"  - Turns: [cyan]{turns}[/]")
        console.print()
        console.print("Metrics that will be measured:")
        console.print("  - Startup time (scenario loading)")
        console.print("  - Turn execution time (avg, P95)")
        console.print("  - Memory usage (initial, peak, final)")
        console.print("  - Total and per-turn cost")
        return

    console.print()

    # Initialize memory monitor
    mem_monitor = get_memory_monitor()
    initial_stats = mem_monitor.get_memory_stats()
    peak_memory_mb = initial_stats.process_mb if initial_stats else 0

    # Track timing
    turn_times: list[float] = []

    try:
        from scenario_lab.runners import SyncRunner
        from scenario_lab.core.events import EventType, Event

        # Measure startup time
        print_section("Initializing...")
        startup_start = time.time()

        runner = SyncRunner(
            scenario_path=scenario_path,
            end_turn=turns,
        )
        runner.setup()

        startup_time = time.time() - startup_start
        console.print(f"  Startup time: [green]{startup_time:.2f}s[/]")

        # Track turn times via events
        turn_start_time = None

        async def on_turn_start(event: Event):
            nonlocal turn_start_time
            turn_start_time = time.time()
            turn = event.data.get("turn", 0)
            console.print(f"  Running turn {turn}...", end="")

        async def on_turn_complete(event: Event):
            nonlocal turn_start_time, peak_memory_mb
            if turn_start_time:
                turn_time = time.time() - turn_start_time
                turn_times.append(turn_time)
                console.print(f" [cyan]{turn_time:.2f}s[/]")

                # Check memory after each turn
                current_stats = mem_monitor.get_memory_stats()
                if current_stats and current_stats.process_mb > peak_memory_mb:
                    peak_memory_mb = current_stats.process_mb

        # Register handlers
        event_bus = runner.event_bus
        event_bus.on(EventType.TURN_STARTED, on_turn_start)
        event_bus.on(EventType.TURN_COMPLETED, on_turn_complete)

        # Run benchmark
        print_section("Running benchmark...")
        total_start = time.time()
        final_state = asyncio.run(runner.run())
        total_time = time.time() - total_start

        # Get final memory stats
        final_stats = mem_monitor.get_memory_stats()

        # Calculate statistics
        console.print()
        print_section("Results")

        # Timing stats
        console.print()
        console.print("[bold]  Timing:[/]")
        console.print(f"    Startup time:     [green]{startup_time:.2f}s[/]")
        console.print(f"    Total time:       [green]{total_time:.2f}s[/]")

        if turn_times:
            avg_turn = statistics.mean(turn_times)
            console.print(f"    Avg turn time:    [cyan]{avg_turn:.2f}s[/]")

            if len(turn_times) >= 2:
                # Calculate P95 (or max if too few samples)
                sorted_times = sorted(turn_times)
                p95_index = int(len(sorted_times) * 0.95)
                p95_time = sorted_times[min(p95_index, len(sorted_times) - 1)]
                console.print(f"    P95 turn time:    [cyan]{p95_time:.2f}s[/]")

                min_time = min(turn_times)
                max_time = max(turn_times)
                console.print(f"    Min/Max turn:     {min_time:.2f}s / {max_time:.2f}s")

        # Memory stats
        console.print()
        console.print("[bold]  Memory:[/]")
        if initial_stats:
            console.print(f"    Initial:          [blue]{initial_stats.process_mb:.1f} MB[/]")
        if peak_memory_mb > 0:
            console.print(f"    Peak:             [yellow]{peak_memory_mb:.1f} MB[/]")
        if final_stats:
            console.print(f"    Final:            [blue]{final_stats.process_mb:.1f} MB[/]")
            if initial_stats:
                memory_delta = final_stats.process_mb - initial_stats.process_mb
                delta_style = "red" if memory_delta > 50 else "green"
                console.print(f"    Delta:            [{delta_style}]{memory_delta:+.1f} MB[/]")

        # Cost stats
        console.print()
        console.print("[bold]  Cost:[/]")
        total_cost = final_state.total_cost()
        console.print(f"    Total cost:       [green]${total_cost:.4f}[/]")

        if final_state.turn > 0:
            cost_per_turn = total_cost / final_state.turn
            console.print(f"    Cost per turn:    [green]${cost_per_turn:.4f}[/]")

        # Cost by phase
        phase_costs: dict[str, float] = {}
        for cost_record in final_state.costs:
            phase = cost_record.phase or "unknown"
            phase_costs[phase] = phase_costs.get(phase, 0) + cost_record.cost

        if phase_costs:
            console.print("    By phase:")
            for phase, cost in sorted(phase_costs.items()):
                console.print(f"      {phase:<16} ${cost:.4f}")

        # Summary
        console.print()
        print_section("Summary")
        efficiency = total_cost / total_time if total_time > 0 else 0
        console.print(f"  Turns completed: {final_state.turn}")
        console.print(f"  Time efficiency: ${efficiency:.4f}/second")

        if turn_times:
            throughput = len(turn_times) / sum(turn_times) if sum(turn_times) > 0 else 0
            console.print(f"  Throughput:      {throughput:.2f} turns/second")

        console.print()
        print_success("Benchmark complete")

        # Output location
        if hasattr(runner, 'output_path') and runner.output_path:
            console.print()
            console.print(f"Benchmark run saved to: [path]{runner.output_path}[/]")

    except ImportError as e:
        print_error(
            "Could not load benchmark dependencies",
            str(e),
            "Make sure scenario_lab is installed correctly"
        )
        sys.exit(1)
    except Exception as e:
        import traceback
        print_error("Benchmark failed", str(e))
        if logging.getLogger().level == logging.DEBUG:
            traceback.print_exc()
        sys.exit(1)


@cli.command()
def version() -> None:
    """Show version information"""
    print_header("Scenario Lab V2")
    print_info("Version", __version__)
    print_info("Architecture", "Event-driven modular", "blue")
    print_info("Status", "V2 Complete", "green")

    print_section("Features:")
    print_checklist_item("Event-driven execution engine")
    print_checklist_item("Immutable state management")
    print_checklist_item("CLI commands (run, validate, estimate, benchmark)")
    print_checklist_item("REST API with WebSocket streaming")
    print_checklist_item("Batch processing with parameter variation")
    print_checklist_item("Response caching and cost management")
    console.print()


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
    console.print()
    print_link("\U0001f310 API Documentation", f"http://{host}:{port}/docs")
    print_link("\U0001f4ca OpenAPI Schema", f"http://{host}:{port}/openapi.json")
    console.print()

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
    console.print()

    # V2 wizard not yet implemented - provide guidance
    print_warning("Interactive wizard not yet available in V2")
    console.print()
    console.print("To create a scenario manually:")
    console.print()
    console.print("  1. Create a scenario directory:")
    console.print("     [command]mkdir -p scenarios/my-scenario/actors[/]")
    console.print()
    console.print("  2. Create scenario.yaml with:")
    console.print("     [yellow]name, description, initial_world_state, turns[/]")
    console.print()
    console.print("  3. Create actor files in actors/:")
    console.print("     [yellow]name, llm_model, system_prompt, goals[/]")
    console.print()
    console.print("  4. Validate your scenario:")
    console.print("     [command]scenario-lab validate scenarios/my-scenario[/]")
    console.print()
    console.print("For complete documentation, see:")
    console.print("  [path]AGENTS.md[/] - Full YAML schema reference")
    console.print("  [path]scenarios/[/] - Example scenarios")
    console.print()


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
    console.print()

    # V2 wizard not yet implemented - provide guidance
    print_warning("Interactive wizard not yet available in V2")
    console.print()
    console.print("To create a batch configuration manually:")
    console.print()
    console.print("  1. Create a YAML file with batch configuration:")
    console.print("     [yellow]experiment_name, base_scenario, variations[/]")
    console.print()
    console.print("  2. Define parameter variations:")
    console.print("     [yellow]actor_models, scenario_parameters, runs_per_variation[/]")
    console.print()
    console.print("  3. Set execution limits:")
    console.print("     [yellow]max_parallel_workers, total_budget, per_run_budget[/]")
    console.print()
    console.print("  4. Run with dry-run to preview:")
    console.print("     [command]python -m scenario_lab.batch.batch_runner config.yaml --dry-run[/]")
    console.print()
    console.print("For examples, see:")
    console.print("  [path]examples/[/] - Example batch configurations")
    console.print()


def main() -> None:
    """Entry point for CLI"""
    cli()


if __name__ == "__main__":
    main()
