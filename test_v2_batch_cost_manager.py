#!/usr/bin/env python3
"""
Test V2 Batch Cost Manager

Tests the batch cost management system for budget enforcement and tracking.
"""
import sys
import tempfile
from pathlib import Path
import json
from datetime import datetime

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.batch.batch_cost_manager import BatchCostManager


def test_basic_cost_tracking():
    """Test basic cost tracking without limits"""
    print("=" * 70)
    print("TEST 1: Basic cost tracking")
    print("=" * 70)
    print()

    manager = BatchCostManager()

    # Record some runs
    manager.record_run_cost('run-001', variation_id=1, cost=1.50, success=True)
    manager.record_run_cost('run-002', variation_id=1, cost=1.75, success=True)
    manager.record_run_cost('run-003', variation_id=2, cost=2.00, success=True)

    assert manager.total_spent == 1.50 + 1.75 + 2.00
    assert manager.runs_completed == 3
    assert manager.runs_failed == 0

    print(f"  ✓ Recorded 3 successful runs")
    print(f"  ✓ Total spent: ${manager.total_spent:.2f}")
    print(f"  ✓ Runs completed: {manager.runs_completed}")

    # Check average cost
    avg_cost = manager.get_average_cost_per_run()
    assert avg_cost is not None
    expected_avg = (1.50 + 1.75 + 2.00) / 3
    assert abs(avg_cost - expected_avg) < 0.01

    print(f"  ✓ Average cost per run: ${avg_cost:.2f}")

    print()
    print("✅ Test 1 passed: Basic cost tracking works")
    print()
    return True


def test_budget_limit_enforcement():
    """Test budget limit enforcement"""
    print("=" * 70)
    print("TEST 2: Budget limit enforcement")
    print("=" * 70)
    print()

    manager = BatchCostManager(budget_limit=10.0)

    # Check we can start initially
    can_start, reason = manager.can_start_run()
    assert can_start is True
    assert reason is None
    print(f"  ✓ Can start run initially (budget: ${manager.budget_limit:.2f})")

    # Spend close to limit
    manager.record_run_cost('run-001', variation_id=1, cost=9.50, success=True)
    assert manager.total_spent == 9.50
    print(f"  ✓ Spent ${manager.total_spent:.2f} / ${manager.budget_limit:.2f}")

    # Should not be able to start if remaining < cost_per_run_limit
    manager.cost_per_run_limit = 1.00
    can_start, reason = manager.can_start_run()
    assert can_start is False
    assert "Insufficient budget" in reason
    print(f"  ✓ Cannot start (insufficient remaining budget)")
    print(f"    Reason: {reason}")

    # Exceed limit
    manager2 = BatchCostManager(budget_limit=5.0)
    manager2.record_run_cost('run-001', variation_id=1, cost=6.0, success=True)

    can_start, reason = manager2.can_start_run()
    assert can_start is False
    assert "Budget limit reached" in reason
    print(f"  ✓ Cannot start (budget limit reached)")

    print()
    print("✅ Test 2 passed: Budget limit enforcement works")
    print()
    return True


def test_per_run_cost_limit():
    """Test per-run cost limit checking"""
    print("=" * 70)
    print("TEST 3: Per-run cost limit")
    print("=" * 70)
    print()

    manager = BatchCostManager(cost_per_run_limit=5.0)

    # Check cost within limit
    within_limit, reason = manager.check_run_cost(4.50)
    assert within_limit is True
    assert reason is None
    print(f"  ✓ Cost $4.50 within limit ($5.00)")

    # Check cost exceeding limit
    within_limit, reason = manager.check_run_cost(6.00)
    assert within_limit is False
    assert "exceeds limit" in reason
    assert manager.runs_budget_exceeded == 1
    print(f"  ✓ Cost $6.00 exceeds limit ($5.00)")
    print(f"    Reason: {reason}")
    print(f"  ✓ Budget exceeded count: {manager.runs_budget_exceeded}")

    print()
    print("✅ Test 3 passed: Per-run cost limit works")
    print()
    return True


def test_failed_run_tracking():
    """Test tracking of failed runs"""
    print("=" * 70)
    print("TEST 4: Failed run tracking")
    print("=" * 70)
    print()

    manager = BatchCostManager()

    manager.record_run_cost('run-001', variation_id=1, cost=2.0, success=True)
    manager.record_run_cost('run-002', variation_id=1, cost=1.5, success=False)
    manager.record_run_cost('run-003', variation_id=1, cost=2.5, success=True)

    assert manager.runs_completed == 2
    assert manager.runs_failed == 1
    assert manager.total_spent == 2.0 + 1.5 + 2.5

    print(f"  ✓ Total spent: ${manager.total_spent:.2f} (includes failed runs)")
    print(f"  ✓ Successful runs: {manager.runs_completed}")
    print(f"  ✓ Failed runs: {manager.runs_failed}")

    print()
    print("✅ Test 4 passed: Failed run tracking works")
    print()
    return True


