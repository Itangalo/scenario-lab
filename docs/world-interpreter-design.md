# World Interpreter Design Document

## Overview

This document describes the design for replacing hard-coded action functions with a narrative-driven World Interpreter system.

## Goals

1. **Narrative Freedom**: Actors express intentions in natural language instead of predefined function calls
2. **Scenario Decoupling**: Generic mechanics reduce scenario-specific code
3. **Controlled Randomness**: Introduce variation across simulation runs
4. **Transparency**: Clear logging of how narrative translates to mechanics

## Enhanced Metrics Schema

### Current Format (Simple)
```yaml
world:
  global_temperature: 1.2
  ai_catastrophe_risk: 0.1
```

### New Format (Enhanced with Metadata)
```yaml
world:
  global_temperature:
    value: 1.2
    min: 0.0
    max: 3.0
    unit: "degrees_celsius"
    description: "Global temperature increase"
    change_magnitudes:
      small: [0.01, 0.05]
      medium: [0.05, 0.15]
      large: [0.15, 0.5]
    randomness: 0.1  # 10% random variation
    dependencies:
      - metric: "world.ai_catastrophe_risk"
        type: "multiplicative"
        coefficient: 1.2
        condition: "> 0.3"
```

### Metadata Fields

- **value**: Current metric value
- **min/max**: Bounds for validation (optional)
- **unit**: Display/interpretation hint (optional)
- **description**: Human-readable explanation
- **change_magnitudes**: Ranges for small/medium/large changes
  - Used by World Interpreter to calibrate narrative → mechanics
- **randomness**: Variance factor (0.0 = deterministic, 1.0 = high variance)
- **dependencies**: Inter-metric relationships
  - **metric**: Path to dependent metric
  - **type**: "additive" or "multiplicative"
  - **coefficient**: Strength of dependency
  - **condition**: Optional constraint (e.g., "> 50", "< 0.5")

## Generic Action Primitives

Replace scenario-specific actions with:

### 1. `adjust_metric(actor, metric_path, magnitude, direction, reason)`
- **magnitude**: "small" | "medium" | "large"
- **direction**: "increase" | "decrease"
- Looks up change range from metric metadata
- Applies randomness
- Validates bounds
- Triggers dependency calculations

### 2. `set_metric(actor, metric_path, value, reason)`
- Direct assignment (used by events, not actors)
- Validates bounds
- Triggers dependencies

### 3. `apply_random_variation(metric_path)`
- Applies configured randomness to a metric
- Used during post-turn processing

## World Interpreter Architecture

### Input
Actors provide free-form narrative in execution phase:
```json
{
  "reasoning": "narrative explanation of intentions",
  "actions_narrative": "We will invest heavily in AI safety research while pushing for international cooperation on AI regulation...",
  "next_turn_goals": ["goal1", "goal2"]
}
```

### Process
1. **Parse Narrative**: World Interpreter (LLM) reads actor's narrative
2. **Extract Intents**: Identifies concrete actions/changes intended
3. **Map to Metrics**: Translates intents to metric adjustments
4. **Generate Changes**: Outputs structured metric change commands
5. **Validate**: Check bounds, dependencies, plausibility
6. **Apply**: Execute changes via generic primitives
7. **Synthesize**: Director weaves into narrative

### Output Format (from World Interpreter)
```json
{
  "metric_changes": [
    {
      "metric": "actors.USA.private.ai_safety_research",
      "operation": "adjust",
      "magnitude": "large",
      "direction": "increase",
      "reasoning": "Actor narrative indicates major investment in AI safety"
    },
    {
      "metric": "actors.USA.public.budget",
      "operation": "adjust",
      "magnitude": "medium",
      "direction": "decrease",
      "reasoning": "Investment requires budget allocation"
    },
    {
      "metric": "world.global_ai_regulation",
      "operation": "adjust",
      "magnitude": "small",
      "direction": "increase",
      "reasoning": "Actor advocates for international cooperation"
    }
  ],
  "interpretation": "The USA prioritizes AI safety through substantial research investment..."
}
```

## World Interpreter Prompt Structure

