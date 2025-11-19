# Scenario Lab V2 - Migration Guide

## Overview

This guide helps you transition from Scenario Lab V1 to V2. The good news: **migration is optional and gradual**. V1 continues to work unchanged while you adopt V2 features at your own pace.

## Key Principles

1. **V1 Still Works**: All existing scenarios and workflows continue unchanged
2. **Gradual Adoption**: Use V2 features when ready, no rush
3. **Backward Compatible**: V2 can run V1 scenarios
4. **No Data Loss**: All V1 runs remain accessible

## Migration Scenarios

Choose the path that fits your situation:

### Scenario A: Gradual Adoption (Recommended)

**Best for**: Active projects, risk-averse users

**Approach**:
- Continue using V1 for production work
- Experiment with V2 for new scenarios
- Migrate when comfortable

**Timeline**: No deadline

**Steps**:
1. Install V2: `pip install -e .`
2. Try V2 CLI: `scenario-lab run scenarios/test-scenario`
3. Compare with V1: `python src/run_scenario.py scenarios/test-scenario`
4. When ready, switch to V2 for new work

### Scenario B: Active Migration

**Best for**: Users wanting V2 benefits now

**Approach**:
- New runs use V2
- Historic data imported on-demand
- V1 available for reference

**Timeline**: 1-2 weeks

**Steps**:
1. Install V2: `pip install -e .`
2. Test V2 with existing scenarios
3. Import historic runs (when Phase 2.2 ready)
4. Switch all new work to V2

### Scenario C: Complete Migration

**Best for**: Long-term V2 commitment

**Approach**:
- One-time import of all V1 data
- Full V2 adoption
- V1 retired (but available for reproduction)

**Timeline**: 1-2 days for import + verification

**Steps**:
1. Install V2: `pip install -e .`
2. Bulk import: `scenario-lab import --all output/` (Phase 2.2)
3. Verify data integrity
4. Use V2 for all work

## Installation

### V1 (Current)

```bash
# No installation needed, run from source
cd scenario-lab
python src/run_scenario.py scenarios/my-scenario
```

### V2 (New)

```bash
# Install as package
cd scenario-lab
pip install -e .

# Or with all features
pip install -e ".[all]"

# Now use anywhere
scenario-lab run scenarios/my-scenario
```

### Side-by-Side

Both V1 and V2 can coexist:

```bash
# V1
python src/run_scenario.py scenarios/ai-summit

# V2
scenario-lab run scenarios/ai-summit
```

## CLI Commands

### V1 → V2 Mapping

| V1 Command | V2 Command | Notes |
|------------|------------|-------|
| `python src/run_scenario.py <path>` | `scenario-lab run <path>` | Same behavior |
| `--max-turns N` | `--max-turns N` | Unchanged |
| `--credit-limit X` | `--credit-limit X` | Unchanged |
| `--resume <path>` | `--resume <path>` | Unchanged |
| `--branch-from <path>` | `--branch-from <path>` | Unchanged |
| N/A | `scenario-lab validate <path>` | New: Schema validation |
| N/A | `scenario-lab estimate <path>` | New: Cost estimation |
| N/A | `scenario-lab compare <runs>` | New: Run comparison |
| N/A | `scenario-lab benchmark <path>` | New: Performance testing |

### New V2 Commands

**Validate Scenario**:
```bash
scenario-lab validate scenarios/ai-summit
```
Checks:
- YAML syntax
- Pydantic schema validation
- Actor definitions
- Metrics configuration

**Estimate Cost**:
```bash
scenario-lab estimate scenarios/ai-summit --max-turns 10
```
Provides:
- Estimated total cost
- Per-actor breakdown
- Per-turn estimate

**Compare Runs**:
```bash
scenario-lab compare run-001 run-002 run-003
```
Shows:
- World state differences
- Actor decision comparison
- Metrics side-by-side
- Cost analysis

**Benchmark**:
```bash
scenario-lab benchmark scenarios/ai-summit
```
Measures:
- Turn execution time
- Memory usage
- Cost per turn
- Startup time

## Scenario Configuration

### V1 Format (Still Works)

```yaml
# scenarios/my-scenario/scenario.yaml
name: "AI Summit"
description: "International AI policy negotiation"

turns: 10
turn_duration: "1 week"

world_state_model: "gpt-4o-mini"
system_prompt: |
  You are simulating world state evolution...

actors:
  - eu_commission
  - us_government
  - tech_consortium
```

### V2 Format (Enhanced)

```yaml
# scenarios/my-scenario/scenario.yaml
schema_version: "2.0"  # Enables V2 features

name: "AI Summit"
description: "International AI policy negotiation"

scenario_length:
  type: fixed
  turns: 10

turn_duration: "1 week"

world_state_model: "gpt-4o-mini"
system_prompt: |
  You are simulating world state evolution...

actors:
  - eu_commission
  - us_government
  - tech_consortium

# V2-specific features
validation:
  enabled: true
  model: "gpt-4o-mini"

exogenous_events:
  enabled: true
```

