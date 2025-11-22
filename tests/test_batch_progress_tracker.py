"""
Tests for Batch Progress Tracker module

Tests progress tracking, display functionality, and fallback behavior.
"""
import pytest
import time
from unittest.mock import patch, MagicMock

from scenario_lab.batch.batch_progress_tracker import (
    BatchProgressTracker,
    SimpleProgressTracker,
    RICH_AVAILABLE,
)


class TestBatchProgressTrackerInit:
    """Tests for BatchProgressTracker initialization"""

    def test_init_basic(self):
        """Test basic initialization"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test Experiment"
        )

        assert tracker.total_runs == 10
        assert tracker.experiment_name == "Test Experiment"
        assert tracker.budget_limit is None
        assert tracker.completed_runs == 0
        assert tracker.failed_runs == 0
        assert tracker.total_cost == 0.0
        assert tracker.start_time is None

    def test_init_with_budget(self):
        """Test initialization with budget limit"""
        tracker = BatchProgressTracker(
            total_runs=20,
            experiment_name="Budget Test",
            budget_limit=100.0
        )

        assert tracker.budget_limit == 100.0

    def test_init_use_rich_flag(self):
        """Test use_rich flag configuration"""
        tracker_no_rich = BatchProgressTracker(
            total_runs=5,
            experiment_name="No Rich",
            use_rich=False
        )

        assert tracker_no_rich.use_rich is False

        tracker_with_rich = BatchProgressTracker(
            total_runs=5,
            experiment_name="With Rich",
            use_rich=True
        )

        # use_rich is True only if RICH_AVAILABLE is also True
        assert tracker_with_rich.use_rich == RICH_AVAILABLE


class TestBatchProgressTrackerStart:
    """Tests for start() method"""

    def test_start_sets_start_time(self):
        """Test that start() sets start time"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        tracker.start()

        assert tracker.start_time is not None
        assert tracker.start_time <= time.time()

    @patch('builtins.print')
    def test_start_prints_header_without_rich(self, mock_print):
        """Test that start() prints header when rich is disabled"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Header Test",
            use_rich=False
        )

        tracker.start()

        # Should have printed experiment info
        assert mock_print.called
        printed = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Header Test" in printed
        assert "10" in printed

    @patch('builtins.print')
    def test_start_prints_budget_without_rich(self, mock_print):
        """Test that start() prints budget when set and rich is disabled"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Budget Header Test",
            budget_limit=50.0,
            use_rich=False
        )

        tracker.start()

        printed = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "50.00" in printed


class TestBatchProgressTrackerStop:
    """Tests for stop() method"""

    @patch('builtins.print')
    def test_stop_prints_summary_without_rich(self, mock_print):
        """Test that stop() prints summary when rich is disabled"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Summary Test",
            use_rich=False
        )

        tracker.start()
        tracker.completed_runs = 8
        tracker.failed_runs = 2
        tracker.total_cost = 5.50
        tracker.stop()

        printed = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "Summary" in printed
        assert "8" in printed
        assert "2" in printed


class TestBatchProgressTrackerUpdateRunStarted:
    """Tests for update_run_started() method"""

    def test_update_run_started_sets_current_run(self):
        """Test that update_run_started() sets current run info"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        tracker.update_run_started("var-001-run-001", "Model: GPT-4")

        assert tracker.current_run_id == "var-001-run-001"
        assert "Model: GPT-4" in tracker.current_run_status

    @patch('builtins.print')
    def test_update_run_started_prints_without_rich(self, mock_print):
        """Test that update_run_started() prints when rich is disabled"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        tracker.update_run_started("var-001-run-001", "Model: GPT-4")

        printed = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "var-001-run-001" in printed
        assert "GPT-4" in printed


class TestBatchProgressTrackerUpdateRunCompleted:
    """Tests for update_run_completed() method"""

    def test_update_run_completed_success(self):
        """Test update_run_completed() with successful run"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        tracker.update_run_completed("var-001-run-001", cost=0.25, success=True)

        assert tracker.completed_runs == 1
        assert tracker.failed_runs == 0
        assert tracker.total_cost == 0.25
        assert tracker.current_run_id is None

    def test_update_run_completed_failure(self):
        """Test update_run_completed() with failed run"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        tracker.update_run_completed("var-001-run-001", cost=0.15, success=False)

        assert tracker.completed_runs == 0
        assert tracker.failed_runs == 1
        assert tracker.total_cost == 0.15

    def test_update_run_completed_accumulates_cost(self):
        """Test that update_run_completed() accumulates cost"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        tracker.update_run_completed("run-1", cost=0.10, success=True)
        tracker.update_run_completed("run-2", cost=0.15, success=True)
        tracker.update_run_completed("run-3", cost=0.20, success=True)

        assert tracker.total_cost == pytest.approx(0.45, rel=0.01)
        assert tracker.completed_runs == 3

    @patch('builtins.print')
    def test_update_run_completed_prints_status_without_rich(self, mock_print):
        """Test that update_run_completed() prints status when rich is disabled"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        tracker.update_run_completed("var-001-run-001", cost=0.25, success=True)

        printed = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "var-001-run-001" in printed
        assert "0.25" in printed


class TestBatchProgressTrackerUpdateCost:
    """Tests for update_cost() method"""

    def test_update_cost(self):
        """Test update_cost() adds to total"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        tracker.update_cost(0.50)
        assert tracker.total_cost == 0.50

        tracker.update_cost(0.25)
        assert tracker.total_cost == 0.75


