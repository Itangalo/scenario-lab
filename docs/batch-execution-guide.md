# Batch Execution Guide

This guide explains how to use Scenario Lab's batch execution system to run multiple scenario variations for statistical analysis.

## Overview

The batch execution system allows you to:

- Run the same scenario multiple times with systematic variations
- Test different LLM models, parameters, or initial conditions
- Collect statistical data across hundreds or thousands of runs
- Identify patterns in successful vs failed scenarios
- Compare cost-efficiency of different approaches
- Generate comprehensive analysis reports

## Quick Start

### 1. Create a Batch Configuration

Create a YAML file defining your batch experiment:

```yaml
# experiments/my-experiment/batch-config.yaml
experiment_name: "Model Comparison Study"
description: "Compare GPT-4 vs Claude in regulation negotiation"

base_scenario: "scenarios/test-regulation-negotiation"

# Run configuration
runs_per_variation: 10      # Run each variation 10 times
max_parallel: 2             # Max 2 concurrent runs
timeout_per_run: 1800       # 30 minutes max per run

# Cost controls
budget_limit: 20.00         # Stop if total cost exceeds $20
cost_per_run_limit: 1.00    # Stop individual runs if they exceed $1

# Variations to test
variations:
  - type: "actor_model"
    actor: "regulator"
    values:
      - "openai/gpt-4o-mini"
      - "anthropic/claude-3-haiku"

  - type: "actor_model"
    actor: "tech-company"
    values:
      - "openai/gpt-4o-mini"
      - "anthropic/claude-3-haiku"

# This creates 2x2 = 4 variations × 10 runs = 40 total runs

output_dir: "experiments/my-experiment"
save_individual_runs: true
aggregate_metrics: true
```

### 2. Run the Batch

```bash
python src/batch_runner.py experiments/my-experiment/batch-config.yaml
```

### 3. Analyze Results

```bash
# Generate analysis report
python src/batch_analyzer.py experiments/my-experiment/ --report

# View results
cat experiments/my-experiment/analysis/analysis-report.md
```

## Batch Configuration Reference

### Required Fields

- `experiment_name` (string): Name of your experiment
- `base_scenario` (string): Path to scenario directory to use as base

### Run Configuration

- `runs_per_variation` (int, default: 1): How many times to run each variation
- `max_parallel` (int, default: 1): Maximum concurrent runs (consider API rate limits)
- `timeout_per_run` (int, default: 1800): Maximum seconds per run

### Cost Controls

- `budget_limit` (float, optional): Maximum total spend for batch in USD
- `cost_per_run_limit` (float, optional): Maximum cost per individual run in USD

If either limit is exceeded, the batch will halt gracefully and save state.

### Variations

The `variations` field defines how to systematically modify the base scenario. Each variation creates a new dimension in the parameter space.

#### Actor Model Variation

Test different LLM models for specific actors:

```yaml
variations:
  - type: "actor_model"
    actor: "actor-short-name"  # Must match actor's short_name in scenario
    values:
      - "openai/gpt-4o-mini"
      - "openai/gpt-4o"
      - "anthropic/claude-3-haiku"
```

**Cartesian Product:** Multiple variations create all combinations. Example:

```yaml
variations:
  - type: "actor_model"
    actor: "actor1"
    values: ["model-a", "model-b"]  # 2 options

  - type: "actor_model"
    actor: "actor2"
    values: ["model-x", "model-y", "model-z"]  # 3 options
```

This creates 2 × 3 = 6 variations. With `runs_per_variation: 10`, you get 60 total runs.

### Output Configuration

- `output_dir` (string): Where to save batch results
- `save_individual_runs` (bool, default: true): Save full output for each run
- `aggregate_metrics` (bool, default: true): Generate aggregated analysis

## Output Structure

After running a batch, you'll have:

```
experiments/my-experiment/
├── batch-config.yaml          # Your configuration (copied here)
├── batch-summary.json         # High-level summary
├── batch-state.json           # State for resumption
├── batch-costs.json           # Cost tracking data
├── runs/                      # Individual run outputs
│   ├── var-001-run-001/
│   │   ├── world-state-*.md
│   │   ├── actor-*.md
│   │   ├── metrics.json
│   │   ├── costs.json
│   │   └── scenario-state.json
│   ├── var-001-run-002/
│   ├── var-002-run-001/
│   └── ...
└── analysis/                  # Aggregated analysis
    ├── analysis-report.md     # Human-readable report
    ├── metrics-analysis.json  # Statistical analysis
    ├── variation-statistics.json
    └── patterns.json          # Identified patterns
```

## Resuming Batches

If a batch is interrupted (budget limit, rate limit, or Ctrl+C), you can resume:

```bash
python src/batch_runner.py experiments/my-experiment/batch-config.yaml --resume
```

The system will:

- Load previous state from `batch-state.json`
- Skip already-completed runs
- Continue from where it left off
- Preserve all cost tracking and progress

## Analyzing Results

### Automatic Analysis

After batch completion, run the analyzer:

```bash
python src/batch_analyzer.py experiments/my-experiment/
```

This generates:

