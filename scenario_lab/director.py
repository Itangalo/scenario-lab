"""
Director agent for Scenario Lab V3.

The Director is responsible for synthesizing the events of a turn into a
coherent narrative.
"""
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta

from .llm_provider import LLMProvider
from .models import TurnActions
from prompts.loader import load_prompt

logger = logging.getLogger(__name__)


class Director:
    """
    The Director agent, responsible for narrative synthesis.
    """

    def __init__(self, llm_provider: LLMProvider, llm_model: str, time_scale: str, start_date: Optional[str] = None):
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.time_scale = time_scale
        self.start_date = start_date
        self.epoch_summary = ""

    def _calculate_time_period(self, turn_number: int) -> str:
        """
        Calculate the specific time period for a given turn.

        Returns a human-readable description like "the first half of 2026"
        or "January-June 2026" based on start_date and time_scale.
        """
        if not self.start_date:
            return f"turn {turn_number}"

        try:
            start = datetime.strptime(self.start_date, "%Y-%m-%d")

            # Parse time_scale to extract duration
            # Examples: "6 months per turn", "1 year per turn", "3 months per turn"
            match = re.search(r'(\d+)\s*(month|year)s?\s*per\s*turn', self.time_scale.lower())
            if not match:
                return f"turn {turn_number}"

            amount = int(match.group(1))
            unit = match.group(2)

            # Calculate period start (turn 1 starts at start_date)
            if unit == "month":
                period_start = start + relativedelta(months=amount * (turn_number - 1))
                period_end = period_start + relativedelta(months=amount, days=-1)
            else:  # year
                period_start = start + relativedelta(years=amount * (turn_number - 1))
                period_end = period_start + relativedelta(years=amount, days=-1)

            # Format based on what makes sense
            start_year = period_start.year
            end_year = period_end.year
            start_month = period_start.strftime("%B")
            end_month = period_end.strftime("%B")

            # Same year, 6-month period
            if start_year == end_year and amount == 6:
                if period_start.month == 1:  # Jan-Jun
                    return f"the first half of {start_year}"
                elif period_start.month == 7:  # Jul-Dec
                    return f"the second half of {start_year}"
                else:
                    return f"{start_month}-{end_month} {start_year}"

            # Same year, other periods
            elif start_year == end_year:
                return f"{start_month}-{end_month} {start_year}"

            # Spans years
            else:
                return f"{start_month} {start_year}-{end_month} {end_year}"

        except Exception as e:
            logger.warning(f"Failed to calculate time period: {e}")
            return f"turn {turn_number}"

    async def synthesize_turn(
        self, 
        turn_number: int,
        turn_actions: TurnActions,
        interpretations: List[str],
        events_triggered: List[Dict],
        previous_narrative: str,
        fact_ledger: List[Any],
    ) -> str:
        """
        Synthesizes the events of a turn into a narrative summary.

        Args:
            turn_number: The current turn number.
            turn_actions: The actions taken by actors this turn.
            interpretations: A list of interpretation strings from the action methods.
            events_triggered: A list of events that triggered this turn.
            previous_narrative: The narrative state from the previous turn.
            fact_ledger: The structured history of verified facts.

        Returns:
            The new narrative summary for the turn.
        """
        if turn_number > 2:
            # For now, we don't have a good way to get the narrative from
            # turns 1 to (current-2). We will just use the previous narrative
            # as the epoch summary. This is a simplification.
            self.epoch_summary = previous_narrative

        # Calculate the specific time period for this turn
        time_period = self._calculate_time_period(turn_number)

        system_prompt = load_prompt(
            "director.txt",
            turn=turn_number,
            time_scale=self.time_scale,
            time_period=time_period,
            narrative=self.epoch_summary or previous_narrative,
            exogenous_events=events_triggered,
            communication_summary="",  # This needs to be passed in from the engine
            actions=[action.model_dump() for action in turn_actions.actions],
            interpretations=interpretations,
            fact_ledger=[f.model_dump() for f in fact_ledger],
        )

        messages = [{"role": "system", "content": system_prompt}]

        try:
            summary = await self.llm_provider.complete(messages, self.llm_model)
            return summary
        except Exception as e:
            logger.error(f"Director failed to synthesize narrative: {e}")
            return f"\nError: The Director failed to synthesize the turn's events. Raw interpretations: {interpretations}"
