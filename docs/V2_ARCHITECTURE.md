# Scenario Lab Version 2 - Architecture Documentation

## Overview

Version 2 represents a complete architectural evolution of Scenario Lab while maintaining full backward compatibility with V1. The new architecture enables web integration, better testing, and scalable batch processing through event-driven design and immutable state management.

**Current Status**: Phase 2.0 Foundation (Alpha)

## Core Principles

### 1. Event-Driven Architecture

All components communicate through events rather than direct coupling. This enables:

- **Observability**: Every state change emits events that can be monitored
- **WebSocket Integration**: Web clients subscribe to events for real-time updates
- **Metrics Tracking**: Metrics are event handlers
- **Logging**: Structured logging via event handlers
- **Testing**: Mock components by subscribing to events

**Example**:
```python
from scenario_lab import EventBus, EventType

bus = EventBus()

@bus.on(EventType.TURN_COMPLETED)
async def log_turn(event):
    print(f"Turn {event.data['turn']} cost: ${event.data['total_cost']:.2f}")

await bus.emit(EventType.TURN_COMPLETED, data={"turn": 1, "total_cost": 0.15})
```

### 2. Immutable State

State objects are immutable (frozen dataclasses). Phases return new state rather than mutating existing state.

**Benefits**:
- Can rollback to any previous state
- Phases can't accidentally corrupt state
- Easy to implement branching
- Safe for parallel execution
- Time-travel debugging

**Example**:
```python
from scenario_lab import ScenarioState, WorldState

# State is immutable
state = ScenarioState(scenario_id="test", scenario_name="Test", run_id="run-001")

# Transformations return new state
new_state = state.with_turn(1)
assert state.turn == 0  # Original unchanged
assert new_state.turn == 1  # New state has change

# Can chain transformations
final_state = (
    state
    .with_turn(1)
    .with_world_state(WorldState(turn=1, content="Updated world"))
    .with_started()
)
```

### 3. Phase Services

Execution is broken into independent phase services:

1. **CommunicationPhase**: Handle bilateral/coalition communications
2. **DecisionPhase**: Process actor decisions
3. **WorldUpdatePhase**: Synthesize new world state
4. **ValidationPhase**: QA consistency checking
5. **PersistencePhase**: Save state to disk/database

Each phase:
- Is independently testable
- Receives immutable state
- Returns new immutable state
- Emits events for observability
- Has no side effects (except I/O)

**Interface**:
```python
from scenario_lab import PhaseService, ScenarioState

class CustomPhase:
    async def execute(self, state: ScenarioState) -> ScenarioState:
        # Do work
        new_state = state.with_some_change()
        return new_state
```

### 4. Central Orchestrator

The `ScenarioOrchestrator` coordinates phase execution:

```python
from scenario_lab import ScenarioOrchestrator, ScenarioState

orchestrator = ScenarioOrchestrator(max_turns=10, credit_limit=5.0)

# Register phases
orchestrator.register_phase(PhaseType.DECISION, DecisionPhase())
orchestrator.register_phase(PhaseType.WORLD_UPDATE, WorldUpdatePhase())

# Execute
initial_state = ScenarioState(...)
final_state = await orchestrator.execute(initial_state)
```

The orchestrator:
- Executes phases in sequence
- Emits lifecycle events
- Enforces credit limits
- Handles pausing/resuming
- Manages error recovery

### 5. Backward Compatibility

V1 continues to work unchanged:

```bash
# V1 (still works)
python src/run_scenario.py scenarios/ai-summit

# V2 (new interface, same behavior)
scenario-lab run scenarios/ai-summit
```

Strategy:
- V1 code stays in `src/` (frozen)
- V2 code in `scenario_lab/` package
- V1 scenarios work in V2 without changes
- Migration is opt-in, not forced

## Directory Structure

```
scenario-lab/
├── src/                          # V1 code (frozen but functional)
│   ├── run_scenario.py
│   ├── actor_engine.py
│   └── ...
├── scenario_lab/                 # V2 package
│   ├── __init__.py
│   ├── cli.py                    # Entry point for scenario-lab command
│   ├── core/                     # Core execution engine
│   │   ├── events.py            # Event bus and event types
│   │   └── orchestrator.py      # Scenario orchestrator
│   ├── models/                   # Data models
│   │   └── state.py             # Immutable state models
│   ├── services/                 # Phase services
│   │   ├── communication.py     # Communication phase
│   │   ├── decision.py          # Decision phase
│   │   ├── world_update.py      # World update phase
│   │   ├── validation.py        # Validation phase
│   │   └── persistence.py       # Persistence phase
│   ├── interfaces/               # User interfaces
│   │   ├── cli.py               # Command-line interface
│   │   ├── api.py               # FastAPI web API
│   │   └── sdk.py               # Python SDK
│   └── utils/                    # Utilities
│       ├── schemas.py           # Pydantic schemas
│       └── cost.py              # Cost tracking utilities
├── tests/                        # V1 tests (existing)
├── scenario_lab/tests/           # V2 tests (new)
├── docs/
│   ├── V2_ARCHITECTURE.md       # This file
│   ├── V2_MIGRATION.md          # Migration guide
│   └── ...
├── pyproject.toml                # Package configuration
└── README.md                     # Project overview
```

