"""
Tests for Metrics Tracker module (legacy V1 metrics tracker)

Tests metric definition loading, extraction, statistics calculation, and reporting.
"""
import pytest
import tempfile
import json
import yaml
from pathlib import Path

from scenario_lab.core.metrics_tracker import (
    MetricsTracker,
    load_metrics_tracker,
)
from scenario_lab.models.state import (
    ScenarioState,
    WorldState,
    MetricRecord,
    Decision,
)


class TestMetricsTrackerInit:
    """Tests for MetricsTracker initialization"""

    def test_init_without_config(self):
        """Test initialization without config file"""
        tracker = MetricsTracker()

        assert tracker.metrics_definitions == {}
        assert tracker.scenario_name == ""

    def test_init_with_config(self):
        """Test initialization with config file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "scenario_name": "Test Scenario",
                "metrics": {
                    "cooperation_index": {
                        "type": "float",
                        "pattern": r"cooperation.*?(\d+\.?\d*)",
                        "unit": "%"
                    }
                }
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker(config_path)

            assert tracker.scenario_name == "Test Scenario"
            assert "cooperation_index" in tracker.metrics_definitions


class TestMetricsTrackerLoadDefinitions:
    """Tests for load_metrics_definitions() method"""

    def test_load_v1_format(self):
        """Test loading V1 format (metrics as dict)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "scenario_name": "V1 Format",
                "metrics": {
                    "metric_a": {"type": "integer", "pattern": r"(\d+)"},
                    "metric_b": {"type": "float", "pattern": r"(\d+\.\d+)"}
                }
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker()
            tracker.load_metrics_definitions(config_path)

            assert len(tracker.metrics_definitions) == 2
            assert "metric_a" in tracker.metrics_definitions
            assert "metric_b" in tracker.metrics_definitions

    def test_load_v2_format(self):
        """Test loading V2 format (metrics as list)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "scenario_name": "V2 Format",
                "metrics": [
                    {"name": "metric_a", "type": "integer", "pattern": r"(\d+)"},
                    {"name": "metric_b", "type": "float", "pattern": r"(\d+\.\d+)"}
                ]
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker()
            tracker.load_metrics_definitions(config_path)

            assert len(tracker.metrics_definitions) == 2
            assert "metric_a" in tracker.metrics_definitions
            assert "metric_b" in tracker.metrics_definitions

    def test_load_missing_file_raises(self):
        """Test that loading from non-existent file raises error"""
        tracker = MetricsTracker()

        with pytest.raises(FileNotFoundError):
            tracker.load_metrics_definitions(Path("/nonexistent/metrics.yaml"))


class TestMetricsTrackerExtraction:
    """Tests for metric extraction from text"""

    def _create_tracker_with_metrics(self, tmpdir, metrics):
        """Helper to create tracker with given metrics"""
        config_path = Path(tmpdir) / "metrics.yaml"
        config = {"scenario_name": "Test", "metrics": metrics}
        config_path.write_text(yaml.dump(config))
        return MetricsTracker(config_path)

    def test_extract_integer_metric(self):
        """Test extracting integer metric from text"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = self._create_tracker_with_metrics(tmpdir, {
                "score": {
                    "type": "integer",
                    "pattern": r"score[:\s]+(\d+)",
                    "extraction_method": "regex"
                }
            })

            text = "The final score: 85 points achieved."
            metrics = tracker.extract_metrics_from_text(turn=1, text=text)

            assert len(metrics) == 1
            assert metrics[0].name == "score"
            assert metrics[0].value == 85.0
            assert metrics[0].turn == 1

    def test_extract_float_metric(self):
        """Test extracting float metric from text"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = self._create_tracker_with_metrics(tmpdir, {
                "percentage": {
                    "type": "float",
                    "pattern": r"percentage[:\s]+(\d+\.?\d*)",
                    "extraction_method": "regex"
                }
            })

            text = "The completion percentage: 87.5 today."
            metrics = tracker.extract_metrics_from_text(turn=2, text=text)

            assert len(metrics) == 1
            assert metrics[0].name == "percentage"
            assert metrics[0].value == pytest.approx(87.5)

    def test_extract_multiple_matches_uses_last(self):
        """Test that multiple matches use the last one"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = self._create_tracker_with_metrics(tmpdir, {
                "level": {
                    "type": "integer",
                    "pattern": r"level[:\s]+(\d+)",
                    "extraction_method": "regex"
                }
            })

            text = "Started at level: 1. Then level: 5. Finally level: 10."
            metrics = tracker.extract_metrics_from_text(turn=1, text=text)

            assert len(metrics) == 1
            assert metrics[0].value == 10.0  # Last match

    def test_extract_no_match_returns_empty(self):
        """Test that no match returns empty list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = self._create_tracker_with_metrics(tmpdir, {
                "score": {
                    "type": "integer",
                    "pattern": r"score[:\s]+(\d+)",
                    "extraction_method": "regex"
                }
            })

            text = "No relevant content here."
            metrics = tracker.extract_metrics_from_text(turn=1, text=text)

            assert len(metrics) == 0

    def test_extract_actor_specific_metric(self):
        """Test extracting actor-specific metric"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = self._create_tracker_with_metrics(tmpdir, {
                "actor_score": {
                    "type": "integer",
                    "pattern": r"score[:\s]+(\d+)",
                    "actor_specific": True,
                    "actor": "Player1"
                }
            })

            # Should extract when actor matches
            text = "The score: 50 points."
            metrics = tracker.extract_metrics_from_text(turn=1, text=text, actor_name="Player1")
            assert len(metrics) == 1

            # Should not extract when actor doesn't match
            metrics = tracker.extract_metrics_from_text(turn=1, text=text, actor_name="Player2")
            assert len(metrics) == 0

            # Should not extract without actor name
            metrics = tracker.extract_metrics_from_text(turn=1, text=text, actor_name=None)
            assert len(metrics) == 0

    def test_extract_case_insensitive(self):
        """Test case insensitive extraction"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = self._create_tracker_with_metrics(tmpdir, {
                "score": {
                    "type": "integer",
                    "pattern": r"SCORE[:\s]+(\d+)",
                    "extraction_method": "regex"
                }
            })

            text = "Final Score: 100 points."  # Mixed case
            metrics = tracker.extract_metrics_from_text(turn=1, text=text)

            assert len(metrics) == 1
            assert metrics[0].value == 100.0


class TestMetricsTrackerConvertValue:
    """Tests for _convert_value() method"""

    def test_convert_integer(self):
        """Test converting to integer"""
        tracker = MetricsTracker()

        assert tracker._convert_value("42", "integer") == 42
        assert tracker._convert_value("100", "integer") == 100

    def test_convert_float(self):
        """Test converting to float"""
        tracker = MetricsTracker()

        assert tracker._convert_value("3.14", "float") == pytest.approx(3.14)
        assert tracker._convert_value("100.5", "float") == pytest.approx(100.5)

    def test_convert_scientific_notation(self):
        """Test converting scientific notation"""
        tracker = MetricsTracker()

        # Format: base^exponent
        result = tracker._convert_value("10^2", "float")
        assert result == pytest.approx(100.0)

        result = tracker._convert_value("2^3", "float")
        assert result == pytest.approx(8.0)

    def test_convert_boolean(self):
        """Test converting to boolean (as numeric)"""
        tracker = MetricsTracker()

        assert tracker._convert_value("true", "boolean") == 1.0
        assert tracker._convert_value("yes", "boolean") == 1.0
        assert tracker._convert_value("", "boolean") == 0.0

    def test_convert_invalid_returns_zero(self):
        """Test that invalid conversion returns 0.0"""
        tracker = MetricsTracker()

        assert tracker._convert_value("not a number", "integer") == 0.0
        assert tracker._convert_value("invalid", "float") == 0.0


class TestMetricsTrackerStatistics:
    """Tests for statistics calculation"""

    def _create_state_with_metrics(self, metrics_list):
        """Helper to create state with metrics"""
        return ScenarioState(
            scenario_id="test-scenario",
            scenario_name="Test Scenario",
            run_id="test-run-001",
            turn=len(metrics_list),
            world_state=WorldState(turn=1, content="Test"),
            decisions={},
            metrics=metrics_list
        )

    def test_calculate_summary_statistics(self):
        """Test summary statistics calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "metrics": {
                    "score": {"type": "integer", "unit": "points"}
                }
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker(config_path)

            metrics = [
                MetricRecord(name="score", value=10.0, turn=1),
                MetricRecord(name="score", value=20.0, turn=2),
                MetricRecord(name="score", value=30.0, turn=3),
            ]
            state = self._create_state_with_metrics(metrics)

            stats = tracker.calculate_summary_statistics(state)

            assert "score" in stats
            assert stats["score"]["count"] == 3
            assert stats["score"]["min"] == 10.0
            assert stats["score"]["max"] == 30.0
            assert stats["score"]["mean"] == 20.0
            assert stats["score"]["first"] == 10.0
            assert stats["score"]["last"] == 30.0
            assert stats["score"]["change"] == 20.0  # 30 - 10

    def test_calculate_summary_multiple_metrics(self):
        """Test summary with multiple metric types"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "metrics": {
                    "score": {"type": "integer"},
                    "percentage": {"type": "float"}
                }
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker(config_path)

            metrics = [
                MetricRecord(name="score", value=100.0, turn=1),
                MetricRecord(name="percentage", value=50.0, turn=1),
                MetricRecord(name="score", value=150.0, turn=2),
                MetricRecord(name="percentage", value=75.0, turn=2),
            ]
            state = self._create_state_with_metrics(metrics)

            stats = tracker.calculate_summary_statistics(state)

            assert "score" in stats
            assert "percentage" in stats
            assert stats["score"]["count"] == 2
            assert stats["percentage"]["count"] == 2

    def test_calculate_summary_empty_metrics(self):
        """Test summary with no metrics"""
        tracker = MetricsTracker()
        state = self._create_state_with_metrics([])

        stats = tracker.calculate_summary_statistics(state)

        assert stats == {}


class TestMetricsTrackerSummary:
    """Tests for get_metrics_summary() method"""

    def test_get_metrics_summary(self):
        """Test getting comprehensive metrics summary"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "scenario_name": "Test Scenario",
                "metrics": {
                    "score": {"type": "integer", "description": "Player score"}
                }
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker(config_path)

            metrics = [
                MetricRecord(name="score", value=50.0, turn=1),
                MetricRecord(name="score", value=100.0, turn=2),
            ]
            state = ScenarioState(
                scenario_id="test-scenario",
                scenario_name="Test Scenario",
                run_id="test-run-001",
                turn=2,
                world_state=WorldState(turn=2, content="Test"),
                decisions={},
                metrics=metrics
            )

            summary = tracker.get_metrics_summary(state)

            assert summary["scenario"] == "Test Scenario"
            assert summary["total_turns"] == 2
            assert summary["total_metrics"] == 2
            assert "score" in summary["metrics_definitions"]
            assert 1 in summary["metrics_by_turn"]
            assert 2 in summary["metrics_by_turn"]
            assert summary["final_metrics"]["score"] == 100.0


