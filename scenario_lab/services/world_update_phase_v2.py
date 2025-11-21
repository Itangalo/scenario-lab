"""
World Update Phase Service for Scenario Lab V2

Synthesizes new world state from actor decisions using V2 components (no V1 dependencies).

Phase 1.3 Implementation + Phase 3.3-3.4 Enhancements:
- Uses V2 WorldSynthesizer for prompt building
- Uses V2 API client for LLM calls
- Updates ScenarioState.world_state immutably
- Tracks costs via ScenarioState
- ✅ Phase 3.3: Metrics extraction from world state
- ✅ Phase 3.4: QA validation of world state coherence
- Defers exogenous events to Phase 3 (stub)
"""
from __future__ import annotations
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import replace

from scenario_lab.models.state import ScenarioState, WorldState, CostRecord
from scenario_lab.utils.api_client import make_llm_call_async, LLMResponse
from scenario_lab.core.world_synthesizer import WorldSynthesizer, WorldUpdateResult
from scenario_lab.core.prompt_builder import build_messages_for_llm
from scenario_lab.utils.model_pricing import calculate_cost

logger = logging.getLogger(__name__)


class WorldUpdatePhaseV2:
    """
    Phase service for world state updates (V2 - Pure implementation)

    This phase:
    1. Gathers all actor decisions from current turn
    2. Calls WorldSynthesizer to build prompts
    3. Makes LLM call to synthesize new world state
    4. Parses response (updated state, key changes, consequences)
    5. Updates ScenarioState.world_state
    6. Tracks costs
    7. Writes world state to markdown file
    """

    def __init__(
        self,
        scenario_name: str,
        world_state_model: str = "openai/gpt-4o-mini",
        output_dir: Optional[str] = None,
        metrics_tracker: Optional[Any] = None,  # MetricsTracker from Phase 3.3
        qa_validator: Optional[Any] = None,  # QAValidator from Phase 3.4
    ):
        """
        Initialize world update phase

        Args:
            scenario_name: Name of the scenario
            world_state_model: LLM model for world state synthesis
            output_dir: Optional directory to save world state markdown files
            metrics_tracker: Optional MetricsTracker for metrics extraction
            qa_validator: Optional QAValidator for validation
        """
        self.scenario_name = scenario_name
        self.world_state_model = world_state_model
        self.output_dir = Path(output_dir) if output_dir else None
        self.api_key = os.environ.get('OPENROUTER_API_KEY')
        self.metrics_tracker = metrics_tracker  # Phase 3.3
        self.qa_validator = qa_validator  # Phase 3.4

        # Create synthesizer
        self.synthesizer = WorldSynthesizer(
            model=world_state_model,
            scenario_name=scenario_name
        )

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
        total_turns = state.scenario_config.get("num_turns") or state.scenario_config.get("turns", 10)

        # Prepare actor decisions for world state update
        actor_decisions_for_update = {}
        for actor_name, decision in state.decisions.items():
            actor_decisions_for_update[actor_name] = {
                "action": decision.action,
                "reasoning": decision.reasoning
            }

        # Phase 1.3: Stub for exogenous events (to be implemented in Phase 3)
        exogenous_events = None  # Will be implemented in Phase 3

        # Build prompts using synthesizer
        system_prompt = self.synthesizer.build_system_prompt()
        user_prompt = self.synthesizer.build_user_prompt(
            current_state=current_state,
            turn=state.turn,
            total_turns=total_turns,
            actor_decisions=actor_decisions_for_update,
            exogenous_events=exogenous_events
        )

        # Build messages for LLM
        messages = build_messages_for_llm(system_prompt, user_prompt)

        # Make LLM call
        try:
            llm_response: LLMResponse = await make_llm_call_async(
                model=self.world_state_model,
                messages=messages,
                api_key=self.api_key,
                max_retries=3,
                context={'turn': state.turn, 'phase': 'world_update'}
            )
        except Exception as e:
            logger.error(f"LLM call failed for world update: {e}")
            raise

        # Parse response
        try:
            parsed = self.synthesizer.parse_world_update_response(llm_response.content)
        except Exception as e:
            logger.error(f"Response parsing failed for world update: {e}")
            # Create minimal update on parse failure
            parsed = {
                'updated_state': llm_response.content,
                'key_changes': [],
                'consequences': []
            }

        # Create new world state
        new_world_state = WorldState(
            turn=state.turn,
            content=parsed['updated_state'],
            timestamp=datetime.now()
        )

        # Update state with new world state
        state = replace(state, world_state=new_world_state)

        # Note: Turn number is managed by orchestrator, not by individual phases
        # The orchestrator increments turn at the start of execute_turn()
        # so we should NOT increment it here

        # Track costs
        cost_amount = calculate_cost(
            model=self.world_state_model,
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens
        )

        cost_record = CostRecord(
            timestamp=datetime.now(),
            actor=None,  # World update is not actor-specific
            phase="world_update",
            model=self.world_state_model,
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens,
            cost=cost_amount,
        )
        state = state.with_cost(cost_record)

        logger.info(f"  ✓ World state updated: {llm_response.tokens_used:,} tokens "
            f"(${cost_amount:.4f})"
        )
        logger.info(f"  ✓ {len(parsed['key_changes'])} key changes identified")
        logger.info(f"  ✓ {len(parsed['consequences'])} consequences noted")

        # Phase 3.3: Extract metrics from world state
        if self.metrics_tracker:
            metrics = await self.metrics_tracker.extract_metrics_from_world_state(state)
            if metrics:
                for metric in metrics:
                    state = state.with_metric(metric)
                logger.info(f"  ✓ Extracted {len(metrics)} metrics from world state")

        # Phase 3.4: Validate world state coherence
        if self.qa_validator and self.qa_validator.is_enabled():
            # Get previous world state (before this update)
            # Note: We've already incremented the turn, so state.turn is now turn+1
            previous_ws_content = current_state  # We saved this at the start

            # Validate world state coherence
            validation_result = await self.qa_validator.validate_world_state_update(
                previous_world_state=previous_ws_content,
                actor_actions={name: d.action for name, d in state.decisions.items()},
                new_world_state=parsed['updated_state'],
                turn=state.turn - 1  # Previous turn
            )

            if validation_result:
                # Log validation result
                if validation_result.passed:
                    logger.info(f"  ✓ QA validation passed: {validation_result.check_name}")
                else:
                    logger.warning(
                        f"  ⚠️  QA validation failed: {validation_result.check_name} "
                        f"(severity: {validation_result.severity})"
                    )
                    for issue in validation_result.issues:
                        logger.warning(f"    - {issue}")

                # Track validation cost
                cost_record = self.qa_validator.create_cost_record(validation_result, state.turn - 1)
                state = state.with_cost(cost_record)

        # Write world state to markdown file
        if self.output_dir:
            self._write_world_state_file(
                state.turn - 1,  # Previous turn (since we just incremented)
                parsed,
                llm_response.content
            )

        return state

    def _write_world_state_file(
        self,
        turn: int,
        parsed_data: Dict[str, Any],
        full_response: str
    ) -> None:
        """Write world state to markdown file"""
        if not self.output_dir:
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Format world state as markdown
        markdown = self._format_world_state_markdown(turn, parsed_data, full_response)

        filename = self.output_dir / f"world-state-{turn:03d}.md"
        with open(filename, "w") as f:
            f.write(markdown)

    def _format_world_state_markdown(
        self,
        turn: int,
        parsed_data: Dict[str, Any],
        full_response: str
    ) -> str:
        """Format world state as markdown"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Format key changes
        key_changes_text = "\n".join(
            f"- {change}" for change in parsed_data.get('key_changes', [])
        ) or "No key changes identified"

        # Format consequences
        consequences_text = "\n".join(
            f"- {cons}" for cons in parsed_data.get('consequences', [])
        ) or "No consequences noted"

        markdown = f"""# World State - Turn {turn}

*Updated at {timestamp}*

## Current Situation

{parsed_data.get('updated_state', 'No state description')}

## Key Changes This Turn

{key_changes_text}

## Consequences

{consequences_text}

---

<details>
<summary>Full LLM Response</summary>

```
{full_response}
```

</details>
"""
        return markdown