## Data Flow

### V1 (String-Based)
```
Actor → Markdown → Regex Parse → Internal State → Markdown File
```
Problems:
- Fragile parsing
- Data loss risk
- Hard to validate

### V2 (Structured with Views)
```
Actor → JSON Schema → Validated Data → {
    ├─ Internal State (structured)
    ├─ Markdown View (generated)
    └─ Database Record (analytics)
}
```
Benefits:
- Type-safe
- Lossless
- Machine-readable + human-readable

## Event System

### Event Types

Defined in `EventType` enum:

**Scenario Lifecycle**:
- `SCENARIO_STARTED`
- `SCENARIO_COMPLETED`
- `SCENARIO_FAILED`
- `SCENARIO_PAUSED`
- `SCENARIO_RESUMED`

**Turn Lifecycle**:
- `TURN_STARTED`
- `TURN_COMPLETED`
- `TURN_FAILED`

**Phase Lifecycle**:
- `PHASE_STARTED`
- `PHASE_COMPLETED`
- `PHASE_FAILED`

**Actor Events**:
- `ACTOR_DECISION_STARTED`
- `ACTOR_DECISION_COMPLETED`
- `ACTOR_DECISION_FAILED`

**Cost Events**:
- `COST_INCURRED`
- `CREDIT_LIMIT_WARNING`
- `CREDIT_LIMIT_EXCEEDED`

**Metrics Events**:
- `METRIC_RECORDED`

### Event Structure

```python
@dataclass(frozen=True)
class Event:
    type: str                      # Event type (e.g., "turn_completed")
    data: Dict[str, Any]          # Event payload
    timestamp: float              # Unix timestamp
    source: Optional[str]         # Source component
    correlation_id: Optional[str] # For tracing related events
```

### Event Handlers

```python
from scenario_lab import get_event_bus, EventType

bus = get_event_bus()

@bus.on(EventType.TURN_COMPLETED)
async def handle_turn_complete(event):
    turn = event.data['turn']
    cost = event.data['total_cost']
    print(f"Turn {turn} completed, cost: ${cost:.2f}")

# Wildcard handler (all events)
@bus.on("*")
async def log_all(event):
    logger.info(f"Event: {event.type}", extra=event.data)
```

## State Models

### ScenarioState

Complete immutable state of a scenario run.

```python
@dataclass(frozen=True)
class ScenarioState:
    scenario_id: str
    scenario_name: str
    run_id: str
    status: ScenarioStatus
    turn: int
    current_phase: Optional[PhaseType]

    world_state: WorldState
    actors: Dict[str, ActorState]

    communications: List[Communication]
    decisions: Dict[str, Decision]

    metrics: List[MetricRecord]
    costs: List[CostRecord]

    # Transformation methods
    def with_turn(self, turn: int) -> ScenarioState: ...
    def with_decision(self, actor: str, decision: Decision) -> ScenarioState: ...
    def with_cost(self, cost: CostRecord) -> ScenarioState: ...
    # ... etc
```

### WorldState

```python
@dataclass(frozen=True)
class WorldState:
    turn: int
    content: str  # Markdown description
    timestamp: datetime
    metadata: Dict[str, Any]
```

### ActorState

```python
@dataclass(frozen=True)
class ActorState:
    name: str
    short_name: str
    model: str
    current_goals: List[str]
    recent_decisions: List[Decision]
    private_information: str
    metadata: Dict[str, Any]
```

### Decision

```python
@dataclass(frozen=True)
class Decision:
    actor: str
    turn: int
    goals: List[str]
    reasoning: str
    action: str
    timestamp: datetime
    metadata: Dict[str, Any]
```

## Cost Management

V2 preserves and enhances V1's cost management:

### Requirements (Non-Negotiable)

- ✓ All LLM calls go through centralized cost tracker
- ✓ Credit limits enforced at orchestrator level
- ✓ Cost estimates shown before execution
- ✓ Real-time cost updates via events
- ✓ Cost tracking survives crashes/resumes
- ✓ Per-actor, per-phase, and total cost breakdowns

### Implementation

```python
# Credit limit enforcement in orchestrator
orchestrator = ScenarioOrchestrator(credit_limit=5.0)

# Cost tracking in state
@dataclass(frozen=True)
class CostRecord:
    timestamp: datetime
    actor: Optional[str]
    phase: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float

# Cost events
await bus.emit(
    EventType.COST_INCURRED,
    data={"actor": "regulator", "cost": 0.15, "total": 1.45}
)

# Credit limit warnings
await bus.emit(
    EventType.CREDIT_LIMIT_WARNING,
    data={"remaining": 0.55, "limit": 5.0}
)
```