class TestMetricsTrackerSaveAndPrint:
    """Tests for save_metrics_summary() and print_summary() methods"""

    def test_save_metrics_summary(self):
        """Test saving metrics summary to JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "scenario_name": "Save Test",
                "metrics": {"score": {"type": "integer"}}
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker(config_path)

            metrics = [MetricRecord(name="score", value=75.0, turn=1)]
            state = ScenarioState(
                scenario_id="test-scenario",
                scenario_name="Save Test",
                run_id="test-run-001",
                turn=1,
                world_state=WorldState(turn=1, content="Test"),
                decisions={},
                metrics=metrics
            )

            output_path = Path(tmpdir) / "metrics-summary.json"
            tracker.save_metrics_summary(state, output_path)

            assert output_path.exists()

            with open(output_path) as f:
                saved = json.load(f)

            assert saved["scenario"] == "Save Test"
            assert saved["total_metrics"] == 1

    def test_print_summary_no_metrics(self, capsys):
        """Test printing summary with no metrics"""
        tracker = MetricsTracker()
        state = ScenarioState(
            scenario_id="test-scenario",
            scenario_name="Test",
            run_id="test-run-001",
            turn=1,
            world_state=WorldState(turn=1, content="Test"),
            decisions={},
            metrics=[]
        )

        tracker.print_summary(state)

        captured = capsys.readouterr()
        assert "No metrics recorded" in captured.out

    def test_print_summary_with_metrics(self, capsys):
        """Test printing summary with metrics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "metrics": {"score": {"type": "integer", "unit": "points"}}
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker(config_path)

            metrics = [
                MetricRecord(name="score", value=50.0, turn=1),
                MetricRecord(name="score", value=100.0, turn=2),
            ]
            state = ScenarioState(
                scenario_id="test-scenario",
                scenario_name="Test",
                run_id="test-run-001",
                turn=2,
                world_state=WorldState(turn=2, content="Test"),
                decisions={},
                metrics=metrics
            )

            tracker.print_summary(state)

            captured = capsys.readouterr()
            assert "METRICS SUMMARY" in captured.out
            assert "Turn 1" in captured.out
            assert "Turn 2" in captured.out
            assert "score" in captured.out


