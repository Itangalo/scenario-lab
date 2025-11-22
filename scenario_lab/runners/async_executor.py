"""
Async Executor for Scenario Lab V2

Provides fully async execution for web API integration with real-time event streaming.
Designed for WebSocket connections, human-in-the-loop, and reactive UIs.
"""
from __future__ import annotations
import asyncio
import logging
from pathlib import Path
from typing import Optional, AsyncIterator, Dict, Any
from datetime import datetime

from scenario_lab.core.orchestrator import ScenarioOrchestrator, PhaseType
from scenario_lab.core.events import EventBus, Event, EventType
from scenario_lab.models.state import ScenarioState, ScenarioStatus
from scenario_lab.loaders import ScenarioLoader
from scenario_lab.runners.sync_runner import SyncRunner
from scenario_lab.utils.logging_config import setup_logging, set_context, clear_context

logger = logging.getLogger(__name__)


class AsyncExecutor:
    """
    Async executor for web API integration

    Key features:
    - Fully async execution
    - Real-time event streaming
    - Human-in-the-loop support (pause/resume)
    - WebSocket-ready
    - Progress tracking
    """

    def __init__(
        self,
        scenario_path: str,
        output_path: Optional[str] = None,
        max_turns: Optional[int] = None,
        credit_limit: Optional[float] = None,
        json_mode: bool = False,
        log_level: str = "INFO",
    ):
        """
        Initialize async executor

        Args:
            scenario_path: Path to scenario directory
            output_path: Path to output directory
            max_turns: Maximum number of turns to execute
            credit_limit: Maximum cost in USD
            json_mode: Whether to use JSON response format for actors
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.scenario_path = scenario_path
        self.output_path = output_path
        self.max_turns = max_turns
        self.credit_limit = credit_limit
        self.json_mode = json_mode

        # Setup structured logging
        setup_logging(level=log_level, format_type="colored")

        # Will be initialized in setup()
        self.sync_runner: Optional[SyncRunner] = None
        self.orchestrator: Optional[ScenarioOrchestrator] = None
        self.event_bus: Optional[EventBus] = None
        self.initial_state: Optional[ScenarioState] = None

        # Event subscribers
        self._event_handlers: Dict[EventType, list] = {}

        # Human-in-the-loop control
        self._paused = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Start unpaused

    async def setup(self) -> None:
        """Initialize executor components asynchronously"""
        logger.info(f"Setting up async executor for: {self.scenario_path}")

        # Use SyncRunner for component initialization (reuse existing code)
        self.sync_runner = SyncRunner(
            scenario_path=self.scenario_path,
            output_path=self.output_path,
            end_turn=self.max_turns,  # SyncRunner uses end_turn, AsyncExecutor uses max_turns
            credit_limit=self.credit_limit,
            json_mode=self.json_mode,
        )

        # Setup the runner (initializes all components)
        self.sync_runner.setup()

        # Extract components we need
        self.orchestrator = self.sync_runner.orchestrator
        self.event_bus = self.sync_runner.event_bus
        self.initial_state = self.sync_runner.initial_state

        # Subscribe to all events for streaming
        await self._setup_event_handlers()

        logger.info("Async executor setup complete")

    async def _setup_event_handlers(self) -> None:
        """Setup internal event handlers"""
        # Log all events
        self.event_bus.on(
            EventType.TURN_STARTED.value,
            self._on_turn_started
        )
        self.event_bus.on(
            EventType.TURN_COMPLETED.value,
            self._on_turn_completed
        )
        self.event_bus.on(
            EventType.PHASE_STARTED.value,
            self._on_phase_started
        )
        self.event_bus.on(
            EventType.PHASE_COMPLETED.value,
            self._on_phase_completed
        )
        self.event_bus.on(
            EventType.SCENARIO_COMPLETED.value,
            self._on_scenario_completed
        )
        self.event_bus.on(
            EventType.SCENARIO_FAILED.value,
            self._on_scenario_failed
        )

    async def _on_turn_started(self, event: Event) -> None:
        """Handle turn started event"""
        logger.info(f"Turn {event.data['turn']} started")

    async def _on_turn_completed(self, event: Event) -> None:
        """Handle turn completed event"""
        logger.info(
            f"Turn {event.data['turn']} completed "
            f"(${event.data.get('total_cost', 0):.4f} total)"
        )

    async def _on_phase_started(self, event: Event) -> None:
        """Handle phase started event"""
        logger.debug(f"Phase started: {event.data['phase']}")

    async def _on_phase_completed(self, event: Event) -> None:
        """Handle phase completed event"""
        logger.debug(f"Phase completed: {event.data['phase']}")

    async def _on_scenario_completed(self, event: Event) -> None:
        """Handle scenario completion event"""
        logger.info(
            f"Scenario completed in {event.data['turns']} turns "
            f"(${event.data['total_cost']:.4f})"
        )

    async def _on_scenario_failed(self, event: Event) -> None:
        """Handle scenario failure event"""
        logger.error(f"Scenario failed: {event.data.get('error', 'Unknown error')}")

    async def execute(self) -> ScenarioState:
        """
        Execute scenario asynchronously

        Returns:
            Final scenario state
        """
        if not self.orchestrator or not self.initial_state:
            raise RuntimeError("Executor not initialized. Call setup() first.")

        # Set logging context
        set_context(
            scenario=self.initial_state.scenario_id,
            run_id=self.initial_state.run_id
        )

        try:
            # Execute scenario
            final_state = await self.orchestrator.execute(self.initial_state)

            return final_state

        finally:
            clear_context()

    async def execute_with_streaming(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Execute scenario with real-time event streaming

        Yields:
            Event dictionaries suitable for WebSocket transmission
        """
        if not self.orchestrator or not self.initial_state:
            raise RuntimeError("Executor not initialized. Call setup() first.")

        # Create event queue for streaming
        event_queue: asyncio.Queue = asyncio.Queue()

        # Subscribe a handler that puts events in queue
        async def stream_handler(event: Event) -> None:
            await event_queue.put({
                'type': event.event_type.value,
                'data': event.data,
                'timestamp': event.timestamp.isoformat(),
                'source': event.source,
            })

        # Subscribe to all event types
        for event_type in EventType:
            self.event_bus.on(event_type.value, stream_handler)

        # Start execution in background
        execution_task = asyncio.create_task(self.execute())

        try:
            # Stream events as they arrive
            while not execution_task.done():
                try:
                    # Wait for event with timeout
                    event_data = await asyncio.wait_for(
                        event_queue.get(),
                        timeout=0.1
                    )
                    yield event_data
                except asyncio.TimeoutError:
                    # No event, check if paused
                    if self._paused:
                        yield {
                            'type': 'paused',
                            'data': {'message': 'Execution paused'},
                            'timestamp': datetime.now().isoformat(),
                        }
                        # Wait for resume
                        await self._pause_event.wait()
                    continue

            # Execution finished, get final state
            final_state = await execution_task

            # Yield completion event
            yield {
                'type': 'execution_complete',
                'data': {
                    'turns': final_state.turn,
                    'total_cost': final_state.total_cost(),
                    'status': final_state.status.value,
                },
                'timestamp': datetime.now().isoformat(),
            }

        finally:
            # Cleanup: unsubscribe handler
            for event_type in EventType:
                self.event_bus.off(event_type.value, stream_handler)

    async def pause(self) -> None:
        """Pause execution (for human-in-the-loop)"""
        logger.info("Pausing execution")
        self._paused = True
        self._pause_event.clear()

    async def resume(self) -> None:
        """Resume execution"""
        logger.info("Resuming execution")
        self._paused = False
        self._pause_event.set()

    async def stop(self) -> None:
        """Stop execution gracefully"""
        logger.info("Stopping execution")
        if self.orchestrator:
            self.orchestrator.should_stop = True

    @property
    def is_paused(self) -> bool:
        """Check if execution is paused"""
        return self._paused

    async def get_current_state(self) -> Optional[ScenarioState]:
        """
        Get current scenario state (for monitoring)

        Returns:
            Current state if available
        """
        # This would require orchestrator to expose current state
        # For now, return None - could be enhanced
        return None

    async def cleanup(self) -> None:
        """Cleanup resources"""
        logger.info("Cleaning up async executor")
        clear_context()


async def run_scenario_async(
    scenario_path: str,
    output_path: Optional[str] = None,
    max_turns: Optional[int] = None,
    credit_limit: Optional[float] = None,
    json_mode: bool = False,
) -> ScenarioState:
    """
    Convenience function to run a scenario asynchronously

    Args:
        scenario_path: Path to scenario directory
        output_path: Path to output directory
        max_turns: Maximum number of turns
        credit_limit: Maximum cost in USD
        json_mode: Whether to use JSON response format

    Returns:
        Final scenario state
    """
    executor = AsyncExecutor(
        scenario_path=scenario_path,
        output_path=output_path,
        max_turns=max_turns,
        credit_limit=credit_limit,
        json_mode=json_mode,
    )

    await executor.setup()
    final_state = await executor.execute()
    await executor.cleanup()

    return final_state
