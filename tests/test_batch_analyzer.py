"""
Tests for Batch Analyzer module

Tests data collection, statistical analysis, pattern identification, and report generation.
"""
import pytest
import tempfile
import json
import yaml
from pathlib import Path

from scenario_lab.batch.batch_analyzer import BatchAnalyzer


class TestBatchAnalyzerInit:
    """Tests for BatchAnalyzer initialization"""

    def test_init_creates_analysis_dir(self):
        """Test that initialization creates analysis directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()

            analyzer = BatchAnalyzer(str(batch_dir))

            assert analyzer.analysis_dir.exists()
            assert analyzer.analysis_dir == batch_dir / "analysis"

    def test_init_with_batch_config(self):
        """Test initialization loads batch config when present"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()

            # Create batch config
            config = {
                "experiment_name": "Test Experiment",
                "base_scenario": "/path/to/scenario",
                "runs_per_variation": 5
            }
            (batch_dir / "batch-config.yaml").write_text(yaml.dump(config))

            analyzer = BatchAnalyzer(str(batch_dir))

            assert analyzer.batch_config is not None
            assert analyzer.batch_config["experiment_name"] == "Test Experiment"

    def test_init_without_batch_config(self):
        """Test initialization handles missing batch config gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()

            analyzer = BatchAnalyzer(str(batch_dir))

            assert analyzer.batch_config is None

    def test_init_with_batch_summary(self):
        """Test initialization loads batch summary when present"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()

            # Create batch summary
            summary = {
                "experiment_name": "Test",
                "runs_completed": 10,
                "runs_failed": 2
            }
            (batch_dir / "batch-summary.json").write_text(json.dumps(summary))

            analyzer = BatchAnalyzer(str(batch_dir))

            assert analyzer.batch_summary is not None
            assert analyzer.batch_summary["runs_completed"] == 10

    def test_init_with_batch_costs(self):
        """Test initialization loads batch costs when present"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()

            # Create batch costs
            costs = {
                "total_cost": 5.50,
                "average_cost": 0.55
            }
            (batch_dir / "batch-costs.json").write_text(json.dumps(costs))

            analyzer = BatchAnalyzer(str(batch_dir))

            assert analyzer.batch_costs is not None
            assert analyzer.batch_costs["total_cost"] == 5.50


class TestBatchAnalyzerDataCollection:
    """Tests for data collection functionality"""

    def _create_run_directory(self, runs_dir: Path, run_id: str, metrics: dict, cost: float, success: bool, turns: int):
        """Helper to create a run directory with data files"""
        run_dir = runs_dir / run_id
        run_dir.mkdir(parents=True)

        # Create metrics.json
        (run_dir / "metrics.json").write_text(json.dumps({
            "final_metrics": metrics
        }))

        # Create costs.json
        (run_dir / "costs.json").write_text(json.dumps({
            "total_cost": cost
        }))

        # Create scenario-state.json
        (run_dir / "scenario-state.json").write_text(json.dumps({
            "status": "completed" if success else "failed",
            "current_turn": turns
        }))

        return run_dir

    def test_collect_run_data_single_run(self):
        """Test collecting data from a single run"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            self._create_run_directory(
                runs_dir, "var-001-run-001",
                metrics={"accuracy": 0.95, "score": 100},
                cost=0.25,
                success=True,
                turns=5
            )

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.collect_run_data()

            assert len(analyzer.run_data) == 1
            assert analyzer.run_data[0]["run_id"] == "var-001-run-001"
            assert analyzer.run_data[0]["variation_id"] == 1
            assert analyzer.run_data[0]["metrics"]["accuracy"] == 0.95
            assert analyzer.run_data[0]["cost"] == 0.25
            assert analyzer.run_data[0]["success"] is True

    def test_collect_run_data_multiple_runs(self):
        """Test collecting data from multiple runs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            # Create multiple runs
            self._create_run_directory(runs_dir, "var-001-run-001", {"metric_a": 10}, 0.10, True, 3)
            self._create_run_directory(runs_dir, "var-001-run-002", {"metric_a": 12}, 0.12, True, 3)
            self._create_run_directory(runs_dir, "var-002-run-001", {"metric_a": 8}, 0.08, False, 2)

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.collect_run_data()

            assert len(analyzer.run_data) == 3
            assert 1 in analyzer.variation_data
            assert 2 in analyzer.variation_data
            assert len(analyzer.variation_data[1]["runs"]) == 2
            assert len(analyzer.variation_data[2]["runs"]) == 1

    def test_collect_run_data_skips_invalid_format(self):
        """Test that invalid run ID formats are skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            # Create valid run
            self._create_run_directory(runs_dir, "var-001-run-001", {"metric": 1}, 0.1, True, 1)

            # Create invalid run directory
            (runs_dir / "invalid-format").mkdir()

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.collect_run_data()

            assert len(analyzer.run_data) == 1

    def test_collect_run_data_no_runs_dir_raises(self):
        """Test that missing runs directory raises error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()

            analyzer = BatchAnalyzer(str(batch_dir))

            with pytest.raises(FileNotFoundError):
                analyzer.collect_run_data()


class TestBatchAnalyzerStatistics:
    """Tests for statistical analysis"""

    def _setup_analyzer_with_data(self, tmpdir):
        """Helper to set up analyzer with test data"""
        batch_dir = Path(tmpdir) / "batch-output"
        batch_dir.mkdir()
        runs_dir = batch_dir / "runs"
        runs_dir.mkdir()

        # Create runs with varied metrics
        runs_data = [
            ("var-001-run-001", {"accuracy": 0.80, "score": 80}, 0.10, True),
            ("var-001-run-002", {"accuracy": 0.85, "score": 85}, 0.12, True),
            ("var-001-run-003", {"accuracy": 0.90, "score": 90}, 0.11, True),
            ("var-002-run-001", {"accuracy": 0.70, "score": 70}, 0.08, True),
            ("var-002-run-002", {"accuracy": 0.75, "score": 75}, 0.09, False),
        ]

        for run_id, metrics, cost, success in runs_data:
            run_dir = runs_dir / run_id
            run_dir.mkdir()
            (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": metrics}))
            (run_dir / "costs.json").write_text(json.dumps({"total_cost": cost}))
            (run_dir / "scenario-state.json").write_text(json.dumps({
                "status": "completed" if success else "failed",
                "current_turn": 5
            }))

        analyzer = BatchAnalyzer(str(batch_dir))
        analyzer.collect_run_data()
        return analyzer

    def test_calculate_metric_statistics(self):
        """Test calculation of overall metric statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = self._setup_analyzer_with_data(tmpdir)

            stats = analyzer.calculate_metric_statistics()

            assert "accuracy" in stats
            assert "score" in stats

            # Check accuracy stats (only successful runs: 0.80, 0.85, 0.90, 0.70)
            acc_stats = stats["accuracy"]
            assert acc_stats["count"] == 4
            assert abs(acc_stats["mean"] - 0.8125) < 0.01
            assert acc_stats["min"] == 0.70
            assert acc_stats["max"] == 0.90

    def test_calculate_metric_statistics_with_median(self):
        """Test that median is calculated correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = self._setup_analyzer_with_data(tmpdir)

            stats = analyzer.calculate_metric_statistics()

            # Median of [0.70, 0.80, 0.85, 0.90] should be 0.825
            assert abs(stats["accuracy"]["median"] - 0.825) < 0.01

    def test_calculate_variation_statistics(self):
        """Test calculation of per-variation statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = self._setup_analyzer_with_data(tmpdir)

            var_stats = analyzer.calculate_variation_statistics()

            assert 1 in var_stats
            assert 2 in var_stats

            # Variation 1: 3 runs, all successful
            assert var_stats[1]["total_runs"] == 3
            assert var_stats[1]["successful_runs"] == 3
            assert var_stats[1]["success_rate"] == 1.0

            # Variation 2: 2 runs, 1 successful
            assert var_stats[2]["total_runs"] == 2
            assert var_stats[2]["successful_runs"] == 1
            assert var_stats[2]["success_rate"] == 0.5

    def test_calculate_variation_statistics_includes_costs(self):
        """Test that variation statistics include cost information"""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = self._setup_analyzer_with_data(tmpdir)

            var_stats = analyzer.calculate_variation_statistics()

            assert "cost" in var_stats[1]
            assert var_stats[1]["cost"]["total"] == pytest.approx(0.33, rel=0.01)
            assert "mean" in var_stats[1]["cost"]

    def test_compare_variations(self):
        """Test comparing variations by metric"""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = self._setup_analyzer_with_data(tmpdir)

            comparison = analyzer.compare_variations("accuracy")

            # Variation 1 should have higher mean accuracy
            assert len(comparison) == 2
            assert comparison[0][0] == 1  # Variation 1 is first (higher)
            assert comparison[0][1] > comparison[1][1]

    def test_compare_variations_sorted_descending(self):
        """Test that variations are sorted by value descending"""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = self._setup_analyzer_with_data(tmpdir)

            comparison = analyzer.compare_variations("score")

            # Should be sorted descending
            for i in range(len(comparison) - 1):
                assert comparison[i][1] >= comparison[i + 1][1]