class TestMetricsTrackerExtractFromState:
    """Tests for extracting metrics from ScenarioState"""

    def test_extract_from_world_state(self):
        """Test extracting metrics from world state content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "metrics": {
                    "tension": {
                        "type": "integer",
                        "pattern": r"tension[:\s]+(\d+)",
                        "extraction_method": "regex"
                    }
                }
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker(config_path)

            state = ScenarioState(
                scenario_id="test-scenario",
                scenario_name="Test",
                run_id="test-run-001",
                turn=3,
                world_state=WorldState(turn=3, content="The tension: 75 has increased."),
                decisions={},
                metrics=[]
            )

            metrics = tracker.extract_metrics_from_world_state(state)

            assert len(metrics) == 1
            assert metrics[0].name == "tension"
            assert metrics[0].value == 75.0
            assert metrics[0].turn == 3

    def test_extract_from_decisions(self):
        """Test extracting metrics from actor decisions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "metrics": {
                    "confidence": {
                        "type": "integer",
                        "pattern": r"confidence[:\s]+(\d+)",
                        "extraction_method": "regex"
                    }
                }
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker(config_path)

            state = ScenarioState(
                scenario_id="test-scenario",
                scenario_name="Test",
                run_id="test-run-001",
                turn=2,
                world_state=WorldState(turn=2, content="World state"),
                decisions={
                    "Actor1": Decision(
                        actor="Actor1",
                        turn=2,
                        goals=["Goals"],
                        reasoning="My confidence: 80 in this decision.",
                        action="Take action with confidence: 90"
                    )
                },
                metrics=[]
            )

            metrics = tracker.extract_metrics_from_decisions(state)

            # Should find matches in both reasoning and action
            assert len(metrics) >= 1


