"""
Database models for Scenario Lab V2

SQLAlchemy ORM models for persisting scenario runs, turns, decisions, metrics, etc.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, Session
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class Run(Base):
    """Represents a complete scenario run"""

    __tablename__ = "runs"

    id = Column(String, primary_key=True)  # e.g., "run-20250119-123456"
    scenario_id = Column(String, nullable=False, index=True)
    scenario_name = Column(String, nullable=False)
    created = Column(DateTime, nullable=False, default=datetime.now)
    status = Column(String, nullable=False)  # initialized, running, completed, halted, failed
    total_turns = Column(Integer, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0.0)
    config = Column(JSON)  # Scenario configuration

    # Relationships
    turns = relationship("Turn", back_populates="run", cascade="all, delete-orphan")
    costs = relationship("Cost", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Run(id='{self.id}', scenario='{self.scenario_name}', turns={self.total_turns}, cost=${self.total_cost:.2f})>"


class Turn(Base):
    """Represents a single turn in a scenario run"""

    __tablename__ = "turns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False, index=True)
    turn_num = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    world_state = Column(Text)  # Markdown content

    # Relationships
    run = relationship("Run", back_populates="turns")
    decisions = relationship("Decision", back_populates="turn", cascade="all, delete-orphan")
    communications = relationship(
        "Communication", back_populates="turn", cascade="all, delete-orphan"
    )
    metrics = relationship("Metric", back_populates="turn", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Turn(run_id='{self.run_id}', turn={self.turn_num})>"


class Decision(Base):
    """Represents an actor's decision in a turn"""

    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    turn_id = Column(Integer, ForeignKey("turns.id"), nullable=False, index=True)
    actor = Column(String, nullable=False, index=True)
    goals = Column(JSON)  # List of goal strings
    reasoning = Column(Text)
    action = Column(Text)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)

    # Relationships
    turn = relationship("Turn", back_populates="decisions")

    def __repr__(self) -> str:
        return f"<Decision(turn_id={self.turn_id}, actor='{self.actor}')>"


class Communication(Base):
    """Represents a communication between actors"""

    __tablename__ = "communications"

    id = Column(String, primary_key=True)  # channel_id
    turn_id = Column(Integer, ForeignKey("turns.id"), nullable=False, index=True)
    type = Column(String, nullable=False)  # bilateral, coalition, public
    sender = Column(String, nullable=False, index=True)
    recipients = Column(JSON)  # List of recipient names
    content = Column(Text)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)

    # Relationships
    turn = relationship("Turn", back_populates="communications")

    def __repr__(self) -> str:
        return f"<Communication(id='{self.id}', type='{self.type}', sender='{self.sender}')>"