class TestBatchProgressTrackerEstimatedTimeRemaining:
    """Tests for get_estimated_time_remaining() method"""

    def test_estimated_time_no_start(self):
        """Test estimated time when not started"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        result = tracker.get_estimated_time_remaining()

        assert result is None

    def test_estimated_time_no_completed_runs(self):
        """Test estimated time with no completed runs"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        tracker.start()
        result = tracker.get_estimated_time_remaining()

        assert result is None

    def test_estimated_time_calculation(self):
        """Test estimated time calculation"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        tracker.start()
        # Simulate 5 seconds elapsed with 2 runs completed
        tracker.start_time = time.time() - 5
        tracker.completed_runs = 2
        tracker.failed_runs = 0

        remaining = tracker.get_estimated_time_remaining()

        # Average is 2.5 seconds per run, 8 remaining runs
        # Expected: 2.5 * 8 = 20 seconds
        assert remaining is not None
        assert remaining == pytest.approx(20.0, rel=0.1)

    def test_estimated_time_includes_failed_runs(self):
        """Test estimated time includes failed runs in calculation"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        tracker.start()
        tracker.start_time = time.time() - 10
        tracker.completed_runs = 2
        tracker.failed_runs = 2  # 4 total finished

        remaining = tracker.get_estimated_time_remaining()

        # Average is 2.5 seconds per run, 6 remaining runs
        # Expected: 2.5 * 6 = 15 seconds
        assert remaining is not None
        assert remaining == pytest.approx(15.0, rel=0.1)


class TestBatchProgressTrackerPrintSummary:
    """Tests for _print_summary() method"""

    @patch('builtins.print')
    def test_print_summary_not_started(self, mock_print):
        """Test print summary when not started does nothing"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        tracker._print_summary()

        # Should not print anything if not started
        mock_print.assert_not_called()

    @patch('builtins.print')
    def test_print_summary_with_data(self, mock_print):
        """Test print summary with tracking data"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Summary Test",
            use_rich=False
        )

        tracker.start()
        tracker.completed_runs = 7
        tracker.failed_runs = 3
        tracker.total_cost = 2.50

        tracker._print_summary()

        printed = ' '.join(str(call) for call in mock_print.call_args_list)
        assert "10" in printed
        assert "7" in printed
        assert "3" in printed
        assert "70" in printed  # 70% success rate
        assert "2.50" in printed

    @patch('builtins.print')
    def test_print_summary_includes_avg_cost(self, mock_print):
        """Test print summary includes average cost per run"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Avg Cost Test",
            use_rich=False
        )

        tracker.start()
        tracker.completed_runs = 4
        tracker.total_cost = 1.00

        tracker._print_summary()

        printed = ' '.join(str(call) for call in mock_print.call_args_list)
        # Average is $0.25 per run
        assert "0.25" in printed


class TestBatchProgressTrackerGenerateDisplay:
    """Tests for _generate_display() method"""

    def test_generate_display_without_rich(self):
        """Test that generate_display returns None when rich is disabled"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Test",
            use_rich=False
        )

        result = tracker._generate_display()

        assert result is None


