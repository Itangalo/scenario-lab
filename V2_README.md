# Scenario Lab Version 2 - Getting Started

## What is Version 2?

Version 2 is a complete architectural evolution of Scenario Lab that transforms it from a working prototype into a production-ready research platform. While maintaining full backward compatibility with V1, V2 introduces:

- **Event-Driven Architecture**: Enables real-time monitoring and WebSocket integration
- **Immutable State Management**: Makes branching trivial and enables time-travel debugging
- **Modular Phase Services**: Each execution phase is independently testable
- **Web API Support**: Dashboard and human-in-the-loop controls
- **Database Analytics**: Fast queries across thousands of runs

**Current Status**: **Phase 2.0 Foundation (Alpha)**

## Quick Start

### Installation

```bash
# Clone repository
cd scenario-lab

# Install V2 package
pip install -e .

# Or with all features
pip install -e ".[all]"

# Verify installation
scenario-lab version
```

### Run Your First V2 Scenario

```bash
# V2 CLI (currently delegates to V1 engine)
scenario-lab run scenarios/test-regulation-negotiation --max-turns 3

# Compare with V1
python src/run_scenario.py scenarios/test-regulation-negotiation --max-turns 3
```

### Explore V2 Features

```bash
# Validate scenario configuration
scenario-lab validate scenarios/ai-summit

# Estimate cost (coming soon)
scenario-lab estimate scenarios/ai-summit --max-turns 10

# Show version and status
scenario-lab version
```

## What's Implemented (Phase 2.0)

### ✅ Core Architecture

- **Event System** (`scenario_lab/core/events.py`)
  - Event bus with pub/sub pattern
  - 20+ event types (turn, phase, cost, metrics)
  - Event history and error tracking
  - Async event handlers

- **Immutable State Models** (`scenario_lab/models/state.py`)
  - `ScenarioState` - Complete scenario state
  - `WorldState` - World state at a point in time
  - `ActorState` - Actor state and decisions
  - `Decision`, `Communication`, `CostRecord`, `MetricRecord`
  - All frozen dataclasses with transformation methods

- **Scenario Orchestrator** (`scenario_lab/core/orchestrator.py`)
  - Event-driven execution coordinator
  - Phase service registration
  - Credit limit enforcement
  - Pause/resume support
  - Error handling

### ✅ Package Structure

```
scenario_lab/
├── __init__.py           # Public API exports
├── cli.py                # CLI entry point
├── core/                 # Core execution engine
│   ├── events.py        # Event bus and types
│   └── orchestrator.py  # Scenario orchestrator
├── models/               # Data models
│   └── state.py         # Immutable state models
├── services/             # Phase services (coming in Phase 2.1)
├── interfaces/           # User interfaces
│   └── cli.py           # Click-based CLI
└── utils/                # Utilities
```

### ✅ Documentation

- **[V2_ARCHITECTURE.md](docs/V2_ARCHITECTURE.md)** - Complete architecture overview
- **[V2_MIGRATION.md](docs/V2_MIGRATION.md)** - Migration guide from V1
- **[ROADMAP_V2.md](ROADMAP_V2.md)** - Full development roadmap

### ✅ Packaging

- **pyproject.toml** with modern packaging
- **CLI entry point**: `scenario-lab` command
- **Development tools**: pytest, black, ruff, mypy

## What's Coming Next

### Phase 2.1: Modular Engine (Next)

- Extract phase services from V1 `run_scenario.py`
- Wire phase services to orchestrator
- Full V2 execution (no V1 delegation)
- Web API can use orchestrator

**Timeline**: 2-3 months

### Phase 2.2: Database & Analytics

- SQLite persistence
- Fast analytics queries
- Import V1 runs
- Migration tools

**Timeline**: +2 months

### Phase 2.3: Web Interface

- React dashboard
- Real-time monitoring
- Human-in-the-loop controls
- Scenario editor

**Timeline**: +4 months

