# Database & Analytics Guide

## Overview

Scenario Lab V2 provides a powerful SQLite-based analytics layer for querying and comparing scenario runs. All execution data is persisted to a database while preserving markdown files for human review.

## Architecture

### Dual Persistence

1. **Markdown Files** (for expert review)
   - World state narratives
   - Actor decisions with reasoning
   - Communication records
   - Easy to read and annotate

2. **SQLite Database** (for analytics)
   - Structured data for fast queries
   - Aggregations across runs
   - Metric tracking and comparison
   - Cost analysis

## Database Schema

### Core Tables

**runs** - Scenario execution metadata
- id, scenario_id, scenario_name
- status, turns, total_cost
- created, completed timestamps
- branching information

**turns** - Individual turn records
- turn_number, timestamp
- world_state content
- Foreign key to run

**decisions** - Actor decisions per turn
- actor, goals, reasoning, action
- timestamps, tokens
- Foreign key to turn

**metrics** - Extracted metrics
- metric_name, value
- source (world_state/actor/communication)
- Foreign key to turn

**communications** - Inter-actor messages
- type (bilateral/coalition/public)
- sender, recipients
- content, internal_notes

**costs** - LLM usage tracking
- actor, phase, model
- input/output tokens
- cost in USD

## Basic Usage

### Initialize Database

```python
from scenario_lab.database import Database

# Create/connect to database
db = Database("scenario-lab.db")

# Database schema is automatically created
```

### Query Runs

```python
# Get a specific run
run = db.get_run("run-001")
print(f"Run: {run.scenario_name}")
print(f"Turns: {run.total_turns}, Cost: ${run.total_cost:.4f}")

# List all runs
runs = db.list_runs()
for run in runs:
    print(f"{run.id}: {run.scenario_name} - {run.status}")

# Filter by scenario
ai_runs = db.list_runs(scenario_id="ai-2027")
```

### Query Decisions

```python
# Get all decisions for an actor
decisions = db.query_decisions_for_actor("United States")

for decision in decisions:
    print(f"Turn {decision.turn.turn_num}: {decision.action}")

# Filter by scenario
us_decisions = db.query_decisions_for_actor(
    "United States",
    scenario="ai-regulatory-negotiation"
)
```

### Query Metrics

```python
# Get all values for a metric
cooperation_metrics = db.query_metrics(metric_name="cooperation_level")

for metric in cooperation_metrics:
    print(f"Turn {metric.turn.turn_num}: {metric.value}")

# Filter by scenario
cooperation_in_ai_summit = db.query_metrics(
    metric_name="cooperation_level",
    scenario="ai-summit"
)

# Filter by actor
us_metrics = db.query_metrics(actor="United States")
```

## Analytics

### Run Statistics

Get comprehensive statistics for a run:

```python
stats = db.get_run_statistics("run-001")

print(f"Scenario: {stats['scenario_name']}")
print(f"Turns: {stats['turn_count']}")
print(f"Decisions: {stats['decision_count']}")
print(f"Total Cost: ${stats['total_cost']:.4f}")

# Cost breakdown by phase
for phase_cost in stats['cost_by_phase']:
    print(f"  {phase_cost['phase']}: ${phase_cost['total']:.4f}")
```

### Compare Runs

Compare multiple runs side-by-side:

```python
comparison = db.compare_runs(["run-001", "run-002", "run-003"])

for run_stats in comparison['runs']:
    print(f"\n{run_stats['scenario_name']} ({run_stats['run_id']})")
    print(f"  Turns: {run_stats['turn_count']}")
    print(f"  Cost: ${run_stats['total_cost']:.4f}")
    print(f"  Decisions: {run_stats['decision_count']}")
```

### Aggregate Metrics

Aggregate a metric across multiple runs:

```python
agg = db.aggregate_metrics("cooperation_level", scenario="ai-summit")

print(f"Cooperation Level (ai-summit):")
print(f"  Average: {agg['avg']:.2f}")
print(f"  Range: {agg['min']:.2f} - {agg['max']:.2f}")
print(f"  Samples: {agg['count']}")
```

## Advanced Queries

### Using SQLAlchemy Directly

For complex queries, you can use SQLAlchemy directly:

```python
from scenario_lab.database.models import Run, Turn, Decision, Metric
from sqlalchemy import func

session = db.get_session()

# Example: Find runs with highest cooperation
query = session.query(
    Run.scenario_name,
    func.avg(Metric.value).label('avg_cooperation')
).join(Turn).join(Metric).filter(
    Metric.name == 'cooperation_level'
).group_by(Run.scenario_name).order_by(
    func.avg(Metric.value).desc()
)

results = query.all()
for scenario, avg_coop in results:
    print(f"{scenario}: {avg_coop:.2f}")

session.close()
```

### Custom Analytics

```python
from sqlalchemy import func, and_

session = db.get_session()

# Example: Track metric evolution over turns
query = session.query(
    Turn.turn_num,
    func.avg(Metric.value).label('avg_value'),
    func.min(Metric.value).label('min_value'),
    func.max(Metric.value).label('max_value')
).join(Metric).join(Run).filter(
    and_(
        Metric.name == 'trust_level',
        Run.scenario_id == 'ai-summit'
    )
).group_by(Turn.turn_num).order_by(Turn.turn_num)

for turn_num, avg, min_val, max_val in query.all():
    print(f"Turn {turn_num}: avg={avg:.2f}, range=[{min_val:.2f}, {max_val:.2f}]")

session.close()
```

## Integration with Runners

### Automatic Persistence

The `SyncRunner` and `AsyncExecutor` automatically persist data when a database is provided:

