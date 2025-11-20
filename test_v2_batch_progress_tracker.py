#!/usr/bin/env python3
"""
Test V2 Batch Progress Tracker

Tests the batch progress tracking system for real-time display.
"""
import sys
import time
from pathlib import Path
from io import StringIO

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.batch.batch_progress_tracker import (
    BatchProgressTracker, SimpleProgressTracker
)


def test_basic_initialization():
    """Test basic tracker initialization"""
    print("=" * 70)
    print("TEST 1: Basic initialization")
    print("=" * 70)
    print()

    tracker = BatchProgressTracker(
        total_runs=10,
        experiment_name="Test Experiment",
        budget_limit=50.0
    )

    assert tracker.total_runs == 10
    assert tracker.experiment_name == "Test Experiment"
    assert tracker.budget_limit == 50.0
    assert tracker.completed_runs == 0
    assert tracker.failed_runs == 0
    assert tracker.total_cost == 0.0

    print(f"  ✓ Initialized tracker")
    print(f"  ✓ Total runs: {tracker.total_runs}")
    print(f"  ✓ Experiment: {tracker.experiment_name}")
    print(f"  ✓ Budget limit: ${tracker.budget_limit:.2f}")

    print()
    print("✅ Test 1 passed: Basic initialization works")
    print()
    return True


def test_run_completion_tracking():
    """Test tracking run completions"""
    print("=" * 70)
    print("TEST 2: Run completion tracking")
    print("=" * 70)
    print()

    tracker = BatchProgressTracker(
        total_runs=5,
        experiment_name="Test",
        use_rich=False  # Use simple mode for testing
    )

    # Track successful runs
    tracker.update_run_started("run-001", "Variation 1")
    assert tracker.current_run_id == "run-001"
    print(f"  ✓ Run started: {tracker.current_run_id}")

    tracker.update_run_completed("run-001", cost=2.5, success=True)
    assert tracker.completed_runs == 1
    assert tracker.failed_runs == 0
    assert tracker.total_cost == 2.5
    assert tracker.current_run_id is None
    print(f"  ✓ Run completed successfully")
    print(f"    - Completed runs: {tracker.completed_runs}")
    print(f"    - Total cost: ${tracker.total_cost:.2f}")

    # Track failed run
    tracker.update_run_started("run-002", "Variation 2")
    tracker.update_run_completed("run-002", cost=1.5, success=False)
    assert tracker.completed_runs == 1
    assert tracker.failed_runs == 1
    assert tracker.total_cost == 4.0
    print(f"  ✓ Run failed")
    print(f"    - Failed runs: {tracker.failed_runs}")
    print(f"    - Total cost: ${tracker.total_cost:.2f}")

    print()
    print("✅ Test 2 passed: Run completion tracking works")
    print()
    return True


def test_cost_updates():
    """Test cost update functionality"""
    print("=" * 70)
    print("TEST 3: Cost updates")
    print("=" * 70)
    print()

    tracker = BatchProgressTracker(
        total_runs=3,
        experiment_name="Cost Test",
        use_rich=False
    )

    initial_cost = tracker.total_cost
    tracker.update_cost(5.0)
    assert tracker.total_cost == 5.0
    print(f"  ✓ Updated cost: ${tracker.total_cost:.2f}")

    tracker.update_cost(3.5)
    assert tracker.total_cost == 8.5
    print(f"  ✓ Updated cost again: ${tracker.total_cost:.2f}")

    print()
    print("✅ Test 3 passed: Cost updates work")
    print()
    return True


def test_time_estimation():
    """Test time remaining estimation"""
    print("=" * 70)
    print("TEST 4: Time remaining estimation")
    print("=" * 70)
    print()

    tracker = BatchProgressTracker(
        total_runs=10,
        experiment_name="Time Test",
        use_rich=False
    )

    # No estimate before starting
    estimate = tracker.get_estimated_time_remaining()
    assert estimate is None
    print(f"  ✓ No estimate before starting: {estimate}")

    # Start and complete some runs
    tracker.start()
    time.sleep(0.1)  # Simulate some time passing

    tracker.update_run_completed("run-001", cost=1.0, success=True)
    time.sleep(0.1)
    tracker.update_run_completed("run-002", cost=1.0, success=True)

    # Should have an estimate now
    estimate = tracker.get_estimated_time_remaining()
    assert estimate is not None
    assert estimate > 0
    print(f"  ✓ Time estimate after 2 runs: {estimate:.2f} seconds")
    print(f"    (for remaining {tracker.total_runs - 2} runs)")

    print()
    print("✅ Test 4 passed: Time estimation works")
    print()
    return True


