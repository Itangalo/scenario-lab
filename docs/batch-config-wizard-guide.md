# Batch Config Wizard & Dry-Run Guide

This guide covers two tools that make batch execution easier: the **Config Wizard** for creating batch configurations interactively, and **Dry-Run** for previewing batches before execution.

## Config Wizard

The batch config wizard helps you create batch configuration files through an interactive Q&A workflow, with validation and helpful suggestions.

### Quick Start

```bash
python src/create_batch_config.py --interactive
```

The wizard will guide you through creating a batch configuration step-by-step.

### Wizard Walkthrough

#### 1. Basic Information

```
Experiment name: My Model Comparison Study
Brief description: Testing different LLM models on regulation scenario
```

#### 2. Scenario Selection

```
Path to base scenario: scenarios/test-regulation-negotiation
✓ Valid scenario found at scenarios/test-regulation-negotiation
ℹ Found 2 actors: regulator, tech-company
```

The wizard automatically:
- Validates that the scenario exists
- Checks for required files (scenario.yaml)
- Detects actors in the scenario

#### 3. Run Configuration

```
Runs per variation (for statistical significance) [10]: 10
Maximum parallel runs (consider API rate limits) [2]: 3
Timeout per run (seconds) [1800]: 1800
```

**Tips:**
- **Runs per variation:** 10-20 for robust statistics, 5 for quick tests
- **Max parallel:** Consider your API rate limits (start with 2-3)
- **Timeout:** 1800s (30 min) is usually safe

#### 4. Budget Limits

```
Set a budget limit? (Y/n): y
Budget limit (USD) [20.00]: 50.00

Set a per-run cost limit? (Y/n): y
Per-run cost limit (USD) [1.00]: 2.00
```

**Budget limits prevent surprises:**
- Batch stops if total cost exceeds budget
- Individual runs halt if they exceed per-run limit

#### 5. Parameter Variations

```
Variation #1
Available actors: regulator, tech-company
Which actor to vary? [regulator]: regulator

Select LLM models for this actor:
ℹ Common LLM models:
  1. openai/gpt-4o-mini (Fast, cheap, good for testing)
  2. openai/gpt-4o (Balanced, good general purpose)
  3. anthropic/claude-3-haiku (Fast, cheap)
  4. anthropic/claude-3.5-sonnet (High quality)
  5. anthropic/claude-3-opus (Best quality, expensive)
  6. google/gemini-pro (Good performance)
  7. meta-llama/llama-3-70b-instruct (Open source)

Enter model numbers (comma-separated) or full model IDs [1,3]: 1,3
✓ Added variation: regulator with 2 models

Add another variation? (y/N): y
```

**Creating Variation Matrix:**
- Each variation adds a dimension to your experiment
- 2 variations with 2 values each = 2×2 = 4 total combinations
- The wizard shows you the total runs: 4 variations × 10 runs = 40 total runs

#### 6. Output Configuration

```
Output directory [experiments/my-model-comparison-study]: experiments/model-study

Save individual run outputs? (Y/n): y
Generate aggregated metrics? (Y/n): y
```

#### 7. Review and Save

```
Configuration Preview:
experiment_name: My Model Comparison Study
description: Testing different LLM models on regulation scenario
base_scenario: scenarios/test-regulation-negotiation
runs_per_variation: 10
max_parallel: 3
...

Save to experiments/model-study/batch-config.yaml? (Y/n): y
✓ Configuration saved to experiments/model-study/batch-config.yaml

ℹ To run this batch:
  python src/batch_runner.py experiments/model-study/batch-config.yaml

ℹ To preview without running:
  python src/batch_runner.py experiments/model-study/batch-config.yaml --dry-run
```

### Model Selection

The wizard provides common models, but you can also enter full model IDs:

```
Enter model numbers or full model IDs: 1,3,anthropic/claude-3-opus
```

This selects:
- Model #1 (openai/gpt-4o-mini)
- Model #3 (anthropic/claude-3-haiku)
- Custom: anthropic/claude-3-opus

### Tips for Using the Wizard

**Best Practices:**
1. Start with the wizard even if you know YAML - it catches mistakes
2. Use default values first, then customize
3. Set budget limits to avoid surprises
4. Start with 2-3 models, expand later
5. Use --dry-run after creating config to verify

**Keyboard Shortcuts:**
- `Ctrl+C` - Cancel wizard anytime
- `Enter` - Accept default value
- `y/n` - Yes/no questions

## Dry-Run

Dry-run shows exactly what will be executed without actually running anything. This lets you verify your batch configuration, estimate costs and time, and catch errors before spending money.

### Quick Start

```bash
python src/batch_runner.py experiments/my-study/batch-config.yaml --dry-run
```

### Dry-Run Output

