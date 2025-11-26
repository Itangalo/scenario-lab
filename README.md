# Scenario Lab V3

AI-powered scenario simulation framework with hybrid LLM + deterministic logic architecture.

## Project Structure

```
scenario_lab/
├── __init__.py          # Package initialization
├── engine.py            # Main simulation loop
├── models.py            # Pydantic data classes
├── llm_provider.py      # LLM abstraction (OpenRouter, Local, Mock)
├── methods_base.py      # Base class for scenario methods
└── utils.py             # File loading, logging helpers

requirements.txt         # Python dependencies
```

## Core Components

### Engine (`engine.py`)

Orchestrates the complete simulation with:

- **Pre-Turn**: Event check, trigger check, AP reset, view generation
- **Phase 1**: Initiative & Communication
- **Phase 2**: Response & Final Negotiation
- **Phase 3**: Execution & Goal Adjustment
- **Post-Turn**: Validation, updates, narrative synthesis

### Models (`models.py`)

Pydantic data structures including:

- `WorldState`: Four-layer state (narrative, metrics, fact ledger, relationships)
- `ActorView`: Filtered view with information asymmetry
- Configuration models for scenarios, metrics, events
- Communication and action models

### LLM Provider (`llm_provider.py`)

Abstract provider interface with implementations for:

- **OpenRouterProvider**: Claude, GPT, Llama (stub)
- **LocalProvider**: Ollama, llama.cpp (stub)
- **MockProvider**: Testing with deterministic responses

### Scenario Methods (`methods_base.py`)

Base class for scenario-specific action logic:

- Action registration and execution
- Validation (max 2 initiatives per turn)
- Utility methods for metrics, facts, relationships

### Utilities (`utils.py`)

Helper functions for:

- File loading (YAML, JSON, Markdown)
- Configuration loading
- Logging setup
- Turn and run directory management
- Metrics filtering (information asymmetry)

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

Run the test scenario to verify installation:

```bash
# Run test scenario (3 turns)
python example_run.py examples/test-scenario 3

# Or run the verification test
python test_scenario.py
```

## Usage

### Using the Simulation Class

```python
from scenario_lab import Simulation

# Initialize simulation
sim = Simulation("examples/test-scenario")

# Run for specified number of turns
sim.run(5)

# Access results
print(f"Run ID: {sim.run_id}")
print(f"Output: {sim.scenario_path}/runs/{sim.run_id}/")
```

### Command Line

```bash
python example_run.py <scenario_path> [num_turns]

# Example
python example_run.py examples/test-scenario 5
```

## Test Scenario

The `examples/test-scenario` directory contains a minimal working scenario:

- **Scenario**: AI Governance crisis between USA and China
- **Actors**: USA, China
- **Time Scale**: 6 months per turn
- **Metrics**: Global AI capability, cooperation levels, actor capabilities
- **Events**: None (empty list for testing)

See [examples/README.md](examples/README.md) for details.

## Dependencies

- **Python**: 3.11+
- **pydantic** (>=2.0.0): Data validation and models
- **pyyaml** (>=6.0): YAML configuration loading
- **httpx** (>=0.24.0): HTTP client for LLM APIs

## Next Steps

1. Implement LLM API calls in `llm_provider.py`
2. Create prompt templates in `prompts/` directory
3. Implement Director for narrative synthesis
4. Build scenario-specific `methods.py` for action logic
5. Add turn state persistence
6. Implement actor views and information filtering

## Architecture Principles

- **Hybrid**: LLMs for narrative, Python for logic
- **Information asymmetry**: Actors have limited visibility
- **Deterministic validation**: Python enforces rules
- **Structured outcomes**: Flags enable quantitative analysis
- **Memory efficiency**: Selective narrative with persistent facts

## Version

3.0.0 - Initial structure
