"""Progress tracking and display for simulations using Rich."""

from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich import box


class ProgressTracker:
    """Track and display simulation progress with Rich."""

    def __init__(self, total_turns: int, actors: list[str], enabled: bool = True, quiet: bool = False):
        """Initialize progress tracker.

        Args:
            total_turns: Total number of turns to run
            actors: List of actor IDs
            enabled: Whether to show progress (--no-progress disables)
            quiet: Minimal output mode (--quiet enables)
        """
        self.total_turns = total_turns
        self.actors = actors
        self.enabled = enabled and not quiet
        self.quiet = quiet
        self.console = Console()

        # Timing data
        self.turn_times: list[float] = []
        self.start_time: Optional[datetime] = None
        self.turn_start: Optional[datetime] = None

        # Progress tracking
        self.current_turn = 0
        self.progress: Optional[Progress] = None
        self.live: Optional[Live] = None
        self.turn_task_id: Optional[int] = None

        # Step tracking
        self.steps = [
            "Determining external events",
            "Getting actor actions",
            "Updating metric rules",
            "Updating metrics and narrative",
            "Updating historical summary"
        ]

    def start_simulation(self):
        """Mark the start of the simulation."""
        if not self.enabled:
            return

        self.start_time = datetime.now()

        # Create welcome panel
        welcome = Panel(
            f"[bold cyan]Starting simulation: {self.total_turns} turns, {len(self.actors)} actors[/bold cyan]\n"
            f"[dim]Started at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
            box=box.ROUNDED,
            border_style="cyan"
        )
        self.console.print(welcome)
        self.console.print()

    def start_turn(self, turn: int, time_period: str):
        """Mark the start of a turn.

        Args:
            turn: Turn number (1-indexed)
            time_period: Time period description
        """
        self.current_turn = turn
        self.turn_start = datetime.now()

        if self.quiet:
            # Minimal output for quiet mode
            self.console.print(f"Turn {turn}/{self.total_turns}: {time_period}")
            return

        if not self.enabled:
            # Print simple output when progress is disabled
            self.console.print(f"\n{'='*60}")
            self.console.print(f"TURN {turn}/{self.total_turns}: {time_period}")
            self.console.print(f"{'='*60}")
            return

        # Create turn panel with ETA
        eta_text = self._get_eta_text()
        turn_panel = Panel(
            f"[bold yellow]Turn {turn}/{self.total_turns}[/bold yellow]: {time_period}\n{eta_text}",
            box=box.DOUBLE,
            border_style="yellow"
        )
        self.console.print(turn_panel)

    def start_step(self, step_num: int, details: str = "") -> "StepContext":
        """Start a simulation step (1-5).

        Args:
            step_num: Step number (1-5)
            details: Optional additional details

        Returns:
            Context manager for the step
        """
        return StepContext(self, step_num, details)

    def _update_step_display(self, step_num: int, details: str, status: str):
        """Internal: Update step display.

        Args:
            step_num: Step number (1-5)
            details: Step details
            status: "start", "complete"
        """
        if self.quiet:
            return

        if not self.enabled:
            # Simple print when progress disabled
            if status == "start":
                step_name = self.steps[step_num - 1] if step_num <= len(self.steps) else f"Step {step_num}"
                self.console.print(f"\n[{step_num}/5] {step_name}...")
            elif status == "complete":
                self.console.print(f"  → {details}")
            return

        # Rich output
        if status == "start":
            step_name = self.steps[step_num - 1] if step_num <= len(self.steps) else f"Step {step_num}"
            self.console.print(f"\n  [{step_num}/5] [cyan]{step_name}...[/cyan]")
        elif status == "complete":
            self.console.print(f"    [green]✓[/green] {details}")

    def complete_turn(self, turn: int, cost_usd: float, tokens: int):
        """Mark turn completion.

        Args:
            turn: Turn number
            cost_usd: Cost in USD for this turn
            tokens: Total tokens used
        """
        if not self.turn_start:
            return

        duration = (datetime.now() - self.turn_start).total_seconds()
        self.turn_times.append(duration)

        if self.quiet:
            # Minimal output
            self.console.print(f"  ✓ ${cost_usd:.4f} ({tokens:,} tokens, {duration:.1f}s)")
            return

        if not self.enabled:
            # Simple output when disabled
            self.console.print(f"\n💰 Turn {turn} cost: ${cost_usd:.4f} ({tokens:,} tokens)")
            return

        # Rich output with summary
        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="dim")
        summary.add_column(style="bold")

        summary.add_row("Duration:", f"{duration:.1f}s")
        summary.add_row("Cost:", f"${cost_usd:.4f}")
        summary.add_row("Tokens:", f"{tokens:,}")

        panel = Panel(
            summary,
            title=f"[bold green]Turn {turn} Complete[/bold green]",
            border_style="green",
            box=box.ROUNDED
        )
        self.console.print()
        self.console.print(panel)

    def complete_simulation(self, total_cost_usd: float, total_tokens: int):
        """Mark simulation completion with summary.

        Args:
            total_cost_usd: Total cost in USD
            total_tokens: Total tokens used
        """
        if not self.start_time:
            return

        total_duration = (datetime.now() - self.start_time).total_seconds()

        if self.quiet:
            # Minimal summary
            self.console.print(f"\nCompleted: ${total_cost_usd:.4f}, {total_tokens:,} tokens, {total_duration:.1f}s")
            return

        # Create summary table
        summary = Table(title="Simulation Complete", box=box.ROUNDED, border_style="green")
        summary.add_column("Metric", style="cyan")
        summary.add_column("Value", style="bold yellow")

        summary.add_row("Total Turns", str(self.total_turns))
        summary.add_row("Total Duration", f"{total_duration/60:.1f} minutes")
        summary.add_row("Avg Turn Time", f"{sum(self.turn_times)/len(self.turn_times):.1f}s" if self.turn_times else "N/A")
        summary.add_row("Total Cost", f"${total_cost_usd:.4f}")
        summary.add_row("Total Tokens", f"{total_tokens:,}")
        summary.add_row("Cost per Turn", f"${total_cost_usd/self.total_turns:.4f}" if self.total_turns > 0 else "N/A")

        self.console.print()
        self.console.print(summary)
        self.console.print()

    def _get_eta_text(self) -> str:
        """Get ETA text for remaining turns."""
        if not self.turn_times:
            return "[dim]Estimated time: Calculating...[/dim]"

        avg_turn_time = sum(self.turn_times) / len(self.turn_times)
        remaining_turns = self.total_turns - self.current_turn + 1
        eta_seconds = avg_turn_time * remaining_turns

        if eta_seconds < 60:
            return f"[dim]Estimated time remaining: {eta_seconds:.0f}s[/dim]"
        else:
            return f"[dim]Estimated time remaining: {eta_seconds/60:.1f} minutes[/dim]"

    @contextmanager
    def spinner(self, text: str):
        """Context manager for spinner during LLM calls.

        Args:
            text: Description of the operation

        Example:
            with progress.spinner("Calling LLM..."):
                response = llm.complete(...)
        """
        if not self.enabled or self.quiet:
            yield
            return

        with self.console.status(f"[cyan]{text}[/cyan]", spinner="dots") as status:
            yield


class StepContext:
    """Context manager for simulation steps."""

    def __init__(self, tracker: ProgressTracker, step_num: int, details: str):
        self.tracker = tracker
        self.step_num = step_num
        self.details = details

    def __enter__(self):
        self.tracker._update_step_display(self.step_num, self.details, "start")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.tracker._update_step_display(self.step_num, self.details, "complete")
        return False

    def update(self, details: str):
        """Update step details."""
        self.details = details
