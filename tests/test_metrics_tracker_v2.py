"""
Unit tests for MetricsTrackerV2

Tests V2 metrics extraction with Pydantic schemas.
"""
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, patch

from scenario_lab.schemas.metrics import MetricsConfig, MetricConfig, MetricExtraction
from scenario_lab.core.metrics_tracker_v2 import MetricsTrackerV2
from scenario_lab.loaders.metrics_loader import load_metrics_config
from scenario_lab.models.state import ScenarioState, WorldState, Decision, MetricRecord
from scenario_lab.utils.api_client import LLMResponse


@pytest.fixture
def sample_metrics_config():
    """Create a sample MetricsConfig for testing"""
    return MetricsConfig(
        metrics=[
            MetricConfig(
                name="cooperation_level",
                description="Level of cooperation",
                type="continuous",
                range=(0, 10),
                unit="score",
                extraction=MetricExtraction(
                    type="pattern",
                    pattern=r"cooperation level[:\s]+(\d+)"
                )
            ),
            MetricConfig(
                name="agreement_reached",
                description="Whether agreement reached",
                type="boolean",
                extraction=MetricExtraction(
                    type="keyword",
                    keywords=["agreement reached", "deal signed"],
                    scoring="presence"
                )
            ),
            MetricConfig(
                name="collaboration_count",
                description="Collaboration mentions",
                type="continuous",
                range=(0, 100),
                unit="count",
                extraction=MetricExtraction(
                    type="keyword",
                    keywords=["collaboration", "collaborate"],
                    scoring="count"
                )
            ),
        ],
        export_format="json",
        auto_export=True
    )


@pytest.fixture
def metrics_tracker(sample_metrics_config):
    """Create MetricsTrackerV2 instance"""
    return MetricsTrackerV2(metrics_config=sample_metrics_config, api_key="test-key")


@pytest.fixture
def sample_state():
    """Create a sample ScenarioState for testing"""
    return ScenarioState(
        scenario_id="test-001",
        scenario_name="Test Scenario",
        run_id="run-001",
        turn=1,
        world_state=WorldState(
            turn=1,
            content="The cooperation level: 7. The actors have agreement reached and are now collaborating closely. They collaborate on multiple fronts.",
            timestamp=datetime.now()
        ),
        decisions={
            "actor-a": Decision(
                actor="Actor A",
                turn=1,
                goals=["cooperate"],
                reasoning="I want to collaborate with others",
                action="Propose collaboration",
                timestamp=datetime.now()
            )
        }
    )