```
======================================================================
                            BATCH PREVIEW
======================================================================

📊 Experiment: Model Comparison Study
   Testing different LLM models on regulation scenario

📁 Base scenario: scenarios/test-regulation-negotiation

🔢 Variations: 4
🔢 Runs per variation: 10
🔢 Total runs: 40

⚡ Execution mode: Parallel (3 concurrent runs)

💰 Budget limit: $50.00
💰 Per-run cost limit: $2.00

💵 Cost Estimation:
   Per run (estimated): $0.85
   Total (estimated): $34.00
   ✓ Within budget (68.0% of limit)

⏱️  Time Estimation:
   Estimated time: 40m

📋 Variations to be executed:

   1. regulator=gpt-4o-mini, tech-company=gpt-4o-mini
      Runs: 10
      • regulator: openai/gpt-4o-mini
      • tech-company: openai/gpt-4o-mini

   2. regulator=gpt-4o-mini, tech-company=claude-3-haiku
      Runs: 10
      • regulator: openai/gpt-4o-mini
      • tech-company: anthropic/claude-3-haiku

   3. regulator=claude-3-haiku, tech-company=gpt-4o-mini
      Runs: 10
      • regulator: anthropic/claude-3-haiku
      • tech-company: openai/gpt-4o-mini

   4. regulator=claude-3-haiku, tech-company=claude-3-haiku
      Runs: 10
      • regulator: anthropic/claude-3-haiku
      • tech-company: anthropic/claude-3-haiku

📁 Output directory: experiments/model-study

======================================================================
To execute this batch, run without --dry-run flag:
  python src/batch_runner.py experiments/model-study/batch-config.yaml
======================================================================
```

### Understanding the Output

#### Variations & Total Runs

```
🔢 Variations: 4
🔢 Runs per variation: 10
🔢 Total runs: 40
```

Shows the Cartesian product of your variations:
- 2 regulator models × 2 tech-company models = 4 variations
- Each variation runs 10 times
- Total: 40 scenario executions

#### Execution Mode

```
⚡ Execution mode: Parallel (3 concurrent runs)
```

- **Sequential:** Runs one at a time (max_parallel: 1)
- **Parallel:** Runs multiple simultaneously (max_parallel > 1)

#### Cost Estimation

```
💵 Cost Estimation:
   Per run (estimated): $0.85
   Total (estimated): $34.00
   ✓ Within budget (68.0% of limit)
```

**Estimates based on:**
- Number of actors in scenario
- Number of turns
- LLM models being used
- Historical token usage patterns

**Budget warnings:**
```
⚠️  Estimated cost exceeds budget!
⚠️  Budget allows ~25 runs (not 40)
```

If cost exceeds budget, dry-run tells you how many runs you can afford.

#### Time Estimation

```
⏱️  Time Estimation:
   Estimated time: 40m
```

**Calculation:**
- Assumes ~3 minutes per run (conservative estimate)
- Accounts for parallel execution
- Sequential: total_runs × 3min
- Parallel: (total_runs / max_parallel) × 3min

**Actual time varies based on:**
- Scenario complexity (turns, actors)
- LLM response speed
- Network conditions
- API rate limits

#### Variation Details

```
📋 Variations to be executed:

   1. regulator=gpt-4o-mini, tech-company=gpt-4o-mini
      Runs: 10
      • regulator: openai/gpt-4o-mini
      • tech-company: openai/gpt-4o-mini
```

Shows exactly which model combinations will be tested.

### When to Use Dry-Run

**Always use dry-run when:**
1. Running a batch for the first time
2. Trying a new scenario
3. Unsure about total cost
4. Testing complex variation matrices
5. Working with expensive models

**Workflow:**
```bash
# 1. Create config with wizard
python src/create_batch_config.py --interactive

# 2. Preview with dry-run
python src/batch_runner.py experiments/my-study/batch-config.yaml --dry-run

# 3. Adjust if needed (edit batch-config.yaml)

# 4. Run when ready
python src/batch_runner.py experiments/my-study/batch-config.yaml
```

### Common Dry-Run Scenarios

#### Scenario 1: Budget Check

```bash
# Create ambitious config
python src/create_batch_config.py --interactive
# ...50 runs per variation, 5 variations...

# Dry-run shows
💵 Cost Estimation:
   Total (estimated): $125.00
   ⚠️  Estimated cost exceeds budget!
   ⚠️  Budget allows ~40 runs (not 250)

# Adjust config, try again
```

#### Scenario 2: Time Planning

```bash
# Dry-run for overnight batch
python src/batch_runner.py experiments/large-study/batch-config.yaml --dry-run

⏱️  Time Estimation:
   Estimated time: 8h 20m

# Perfect for overnight run
```

#### Scenario 3: Verify Variations

```bash
# Complex variation matrix
python src/batch_runner.py experiments/complex/batch-config.yaml --dry-run

📋 Variations to be executed:
   1. actor1=model-a, actor2=model-x, actor3=model-1 (10 runs)
   2. actor1=model-a, actor2=model-x, actor3=model-2 (10 runs)
   ...
   27. actor1=model-c, actor2=model-z, actor3=model-3 (10 runs)

# Verify all 27 combinations are what you want
```

