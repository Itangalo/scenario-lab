"""
Communication Phase Service for Scenario Lab V2

Handles bilateral and coalition communications by integrating V1's CommunicationManager.
"""
from __future__ import annotations
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Add V1 src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from actor_engine import Actor
from context_manager import ContextManager
from world_state import WorldState as V1WorldState
from communication_manager import CommunicationManager, ChannelType
from cost_tracker import CostTracker

from scenario_lab.models.state import ScenarioState, Communication, CostRecord
from datetime import datetime

logger = logging.getLogger(__name__)


class CommunicationPhase:
    """
    Phase service for actor communications

    This phase:
    1. Bilateral communications - actors can negotiate privately
    2. Coalition formation - actors can form groups
    3. Tracks costs for all communication decisions
    """

    def __init__(
        self,
        actors: Dict[str, Actor],
        context_manager: ContextManager,
        v1_world_state: V1WorldState,
        communication_manager: CommunicationManager,
        cost_tracker: Optional[CostTracker] = None,
    ):
        """
        Initialize communication phase

        Args:
            actors: Dictionary of actor short names to V1 Actor objects
            context_manager: V1 ContextManager for actor-specific context
            v1_world_state: V1 WorldState object
            communication_manager: V1 CommunicationManager for channel management
            cost_tracker: Optional V1 CostTracker for tracking communication costs
        """
        self.actors = actors
        self.context_manager = context_manager
        self.v1_world_state = v1_world_state
        self.communication_manager = communication_manager
        self.cost_tracker = cost_tracker

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """
        Execute communication phase

        Args:
            state: Current immutable scenario state

        Returns:
            New scenario state with communications added
        """
        logger.info(f"Executing communication phase for turn {state.turn}")

        # Determine total turns
        total_turns = (
            state.scenario_config.get("num_turns", 10) if state.scenario_config else 10
        )

        # Execute bilateral communications
        state = await self._execute_bilateral_communications(state, total_turns)

        # Execute coalition formation
        state = await self._execute_coalition_formation(state, total_turns)

        logger.info(f"Communication phase complete")
        return state

    async def _execute_bilateral_communications(
        self, state: ScenarioState, total_turns: int
    ) -> ScenarioState:
        """Execute bilateral communications between actors"""

        for actor_short_name, actor in self.actors.items():
            # Get contextualized world state for this actor
            actor_context = self.context_manager.get_context_for_actor(
                actor.name, self.v1_world_state, state.turn, self.communication_manager
            )

            # Get list of other actors
            other_actor_names = [a.name for a in self.actors.values() if a.name != actor.name]

            # Ask if actor wants to communicate privately
            if len(other_actor_names) > 0:
                logger.debug(f"{actor.name} considering private communication...")
                comm_decision = actor.decide_communication(
                    actor_context, state.turn, total_turns, other_actor_names
                )

                # Track communication decision cost
                if self.cost_tracker:
                    self.cost_tracker.record_actor_decision(
                        actor_name=actor.name,
                        turn=state.turn,
                        model=actor.llm_model,
                        tokens_used=comm_decision.get("tokens_used", 0),
                    )

                # Add cost to V2 state
                cost_record = CostRecord(
                    timestamp=datetime.now(),
                    actor=actor.name,
                    phase="communication",
                    model=actor.llm_model,
                    input_tokens=int(comm_decision.get("tokens_used", 0) * 0.7),
                    output_tokens=int(comm_decision.get("tokens_used", 0) * 0.3),
                    cost=self._calculate_cost(
                        actor.llm_model, comm_decision.get("tokens_used", 0)
                    ),
                )
                state = state.with_cost(cost_record)

                if comm_decision["initiate_bilateral"]:
                    target = comm_decision["target_actor"]
                    message = comm_decision["message"]

                    logger.info(f"  → Initiating bilateral: {actor.name} ↔ {target}")

                    # Get or create bilateral channel
                    channel = self.communication_manager.get_or_create_bilateral(
                        actor.name, target, state.turn
                    )

                    # Send initiator's message
                    self.communication_manager.send_message(
                        channel.channel_id, actor.name, message
                    )

                    # Create V2 Communication record
                    comm = Communication(
                        id=channel.channel_id,
                        turn=state.turn,
                        type="bilateral",
                        sender=actor.name,
                        recipients=[target],
                        content=message,
                    )
                    state = state.with_communication(comm)

                    # Get target actor
                    target_actor = next(a for a in self.actors.values() if a.name == target)

                    # Get contextualized state for target actor
                    target_context = self.context_manager.get_context_for_actor(
                        target, self.v1_world_state, state.turn, self.communication_manager
                    )

                    # Target responds
                    logger.debug(f"{target} responding...")
                    response = target_actor.respond_to_bilateral(
                        target_context, state.turn, total_turns, actor.name, message
                    )

                    # Track response cost
                    if self.cost_tracker:
                        self.cost_tracker.record_actor_decision(
                            actor_name=target,
                            turn=state.turn,
                            model=target_actor.llm_model,
                            tokens_used=response.get("tokens_used", 0),
                        )

                    # Add response cost to V2 state
                    response_cost = CostRecord(
                        timestamp=datetime.now(),
                        actor=target,
                        phase="communication",
                        model=target_actor.llm_model,
                        input_tokens=int(response.get("tokens_used", 0) * 0.7),
                        output_tokens=int(response.get("tokens_used", 0) * 0.3),
                        cost=self._calculate_cost(
                            target_actor.llm_model, response.get("tokens_used", 0)
                        ),
                    )
                    state = state.with_cost(response_cost)

                    # Send response
                    self.communication_manager.send_message(
                        channel.channel_id, target, response["response"]
                    )

                    # Create V2 Communication record for response
                    response_comm = Communication(
                        id=channel.channel_id + "-response",
                        turn=state.turn,
                        type="bilateral",
                        sender=target,
                        recipients=[actor.name],
                        content=response["response"],
                    )
                    state = state.with_communication(response_comm)

                    logger.info(f"  ✓ Bilateral negotiation completed")
                else:
                    logger.debug(f"  → No private communication from {actor.name}")

        return state

    async def _execute_coalition_formation(
        self, state: ScenarioState, total_turns: int
    ) -> ScenarioState:
        """Execute coalition formation among actors"""

        formed_coalitions = []

        for actor_short_name, actor in self.actors.items():
            # Get contextualized world state for this actor
            actor_context = self.context_manager.get_context_for_actor(
                actor.name, self.v1_world_state, state.turn, self.communication_manager
            )

            # Get list of other actors
            other_actor_names = [a.name for a in self.actors.values() if a.name != actor.name]

            # Only consider coalition formation if there are at least 2 other actors
            if len(other_actor_names) >= 2:
                logger.debug(f"{actor.name} considering coalition formation...")
                coalition_decision = actor.decide_coalition(
                    actor_context, state.turn, total_turns, other_actor_names
                )

                # Track coalition decision cost
                if self.cost_tracker:
                    self.cost_tracker.record_actor_decision(
                        actor_name=actor.name,
                        turn=state.turn,
                        model=actor.llm_model,
                        tokens_used=coalition_decision.get("tokens_used", 0),
                    )

                # Add cost to V2 state
                cost_record = CostRecord(
                    timestamp=datetime.now(),
                    actor=actor.name,
                    phase="communication",
                    model=actor.llm_model,
                    input_tokens=int(coalition_decision.get("tokens_used", 0) * 0.7),
                    output_tokens=int(coalition_decision.get("tokens_used", 0) * 0.3),
                    cost=self._calculate_cost(
                        actor.llm_model, coalition_decision.get("tokens_used", 0)
                    ),
                )
                state = state.with_cost(cost_record)

                if coalition_decision["propose_coalition"]:
                    proposed_members = [actor.name] + coalition_decision["members"]
                    proposed_members_sorted = sorted(proposed_members)

                    # Check if this coalition already exists for this turn
                    if proposed_members_sorted in [
                        sorted(c["members"]) for c in formed_coalitions
                    ]:
                        logger.debug(f"  → Coalition already formed with these members")
                        continue

                    logger.info(
                        f"  → Proposing coalition with {', '.join(coalition_decision['members'])}"
                    )
                    logger.info(f"  → Purpose: {coalition_decision['purpose']}")

                    # Ask each proposed member to accept or reject
                    all_accepted = True

                    for member_name in coalition_decision["members"]:
                        member_actor = next(
                            a for a in self.actors.values() if a.name == member_name
                        )

                        # Get contextualized state for member
                        member_context = self.context_manager.get_context_for_actor(
                            member_name,
                            self.v1_world_state,
                            state.turn,
                            self.communication_manager,
                        )

                        logger.debug(f"{member_name} considering coalition...")
                        response = member_actor.respond_to_coalition(
                            member_context,
                            state.turn,
                            total_turns,
                            actor.name,
                            proposed_members,
                            coalition_decision["purpose"],
                        )

                        # Track response cost
                        if self.cost_tracker:
                            self.cost_tracker.record_actor_decision(
                                actor_name=member_name,
                                turn=state.turn,
                                model=member_actor.llm_model,
                                tokens_used=response.get("tokens_used", 0),
                            )

                        # Add cost to V2 state
                        response_cost = CostRecord(
                            timestamp=datetime.now(),
                            actor=member_name,
                            phase="communication",
                            model=member_actor.llm_model,
                            input_tokens=int(response.get("tokens_used", 0) * 0.7),
                            output_tokens=int(response.get("tokens_used", 0) * 0.3),
                            cost=self._calculate_cost(
                                member_actor.llm_model, response.get("tokens_used", 0)
                            ),
                        )
                        state = state.with_cost(response_cost)

                        if not response["accept"]:
                            all_accepted = False
                            logger.info(f"    ✗ {member_name} declined coalition")
                            break
                        else:
                            logger.info(f"    ✓ {member_name} accepted coalition")

                    if all_accepted:
                        # Create coalition channel
                        channel = self.communication_manager.create_channel(
                            ChannelType.COALITION, proposed_members, state.turn
                        )

                        # Send initial message
                        self.communication_manager.send_message(
                            channel.channel_id, actor.name, coalition_decision["purpose"]
                        )

                        # Track coalition
                        formed_coalitions.append(
                            {
                                "members": proposed_members,
                                "purpose": coalition_decision["purpose"],
                                "channel_id": channel.channel_id,
                            }
                        )

                        # Create V2 Communication record
                        coalition_comm = Communication(
                            id=channel.channel_id,
                            turn=state.turn,
                            type="coalition",
                            sender=actor.name,
                            recipients=coalition_decision["members"],
                            content=coalition_decision["purpose"],
                        )
                        state = state.with_communication(coalition_comm)

                        logger.info(f"  ✓ Coalition formed successfully")
                else:
                    logger.debug(f"  → No coalition proposed by {actor.name}")

        return state

    def _calculate_cost(self, model: str, tokens_used: int) -> float:
        """Calculate cost based on model and tokens"""
        cost_per_1k = 0.00015  # Default ~GPT-4o-mini pricing
        return (tokens_used / 1000.0) * cost_per_1k
