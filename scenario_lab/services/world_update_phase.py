"""
World Update Phase Service for Scenario Lab V2

Synthesizes new world state using LLM by integrating V1's WorldStateUpdater.
"""
from __future__ import annotations
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Add V1 src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from world_state import WorldState as V1WorldState
from world_state_updater import WorldStateUpdater
from metrics_tracker import MetricsTracker
from qa_validator import QAValidator
from exogenous_events import ExogenousEventManager

from scenario_lab.models.state import ScenarioState, WorldState, CostRecord

logger = logging.getLogger(__name__)


class WorldUpdatePhase:
    """
    Phase service for world state updates

    This phase:
    1. Gathers all actor decisions from current turn
    2. Gets exogenous events for this turn (if any)
    3. Calls WorldStateUpdater to synthesize new world state via LLM
    4. Updates world state in scenario state
    5. Tracks costs
    6. Extracts metrics
    7. Validates world state update (optional)
    8. Writes world state to markdown file
    """

    def __init__(
        self,
        world_state_updater: WorldStateUpdater,
        v1_world_state: V1WorldState,
        scenario_name: str,
        world_state_model: str,
        metrics_tracker: Optional[MetricsTracker] = None,
        qa_validator: Optional[QAValidator] = None,
        exogenous_event_manager: Optional[ExogenousEventManager] = None,
        output_dir: Optional[str] = None,
    ):
        """
        Initialize world update phase

        Args:
            world_state_updater: V1 WorldStateUpdater for LLM synthesis
            v1_world_state: V1 WorldState object
            scenario_name: Name of the scenario
            world_state_model: LLM model for world state updates
            metrics_tracker: Optional V1 MetricsTracker for extracting metrics
            qa_validator: Optional V1 QAValidator for validating updates
            exogenous_event_manager: Optional manager for background events
            output_dir: Optional directory to save world state markdown files
        """
        self.world_state_updater = world_state_updater
        self.v1_world_state = v1_world_state
        self.scenario_name = scenario_name
        self.world_state_model = world_state_model
        self.metrics_tracker = metrics_tracker
        self.qa_validator = qa_validator
        self.exogenous_event_manager = exogenous_event_manager
        self.output_dir = Path(output_dir) if output_dir else None

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """
        Execute world update phase

        Args:
            state: Current immutable scenario state

        Returns:
            New scenario state with updated world state
        """
        logger.info(f"Executing world update phase for turn {state.turn}")

        # Get current world state content
        current_state = state.world_state.content

        # Determine total turns
        total_turns = (
            state.scenario_config.get("num_turns", 10) if state.scenario_config else 10
        )

        # Prepare actor decisions for world state update
        actor_decisions_for_update = {}
        for actor_name, decision in state.decisions.items():
            actor_decisions_for_update[actor_name] = {
                "reasoning": decision.reasoning,
                "action": decision.action,
            }

        # Get exogenous events for this turn
        exogenous_events = []
        if self.exogenous_event_manager:
            # Get current metrics for conditional events
            current_metrics = (
                self.metrics_tracker.get_current_metrics()
                if self.metrics_tracker and hasattr(self.metrics_tracker, "get_current_metrics")
                else None
            )
            exogenous_events = self.exogenous_event_manager.get_events_for_turn(
                state.turn, current_metrics
            )

            if exogenous_events:
                logger.info(f"  📋 {len(exogenous_events)} background event(s) occurring this turn")
                for event in exogenous_events:
                    logger.debug(f"     - {event['name']}")

        # Call V1 WorldStateUpdater to synthesize new world state
        world_update_result = self.world_state_updater.update_world_state(
            current_state=current_state,
            turn=state.turn,
            total_turns=total_turns,
            actor_decisions=actor_decisions_for_update,
            scenario_name=self.scenario_name,
            exogenous_events=exogenous_events,
        )

        new_state_content = world_update_result["updated_state"]

        # Update V1 world state (for context in next phases)
        self.v1_world_state.update_state(new_state_content)

        # Create V2 WorldState
        new_world_state = WorldState(turn=state.turn, content=new_state_content)

        # Track world state update costs
        tokens_used = world_update_result["metadata"].get("tokens_used", 0)
        cost = self._calculate_cost(self.world_state_model, tokens_used)
        cost_record = CostRecord(
            timestamp=datetime.now(),
            actor="world_state_updater",
            phase="world_update",
            model=self.world_state_model,
            input_tokens=int(tokens_used * 0.7),
            output_tokens=int(tokens_used * 0.3),
            cost=cost,
        )
        state = state.with_cost(cost_record)

        # Extract metrics from world state
        if self.metrics_tracker:
            self.metrics_tracker.extract_metrics_from_text(
                turn=state.turn, text=new_state_content
            )

        # Write world state to file
        if self.output_dir:
            self._write_world_state_file(state.turn, new_state_content)

        logger.info(f"  ✓ World state updated: {tokens_used:,} tokens")

        # Validate world state update (if enabled)
        if self.qa_validator and self.qa_validator.is_enabled():
            if self.qa_validator.should_run_after_turn():
                # Extract just the action text for each actor
                actor_actions_text = {
                    name: decision.action for name, decision in state.decisions.items()
                }

                validation_result = self.qa_validator.validate_world_state_update(
                    previous_world_state=current_state,
                    actor_actions=actor_actions_text,
                    new_world_state=new_state_content,
                    turn=state.turn,
                )
                if validation_result and not validation_result.passed:
                    severity_emoji = "⚠️" if validation_result.severity != "High" else "❌"
                    logger.warning(
                        f"    {severity_emoji} World state validation: {validation_result.issues[0] if validation_result.issues else 'Inconsistency detected'}"
                    )

                # Generate turn validation report
                if self.output_dir:
                    self.qa_validator.generate_turn_report(state.turn, str(self.output_dir))

        # Update state with new world state
        return state.with_world_state(new_world_state)

    def _calculate_cost(self, model: str, tokens_used: int) -> float:
        """Calculate cost based on model and tokens"""
        cost_per_1k = 0.00015  # Default ~GPT-4o-mini pricing
        return (tokens_used / 1000.0) * cost_per_1k

    def _write_world_state_file(self, turn: int, content: str) -> None:
        """Write world state to markdown file"""
        if not self.output_dir:
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Use V1 world state's markdown generation
        world_state_md = self.v1_world_state.to_markdown(turn)

        filename = self.output_dir / f"world-state-{turn:03d}.md"
        with open(filename, "w") as f:
            f.write(world_state_md)
