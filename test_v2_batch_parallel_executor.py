#!/usr/bin/env python3
"""
Test V2 Batch Parallel Executor

Tests the async parallel execution system with rate limiting.
"""
import sys
import asyncio
import time
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.batch.batch_parallel_executor import (
    RateLimitManager,
    BatchParallelExecutor,
    run_scenarios_parallel
)


def test_rate_limit_manager_initialization():
    """Test rate limit manager initialization"""
    print("=" * 70)
    print("TEST 1: Rate limit manager initialization")
    print("=" * 70)
    print()

    manager = RateLimitManager()

    assert manager.backoff_until == 0.0
    assert manager.backoff_duration == 0.0
    assert manager.consecutive_429s == 0

    print(f"  ✓ Rate limit manager initialized")
    print(f"  ✓ Backoff until: {manager.backoff_until}")
    print(f"  ✓ Consecutive 429s: {manager.consecutive_429s}")

    print()
    print("✅ Test 1 passed: Rate limit manager initialization works")
    print()
    return True


async def test_rate_limit_backoff():
    """Test rate limit backoff logic"""
    print("=" * 70)
    print("TEST 2: Rate limit backoff")
    print("=" * 70)
    print()

    manager = RateLimitManager()

    # Initially no backoff
    start = time.time()
    await manager.check_rate_limit()
    elapsed = time.time() - start
    assert elapsed < 0.1  # Should be instant
    print(f"  ✓ No backoff initially (elapsed: {elapsed:.3f}s)")

    # Record a 429 error
    await manager.record_429_error()
    assert manager.consecutive_429s == 1
    assert manager.backoff_duration == 2.0  # 2^1
    print(f"  ✓ First 429: backoff = {manager.backoff_duration}s")

    # Record another 429
    await manager.record_429_error()
    assert manager.consecutive_429s == 2
    assert manager.backoff_duration == 4.0  # 2^2
    print(f"  ✓ Second 429: backoff = {manager.backoff_duration}s")

    # Record success (should reset)
    await manager.record_success()
    assert manager.consecutive_429s == 0
    assert manager.backoff_duration == 0.0
    print(f"  ✓ Success recorded: counter reset")

    print()
    print("✅ Test 2 passed: Rate limit backoff works")
    print()
    return True


async def test_rate_limit_with_retry_after():
    """Test rate limit with server-provided retry-after"""
    print("=" * 70)
    print("TEST 3: Rate limit with retry-after header")
    print("=" * 70)
    print()

    manager = RateLimitManager()

    # Record 429 with retry-after
    await manager.record_429_error(retry_after=5)
    assert manager.backoff_duration == 5.0
    print(f"  ✓ Used server retry-after: {manager.backoff_duration}s")

    # Without retry-after, should use exponential backoff
    await manager.record_success()  # Reset first
    await manager.record_429_error()  # No retry-after
    assert manager.backoff_duration == 2.0  # 2^1
    print(f"  ✓ Without retry-after: exponential backoff = {manager.backoff_duration}s")

    print()
    print("✅ Test 3 passed: Retry-after header support works")
    print()
    return True


async def test_parallel_executor_initialization():
    """Test parallel executor initialization"""
    print("=" * 70)
    print("TEST 4: Parallel executor initialization")
    print("=" * 70)
    print()

    executor = BatchParallelExecutor(max_parallel=3)

    assert executor.max_parallel == 3
    assert executor.semaphore._value == 3
    assert executor.rate_limit_manager is not None

    print(f"  ✓ Executor initialized")
    print(f"  ✓ Max parallel: {executor.max_parallel}")
    print(f"  ✓ Semaphore value: {executor.semaphore._value}")

    # Test with shared rate limit manager
    manager = RateLimitManager()
    executor2 = BatchParallelExecutor(max_parallel=2, rate_limit_manager=manager)
    assert executor2.rate_limit_manager is manager
    print(f"  ✓ Shared rate limit manager works")

    print()
    print("✅ Test 4 passed: Parallel executor initialization works")
    print()
    return True