def test_start_stop_lifecycle():
    """Test tracker lifecycle (start/stop)"""
    print("=" * 70)
    print("TEST 5: Tracker lifecycle")
    print("=" * 70)
    print()

    # Suppress output during test
    original_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        tracker = BatchProgressTracker(
            total_runs=3,
            experiment_name="Lifecycle Test",
            use_rich=False
        )

        # Start tracker
        tracker.start()
        assert tracker.start_time is not None

        # Complete some runs
        tracker.update_run_completed("run-001", cost=1.0, success=True)
        tracker.update_run_completed("run-002", cost=1.5, success=True)

        # Stop tracker (prints summary)
        tracker.stop()

        sys.stdout = original_stdout

        print(f"  ✓ Tracker started")
        print(f"  ✓ Completed 2 runs")
        print(f"  ✓ Tracker stopped and summary printed")

    finally:
        sys.stdout = original_stdout

    print()
    print("✅ Test 5 passed: Lifecycle works correctly")
    print()
    return True


def test_simple_progress_tracker():
    """Test SimpleProgressTracker wrapper"""
    print("=" * 70)
    print("TEST 6: SimpleProgressTracker wrapper")
    print("=" * 70)
    print()

    tracker = SimpleProgressTracker(
        total_runs=5,
        experiment_name="Simple Test",
        budget_limit=25.0
    )

    # Should work like BatchProgressTracker
    assert tracker.total_runs == 5
    assert tracker.experiment_name == "Simple Test"
    assert tracker.budget_limit == 25.0

    print(f"  ✓ SimpleProgressTracker created")
    print(f"  ✓ Total runs: {tracker.total_runs}")
    print(f"  ✓ Budget: ${tracker.budget_limit:.2f}")

    # Test that it delegates properly
    tracker.update_run_completed("run-001", cost=5.0, success=True)
    assert tracker.completed_runs == 1
    assert tracker.total_cost == 5.0

    print(f"  ✓ Delegation works")
    print(f"    - Completed: {tracker.completed_runs}")
    print(f"    - Cost: ${tracker.total_cost:.2f}")

    print()
    print("✅ Test 6 passed: SimpleProgressTracker works")
    print()
    return True


def test_statistics_calculation():
    """Test statistics calculations"""
    print("=" * 70)
    print("TEST 7: Statistics calculations")
    print("=" * 70)
    print()

    tracker = BatchProgressTracker(
        total_runs=10,
        experiment_name="Stats Test",
        budget_limit=100.0,
        use_rich=False
    )

    # Complete several runs
    tracker.update_run_completed("run-001", cost=5.0, success=True)
    tracker.update_run_completed("run-002", cost=7.5, success=True)
    tracker.update_run_completed("run-003", cost=3.0, success=False)
    tracker.update_run_completed("run-004", cost=6.0, success=True)

    # Check statistics
    total_finished = tracker.completed_runs + tracker.failed_runs
    assert total_finished == 4
    print(f"  ✓ Total finished: {total_finished}")

    success_rate = (tracker.completed_runs / total_finished * 100)
    assert success_rate == 75.0  # 3 successful out of 4
    print(f"  ✓ Success rate: {success_rate:.1f}%")

    # Average cost uses total_cost / completed_runs
    # Note: total_cost includes both successful and failed runs
    avg_cost = tracker.total_cost / tracker.completed_runs
    expected_avg = (5.0 + 7.5 + 3.0 + 6.0) / 3  # Total cost / successful runs
    assert abs(avg_cost - expected_avg) < 0.01
    print(f"  ✓ Average cost per successful run: ${avg_cost:.2f}")

    # Budget tracking
    remaining = tracker.budget_limit - tracker.total_cost
    assert remaining == 100.0 - 21.5
    print(f"  ✓ Remaining budget: ${remaining:.2f}")

    print()
    print("✅ Test 7 passed: Statistics calculations work")
    print()
    return True


