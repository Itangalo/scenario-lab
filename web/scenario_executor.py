"""
Scenario Executor for Web Interface

Wraps scenario execution with web API integration:
- Pauses for human actor decisions
- Sends WebSocket updates
- Handles async execution

NOTE: This is a Phase 3 implementation that simulates execution flow.
Phase 2.1 will integrate with the actual run_scenario.py components.

Phase 2.0 Update: Now uses Pydantic schemas for validation.
"""
import asyncio
import yaml
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from pydantic import ValidationError

# Add src to path for schema imports
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from schemas import (
        ScenarioConfig, ActorConfig, MetricsConfig, ValidationConfig,
        load_scenario_config, load_actor_config
    )
    SCHEMAS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import schemas: {e}")
    SCHEMAS_AVAILABLE = False
    ScenarioConfig = None
    ActorConfig = None


class SimpleCostTracker:
    """Simplified cost tracker for Phase 3"""
    def __init__(self):
        self.total_cost = 0.0

    def get_total_cost(self) -> float:
        return self.total_cost


@dataclass
class HumanDecision:
    """Container for human actor decision"""
    long_term_goals: list[str]
    short_term_priorities: list[str]
    reasoning: str
    action: str


class ScenarioExecutor:
    """
    Executes scenarios with web API integration

    Handles:
    - Pausing for human actors
    - WebSocket status updates
    - Async execution in background
    """

    def __init__(self, scenario_path: str, max_turns: Optional[int] = None,
                 credit_limit: Optional[float] = None):
        """
        Initialize scenario executor

        Args:
            scenario_path: Path to scenario directory
            max_turns: Optional maximum number of turns
            credit_limit: Optional cost limit in dollars
        """
        self.scenario_path = scenario_path
        self.max_turns = max_turns
        self.credit_limit = credit_limit

        # State
        self.current_turn = 0
        self.is_running = False
        self.is_paused = False
        self.waiting_for_actor: Optional[str] = None
        self.pending_human_decision: Optional[HumanDecision] = None

        # Components (simplified for Phase 3)
        self.cost_tracker = SimpleCostTracker()
        self.actors: Dict[str, Dict] = {}  # Will be loaded from scenario.yaml
        self.scenario_data: Optional[Dict] = None

        # Callbacks
        self.status_callback: Optional[Callable] = None
        self.turn_complete_callback: Optional[Callable] = None

    def set_status_callback(self, callback: Callable):
        """Set callback for status updates (for WebSocket broadcasting)"""
        self.status_callback = callback

    def set_turn_complete_callback(self, callback: Callable):
        """Set callback when turn completes"""
        self.turn_complete_callback = callback

    async def _broadcast_status(self, event_type: str, data: Optional[Dict] = None):
        """Broadcast status update via callback"""
        if self.status_callback:
            status_data = {
                'type': event_type,
                'current_turn': self.current_turn,
                'is_running': self.is_running,
                'is_paused': self.is_paused,
                'waiting_for_actor': self.waiting_for_actor,
                'total_cost': self.cost_tracker.get_total_cost(),
            }
            if data:
                status_data.update(data)

            await self.status_callback(status_data)

    async def setup(self):
        """
        Initialize scenario components

        Now includes Pydantic validation (Phase 2.0):
        - Validates scenario.yaml structure
        - Validates actor YAML files
        - Provides clear error messages for invalid configs
        """
        try:
            # Load scenario.yaml
            scenario_path = Path(self.scenario_path)
            scenario_file = scenario_path / 'scenario.yaml'

            if not scenario_file.exists():
                print(f"Error: scenario.yaml not found at {scenario_file}")
                return False

            with open(scenario_file, 'r') as f:
                scenario_yaml = yaml.safe_load(f)

            # Validate scenario config if schemas available
            if SCHEMAS_AVAILABLE:
                try:
                    validated_scenario = load_scenario_config(scenario_yaml)
                    self.scenario_data = validated_scenario.dict()
                    print(f"✓ Validated scenario config (schema v{validated_scenario.schema_version})")
                except ValidationError as e:
                    print(f"⚠ Scenario validation failed:")
                    for error in e.errors():
                        field = " -> ".join(str(loc) for loc in error['loc'])
                        print(f"  {field}: {error['msg']}")
                    print(f"  Continuing with unvalidated data...")
                    self.scenario_data = scenario_yaml
            else:
                self.scenario_data = scenario_yaml

            # Load actor files from actors/ directory
            actors_dir = scenario_path / 'actors'
            if actors_dir.exists():
                for actor_file in actors_dir.glob('*.yaml'):
                    with open(actor_file, 'r') as f:
                        actor_yaml = yaml.safe_load(f)
                        actor_name = actor_file.stem

                    # Validate actor config if schemas available
                    if SCHEMAS_AVAILABLE:
                        try:
                            validated_actor = load_actor_config(actor_yaml)
                            self.actors[actor_name] = validated_actor.dict()
                            print(f"✓ Validated actor: {validated_actor.name} ({validated_actor.control})")
                        except ValidationError as e:
                            print(f"⚠ Actor '{actor_name}' validation failed:")
                            for error in e.errors():
                                field = " -> ".join(str(loc) for loc in error['loc'])
                                print(f"  {field}: {error['msg']}")
                            print(f"  Continuing with unvalidated data...")
                            self.actors[actor_name] = actor_yaml
                    else:
                        self.actors[actor_name] = actor_yaml

            print(f"✓ Loaded scenario with {len(self.actors)} actors")
            return True

        except Exception as e:
            print(f"Setup error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_actors_info(self) -> list[Dict[str, Any]]:
        """Get actor information"""
        return [
            {
                'name': actor_name,
                'control': actor_config.get('control', 'ai'),
                'status': 'waiting'
            }
            for actor_name, actor_config in self.actors.items()
        ]

    async def run(self):
        """
        Run scenario execution

        This is the main execution loop that:
        - Runs turns sequentially
        - Pauses for human actors
        - Sends status updates
        - Checks limits
        """
        self.is_running = True

        try:
            # Setup if not already done
            if not self.actors:
                success = await self.setup()
                if not success:
                    self.is_running = False
                    return

            # Main execution loop
            while self.is_running:
                # Check if we've hit max turns
                if self.max_turns and self.current_turn >= self.max_turns:
                    await self._broadcast_status('scenario_complete', {
                        'reason': 'max_turns_reached'
                    })
                    break

                # Check credit limit
                if self.credit_limit and self.cost_tracker:
                    if self.cost_tracker.get_total_cost() >= self.credit_limit:
                        await self._broadcast_status('scenario_halted', {
                            'reason': 'credit_limit_reached'
                        })
                        break

                # Execute turn
                await self.execute_turn()

                # Wait a bit between turns
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Execution error: {e}")
            import traceback
            traceback.print_exc()
            await self._broadcast_status('error', {'error': str(e)})

        finally:
            self.is_running = False

    async def execute_turn(self):
        """Execute a single turn"""
        self.current_turn += 1

        await self._broadcast_status('turn_start', {'turn': self.current_turn})

        # For each actor, get decision
        for actor_name in self.actors.keys():
            actor_config = self.actors[actor_name]
            control_type = actor_config.get('control', 'ai')

            if control_type == 'human':
                # Pause and wait for human decision
                await self._wait_for_human_decision(actor_name)
            else:
                # Get AI decision
                await self._get_ai_decision(actor_name)

        # Turn complete
        if self.turn_complete_callback:
            await self.turn_complete_callback(self.current_turn)

        await self._broadcast_status('turn_complete', {'turn': self.current_turn})

    async def _wait_for_human_decision(self, actor_name: str):
        """
        Pause execution and wait for human to submit decision

        This is the core human-in-the-loop feature:
        - Pauses scenario execution
        - Broadcasts waiting status via WebSocket
        - Waits for decision from web interface
        - Resumes execution after decision received
        """
        self.is_paused = True
        self.waiting_for_actor = actor_name

        await self._broadcast_status('waiting_for_human', {
            'actor': actor_name,
            'turn': self.current_turn,
            'message': f'Waiting for {actor_name} to make a decision'
        })

        # Wait for decision to be submitted (max 5 minutes)
        timeout_seconds = 300
        elapsed = 0
        while self.pending_human_decision is None and self.is_running and elapsed < timeout_seconds:
            await asyncio.sleep(0.5)
            elapsed += 0.5

        # Process the decision
        if self.pending_human_decision:
            decision = self.pending_human_decision

            await self._broadcast_status('human_decision_processed', {
                'actor': actor_name,
                'turn': self.current_turn,
                'decision': decision.action,
                'reasoning': decision.reasoning
            })

            # Clear for next human decision
            self.pending_human_decision = None

        elif not self.is_running:
            await self._broadcast_status('scenario_stopped', {
                'reason': 'user_stopped',
                'actor': actor_name,
                'turn': self.current_turn
            })

        else:  # timeout
            await self._broadcast_status('timeout', {
                'actor': actor_name,
                'turn': self.current_turn,
                'message': 'Human decision timeout after 5 minutes'
            })

        self.is_paused = False
        self.waiting_for_actor = None

    async def _get_ai_decision(self, actor_name: str):
        """
        Get AI actor decision

        NOTE: Phase 3 simulates AI decision making.
        Phase 2.1 will integrate with actual ActorEngine.
        """
        await self._broadcast_status('actor_thinking', {
            'actor': actor_name,
            'turn': self.current_turn
        })

        # Simulate AI thinking time (1-2 seconds)
        await asyncio.sleep(1.5)

        # Simulate cost accumulation
        self.cost_tracker.total_cost += 0.01  # Simulate ~$0.01 per decision

        await self._broadcast_status('actor_complete', {
            'actor': actor_name,
            'turn': self.current_turn,
            'decision': f'Simulated decision from {actor_name}'
        })

    def submit_human_decision(self, decision: HumanDecision):
        """Submit human actor decision"""
        self.pending_human_decision = decision

    def pause(self):
        """Pause execution"""
        self.is_paused = True

    def resume(self):
        """Resume execution"""
        self.is_paused = False

    def stop(self):
        """Stop execution"""
        self.is_running = False
