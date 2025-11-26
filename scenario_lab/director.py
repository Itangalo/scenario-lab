"""
Director agent for Scenario Lab V3.

The Director is responsible for synthesizing the events of a turn into a
coherent narrative.
"""
import logging
from typing import Dict, List, Any

from .llm_provider import LLMProvider
from .models import TurnActions
from prompts.loader import load_prompt

logger = logging.getLogger(__name__)


class Director:
    """
    The Director agent, responsible for narrative synthesis.
    """

    def __init__(self, llm_provider: LLMProvider, llm_model: str):
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.epoch_summary = ""

    async def synthesize_turn(
        self, 
        turn_number: int,
        turn_actions: TurnActions,
        interpretations: List[str],
        events_triggered: List[Dict],
        previous_narrative: str,
    ) -> str:
        """
        Synthesizes the events of a turn into a narrative summary.

        Args:
            turn_number: The current turn number.
            turn_actions: The actions taken by actors this turn.
            interpretations: A list of interpretation strings from the action methods.
            events_triggered: A list of events that triggered this turn.
            previous_narrative: The narrative state from the previous turn.

        Returns:
            The new narrative summary for the turn.
        """
        if turn_number > 2:
            # For now, we don't have a good way to get the narrative from
            # turns 1 to (current-2). We will just use the previous narrative
            # as the epoch summary. This is a simplification.
            self.epoch_summary = previous_narrative

        system_prompt = load_prompt(
            "director.txt",
            turn=turn_number,
            narrative=self.epoch_summary or previous_narrative,
            exogenous_events=events_triggered,
            communication_summary="",  # This needs to be passed in from the engine
            actions=[action.model_dump() for action in turn_actions.actions],
            interpretations=interpretations,
        )

        messages = [{"role": "system", "content": system_prompt}]

        try:
            summary = await self.llm_provider.complete(messages, self.llm_model)
            return summary
        except Exception as e:
            logger.error(f"Director failed to synthesize narrative: {e}")
            return f"\nError: The Director failed to synthesize the turn's events. Raw interpretations: {interpretations}"
