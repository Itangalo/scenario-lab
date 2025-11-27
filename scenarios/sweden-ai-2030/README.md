# Sverige och AI 2030 - World Interpreter Migration

This scenario has been updated to use the **World Interpreter** system for narrative-driven mechanics.

## What Changed

### ✅ Enabled Narrative Mode
- Set `execution_mode: "narrative"` in `scenario.yaml`
- Actors now describe intentions in natural language instead of calling predefined functions

### ✅ Enhanced Metrics
- Replaced `metrics.yaml` with enhanced version including:
  - **Bounds**: Min/max values for all metrics
  - **Change Magnitudes**: Small/medium/large ranges for controlled changes
  - **Randomness**: Per-metric variance for variation across runs
  - **Dependencies**: Inter-metric relationships (e.g., unemployment affects sentiment)

### ✅ Simplified Methods
- `methods.py` no longer contains active action logic
- Kept for backward compatibility (can switch to `execution_mode: "legacy"`)
- All mechanics now handled by World Interpreter + generic primitives

## Key Dependencies in This Scenario

The enhanced metrics include several inter-metric dependencies:

1. **Unemployment → Public Sentiment**
   - High unemployment (>10%) reduces public sentiment by -2 points per %

2. **AI Capability → Unemployment**
   - Rapid AI progress (>100 hours) increases unemployment by 0.05% per point

3. **Business Profitability → Unemployment**
   - High profitability (>70) reduces unemployment by 2%

4. **EU Coordination → International Influence**
   - Strong EU coordination (>70) boosts Sweden's influence by 0.1 points

5. **Union Unity → Negotiating Power**
   - High internal unity (>75) adds 0.2 points to negotiating power

6. **AI Adoption → Business Profitability**
   - High AI adoption (>60) boosts profitability by 0.15 points

## How Actors Work Now

### Before (Legacy Mode)
```json
{
  "reasoning": "We need to boost AI adoption",
  "actions": [
    {"name": "invest_ai_adoption", "args": {"amount": 50}}
  ]
}
```

### After (Narrative Mode)
```json
{
  "reasoning": "Sweden's businesses are falling behind in AI adoption. We need to act decisively.",
  "actions_narrative": "The government will launch a major AI adoption initiative, allocating 5 billion SEK to support businesses in implementing AI technologies. We'll coordinate closely with the EU to ensure our approach aligns with upcoming regulations, and we'll invest in public education to build trust in these technologies.",
  "next_turn_goals": ["Increase AI adoption by 20%", "Strengthen EU coordination", "Maintain public trust above 60%"]
}
```

The World Interpreter translates the narrative into:
- Budget decrease (medium)
- AI adoption commitment increase (large)
- EU coordination increase (medium)
- Public trust adjustment (small increase)

## File Structure

```
sweden-ai-2030/
├── scenario.yaml              # execution_mode: "narrative"
├── metrics.yaml               # Enhanced with metadata
├── metrics-simple.yaml        # Backup of original simple format
├── metrics-enhanced.yaml      # Source of current metrics.yaml
├── methods.py                 # Simplified (legacy compatibility)
├── events.yaml                # Unchanged
├── background/                # Unchanged
└── README.md                  # This file
```

## Switching Back to Legacy Mode

If you want to use the old function-call system:

1. Edit `scenario.yaml`:
   ```yaml
   execution_mode: "legacy"
   ```

2. Restore old metrics if needed:
   ```bash
   cp metrics-simple.yaml metrics.yaml
   ```

3. Restore the full `methods.py` from git history

## Running Simulations

```bash
# Run with default settings (narrative mode)
python -m scenario_lab.cli run scenarios/sweden-ai-2030

# Specify turns
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --turns 5

# Use different model
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --model anthropic/claude-sonnet-4
```

## Debugging

Each turn directory now includes:

- `metric_changes.json`: Detailed log of all metric changes
  - Shows before/after values
  - Includes World Interpreter's reasoning
  - Tracks which actor requested each change

Example log entry:
```json
{
  "turn": 1,
  "actor": "government",
  "metric_path": "actors.government.private.ai_adoption_commitment",
  "old_value": 40.0,
  "new_value": 52.3,
  "operation": "adjust",
  "magnitude": "large",
  "direction": "increase",
  "reasoning": "Government narrative indicates major push for AI adoption",
  "applied_at": "2025-01-15T14:30:22.123456"
}
```

## Benefits

### For This Scenario

1. **Richer Narratives**: Swedish actors think strategically about EU coordination, labor relations, and public sentiment
2. **Emergent Dynamics**: Dependencies create realistic cascading effects (e.g., AI adoption → unemployment → sentiment)
3. **Variation**: Multiple runs produce different but plausible outcomes
4. **Less Code**: Metrics definition instead of Python functions

### Example Emergent Behavior

In one run, aggressive AI adoption by businesses might:
1. Increase business profitability ↑
2. But also increase unemployment ↑
3. Which decreases public sentiment ↓
4. Reducing government public trust ↓
5. Making further pro-AI policies harder

In another run with better coordination:
1. Government invests in retraining
2. Media builds AI expertise
3. Public sentiment remains stable
4. Unions maintain negotiating power
5. Transition happens smoothly

## Questions?

See the main documentation:
- `/docs/world-interpreter-design.md` - Complete design
- `/docs/world-interpreter-implementation-summary.md` - Usage guide
- `/examples/us-china-ai/metrics-enhanced.yaml` - Another example
