# Scenario Lab V3 - Example Scenarios

This directory contains example scenarios demonstrating the capabilities of Scenario Lab V3.

## Available Scenarios

### test-scenario - AI Governance

A minimal test scenario demonstrating basic framework functionality.

**Actors**: USA, China
**Time Scale**: 6 months per turn
**Max Turns**: 5

**Purpose**:
- Verify framework installation and configuration
- Test basic simulation loop
- Demonstrate scenario structure

**Run**:
```bash
python example_run.py examples/test-scenario 3
```

See [test-scenario/README.md](test-scenario/README.md) for details.

## Creating New Scenarios

Each scenario requires:

### Required Files

1. **scenario.yaml** - Main configuration
   - Scenario name and metadata
   - Actor list
   - LLM configuration
   - Action point rules
   - World-altering triggers

2. **metrics.yaml** - Metrics structure
   - World metrics (visible to all)
   - Actor metrics with private/public split

3. **events.yaml** - Exogenous events
   - List of events with turn numbers
   - Event effects on metrics

4. **background/context.md** - Overall scenario context
   - Background narrative
   - Current situation

5. **background/actors/{actor}.md** - Per-actor backgrounds
   - Actor overview
   - Strategic goals
   - Current capabilities

### Optional Files

6. **methods.py** - Scenario-specific action logic
   - Custom action functions
   - Validation rules
   - Metric calculations

### Directory Structure

```
scenario-name/
├── scenario.yaml
├── metrics.yaml
├── events.yaml
├── background/
│   ├── context.md
│   └── actors/
│       ├── Actor1.md
│       └── Actor2.md
├── methods.py (optional)
└── runs/ (generated during simulation)
    └── run-YYYYMMDD-HHMMSS/
        ├── simulation.log
        └── turn-XX/ (future: turn state)
```

## Technical Requirements

- Python 3.11+
- pydantic >=2.0.0
- pyyaml >=6.0
- httpx >=0.24.0

Type hints required throughout all scenario files.

## Testing Scenarios

Use the test script to verify your scenario:

```bash
python test_scenario.py
```

This validates:
- YAML files load correctly
- Metrics structure is valid
- Background files exist and are readable
- Simulation runs without errors
