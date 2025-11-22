"""
Integration tests for database analytics

Tests database persistence and query functionality.
"""
import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from scenario_lab.database import Database
from scenario_lab.database.models import (
    Run,
    Turn,
    Decision,
    Metric,
    Communication,
    Cost,
)


@pytest.fixture
def test_db():
    """Create a temporary test database"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()

    db = Database(f"sqlite:///{temp_file.name}")

    yield db

    # Cleanup - Database class doesn't have close(), just unlink the file
    os.unlink(temp_file.name)


class TestDatabaseBasics:
    """Test basic database operations"""

    def test_database_initialization(self, test_db):
        """Test that database initializes with schema"""
        session = test_db.get_session()
        try:
            # Check that tables exist by querying them
            session.query(Run).count()
            session.query(Turn).count()
            session.query(Decision).count()
            assert True  # If we get here, tables exist
        finally:
            session.close()

    def test_save_and_retrieve_run(self, test_db):
        """Test saving and retrieving a run"""
        # Create a run
        run = Run(
            id="test-run-001",
            scenario_id="test-scenario",
            scenario_name="Test Scenario",
            created=datetime.now(),
            status="completed",
            total_turns=5,
            total_cost=1.23,
        )

        test_db.save_run(run)

        # Retrieve it
        retrieved = test_db.get_run("test-run-001")

        assert retrieved is not None
        assert retrieved.scenario_name == "Test Scenario"
        assert retrieved.total_turns == 5
        assert abs(retrieved.total_cost - 1.23) < 0.01

    def test_list_runs(self, test_db):
        """Test listing runs"""
        # Create multiple runs
        for i in range(3):
            run = Run(
                id=f"test-run-{i:03d}",
                scenario_id="test-scenario",
                scenario_name=f"Test {i}",
                created=datetime.now(),
                status="completed",
                total_turns=i + 1,
                total_cost=float(i),
            )
            test_db.save_run(run)

        # List all runs
        runs = test_db.list_runs()
        assert len(runs) == 3

        # List by scenario
        scenario_runs = test_db.list_runs(scenario_id="test-scenario")
        assert len(scenario_runs) == 3


class TestDatabaseQueries:
    """Test database query methods"""

    @pytest.fixture
    def populated_db(self, test_db):
        """Create a database with test data"""
        session = test_db.get_session()
        try:
            # Create run
            run = Run(
                id="query-test-run",
                scenario_id="query-scenario",
                scenario_name="Query Test",
                created=datetime.now(),
                status="completed",
                total_turns=2,
                total_cost=0.5,
            )
            session.add(run)

            # Create turns
            turn1 = Turn(
                run_id="query-test-run",
                turn_num=1,
                timestamp=datetime.now(),
                world_state="Turn 1 world state",
            )
            session.add(turn1)
            session.flush()

            turn2 = Turn(
                run_id="query-test-run",
                turn_num=2,
                timestamp=datetime.now(),
                world_state="Turn 2 world state",
            )
            session.add(turn2)
            session.flush()

            # Create decisions
            decision1 = Decision(
                turn_id=turn1.id,
                actor="Actor A",
                goals=["Goal 1"],
                reasoning="Reasoning for turn 1",
                action="Action for turn 1",
                timestamp=datetime.now(),
            )
            session.add(decision1)

            decision2 = Decision(
                turn_id=turn2.id,
                actor="Actor A",
                goals=["Goal 2"],
                reasoning="Reasoning for turn 2",
                action="Action for turn 2",
                timestamp=datetime.now(),
            )
            session.add(decision2)

            # Create metrics
            metric1 = Metric(
                turn_id=turn1.id,
                name="cooperation_level",
                value=0.5,
                actor="Actor A",
                timestamp=datetime.now(),
            )
            session.add(metric1)

            metric2 = Metric(
                turn_id=turn2.id,
                name="cooperation_level",
                value=0.7,
                actor="Actor A",
                timestamp=datetime.now(),
            )
            session.add(metric2)

            # Create costs
            cost1 = Cost(
                run_id="query-test-run",
                timestamp=datetime.now(),
                actor="Actor A",
                phase="decision",
                model="test/model",
                input_tokens=100,
                output_tokens=50,
                cost=0.25,
            )
            session.add(cost1)

            session.commit()

        finally:
            session.close()

        return test_db

    def test_query_decisions_for_actor(self, populated_db):
        """Test querying decisions by actor"""
        decisions = populated_db.query_decisions_for_actor("Actor A")

        assert len(decisions) == 2
        assert decisions[0].action == "Action for turn 1"
        assert decisions[1].action == "Action for turn 2"

    def test_query_metrics(self, populated_db):
        """Test querying metrics"""
        metrics = populated_db.query_metrics(metric_name="cooperation_level")

        assert len(metrics) == 2
        assert metrics[0].value == 0.5
        assert metrics[1].value == 0.7

    def test_get_run_statistics(self, populated_db):
        """Test getting run statistics"""
        stats = populated_db.get_run_statistics("query-test-run")

        assert stats["run_id"] == "query-test-run"
        # Implementation returns "scenario" key, not "scenario_name"
        assert stats["scenario"] == "Query Test"
        assert stats["turns"] == 2
        assert stats["decisions"] == 2
        assert abs(stats["total_cost"] - 0.5) < 0.01

        # Check cost breakdown
        assert "cost_by_phase" in stats
        assert len(stats["cost_by_phase"]) > 0


class TestDatabaseAnalytics:
    """Test analytics methods"""

    @pytest.fixture
    def analytics_db(self, test_db):
        """Create database with data for analytics"""
        session = test_db.get_session()
        try:
            # Create multiple runs
            for run_num in range(3):
                run = Run(
                    id=f"analytics-run-{run_num:03d}",
                    scenario_id="analytics-scenario",
                    scenario_name=f"Analytics Test {run_num}",
                    created=datetime.now(),
                    status="completed",
                    total_turns=2,
                    total_cost=float(run_num) * 0.5,
                )
                session.add(run)

                # Create turns with metrics
                for turn_num in [1, 2]:
                    turn = Turn(
                        run_id=run.id,
                        turn_num=turn_num,
                        timestamp=datetime.now(),
                        world_state=f"World state for run {run_num}, turn {turn_num}",
                    )
                    session.add(turn)
                    session.flush()

                    # Add metric
                    metric = Metric(
                        turn_id=turn.id,
                        name="test_metric",
                        value=float(run_num + turn_num),
                        timestamp=datetime.now(),
                    )
                    session.add(metric)

            session.commit()

        finally:
            session.close()

        return test_db

    def test_compare_runs(self, analytics_db):
        """Test comparing multiple runs"""
        comparison = analytics_db.compare_runs([
            "analytics-run-000",
            "analytics-run-001",
            "analytics-run-002",
        ])

        assert "runs" in comparison
        assert len(comparison["runs"]) == 3

        # Check that runs are in order
        assert comparison["runs"][0]["run_id"] == "analytics-run-000"
        assert comparison["runs"][1]["run_id"] == "analytics-run-001"
        assert comparison["runs"][2]["run_id"] == "analytics-run-002"

    def test_aggregate_metrics(self, analytics_db):
        """Test metric aggregation"""
        agg = analytics_db.aggregate_metrics(
            "test_metric",
            scenario="analytics-scenario"
        )

        assert agg["metric"] == "test_metric"
        assert agg["count"] == 6  # 3 runs × 2 turns
        assert agg["min"] is not None
        assert agg["max"] is not None
        assert agg["avg"] is not None

        # Min should be 1.0 (run 0, turn 1)
        assert abs(agg["min"] - 1.0) < 0.01
        # Max should be 4.0 (run 2, turn 2)
        assert abs(agg["max"] - 4.0) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
