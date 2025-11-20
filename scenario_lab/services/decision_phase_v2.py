"""
Decision Phase Service for Scenario Lab V2

Handles actor decision-making using V2 components (no V1 dependencies).

Phase 2.1 Updates:
- ✅ Uses V2 API client for LLM calls
- ✅ Uses V2 prompt builder for prompt construction
- ✅ Uses V2 response parser for parsing
- ✅ Tracks costs via ScenarioState
- ✅ Uses V2 ContextManager for context windowing (Phase 2.1)
- ⏳ Defers communication to Phase 2.2 (no communication context yet)
- ⏳ Defers metrics extraction to Phase 3.3 (stub)
- ⏳ Defers QA validation to Phase 3.4 (stub)
"""
from __future__ import annotations
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from scenario_lab.models.state import ScenarioState, Decision, CostRecord
from scenario_lab.utils.api_client import make_llm_call_async, LLMResponse
from scenario_lab.core.prompt_builder import build_decision_prompt, build_messages_for_llm
from scenario_lab.utils.response_parser import parse_decision
from scenario_lab.utils.model_pricing import calculate_cost
from scenario_lab.core.context_manager import ContextManagerV2

logger = logging.getLogger(__name__)


class DecisionPhaseV2:
    """
    Phase service for actor decision-making (V2 - Pure implementation)

    This phase:
    1. Gets contextualized world state for each actor (via ContextManager)
    2. Builds decision prompts for each actor
    3. Makes LLM API calls
    4. Parses responses
    5. Records decisions in state
    6. Tracks costs
    7. Writes decisions to markdown files
    """

    def __init__(
        self,
        actor_configs: Dict[str, Dict[str, Any]],
        scenario_system_prompt: str = "",
        output_dir: Optional[str] = None,
        json_mode: bool = False,
        context_window_size: int = 3,
    ):
        """
        Initialize decision phase

        Args:
            actor_configs: Dictionary of actor short names to actor config dicts
            scenario_system_prompt: System prompt from scenario configuration
            output_dir: Optional directory to save decision markdown files
            json_mode: Whether to use JSON response format (default: False)
            context_window_size: Number of recent turns to keep in full detail (default: 3)
        """
        self.actor_configs = actor_configs
        self.scenario_system_prompt = scenario_system_prompt
        self.output_dir = Path(output_dir) if output_dir else None
        self.json_mode = json_mode
        self.api_key = os.environ.get('OPENROUTER_API_KEY')

        # Create context manager for windowing
        self.context_manager = ContextManagerV2(
            window_size=context_window_size,
            summarization_model="openai/gpt-4o-mini",
            api_key=self.api_key
        )

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """
        Execute decision phase

        Args:
            state: Current immutable scenario state

        Returns:
            New scenario state with actor decisions
        """
        logger.info(f"Executing decision phase for turn {state.turn}")

        # Determine total turns from scenario config
        total_turns = state.scenario_config.get("num_turns") or state.scenario_config.get("turns", 10)

        # For each actor, make decision
        for actor_short_name, actor_config in self.actor_configs.items():
            actor_name = actor_config['name']
            logger.debug(f"Getting decision from {actor_name}")

            # Phase 2.1: Get contextualized world state for this actor
            current_world_state = await self.context_manager.get_context_for_actor(
                actor_name=actor_name,
                state=state
            )

            # Extract recent goals from previous decisions
            recent_goals = self._extract_recent_goals(state, actor_name)

            # Build prompts
            system_prompt, user_prompt = build_decision_prompt(
                world_state=current_world_state,
                turn=state.turn,
                total_turns=total_turns,
                actor_name=actor_name,
                scenario_system_prompt=self.scenario_system_prompt,
                actor_system_prompt=actor_config.get('system_prompt'),
                recent_goals=recent_goals,
                json_mode=self.json_mode,
                # Phase 2.1: Deferred to later phases
                other_actors_decisions=None,  # Phase 2: Actor interactions
                communications_context=None,   # Phase 2.2: Communication system
            )

            # Build messages for LLM
            messages = build_messages_for_llm(system_prompt, user_prompt)

            # Make LLM call
            try:
                llm_response: LLMResponse = await make_llm_call_async(
                    model=actor_config['llm_model'],
                    messages=messages,
                    api_key=self.api_key,
                    max_retries=3,
                    context={'actor': actor_name, 'turn': state.turn, 'phase': 'decision'}
                )
            except Exception as e:
                logger.error(f"LLM call failed for {actor_name}: {e}")
                raise

            # Parse response
            try:
                parsed = parse_decision(llm_response.content, json_mode=self.json_mode)
            except Exception as e:
                logger.error(f"Response parsing failed for {actor_name}: {e}")
                # Create empty decision on parse failure
                parsed = {'goals': '', 'reasoning': '', 'action': ''}

            # Create V2 Decision
            decision = Decision(
                actor=actor_name,
                turn=state.turn,
                goals=parsed.get('goals', '').split('\n') if parsed.get('goals') else [],
                reasoning=parsed.get('reasoning', ''),
                action=parsed.get('action', ''),
            )

            # Add decision to state
            state = state.with_decision(actor_name, decision)

            # Track costs
            cost_amount = calculate_cost(
                model=actor_config['llm_model'],
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens
            )

            cost_record = CostRecord(
                timestamp=datetime.now(),
                actor=actor_name,
                phase="decision",
                model=actor_config['llm_model'],
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
                cost=cost_amount,
            )
            state = state.with_cost(cost_record)

            logger.info(
                f"  ✓ Decision recorded: {llm_response.tokens_used:,} tokens "
                f"(${cost_amount:.4f})"
            )

            # Write decision to markdown file
            if self.output_dir:
                self._write_decision_file(actor_short_name, actor_name, state.turn, parsed)

        return state

    def _extract_recent_goals(self, state: ScenarioState, actor_name: str) -> str:
        """
        Extract recent goals from previous turns (last 2 turns)

        Phase 1.2: Simplified version. Will be enhanced in Phase 2.
        """
        if state.turn <= 1:
            return ""

        goals_list = []

        # Look at decisions from current state
        if actor_name in state.decisions:
            decision = state.decisions[actor_name]
            if decision.goals and decision.turn < state.turn:
                goals_text = "\n".join(f"- {g}" for g in decision.goals if g.strip())
                if goals_text:
                    goals_list.append(f"**Turn {decision.turn}:**\n{goals_text}\n")

        return "\n".join(goals_list) if goals_list else ""

    def _write_decision_file(
        self,
        actor_short_name: str,
        actor_name: str,
        turn: int,
        decision_data: Dict[str, str]
    ) -> None:
        """Write decision to markdown file"""
        if not self.output_dir:
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Format decision as markdown
        markdown = self._format_decision_markdown(actor_name, turn, decision_data)

        filename = self.output_dir / f"{actor_short_name}-{turn:03d}.md"
        with open(filename, "w") as f:
            f.write(markdown)

    def _format_decision_markdown(
        self,
        actor_name: str,
        turn: int,
        decision_data: Dict[str, str]
    ) -> str:
        """Format decision as markdown"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        markdown = f"""# {actor_name} - Turn {turn}

*Decision made at {timestamp}*

## Goals

{decision_data.get('goals', 'No goals stated')}

## Reasoning

{decision_data.get('reasoning', 'No reasoning provided')}

## Action

{decision_data.get('action', 'No action specified')}
"""
        return markdown
