"""
Batch Runner - Orchestrates batch scenario execution (V2)

Main entry point for batch execution that composes:
- BatchConfig: Configuration loading and validation
- BatchExecutor: Sequential and parallel execution
- BatchDryRun: Preview mode without execution
- BatchCostManager: Budget tracking and enforcement
- ParameterVariator: Variation generation

Features:
- Configuration loading and validation
- Variation generation and execution
- Cost management and budget enforcement
- Progress tracking with rich display
- Sequential and parallel execution modes
- State persistence for resumption
- Comprehensive error handling
- Summary generation with statistics
"""
import os
import json
import asyncio
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

from scenario_lab.batch.batch_config import BatchConfig, load_batch_config, save_config_copy
from scenario_lab.batch.batch_executor import BatchExecutor
from scenario_lab.batch.batch_dry_run import BatchDryRun
from scenario_lab.batch.parameter_variator import ParameterVariator
from scenario_lab.batch.batch_cost_manager import BatchCostManager
from scenario_lab.utils.error_handler import ErrorHandler
from scenario_lab.utils.response_cache import get_global_cache
from scenario_lab.utils.memory_optimizer import get_memory_monitor


class BatchRunner:
    """
    Orchestrates batch scenario execution (V2)

    Integrates all batch components:
    - Parameter variation
    - Cost management
    - Progress tracking
    - Parallel execution with rate limiting
    - Error handling
    - State persistence
    """

    def __init__(
        self,
        config_path: str,
        resume: bool = False,
        progress_display: bool = True,
        dry_run: bool = False
    ):
        """
        Initialize batch runner

        Args:
            config_path: Path to batch configuration YAML
            resume: Whether to resume incomplete batch
            progress_display: Whether to show rich progress display
            dry_run: Preview mode (don't execute)
        """
        self.config_path = config_path
        self.resume_mode = resume
        self.progress_display = progress_display
        self.dry_run = dry_run

        # Load configuration
        self.config = load_batch_config(config_path)

        # Initialize logger
        self.logger = logging.getLogger("batch_runner")

        # Initialize components
        self.variator = ParameterVariator(
            base_scenario_path=self.config.base_scenario,
            variations_config=self.config.variations
        )

        self.cost_manager = BatchCostManager(
            budget_limit=self.config.budget_limit,
            cost_per_run_limit=self.config.cost_per_run_limit
        )

        self.error_handler = ErrorHandler()

        # Initialize executor
        self.executor = BatchExecutor(
            config=self.config,
            variator=self.variator,
            cost_manager=self.cost_manager,
            error_handler=self.error_handler,
            progress_display=self.progress_display
        )

        # Initialize dry-run preview
        self._dry_run_preview = BatchDryRun(
            config=self.config,
            variator=self.variator,
            cost_manager=self.cost_manager
        )

    # Backward compatibility properties
    @property
    def experiment_name(self) -> str:
        return self.config.experiment_name

    @property
    def base_scenario(self) -> str:
        return self.config.base_scenario

    @property
    def output_dir(self) -> str:
        return self.config.output_dir

    @property
    def runs_per_variation(self) -> int:
        return self.config.runs_per_variation

    @property
    def max_parallel(self) -> int:
        return self.config.max_parallel

    @property
    def runs_dir(self) -> str:
        return self.config.runs_dir

    @property
    def variations(self):
        return self.executor.variations

    @variations.setter
    def variations(self, value):
        self.executor.variations = value

    @property
    def completed_runs(self):
        return self.executor.completed_runs

    @completed_runs.setter
    def completed_runs(self, value):
        self.executor.completed_runs = value

    @property
    def failed_runs(self):
        return self.executor.failed_runs

    @failed_runs.setter
    def failed_runs(self, value):
        self.executor.failed_runs = value

    @property
    def start_time(self):
        return self.executor.start_time

    @start_time.setter
    def start_time(self, value):
        self.executor.start_time = value

    @property
    def end_time(self):
        return self.executor.end_time

    @end_time.setter
    def end_time(self, value):
        self.executor.end_time = value

    def _setup_output_directory(self) -> None:
        """Setup output directory structure"""
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs(self.config.runs_dir, exist_ok=True)

        # Save copy of configuration
        save_config_copy(self.config, self.config_path, self.config.output_dir)

    def _generate_run_id(self, variation_id: int, run_number: int) -> str:
        """
        Generate unique run identifier (backward compatibility)

        Args:
            variation_id: Variation number
            run_number: Run number within variation

        Returns:
            Run ID string (e.g., "var-001-run-003")
        """
        return self.executor.generate_run_id(variation_id, run_number)

    def _save_batch_state(self) -> None:
        """Save batch execution state for resumption (backward compatibility)"""
        self.executor.save_state()

    def _load_batch_state(self) -> bool:
        """Load batch execution state from previous run (backward compatibility)"""
        return self.executor.load_state()

    async def _run_single_scenario(
        self,
        run_id: str,
        variation: Dict[str, Any],
        run_number: int
    ) -> Dict[str, Any]:
        """Execute a single scenario run (backward compatibility)"""
        return await self.executor.run_single_scenario(run_id, variation, run_number)

    def show_batch_preview(self) -> None:
        """Show detailed preview of batch execution without running"""
        self._dry_run_preview.show_preview()

    def run(self) -> None:
        """Execute the batch experiment"""
        # If dry-run mode, show preview and exit
        if self.dry_run:
            self.show_batch_preview()
            return

        # Setup output directory
        self._setup_output_directory()

        # Choose execution mode based on max_parallel
        if self.config.max_parallel > 1:
            # Use parallel execution
            asyncio.run(self._run_parallel_with_summary())
        else:
            # Use sequential execution
            asyncio.run(self._run_sequential_with_summary())

    async def _run_sequential_with_summary(self) -> None:
        """Run sequential execution and generate summary"""
        await self.executor.run_sequential(resume_mode=self.resume_mode)
        self._generate_summary()

    async def _run_parallel_with_summary(self) -> None:
        """Run parallel execution and generate summary"""
        await self.executor.run_parallel(resume_mode=self.resume_mode)
        self._generate_summary()

    async def run_sequential(self) -> None:
        """Execute the batch experiment sequentially (backward compatibility)"""
        self._setup_output_directory()
        await self.executor.run_sequential(resume_mode=self.resume_mode)
        self._generate_summary()

    async def run_parallel(self) -> None:
        """Execute the batch experiment in parallel (backward compatibility)"""
        self._setup_output_directory()
        await self.executor.run_parallel(resume_mode=self.resume_mode)
        self._generate_summary()

    def _generate_summary(self) -> None:
        """Generate and save batch summary"""
        duration = None
        if self.executor.start_time and self.executor.end_time:
            duration = (self.executor.end_time - self.executor.start_time).total_seconds()
        elif self.executor.start_time:
            duration = (datetime.now() - self.executor.start_time).total_seconds()

        summary = {
            'experiment_name': self.config.experiment_name,
            'base_scenario': self.config.base_scenario,
            'total_variations': len(self.executor.variations),
            'runs_per_variation': self.config.runs_per_variation,
            'total_runs_planned': len(self.executor.variations) * self.config.runs_per_variation,
            'runs_completed': len(self.executor.completed_runs),
            'runs_failed': len(self.executor.failed_runs),
            'duration_seconds': duration,
            'cost_summary': self.cost_manager.get_summary(),
            'failed_runs': self.executor.failed_runs
        }

        # Save JSON summary
        summary_file = os.path.join(self.config.output_dir, 'batch-summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        # Print summary
        self.logger.info(f"\nRuns completed: {summary['runs_completed']}/{summary['total_runs_planned']}")
        self.logger.info(f"Runs failed: {summary['runs_failed']}")
        self.logger.info(f"Total cost: ${self.cost_manager.total_spent:.2f}")

        if self.cost_manager.budget_limit:
            pct = (self.cost_manager.total_spent / self.cost_manager.budget_limit) * 100
            self.logger.info(f"Budget used: {pct:.1f}%")

        if summary.get('duration_seconds'):
            minutes = summary['duration_seconds'] / 60
            self.logger.info(f"Duration: {minutes:.1f} minutes")

        if summary['runs_completed'] > 0:
            avg = self.cost_manager.get_average_cost_per_run()
            if avg is not None:
                self.logger.info(f"Average per run: ${avg:.3f}")

        # Show failed runs details if any
        if summary['runs_failed'] > 0:
            self.logger.info(f"\nFailed Runs Details:")
            for failed in self.executor.failed_runs[:10]:  # Show first 10 failures
                error_preview = str(failed.get('error', 'Unknown error'))[:100]
                self.logger.info(f"   - {failed['run_id']}: {error_preview}")
            if len(self.executor.failed_runs) > 10:
                self.logger.info(f"   ... and {len(self.executor.failed_runs) - 10} more (see batch-summary.json)")

        # Show cache statistics if caching was used
        cache = get_global_cache()
        cache_stats = cache.get_stats()
        if cache_stats.total_requests > 0:
            self.logger.info(f"\nCache Performance:")
            self.logger.info(f"   Requests: {cache_stats.total_requests}")
            self.logger.info(f"   Hit rate: {cache_stats.hit_rate:.1f}%")
            self.logger.info(f"   Tokens saved: {cache_stats.tokens_saved:,}")
            self.logger.info(f"   Cost saved: ${cache_stats.estimated_cost_saved:.4f}")

        # Show memory usage summary
        memory_monitor = get_memory_monitor()
        mem_stats = memory_monitor.get_memory_stats()
        if mem_stats:
            self.logger.info(f"\nMemory Usage:")
            self.logger.info(f"   System: {mem_stats.used_mb:,.1f}/{mem_stats.total_mb:,.1f} MB ({mem_stats.percent_used:.1f}%)")
            self.logger.info(f"   Process: {mem_stats.process_mb:,.1f} MB")

        self.logger.info(f"\nResults saved to: {self.config.output_dir}")
        self.logger.info(f"Summary: {summary_file}")


def main():
    """Command-line interface for batch runner"""
    parser = argparse.ArgumentParser(
        description='Run batch scenario experiments for statistical analysis (V2)'
    )
    parser.add_argument(
        'config',
        help='Path to batch configuration YAML file'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume incomplete batch execution'
    )
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable rich progress display (use simple logging instead)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show preview of what will be executed without running'
    )

    args = parser.parse_args()

    # Create and run batch
    batch_runner = BatchRunner(
        args.config,
        resume=args.resume,
        progress_display=not args.no_progress,
        dry_run=args.dry_run
    )
    batch_runner.run()


if __name__ == '__main__':
    main()