```
You are the World Interpreter for Scenario Lab.

Your role: Translate actor narratives into mechanical consequences.

ACTOR NARRATIVE:
{actor_narrative}

CURRENT METRICS:
{visible_metrics_for_context}

METRIC METADATA:
{metric_definitions_with_bounds_and_magnitudes}

CONSTRAINTS:
1. Actors can only directly affect their own private metrics
2. World metrics change through indirect consequences
3. Other actors' metrics change through relationships/agreements
4. Stay within defined bounds and magnitudes
5. Be conservative: small changes are more plausible than large

OUTPUT FORMAT:
Return JSON with:
- metric_changes: List of metric adjustments
- interpretation: Narrative summary for Director

METRIC CHANGE FORMAT:
{
  "metric": "path.to.metric",
  "operation": "adjust",
  "magnitude": "small|medium|large",
  "direction": "increase|decrease",
  "reasoning": "why this change makes sense"
}
```

## Dependency System

### Additive Dependencies
```yaml
actors:
  USA:
    public:
      international_influence:
        value: 90
        dependencies:
          - metric: "actors.USA.public.budget"
            type: "additive"
            coefficient: 0.1
            condition: "> 1000"
```
When budget > 1000, international_influence gains +0.1 per turn.

### Multiplicative Dependencies
```yaml
world:
  ai_catastrophe_risk:
    value: 0.1
    dependencies:
      - metric: "world.global_ai_regulation"
        type: "multiplicative"
        coefficient: 0.8
        condition: "> 50"
```
When regulation > 50, catastrophe_risk multiplies by 0.8 (decreases).

## Implementation Status

### ✅ Phase 1: Enhanced Metrics Schema
- [x] Updated Pydantic models for metric metadata
- [x] Added backward compatibility for simple metrics
- [x] Updated metrics.yaml parser with parse_enhanced_metrics()

### ✅ Phase 2: Generic Primitives
- [x] Implemented adjust_metric() with magnitude ranges
- [x] Implemented set_metric_direct() with validation
- [x] Implemented apply_random_variation()
- [x] Added bounds enforcement
- [x] Added change history logging (MetricChangeLog)

### ✅ Phase 3: Dependency System
- [x] Implemented additive dependencies
- [x] Implemented multiplicative dependencies
- [x] Added condition evaluation with regex patterns
- [x] Added cycle detection

### ✅ Phase 4: World Interpreter Agent
- [x] Created WorldInterpreter class
- [x] Designed prompt templates (integrated in class)
- [x] Implemented narrative → mechanics translation
- [x] Added plausibility validation
- [x] Added detailed logging

### ✅ Phase 5: Engine Integration
- [x] Updated execution phase to accept narrative input
- [x] Route narrative through World Interpreter
- [x] Apply interpreter output via primitives
- [x] Updated Director synthesis integration
- [x] Added execution_mode flag for backward compatibility

### 🔄 Phase 6: Testing & Refinement
- [x] Created enhanced metrics.yaml example (metrics-enhanced.yaml)
- [ ] Test with multiple runs for randomness
- [ ] Validate dependency cascades
- [ ] Tune interpreter prompt for quality

## Usage Instructions

### Converting Existing Scenarios

To enable the World Interpreter for an existing scenario:

1. **Update scenario.yaml** to set execution mode:
```yaml
execution_mode: "narrative"  # or "legacy" for old function-call mode
```

2. **Enhance metrics.yaml** (optional but recommended):
```yaml
world:
  ai_catastrophe_risk:
    value: 0.1
    min: 0.0
    max: 1.0
    description: "Probability of catastrophic AI incident"
    change_magnitudes:
      small: [0.01, 0.03]
      medium: [0.03, 0.08]
      large: [0.08, 0.2]
    randomness: 0.1
    dependencies:
      - metric: "world.global_ai_regulation"
        type: "multiplicative"
        coefficient: 0.95
        condition: "> 0.3"
```

3. **Remove action functions** from methods.py (now handled by World Interpreter)

4. **Update actor prompts** to encourage narrative descriptions

### Creating New Scenarios

For new scenarios, use the enhanced format from the start:

1. Use `examples/us-china-ai/metrics-enhanced.yaml` as a template
2. Define bounds, magnitudes, and dependencies for each metric
3. Set `execution_mode: "narrative"` in scenario.yaml
4. Write actor backgrounds that encourage strategic thinking

### Debugging Metric Changes

The system creates detailed logs in each turn directory:

- `metric_changes.json`: Complete log of all metric changes
  - Shows before/after values
  - Includes reasoning from World Interpreter
  - Tracks which actor requested each change

