# Scenario Lab V2 Migration Guide

## Overview

This guide explains the architectural transformation from V1 (monolithic) to V2 (modular) and how to use the new V2 CLI.

## Quick Comparison

### V1 Architecture (1354 lines in run_scenario.py)

```
run_scenario.py
├─ Parse YAML (inline)
├─ Initialize components (inline)
├─ Main loop (inline):
│   ├─ Private communications (inline)
│   ├─ Coalitions (inline)
│   ├─ Public actions (inline)
│   ├─ World state update (inline)
│   ├─ QA validation (inline)
│   └─ Save files (inline)
└─ CLI only, no API
```

**Problems:**
- Cannot test phases independently
- Cannot reuse in web API
- Hard to extend with new phases
- Difficult to maintain
- No async support

### V2 Architecture (219 lines in run_scenario_v2.py)

```
run_scenario_v2.py (thin CLI wrapper)
    ↓
SyncRunner / AsyncExecutor
    ↓
ScenarioOrchestrator (event-driven)
    ↓
Phase Services (modular, testable):
    ├─ CommunicationPhase
    ├─ DecisionPhase
    ├─ WorldUpdatePhase
    ├─ PersistencePhase
    └─ DatabasePersistencePhase
```

**Benefits:**
- Each phase is independently testable
- Same engine for CLI, web API, notebooks
- Easy to add new phases
- Clean separation of concerns
- Full async support for WebSockets
- Event-driven for observability

## V2 CLI Usage

### Basic Usage

```bash
# Run a scenario (same as V1)
python run_scenario_v2.py scenarios/ai-2027

# With limits
python run_scenario_v2.py scenarios/ai-2027 --max-turns 5 --credit-limit 2.0

# Resume a paused run
python run_scenario_v2.py scenarios/ai-2027 --resume output/ai-2027/run-001

# Branch from a previous run
python run_scenario_v2.py scenarios/ai-2027 --branch-from output/ai-2027/run-001 --branch-at-turn 3
```

### New V2 Features

```bash
# Use JSON mode for robust agent output parsing
python run_scenario_v2.py scenarios/ai-2027 --json-mode

# Set log level for debugging
python run_scenario_v2.py scenarios/ai-2027 --log-level DEBUG
```

## V2 Advantages Over V1

### 1. Modular Phase Services

Each phase is a separate service with:
- Clear input/output contracts
- Independent unit tests
- Mocked dependencies
- Easy to modify/extend

**Example - Adding a Custom Phase:**

```python
# Create custom phase
class CustomAnalysisPhase:
    async def execute(self, state: ScenarioState) -> ScenarioState:
        # Your custom logic here
        analysis_result = analyze_decisions(state.decisions)
        return state.with_metadata(analysis=analysis_result)

# Register with orchestrator
orchestrator.register_phase(PhaseType.CUSTOM_ANALYSIS, CustomAnalysisPhase())
```

### 2. Structured Logging

All logs include contextual metadata:

```
[INFO] Starting turn 1 [scenario=ai-2027, run_id=run-001]
[INFO] LLM call: openai/gpt-4o-mini (1500 in, 500 out) = $0.0003 [turn=1, actor=US, phase=decision]
[INFO] Turn 1 completed [total_cost=0.0015, decisions=3]
```

### 3. JSON Agent Outputs

Actors can output structured JSON instead of markdown:

```json
{
  "goals": {
    "long_term": "Establish AI safety standards",
    "short_term": "Draft regulation proposal"
  },
  "reasoning": "Current landscape requires...",
  "action": "I will introduce legislation..."
}
```

**Benefits:**
- Eliminates markdown parsing errors
- Structured data for analysis
- Still generates human-readable markdown
- Automatic fallback to V1 parser

### 4. Async Execution for Web APIs

```python
from scenario_lab.runners import AsyncExecutor

executor = AsyncExecutor(
    scenario_path="scenarios/ai-2027",
    max_turns=10,
)

await executor.setup()

# Stream events in real-time (for WebSockets)
async for event in executor.execute_with_streaming():
    print(f"{event['type']}: {event['data']}")
    # Send to WebSocket clients

await executor.cleanup()
```

### 5. Comprehensive Testing

