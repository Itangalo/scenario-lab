"""
Batch Processing Components (V2)

Components for running multiple scenario variations in batch mode.

Architecture:
- BatchRunner: Main orchestrator for batch execution
- BatchConfig: Configuration loading and validation
- BatchExecutor: Sequential and parallel execution logic
- BatchDryRun: Preview mode without execution
- BatchCostManager: Budget tracking and enforcement
- ParameterVariator: Variation generation
- BatchProgressTracker: Progress display
- BatchAnalyzer: Statistical analysis of results
"""
from scenario_lab.batch.parameter_variator import ParameterVariator
from scenario_lab.batch.batch_cost_manager import BatchCostManager
from scenario_lab.batch.batch_progress_tracker import BatchProgressTracker, SimpleProgressTracker
from scenario_lab.batch.batch_parallel_executor import (
    BatchParallelExecutor,
    RateLimitManager,
    run_scenarios_parallel
)
from scenario_lab.batch.batch_config import BatchConfig, load_batch_config
from scenario_lab.batch.batch_executor import BatchExecutor
from scenario_lab.batch.batch_dry_run import BatchDryRun, show_batch_preview
from scenario_lab.batch.batch_runner import BatchRunner
from scenario_lab.batch.batch_analyzer import BatchAnalyzer

__all__ = [
    # Configuration
    'BatchConfig',
    'load_batch_config',
    # Execution
    'BatchRunner',
    'BatchExecutor',
    'BatchDryRun',
    'show_batch_preview',
    # Variation
    'ParameterVariator',
    # Cost management
    'BatchCostManager',
    # Progress tracking
    'BatchProgressTracker',
    'SimpleProgressTracker',
    # Parallel execution
    'BatchParallelExecutor',
    'RateLimitManager',
    'run_scenarios_parallel',
    # Analysis
    'BatchAnalyzer'
]
