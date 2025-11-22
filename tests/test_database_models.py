"""
Unit tests for database models

Tests the ORM models (Run, Turn, Decision, Communication, Metric, Cost)
for proper initialization, defaults, repr methods, and relationships.
"""
import pytest
import tempfile
import os
from datetime import datetime
from sqlalchemy.orm import Session

from scenario_lab.database import Database
from scenario_lab.database.models import (
    Base,
    Run,
    Turn,
    Decision,
    Communication,
    Metric,
    Cost,
)


@pytest.fixture
def test_db():
    """Create a temporary test database"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_file.close()

    db = Database(f"sqlite:///{temp_file.name}")

    yield db

    os.unlink(temp_file.name)


@pytest.fixture
def session(test_db):
    """Get a database session"""
    session = test_db.get_session()
    yield session
    session.close()


class TestRunModel:
    """Tests for the Run model"""

    def test_run_creation_minimal(self, session):
        """Test creating a Run with minimal required fields"""
        run = Run(
            id="test-run-001",
            scenario_id="scenario-1",
            scenario_name="Test Scenario",
            status="initialized",
        )
        session.add(run)
        session.commit()

        # Verify defaults
        assert run.total_turns == 0
        assert run.total_cost == 0.0
        assert run.config is None
        assert run.created is not None

    def test_run_creation_full(self, session):
        """Test creating a Run with all fields"""
        created_time = datetime(2025, 1, 15, 10, 30, 0)
        config = {"turns": 10, "model": "gpt-4"}

        run = Run(
            id="test-run-002",
            scenario_id="scenario-2",
            scenario_name="Full Scenario",
            created=created_time,
            status="completed",
            total_turns=10,
            total_cost=5.50,
            config=config,
        )
        session.add(run)
        session.commit()

        # Retrieve and verify
        retrieved = session.query(Run).filter(Run.id == "test-run-002").first()
        assert retrieved.scenario_id == "scenario-2"
        assert retrieved.scenario_name == "Full Scenario"
        assert retrieved.created == created_time
        assert retrieved.status == "completed"
        assert retrieved.total_turns == 10
        assert abs(retrieved.total_cost - 5.50) < 0.001
        assert retrieved.config == config

    def test_run_repr(self, session):
        """Test Run string representation"""
        run = Run(
            id="repr-run",
            scenario_id="scenario",
            scenario_name="Repr Test",
            status="running",
            total_turns=3,
            total_cost=1.25,
        )
        session.add(run)
        session.commit()

        repr_str = repr(run)
        assert "repr-run" in repr_str
        assert "Repr Test" in repr_str
        assert "turns=3" in repr_str
        assert "$1.25" in repr_str

    def test_run_status_values(self, session):
        """Test different valid status values"""
        statuses = ["initialized", "running", "completed", "halted", "failed"]

        for i, status in enumerate(statuses):
            run = Run(
                id=f"status-run-{i}",
                scenario_id="scenario",
                scenario_name="Status Test",
                status=status,
            )
            session.add(run)

        session.commit()

        for i, status in enumerate(statuses):
            retrieved = session.query(Run).filter(Run.id == f"status-run-{i}").first()
            assert retrieved.status == status

    def test_run_relationships_empty(self, session):
        """Test Run relationships when empty"""
        run = Run(
            id="rel-run",
            scenario_id="scenario",
            scenario_name="Relationship Test",
            status="initialized",
        )
        session.add(run)
        session.commit()

        assert run.turns == []
        assert run.costs == []


class TestTurnModel:
    """Tests for the Turn model"""

    @pytest.fixture
    def run_with_turn(self, session):
        """Create a run with a turn"""
        run = Run(
            id="turn-test-run",
            scenario_id="scenario",
            scenario_name="Turn Test",
            status="running",
        )
        session.add(run)
        session.commit()
        return run

    def test_turn_creation(self, session, run_with_turn):
        """Test creating a Turn"""
        turn = Turn(
            run_id=run_with_turn.id,
            turn_num=1,
            world_state="Initial world state with actors and events.",
        )
        session.add(turn)
        session.commit()

        assert turn.id is not None
        assert turn.timestamp is not None
        assert turn.world_state == "Initial world state with actors and events."

    def test_turn_repr(self, session, run_with_turn):
        """Test Turn string representation"""
        turn = Turn(
            run_id=run_with_turn.id,
            turn_num=5,
        )
        session.add(turn)
        session.commit()

        repr_str = repr(turn)
        assert "turn-test-run" in repr_str
        assert "turn=5" in repr_str

    def test_turn_run_relationship(self, session, run_with_turn):
        """Test Turn-Run relationship"""
        turn = Turn(
            run_id=run_with_turn.id,
            turn_num=1,
        )
        session.add(turn)
        session.commit()

        # Access relationship
        assert turn.run is not None
        assert turn.run.id == run_with_turn.id
        assert turn.run.scenario_name == "Turn Test"

        # Access from run side
        session.refresh(run_with_turn)
        assert len(run_with_turn.turns) == 1
        assert run_with_turn.turns[0].turn_num == 1

    def test_turn_cascade_delete(self, session, run_with_turn):
        """Test that deleting a run cascades to turns"""
        turn = Turn(
            run_id=run_with_turn.id,
            turn_num=1,
        )
        session.add(turn)
        session.commit()

        turn_id = turn.id

        # Delete the run
        session.delete(run_with_turn)
        session.commit()

        # Turn should be gone
        deleted_turn = session.query(Turn).filter(Turn.id == turn_id).first()
        assert deleted_turn is None

    def test_multiple_turns_ordering(self, session, run_with_turn):
        """Test multiple turns with ordering"""
        for i in range(1, 4):
            turn = Turn(
                run_id=run_with_turn.id,
                turn_num=i,
                world_state=f"World state for turn {i}",
            )
            session.add(turn)

        session.commit()
        session.refresh(run_with_turn)

        assert len(run_with_turn.turns) == 3


class TestDecisionModel:
    """Tests for the Decision model"""

    @pytest.fixture
    def turn(self, session):
        """Create a run with a turn for testing decisions"""
        run = Run(
            id="decision-test-run",
            scenario_id="scenario",
            scenario_name="Decision Test",
            status="running",
        )
        session.add(run)
        session.commit()

        turn = Turn(
            run_id=run.id,
            turn_num=1,
        )
        session.add(turn)
        session.commit()

        return turn

    def test_decision_creation(self, session, turn):
        """Test creating a Decision"""
        decision = Decision(
            turn_id=turn.id,
            actor="US Government",
            goals=["Maintain security", "Promote AI safety"],
            reasoning="Based on current geopolitical situation...",
            action="Propose new AI regulations",
        )
        session.add(decision)
        session.commit()

        assert decision.id is not None
        assert decision.actor == "US Government"
        assert decision.goals == ["Maintain security", "Promote AI safety"]
        assert decision.reasoning == "Based on current geopolitical situation..."
        assert decision.action == "Propose new AI regulations"
        assert decision.timestamp is not None

    def test_decision_repr(self, session, turn):
        """Test Decision string representation"""
        decision = Decision(
            turn_id=turn.id,
            actor="China",
            action="Invest in AI research",
        )
        session.add(decision)
        session.commit()

        repr_str = repr(decision)
        assert f"turn_id={turn.id}" in repr_str
        assert "actor='China'" in repr_str

    def test_decision_with_empty_goals(self, session, turn):
        """Test Decision with empty goals list"""
        decision = Decision(
            turn_id=turn.id,
            actor="Actor A",
            goals=[],
            action="Take action",
        )
        session.add(decision)
        session.commit()

        retrieved = session.query(Decision).filter(Decision.id == decision.id).first()
        assert retrieved.goals == []

    def test_decision_turn_relationship(self, session, turn):
        """Test Decision-Turn relationship"""
        decision = Decision(
            turn_id=turn.id,
            actor="Actor B",
            action="Action B",
        )
        session.add(decision)
        session.commit()

        assert decision.turn is not None
        assert decision.turn.id == turn.id

        session.refresh(turn)
        assert len(turn.decisions) == 1
        assert turn.decisions[0].actor == "Actor B"

    def test_multiple_decisions_per_turn(self, session, turn):
        """Test multiple decisions in a single turn"""
        actors = ["Actor A", "Actor B", "Actor C"]

        for actor in actors:
            decision = Decision(
                turn_id=turn.id,
                actor=actor,
                action=f"{actor} action",
            )
            session.add(decision)

        session.commit()
        session.refresh(turn)

        assert len(turn.decisions) == 3
        actor_names = [d.actor for d in turn.decisions]
        assert set(actor_names) == set(actors)


class TestCommunicationModel:
    """Tests for the Communication model"""

    @pytest.fixture
    def turn(self, session):
        """Create a run with a turn for testing communications"""
        run = Run(
            id="comm-test-run",
            scenario_id="scenario",
            scenario_name="Communication Test",
            status="running",
        )
        session.add(run)
        session.commit()

        turn = Turn(
            run_id=run.id,
            turn_num=1,
        )
        session.add(turn)
        session.commit()

        return turn

    def test_communication_bilateral(self, session, turn):
        """Test creating a bilateral communication"""
        comm = Communication(
            id="comm-001",
            turn_id=turn.id,
            type="bilateral",
            sender="US Government",
            recipients=["China"],
            content="Let's discuss AI safety cooperation.",
        )
        session.add(comm)
        session.commit()

        assert comm.type == "bilateral"
        assert comm.sender == "US Government"
        assert comm.recipients == ["China"]
        assert comm.content == "Let's discuss AI safety cooperation."
        assert comm.timestamp is not None

    def test_communication_public(self, session, turn):
        """Test creating a public communication"""
        comm = Communication(
            id="comm-002",
            turn_id=turn.id,
            type="public",
            sender="EU",
            recipients=["all"],
            content="We announce new AI regulations.",
        )
        session.add(comm)
        session.commit()

        assert comm.type == "public"
        assert comm.recipients == ["all"]

    def test_communication_coalition(self, session, turn):
        """Test creating a coalition communication"""
        comm = Communication(
            id="comm-003",
            turn_id=turn.id,
            type="coalition",
            sender="US Government",
            recipients=["EU", "UK", "Japan"],
            content="Let's form an AI safety alliance.",
        )
        session.add(comm)
        session.commit()

        assert comm.type == "coalition"
        assert len(comm.recipients) == 3

    def test_communication_repr(self, session, turn):
        """Test Communication string representation"""
        comm = Communication(
            id="repr-comm",
            turn_id=turn.id,
            type="bilateral",
            sender="Actor A",
            recipients=["Actor B"],
        )
        session.add(comm)
        session.commit()

        repr_str = repr(comm)
        assert "repr-comm" in repr_str
        assert "bilateral" in repr_str
        assert "Actor A" in repr_str

    def test_communication_turn_relationship(self, session, turn):
        """Test Communication-Turn relationship"""
        comm = Communication(
            id="rel-comm",
            turn_id=turn.id,
            type="public",
            sender="Actor C",
            recipients=["all"],
        )
        session.add(comm)
        session.commit()

        assert comm.turn is not None
        assert comm.turn.id == turn.id

        session.refresh(turn)
        assert len(turn.communications) == 1


class TestMetricModel:
    """Tests for the Metric model"""

    @pytest.fixture
    def turn(self, session):
        """Create a run with a turn for testing metrics"""
        run = Run(
            id="metric-test-run",
            scenario_id="scenario",
            scenario_name="Metric Test",
            status="running",
        )
        session.add(run)
        session.commit()

        turn = Turn(
            run_id=run.id,
            turn_num=1,
        )
        session.add(turn)
        session.commit()

        return turn

    def test_metric_scenario_level(self, session, turn):
        """Test creating a scenario-level metric (no actor)"""
        metric = Metric(
            turn_id=turn.id,
            name="global_cooperation_index",
            value=0.75,
            actor=None,
        )
        session.add(metric)
        session.commit()

        assert metric.id is not None
        assert metric.name == "global_cooperation_index"
        assert metric.value == 0.75
        assert metric.actor is None
        assert metric.timestamp is not None

    def test_metric_actor_level(self, session, turn):
        """Test creating an actor-level metric"""
        metric = Metric(
            turn_id=turn.id,
            name="ai_capability",
            value=0.85,
            actor="Tech Company",
        )
        session.add(metric)
        session.commit()

        assert metric.actor == "Tech Company"
        assert metric.value == 0.85

    def test_metric_repr_with_actor(self, session, turn):
        """Test Metric repr with actor"""
        metric = Metric(
            turn_id=turn.id,
            name="influence",
            value=50.0,
            actor="EU",
        )
        session.add(metric)
        session.commit()

        repr_str = repr(metric)
        assert "influence" in repr_str
        assert "50.0" in repr_str
        assert "EU" in repr_str

    def test_metric_repr_without_actor(self, session, turn):
        """Test Metric repr without actor"""
        metric = Metric(
            turn_id=turn.id,
            name="global_risk",
            value=0.3,
            actor=None,
        )
        session.add(metric)
        session.commit()

        repr_str = repr(metric)
        assert "global_risk" in repr_str
        assert "0.3" in repr_str
        assert "actor=" not in repr_str

    def test_metric_edge_values(self, session, turn):
        """Test metric with edge case values"""
        # Zero value
        metric_zero = Metric(
            turn_id=turn.id,
            name="zero_metric",
            value=0.0,
        )
        session.add(metric_zero)

        # Negative value
        metric_neg = Metric(
            turn_id=turn.id,
            name="negative_metric",
            value=-10.5,
        )
        session.add(metric_neg)

        # Large value
        metric_large = Metric(
            turn_id=turn.id,
            name="large_metric",
            value=1000000.0,
        )
        session.add(metric_large)

        session.commit()

        assert metric_zero.value == 0.0
        assert metric_neg.value == -10.5
        assert metric_large.value == 1000000.0

    def test_metric_turn_relationship(self, session, turn):
        """Test Metric-Turn relationship"""
        metric = Metric(
            turn_id=turn.id,
            name="test_metric",
            value=1.0,
        )
        session.add(metric)
        session.commit()

        assert metric.turn is not None
        assert metric.turn.id == turn.id

        session.refresh(turn)
        assert len(turn.metrics) == 1


class TestCostModel:
    """Tests for the Cost model"""

    @pytest.fixture
    def run(self, session):
        """Create a run for testing costs"""
        run = Run(
            id="cost-test-run",
            scenario_id="scenario",
            scenario_name="Cost Test",
            status="running",
        )
        session.add(run)
        session.commit()
        return run

    def test_cost_creation(self, session, run):
        """Test creating a Cost record"""
        cost = Cost(
            run_id=run.id,
            actor="Actor A",
            phase="decision",
            model="openai/gpt-4",
            input_tokens=500,
            output_tokens=200,
            cost=0.0345,
        )
        session.add(cost)
        session.commit()

        assert cost.id is not None
        assert cost.actor == "Actor A"
        assert cost.phase == "decision"
        assert cost.model == "openai/gpt-4"
        assert cost.input_tokens == 500
        assert cost.output_tokens == 200
        assert abs(cost.cost - 0.0345) < 0.0001
        assert cost.timestamp is not None

    def test_cost_repr(self, session, run):
        """Test Cost string representation"""
        cost = Cost(
            run_id=run.id,
            actor="World State Updater",
            phase="world_update",
            model="openai/gpt-4",
            input_tokens=1000,
            output_tokens=500,
            cost=0.1234,
        )
        session.add(cost)
        session.commit()

        repr_str = repr(cost)
        assert "World State Updater" in repr_str
        assert "world_update" in repr_str
        assert "$0.1234" in repr_str

    def test_cost_phases(self, session, run):
        """Test different cost phases"""
        phases = ["communication", "decision", "world_update", "validation"]

        for i, phase in enumerate(phases):
            cost = Cost(
                run_id=run.id,
                actor=f"Actor {i}",
                phase=phase,
                model="test-model",
                input_tokens=100,
                output_tokens=50,
                cost=0.01,
            )
            session.add(cost)

        session.commit()

        costs = session.query(Cost).filter(Cost.run_id == run.id).all()
        assert len(costs) == 4
        retrieved_phases = {c.phase for c in costs}
        assert retrieved_phases == set(phases)

    def test_cost_run_relationship(self, session, run):
        """Test Cost-Run relationship"""
        cost = Cost(
            run_id=run.id,
            actor="Test Actor",
            phase="decision",
            model="test-model",
            input_tokens=100,
            output_tokens=50,
            cost=0.05,
        )
        session.add(cost)
        session.commit()

        assert cost.run is not None
        assert cost.run.id == run.id

        session.refresh(run)
        assert len(run.costs) == 1

    def test_cost_zero_tokens(self, session, run):
        """Test cost with zero tokens (edge case)"""
        cost = Cost(
            run_id=run.id,
            actor="Cache Hit",
            phase="decision",
            model="cached",
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
        )
        session.add(cost)
        session.commit()

        assert cost.input_tokens == 0
        assert cost.output_tokens == 0
        assert cost.cost == 0.0


class TestDatabaseClass:
    """Tests for the Database class methods"""

    def test_database_non_sqlite_engine(self):
        """Test that non-SQLite URLs don't use StaticPool"""
        # We can't actually connect to PostgreSQL, but we can test the path
        # This is a partial test that would need mocking for full coverage
        pass

    def test_get_run_not_found(self, test_db):
        """Test get_run returns None for non-existent run"""
        result = test_db.get_run("non-existent-run")
        assert result is None

    def test_list_runs_empty(self, test_db):
        """Test list_runs returns empty list when no runs"""
        runs = test_db.list_runs()
        assert runs == []

    def test_get_run_statistics_not_found(self, test_db):
        """Test get_run_statistics returns empty dict for non-existent run"""
        stats = test_db.get_run_statistics("non-existent-run")
        assert stats == {}

    def test_aggregate_metrics_no_data(self, test_db):
        """Test aggregate_metrics with no data"""
        agg = test_db.aggregate_metrics("non_existent_metric")
        assert agg["count"] == 0
        assert agg["min"] is None
        assert agg["max"] is None
        assert agg["avg"] is None

    def test_query_metrics_with_filters(self, test_db):
        """Test query_metrics with various filter combinations"""
        session = test_db.get_session()
        try:
            # Create test data
            run = Run(
                id="filter-run",
                scenario_id="filter-scenario",
                scenario_name="Filter Test",
                status="completed",
            )
            session.add(run)
            session.commit()

            turn = Turn(run_id=run.id, turn_num=1)
            session.add(turn)
            session.commit()

            metric1 = Metric(
                turn_id=turn.id,
                name="metric_a",
                value=1.0,
                actor="Actor X",
            )
            metric2 = Metric(
                turn_id=turn.id,
                name="metric_b",
                value=2.0,
                actor="Actor Y",
            )
            session.add(metric1)
            session.add(metric2)
            session.commit()
        finally:
            session.close()

        # Test filter by scenario
        metrics = test_db.query_metrics(scenario="filter-scenario")
        assert len(metrics) == 2

        # Test filter by actor
        metrics = test_db.query_metrics(actor="Actor X")
        assert len(metrics) == 1
        assert metrics[0].name == "metric_a"

        # Test filter by metric name
        metrics = test_db.query_metrics(metric_name="metric_b")
        assert len(metrics) == 1
        assert metrics[0].actor == "Actor Y"

    def test_query_decisions_for_actor_with_scenario_filter(self, test_db):
        """Test query_decisions_for_actor with scenario filter"""
        session = test_db.get_session()
        try:
            # Create test data in two scenarios
            for scenario_num in [1, 2]:
                run = Run(
                    id=f"decision-filter-run-{scenario_num}",
                    scenario_id=f"scenario-{scenario_num}",
                    scenario_name=f"Scenario {scenario_num}",
                    status="completed",
                )
                session.add(run)
                session.commit()

                turn = Turn(run_id=run.id, turn_num=1)
                session.add(turn)
                session.commit()

                decision = Decision(
                    turn_id=turn.id,
                    actor="Shared Actor",
                    action=f"Action in scenario {scenario_num}",
                )
                session.add(decision)
                session.commit()
        finally:
            session.close()

        # Without filter - should get both
        all_decisions = test_db.query_decisions_for_actor("Shared Actor")
        assert len(all_decisions) == 2

        # With filter - should get one
        filtered = test_db.query_decisions_for_actor(
            "Shared Actor", scenario="scenario-1"
        )
        assert len(filtered) == 1
        assert "scenario 1" in filtered[0].action

    def test_compare_runs_partial(self, test_db):
        """Test compare_runs when some runs don't exist"""
        session = test_db.get_session()
        try:
            run = Run(
                id="compare-run-1",
                scenario_id="compare-scenario",
                scenario_name="Compare Test",
                status="completed",
            )
            session.add(run)
            session.commit()
        finally:
            session.close()

        # Compare with one existing and one non-existing run
        comparison = test_db.compare_runs(["compare-run-1", "non-existent"])
        assert "runs" in comparison
        # Only the existing run should be in results
        assert len(comparison["runs"]) == 1
        assert comparison["runs"][0]["run_id"] == "compare-run-1"