V2 includes:
- **Unit tests** for each phase service (with mocked dependencies)
- **Integration tests** with deterministic LLM responses
- **Golden file tests** for regression testing
- **Async executor tests** for web API

```bash
# Run all tests
pytest tests/

# Run specific test suites
pytest tests/test_v2_phases.py      # Phase service unit tests
pytest tests/test_v2_integration.py  # End-to-end integration
pytest tests/test_async_executor.py  # Async execution
```

## Migration Path

### For V1 Users

**No migration required!** V1 still works:

```bash
# V1 still works
python src/run_scenario.py scenarios/ai-2027

# V2 works alongside V1
python run_scenario_v2.py scenarios/ai-2027
```

### For New Development

**Use V2 for new scenarios:**

```bash
# Create scenario with wizard
python src/create_scenario.py

# Run with V2
python run_scenario_v2.py scenarios/your-scenario
```

### For API Integration

**Use AsyncExecutor for web apps:**

```python
# FastAPI example
from fastapi import FastAPI, WebSocket
from scenario_lab.runners import AsyncExecutor

app = FastAPI()

@app.websocket("/ws/scenario/{scenario_id}")
async def scenario_websocket(websocket: WebSocket, scenario_id: str):
    await websocket.accept()

    executor = AsyncExecutor(
        scenario_path=f"scenarios/{scenario_id}",
        max_turns=10,
    )

    await executor.setup()

    # Stream events to WebSocket
    async for event in executor.execute_with_streaming():
        await websocket.send_json(event)

    await executor.cleanup()
```

## Performance Comparison

| Feature | V1 | V2 |
|---------|----|----|
| Lines of code (CLI) | 1354 | 219 |
| Testability | Hard | Easy |
| Async support | No | Yes |
| Web API ready | No | Yes |
| Structured logging | Basic | Full |
| Event streaming | No | Yes |
| Modular phases | No | Yes |
| Cost tracking | Yes | Enhanced |

## Architectural Layers

### Layer 1: CLI Interface
- `run_scenario_v2.py`: Thin argument parser and display logic
- Delegates to Layer 2

### Layer 2: Execution Runners
- `SyncRunner`: Synchronous execution for CLI
- `AsyncExecutor`: Async execution for web APIs
- Both use Layer 3

### Layer 3: Orchestration
- `ScenarioOrchestrator`: Event-driven phase execution
- Coordinates Layer 4 services

### Layer 4: Phase Services
- `CommunicationPhase`: Handles actor communications
- `DecisionPhase`: Collects actor decisions
- `WorldUpdatePhase`: Synthesizes world state
- `PersistencePhase`: Writes markdown files
- `DatabasePersistencePhase`: Saves to SQLite (future)

### Layer 5: V1 Components (Reused)
- `Actor`: LLM-powered actor decisions
- `WorldStateUpdater`: LLM-powered world synthesis
- `ContextManager`: Actor-specific context
- `CommunicationManager`: Private communications
- `MetricsTracker`: Metrics extraction
- `QAValidator`: Quality assurance validation

## V2 Development Principles

1. **Immutable State**: `ScenarioState` is immutable, methods return new states
2. **Event-Driven**: Orchestrator emits events for observability
3. **Async-First**: All phase services are async
4. **Testable**: Mocked dependencies, unit tests per phase
5. **Modular**: Each phase is independent
6. **Backward Compatible**: V1 scenarios work unchanged

## Future Enhancements

V2 architecture enables:

- **Phase 2.2**: Database analytics and batch analysis
- **Phase 2.3**: Real-time web dashboard
- **Phase 3**: Human-in-the-loop web interface
- **Phase 4**: Advanced batch processing
- **Phase 5**: Custom phase plugins

## Getting Help

- **Documentation**: See `README.md` and `CLAUDE.md`
- **Examples**: Check `scenarios/` directory
- **Issues**: Report at GitHub issues
- **Architecture**: See `ROADMAP_V2.md`

## Summary

V2 transforms Scenario Lab from a monolithic script to a modular, testable, web-ready platform while maintaining full backward compatibility with V1.

**Key Takeaway**: The V2 CLI is just 219 lines because all complexity is properly factored into reusable, testable components.