### Automatic Conversion

V2 automatically converts V1 scenarios:

```python
from scenario_lab.utils.schemas import load_scenario_config

# Works with both V1 and V2 formats
config = load_scenario_config('scenarios/my-scenario/scenario.yaml')
```

To upgrade manually:
```bash
scenario-lab upgrade scenarios/my-scenario  # Coming in Phase 2.0
```

## Actor Definitions

### V1 Format (Still Works)

```yaml
# actors/regulator.yaml
name: "National AI Safety Regulator"
short_name: "regulator"
llm_model: "gpt-4o-mini"

role: "Regulatory agency head"
goals:
  - Ensure robust safety standards
  - Maintain public trust

constraints:
  - Must consider industry feedback

expertise:
  ai_safety: expert
  policy: expert

decision_style: "Cautious but pragmatic"
```

### V2 Format (Enhanced)

```yaml
# actors/regulator.yaml
schema_version: "2.0"

name: "National AI Safety Regulator"
short_name: "regulator"
model: "gpt-4o-mini"  # 'model' preferred in V2

role: "Regulatory agency head"
long_term_goals:  # More explicit naming
  - Ensure robust safety standards
  - Maintain public trust

constraints:
  - Must consider industry feedback

expertise:
  ai_safety: expert
  policy: expert

decision_making_style: "Cautious but pragmatic"

# V2-specific fields
control: ai  # 'ai' or 'human'
private_information: |
  Internal analysis suggests...
personality_traits:
  - Methodical
  - Risk-averse
```

## Python SDK

### V1 (Import Directly)

```python
# Add src to path
import sys
sys.path.insert(0, 'src')

from run_scenario import run_scenario

# Run scenario
run_scenario('scenarios/ai-summit', max_turns=10)
```

### V2 (Clean Import)

```python
from scenario_lab import Scenario, Runner

# Simple usage
scenario = Scenario.load('scenarios/ai-summit')
result = Runner().run(scenario, max_turns=10, credit_limit=5.0)

print(f"Cost: ${result.total_cost:.2f}")
print(f"Turns: {result.turns}")

# Advanced usage with events
runner = Runner()

@runner.on('turn_complete')
async def log_turn(event):
    print(f"Turn {event.data['turn']} cost: ${event.data['cost']:.2f}")

result = await runner.run_async(scenario)
```

## Event System (New in V2)

Subscribe to execution events:

```python
from scenario_lab import get_event_bus, EventType

bus = get_event_bus()

# Log all turns
@bus.on(EventType.TURN_COMPLETED)
async def log_turn(event):
    print(f"Turn {event.data['turn']} completed")

# Watch costs
@bus.on(EventType.COST_INCURRED)
async def track_cost(event):
    actor = event.data['actor']
    cost = event.data['cost']
    print(f"{actor}: ${cost:.4f}")

# Credit warnings
@bus.on(EventType.CREDIT_LIMIT_WARNING)
async def warn_cost(event):
    remaining = event.data['remaining']
    print(f"Warning: ${remaining:.2f} remaining")
```

## Data Import (Phase 2.2)

### Import Single Run

```bash
scenario-lab import output/ai-summit/run-003
```

### Import All Runs

```bash
scenario-lab import --all output/
```

### Import Specific Scenario

```bash
scenario-lab import --scenario ai-summit output/
```

### Verify Import

```bash
scenario-lab verify-import output/
```

Shows:
- Number of runs imported
- Any failures
- Data integrity checks

## Database Queries (Phase 2.2)

V2 stores data in SQLite for fast analytics:

```python
from scenario_lab.db import RunDatabase

db = RunDatabase('scenario-lab.db')

# Find runs
runs = db.runs.filter(scenario='ai-summit', cost__lt=1.0)

# Aggregate metrics
avg_cooperation = db.metrics.aggregate('cooperation_level').mean()

# Query actor decisions
decisions = db.decisions.for_actor('EU').across_runs()

# Export to DataFrame
import pandas as pd
df = db.query_metrics(scenario='ai-summit')
df.to_csv('metrics.csv')
```

## Web Dashboard (Phase 2.3)

Start web server:

```bash
scenario-lab serve
```

Access at: http://localhost:8000

Features:
- Monitor scenarios in real-time
- Control human actors
- View analytics
- Edit scenarios
- Compare runs

## Testing Your Migration

### Step 1: Verify V2 Installation

```bash
scenario-lab version
```

Should show: `Scenario Lab V2: 2.0.0-alpha.1`

### Step 2: Test V2 with V1 Scenario