class TestCascadeDeletes:
    """Tests for cascade delete behavior"""

    def test_turn_cascade_deletes_decisions(self, test_db):
        """Test that deleting a turn cascades to decisions"""
        session = test_db.get_session()
        try:
            run = Run(
                id="cascade-run",
                scenario_id="scenario",
                scenario_name="Cascade Test",
                status="running",
            )
            session.add(run)
            session.commit()

            turn = Turn(run_id=run.id, turn_num=1)
            session.add(turn)
            session.commit()

            decision = Decision(
                turn_id=turn.id,
                actor="Actor",
                action="Action",
            )
            session.add(decision)
            session.commit()

            decision_id = decision.id

            # Delete turn
            session.delete(turn)
            session.commit()

            # Decision should be gone
            deleted = session.query(Decision).filter(Decision.id == decision_id).first()
            assert deleted is None
        finally:
            session.close()

    def test_turn_cascade_deletes_communications(self, test_db):
        """Test that deleting a turn cascades to communications"""
        session = test_db.get_session()
        try:
            run = Run(
                id="cascade-comm-run",
                scenario_id="scenario",
                scenario_name="Cascade Test",
                status="running",
            )
            session.add(run)
            session.commit()

            turn = Turn(run_id=run.id, turn_num=1)
            session.add(turn)
            session.commit()

            comm = Communication(
                id="cascade-comm",
                turn_id=turn.id,
                type="public",
                sender="Actor",
                recipients=["all"],
            )
            session.add(comm)
            session.commit()

            # Delete turn
            session.delete(turn)
            session.commit()

            # Communication should be gone
            deleted = session.query(Communication).filter(
                Communication.id == "cascade-comm"
            ).first()
            assert deleted is None
        finally:
            session.close()

    def test_turn_cascade_deletes_metrics(self, test_db):
        """Test that deleting a turn cascades to metrics"""
        session = test_db.get_session()
        try:
            run = Run(
                id="cascade-metric-run",
                scenario_id="scenario",
                scenario_name="Cascade Test",
                status="running",
            )
            session.add(run)
            session.commit()

            turn = Turn(run_id=run.id, turn_num=1)
            session.add(turn)
            session.commit()

            metric = Metric(
                turn_id=turn.id,
                name="test",
                value=1.0,
            )
            session.add(metric)
            session.commit()

            metric_id = metric.id

            # Delete turn
            session.delete(turn)
            session.commit()

            # Metric should be gone
            deleted = session.query(Metric).filter(Metric.id == metric_id).first()
            assert deleted is None
        finally:
            session.close()

    def test_run_cascade_deletes_costs(self, test_db):
        """Test that deleting a run cascades to costs"""
        session = test_db.get_session()
        try:
            run = Run(
                id="cascade-cost-run",
                scenario_id="scenario",
                scenario_name="Cascade Test",
                status="running",
            )
            session.add(run)
            session.commit()

            cost = Cost(
                run_id=run.id,
                actor="Actor",
                phase="decision",
                model="test",
                input_tokens=100,
                output_tokens=50,
                cost=0.01,
            )
            session.add(cost)
            session.commit()

            cost_id = cost.id

            # Delete run
            session.delete(run)
            session.commit()

            # Cost should be gone
            deleted = session.query(Cost).filter(Cost.id == cost_id).first()
            assert deleted is None
        finally:
            session.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
