"""
Communication Phase Service for Scenario Lab V2

Handles communication between actors (Phase 2.2 - stub implementation).

This phase allows actors to:
- Initiate bilateral negotiations
- Respond to bilateral communications
- Form coalitions
- Make public statements

Phase 2.2 Note: This is a simplified stub implementation.
Full communication logic (prompting actors to initiate communications,
handling multi-round negotiations, etc.) will be added in future phases.
"""
from __future__ import annotations
import logging
from typing import Optional

from scenario_lab.models.state import ScenarioState
from scenario_lab.core.communication_manager import create_communication

logger = logging.getLogger(__name__)


class CommunicationPhaseV2:
    """
    Phase service for actor communications (V2 - Stub implementation)

    Phase 2.2 Scope:
    - Basic communication recording
    - Communication visibility rules
    - Export to markdown files

    Deferred to Future Phases:
    - Prompting actors to initiate communications
    - Multi-round bilateral negotiations
    - Coalition formation prompts
    - Public statement prompts
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize communication phase

        Args:
            output_dir: Optional directory to export communication files
        """
        self.output_dir = output_dir

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """
        Execute communication phase

        Phase 2.2: This is a stub that:
        1. Checks for any communications in state for current turn
        2. Exports them to files if output_dir is set

        Future phases will add:
        - Prompting actors to initiate communications
        - Handling bilateral negotiations
        - Coalition formation

        Args:
            state: Current immutable scenario state

        Returns:
            Same scenario state (communication phase doesn't modify state in stub)
        """
        logger.info(f"Executing communication phase for turn {state.turn}")

        # Phase 2.2 Stub: Just log if there are communications
        turn_comms = [c for c in state.communications if c.turn == state.turn]

        if turn_comms:
            logger.info(f"  Found {len(turn_comms)} communications for turn {state.turn}")

            # Export to files if output_dir is set
            if self.output_dir:
                from scenario_lab.core.communication_manager import export_communications_to_files
                export_communications_to_files(state, self.output_dir, state.turn)
                logger.info(f"  Exported communications to {self.output_dir}")
        else:
            logger.info(f"  No communications for turn {state.turn}")

        # Return unchanged state (stub implementation)
        # Future: Will prompt actors and add new communications to state
        return state


def add_communication_to_state(
    state: ScenarioState,
    sender: str,
    recipients: list,
    content: str,
    comm_type: str = "bilateral"
) -> ScenarioState:
    """
    Helper function to add a communication to state

    Args:
        state: Current scenario state
        sender: Name of sender
        recipients: List of recipient names
        content: Message content
        comm_type: Type of communication ("public", "bilateral", "coalition")

    Returns:
        New scenario state with communication added
    """
    comm = create_communication(
        sender=sender,
        recipients=recipients,
        content=content,
        turn=state.turn,
        comm_type=comm_type
    )

    return state.with_communication(comm)