def test_budget_monitoring():
    """Test budget monitoring features"""
    print("=" * 70)
    print("TEST 8: Budget monitoring")
    print("=" * 70)
    print()

    tracker = BatchProgressTracker(
        total_runs=5,
        experiment_name="Budget Test",
        budget_limit=20.0,
        use_rich=False
    )

    # Spend some budget
    tracker.update_run_completed("run-001", cost=8.0, success=True)
    remaining = tracker.budget_limit - tracker.total_cost
    assert remaining == 12.0
    print(f"  ✓ After $8.00 spend: ${remaining:.2f} remaining")

    tracker.update_run_completed("run-002", cost=7.0, success=True)
    remaining = tracker.budget_limit - tracker.total_cost
    assert remaining == 5.0
    print(f"  ✓ After $7.00 spend: ${remaining:.2f} remaining")

    # Calculate budget percentage
    budget_pct = (tracker.total_cost / tracker.budget_limit * 100)
    assert budget_pct == 75.0
    print(f"  ✓ Budget used: {budget_pct:.1f}%")

    print()
    print("✅ Test 8 passed: Budget monitoring works")
    print()
    return True


def test_no_budget_limit():
    """Test tracker without budget limit"""
    print("=" * 70)
    print("TEST 9: No budget limit")
    print("=" * 70)
    print()

    tracker = BatchProgressTracker(
        total_runs=3,
        experiment_name="No Limit Test",
        budget_limit=None,  # No limit
        use_rich=False
    )

    assert tracker.budget_limit is None
    print(f"  ✓ Budget limit: {tracker.budget_limit}")

    # Should still track costs
    tracker.update_run_completed("run-001", cost=10.0, success=True)
    tracker.update_run_completed("run-002", cost=15.0, success=True)

    assert tracker.total_cost == 25.0
    print(f"  ✓ Total cost tracked: ${tracker.total_cost:.2f}")
    print(f"  ✓ No budget constraints applied")

    print()
    print("✅ Test 9 passed: No budget limit works")
    print()
    return True


def test_current_run_status():
    """Test current run status tracking"""
    print("=" * 70)
    print("TEST 10: Current run status")
    print("=" * 70)
    print()

    tracker = BatchProgressTracker(
        total_runs=3,
        experiment_name="Status Test",
        use_rich=False
    )

    # Initially idle
    assert tracker.current_run_id is None
    assert tracker.current_run_status == "Initializing"
    print(f"  ✓ Initial status: {tracker.current_run_status}")

    # Start a run
    tracker.update_run_started("run-001", "Test variation 1")
    assert tracker.current_run_id == "run-001"
    assert "Test variation 1" in tracker.current_run_status
    print(f"  ✓ Run started: {tracker.current_run_id}")
    print(f"    Status: {tracker.current_run_status}")

    # Complete the run
    tracker.update_run_completed("run-001", cost=2.0, success=True)
    assert tracker.current_run_id is None
    assert tracker.current_run_status == "Idle"
    print(f"  ✓ After completion: {tracker.current_run_status}")

    print()
    print("✅ Test 10 passed: Current run status works")
    print()
    return True


def run_all_tests():
    """Run all batch progress tracker tests"""
    print()
    print("=" * 70)
    print("V2 BATCH PROGRESS TRACKER TESTS")
    print("=" * 70)
    print()

    tests = [
        test_basic_initialization,
        test_run_completion_tracking,
        test_cost_updates,
        test_time_estimation,
        test_start_stop_lifecycle,
        test_simple_progress_tracker,
        test_statistics_calculation,
        test_budget_monitoring,
        test_no_budget_limit,
        test_current_run_status,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("=" * 70)
    print("BATCH PROGRESS TRACKER TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL BATCH PROGRESS TRACKER TESTS PASSED")
        print()
        print("Phase 4.3 Complete: Batch Progress Tracker")
        print("  ✓ Basic initialization")
        print("  ✓ Run completion tracking (success/failure)")
        print("  ✓ Cost updates and tracking")
        print("  ✓ Time remaining estimation")
        print("  ✓ Start/stop lifecycle")
        print("  ✓ SimpleProgressTracker wrapper")
        print("  ✓ Statistics calculations")
        print("  ✓ Budget monitoring")
        print("  ✓ Optional budget limits")
        print("  ✓ Current run status tracking")
        print()
        print("Note: Rich library support is optional and degrades gracefully")
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