## Complete Workflow Example

### Step 1: Create Configuration

```bash
$ python src/create_batch_config.py --interactive

Batch Configuration Wizard
...interactive prompts...

✓ Configuration saved to experiments/my-experiment/batch-config.yaml
```

### Step 2: Preview

```bash
$ python src/batch_runner.py experiments/my-experiment/batch-config.yaml --dry-run

======================================================================
                            BATCH PREVIEW
======================================================================
...
💵 Cost Estimation:
   Total (estimated): $45.00
   ✓ Within budget (90.0% of limit)

⏱️  Time Estimation:
   Estimated time: 1h 30m
...
```

### Step 3: Adjust if Needed

```bash
# If cost/time too high, edit batch-config.yaml
vim experiments/my-experiment/batch-config.yaml

# Change runs_per_variation from 20 to 10
# Or remove some model variations

# Dry-run again to verify
python src/batch_runner.py experiments/my-experiment/batch-config.yaml --dry-run
```

### Step 4: Execute

```bash
$ python src/batch_runner.py experiments/my-experiment/batch-config.yaml

🔬 Batch Experiment: My Experiment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 15/40 (38%) ━━━
⏱️  Time: 22m 15s | Est. remaining: 35m 45s
💰 Cost: $16.50 / $50.00 (33%)
...
```

### Step 5: Analyze

```bash
$ python src/batch_analyzer.py experiments/my-experiment/ --report

# View results
cat experiments/my-experiment/analysis/analysis-report.md
```

## Tips & Best Practices

### For the Wizard

✓ **DO:**
- Use the wizard for all new batch configs
- Accept defaults first, customize later
- Set budget limits
- Review the preview before saving

✗ **DON'T:**
- Skip the wizard and write YAML manually (error-prone)
- Set unlimited budgets on first try
- Create 100+ variations without testing smaller first

### For Dry-Run

✓ **DO:**
- Always dry-run before expensive batches
- Use dry-run to plan overnight runs
- Dry-run after editing configs manually
- Compare dry-run estimates with actual results to improve planning

✗ **DON'T:**
- Skip dry-run for new scenarios
- Trust manual cost calculations
- Run large batches without preview

### General Workflow

1. **Start small:** Create 2-3 variations with 5 runs each
2. **Dry-run:** Verify everything looks correct
3. **Test run:** Execute the small batch
4. **Scale up:** If results look good, create larger batch
5. **Dry-run again:** Verify the scaled-up version
6. **Execute:** Run the full experiment

## Troubleshooting

### Wizard Issues

**"Scenario not found or invalid"**
- Check the path is correct
- Ensure scenario.yaml exists in the directory
- Verify scenario has actors/ directory

**"Must be a positive number"**
- Enter numbers without commas or other characters
- Use decimal point for dollars: `20.50` not `20,50`

### Dry-Run Issues

**"Unable to estimate cost"**
- Check that scenario has valid actor files
- Ensure actors have llm_model specified
- Verify scenario.yaml is valid YAML

**Cost shows $0.00**
- Scenario might use free models
- This is OK - estimation works correctly
- Free models are great for testing!

**Time estimate seems wrong**
- Default is 3 minutes per run (conservative)
- Actual time varies based on scenario complexity
- Use as rough guide, not exact prediction

## Advanced Usage

### Custom Model Lists

Edit the wizard's model list in `src/create_batch_config.py`:

```python
def get_common_models() -> Dict[str, str]:
    return {
        "your/custom-model": "Your Custom Model (description)",
        ...
    }
```

### Programmatic Config Creation

For automation, you can skip the wizard and create configs programmatically:

```python
import yaml

config = {
    'experiment_name': 'Automated Experiment',
    'base_scenario': 'scenarios/my-scenario',
    'runs_per_variation': 10,
    'max_parallel': 3,
    'budget_limit': 50.00,
    'variations': [
        {
            'type': 'actor_model',
            'actor': 'actor1',
            'values': ['openai/gpt-4o-mini', 'anthropic/claude-3-haiku']
        }
    ],
    'output_dir': 'experiments/auto-experiment'
}

with open('experiments/auto-experiment/batch-config.yaml', 'w') as f:
    yaml.dump(config, f)
```

Then dry-run and execute as usual.

## Further Reading

- [Batch Execution Guide](batch-execution-guide.md) - Complete batch system documentation
- [README.md](../README.md) - Main project documentation
- Example configs in `experiments/` directory

## Getting Help

If you encounter issues:
1. Try the wizard - it catches most mistakes
2. Use dry-run to verify
3. Check example configs in `experiments/`
4. Review error messages carefully
5. Start with simpler config and build up
