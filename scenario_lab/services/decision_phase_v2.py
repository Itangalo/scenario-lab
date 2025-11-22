"""
Decision Phase Service for Scenario Lab V2

Handles actor decision-making using V2 components (no V1 dependencies).

Phase 2.2 Updates:
- ✅ Uses V2 API client for LLM calls
- ✅ Uses V2 prompt builder for prompt construction
- ✅ Uses V2 response parser for parsing
- ✅ Tracks costs via ScenarioState
- ✅ Uses V2 ContextManager for context windowing (Phase 2.1)
- ✅ Uses V2 CommunicationManager for communication context (Phase 2.2)
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
from scenario_lab.core.communication_manager import format_communications_for_context

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
        metrics_tracker: Optional[Any] = None,  # MetricsTracker from Phase 3.3
    ):
        """
        Initialize decision phase

        Args:
            actor_configs: Dictionary of actor short names to actor config dicts
            scenario_system_prompt: System prompt from scenario configuration
            output_dir: Optional directory to save decision markdown files
            json_mode: Whether to use JSON response format (default: False)
            metrics_tracker: Optional MetricsTracker for metrics extraction
            context_window_size: Number of recent turns to keep in full detail (default: 3)
        """
        self.actor_configs = actor_configs
        self.scenario_system_prompt = scenario_system_prompt
        self.output_dir = Path(output_dir) if output_dir else None
        self.json_mode = json_mode
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        self.metrics_tracker = metrics_tracker  # Phase 3.3

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

            # Phase 2.2: Get communication context for this actor
            communications_context = format_communications_for_context(
                state=state,
                actor_name=actor_name,
                turn=state.turn
            )

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
                communications_context=communications_context,  # Phase 2.2: Now included
                # Phase 2+: Deferred to later phases
                other_actors_decisions=None,  # Future: Actor interactions/simultaneous reveal
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

            # Show actor name and preview of decision
            action_preview = decision.action[:20].replace('\n', ' ') if decision.action else ""
            if len(decision.action) > 20:
                action_preview += "..."

            # Write decision to markdown file and get path for link
            if self.output_dir:
                filepath = self._write_decision_file(actor_short_name, actor_name, state.turn, parsed)
                # Create terminal hyperlink on the preview text (OSC 8 format)
                linked_preview = f"\033]8;;file://{filepath}\033\\\"{action_preview}\"\033]8;;\033\\"
            else:
                linked_preview = f"\"{action_preview}\""

            logger.info(
                f"  ✓ {actor_name}: {linked_preview} "
                f"({llm_response.tokens_used:,} tokens, ${cost_amount:.4f})"
            )

        # Phase 3.3: Extract metrics from all decisions after all actors have decided
        if self.metrics_tracker:
            metrics = await self.metrics_tracker.extract_metrics_from_decisions(state)
            if metrics:
                for metric in metrics:
                    state = state.with_metric(metric)
                logger.info(f"  ✓ Extracted {len(metrics)} metrics from actor decisions")

        return state

    def _extract_recent_goals(self, state: ScenarioState, actor_name: str) -> str:
        """
        Extract recent goals from previous turns (last 2 turns)

        Uses persistent actor state (recent_decisions) rather than the per-turn
        decisions dictionary which gets cleared each turn.
        """
        if state.turn <= 1:
            return ""

        goals_list = []

        # Look at decisions from persistent actor state
        if actor_name in state.actors:
            actor_state = state.actors[actor_name]
            # Get up to the last 2 decisions from the actor's history
            recent = actor_state.recent_decisions[-2:]
            for decision in recent:
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
    ) -> Optional[Path]:
        """Write decision to markdown file and return the filepath"""
        if not self.output_dir:
            return None

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Format decision as markdown
        markdown = self._format_decision_markdown(actor_name, turn, decision_data)

        filepath = self.output_dir / f"{actor_short_name}-{turn:03d}.md"
        with open(filepath, "w") as f:
            f.write(markdown)

        return filepath.resolve()

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