def test_remaining_budget_calculation():
    """Test remaining budget calculation"""
    print("=" * 70)
    print("TEST 5: Remaining budget calculation")
    print("=" * 70)
    print()

    manager = BatchCostManager(budget_limit=20.0)

    # Initially full budget
    remaining = manager.get_remaining_budget()
    assert remaining == 20.0
    print(f"  ✓ Initial remaining budget: ${remaining:.2f}")

    # After some spending
    manager.record_run_cost('run-001', variation_id=1, cost=7.5, success=True)
    remaining = manager.get_remaining_budget()
    assert remaining == 12.5
    print(f"  ✓ After spending $7.50: ${remaining:.2f} remaining")

    # No limit case
    manager_no_limit = BatchCostManager()
    remaining = manager_no_limit.get_remaining_budget()
    assert remaining is None
    print(f"  ✓ No budget limit: remaining = None")

    print()
    print("✅ Test 5 passed: Remaining budget calculation works")
    print()
    return True


def test_runs_remaining_estimation():
    """Test estimation of remaining runs"""
    print("=" * 70)
    print("TEST 6: Runs remaining estimation")
    print("=" * 70)
    print()

    # Test with cost_per_run_limit
    manager = BatchCostManager(budget_limit=20.0, cost_per_run_limit=2.5)
    estimate = manager.estimate_runs_remaining()
    assert estimate == 8  # 20.0 / 2.5 = 8
    print(f"  ✓ With cost_per_run_limit: {estimate} runs remaining")

    # After some spending
    manager.record_run_cost('run-001', variation_id=1, cost=2.5, success=True)
    estimate = manager.estimate_runs_remaining()
    assert estimate == 7  # 17.5 / 2.5 = 7
    print(f"  ✓ After 1 run: {estimate} runs remaining")

    # Test with average cost estimation
    manager2 = BatchCostManager(budget_limit=20.0)
    manager2.record_run_cost('run-001', variation_id=1, cost=3.0, success=True)
    manager2.record_run_cost('run-002', variation_id=1, cost=2.0, success=True)
    # Average: 2.5, remaining: 15.0, estimate: 6
    estimate = manager2.estimate_runs_remaining()
    assert estimate == 6
    print(f"  ✓ With average cost: {estimate} runs remaining")

    # No limit case
    manager_no_limit = BatchCostManager()
    estimate = manager_no_limit.estimate_runs_remaining()
    assert estimate is None
    print(f"  ✓ No budget limit: estimate = None")

    print()
    print("✅ Test 6 passed: Runs remaining estimation works")
    print()
    return True


def test_variation_statistics():
    """Test per-variation cost statistics"""
    print("=" * 70)
    print("TEST 7: Variation statistics")
    print("=" * 70)
    print()

    manager = BatchCostManager()

    # Record runs for different variations
    manager.record_run_cost('run-001', variation_id=1, cost=1.0, success=True)
    manager.record_run_cost('run-002', variation_id=1, cost=1.5, success=True)
    manager.record_run_cost('run-003', variation_id=2, cost=2.0, success=True)
    manager.record_run_cost('run-004', variation_id=2, cost=2.5, success=False)
    manager.record_run_cost('run-005', variation_id=3, cost=3.0, success=True)

    stats = manager.get_variation_statistics()

    assert 1 in stats
    assert 2 in stats
    assert 3 in stats

    # Check variation 1
    assert stats[1]['num_runs'] == 2
    assert stats[1]['successful_runs'] == 2
    assert stats[1]['total_cost'] == 2.5
    assert stats[1]['avg_cost_per_run'] == 1.25

    print(f"  ✓ Variation 1: {stats[1]['num_runs']} runs, ${stats[1]['total_cost']:.2f} total")

    # Check variation 2
    assert stats[2]['num_runs'] == 2
    assert stats[2]['successful_runs'] == 1  # One failed
    assert stats[2]['total_cost'] == 4.5
    assert stats[2]['avg_cost_per_run'] == 2.25

    print(f"  ✓ Variation 2: {stats[2]['num_runs']} runs, {stats[2]['successful_runs']} successful")

    # Check variation 3
    assert stats[3]['num_runs'] == 1
    assert stats[3]['total_cost'] == 3.0

    print(f"  ✓ Variation 3: {stats[3]['num_runs']} run, ${stats[3]['total_cost']:.2f} total")

    print()
    print("✅ Test 7 passed: Variation statistics work")
    print()
    return True