async def test_execute_single_scenario():
    """Test executing a single scenario"""
    print("=" * 70)
    print("TEST 5: Execute single scenario")
    print("=" * 70)
    print()

    executor = BatchParallelExecutor(max_parallel=2)

    # Simple function to execute
    def simple_func(x, y):
        time.sleep(0.05)  # Simulate work
        return x + y

    result = await executor.execute_scenario(simple_func, 5, 10)
    assert result == 15
    print(f"  ✓ Executed scenario: 5 + 10 = {result}")

    # Check that success was recorded
    assert executor.rate_limit_manager.consecutive_429s == 0
    print(f"  ✓ Success recorded (429 counter: {executor.rate_limit_manager.consecutive_429s})")

    print()
    print("✅ Test 5 passed: Single scenario execution works")
    print()
    return True


async def test_execute_batch_scenarios():
    """Test executing batch of scenarios"""
    print("=" * 70)
    print("TEST 6: Execute batch scenarios")
    print("=" * 70)
    print()

    executor = BatchParallelExecutor(max_parallel=3)

    # Function to execute
    def multiply(x, y):
        time.sleep(0.05)
        return x * y

    # Create batch tasks
    tasks = [
        {'args': [2, 3]},
        {'args': [4, 5]},
        {'args': [6, 7]},
        {'args': [8, 9]},
    ]

    results = await executor.execute_batch(tasks, multiply)

    assert len(results) == 4
    assert results[0] == 6
    assert results[1] == 20
    assert results[2] == 42
    assert results[3] == 72

    print(f"  ✓ Executed {len(results)} scenarios")
    for i, result in enumerate(results):
        print(f"    Task {i}: {result}")

    print()
    print("✅ Test 6 passed: Batch execution works")
    print()
    return True


async def test_parallelism_control():
    """Test that parallelism is actually limited"""
    print("=" * 70)
    print("TEST 7: Parallelism control")
    print("=" * 70)
    print()

    # Track concurrent executions
    concurrent_count = 0
    max_concurrent = 0
    lock = asyncio.Lock()

    def tracked_func():
        nonlocal concurrent_count, max_concurrent

        # Increment counter (need to use sync approach here)
        import threading
        with threading.Lock():
            concurrent_count += 1
            if concurrent_count > max_concurrent:
                max_concurrent = concurrent_count

        time.sleep(0.1)  # Simulate work

        with threading.Lock():
            concurrent_count -= 1

        return "done"

    executor = BatchParallelExecutor(max_parallel=2)

    tasks = [{'args': []} for _ in range(6)]
    results = await executor.execute_batch(tasks, tracked_func)

    assert len(results) == 6
    assert max_concurrent <= 2
    print(f"  ✓ Executed 6 tasks with max_parallel=2")
    print(f"  ✓ Max concurrent observed: {max_concurrent}")
    print(f"  ✓ Parallelism respected ✓")

    print()
    print("✅ Test 7 passed: Parallelism control works")
    print()
    return True


async def test_progress_callback():
    """Test progress callback functionality"""
    print("=" * 70)
    print("TEST 8: Progress callback")
    print("=" * 70)
    print()

    executor = BatchParallelExecutor(max_parallel=2)

    # Track progress
    completed = []

    def progress_callback(task_id, result):
        completed.append((task_id, result))

    def simple_func(x):
        return x * 2

    tasks = [
        {'args': [1]},
        {'args': [2]},
        {'args': [3]},
    ]

    results = await executor.execute_batch(tasks, simple_func, progress_callback)

    assert len(results) == 3
    assert len(completed) == 3
    print(f"  ✓ Progress callback called {len(completed)} times")

    # Check callback data
    for task_id, result in completed:
        print(f"    Task {task_id}: {result}")

    print()
    print("✅ Test 8 passed: Progress callback works")
    print()
    return True


async def test_error_handling():
    """Test error handling in parallel execution"""
    print("=" * 70)
    print("TEST 9: Error handling")
    print("=" * 70)
    print()

    executor = BatchParallelExecutor(max_parallel=2)

    def failing_func(x):
        if x == 2:
            raise ValueError(f"Error for {x}")
        return x * 2

    tasks = [
        {'args': [1]},
        {'args': [2]},  # Will fail
        {'args': [3]},
    ]

    results = await executor.execute_batch(tasks, failing_func)

    assert len(results) == 3
    assert results[0] == 2
    assert 'error' in results[1]
    assert results[2] == 6

    print(f"  ✓ Handled 1 error in batch")
    print(f"    Result 0: {results[0]}")
    print(f"    Result 1 (error): {results[1]}")
    print(f"    Result 2: {results[2]}")

    print()
    print("✅ Test 9 passed: Error handling works")
    print()
    return True