See [ROADMAP_V2.md](ROADMAP_V2.md) for complete plan.

## Using V2 (Current Alpha)

### Basic CLI Usage

```bash
# Run scenario (delegates to V1 currently)
scenario-lab run scenarios/ai-summit

# With options
scenario-lab run scenarios/ai-summit --max-turns 10 --credit-limit 5.0

# Resume scenario
scenario-lab run scenarios/ai-summit --resume output/ai-summit/run-003

# Branch scenario
scenario-lab run scenarios/ai-summit \
  --branch-from output/ai-summit/run-003 \
  --branch-at-turn 5

# Validate scenario
scenario-lab validate scenarios/ai-summit
```

### Python SDK (Experimental)

```python
# Import V2 modules
from scenario_lab import (
    EventBus,
    EventType,
    ScenarioState,
    ScenarioOrchestrator,
    WorldState,
    ActorState,
)

# Create event bus
bus = EventBus(keep_history=True)

# Subscribe to events
@bus.on(EventType.TURN_COMPLETED)
async def log_turn(event):
    print(f"Turn {event.data['turn']} completed")

# Create scenario state
state = ScenarioState(
    scenario_id="test",
    scenario_name="Test Scenario",
    run_id="run-001",
)

# Transform state (immutable)
new_state = (
    state
    .with_started()
    .with_turn(1)
    .with_world_state(WorldState(turn=1, content="Initial state"))
)

print(f"Turn: {new_state.turn}, Status: {new_state.status}")
```

### Event System Example

```python
import asyncio
from scenario_lab import get_event_bus, EventType

async def main():
    bus = get_event_bus()

    # Subscribe to all cost events
    @bus.on(EventType.COST_INCURRED)
    async def track_costs(event):
        actor = event.data.get('actor', 'system')
        cost = event.data['cost']
        print(f"{actor}: ${cost:.4f}")

    # Emit some events
    await bus.emit(
        EventType.COST_INCURRED,
        data={"actor": "regulator", "cost": 0.0123}
    )

    await bus.emit(
        EventType.COST_INCURRED,
        data={"actor": "tech_company", "cost": 0.0234}
    )

asyncio.run(main())
```

## Architecture Highlights

### Event-Driven Design

All components communicate via events:

```python
# Events enable:
# - WebSocket updates (web clients subscribe)
# - Metrics tracking (metrics service subscribes)
# - Logging (logger subscribes)
# - Testing (mock components subscribe)

await bus.emit(
    EventType.TURN_STARTED,
    data={"turn": 1, "timestamp": time.time()},
    source="orchestrator"
)
```

### Immutable State

State transformations return new objects:

```python
# Original state unchanged
state = ScenarioState(...)

# Transformations create new state
new_state = state.with_turn(1)
assert state.turn == 0       # Original unchanged
assert new_state.turn == 1   # New state has change

# Can chain transformations
final = state.with_turn(1).with_started().with_world_state(...)
```

### Phase Services

Execution broken into testable phases:

```python
class CommunicationPhase:
    async def execute(self, state: ScenarioState) -> ScenarioState:
        # Process communications
        # Return new state
        return state.with_communication(...)

# Register with orchestrator
orchestrator.register_phase(PhaseType.COMMUNICATION, CommunicationPhase())
```

## Development

### Running Tests

```bash
# V1 tests (existing)
pytest tests/

# V2 tests (when added)
pytest scenario_lab/tests/

# All tests
pytest

# With coverage
pytest --cov=scenario_lab --cov-report=html
```

### Code Quality

```bash
# Format code
black scenario_lab/

# Lint
ruff scenario_lab/

# Type check
mypy scenario_lab/
```

### Adding Dependencies

```bash
# Add to pyproject.toml [project.dependencies]
pip install -e .

# Development dependencies
# Add to [project.optional-dependencies.dev]
pip install -e ".[dev]"
```

## Backward Compatibility

V2 is fully backward compatible with V1:

### ✅ V1 Scenarios Work Unchanged

