"""
Persistence Phase Service for Scenario Lab V2

Handles saving scenario state to disk (markdown files, JSON, etc.)
"""
from __future__ import annotations
import logging
import os
import json
from pathlib import Path
from datetime import datetime

from scenario_lab.models.state import ScenarioState

logger = logging.getLogger(__name__)


class PersistencePhase:
    """
    Phase service for persisting scenario state

    This phase:
    1. Saves world state to markdown file
    2. Saves actor decisions to markdown files
    3. Saves metrics to JSON
    4. Saves costs to JSON
    5. Saves full state for resume capability
    """

    def __init__(self, output_dir: str):
        """
        Initialize persistence phase

        Args:
            output_dir: Directory to save files to
        """
        self.output_dir = Path(output_dir)
        self.files_saved = 0

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """
        Execute persistence phase

        Args:
            state: Current immutable scenario state

        Returns:
            Same scenario state (persistence doesn't modify state)
        """
        logger.info(f"Executing persistence phase for turn {state.turn}")

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Save world state
        await self._save_world_state(state)

        # Save actor decisions
        await self._save_actor_decisions(state)

        # Save metrics
        await self._save_metrics(state)

        # Save costs
        await self._save_costs(state)

        # Save full state for resume
        await self._save_scenario_state(state)

        logger.info(f"Persistence complete: {self.files_saved} files saved")
        return state

    async def _save_world_state(self, state: ScenarioState) -> None:
        """Save world state to markdown file"""
        filename = self.output_dir / f"world-state-{state.turn:03d}.md"
        content = state.world_state.content

        with open(filename, "w") as f:
            f.write(content)

        self.files_saved += 1
        logger.debug(f"Saved world state: {filename}")

    async def _save_actor_decisions(self, state: ScenarioState) -> None:
        """Save actor decisions to markdown files"""
        for actor_name, decision in state.decisions.items():
            # Create safe filename from actor name
            safe_name = actor_name.lower().replace(" ", "-")
            filename = self.output_dir / f"{safe_name}-{state.turn:03d}.md"

            content = [
                f"# {actor_name} - Turn {state.turn}",
                "",
                "## Goals",
                *[f"- {goal}" for goal in decision.goals],
                "",
                "## Reasoning",
                decision.reasoning,
                "",
                "## Action",
                decision.action,
                "",
                f"*Decision made at {decision.timestamp.isoformat()}*",
            ]

            with open(filename, "w") as f:
                f.write("\n".join(content))

            self.files_saved += 1
            logger.debug(f"Saved decision: {filename}")

    async def _save_metrics(self, state: ScenarioState) -> None:
        """Save metrics to JSON file"""
        filename = self.output_dir / "metrics.json"

        # Convert metrics to serializable format
        metrics_data = [
            {
                "name": m.name,
                "value": m.value,
                "turn": m.turn,
                "timestamp": m.timestamp.isoformat(),
                "metadata": m.metadata,
            }
            for m in state.metrics
        ]

        with open(filename, "w") as f:
            json.dump(metrics_data, f, indent=2)

        self.files_saved += 1
        logger.debug(f"Saved metrics: {filename}")

    async def _save_costs(self, state: ScenarioState) -> None:
        """Save costs to JSON file"""
        filename = self.output_dir / "costs.json"

        # Convert costs to serializable format
        costs_data = {
            "total_cost": state.total_cost(),
            "by_actor": {
                actor: state.actor_cost(actor) for actor in state.actors.keys()
            },
            "records": [
                {
                    "timestamp": c.timestamp.isoformat(),
                    "actor": c.actor,
                    "phase": c.phase,
                    "model": c.model,
                    "input_tokens": c.input_tokens,
                    "output_tokens": c.output_tokens,
                    "cost": c.cost,
                }
                for c in state.costs
            ],
        }

        with open(filename, "w") as f:
            json.dump(costs_data, f, indent=2)

        self.files_saved += 1
        logger.debug(f"Saved costs: {filename}")

    async def _save_scenario_state(self, state: ScenarioState) -> None:
        """Save complete scenario state for resume capability"""
        filename = self.output_dir / "scenario-state.json"

        # Use the built-in to_dict method
        state_data = state.to_dict()

        with open(filename, "w") as f:
            json.dump(state_data, f, indent=2)

        self.files_saved += 1
        logger.debug(f"Saved scenario state: {filename}")
