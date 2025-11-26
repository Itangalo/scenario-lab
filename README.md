# Scenario Lab V3

AI-powered multi-agent scenario simulation framework with hybrid LLM + deterministic logic architecture.

## Features

- **Multi-agent simulation** with information asymmetry between actors
- **Hybrid architecture**: LLMs handle narrative and decision-making, Python handles deterministic game logic
- **Three-phase turn cycle**: Communication → Negotiation → Execution
- **Director agent** for narrative synthesis after each turn
- **Flexible LLM providers**: OpenRouter, local endpoints, or mock for testing
- **Event system**: Scheduled and conditional events that affect the world state
- **Extensible actions**: Define scenario-specific actions with custom game mechanics

## Project Structure

```
scenario_lab/
├── __init__.py          # Package initialization
├── engine.py            # Main simulation engine
├── models.py            # Pydantic data models
├── llm_provider.py      # LLM abstraction (OpenRouter, Local, Mock)
├── methods_base.py      # Base class for scenario-specific actions
├── director.py          # Director agent for narrative synthesis
├── cli.py               # Command-line interface
└── utils.py             # File loading, logging helpers

prompts/
├── loader.py            # Jinja2 template loader
├── actor_phase1.txt     # Phase 1: Initiative & Communication
├── actor_phase2.txt     # Phase 2: Response & Negotiation
├── actor_phase3.txt     # Phase 3: Execution & Goals
└── director.txt         # Director narrative synthesis

examples/
├── test-scenario/       # Minimal test scenario (USA vs China)
└── us-china-ai/         # Full scenario: US-China AI Race (3 actors)
```

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Command Line Interface

```bash
# Run a scenario with mock LLM (for testing)
python -m scenario_lab.cli run examples/us-china-ai --turns 5 --dry-run

# Run with real LLM provider
python -m scenario_lab.cli run examples/us-china-ai --turns 10

# Analyze recent runs
python -m scenario_lab.cli analyze examples/us-china-ai --runs 5

# Show help
python -m scenario_lab.cli --help
```

### Python API

```python
import asyncio
from scenario_lab import Simulation

async def main():
    # Initialize simulation
    sim = Simulation("examples/us-china-ai")
    
    # Run for specified number of turns
    await sim.run(num_turns=10)
    
    # Results saved to: examples/us-china-ai/runs/<run-id>/

asyncio.run(main())
```

### Verification Test

```bash
python test_scenario.py
```

## Example Scenarios

### test-scenario (Minimal)

A minimal two-actor scenario for testing:

- **Actors**: USA, China
- **Time scale**: 6 months per turn
- **Actions**: invest_research, sign_agreement, increase_risk_assessment, declare_war

### us-china-ai (Full)

A complete three-actor geopolitical AI race scenario:

- **Actors**: USA, China, EU
- **Time scale**: 1 year per turn
- **Metrics**: AI capability, safety research, military capacity, public trust, catastrophe risk
- **Events**: Global AI Safety Summit (turn 2), US Election (turn 4), AI Breakthrough (turn 6)
- **Conditional triggers**: Military arms race, loss of public trust, AI dominance
- **Actions**: invest_ai_research, invest_ai_safety, impose_sanctions, form_alliance, propose_treaty, military_posturing, public_announcement

## Creating a New Scenario

A scenario consists of a directory with the following files:

```
my-scenario/
├── scenario.yaml        # Core configuration
├── metrics.yaml         # Initial metrics (world + actors)
├── events.yaml          # Scheduled and conditional events
├── methods.py           # Scenario-specific actions
└── background/
    ├── context.md       # World background
    └── actors/
        ├── Actor1.md    # Actor description and goals
        └── Actor2.md
```

### scenario.yaml

```yaml
name: "My Scenario"
time_scale: "1 year per turn"
max_turns: 10

actors:
  - Actor1
  - Actor2

llm:
  provider: "openrouter"
  model: "anthropic/claude-3.5-sonnet"
  api_key_env: "OPENROUTER_API_KEY"
  temperature: 0.7
  max_tokens: 2000

action_point_rules:
  initial_per_turn: 3
  message_to_new_recipient: 1
  message_reply: 0
```

### metrics.yaml

```yaml
world:
  global_tension: 0.3
  cooperation_index: 0.5

actors:
  Actor1:
    public:
      budget: 1000
      influence: 80
    private:
      secret_capability: 50
  Actor2:
    public:
      budget: 800
      influence: 60
    private:
      secret_capability: 40
```

### methods.py

```python
from typing import List
from scenario_lab.methods_base import ScenarioMethods
from scenario_lab.models import WorldState

class MyScenarioMethods(ScenarioMethods):
    def _register_actions(self) -> None:
        self.register_action("my_action", self.my_action)

    def my_action(self, actor: str, args: dict, state: WorldState) -> List[str]:
        amount = args.get("amount", 10)
        state.set_metric(actor, "budget", state.get_metric(actor, "budget") - amount)
        return [f"{actor} performed my_action with amount {amount}."]
```

## Turn Cycle

Each turn follows this structure:

1. **Pre-Turn**
   - Process scheduled events
   - Check conditional triggers
   - Reset action points
   - Generate actor views (with information asymmetry)

2. **Phase 1: Initiative & Communication**
   - Actors send messages to other actors
   - Cost: 1 AP for new recipient, 0 AP for replies

3. **Phase 2: Response & Negotiation**
   - Actors respond to received messages
   - Final negotiation before action phase

4. **Phase 3: Execution & Goal Adjustment**
   - Actors choose and execute actions
   - Update goals based on outcomes

5. **Post-Turn**
   - Validate all actions
   - Execute actions and update metrics
   - Director synthesizes narrative
   - Save turn state to disk

## Output Structure

Each run creates a directory with:

```
runs/run-YYYYMMDD-HHMMSS/
├── simulation.log       # Detailed execution log
├── summary.json         # Final metrics and outcome flags
├── turn-01/
│   ├── world_state.md   # Narrative state
│   ├── metrics.json     # Metrics snapshot
│   ├── actions.json     # Actions taken
│   ├── comms_phase_1.json
│   ├── comms_phase_2.json
│   ├── relationships.json
│   ├── fact_ledger.json
│   └── views/
│       ├── Actor1.json  # What Actor1 sees
│       └── Actor2.json
└── turn-02/
    └── ...
```

## LLM Providers

### OpenRouter (Production)

```yaml
llm:
  provider: "openrouter"
  model: "anthropic/claude-3.5-sonnet"
  api_key_env: "OPENROUTER_API_KEY"
```

### Local (Ollama, llama.cpp)

```yaml
llm:
  provider: "local"
  model: "llama3"
  base_url: "http://localhost:11434"
```

### Mock (Testing)

```bash
python -m scenario_lab.cli run examples/test-scenario --dry-run
```

## Dependencies

- **Python**: 3.11+
- **pydantic** (>=2.0.0): Data validation
- **pyyaml** (>=6.0): YAML loading
- **httpx** (>=0.24.0): Async HTTP client
- **jinja2** (>=3.0.0): Prompt templates

## Architecture Principles

- **Hybrid execution**: LLMs for narrative reasoning, Python for deterministic logic
- **Information asymmetry**: Actors only see public metrics of others
- **Deterministic validation**: Python enforces game rules
- **Structured outcomes**: Outcome flags enable quantitative analysis
- **Memory efficiency**: Epoch summaries prevent context overflow

## Version

3.0.0 - Full implementation with CLI, Director, and complete US-China AI scenario