```bash
# V1 scenario
scenario-lab run scenarios/old-v1-scenario
```

### ✅ V1 CLI Still Available

```bash
# V1 command still works
python src/run_scenario.py scenarios/ai-summit
```

### ✅ V1 Data Accessible

All V1 runs in `output/` remain accessible. In Phase 2.2, they can be imported into the V2 database for analytics.

## Performance

### Targets (vs V1 Baseline)

- Turn execution: **-20%** (faster)
- Memory usage: **-30%** (less)
- Startup time: **<2s** (absolute)
- Event overhead: **<10%** (negligible)

### Measuring Performance

```bash
# Benchmark scenario (coming soon)
scenario-lab benchmark scenarios/test-regulation-negotiation

# Compare with V1
python src/run_scenario.py scenarios/test-regulation-negotiation
```

Baseline measurements will be documented in `docs/performance-baseline.md`.

## Contributing to V2

### Priority Areas (Phase 2.0)

1. **Integration Tests** - Test scenarios with mocked LLM
2. **Performance Baseline** - Measure V1 performance
3. **Schema Migration** - Move Pydantic schemas to V2
4. **Documentation** - Examples and tutorials

### Next Phase (2.1)

1. **Phase Services** - Extract from V1 `run_scenario.py`
2. **Service Registration** - Wire to orchestrator
3. **Full Execution** - Remove V1 delegation
4. **Web API** - FastAPI endpoints

See [ROADMAP_V2.md](ROADMAP_V2.md) for detailed tasks.

## FAQ

### Is V2 production-ready?

Not yet. V2 is currently **alpha** (Phase 2.0). Use V1 for production work. V2 will be production-ready after Phase 2.1 (Modular Engine) is complete.

### Will V2 break my workflows?

No. V2 is backward compatible. All V1 scenarios and commands work unchanged.

### When should I switch to V2?

**Now**: Experiment and provide feedback
**Phase 2.1 complete**: Consider for new projects
**Phase 2.3 complete**: Full production use

### How do I report bugs?

GitHub Issues: https://github.com/yourusername/scenario-lab/issues

Include:
- V2 version: `scenario-lab version`
- Minimal reproduction
- Expected vs actual behavior

### Can I contribute?

Yes! See priority areas above. Start with:
1. Testing V2 with your scenarios
2. Reporting issues
3. Writing integration tests
4. Improving documentation

## Resources

### Documentation

- **[V2_ARCHITECTURE.md](docs/V2_ARCHITECTURE.md)** - Architecture deep-dive
- **[V2_MIGRATION.md](docs/V2_MIGRATION.md)** - Migration from V1
- **[ROADMAP_V2.md](ROADMAP_V2.md)** - Development roadmap
- **[README.md](README.md)** - Project overview

### Code Examples

- `scenario_lab/core/events.py` - Event system implementation
- `scenario_lab/models/state.py` - Immutable state models
- `scenario_lab/core/orchestrator.py` - Execution orchestrator
- `scenario_lab/interfaces/cli.py` - CLI implementation

### Getting Help

- GitHub Discussions: https://github.com/yourusername/scenario-lab/discussions
- GitHub Issues: https://github.com/yourusername/scenario-lab/issues

## Summary

Scenario Lab V2 is the foundation for a production-ready research platform:

- ✅ **Event-driven architecture** - Enables real-time monitoring
- ✅ **Immutable state** - Makes branching and debugging trivial
- ✅ **Modular design** - Each phase is independently testable
- ✅ **Backward compatible** - V1 continues to work
- ⏳ **Full execution** - Coming in Phase 2.1
- ⏳ **Web dashboard** - Coming in Phase 2.3

Try it today:

```bash
pip install -e .
scenario-lab run scenarios/test-regulation-negotiation
```

We're building something researchers actually want. Join us!

---

**Status**: Phase 2.0 Foundation (Alpha)
**Version**: 2.0.0-alpha.1
**Last Updated**: 2025-11-18
