"""
Scenario Orchestrator - Core execution engine for Scenario Lab V2

The orchestrator coordinates execution of scenario phases using an event-driven architecture.
It's the bridge between V1's monolithic run_scenario.py and V2's modular service architecture.

Based on ROADMAP_V2.md Phase 2.1 design.
"""
from __future__ import annotations
import uuid
import logging
from typing import Optional, Dict, Any, Protocol
from datetime import datetime

from scenario_lab.models.state import (
    ScenarioState,
    ScenarioStatus,
    PhaseType,
    WorldState,
    ActorState,
)
from scenario_lab.core.events import EventBus, EventType, get_event_bus
from scenario_lab.utils.state_persistence import StatePersistence
from scenario_lab.utils.logging_config import set_context, clear_context


logger = logging.getLogger(__name__)


class PhaseService(Protocol):
    """
    Protocol for phase services

    Each phase (communication, decision, world update, etc.) implements this interface.
    This allows the orchestrator to treat all phases uniformly.
    """

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """
        Execute this phase

        Args:
            state: Current immutable scenario state

        Returns:
            New scenario state with phase results

        Raises:
            Exception: If phase execution fails
        """
        ...


class ScenarioOrchestrator:
    """
    Central orchestrator for scenario execution

    Responsibilities:
    - Coordinate phase execution
    - Emit events for observability
    - Manage state transitions
    - Handle errors and pausing
    - Enforce credit limits

    The orchestrator doesn't implement any business logic itself - it delegates
    to phase services and coordinates the flow.
    """

    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        max_turns: Optional[int] = None,
        credit_limit: Optional[float] = None,
        output_dir: Optional[str] = None,
        save_state_every_turn: bool = True,
    ):
        """
        Initialize orchestrator

        Args:
            event_bus: Event bus for emitting events (creates one if not provided)
            max_turns: Maximum number of turns to execute
            credit_limit: Maximum cost in USD
            output_dir: Output directory for state saving
            save_state_every_turn: Whether to save state after each turn
        """
        self.event_bus = event_bus or get_event_bus()
        self.max_turns = max_turns
        self.credit_limit = credit_limit
        self.output_dir = output_dir
        self.save_state_every_turn = save_state_every_turn

        # Phase services (to be injected)
        self.phases: Dict[PhaseType, PhaseService] = {}

        # Execution state
        self.paused = False
        self.should_stop = False

    def register_phase(self, phase_type: PhaseType, service: PhaseService) -> None:
        """
        Register a phase service

        Args:
            phase_type: The type of phase
            service: The service implementing the phase
        """
        self.phases[phase_type] = service
        logger.info(f"Registered phase service: {phase_type.value}")

    async def execute(self, state: ScenarioState) -> ScenarioState:
        """
        Execute a complete scenario

        Args:
            state: Initial scenario state

        Returns:
            Final scenario state
        """
        # Set logging context for entire scenario
        set_context(scenario=state.scenario_id, run_id=state.run_id)

        # Mark as started
        state = state.with_started()

        logger.info(
            "Scenario execution started",
            extra={
                "max_turns": self.max_turns,
                "credit_limit": self.credit_limit,
            }
        )

        # Emit scenario started event
        await self.event_bus.emit(
            EventType.SCENARIO_STARTED,
            data={
                "scenario_id": state.scenario_id,
                "run_id": state.run_id,
                "max_turns": self.max_turns,
                "credit_limit": self.credit_limit,
            },
            source="orchestrator",
        )

        try:
            # Track halt reason
            halt_reason = None

            # Execute turns until completion
            while not self._should_stop_execution(state):
                state = await self.execute_turn(state)

                # Check pause flag
                if self.paused:
                    state = state.with_paused()
                    await self.event_bus.emit(
                        EventType.SCENARIO_PAUSED,
                        data={"turn": state.turn, "total_cost": state.total_cost()},
                        source="orchestrator",
                    )
                    break

                # Check stop flag
                if self.should_stop:
                    halt_reason = "Manual stop requested"
                    break

            # Check if we halted due to credit limit or manual stop
            if halt_reason or (self.paused and self.credit_limit is not None and state.total_cost() >= self.credit_limit):
                reason = halt_reason or f"Credit limit exceeded: ${state.total_cost():.2f} >= ${self.credit_limit:.2f}"
                state = state.with_halted(reason)

                logger.warning(f"Scenario halted: {reason}")

                await self.event_bus.emit(
                    EventType.SCENARIO_HALTED,
                    data={
                        "scenario_id": state.scenario_id,
                        "run_id": state.run_id,
                        "turn": state.turn,
                        "total_cost": state.total_cost(),
                        "reason": reason,
                    },
                    source="orchestrator",
                )

            # Mark as completed if still running (normal completion)
            elif state.status == ScenarioStatus.RUNNING:
                state = state.with_completed()

                logger.info(
                    "Scenario execution completed",
                    extra={
                        "turns": state.turn,
                        "total_cost": state.total_cost(),
                    }
                )

                await self.event_bus.emit(
                    EventType.SCENARIO_COMPLETED,
                    data={
                        "scenario_id": state.scenario_id,
                        "run_id": state.run_id,
                        "turns": state.turn,
                        "total_cost": state.total_cost(),
                        "status": state.status.value,
                    },
                    source="orchestrator",
                )

        except Exception as e:
            logger.error(f"Scenario execution failed: {e}", exc_info=True)
            state = state.with_error(str(e))

            await self.event_bus.emit(
                EventType.SCENARIO_FAILED,
                data={
                    "scenario_id": state.scenario_id,
                    "run_id": state.run_id,
                    "turn": state.turn,
                    "error": str(e),
                },
                source="orchestrator",
            )

        finally:
            # Clear logging context
            clear_context()

        return state

    async def execute_turn(self, state: ScenarioState) -> ScenarioState:
        """
        Execute a single turn

        A turn consists of multiple phases:
        1. Communication phase
        2. Coalition phase (if enabled)
        3. Decision phase
        4. World update phase
        5. Validation phase (if enabled)
        6. Persistence phase

        Args:
            state: Current scenario state

        Returns:
            New scenario state after turn completion
        """
        # Advance turn
        turn = state.turn + 1
        state = state.with_turn(turn)

        # Set turn context for logging
        set_context(turn=turn)

        logger.info(f"Starting turn {turn}", extra={"total_cost": state.total_cost()})

        # Emit turn started event
        await self.event_bus.emit(
            EventType.TURN_STARTED,
            data={"turn": turn, "total_cost": state.total_cost()},
            source="orchestrator",
        )

        try:
            # Execute each phase in sequence
            phase_sequence = self._get_phase_sequence(state)

            for phase_type in phase_sequence:
                if phase_type not in self.phases:
                    logger.warning(f"Phase {phase_type.value} not registered, skipping")
                    continue

                state = await self._execute_phase(phase_type, state)

                # Check credit limit after each phase
                if await self._check_credit_limit(state):
                    self.paused = True
                    break

            logger.info(
                f"Turn {turn} completed",
                extra={
                    "total_cost": state.total_cost(),
                    "decisions": len(state.decisions),
                }
            )

            # Emit turn completed event
            await self.event_bus.emit(
                EventType.TURN_COMPLETED,
                data={
                    "turn": turn,
                    "total_cost": state.total_cost(),
                    "decisions": len(state.decisions),
                    "state": state,  # Include state for event handlers
                },
                source="orchestrator",
            )

            # Save state if enabled
            if self.save_state_every_turn and self.output_dir:
                self._save_state(state)

        except Exception as e:
            logger.error(f"Turn {turn} failed: {e}", exc_info=True)

            await self.event_bus.emit(
                EventType.TURN_FAILED,
                data={"turn": turn, "error": str(e)},
                source="orchestrator",
            )
            raise

        return state

    async def _execute_phase(
        self, phase_type: PhaseType, state: ScenarioState
    ) -> ScenarioState:
        """
        Execute a single phase

        Args:
            phase_type: The type of phase to execute
            state: Current scenario state

        Returns:
            New scenario state after phase execution
        """
        # Update phase
        state = state.with_phase(phase_type)

        # Set phase context for logging
        set_context(phase=phase_type.value)

        logger.debug(f"Starting phase: {phase_type.value}")

        # Emit phase started event
        await self.event_bus.emit(
            EventType.PHASE_STARTED,
            data={"phase": phase_type.value, "turn": state.turn},
            source="orchestrator",
        )

        try:
            # Execute the phase service
            service = self.phases[phase_type]
            state = await service.execute(state)

            logger.debug(f"Phase completed: {phase_type.value}")

            # Emit phase completed event
            await self.event_bus.emit(
                EventType.PHASE_COMPLETED,
                data={"phase": phase_type.value, "turn": state.turn},
                source="orchestrator",
            )

        except Exception as e:
            logger.error(f"Phase {phase_type.value} failed: {e}", exc_info=True)

            await self.event_bus.emit(
                EventType.PHASE_FAILED,
                data={"phase": phase_type.value, "turn": state.turn, "error": str(e)},
                source="orchestrator",
            )
            raise

        return state

    def _get_phase_sequence(self, state: ScenarioState) -> list[PhaseType]:
        """
        Get the sequence of phases to execute for this turn

        This can be customized based on scenario configuration.

        Args:
            state: Current scenario state

        Returns:
            List of phase types in execution order
        """
        # Standard sequence
        sequence = [PhaseType.COMMUNICATION, PhaseType.DECISION, PhaseType.WORLD_UPDATE]

        # Add optional phases if registered
        optional_phases = [PhaseType.VALIDATION, PhaseType.PERSISTENCE]
        sequence.extend(phase for phase in optional_phases if phase in self.phases)

        return sequence

    def _should_stop_execution(self, state: ScenarioState) -> bool:
        """
        Check if execution should stop

        Args:
            state: Current scenario state

        Returns:
            True if execution should stop
        """
        # Stop if max turns reached
        if self.max_turns is not None and state.turn >= self.max_turns:
            return True

        # Stop if scenario has ended
        terminal_statuses = {ScenarioStatus.COMPLETED, ScenarioStatus.FAILED, ScenarioStatus.PAUSED}
        return state.status in terminal_statuses

    async def _check_credit_limit(self, state: ScenarioState) -> bool:
        """
        Check if credit limit has been exceeded

        Args:
            state: Current scenario state

        Returns:
            True if limit exceeded
        """
        if self.credit_limit is None:
            return False

        total_cost = state.total_cost()

        # Warning at 80%
        if total_cost >= self.credit_limit * 0.8 and total_cost < self.credit_limit:
            remaining = self.credit_limit - total_cost
            await self.event_bus.emit(
                EventType.CREDIT_LIMIT_WARNING,
                data={
                    "total_cost": total_cost,
                    "credit_limit": self.credit_limit,
                    "remaining": remaining,
                },
                source="orchestrator",
            )

        # Stop at 100%
        if total_cost >= self.credit_limit:
            await self.event_bus.emit(
                EventType.CREDIT_LIMIT_EXCEEDED,
                data={
                    "total_cost": total_cost,
                    "credit_limit": self.credit_limit,
                },
                source="orchestrator",
            )
            logger.warning(f"Credit limit exceeded: ${total_cost:.2f} >= ${self.credit_limit:.2f}")
            return True

        return False

    def pause(self) -> None:
        """Request orchestrator to pause after current turn"""
        self.paused = True
        logger.info("Pause requested")

    def resume(self) -> None:
        """Resume execution after pause"""
        self.paused = False
        logger.info("Resumed execution")

    def stop(self) -> None:
        """Request orchestrator to stop execution"""
        self.should_stop = True
        logger.info("Stop requested")

    def _save_state(self, state: ScenarioState) -> None:
        """
        Save current state to disk

        Args:
            state: Current scenario state
        """
        if not self.output_dir:
            return

        try:
            StatePersistence.save_state(state, self.output_dir)
        except Exception as e:
            logger.error(f"Failed to save state: {e}", exc_info=True)
            # Don't fail execution on save errors