class TestSimpleProgressTracker:
    """Tests for SimpleProgressTracker class"""

    def test_simple_tracker_is_wrapper(self):
        """Test that SimpleProgressTracker wraps BatchProgressTracker"""
        tracker = SimpleProgressTracker(
            total_runs=10,
            experiment_name="Simple Test"
        )

        # Should have access to underlying tracker
        assert hasattr(tracker, 'tracker')
        assert isinstance(tracker.tracker, BatchProgressTracker)
        assert tracker.tracker.use_rich is False

    def test_simple_tracker_with_budget(self):
        """Test SimpleProgressTracker with budget"""
        tracker = SimpleProgressTracker(
            total_runs=10,
            experiment_name="Budget Test",
            budget_limit=50.0
        )

        assert tracker.tracker.budget_limit == 50.0

    def test_simple_tracker_delegates_methods(self):
        """Test that SimpleProgressTracker delegates to underlying tracker"""
        tracker = SimpleProgressTracker(
            total_runs=10,
            experiment_name="Delegate Test"
        )

        # These should all delegate to the underlying tracker
        tracker.start()
        assert tracker.tracker.start_time is not None

        tracker.update_run_started("run-1", "test")
        assert tracker.tracker.current_run_id == "run-1"

        tracker.update_run_completed("run-1", 0.25, success=True)
        assert tracker.tracker.completed_runs == 1
        assert tracker.tracker.total_cost == 0.25


class TestBatchProgressTrackerIntegration:
    """Integration tests for batch progress tracking"""

    @patch('builtins.print')
    def test_full_batch_workflow(self, mock_print):
        """Test a complete batch tracking workflow"""
        tracker = BatchProgressTracker(
            total_runs=5,
            experiment_name="Full Workflow Test",
            budget_limit=10.0,
            use_rich=False
        )

        # Start tracking
        tracker.start()

        # Process runs
        for i in range(5):
            run_id = f"var-001-run-{i+1:03d}"
            tracker.update_run_started(run_id, f"Variation {i+1}")

            # Simulate some work
            cost = 0.10 + (i * 0.05)
            success = i < 4  # Last run fails

            tracker.update_run_completed(run_id, cost, success)

        # Stop tracking
        tracker.stop()

        # Verify final state
        assert tracker.completed_runs == 4
        assert tracker.failed_runs == 1
        assert tracker.total_cost == pytest.approx(0.10 + 0.15 + 0.20 + 0.25 + 0.30, rel=0.01)

    @patch('builtins.print')
    def test_success_rate_calculation(self, mock_print):
        """Test success rate is calculated correctly in summary"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Success Rate Test",
            use_rich=False
        )

        tracker.start()

        # 6 successful, 4 failed
        for i in range(10):
            tracker.update_run_completed(f"run-{i}", 0.10, success=(i < 6))

        # Verify internal state
        total_finished = tracker.completed_runs + tracker.failed_runs
        success_rate = tracker.completed_runs / total_finished * 100

        assert total_finished == 10
        assert tracker.completed_runs == 6
        assert tracker.failed_runs == 4
        assert success_rate == 60.0


class TestBatchProgressTrackerEdgeCases:
    """Tests for edge cases"""

    def test_zero_runs(self):
        """Test tracker with zero runs"""
        tracker = BatchProgressTracker(
            total_runs=0,
            experiment_name="Zero Runs",
            use_rich=False
        )

        tracker.start()
        tracker.stop()

        # Should handle gracefully
        assert tracker.total_runs == 0
        assert tracker.completed_runs == 0

    def test_zero_budget_limit(self):
        """Test tracker with zero budget limit"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Zero Budget",
            budget_limit=0.0,
            use_rich=False
        )

        assert tracker.budget_limit == 0.0

    def test_negative_cost(self):
        """Test handling of negative cost (edge case)"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="Negative Cost",
            use_rich=False
        )

        # While unusual, the tracker should handle it
        tracker.update_run_completed("run-1", -0.10, success=True)

        assert tracker.total_cost == -0.10

    def test_very_long_experiment_name(self):
        """Test with very long experiment name"""
        long_name = "A" * 1000
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name=long_name,
            use_rich=False
        )

        assert tracker.experiment_name == long_name

    def test_unicode_in_names(self):
        """Test handling of unicode characters in names"""
        tracker = BatchProgressTracker(
            total_runs=10,
            experiment_name="测试实验 🧪",
            use_rich=False
        )

        tracker.update_run_started("运行-001", "变体说明 📊")

        assert tracker.experiment_name == "测试实验 🧪"
        assert tracker.current_run_id == "运行-001"