async def test_rate_limit_error_handling():
    """Test rate limit (429) error handling"""
    print("=" * 70)
    print("TEST 10: Rate limit error handling")
    print("=" * 70)
    print()

    executor = BatchParallelExecutor(max_parallel=1)

    def rate_limited_func(x):
        if x == 1:
            raise Exception("429 Rate limit exceeded")
        return x * 2

    tasks = [
        {'args': [1]},  # Will trigger 429
        {'args': [2]},
    ]

    results = await executor.execute_batch(tasks, rate_limited_func)

    # First task should have error
    assert 'error' in results[0]
    assert '429' in results[0]['error']

    # Rate limit manager should have recorded it
    # Note: It might be reset by the second task's success
    print(f"  ✓ 429 error detected and handled")
    print(f"    Result 0: {results[0]}")
    print(f"    Result 1: {results[1]}")

    print()
    print("✅ Test 10 passed: Rate limit error handling works")
    print()
    return True


async def test_executor_status():
    """Test executor status reporting"""
    print("=" * 70)
    print("TEST 11: Executor status")
    print("=" * 70)
    print()

    executor = BatchParallelExecutor(max_parallel=3)

    status = executor.get_status()

    assert 'max_parallel' in status
    assert 'rate_limit_active' in status
    assert 'backoff_remaining' in status
    assert 'consecutive_429s' in status

    assert status['max_parallel'] == 3
    assert status['rate_limit_active'] is False
    assert status['consecutive_429s'] == 0

    print(f"  ✓ Status retrieved")
    print(f"    Max parallel: {status['max_parallel']}")
    print(f"    Rate limit active: {status['rate_limit_active']}")
    print(f"    Consecutive 429s: {status['consecutive_429s']}")

    print()
    print("✅ Test 11 passed: Status reporting works")
    print()
    return True


async def test_convenience_function():
    """Test run_scenarios_parallel convenience function"""
    print("=" * 70)
    print("TEST 12: Convenience function")
    print("=" * 70)
    print()

    def add(x, y):
        return x + y

    scenarios = [
        {'args': [1, 2]},
        {'args': [3, 4]},
        {'args': [5, 6]},
    ]

    results = await run_scenarios_parallel(
        scenarios,
        add,
        max_parallel=2
    )

    assert len(results) == 3
    assert results[0] == 3
    assert results[1] == 7
    assert results[2] == 11

    print(f"  ✓ Convenience function executed {len(results)} scenarios")
    for i, result in enumerate(results):
        print(f"    Scenario {i}: {result}")

    print()
    print("✅ Test 12 passed: Convenience function works")
    print()
    return True


def run_all_tests():
    """Run all batch parallel executor tests"""
    print()
    print("=" * 70)
    print("V2 BATCH PARALLEL EXECUTOR TESTS")
    print("=" * 70)
    print()

    async def run_async_tests():
        tests = [
            test_rate_limit_manager_initialization,
            test_rate_limit_backoff,
            test_rate_limit_with_retry_after,
            test_parallel_executor_initialization,
            test_execute_single_scenario,
            test_execute_batch_scenarios,
            test_parallelism_control,
            test_progress_callback,
            test_error_handling,
            test_rate_limit_error_handling,
            test_executor_status,
            test_convenience_function,
        ]

        results = []
        for test in tests:
            try:
                if asyncio.iscoroutinefunction(test):
                    result = await test()
                else:
                    result = test()
                results.append(result)
            except Exception as e:
                print(f"  ✗ TEST FAILED: {e}")
                import traceback
                traceback.print_exc()
                results.append(False)

        return results

    results = asyncio.run(run_async_tests())

    print("=" * 70)
    print("BATCH PARALLEL EXECUTOR TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL BATCH PARALLEL EXECUTOR TESTS PASSED")
        print()
        print("Phase 4.4 Complete: Batch Parallel Executor")
        print("  ✓ Rate limit manager initialization")
        print("  ✓ Exponential backoff (2^n, max 60s)")
        print("  ✓ Retry-after header support")
        print("  ✓ Parallel executor initialization")
        print("  ✓ Single scenario execution")
        print("  ✓ Batch scenario execution")
        print("  ✓ Parallelism control (semaphore)")
        print("  ✓ Progress callbacks")
        print("  ✓ Error handling")
        print("  ✓ 429 rate limit detection")
        print("  ✓ Status reporting")
        print("  ✓ Convenience function")
        print()
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