class Metric(Base):
    """Represents a metric value extracted from a turn"""

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    turn_id = Column(Integer, ForeignKey("turns.id"), nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    actor = Column(String, nullable=True, index=True)  # Null for scenario-level metrics
    timestamp = Column(DateTime, nullable=False, default=datetime.now)

    # Relationships
    turn = relationship("Turn", back_populates="metrics")

    def __repr__(self) -> str:
        actor_str = f", actor='{self.actor}'" if self.actor else ""
        return f"<Metric(name='{self.name}', value={self.value}{actor_str})>"


class Cost(Base):
    """Represents a cost record for LLM API calls"""

    __tablename__ = "costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("runs.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    actor = Column(String, nullable=False, index=True)  # Or "world_state_updater"
    phase = Column(String, nullable=False, index=True)  # communication, decision, world_update
    model = Column(String, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)

    # Relationships
    run = relationship("Run", back_populates="costs")

    def __repr__(self) -> str:
        return f"<Cost(actor='{self.actor}', phase='{self.phase}', cost=${self.cost:.4f})>"


class Database:
    """
    Database manager for Scenario Lab V2

    Provides high-level API for persisting and querying scenario data.
    """

    def __init__(self, db_url: str = "sqlite:///scenario-lab.db"):
        """
        Initialize database connection

        Args:
            db_url: SQLAlchemy database URL
        """
        # Use StaticPool for SQLite to avoid threading issues
        if db_url.startswith("sqlite"):
            self.engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            self.engine = create_engine(db_url)

        # Create tables
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a new database session"""
        from sqlalchemy.orm import sessionmaker

        SessionLocal = sessionmaker(bind=self.engine)
        return SessionLocal()

    def save_run(self, run: Run) -> None:
        """Save a run to the database"""
        session = self.get_session()
        try:
            session.add(run)
            session.commit()
        finally:
            session.close()

    def get_run(self, run_id: str) -> Optional[Run]:
        """Get a run by ID"""
        session = self.get_session()
        try:
            return session.query(Run).filter(Run.id == run_id).first()
        finally:
            session.close()

    def list_runs(self, scenario_id: Optional[str] = None) -> List[Run]:
        """List all runs, optionally filtered by scenario"""
        session = self.get_session()
        try:
            query = session.query(Run)
            if scenario_id:
                query = query.filter(Run.scenario_id == scenario_id)
            return query.order_by(Run.created.desc()).all()
        finally:
            session.close()

    def query_metrics(
        self,
        scenario: Optional[str] = None,
        actor: Optional[str] = None,
        metric_name: Optional[str] = None,
    ) -> List[Metric]:
        """
        Query metrics with optional filters

        Args:
            scenario: Filter by scenario ID
            actor: Filter by actor name
            metric_name: Filter by metric name

        Returns:
            List of metrics matching filters
        """
        session = self.get_session()
        try:
            query = session.query(Metric).join(Turn).join(Run)

            if scenario:
                query = query.filter(Run.scenario_id == scenario)
            if actor:
                query = query.filter(Metric.actor == actor)
            if metric_name:
                query = query.filter(Metric.name == metric_name)

            return query.order_by(Metric.timestamp).all()
        finally:
            session.close()

    def query_decisions_for_actor(
        self, actor: str, scenario: Optional[str] = None
    ) -> List[Decision]:
        """
        Get all decisions made by an actor

        Args:
            actor: Actor name
            scenario: Optional scenario filter

        Returns:
            List of decisions
        """
        session = self.get_session()
        try:
            query = session.query(Decision).join(Turn).join(Run)
            query = query.filter(Decision.actor == actor)

            if scenario:
                query = query.filter(Run.scenario_id == scenario)

            return query.order_by(Turn.turn_num).all()
        finally:
            session.close()

    def get_run_statistics(self, run_id: str) -> dict:
        """
        Get comprehensive statistics for a run

        Args:
            run_id: Run identifier

        Returns:
            Dictionary with run statistics
        """
        session = self.get_session()
        try:
            run = session.query(Run).filter(Run.id == run_id).first()
            if not run:
                return {}

            # Count entities
            turn_count = session.query(Turn).filter(Turn.run_id == run_id).count()
            decision_count = (
                session.query(Decision).join(Turn).filter(Turn.run_id == run_id).count()
            )
            comm_count = (
                session.query(Communication)
                .join(Turn)
                .filter(Turn.run_id == run_id)
                .count()
            )
            metric_count = (
                session.query(Metric).join(Turn).filter(Turn.run_id == run_id).count()
            )

            # Cost breakdown
            cost_by_phase = {}
            costs = session.query(Cost).filter(Cost.run_id == run_id).all()
            for cost in costs:
                if cost.phase not in cost_by_phase:
                    cost_by_phase[cost.phase] = 0.0
                cost_by_phase[cost.phase] += cost.cost

            return {
                "run_id": run.id,
                "scenario": run.scenario_name,
                "status": run.status,
                "turns": turn_count,
                "decisions": decision_count,
                "communications": comm_count,
                "metrics": metric_count,
                "total_cost": run.total_cost,
                "cost_by_phase": cost_by_phase,
                "created": run.created,
            }
        finally:
            session.close()

    def compare_runs(self, run_ids: List[str]) -> dict:
        """
        Compare multiple runs side by side

        Args:
            run_ids: List of run IDs to compare

        Returns:
            Comparison statistics
        """
        session = self.get_session()
        try:
            runs = session.query(Run).filter(Run.id.in_(run_ids)).all()

            comparison = {"runs": []}
            for run in runs:
                stats = self.get_run_statistics(run.id)
                comparison["runs"].append(stats)

            return comparison
        finally:
            session.close()

    def aggregate_metrics(
        self, metric_name: str, scenario: Optional[str] = None
    ) -> dict:
        """
        Aggregate a metric across runs

        Args:
            metric_name: Name of metric to aggregate
            scenario: Optional scenario filter

        Returns:
            Aggregation results (min, max, avg, count)
        """
        from sqlalchemy import func

        session = self.get_session()
        try:
            query = session.query(
                func.min(Metric.value).label("min"),
                func.max(Metric.value).label("max"),
                func.avg(Metric.value).label("avg"),
                func.count(Metric.value).label("count"),
            )

            query = query.join(Turn).join(Run).filter(Metric.name == metric_name)

            if scenario:
                query = query.filter(Run.scenario_id == scenario)

            result = query.first()

            return {
                "metric": metric_name,
                "min": float(result.min) if result.min is not None else None,
                "max": float(result.max) if result.max is not None else None,
                "avg": float(result.avg) if result.avg is not None else None,
                "count": int(result.count) if result.count is not None else 0,
                "scenario": scenario,
            }
        finally:
            session.close()