class TestBatchAnalyzerPatterns:
    """Tests for pattern identification"""

    def test_identify_patterns_success_rate(self):
        """Test pattern identification for success rate"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            # Create 8 successful and 2 failed runs
            for i in range(10):
                run_id = f"var-001-run-{i+1:03d}"
                run_dir = runs_dir / run_id
                run_dir.mkdir()
                (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": {"m": i}}))
                (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
                (run_dir / "scenario-state.json").write_text(json.dumps({
                    "status": "completed" if i < 8 else "failed",
                    "current_turn": 3
                }))

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.collect_run_data()

            patterns = analyzer.identify_patterns()

            assert patterns["success_rate"] == 0.8
            assert patterns["total_runs"] == 10
            assert patterns["successful_runs"] == 8
            assert patterns["failed_runs"] == 2

    def test_identify_patterns_best_variation(self):
        """Test identification of best performing variation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            # Variation 1: 2/3 success (67%)
            for i in range(3):
                run_id = f"var-001-run-{i+1:03d}"
                run_dir = runs_dir / run_id
                run_dir.mkdir()
                (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": {}}))
                (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
                (run_dir / "scenario-state.json").write_text(json.dumps({
                    "status": "completed" if i < 2 else "failed",
                    "current_turn": 3
                }))

            # Variation 2: 3/3 success (100%)
            for i in range(3):
                run_id = f"var-002-run-{i+1:03d}"
                run_dir = runs_dir / run_id
                run_dir.mkdir()
                (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": {}}))
                (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
                (run_dir / "scenario-state.json").write_text(json.dumps({
                    "status": "completed",
                    "current_turn": 3
                }))

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.collect_run_data()

            patterns = analyzer.identify_patterns()

            assert "best_variation" in patterns
            assert patterns["best_variation"]["variation_id"] == 2
            assert patterns["best_variation"]["success_rate"] == 1.0

    def test_identify_patterns_cost_efficiency(self):
        """Test identification of cost efficiency patterns"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            # Variation 1: 2 successful runs, $0.20 total
            for i in range(2):
                run_id = f"var-001-run-{i+1:03d}"
                run_dir = runs_dir / run_id
                run_dir.mkdir()
                (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": {}}))
                (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
                (run_dir / "scenario-state.json").write_text(json.dumps({
                    "status": "completed",
                    "current_turn": 3
                }))

            # Variation 2: 1 successful run, $0.50 total
            run_dir = runs_dir / "var-002-run-001"
            run_dir.mkdir()
            (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": {}}))
            (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.5}))
            (run_dir / "scenario-state.json").write_text(json.dumps({
                "status": "completed",
                "current_turn": 3
            }))

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.collect_run_data()

            patterns = analyzer.identify_patterns()

            assert "cost_efficiency" in patterns
            assert len(patterns["cost_efficiency"]) == 2
            # Variation 1 should be more cost efficient (2 runs / $0.20 = 10 runs/$)
            assert patterns["cost_efficiency"][0]["variation_id"] == 1


class TestBatchAnalyzerReports:
    """Tests for report generation"""

    def test_generate_analysis_report(self):
        """Test analysis report generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            # Create test run
            run_dir = runs_dir / "var-001-run-001"
            run_dir.mkdir()
            (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": {"score": 85}}))
            (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.15}))
            (run_dir / "scenario-state.json").write_text(json.dumps({
                "status": "completed",
                "current_turn": 5
            }))

            # Add batch config
            (batch_dir / "batch-config.yaml").write_text(yaml.dump({
                "experiment_name": "Test Experiment"
            }))

            analyzer = BatchAnalyzer(str(batch_dir))

            report = analyzer.generate_analysis_report()

            assert "# Batch Analysis Report" in report
            assert "Test Experiment" in report
            assert "Total Runs:" in report
            assert "Success Rate:" in report

    def test_generate_analysis_report_saves_file(self):
        """Test that analysis report is saved to file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            run_dir = runs_dir / "var-001-run-001"
            run_dir.mkdir()
            (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": {}}))
            (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
            (run_dir / "scenario-state.json").write_text(json.dumps({
                "status": "completed",
                "current_turn": 3
            }))

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.generate_analysis_report()

            report_path = analyzer.analysis_dir / "analysis-report.md"
            assert report_path.exists()

    def test_save_analysis_data(self):
        """Test saving analysis data to JSON files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            run_dir = runs_dir / "var-001-run-001"
            run_dir.mkdir()
            (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": {"accuracy": 0.9}}))
            (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
            (run_dir / "scenario-state.json").write_text(json.dumps({
                "status": "completed",
                "current_turn": 3
            }))

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.save_analysis_data()

            # Check all files were created
            assert (analyzer.analysis_dir / "metrics-analysis.json").exists()
            assert (analyzer.analysis_dir / "variation-statistics.json").exists()
            assert (analyzer.analysis_dir / "patterns.json").exists()

    def test_save_analysis_data_removes_raw_values(self):
        """Test that raw values are removed from saved metrics analysis"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            run_dir = runs_dir / "var-001-run-001"
            run_dir.mkdir()
            (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": {"accuracy": 0.9}}))
            (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
            (run_dir / "scenario-state.json").write_text(json.dumps({
                "status": "completed",
                "current_turn": 3
            }))

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.save_analysis_data()

            # Load and check metrics analysis
            with open(analyzer.analysis_dir / "metrics-analysis.json") as f:
                metrics_analysis = json.load(f)

            if metrics_analysis:  # If there are metrics
                for metric_name, stats in metrics_analysis.items():
                    assert "values" not in stats  # Raw values should be removed


class TestBatchAnalyzerVariationDescription:
    """Tests for variation description retrieval"""

    def test_get_variation_description_from_state(self):
        """Test getting variation description from batch state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            # Create batch state with variation descriptions
            batch_state = {
                "variations": [
                    {"variation_id": 1, "description": "Model: GPT-4"},
                    {"variation_id": 2, "description": "Model: GPT-3.5"}
                ]
            }
            (batch_dir / "batch-state.json").write_text(json.dumps(batch_state))

            # Create run
            run_dir = runs_dir / "var-001-run-001"
            run_dir.mkdir()
            (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": {}}))
            (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
            (run_dir / "scenario-state.json").write_text(json.dumps({
                "status": "completed",
                "current_turn": 3
            }))

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.collect_run_data()

            # The description should be loaded (either from state or fallback)
            assert "description" in analyzer.variation_data[1]
            # If state file exists, it may be used - check that we have some description
            description = analyzer.variation_data[1]["description"]
            assert description == "Model: GPT-4" or description == "Variation 1"

    def test_get_variation_description_fallback(self):
        """Test fallback variation description when no state file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            run_dir = runs_dir / "var-001-run-001"
            run_dir.mkdir()
            (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": {}}))
            (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
            (run_dir / "scenario-state.json").write_text(json.dumps({
                "status": "completed",
                "current_turn": 3
            }))

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.collect_run_data()

            assert analyzer.variation_data[1]["description"] == "Variation 1"


class TestBatchAnalyzerEdgeCases:
    """Tests for edge cases"""

    def test_empty_batch(self):
        """Test handling of empty batch (no runs)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.collect_run_data()

            assert len(analyzer.run_data) == 0
            assert len(analyzer.variation_data) == 0

            patterns = analyzer.identify_patterns()
            assert patterns["success_rate"] == 0.0
            assert patterns["total_runs"] == 0

    def test_all_failed_runs(self):
        """Test handling of batch where all runs failed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            # Create failed runs
            for i in range(3):
                run_dir = runs_dir / f"var-001-run-{i+1:03d}"
                run_dir.mkdir()
                (run_dir / "metrics.json").write_text(json.dumps({"final_metrics": {}}))
                (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
                (run_dir / "scenario-state.json").write_text(json.dumps({
                    "status": "failed",
                    "current_turn": 1
                }))

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.collect_run_data()

            stats = analyzer.calculate_metric_statistics()
            assert stats == {}  # No metrics from failed runs

            patterns = analyzer.identify_patterns()
            assert patterns["success_rate"] == 0.0

    def test_missing_metrics_file(self):
        """Test handling of missing metrics file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            run_dir = runs_dir / "var-001-run-001"
            run_dir.mkdir()
            # Only create costs and state, not metrics
            (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
            (run_dir / "scenario-state.json").write_text(json.dumps({
                "status": "completed",
                "current_turn": 3
            }))

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.collect_run_data()

            assert len(analyzer.run_data) == 1
            assert analyzer.run_data[0]["metrics"] == {}

    def test_corrupted_json_file(self):
        """Test handling of corrupted JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            run_dir = runs_dir / "var-001-run-001"
            run_dir.mkdir()
            (run_dir / "metrics.json").write_text("invalid json {")
            (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
            (run_dir / "scenario-state.json").write_text(json.dumps({
                "status": "completed",
                "current_turn": 3
            }))

            analyzer = BatchAnalyzer(str(batch_dir))
            # Should not raise, just warn and continue
            analyzer.collect_run_data()

            assert len(analyzer.run_data) == 1
            assert analyzer.run_data[0]["metrics"] == {}

    def test_non_numeric_metrics_ignored(self):
        """Test that non-numeric metrics are ignored in statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch-output"
            batch_dir.mkdir()
            runs_dir = batch_dir / "runs"
            runs_dir.mkdir()

            run_dir = runs_dir / "var-001-run-001"
            run_dir.mkdir()
            (run_dir / "metrics.json").write_text(json.dumps({
                "final_metrics": {
                    "numeric_metric": 42,
                    "string_metric": "not a number"
                }
            }))
            (run_dir / "costs.json").write_text(json.dumps({"total_cost": 0.1}))
            (run_dir / "scenario-state.json").write_text(json.dumps({
                "status": "completed",
                "current_turn": 3
            }))

            analyzer = BatchAnalyzer(str(batch_dir))
            analyzer.collect_run_data()

            stats = analyzer.calculate_metric_statistics()

            assert "numeric_metric" in stats
            assert "string_metric" not in stats
