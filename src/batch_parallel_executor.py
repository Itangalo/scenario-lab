"""
Batch Parallel Executor - Async execution with rate limiting for batch runs
"""
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging


class RateLimitManager:
    """
    Manages rate limiting across parallel workers
    """

    def __init__(self):
        """Initialize rate limit manager"""
        self.backoff_until = 0.0  # Timestamp when backoff expires
        self.backoff_duration = 0.0  # Current backoff duration in seconds
        self.consecutive_429s = 0  # Count of consecutive 429 errors
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger("rate_limit_manager")

    async def check_rate_limit(self):
        """
        Check if we're currently in a rate limit backoff period
        If yes, wait until backoff expires
        """
        async with self.lock:
            if self.backoff_until > time.time():
                wait_time = self.backoff_until - time.time()
                self.logger.warning(f"Rate limit active, waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)

    async def record_429_error(self, retry_after: Optional[int] = None):
        """
        Record a 429 rate limit error and set backoff

        Args:
            retry_after: Optional retry-after value from response headers (seconds)
        """
        async with self.lock:
            self.consecutive_429s += 1

            # Calculate backoff duration
            if retry_after:
                # Use server-provided retry-after
                backoff = retry_after
            else:
                # Exponential backoff: 2^n seconds, max 60
                backoff = min(2 ** self.consecutive_429s, 60)

            self.backoff_duration = backoff
            self.backoff_until = time.time() + backoff

            self.logger.warning(
                f"Rate limit hit (#{self.consecutive_429s}), backing off {backoff:.1f}s"
            )

    async def record_success(self):
        """Record a successful request (resets consecutive 429 counter)"""
        async with self.lock:
            if self.consecutive_429s > 0:
                self.logger.info("Rate limit cleared, resuming normal operation")
                self.consecutive_429s = 0
                self.backoff_duration = 0.0


class BatchParallelExecutor:
    """
    Executes batch scenarios in parallel with rate limiting
    """

    def __init__(
        self,
        max_parallel: int = 2,
        rate_limit_manager: Optional[RateLimitManager] = None
    ):
        """
        Initialize parallel executor

        Args:
            max_parallel: Maximum number of concurrent executions
            rate_limit_manager: Shared rate limit manager (created if not provided)
        """
        self.max_parallel = max_parallel
        self.semaphore = asyncio.Semaphore(max_parallel)
        self.rate_limit_manager = rate_limit_manager or RateLimitManager()
        self.logger = logging.getLogger("batch_parallel_executor")

    async def execute_scenario(
        self,
        scenario_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a single scenario with rate limiting and semaphore control

        Args:
            scenario_func: The scenario function to execute (will be run in thread pool)
            *args: Positional arguments for scenario_func
            **kwargs: Keyword arguments for scenario_func

        Returns:
            Result from scenario_func
        """
        # Wait for semaphore (limits concurrent executions)
        async with self.semaphore:
            # Check rate limit before starting
            await self.rate_limit_manager.check_rate_limit()

            try:
                # Run scenario function in thread pool (since it's blocking)
                result = await asyncio.to_thread(scenario_func, *args, **kwargs)

                # Record success (clears rate limit counter)
                await self.rate_limit_manager.record_success()

                return result

            except Exception as e:
                # Check if this is a rate limit error
                error_str = str(e).lower()
                if '429' in error_str or 'rate limit' in error_str:
                    # Record 429 and set backoff
                    await self.rate_limit_manager.record_429_error()
                    # Re-raise to let caller handle
                    raise

                # Other errors just propagate
                raise

    async def execute_batch(
        self,
        tasks: List[Dict[str, Any]],
        scenario_func: Callable,
        progress_callback: Optional[Callable] = None
    ) -> List[Any]:
        """
        Execute a batch of scenarios in parallel

        Args:
            tasks: List of task dictionaries containing args/kwargs for each run
            scenario_func: The scenario function to execute
            progress_callback: Optional callback(task_id, result) called after each completion

        Returns:
            List of results in same order as tasks
        """
        async def run_task(task_id: int, task: Dict[str, Any]):
            """Run a single task with progress callback"""
            try:
                result = await self.execute_scenario(
                    scenario_func,
                    *task.get('args', []),
                    **task.get('kwargs', {})
                )

                # Call progress callback if provided
                if progress_callback:
                    await asyncio.to_thread(progress_callback, task_id, result)

                return result

            except Exception as e:
                # Call progress callback with error
                if progress_callback:
                    await asyncio.to_thread(progress_callback, task_id, {'error': str(e)})

                return {'error': str(e), 'task_id': task_id}

        # Create tasks for all scenarios
        coroutines = [run_task(i, task) for i, task in enumerate(tasks)]

        # Execute all tasks concurrently (limited by semaphore)
        results = await asyncio.gather(*coroutines, return_exceptions=False)

        return results

    def get_status(self) -> Dict[str, Any]:
        """
        Get current executor status

        Returns:
            Status dictionary
        """
        return {
            'max_parallel': self.max_parallel,
            'rate_limit_active': self.rate_limit_manager.backoff_until > time.time(),
            'backoff_remaining': max(0, self.rate_limit_manager.backoff_until - time.time()),
            'consecutive_429s': self.rate_limit_manager.consecutive_429s
        }


async def run_scenarios_parallel(
    scenarios: List[Dict[str, Any]],
    scenario_func: Callable,
    max_parallel: int = 2,
    progress_callback: Optional[Callable] = None
) -> List[Any]:
    """
    Convenience function to run scenarios in parallel

    Args:
        scenarios: List of scenario configurations (each with 'args' and 'kwargs')
        scenario_func: Function to execute for each scenario
        max_parallel: Maximum concurrent executions
        progress_callback: Optional callback for progress updates

    Returns:
        List of results

    Example:
        scenarios = [
            {'args': ['scenario1'], 'kwargs': {'output': 'out1'}},
            {'args': ['scenario2'], 'kwargs': {'output': 'out2'}},
        ]
        results = await run_scenarios_parallel(scenarios, run_scenario, max_parallel=3)
    """
    executor = BatchParallelExecutor(max_parallel=max_parallel)
    return await executor.execute_batch(scenarios, scenario_func, progress_callback)