## Testing Strategy

### Unit Tests

Test individual components in isolation:

```python
# Test event bus
async def test_event_emission():
    bus = EventBus(keep_history=True)
    await bus.emit("test_event", data={"foo": "bar"})

    history = bus.get_history()
    assert len(history) == 1
    assert history[0].type == "test_event"

# Test state transformations
def test_state_immutability():
    state = ScenarioState(...)
    new_state = state.with_turn(1)

    assert state.turn == 0  # Original unchanged
    assert new_state.turn == 1
```

### Integration Tests

Test full scenarios with mocked LLM:

```python
class MockLLM:
    async def generate(self, prompt: str, **kwargs) -> str:
        # Return deterministic responses
        return '{"goals": [...], "reasoning": "...", "action": "..."}'

async def test_full_scenario():
    orchestrator = ScenarioOrchestrator(max_turns=3)
    # ... register phases with MockLLM ...

    state = ScenarioState(...)
    final_state = await orchestrator.execute(state)

    assert final_state.turn == 3
    assert final_state.status == ScenarioStatus.COMPLETED
```

### Golden File Tests

Compare outputs against known-good results:

```python
def test_world_state_generation():
    result = generate_world_state(...)
    expected = load_golden_file("test-scenario-turn-1.md")
    assert normalize(result) == normalize(expected)
```

## Migration Path

### Phase 2.0: Foundation (Current)

- ✓ Pydantic schemas
- ✓ Event system
- ✓ Immutable state models
- ✓ Orchestrator
- ✓ Package structure
- ⏳ Integration tests
- ⏳ Performance baseline

### Phase 2.1: Modular Engine

- Extract phase services from V1
- Wire phases to orchestrator
- V1 becomes thin wrapper over V2
- Web API can use orchestrator

### Phase 2.2: Database & Analytics

- SQLite for persistence
- Fast queries across runs
- Still generate markdown files
- Migration tools for V1 runs

### Phase 2.3: Web Interface

- React dashboard
- Real-time monitoring
- Human-in-the-loop controls
- Scenario editor
- Analytics visualizations

## Performance Targets

Based on V1 baseline (to be measured):

- Turn execution: -20% vs baseline
- Memory usage: -30% vs baseline
- Startup time: <2s (absolute)
- Event overhead: <10% vs monolithic

## API Examples

### Python SDK

```python
from scenario_lab import Scenario, Runner

# Simple usage
scenario = Scenario.load('scenarios/ai-summit')
result = Runner().run(scenario, max_turns=10, credit_limit=5.0)
print(f"Completed in {result.turns} turns, cost ${result.total_cost:.2f}")

# Event handlers
runner = Runner()

@runner.on('turn_complete')
async def log_turn(event):
    print(f"Turn {event.data['turn']} done")

result = await runner.run_async(scenario)
```

### CLI

```bash
# V1 still works
python src/run_scenario.py scenarios/ai-summit

# V2 enhanced CLI
scenario-lab run scenarios/ai-summit --max-turns 10 --credit-limit 5.0
scenario-lab validate scenarios/ai-summit
scenario-lab estimate scenarios/ai-summit
scenario-lab compare run-001 run-002 run-003
```

### Web API

```python
# FastAPI endpoints (Phase 2.3)
POST   /api/scenarios/{id}/execute
GET    /api/scenarios/{id}/status
POST   /api/scenarios/{id}/pause
WS     /api/scenarios/{id}/stream
```

## Design Decisions

### Why Event-Driven?

- Decouples components
- Natural for async operations
- WebSocket integration is trivial
- Easy to add new observers
- Excellent for testing

### Why Immutable State?

- Prevents subtle bugs
- Enables time-travel debugging
- Trivial branching
- Safe parallelization
- Clear data flow

### Why Keep V1?

- Proven and stable
- Users depend on it
- Test suite is comprehensive
- Migration can be gradual
- Reduces risk

### Why Hybrid Files + Database?

- Files for expert review (essential)
- Database for analytics (fast queries)
- Best of both worlds
- Simpler than full database migration

## Future Enhancements

### Phase 3: Advanced Features

- Real-time collaboration
- Plugin architecture
- Custom phase services
- Advanced branching strategies
- Distributed execution

### Phase 4: Research Platform

- Published research using framework
- Community scenarios
- Scenario marketplace
- Academic partnerships

## References

- [ROADMAP_V2.md](../ROADMAP_V2.md) - Complete development roadmap
- [V2_MIGRATION.md](V2_MIGRATION.md) - Migration guide for users
- [CLAUDE.md](../CLAUDE.md) - Project overview and V1 features
- [README.md](../README.md) - Getting started guide
