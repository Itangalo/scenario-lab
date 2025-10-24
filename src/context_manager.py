"""
Context Manager - Manages context windows for actors to prevent token overflow
"""
import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from world_state import WorldState
from communication_manager import CommunicationManager
from api_utils import make_openrouter_call

load_dotenv()


class ContextManager:
    """
    Manages context windows for long-running scenarios

    Provides actors with:
    - Summary of old turns (beyond window)
    - Full detail of recent turns (within window)
    - Full communication history they participated in
    """

    def __init__(
        self,
        window_size: int = 3,
        summarization_model: str = "openai/gpt-4o-mini"
    ):
        """
        Initialize context manager

        Args:
            window_size: Number of recent turns to keep in full detail
            summarization_model: LLM model to use for summarization (should be cheap)
        """
        self.window_size = window_size
        self.summarization_model = summarization_model
        self.summaries_cache: Dict[str, str] = {}  # Cache summaries to avoid re-generating

    def get_context_for_actor(
        self,
        actor_name: str,
        world_state: WorldState,
        turn: int,
        communication_manager: Optional[CommunicationManager] = None
    ) -> str:
        """
        Get contextualized world state for an actor

        Args:
            actor_name: Name of the actor
            world_state: WorldState object
            turn: Current turn number
            communication_manager: Optional communication manager for private messages

        Returns:
            Formatted context string combining summary and recent detail
        """
        # If we're within the window size, return full history
        if turn <= self.window_size:
            return self._get_full_history(world_state, turn, actor_name, communication_manager)

        # Otherwise, return summary + recent window
        return self._get_windowed_context(world_state, turn, actor_name, communication_manager)

    def _get_full_history(
        self,
        world_state: WorldState,
        turn: int,
        actor_name: str,
        communication_manager: Optional[CommunicationManager] = None
    ) -> str:
        """Get full history when scenario is short enough"""
        context = "## Scenario History\n\n"

        # Initial state
        context += f"### Turn 0 (Initial State)\n\n{world_state.states[0]}\n\n"

        # Completed turns (turn - 1 because we're being called during turn execution)
        # Only include turns that have been completed (world state updated)
        for t in range(1, turn):
            if t in world_state.states:
                context += f"### Turn {t}\n\n"
                context += f"**World State:**\n{world_state.states[t]}\n\n"

                # Actor decisions
                decisions = world_state.get_actor_decisions_for_turn(t)
                if decisions:
                    context += "**Actions Taken:**\n\n"
                    for actor, decision in decisions.items():
                        context += f"- **{actor}:** {decision['action']}\n"
                    context += "\n"

                # Private communications (if any)
                if communication_manager:
                    comm_context = communication_manager.format_messages_for_context(actor_name, t)
                    if comm_context:
                        context += comm_context

        # Current turn - just show current state (no decisions yet)
        context += f"### Turn {turn} (Current)\n\n"
        context += f"**Current World State:**\n{world_state.get_current_state()}\n\n"

        return context

    def _get_windowed_context(
        self,
        world_state: WorldState,
        turn: int,
        actor_name: str,
        communication_manager: Optional[CommunicationManager] = None
    ) -> str:
        """Get summarized old history + detailed recent history"""
        context = ""

        # Determine window boundaries
        window_start = turn - self.window_size + 1
        summary_end = window_start - 1  # Last turn to include in summary

        # Generate or retrieve summary for old turns
        summary_key = f"{world_state.scenario_name}-0-{summary_end}"

        if summary_key not in self.summaries_cache:
            summary = self._generate_summary(world_state, 0, summary_end)
            self.summaries_cache[summary_key] = summary
        else:
            summary = self.summaries_cache[summary_key]

        context += "## Earlier Events (Summary)\n\n"
        context += summary + "\n\n"
        context += "---\n\n"

        # Add recent turns in full detail
        context += f"## Recent History (Last {self.window_size} Turns)\n\n"

        # Only include completed turns
        for t in range(window_start, turn):
            if t in world_state.states:
                context += f"### Turn {t}\n\n"
                context += f"**World State:**\n{world_state.states[t]}\n\n"

                # Actor decisions
                decisions = world_state.get_actor_decisions_for_turn(t)
                if decisions:
                    context += "**Actions Taken:**\n\n"
                    for actor, decision in decisions.items():
                        context += f"- **{actor}:** {decision['action']}\n"
                    context += "\n"

                # Private communications (if any)
                if communication_manager:
                    comm_context = communication_manager.format_messages_for_context(actor_name, t)
                    if comm_context:
                        context += comm_context

        # Current turn - just show current state (no decisions yet)
        context += f"### Turn {turn} (Current)\n\n"
        context += f"**Current World State:**\n{world_state.get_current_state()}\n\n"

        return context

    def _generate_summary(
        self,
        world_state: WorldState,
        start_turn: int,
        end_turn: int
    ) -> str:
        """
        Generate LLM-powered summary of turns from start to end

        Args:
            world_state: WorldState object
            start_turn: First turn to summarize (inclusive)
            end_turn: Last turn to summarize (inclusive)

        Returns:
            Summary text
        """
        # Build history text to summarize
        history_text = ""

        # Initial state
        if start_turn == 0:
            history_text += f"**Turn 0 (Initial State):**\n{world_state.states[0]}\n\n"
            start_turn = 1

        # Subsequent turns
        for t in range(start_turn, end_turn + 1):
            history_text += f"**Turn {t}:**\n"
            history_text += f"World State: {world_state.states[t]}\n\n"

            decisions = world_state.get_actor_decisions_for_turn(t)
            if decisions:
                history_text += "Actions:\n"
                for actor, decision in decisions.items():
                    history_text += f"- {actor}: {decision['action']}\n"
                history_text += "\n"

        # Call LLM to summarize
        system_prompt = """You are a scenario historian. Your job is to create concise summaries of scenario history.

Focus on:
- Key events and turning points
- Important decisions by actors
- Changes in world state
- Trends and patterns

Keep the summary clear and factual. Aim for 200-400 words."""

        user_prompt = f"""Please summarize the following scenario history from turn {start_turn if start_turn > 0 else 0} to turn {end_turn}:

{history_text}

Provide a concise summary that captures the key events, decisions, and state changes."""

        summary = self._call_llm(system_prompt, user_prompt)

        return summary

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenRouter API for summarization"""
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        data = {
            "model": self.summarization_model,
            "messages": messages
        }

        response = make_openrouter_call(url, headers, data, max_retries=3)
        result = response.json()
        return result['choices'][0]['message']['content']

    def get_summary_cost(self, world_state: WorldState, start_turn: int, end_turn: int) -> Dict[str, Any]:
        """
        Estimate cost of summarizing a range of turns

        This is approximate - actual cost depends on content length
        """
        # Rough estimate: 100 tokens per turn input, 200 tokens output
        estimated_input_tokens = (end_turn - start_turn + 1) * 100
        estimated_output_tokens = 200

        # gpt-4o-mini pricing (approximate)
        input_cost_per_token = 0.00000015  # $0.15 per 1M tokens
        output_cost_per_token = 0.00000060  # $0.60 per 1M tokens

        estimated_cost = (
            estimated_input_tokens * input_cost_per_token +
            estimated_output_tokens * output_cost_per_token
        )

        return {
            'estimated_cost': estimated_cost,
            'estimated_input_tokens': estimated_input_tokens,
            'estimated_output_tokens': estimated_output_tokens,
            'total_estimated_tokens': estimated_input_tokens + estimated_output_tokens
        }

    def clear_cache(self):
        """Clear summary cache (useful for testing or memory management)"""
        self.summaries_cache = {}
