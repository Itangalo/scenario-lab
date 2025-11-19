"""
Database Persistence Phase Service for Scenario Lab V2

Persists scenario data to SQLite database for analytics while maintaining markdown files.
"""
from __future__ import annotations
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from scenario_lab.models.state import ScenarioState
from scenario_lab.database.models import (
    Database,
    Run,
    Turn,
    Decision as DBDecision,
    Communication as DBCommunication,
    Metric as DBMetric,
    Cost as DBCost,
)

logger = logging.getLogger(__name__)


class DatabasePersistencePhase:
    """
    Phase service for database persistence

    This phase:
    1. Persists run metadata to database
    2. Persists turn data (world state, decisions, communications)
    3. Persists metrics and costs
    4. Complements (not replaces) markdown file persistence
    """

    def __init__(self, database: Database):
        """
        Initialize database persistence phase

        Args:
            database: Database instance
        """
        self.database = database

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """
        Execute database persistence phase

        Args:
            state: Current immutable scenario state

        Returns:
            Same scenario state (persistence doesn't modify state)
        """
        logger.info(f"Executing database persistence for turn {state.turn}")

        session = self.database.get_session()
        try:
            # Get or create run
            run = session.query(Run).filter(Run.id == state.run_id).first()
            if not run:
                run = Run(
                    id=state.run_id,
                    scenario_id=state.scenario_id,
                    scenario_name=state.scenario_name,
                    created=datetime.now(),
                    status=state.status.value,
                    total_turns=0,
                    total_cost=0.0,
                    config=state.scenario_config,
                )
                session.add(run)
                logger.debug(f"Created new run record: {run.id}")

            # Update run status and totals
            run.status = state.status.value
            run.total_turns = state.turn
            run.total_cost = state.total_cost()

            # Create turn record
            turn = Turn(
                run_id=state.run_id,
                turn_num=state.turn,
                timestamp=datetime.now(),
                world_state=state.world_state.content,
            )
            session.add(turn)
            session.flush()  # Get turn.id
            logger.debug(f"Created turn record: {turn.turn_num}")

            # Persist decisions
            for actor_name, decision in state.decisions.items():
                db_decision = DBDecision(
                    turn_id=turn.id,
                    actor=actor_name,
                    goals=decision.goals,
                    reasoning=decision.reasoning,
                    action=decision.action,
                    timestamp=datetime.now(),
                )
                session.add(db_decision)
            logger.debug(f"Persisted {len(state.decisions)} decisions")

            # Persist communications for this turn
            turn_communications = [
                c for c in state.communications if c.turn == state.turn
            ]
            for comm in turn_communications:
                db_comm = DBCommunication(
                    id=comm.id,
                    turn_id=turn.id,
                    type=comm.type,
                    sender=comm.sender,
                    recipients=comm.recipients,
                    content=comm.content,
                    timestamp=comm.timestamp,
                )
                session.add(db_comm)
            logger.debug(f"Persisted {len(turn_communications)} communications")

            # Persist metrics for this turn
            turn_metrics = [m for m in state.metrics if m.turn == state.turn]
            for metric in turn_metrics:
                db_metric = DBMetric(
                    turn_id=turn.id,
                    name=metric.name,
                    value=metric.value,
                    actor=metric.actor,
                    timestamp=metric.timestamp,
                )
                session.add(db_metric)
            logger.debug(f"Persisted {len(turn_metrics)} metrics")

            # Persist costs for this turn
            turn_costs = [c for c in state.costs if c.actor]  # All costs for this run
            for cost in turn_costs:
                # Check if cost already persisted
                existing = (
                    session.query(DBCost)
                    .filter(
                        DBCost.run_id == state.run_id,
                        DBCost.timestamp == cost.timestamp,
                        DBCost.actor == cost.actor,
                        DBCost.phase == cost.phase,
                    )
                    .first()
                )
                if not existing:
                    db_cost = DBCost(
                        run_id=state.run_id,
                        timestamp=cost.timestamp,
                        actor=cost.actor,
                        phase=cost.phase,
                        model=cost.model,
                        input_tokens=cost.input_tokens,
                        output_tokens=cost.output_tokens,
                        cost=cost.cost,
                    )
                    session.add(db_cost)

            # Commit transaction
            session.commit()
            logger.info(f"Database persistence complete for turn {state.turn}")

        except Exception as e:
            session.rollback()
            logger.error(f"Database persistence failed: {e}")
            # Don't fail the scenario - database is optional
            raise

        finally:
            session.close()

        return state
