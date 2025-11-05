# Exogenous Events Guide

Exogenous events are background developments that occur independently of actor decisions. They enable more realistic scenarios where the world evolves through both actor choices and external factors.

## Overview

Exogenous events include:
- **Background trends** (compute costs declining, academic research)
- **Random events** (incidents, breakthroughs, policy announcements)
- **Conditional events** (triggered when metrics reach thresholds)
- **Scheduled events** (conferences, reports at specific times)

## Configuration

Create an `exogenous-events.yaml` file in your scenario's definition directory:

```yaml
exogenous_events:
  # Event definitions here
```

If this file doesn't exist, the scenario runs without exogenous events (backward compatible).

## Event Types

### 1. Trend Events

Regular recurring background developments:

```yaml
- type: trend
  name: "Compute Cost Decline"
  description: "Training costs decrease by ~10% this month due to hardware improvements"
  turn_range: [1, 66]  # Active from turn 1 to 66
  frequency: 3         # Occurs every 3 turns
```

### 2. Random Events

Probabilistic events that may occur:

```yaml
- type: random
  name: "Minor Safety Incident"
  description: "An AI system exhibits unexpected behavior, raising safety concerns"
  probability: 0.08    # 8% chance each turn
  turn_range: [10, 50] # Can only occur between turns 10-50
  once: true           # Triggers at most once
```

### 3. Conditional Events

Triggered when metrics reach thresholds:

```yaml
- type: conditional
  name: "Emergency Regulation"
  description: "Governments announce emergency AI safety regulations"
  conditions:
    misalignment_risk_level: ">= 8"
    regulatory_stringency: "< 6"
  turn_range: [20, 60]
  once: true
```

**Supported operators:** `>=`, `>`, `<=`, `<`, `==`, `!=`

### 4. Scheduled Events

Events at specific turns:

```yaml
- type: scheduled
  turn: 24
  name: "Major Conference"
  description: "Annual AI conference presents new capability results"
  once: true  # Default for scheduled events
```

## Integration with World State

Exogenous events are provided to the world state synthesis LLM alongside actor decisions:

```
## Actor Actions This Turn
[Actor 1 actions]
[Actor 2 actions]

## Background Events This Turn
**Compute Cost Decline:** Training costs decrease by ~10% this month...
**Minor Safety Incident:** An AI system at Company X exhibits...

## Your Task
Synthesize these actions and background events into an updated world state...
```

The LLM weaves events naturally into the narrative rather than listing them separately.

## Example: AI 2027 Scenario

The AI 2027 scenario includes:

**Trends (6 events):**
- Compute costs declining every 3 months
- Academic research publishing every 2 months
- Chip supply tightening every 4 months

**Scheduled (3 events):**
- Major AI conference at turn 12
- OECD report at turn 24
- G7 summit at turn 36

**Random (5 events):**
- Minor incidents (8% probability)
- Interpretability breakthrough (6%)
- Top researcher recruitment (5%)
- Export controls (7%)
- Economic downturn (4%)

**Conditional (5 events):**
- Major safety incident (if capabilities high, alignment low)
- Public safety movement (if awareness and risk both high)
- Alignment research crisis (if capability-alignment gap large)
- International cooperation (if risk high, some cooperation exists)
- Emergency regulation (if risk very high, regulation low)

This creates a rich, dynamic environment where the world evolves realistically beyond just actor decisions.

## Technical Details

### Event Manager

The `ExogenousEventManager` class handles event logic:

```python
from exogenous_events import ExogenousEventManager

# Load from YAML
event_manager = load_exogenous_events(scenario_path)

# Get events for a turn
events = event_manager.get_events_for_turn(
    turn=15,
    metrics={'ai_capability_level': 7.5, 'alignment_progress': 3.2}
)

# Returns: [{'name': 'Event Name', 'description': 'What happened...'}]
```

### One-Time vs Repeating

- **once: true** (default for most) - Event can only trigger once in the entire scenario
- **once: false** - Event can trigger multiple times (e.g., researcher recruitment)

Once an event triggers, it's tracked to prevent re-triggering (even across resumed scenarios).

### Metrics for Conditional Events

Conditional events use the most recent metrics values. Metrics are extracted from world state text after each turn, so conditional events on turn N use metrics from turn N-1.

If metrics haven't been extracted yet (turn 1), conditional events won't trigger.

## Best Practices

**1. Use Trends for Predictable Changes**
- Economic cycles, technology improvements, regular publications
- Frequency should match scenario turn duration

**2. Use Random Events Sparingly**
- Keep probabilities low (2-10%)
- Too many random events reduce actor agency
- Use for genuinely unpredictable developments

**3. Use Conditional Events for Emergent Dynamics**
- Safety incidents when risk is high
- Public movements when awareness grows
- Policy responses when problems escalate

**4. Write Clear Descriptions**
- Events are shown directly to the world state LLM
- Include concrete details, not just vague trends
- Describe impact, not just what happened

**5. Test Event Timing**
- Run short test scenarios to verify events trigger appropriately
- Check that turn_range makes sense for your scenario duration
- Ensure conditional thresholds are reachable

## Debugging

Enable DEBUG logging to see event triggers:

```bash
python src/run_scenario.py scenario-path --verbose
```

You'll see:
```
📋 2 background event(s) occurring this turn
   - Compute Cost Decline
   - Academic Research Progress
```

Check the world state markdown files to see how events were integrated into the narrative.

## See Also

- AI 2027 scenario: `scenarios/ai-2027/definition/exogenous-events.yaml`
- Event manager code: `src/exogenous_events.py`
- World state updater: `src/world_state_updater.py`
