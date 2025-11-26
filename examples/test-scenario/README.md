# Test Scenario - AI Governance

A minimal test scenario for Scenario Lab V3 demonstrating the basic structure and configuration.

## Scenario Overview

Two major AI powers (USA and China) navigate the challenges of AI governance, balancing competition and cooperation as advanced AI capabilities emerge.

## Files Structure

```
test-scenario/
├── scenario.yaml           # Scenario configuration
├── metrics.yaml            # World and actor metrics
├── events.yaml             # Exogenous events (empty for this test)
├── background/
│   ├── context.md         # Overall scenario context
│   └── actors/
│       ├── USA.md         # USA background and goals
│       └── China.md       # China background and goals
└── README.md
```

## Configuration Details

### Actors
- **USA**: Leading AI superpower focused on democratic governance
- **China**: Emerging AI superpower with coordinated state planning

### Time Scale
- 6 months per turn
- 5 turns maximum

### Metrics

**World Metrics** (visible to all):
- `global_ai_capability`: 0.5
- `international_cooperation`: 0.6
- `catastrophic_risk_level`: 0.15

**Actor Metrics** (private/public split):
- Private: Research capacity, classified programs, intelligence assessments
- Public: GDP, AI investment, public stance

### Action Points
- Initial per turn: 3
- New message: 1 AP
- Reply: 0 AP
- Forward: 1 AP

## Running the Test Scenario

```bash
# From project root
python example_run.py examples/test-scenario 3

# Or using the Simulation class directly
python -c "from scenario_lab import Simulation; sim = Simulation('examples/test-scenario'); sim.run(3)"
```

## Expected Output

The simulation will:
1. Load all configuration files
2. Initialize world state with background context
3. Run 3 turns with phase logging
4. Save output to `examples/test-scenario/runs/<run-id>/`

## Technical Requirements

- Python 3.11+
- pydantic >=2.0.0
- pyyaml >=6.0
- httpx >=0.24.0 (for future LLM integration)