```python
from scenario_lab.runners import SyncRunner
from scenario_lab.database import Database

# Create database
db = Database("my-scenarios.db")

# Create runner with database
runner = SyncRunner(
    scenario_path="scenarios/ai-summit",
    database=db  # Automatically persists all data
)

runner.setup()
final_state = await runner.run()

# Query results immediately
stats = db.get_run_statistics(final_state.run_id)
print(f"Run completed: ${stats['total_cost']:.4f}")
```

### AsyncExecutor Example

```python
from scenario_lab.runners import AsyncExecutor
from scenario_lab.database import Database

db = Database("scenarios.db")

executor = AsyncExecutor(
    scenario_path="scenarios/ai-2027",
    end_turn=10,
)

# Note: Database needs to be passed to SyncRunner internally
# or configured via the executor setup

await executor.setup()
final_state = await executor.execute()

# Analytics after execution
comparison = db.compare_runs([
    "run-001",
    "run-002",
    final_state.run_id
])
```

## Batch Analysis Workflows

### Scenario Variation Analysis

```python
from scenario_lab.database import Database
import pandas as pd

db = Database("batch-results.db")

# Get all runs for a scenario
runs = db.list_runs(scenario_id="ai-regulatory-negotiation")

# Extract key metrics
data = []
for run in runs:
    stats = db.get_run_statistics(run.id)

    # Get final cooperation level
    cooperation = db.query_metrics(
        scenario="ai-regulatory-negotiation",
        metric_name="cooperation_level"
    )
    final_coop = max(m.value for m in cooperation if m.turn.run_id == run.id)

    data.append({
        'run_id': run.id,
        'turns': stats['turn_count'],
        'cost': stats['total_cost'],
        'cooperation': final_coop
    })

# Convert to DataFrame for analysis
df = pd.DataFrame(data)
print(df.describe())

# Find high-cooperation, low-cost runs
efficient_runs = df[(df['cooperation'] > 0.7) & (df['cost'] < 1.0)]
print("\nEfficient runs (high cooperation, low cost):")
print(efficient_runs)
```

### Actor Strategy Comparison

```python
# Compare decision patterns across actors
for actor in ["United States", "European Union", "China"]:
    decisions = db.query_decisions_for_actor(
        actor,
        scenario="ai-summit"
    )

    # Analyze decision frequency
    print(f"\n{actor}: {len(decisions)} decisions across {len(set(d.turn.run_id for d in decisions))} runs")

    # Extract action patterns (simplified)
    actions = [d.action[:100] for d in decisions]  # First 100 chars
    # Further analysis...
```

## Performance Tips

### Indexing

The database automatically creates indexes on:
- run.scenario_id, run.status
- turn.run_id, turn.turn_num
- decision.actor
- metric.name, metric.value
- cost.actor, cost.phase

### Query Optimization

```python
# BAD: Loading everything into memory
all_metrics = db.query_metrics()  # Could be thousands
for metric in all_metrics:
    if metric.name == "cooperation_level":
        process(metric)

# GOOD: Filter in database
cooperation = db.query_metrics(metric_name="cooperation_level")
for metric in cooperation:
    process(metric)
```

### Session Management

```python
# Always close sessions when using raw SQLAlchemy
session = db.get_session()
try:
    results = session.query(Run).all()
    # Process results
finally:
    session.close()

# Or use the built-in methods which handle this automatically
runs = db.list_runs()  # Session automatically closed
```

## Export and Backup

### Export to CSV

```python
import csv
from scenario_lab.database import Database

db = Database("scenario-lab.db")

# Export metrics to CSV
metrics = db.query_metrics(scenario="ai-summit")

with open('ai-summit-metrics.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['run_id', 'turn', 'metric', 'value', 'actor'])

    for m in metrics:
        writer.writerow([
            m.turn.run_id,
            m.turn.turn_num,
            m.name,
            m.value,
            m.actor
        ])
```

### Backup Database

```bash
# SQLite backup (simple file copy)
cp scenario-lab.db scenario-lab-backup-2025-11-19.db

# Or use SQLite's backup command
sqlite3 scenario-lab.db ".backup 'backup.db'"
```

## Schema Migrations

The database schema is automatically created/updated when you initialize a Database instance. For version tracking:

```python
from scenario_lab.database import Database

db = Database()

# Check schema version
session = db.get_session()
version = session.execute("SELECT version FROM schema_version").fetchone()
print(f"Database schema version: {version[0]}")
session.close()
```

## Troubleshooting

### Database Locked

If you get "database is locked" errors:

```python
# Use StaticPool (default for SQLite)
db = Database("sqlite:///scenario-lab.db")  # Automatically handled

# Or check for unclosed sessions
# Make sure all db.get_session() calls have matching .close()
```

### Missing Data

If expected data isn't in the database:

1. Check that `DatabasePersistencePhase` is registered in the orchestrator
2. Verify the database path is correct
3. Check for errors in logs (database errors are logged but don't halt execution)

### Performance Issues

For large batch runs:

```python
# Use separate databases per batch
db = Database(f"batch-{batch_id}.db")

# Or periodic commits for long runs
# (handled automatically by DatabasePersistencePhase)
```

## Summary

The database layer provides powerful analytics capabilities while maintaining the human-readable markdown files that experts need for review. Use the database for:

- **Comparing** multiple scenario runs
- **Tracking** metrics over time
- **Analyzing** actor decision patterns
- **Optimizing** scenario parameters
- **Identifying** successful strategies

All while preserving the rich narrative outputs that make Scenario Lab valuable for policy research.
