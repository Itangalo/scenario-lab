# Scenario Lab V3 - Complete Project Structure

## Directory Tree

```
Scenario Lab 3/
├── scenario_lab/                # Core package
│   ├── __init__.py             # Package exports
│   ├── engine.py               # Simulation and SimulationEngine classes
│   ├── models.py               # Pydantic data models
│   ├── llm_provider.py         # LLM abstraction layer
│   ├── methods_base.py         # Base class for scenario methods
│   └── utils.py                # Utilities (loading, logging, filtering)
│
├── examples/                    # Example scenarios
│   ├── README.md               # Examples documentation
│   └── test-scenario/          # Minimal test scenario
│       ├── README.md           # Test scenario docs
│       ├── scenario.yaml       # Scenario configuration
│       ├── metrics.yaml        # World and actor metrics
│       ├── events.yaml         # Exogenous events (empty)
│       └── background/
│           ├── context.md      # Overall scenario context
│           └── actors/
│               ├── USA.md      # USA background
│               └── China.md    # China background
│
├── requirements.txt             # Python dependencies
├── example_run.py              # CLI runner script
├── test_scenario.py            # Verification test script
├── .gitignore                  # Git ignore rules
├── README.md                   # Main documentation
└── STRUCTURE.md                # This file
```

## Core Package (`scenario_lab/`)

### `models.py` - Data Models
- **Actor**: Individual participant with goals, AP, background
- **Metrics**: Structured world + actor metrics (private/public)
- **WorldState**: Four-layer state (narrative, metrics, facts, relationships)
- **ActorView**: Filtered view implementing information asymmetry
- **Message**: Communication with intent and visibility
- **Configuration models**: ScenarioConfig, MetricsConfig, EventsConfig
- **Action models**: FunctionCall, ActorAction, TurnActions

### `engine.py` - Simulation Logic
- **Simulation**: Main class with simple interface
  - `__init__(scenario_path)`: Load YAML configs
  - `run(num_turns)`: Execute simulation loop
  - `run_turn()`: Execute single turn with 5 phases
- **SimulationEngine**: Advanced engine with full implementation

### `llm_provider.py` - LLM Abstraction
- **LLMProvider**: Abstract base class
- **OpenRouterProvider**: Claude, GPT, Llama (stub)
- **LocalProvider**: Ollama, llama.cpp (stub)
- **MockProvider**: Testing provider
- **create_provider()**: Factory function

### `methods_base.py` - Action Framework
- **ScenarioMethods**: Base class for scenario logic
  - Action registration and execution
  - Validation (max 2 initiatives per turn)
  - Helper methods for metrics, facts, relationships
- **EmptyScenarioMethods**: Testing implementation

### `utils.py` - Utilities
- **Logging**: setup_logging() with file + console
- **Loading**: YAML, JSON, Markdown loaders
- **Filtering**: get_visible_metrics() for information asymmetry
- **Persistence**: Turn and run directory management
- **Prompts**: Template loading (future)

## Test Scenario (`examples/test-scenario/`)

### Configuration Files

**scenario.yaml**
```yaml
name: "AI Governance Test Scenario"
time_scale: "6 months per turn"
max_turns: 5
actors: [USA, China]
llm: {provider: "mock", ...}
action_point_rules: {...}
```

**metrics.yaml**
```yaml
world:
  global_ai_capability: 0.5
  international_cooperation: 0.6
  catastrophic_risk_level: 0.15

actors:
  USA:
    private: {ai_research_capacity: 85, ...}
    public: {gdp_trillion: 25.5, ...}
  China:
    private: {ai_research_capacity: 80, ...}
    public: {gdp_trillion: 17.9, ...}
```

**events.yaml**
```yaml
events: []
```

### Background Files

**background/context.md**: Single paragraph scenario setup

**background/actors/*.md**: Actor-specific backgrounds with:
- Overview
- Strategic goals
- Current capabilities

## Running the Framework

### Quick Test
```bash
# Run verification test
python test_scenario.py

# Run example scenario (3 turns)
python example_run.py examples/test-scenario 3
```

### Programmatic Usage
```python
from scenario_lab import Simulation

sim = Simulation("examples/test-scenario")
sim.run(5)
```

### Output Structure
```
examples/test-scenario/runs/
└── run-YYYYMMDD-HHMMSS/
    └── simulation.log
```

## Technical Requirements

- **Python**: 3.11+
- **pydantic**: >=2.0.0 (data validation)
- **pyyaml**: >=6.0 (YAML parsing)
- **httpx**: >=0.24.0 (HTTP client for LLMs)
- **Type hints**: Required throughout

## Architecture Features

### Hybrid Model
- LLMs handle narrative, diplomacy, intentions
- Python handles metrics, validation, deterministic logic

### Information Asymmetry
- World metrics: Visible to all
- Actor private metrics: Only visible to owner
- Actor public metrics: Visible to all
- Messages: Private, public, or leaked

### Phase Structure
1. **Pre-Turn**: Events, triggers, AP reset, view generation
2. **Phase 1**: Initiative & Communication
3. **Phase 2**: Response & Final Negotiation
4. **Phase 3**: Execution & Goal Adjustment
5. **Post-Turn**: Validation, synthesis, persistence

### Data Persistence
- Narrative state with rolling window
- Fact ledger (never summarized away)
- Relationship state (structured)
- Metrics snapshots
- Outcome flags for analysis

## Status

✅ **Complete**:
- Core data models with Pydantic
- Configuration loading from YAML
- Simulation loop with phase logging
- Information asymmetry in metrics
- Test scenario with full structure
- Logging infrastructure
- CLI runner

🚧 **TODO**:
- LLM API integration (OpenRouter, local)
- Prompt templates
- Director for narrative synthesis
- Actor view generation with filtering
- Turn state persistence
- Action execution via methods.py
- Communication phase implementation
- Relationship state updates
- Exogenous event handling

## Version

3.0.0 - Initial implementation (November 2025)
