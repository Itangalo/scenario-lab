"""
State Persistence for Scenario Lab V2

Handles saving and loading scenario state for resume and branch functionality.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from scenario_lab.models.state import (
    ScenarioState,
    ScenarioStatus,
    WorldState,
    ActorState,
    Decision,
    Communication,
    CostRecord,
    MetricRecord,
)

logger = logging.getLogger(__name__)


class StatePersistence:
    """Handles saving and loading scenario state"""

    @staticmethod
    def save_state(state: ScenarioState, output_dir: str) -> None:
        """
        Save scenario state to JSON file

        Args:
            state: Current scenario state
            output_dir: Directory to save state file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        state_file = output_path / "scenario-state-v2.json"

        # Convert state to dictionary
        state_dict = {
            "version": "2.0",
            "scenario_id": state.scenario_id,
            "scenario_name": state.scenario_name,
            "run_id": state.run_id,
            "turn": state.turn,
            "status": state.status.value,
            "scenario_config": state.scenario_config,  # Save scenario configuration
            "world_state": {
                "turn": state.world_state.turn,
                "content": state.world_state.content,
            },
            "actors": {
                name: {
                    "name": actor.name,
                    "short_name": actor.short_name,
                    "model": actor.model,
                    "current_goals": actor.current_goals,
                    "private_information": actor.private_information,
                }
                for name, actor in state.actors.items()
            },
            "decisions": {
                name: {
                    "actor": decision.actor,
                    "turn": decision.turn,
                    "goals": decision.goals,
                    "reasoning": decision.reasoning,
                    "action": decision.action,
                }
                for name, decision in state.decisions.items()
            },
            "communications": [
                {
                    "id": comm.id,
                    "turn": comm.turn,
                    "type": comm.type,
                    "sender": comm.sender,
                    "recipients": comm.recipients,
                    "content": comm.content,
                    "timestamp": comm.timestamp.isoformat(),
                }
                for comm in state.communications
            ],
            "costs": [
                {
                    "timestamp": cost.timestamp.isoformat(),
                    "actor": cost.actor,
                    "phase": cost.phase,
                    "model": cost.model,
                    "input_tokens": cost.input_tokens,
                    "output_tokens": cost.output_tokens,
                    "cost": cost.cost,
                }
                for cost in state.costs
            ],
            "metrics": [
                {
                    "turn": metric.turn,
                    "name": metric.name,
                    "value": metric.value,
                    "actor": metric.actor,
                    "timestamp": metric.timestamp.isoformat(),
                }
                for metric in state.metrics
            ],
            "metadata": state.metadata,
        }

        # Write to file
        with open(state_file, "w") as f:
            json.dump(state_dict, f, indent=2)

        logger.info(f"Saved scenario state to {state_file}")

    @staticmethod
    def load_state(state_file: str) -> ScenarioState:
        """
        Load scenario state from JSON file

        Args:
            state_file: Path to state file

        Returns:
            Loaded scenario state
        """
        state_path = Path(state_file)
        if not state_path.exists():
            raise FileNotFoundError(f"State file not found: {state_file}")

        with open(state_path, "r") as f:
            state_dict = json.load(f)

        # Check version
        version = state_dict.get("version", "1.0")
        if not version.startswith("2."):
            raise ValueError(f"Incompatible state version: {version}")

        # Reconstruct state objects
        world_state = WorldState(
            turn=state_dict["world_state"]["turn"],
            content=state_dict["world_state"]["content"],
        )

        actors = {
            name: ActorState(
                name=actor["name"],
                short_name=actor["short_name"],
                model=actor["model"],
                current_goals=actor.get("current_goals", []),
                private_information=actor.get("private_information", ""),
            )
            for name, actor in state_dict["actors"].items()
        }

        decisions = {
            name: Decision(
                actor=decision["actor"],
                turn=decision["turn"],
                goals=decision["goals"],
                reasoning=decision["reasoning"],
                action=decision["action"],
            )
            for name, decision in state_dict["decisions"].items()
        }

        communications = [
            Communication(
                id=comm["id"],
                turn=comm["turn"],
                type=comm["type"],
                sender=comm["sender"],
                recipients=comm["recipients"],
                content=comm["content"],
                timestamp=datetime.fromisoformat(comm["timestamp"]),
            )
            for comm in state_dict["communications"]
        ]

        costs = [
            CostRecord(
                timestamp=datetime.fromisoformat(cost["timestamp"]),
                actor=cost["actor"],
                phase=cost["phase"],
                model=cost["model"],
                input_tokens=cost["input_tokens"],
                output_tokens=cost["output_tokens"],
                cost=cost["cost"],
            )
            for cost in state_dict["costs"]
        ]

        metrics = [
            MetricRecord(
                turn=metric["turn"],
                name=metric["name"],
                value=metric["value"],
                actor=metric["actor"],
                timestamp=datetime.fromisoformat(metric["timestamp"]),
            )
            for metric in state_dict["metrics"]
        ]

        # Create state
        state = ScenarioState(
            scenario_id=state_dict["scenario_id"],
            scenario_name=state_dict["scenario_name"],
            run_id=state_dict["run_id"],
            turn=state_dict["turn"],
            status=ScenarioStatus(state_dict["status"]),
            scenario_config=state_dict.get("scenario_config", {}),  # Load scenario configuration
            world_state=world_state,
            actors=actors,
            decisions=decisions,
            communications=communications,
            costs=costs,
            metrics=metrics,
            metadata=state_dict.get("metadata", {}),
        )

        logger.info(f"Loaded scenario state from {state_file} (turn {state.turn})")
        return state

    @staticmethod
    def create_branch(
        source_state_file: str,
        branch_at_turn: int,
        new_output_dir: str,
    ) -> ScenarioState:
        """
        Create a branch from an existing state file

        Args:
            source_state_file: Path to source state file
            branch_at_turn: Turn number to branch from
            new_output_dir: Directory for the new branch

        Returns:
            Branched scenario state
        """
        # Load source state
        source_state = StatePersistence.load_state(source_state_file)

        if branch_at_turn > source_state.turn:
            raise ValueError(
                f"Cannot branch at turn {branch_at_turn}: "
                f"source state only has {source_state.turn} turns"
            )

        # Filter state to branch point
        # For simplicity, we keep all data but update the turn
        # In a full implementation, we'd filter decisions/communications/etc by turn

        branched_state = ScenarioState(
            scenario_id=source_state.scenario_id,
            scenario_name=source_state.scenario_name,
            run_id=f"branch-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            turn=branch_at_turn,
            status=ScenarioStatus.RUNNING,
            world_state=source_state.world_state,  # Use world state at branch point
            actors=source_state.actors,
            decisions={},  # Clear decisions after branch point
            communications=[],  # Clear communications after branch point
            costs=source_state.costs[:],  # Keep costs up to branch point
            metrics=source_state.metrics[:],  # Keep metrics up to branch point
            metadata={
                **source_state.metadata,
                "branched_from": source_state.run_id,
                "branch_point": branch_at_turn,
                "branch_created": datetime.now().isoformat(),
            },
        )

        logger.info(
            f"Created branch from {source_state.run_id} at turn {branch_at_turn}"
        )

        return branched_state