```bash
# Choose a simple scenario
scenario-lab run scenarios/test-regulation-negotiation --max-turns 3

# Compare with V1
python src/run_scenario.py scenarios/test-regulation-negotiation --max-turns 3

# Outputs should be identical
```

### Step 3: Validate Configuration

```bash
scenario-lab validate scenarios/ai-summit
```

Should report any issues.

### Step 4: Test New Features

```bash
# Cost estimation
scenario-lab estimate scenarios/ai-summit --max-turns 10

# Performance baseline
scenario-lab benchmark scenarios/test-regulation-negotiation
```

## Troubleshooting

### V2 CLI Not Found

```bash
# Reinstall package
pip install -e .

# Or use full path
python -m scenario_lab.cli run scenarios/test
```

### Import Errors

```bash
# Ensure dependencies installed
pip install -e ".[all]"

# Check Python version
python --version  # Should be 3.9+
```

### V1 Compatibility Issues

If V2 can't run a V1 scenario:

1. Check scenario format: `scenario-lab validate scenarios/problem-scenario`
2. Fall back to V1: `python src/run_scenario.py scenarios/problem-scenario`
3. Report issue: https://github.com/yourusername/scenario-lab/issues

### Performance Degradation

If V2 is slower than V1:

1. Run benchmark: `scenario-lab benchmark scenarios/test`
2. Compare with V1 baseline
3. Report if >10% slower

## Support & Resources

### Documentation

- [V2_ARCHITECTURE.md](V2_ARCHITECTURE.md) - Architecture overview
- [ROADMAP_V2.md](../ROADMAP_V2.md) - Development roadmap
- [README.md](../README.md) - Getting started

### Getting Help

- GitHub Issues: https://github.com/yourusername/scenario-lab/issues
- Discussions: https://github.com/yourusername/scenario-lab/discussions

### Reporting Bugs

When reporting V2 issues:

1. Specify V2 version: `scenario-lab version`
2. Include minimal reproduction
3. Compare with V1 behavior if applicable
4. Include error messages and logs

## Migration Checklist

- [ ] Install V2: `pip install -e .`
- [ ] Test V2 CLI: `scenario-lab version`
- [ ] Run test scenario in V2
- [ ] Compare V2 vs V1 output
- [ ] Validate existing scenarios
- [ ] Try new V2 features
- [ ] Import historic runs (Phase 2.2)
- [ ] Update documentation/workflows
- [ ] Train team on V2 features

## Timeline

### Now (Phase 2.0 - Foundation)

- ✓ V2 package structure
- ✓ Event system
- ✓ Immutable state models
- ✓ Basic CLI
- ⏳ Pydantic schemas complete
- ⏳ Integration tests

**What you can do**: Install and experiment with V2 CLI

### Next (Phase 2.1 - Modular Engine)

- Full scenario execution in V2
- Phase services extracted
- Web API ready

**What you can do**: Switch to V2 for all runs

### Later (Phase 2.2 - Database)

- SQLite analytics
- Import tools
- Fast queries

**What you can do**: Import V1 runs, use analytics

### Future (Phase 2.3 - Web)

- Dashboard
- Scenario editor
- Real-time monitoring

**What you can do**: Use web interface for all workflows

## Frequently Asked Questions

### Do I have to migrate?

No. V1 remains fully functional. Migrate when it makes sense for you.

### Will my V1 scenarios break?

No. V2 is backward compatible. All V1 scenarios work in V2.

### Can I run V1 and V2 side-by-side?

Yes. They don't interfere with each other.

### What about my existing data?

All V1 runs remain accessible. In Phase 2.2, you can import them into the V2 database for analytics.

### Is V2 stable?

V2 is currently alpha. Use V1 for production work until V2 reaches beta (Phase 2.1 complete).

### What's the performance impact?

Target is 20% faster than V1. Early results will be documented in performance baseline.

### How do I contribute to V2?

See [CONTRIBUTING.md](../CONTRIBUTING.md) (coming soon).

### When should I migrate?

Recommended timeline:
- **Now**: Experiment with V2
- **Phase 2.1 complete**: Consider switching for new work
- **Phase 2.2 complete**: Import historic data
- **Phase 2.3 complete**: Full V2 adoption

### What if I find a V2 bug?

Report it on GitHub Issues. Use V1 as fallback for critical work.

---

## Summary

Version 2 is designed for gradual, low-risk adoption:

1. **Install**: `pip install -e .`
2. **Experiment**: Try V2 CLI with test scenarios
3. **Compare**: Verify V2 matches V1 output
4. **Adopt**: Switch to V2 when comfortable
5. **Import**: Bring in historic data (Phase 2.2)
6. **Enhance**: Use new features (web, analytics)

No rush, no forced migration, no data loss. V2 is here when you're ready.