- `analysis/metrics-analysis.json` - Statistics per metric (mean, std, min, max)
- `analysis/variation-statistics.json` - Per-variation statistics
- `analysis/patterns.json` - Identified patterns and success factors

### Generate Report

Create a human-readable markdown report:

```bash
python src/batch_analyzer.py experiments/my-experiment/ --report
```

The report includes:

- Overall success rate
- Statistics for each metric across all runs
- Comparison between variations
- Cost efficiency analysis
- Pattern identification

### Manual Analysis

You can also analyze data programmatically:

```python
from batch_analyzer import BatchAnalyzer

analyzer = BatchAnalyzer('experiments/my-experiment')
analyzer.collect_run_data()

# Get overall statistics
metrics = analyzer.calculate_metric_statistics()
print(f"Average cooperation_level: {metrics['cooperation_level']['mean']:.2f}")

# Compare variations
comparison = analyzer.compare_variations('cooperation_level')
print("Best variation:", comparison[0])

# Identify patterns
patterns = analyzer.identify_patterns()
print(f"Success rate: {patterns['success_rate']*100:.1f}%")
```

## Best Practices

### Start Small

Begin with a small batch to verify everything works:

```yaml
runs_per_variation: 2
budget_limit: 1.00
```

Then scale up once you're confident.

### Use Cost Limits

Always set budget limits to avoid surprises:

```yaml
budget_limit: 50.00          # Hard cap
cost_per_run_limit: 2.00     # Per-run safety net
```

### Consider Rate Limits

Don't set `max_parallel` too high:

- OpenRouter free tier: Keep `max_parallel: 1-2`
- Paid tier: Can use `max_parallel: 3-5` depending on limits

### Use Free Models for Testing

Test your batch configuration with free models first:

```yaml
variations:
  - type: "actor_model"
    actor: "your-actor"
    values:
      - "alibaba/tongyi-deepresearch-30b-a3b:free"
```

### Design for Statistical Power

For meaningful statistical analysis, use enough runs:

- Exploratory: 5-10 runs per variation
- Robust analysis: 20-50 runs per variation
- Publication-quality: 100+ runs per variation

## Example Use Cases

### 1. Model Comparison

Compare which LLM models perform best in your scenario:

```yaml
variations:
  - type: "actor_model"
    actor: "negotiator"
    values:
      - "openai/gpt-4o-mini"
      - "openai/gpt-4o"
      - "anthropic/claude-3-haiku"
      - "anthropic/claude-3.5-sonnet"

runs_per_variation: 20
```

Analyze which model achieves better outcomes on your defined metrics.

### 2. Sensitivity Analysis

Test if outcomes change with different model combinations:

```yaml
variations:
  - type: "actor_model"
    actor: "actor1"
    values: ["fast-model", "smart-model"]

  - type: "actor_model"
    actor: "actor2"
    values: ["fast-model", "smart-model"]
```

This creates 4 combinations: fast-fast, fast-smart, smart-fast, smart-smart.

### 3. Robustness Testing

Run the same scenario many times to measure variability:

```yaml
variations: []  # No variations, just multiple runs
runs_per_variation: 50
```

Analyze: How consistent are outcomes? What's the variance in key metrics?

## Troubleshooting

### "Budget limit reached"

Your batch exceeded `budget_limit`. Either:

- Increase the limit
- Reduce `runs_per_variation`
- Use cheaper models
- Resume with `--resume` after increasing limit

### "API rate limit" errors

You hit API rate limits. Solutions:

- Reduce `max_parallel`
- Add API key with higher limits
- Wait and resume with `--resume`

### "Run cost exceeds limit"

Individual run exceeded `cost_per_run_limit`. Either:

- Increase `cost_per_run_limit`
- Reduce scenario complexity (fewer turns)
- Use cheaper models for world state updates

### Incomplete batches

If a batch stops early, check:

```bash
cat experiments/my-experiment/batch-summary.json
```

Look at `runs_completed`, `runs_failed`, and `failed_runs` for details.

Resume with:

```bash
python src/batch_runner.py experiments/my-experiment/batch-config.yaml --resume
```

## Advanced Topics

### Custom Metrics

Define metrics in your scenario's `metrics.yaml`:

```yaml
metrics:
  cooperation_level:
    description: "Level of cooperation between actors"
    extraction_method: "regex"
    pattern: "cooperation.*?(\\d+)"
    type: "int"
```

These will be automatically tracked and analyzed in batch runs.

### Parallel Execution

Currently, batch runner uses sequential execution. Parallel execution is coming in a future update and will support:

- Async execution with configurable parallelism
- Shared rate limit handling across workers
- Real-time progress bars
- Dynamic load balancing

## Further Reading

- [README.md](../README.md) - Main project documentation
- [Example Batch Configs](../experiments/) - Sample configurations
- [Metrics Guide](metrics-guide.md) - How to define metrics (if exists)

## Getting Help

If you encounter issues:

1. Check the batch summary: `batch-summary.json`
2. Review failed runs: Look in `runs/` for error messages
3. Check logs: Each run has a `scenario.log` file
4. Reduce complexity: Try with fewer variations and runs first
