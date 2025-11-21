"""
Context Manager for Scenario Lab V2

Manages context windows for actors to prevent token overflow in long-running scenarios.
Migrated from V1 with adaptations for immutable ScenarioState.

Provides actors with:
- Summary of old turns (beyond window)
- Full detail of recent turns (within window)
- Full communication history they participated in
"""
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass

from scenario_lab.models.state import ScenarioState, Decision, Communication
from scenario_lab.utils.api_client import make_llm_call_async, LLMResponse
from scenario_lab.core.prompt_builder import build_messages_for_llm

logger = logging.getLogger(__name__)


@dataclass
class ContextWindow:
    """Represents a context window for an actor"""
    summary: str  # Summary of old turns
    recent_history: str  # Full detail of recent turns
    current_state: str  # Current world state


class ContextManagerV2:
    """
    Manages context windows for long-running scenarios

    Uses LLM-based summarization to keep context within token limits while
    preserving important historical information.
    """

    def __init__(
        self,
        window_size: int = 3,
        summarization_model: str = "openai/gpt-4o-mini",
        max_cache_size: int = 1000,
        api_key: Optional[str] = None
    ):
        """
        Initialize context manager

        Args:
            window_size: Number of recent turns to keep in full detail (must be >= 1)
            summarization_model: LLM model for summarization (should be cheap)
            max_cache_size: Maximum number of summaries to cache (must be >= 1)
            api_key: API key for LLM calls (if None, uses environment variable)

        Raises:
            ValueError: If window_size < 1 or max_cache_size < 1 or summarization_model is empty
        """
        # V2 Pattern: Validate parameters in __init__
        if window_size < 1:
            raise ValueError(f"window_size must be >= 1, got {window_size}")

        if max_cache_size < 1:
            raise ValueError(f"max_cache_size must be >= 1, got {max_cache_size}")

        if not summarization_model or not summarization_model.strip():
            raise ValueError("summarization_model cannot be empty")

        self.window_size = window_size
        self.summarization_model = summarization_model
        self.max_cache_size = max_cache_size
        self.api_key = api_key

        # LRU cache for summaries
        self.summaries_cache: Dict[str, str] = {}
        self.cache_access_order: List[str] = []

        logger.debug(
            f"ContextManagerV2 initialized: window_size={window_size}, "
            f"model={summarization_model}, cache_size={max_cache_size}"
        )

    def _get_cached_summary(self, key: str) -> Optional[str]:
        """Get summary from cache and update LRU order"""
        if key in self.summaries_cache:
            # Move to end (most recently used)
            if key in self.cache_access_order:
                self.cache_access_order.remove(key)
            self.cache_access_order.append(key)
            return self.summaries_cache[key]
        return None

    def _cache_summary(self, key: str, value: str) -> None:
        """Cache summary with LRU eviction if needed"""
        # Evict oldest if cache is full
        if len(self.summaries_cache) >= self.max_cache_size and key not in self.summaries_cache:
            oldest_key = self.cache_access_order.pop(0)
            del self.summaries_cache[oldest_key]

        # Add to cache
        self.summaries_cache[key] = value
        if key in self.cache_access_order:
            self.cache_access_order.remove(key)
        self.cache_access_order.append(key)

    async def get_context_for_actor(
        self,
        actor_name: str,
        state: ScenarioState,
    ) -> str:
        """
        Get contextualized world state for an actor

        Args:
            actor_name: Name of the actor
            state: Current scenario state

        Returns:
            Formatted context string combining summary and recent detail
        """
        turn = state.turn

        # If we're within the window size, return full history
        if turn <= self.window_size:
            return self._get_full_history(state, actor_name)

        # Otherwise, return summary + recent window
        return await self._get_windowed_context(state, actor_name)

    def _get_full_history(
        self,
        state: ScenarioState,
        actor_name: str
    ) -> str:
        """Get full history when scenario is short enough"""
        context = "## Scenario History\n\n"

        # Initial state (turn 0)
        context += f"### Turn 0 (Initial State)\n\n{state.scenario_config.get('initial_world_state', '')}\n\n"

        # Note: In V2, we only have the current turn's world_state in state.world_state
        # For full history, we would need to reconstruct from saved states or
        # maintain a history in ScenarioState. For Phase 2.1, we'll use a simplified approach:
        # Show only current world state for now (this will be enhanced in later phases)

        # Current turn
        context += f"### Turn {state.turn} (Current)\n\n"
        context += f"**Current World State:**\n{state.world_state.content}\n\n"

        # Recent decisions (from current state)
        if state.decisions:
            context += "**Recent Actions Taken:**\n\n"
            for actor, decision in state.decisions.items():
                context += f"- **{actor}:** {decision.action}\n"
            context += "\n"

        # Phase 2.1: Communications will be added in Phase 2.2
        # For now, stub it out
        # if state.communications:
        #     context += self._format_communications_for_actor(state, actor_name)

        return context

    async def _get_windowed_context(
        self,
        state: ScenarioState,
        actor_name: str
    ) -> str:
        """Get summarized old history + detailed recent history"""
        context = ""

        # Determine window boundaries
        window_start = state.turn - self.window_size + 1
        summary_end = window_start - 1  # Last turn to include in summary

        # Generate or retrieve summary for old turns
        summary_key = f"{state.scenario_id}-0-{summary_end}"

        summary = self._get_cached_summary(summary_key)
        if summary is None:
            # Phase 2.1: Simplified summary (just mention we're X turns in)
            # Full LLM-based summarization will be added when we have full history
            summary = f"This scenario has been running for {summary_end + 1} turns. The actors have been making decisions and the world state has been evolving based on their actions."
            # Future: Call LLM to generate proper summary
            # summary = await self._generate_summary(state, 0, summary_end)
            self._cache_summary(summary_key, summary)

        context += "## Earlier Events (Summary)\n\n"
        context += summary + "\n\n"
        context += "---\n\n"

        # Add recent turns in full detail
        context += f"## Recent History (Last {self.window_size} Turns)\n\n"

        # Phase 2.1: Simplified - show current turn only
        # Full history tracking will be added in later phases
        context += f"### Turn {state.turn} (Current)\n\n"
        context += f"**Current World State:**\n{state.world_state.content}\n\n"

        # Recent decisions
        if state.decisions:
            context += "**Actions Taken This Turn:**\n\n"
            for actor, decision in state.decisions.items():
                context += f"- **{actor}:** {decision.action}\n"
            context += "\n"

        return context

    async def _generate_summary(
        self,
        state: ScenarioState,
        start_turn: int,
        end_turn: int
    ) -> str:
        """
        Generate LLM-powered summary of turns from start to end

        Phase 2.1: Stub implementation. Full implementation will require
        access to historical states, which will be added in later phases.

        Args:
            state: Current scenario state
            start_turn: First turn to summarize (inclusive)
            end_turn: Last turn to summarize (inclusive)

        Returns:
            Summary text
        """
        # For now, return a placeholder
        # In the future, this will:
        # 1. Load historical world states from persistence
        # 2. Build history text from those states
        # 3. Call LLM to summarize

        system_prompt = """You are a scenario historian. Your job is to create concise summaries of scenario history.

Focus on:
- Key events and turning points
- Important decisions by actors
- Changes in world state
- Trends and patterns

Keep the summary clear and factual. Aim for 200-400 words."""

        user_prompt = f"""Please summarize the following scenario history from turn {start_turn} to turn {end_turn}:

[Phase 2.1: Historical data access not yet implemented]

Provide a concise summary that captures the key events, decisions, and state changes."""

        try:
            messages = build_messages_for_llm(system_prompt, user_prompt)

            llm_response: LLMResponse = await make_llm_call_async(
                model=self.summarization_model,
                messages=messages,
                api_key=self.api_key,
                max_retries=3,
                context={'phase': 'context_summary', 'turns': f'{start_turn}-{end_turn}'}
            )

            logger.info(f"Generated summary for turns {start_turn}-{end_turn} ({llm_response.tokens_used} tokens)")

            return llm_response.content

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            # Return fallback summary
            return f"Summary of turns {start_turn} to {end_turn} (summarization failed)"

    def clear_cache(self):
        """Clear summary cache (useful for testing or memory management)"""
        self.summaries_cache = {}
        self.cache_access_order = []
        logger.info("Context summary cache cleared")
