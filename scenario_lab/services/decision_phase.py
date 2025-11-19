"""
Decision Phase Service for Scenario Lab V2

Handles actor decision-making and reasoning by integrating V1's Actor engine.
"""
from __future__ import annotations
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add V1 src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from actor_engine import Actor
from context_manager import ContextManager
from world_state import WorldState as V1WorldState
from communication_manager import CommunicationManager
from metrics_tracker import MetricsTracker
from qa_validator import QAValidator

from scenario_lab.models.state import ScenarioState, Decision, CostRecord

logger = logging.getLogger(__name__)


class DecisionPhase:
    """
    Phase service for actor decision-making

    This phase:
    1. Gets contextualized world state for each actor (via ContextManager)
    2. Asks each actor to make a decision (via Actor.make_decision())
    3. Records decisions in state
    4. Tracks costs
    5. Extracts metrics (via MetricsTracker)
    6. Validates decisions (via QAValidator, optional)
    7. Writes decisions to markdown files
    """

    def __init__(
        self,
        actors: Dict[str, Actor],
        context_manager: ContextManager,
        v1_world_state: V1WorldState,
        communication_manager: CommunicationManager,
        metrics_tracker: Optional[MetricsTracker] = None,
        qa_validator: Optional[QAValidator] = None,
        output_dir: Optional[str] = None,
    ):
        """
        Initialize decision phase

        Args:
            actors: Dictionary of actor short names to V1 Actor objects
            context_manager: V1 ContextManager for actor-specific context
            v1_world_state: V1 WorldState object for recording decisions
            communication_manager: V1 CommunicationManager for communication context
            metrics_tracker: Optional V1 MetricsTracker for extracting metrics
            qa_validator: Optional V1 QAValidator for validating decisions
            output_dir: Optional directory to save decision markdown files
        """
        self.actors = actors
        self.context_manager = context_manager
        self.v1_world_state = v1_world_state
        self.communication_manager = communication_manager
        self.metrics_tracker = metrics_tracker
        self.qa_validator = qa_validator
        self.output_dir = Path(output_dir) if output_dir else None

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """
        Execute decision phase

        Args:
            state: Current immutable scenario state

        Returns:
            New scenario state with actor decisions
        """
        logger.info(f"Executing decision phase for turn {state.turn}")

        # Get current world state content
        current_state = state.world_state.content

        # Determine total turns from scenario config
        total_turns = (
            state.scenario_config.get("num_turns", 10) if state.scenario_config else 10
        )

        # For each actor, get context and make decision
        for actor_short_name, actor in self.actors.items():
            logger.debug(f"Getting decision from {actor.name}")

            # Get contextualized world state for this actor
            actor_context = self.context_manager.get_context_for_actor(
                actor.name, self.v1_world_state, state.turn, self.communication_manager
            )

            # Extract recent goals from previous decisions
            recent_goals = self._extract_recent_goals(state, actor.name)

            # Actor makes decision
            decision_result = actor.make_decision(
                world_state=actor_context,
                turn=state.turn,
                total_turns=total_turns,
                recent_goals=recent_goals,
            )

            # Create V2 Decision from V1 result
            decision = Decision(
                actor=actor.name,
                turn=state.turn,
                goals=decision_result.get("goals", "").split("\n")
                if decision_result.get("goals")
                else [],
                reasoning=decision_result.get("reasoning", ""),
                action=decision_result.get("action", ""),
            )

            # Record decision in V1 world state (for context in next phases)
            self.v1_world_state.record_actor_decision(
                state.turn, actor.name, decision_result
            )

            # Add decision to V2 state
            state = state.with_decision(actor.name, decision)

            # Track costs
            tokens_used = decision_result.get("tokens_used", 0)
            cost = self._calculate_cost(actor.llm_model, tokens_used)
            cost_record = CostRecord(
                timestamp=datetime.now(),
                actor=actor.name,
                phase="decision",
                model=actor.llm_model,
                input_tokens=int(tokens_used * 0.7),  # Approximate split
                output_tokens=int(tokens_used * 0.3),
                cost=cost,
            )
            state = state.with_cost(cost_record)

            # Extract metrics from action
            if self.metrics_tracker:
                self.metrics_tracker.extract_metrics_from_text(
                    turn=state.turn, text=decision_result["action"], actor_name=actor.name
                )

            # Validate decision (if enabled)
            if self.qa_validator and self.qa_validator.is_enabled():
                if self.qa_validator.should_run_after_turn():
                    validation_result = self.qa_validator.validate_actor_decision(
                        actor_profile=actor.to_dict(),
                        world_state=current_state,
                        actor_reasoning=decision_result["reasoning"],
                        actor_action=decision_result["action"],
                        turn=state.turn,
                    )
                    if validation_result and not validation_result.passed:
                        severity_emoji = (
                            "⚠️" if validation_result.severity != "High" else "❌"
                        )
                        logger.warning(
                            f"  {severity_emoji} Validation: {validation_result.issues[0] if validation_result.issues else 'Inconsistency detected'}"
                        )

            # Write decision to markdown file
            if self.output_dir:
                self._write_decision_file(actor_short_name, state.turn, decision_result)

            logger.info(f"  ✓ Decision recorded: {tokens_used:,} tokens")

        return state

    def _extract_recent_goals(self, state: ScenarioState, actor_name: str) -> str:
        """Extract recent goals from previous turns (last 2 turns)"""
        if state.turn <= 1:
            return ""

        goals_list = []
        # Look at decisions from current state (which may contain previous turns)
        if actor_name in state.decisions:
            decision = state.decisions[actor_name]
            if decision.goals and decision.turn < state.turn:
                goals_text = "\n".join(f"- {g}" for g in decision.goals)
                goals_list.append(f"**Turn {decision.turn}:**\n{goals_text}\n")

        return "\n".join(goals_list) if goals_list else ""

    def _calculate_cost(self, model: str, tokens_used: int) -> float:
        """Calculate cost based on model and tokens"""
        # Simplified cost calculation - could be made more sophisticated
        cost_per_1k = 0.00015  # Default ~GPT-4o-mini pricing
        return (tokens_used / 1000.0) * cost_per_1k

    def _write_decision_file(
        self, actor_short_name: str, turn: int, decision_result: Dict[str, Any]
    ) -> None:
        """Write decision to markdown file"""
        if not self.output_dir:
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Use V1 world state's markdown generation
        actor_md = self.v1_world_state.actor_decision_to_markdown(
            turn, self.actors[actor_short_name].name, decision_result
        )

        filename = self.output_dir / f"{actor_short_name}-{turn:03d}.md"
        with open(filename, "w") as f:
            f.write(actor_md)
