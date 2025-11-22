"""
Batch Progress Tracker - Real-time progress display for batch execution (V2)

Features:
- Rich library integration for beautiful progress bars
- Real-time statistics and cost tracking
- Time remaining estimation

V2 Design:
- No V1 dependencies
- Uses shared Rich console from scenario_lab.utils
- Works with V2 batch components
"""
from __future__ import annotations

import time
from datetime import timedelta
from typing import Optional

from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TimeElapsedColumn
)
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel

from scenario_lab.utils.rich_console import console


class BatchProgressTracker:
    """
    Tracks and displays progress for batch scenario execution (V2)

    Provides real-time progress updates with:
    - Progress bars with Rich library
    - Success/failure statistics
    - Cost tracking and budget monitoring
    - Time remaining estimates
    """

    def __init__(
        self,
        total_runs: int,
        experiment_name: str,
        budget_limit: Optional[float] = None,
        use_rich: bool = True
    ):
        """
        Initialize progress tracker

        Args:
            total_runs: Total number of runs in batch
            experiment_name: Name of the experiment
            budget_limit: Optional budget limit in USD
            use_rich: Use rich library for display (default: True)
        """
        self.total_runs = total_runs
        self.experiment_name = experiment_name
        self.budget_limit = budget_limit
        self.use_rich = use_rich

        # Progress tracking
        self.completed_runs = 0
        self.failed_runs = 0
        self.total_cost = 0.0
        self.start_time: Optional[float] = None
        self.current_run_id: Optional[str] = None
        self.current_run_status = "Initializing"

        # Rich components
        self.progress: Optional[Progress] = None
        self.task_id = None
        self.live: Optional[Live] = None

    def start(self) -> None:
        """Start tracking batch progress"""
        self.start_time = time.time()

        if self.use_rich:
            # Create progress bar
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("\u2022"),
                TextColumn("{task.completed}/{task.total} runs"),
                TimeElapsedColumn(),
                TextColumn("\u2022"),
                TimeRemainingColumn(),
            )

            self.task_id = self.progress.add_task(
                f"[cyan]{self.experiment_name}",
                total=self.total_runs
            )

            # Start live display using shared console
            self.live = Live(
                self._generate_display(),
                refresh_per_second=4,
                console=console
            )
            self.live.start()
        else:
            # Simple text output
            console.print(f"\n{'='*60}")
            console.print(f"Batch Experiment: {self.experiment_name}")
            console.print(f"Total runs: {self.total_runs}")
            if self.budget_limit:
                console.print(f"Budget limit: ${self.budget_limit:.2f}")
            console.print(f"{'='*60}\n")

    def stop(self):
        """Stop tracking and display final summary"""
        if self.use_rich and self.live:
            self.live.stop()

        # Print final summary
        self._print_summary()

    def update_run_started(self, run_id: str, variation_description: str) -> None:
        """
        Update progress when a run starts

        Args:
            run_id: Unique run identifier
            variation_description: Description of the variation
        """
        self.current_run_id = run_id
        self.current_run_status = f"Running: {variation_description}"

        if not self.use_rich:
            console.print(f"\u25b6\ufe0f  [{self.completed_runs + 1}/{self.total_runs}] {run_id}: {variation_description}")

    def update_run_completed(self, run_id: str, cost: float, success: bool = True) -> None:
        """
        Update progress when a run completes

        Args:
            run_id: Unique run identifier
            cost: Cost of the run in USD
            success: Whether run completed successfully
        """
        if success:
            self.completed_runs += 1
        else:
            self.failed_runs += 1

        self.total_cost += cost
        self.current_run_id = None
        self.current_run_status = "Idle"

        if self.use_rich and self.progress:
            self.progress.update(self.task_id, advance=1)

            if self.live:
                self.live.update(self._generate_display())
        else:
            status_emoji = "[green]\u2713[/]" if success else "[red]\u274c[/]"
            console.print(f"{status_emoji} {run_id}: Completed (${cost:.3f})")

    def update_cost(self, cost: float):
        """
        Update total cost

        Args:
            cost: Additional cost to add
        """
        self.total_cost += cost

        if self.use_rich and self.live:
            self.live.update(self._generate_display())

    def _generate_display(self) -> Layout:
        """Generate rich display layout"""
        if not self.use_rich:
            return None

        layout = Layout()
        layout.split_column(
            Layout(name="progress", size=3),
            Layout(name="stats", size=8),
            Layout(name="current", size=4)
        )

        # Progress bar
        layout["progress"].update(self.progress)

        # Statistics table
        stats_table = Table(show_header=False, box=None, padding=(0, 2))
        stats_table.add_column("Label", style="cyan")
        stats_table.add_column("Value", style="bold")

        # Calculate success rate
        total_finished = self.completed_runs + self.failed_runs
        success_rate = (self.completed_runs / total_finished * 100) if total_finished > 0 else 0.0

        stats_table.add_row("✓ Successful:", f"{self.completed_runs}")
        stats_table.add_row("❌ Failed:", f"{self.failed_runs}")
        stats_table.add_row("📊 Success Rate:", f"{success_rate:.1f}%")

        # Cost information
        if self.budget_limit:
            budget_pct = (self.total_cost / self.budget_limit * 100) if self.budget_limit > 0 else 0.0
            remaining = self.budget_limit - self.total_cost
            stats_table.add_row(
                "💰 Cost:",
                f"${self.total_cost:.2f} / ${self.budget_limit:.2f} ({budget_pct:.1f}%)"
            )
            stats_table.add_row("💵 Remaining:", f"${remaining:.2f}")
        else:
            stats_table.add_row("💰 Total Cost:", f"${self.total_cost:.2f}")

        # Average cost per run
        if total_finished > 0:
            avg_cost = self.total_cost / total_finished
            stats_table.add_row("💸 Avg/Run:", f"${avg_cost:.3f}")

        layout["stats"].update(Panel(stats_table, title="Statistics", border_style="green"))

        # Current run info
        if self.current_run_id:
            current_info = f"[bold cyan]Current:[/bold cyan] {self.current_run_id}\n"
            current_info += f"[dim]{self.current_run_status}[/dim]"
        else:
            current_info = "[dim]Waiting for next run...[/dim]"

        layout["current"].update(Panel(current_info, title="Status", border_style="blue"))

        return layout

    def _print_summary(self) -> None:
        """Print final summary"""
        if not self.start_time:
            return

        duration = time.time() - self.start_time
        total_finished = self.completed_runs + self.failed_runs
        success_rate = (self.completed_runs / total_finished * 100) if total_finished > 0 else 0.0

        if self.use_rich:
            # Rich formatted summary
            summary_table = Table(title="Batch Execution Summary", show_header=False, box=None)
            summary_table.add_column("Label", style="cyan")
            summary_table.add_column("Value", style="bold")

            summary_table.add_row("Total Runs:", str(self.total_runs))
            summary_table.add_row("Completed:", str(self.completed_runs))
            summary_table.add_row("Failed:", str(self.failed_runs))
            summary_table.add_row("Success Rate:", f"{success_rate:.1f}%")
            summary_table.add_row("Total Cost:", f"${self.total_cost:.2f}")

            if self.completed_runs > 0:
                avg_cost = self.total_cost / self.completed_runs
                summary_table.add_row("Avg Cost/Run:", f"${avg_cost:.3f}")

            duration_str = str(timedelta(seconds=int(duration)))
            summary_table.add_row("Duration:", duration_str)

            console.print("\n")
            console.print(summary_table)
            console.print("\n")
        else:
            # Simple text summary
            console.print(f"\n{'='*60}")
            console.print("Batch Execution Summary")
            console.print(f"{'='*60}")
            console.print(f"Total runs: {self.total_runs}")
            console.print(f"Completed: {self.completed_runs}")
            console.print(f"Failed: {self.failed_runs}")
            console.print(f"Success rate: {success_rate:.1f}%")
            console.print(f"Total cost: ${self.total_cost:.2f}")

            if self.completed_runs > 0:
                avg_cost = self.total_cost / self.completed_runs
                console.print(f"Avg cost per run: ${avg_cost:.3f}")

            duration_str = str(timedelta(seconds=int(duration)))
            console.print(f"Duration: {duration_str}")
            console.print(f"{'='*60}\n")

    def get_estimated_time_remaining(self) -> Optional[float]:
        """
        Estimate time remaining based on current progress

        Returns:
            Estimated seconds remaining, or None if not enough data
        """
        if not self.start_time or self.completed_runs == 0:
            return None

        elapsed = time.time() - self.start_time
        avg_time_per_run = elapsed / (self.completed_runs + self.failed_runs)
        remaining_runs = self.total_runs - (self.completed_runs + self.failed_runs)

        return avg_time_per_run * remaining_runs


class SimpleProgressTracker:
    """
    Fallback simple progress tracker without rich library (V2)
    (Alias for BatchProgressTracker with use_rich=False)
    """

    def __init__(self, total_runs: int, experiment_name: str, budget_limit: Optional[float] = None):
        self.tracker = BatchProgressTracker(
            total_runs=total_runs,
            experiment_name=experiment_name,
            budget_limit=budget_limit,
            use_rich=False
        )

    def __getattr__(self, name):
        return getattr(self.tracker, name)