Example log entry:
```json
{
  "turn": 1,
  "actor": "USA",
  "metric_path": "actors.USA.private.ai_safety_research",
  "old_value": 50.0,
  "new_value": 58.5,
  "operation": "adjust",
  "magnitude": "large",
  "direction": "increase",
  "reasoning": "Actor narrative indicates major investment in AI safety",
  "applied_at": "2025-01-15T10:30:45.123456"
}
```

### Tuning the World Interpreter

The World Interpreter prompt can be customized by:

1. Creating a custom prompt template file
2. Passing it to WorldInterpreter constructor:
```python
interpreter = WorldInterpreter(
    llm_provider=provider,
    model=model_name,
    prompt_template_path=Path("prompts/custom_interpreter.txt")
)
```

Key prompt parameters:
- **Magnitude guidelines**: Tune small/medium/large thresholds
- **Conservatism level**: Adjust how cautious the interpreter is
- **Context emphasis**: How much weight to give to current metrics vs narrative

### Backward Compatibility

The system maintains full backward compatibility:

- Set `execution_mode: "legacy"` to use old function-call system
- Simple metrics (just numbers) work with enhanced system
- Existing scenarios run unchanged with legacy mode

## Design Decisions

### Q: How autonomous should the World Interpreter be?
**A**: Constrained by scenario rules. The interpreter translates narrative to mechanics, but:
- Cannot exceed defined magnitude ranges
- Must respect metric bounds
- Cannot modify metrics without justification from narrative

### Q: Should randomness be per-metric or global?
**A**: Per-metric. Different metrics have different uncertainty levels:
- Budget: Low randomness (deterministic accounting)
- Public sentiment: High randomness (unpredictable social dynamics)
- AI capability: Medium randomness (research has uncertain outcomes)

### Q: Can methods.py be eliminated entirely?
**A**: No. Keep it for:
- Scenario-specific dependency logic
- Complex multi-metric calculations
- Event handlers
But replace action functions with generic primitives.

### Q: How to ensure interpreter stays within bounds?
**A**: Multiple layers:
1. **Metadata bounds**: Hard min/max constraints
2. **Magnitude ranges**: Calibrated reasonable changes
3. **Validation**: Check output before applying
4. **Prompt engineering**: Instruct interpreter to be conservative

### Q: How to debug LLM-mediated changes?
**A**: Comprehensive logging:
- Save interpreter input (actor narrative)
- Save interpreter output (metric changes + reasoning)
- Log before/after values
- Track dependency cascades
- Include in turn artifacts

## File Structure Changes

```
scenario-name/
├── metrics.yaml          # Enhanced with metadata
├── methods.py            # Generic primitives + dependencies
└── runs/
    └── run-001/
        └── turn-01/
            ├── actions.json           # Now contains narratives
            ├── interpreter_log.json   # NEW: interpretation details
            ├── metric_changes.json    # NEW: change history
            └── ...
```

## Example: US-China-AI Conversion

### Before (Hard-coded)
```python
def invest_ai_research(self, actor, args, state):
    amount = args.get("amount", 10)
    current_budget = state.get_metric(actor, "public.budget")
    state.set_metric(actor, "public.budget", current_budget - amount)
    # ... complex logic ...
```

### After (Narrative-driven)
Actor output:
```json
{
  "reasoning": "China is falling behind in AI capabilities...",
  "actions_narrative": "We commit 50 billion to accelerate AI research, focusing on both capability advancement and safety measures. We'll also reach out to European partners to coordinate regulation.",
  "next_turn_goals": ["Achieve AI parity with USA", "Build EU alliance"]
}
```

World Interpreter output:
```json
{
  "metric_changes": [
    {"metric": "actors.China.private.ai_capability", "operation": "adjust", "magnitude": "large", "direction": "increase"},
    {"metric": "actors.China.private.ai_safety_research", "operation": "adjust", "magnitude": "medium", "direction": "increase"},
    {"metric": "actors.China.public.budget", "operation": "adjust", "magnitude": "large", "direction": "decrease"},
    {"metric": "actors.China.relationships.EU.trust", "operation": "adjust", "magnitude": "small", "direction": "increase"}
  ]
}
```

## Success Metrics

1. **Reduced Code**: methods.py shrinks from 200+ to <50 lines
2. **Scenario Portability**: New scenarios need only metrics.yaml, not custom code
3. **Variation**: Multiple runs produce different but plausible outcomes
4. **Transparency**: Logs clearly show narrative → mechanics translation
5. **Quality**: Director narratives remain coherent and engaging