class TestLoadMetricsTracker:
    """Tests for load_metrics_tracker() function"""

    def test_load_metrics_tracker_success(self):
        """Test successful loading of metrics tracker"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = Path(tmpdir)
            metrics_path = scenario_path / "metrics.yaml"
            metrics_path.write_text(yaml.dump({
                "scenario_name": "Test",
                "metrics": {"score": {"type": "integer"}}
            }))

            tracker = load_metrics_tracker(scenario_path)

            assert tracker is not None
            assert "score" in tracker.metrics_definitions

    def test_load_metrics_tracker_no_file(self):
        """Test loading when no metrics.yaml exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = Path(tmpdir)

            tracker = load_metrics_tracker(scenario_path)

            assert tracker is None


class TestMetricsTrackerEdgeCases:
    """Tests for edge cases"""

    def test_extract_tuple_from_regex_groups(self):
        """Test extracting value from regex with multiple groups"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "metrics": {
                    "value": {
                        "type": "integer",
                        "pattern": r"(\d+)\s+or\s+(\d+)",
                        "extraction_method": "regex"
                    }
                }
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker(config_path)

            text = "Choose 5 or 10 options."
            metrics = tracker.extract_metrics_from_text(turn=1, text=text)

            # Should extract the first non-empty group
            assert len(metrics) == 1
            assert metrics[0].value == 5.0  # First group

    def test_manual_extraction_method_skipped(self):
        """Test that manual extraction method is skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "metrics": {
                    "manual_metric": {
                        "type": "integer",
                        "extraction_method": "manual"
                    }
                }
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker(config_path)

            text = "Some content with numbers 123"
            metrics = tracker.extract_metrics_from_text(turn=1, text=text)

            assert len(metrics) == 0

    def test_metric_record_metadata(self):
        """Test that extracted metrics include proper metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "metrics.yaml"
            config = {
                "metrics": {
                    "score": {
                        "type": "integer",
                        "pattern": r"score[:\s]+(\d+)",
                        "unit": "points",
                        "description": "Player score",
                        "extraction_method": "regex"
                    }
                }
            }
            config_path.write_text(yaml.dump(config))

            tracker = MetricsTracker(config_path)

            text = "Final score: 100 achieved."
            metrics = tracker.extract_metrics_from_text(turn=1, text=text, actor_name="Player1")

            assert len(metrics) == 1
            assert metrics[0].metadata["actor"] == "Player1"
            assert metrics[0].metadata["type"] == "integer"
            assert metrics[0].metadata["raw_value"] == "100"
            assert metrics[0].metadata["unit"] == "points"
            assert metrics[0].metadata["definition"] == "Player score"

    def test_empty_state_metrics(self):
        """Test calculating stats with empty state metrics"""
        tracker = MetricsTracker()
        state = ScenarioState(
            scenario_id="test-scenario",
            scenario_name="Test",
            run_id="test-run-001",
            turn=1,
            world_state=WorldState(turn=1, content="Test"),
            decisions={},
            metrics=[]
        )

        summary = tracker.get_metrics_summary(state)

        assert summary["total_metrics"] == 0
        assert summary["final_metrics"] == {}