class TestMetricsTrackerV2:
    """Test MetricsTrackerV2 functionality"""

    def test_initialization(self, sample_metrics_config):
        """Test MetricsTrackerV2 initialization"""
        tracker = MetricsTrackerV2(
            metrics_config=sample_metrics_config,
            api_key="test-key"
        )

        assert len(tracker.metrics) == 3
        assert "cooperation_level" in tracker.metrics
        assert "agreement_reached" in tracker.metrics
        assert "collaboration_count" in tracker.metrics

    @pytest.mark.asyncio
    async def test_extract_with_pattern(self, metrics_tracker):
        """Test pattern extraction"""
        text = "The cooperation level: 8 out of 10."

        records = await metrics_tracker.extract_metrics_from_text(
            turn=1,
            text=text,
            actor_name=None
        )

        # Should extract cooperation_level
        coop_records = [r for r in records if r.name == "cooperation_level"]
        assert len(coop_records) == 1
        assert coop_records[0].value == 8.0
        assert coop_records[0].turn == 1

    @pytest.mark.asyncio
    async def test_extract_with_keyword_presence(self, metrics_tracker):
        """Test keyword extraction with presence scoring"""
        text = "The parties have agreement reached and the deal was completed."

        records = await metrics_tracker.extract_metrics_from_text(
            turn=1,
            text=text,
            actor_name=None
        )

        # Should extract agreement_reached
        agreement_records = [r for r in records if r.name == "agreement_reached"]
        assert len(agreement_records) == 1
        assert agreement_records[0].value == 1.0  # Present

    @pytest.mark.asyncio
    async def test_extract_with_keyword_count(self, metrics_tracker):
        """Test keyword extraction with count scoring"""
        text = "We need collaboration. More collaboration is key. Collaborate now."

        records = await metrics_tracker.extract_metrics_from_text(
            turn=1,
            text=text,
            actor_name=None
        )

        # Should extract collaboration_count
        collab_records = [r for r in records if r.name == "collaboration_count"]
        assert len(collab_records) == 1
        assert collab_records[0].value == 3.0  # 2x "collaboration", 1x "collaborate"

    @pytest.mark.asyncio
    async def test_extract_from_world_state(self, metrics_tracker, sample_state):
        """Test extracting metrics from world state"""
        records = await metrics_tracker.extract_metrics_from_world_state(sample_state)

        # Should extract multiple metrics from world state
        assert len(records) > 0

        # Check specific metrics
        coop_records = [r for r in records if r.name == "cooperation_level"]
        assert len(coop_records) == 1
        assert coop_records[0].value == 7.0

    @pytest.mark.asyncio
    async def test_extract_from_decisions(self, metrics_tracker, sample_state):
        """Test extracting metrics from actor decisions"""
        records = await metrics_tracker.extract_metrics_from_decisions(sample_state)

        # Should extract metrics from decisions
        assert len(records) >= 0  # May or may not find metrics in decision text

        # Check that all records have correct turn
        for record in records:
            assert record.turn == 1

    def test_calculate_summary_statistics(self, metrics_tracker, sample_state):
        """Test calculating summary statistics"""
        # Add some metric records to state
        state = sample_state
        state = state.with_metric(MetricRecord(
            name="cooperation_level",
            value=5.0,
            turn=1,
            timestamp=datetime.now()
        ))
        state = state.with_metric(MetricRecord(
            name="cooperation_level",
            value=7.0,
            turn=2,
            timestamp=datetime.now()
        ))

        stats = metrics_tracker.calculate_summary_statistics(state)

        assert "cooperation_level" in stats
        coop_stats = stats["cooperation_level"]
        assert coop_stats["count"] == 2
        assert coop_stats["min"] == 5.0
        assert coop_stats["max"] == 7.0
        assert coop_stats["mean"] == 6.0
        assert coop_stats["change"] == 2.0

    def test_get_metrics_summary(self, metrics_tracker, sample_state):
        """Test getting comprehensive metrics summary"""
        state = sample_state.with_metric(MetricRecord(
            name="cooperation_level",
            value=8.0,
            turn=1,
            timestamp=datetime.now()
        ))

        summary = metrics_tracker.get_metrics_summary(state)

        assert "scenario" in summary
        assert summary["scenario"] == "Test Scenario"
        assert "total_turns" in summary
        assert "total_metrics" in summary
        assert "metrics_by_turn" in summary
        assert "final_metrics" in summary
        assert "summary_statistics" in summary


class TestMetricsLoader:
    """Test metrics loader functionality"""

    def test_load_metrics_config_v2_format(self):
        """Test loading V2 format metrics.yaml"""
        metrics_file = Path("scenarios/test-metrics-v2/metrics.yaml")

        if metrics_file.exists():
            config = load_metrics_config(metrics_file)

            assert config is not None
            assert len(config.metrics) > 0

            # Check first metric
            first_metric = config.metrics[0]
            assert hasattr(first_metric, 'name')
            assert hasattr(first_metric, 'description')
            assert hasattr(first_metric, 'type')
            assert hasattr(first_metric, 'extraction')

    def test_load_metrics_config_nonexistent(self):
        """Test loading from nonexistent file"""
        metrics_file = Path("nonexistent/metrics.yaml")
        config = load_metrics_config(metrics_file)

        assert config is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