def test_batch_timing():
    """Test batch timing tracking"""
    print("=" * 70)
    print("TEST 8: Batch timing")
    print("=" * 70)
    print()

    manager = BatchCostManager()

    # Start batch
    manager.start_batch()
    assert manager.start_time is not None
    print(f"  ✓ Batch started at: {manager.start_time.isoformat()}")

    # End batch
    manager.end_batch()
    assert manager.end_time is not None
    print(f"  ✓ Batch ended at: {manager.end_time.isoformat()}")

    # Check duration in summary
    summary = manager.get_summary()
    assert summary['duration_seconds'] is not None
    assert summary['duration_seconds'] >= 0
    print(f"  ✓ Batch duration: {summary['duration_seconds']:.3f} seconds")

    print()
    print("✅ Test 8 passed: Batch timing works")
    print()
    return True


def test_summary_generation():
    """Test summary generation"""
    print("=" * 70)
    print("TEST 9: Summary generation")
    print("=" * 70)
    print()

    manager = BatchCostManager(budget_limit=50.0, cost_per_run_limit=5.0)
    manager.start_batch()

    manager.record_run_cost('run-001', variation_id=1, cost=4.0, success=True)
    manager.record_run_cost('run-002', variation_id=1, cost=3.5, success=True)
    manager.record_run_cost('run-003', variation_id=2, cost=6.0, success=True)  # Exceeds per-run limit

    manager.check_run_cost(6.0)  # Trigger budget exceeded counter
    manager.end_batch()

    summary = manager.get_summary()

    assert summary['total_spent'] == 13.5
    assert summary['budget_limit'] == 50.0
    assert summary['cost_per_run_limit'] == 5.0
    assert summary['remaining_budget'] == 36.5
    assert summary['runs_completed'] == 3
    assert summary['runs_failed'] == 0
    assert summary['runs_budget_exceeded'] == 1
    assert summary['avg_cost_per_run'] is not None
    assert summary['duration_seconds'] is not None

    print(f"  ✓ Total spent: ${summary['total_spent']:.2f}")
    print(f"  ✓ Remaining budget: ${summary['remaining_budget']:.2f}")
    print(f"  ✓ Runs completed: {summary['runs_completed']}")
    print(f"  ✓ Runs budget exceeded: {summary['runs_budget_exceeded']}")
    print(f"  ✓ Average cost per run: ${summary['avg_cost_per_run']:.2f}")

    print()
    print("✅ Test 9 passed: Summary generation works")
    print()
    return True


def test_save_and_load():
    """Test save/load functionality"""
    print("=" * 70)
    print("TEST 10: Save and load")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'batch_costs.json'

        # Create and populate manager
        manager1 = BatchCostManager(budget_limit=100.0, cost_per_run_limit=10.0)
        manager1.start_batch()
        manager1.record_run_cost('run-001', variation_id=1, cost=5.0, success=True)
        manager1.record_run_cost('run-002', variation_id=2, cost=7.5, success=True)
        manager1.end_batch()

        # Save
        manager1.save_to_file(str(output_path))
        assert output_path.exists()
        print(f"  ✓ Saved to {output_path}")

        # Verify JSON structure
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'summary' in data
        assert 'run_costs' in data
        assert 'variation_statistics' in data
        print(f"  ✓ JSON structure valid")

        # Load into new manager
        manager2 = BatchCostManager(budget_limit=100.0, cost_per_run_limit=10.0)
        manager2.load_from_file(str(output_path))

        # Verify loaded data
        assert manager2.total_spent == 12.5
        assert manager2.runs_completed == 2
        assert len(manager2.run_costs) == 2
        assert 1 in manager2.variation_costs
        assert 2 in manager2.variation_costs
        assert manager2.start_time is not None

        print(f"  ✓ Loaded data matches:")
        print(f"    - Total spent: ${manager2.total_spent:.2f}")
        print(f"    - Runs completed: {manager2.runs_completed}")
        print(f"    - Variations: {list(manager2.variation_costs.keys())}")

    print()
    print("✅ Test 10 passed: Save and load work correctly")
    print()
    return True


def run_all_tests():
    """Run all batch cost manager tests"""
    print()
    print("=" * 70)
    print("V2 BATCH COST MANAGER TESTS")
    print("=" * 70)
    print()

    tests = [
        test_basic_cost_tracking,
        test_budget_limit_enforcement,
        test_per_run_cost_limit,
        test_failed_run_tracking,
        test_remaining_budget_calculation,
        test_runs_remaining_estimation,
        test_variation_statistics,
        test_batch_timing,
        test_summary_generation,
        test_save_and_load,
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
    print("BATCH COST MANAGER TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL BATCH COST MANAGER TESTS PASSED")
        print()
        print("Phase 4.2 Complete: Batch Cost Manager")
        print("  ✓ Basic cost tracking")
        print("  ✓ Budget limit enforcement")
        print("  ✓ Per-run cost limits")
        print("  ✓ Failed run tracking")
        print("  ✓ Remaining budget calculation")
        print("  ✓ Runs remaining estimation")
        print("  ✓ Per-variation statistics")
        print("  ✓ Batch timing (start/end)")
        print("  ✓ Summary generation")
        print("  ✓ Save/load to JSON")
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
