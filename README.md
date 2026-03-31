# Scenario Lab

If you are an AI coding agent working in this repository, read [AGENTS.md](AGENTS.md) before making changes.

Scenario Lab is a framework for running multi-turn scenario simulations with LLMs.

You define a world, a set of actors, a few quantitative metrics, and possible external events. Scenario Lab then simulates how that world evolves over time by using LLMs to:

- determine which events occur
- generate actions for each actor
- update the quantitative rules that shape the world
- produce new metric values and a narrative for each turn

The output is not just a final summary. Each run produces a full turn-by-turn record, which makes it possible to inspect what happened, compare runs, and analyze why a specific future emerged.

## What It Is Good For

Scenario Lab is built for exploratory analysis, not point prediction.

Typical use cases include:

- exploring how a policy, technology shift, or crisis might play out over time
- comparing many runs of the same scenario to see where outcomes converge or diverge
- testing "what if" changes by branching from an earlier run
- studying which events, actor choices, or institutional responses drive a specific outcome

In practice, that means you can use it for questions like:

- What happens if AI adoption rises faster than labor-market adaptation?
- Which responses make the same shock lead to stability in one run and backlash in another?
- How sensitive is an outcome to one changed metric, event, or model choice?

## How It Works

Each turn follows the same basic loop:

1. The system evaluates which external events happen.
2. Each actor responds to the current situation.
3. The system updates the metric rules if the world has changed.
4. The system updates the metrics and writes the turn narrative.
5. If the scenario includes constitutional constraints, an optional referee step checks for unrealistic changes.
6. The historical summary is updated for the next turn.

LLMs do the scenario reasoning. Python handles orchestration, validation, persistence, and reporting.

## Quick Start

### Installation

```bash
pip install -e .
cp .env.example .env
```

Then add your `OPENROUTER_API_KEY` to `.env`.

### Recommended workflow

Scenario Lab works much better with a terminal-based AI coding agent assisting your workflow, for example:

- Claude Code
- OpenAI Codex
- Gemini CLI

You can run scenarios manually, but an agent is especially useful for reviewing run outputs, comparing trajectories, and iterating quickly on prompts/rules.

### Run the example scenario

```bash
python -m scenario_lab.cli run scenarios/sweden-ai-2030
```

### Run a shorter test

```bash
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --turns 3
```

### Estimate cost before running

```bash
python -m scenario_lab.cli estimate scenarios/sweden-ai-2030 --turns 10
```

### Validate a scenario without running it

```bash
python -m scenario_lab.cli validate scenarios/sweden-ai-2030
```

## Core Commands

### Run a scenario

```bash
python -m scenario_lab.cli run scenarios/sweden-ai-2030
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --turns 5
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --dry-run
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --override output_language=Swedish
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --skip-model-checks
```

By default, `run` performs model hygiene checks before execution and warns if the configured models look stale or risky.

### Validate a scenario

```bash
python -m scenario_lab.cli validate scenarios/sweden-ai-2030
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --validate
```

Validation checks:

- scenario structure and required files
- actor references
- metric references in prompts and rules
- event probability expressions
- LLM configuration
- model hygiene warnings

### Inspect or control cost

```bash
python -m scenario_lab.cli estimate scenarios/sweden-ai-2030 --turns 10
python -m scenario_lab.cli costs scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS
python -m scenario_lab.cli costs scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS --detailed
python -m scenario_lab.cli refresh-pricing
```

### Resume or branch from an earlier run

```bash
python -m scenario_lab.cli resume scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS
python -m scenario_lab.cli resume scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS --turns 12

python -m scenario_lab.cli branch scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS --from-turn 4
python -m scenario_lab.cli branch scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS --from-turn 4 --modify-metric unemployment=12
```

`resume` continues the same run. `branch` creates a new run starting from a previous turn, which is useful for "what if" analysis.

### Compare two saved runs

```bash
python -m scenario_lab.cli compare-runs scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS-01
python -m scenario_lab.cli compare-runs path/to/baseline-run path/to/candidate-run --fail-on-diff
```

`compare-runs` highlights differences in final metrics, per-turn metrics, occurred events, rules versions, and total cost. `--fail-on-diff` makes it suitable for regression checks in scripts or CI.

### Validate a saved run's integrity

```bash
python -m scenario_lab.cli check-run-integrity scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS
python -m scenario_lab.cli check-run-integrity tests/fixtures/regression/pairwise/run-baseline
python -m scenario_lab.cli check-run-integrity scenarios/sweden-ai-2030 --max-runs 5
```

`check-run-integrity` performs strict structural validation of saved runs: required files, JSON readability, turn numbering, summary/history consistency, and alignment between `summary.json` and persisted turn metrics. You can point it at a single run, a `runs/` directory, or a whole scenario directory.

### Check a regression manifest

```bash
python -m scenario_lab.cli check-regressions regressions.yaml
python -m scenario_lab.cli check-regressions regressions.yaml --fail-on-diff
python -m scenario_lab.cli check-regressions tests/fixtures/regression/pairwise-regressions.yaml
python -m scenario_lab.cli check-regressions scenarios/sweden-ai-2030
```

`check-regressions` runs one or more YAML manifests of saved-run comparisons and produces a summary report for each suite. You can pass either a manifest file or a scenario directory; when given a scenario directory, it auto-discovers pairwise manifests under `regressions/`.

### Compare distributions across sets of runs

```bash
python -m scenario_lab.cli compare-distributions distributions.yaml
python -m scenario_lab.cli compare-distributions tests/fixtures/regression/distribution-comparison.yaml
python -m scenario_lab.cli compare-distributions scenarios/ai-safety-race
```

`compare-distributions` compares sets of saved runs and reports shifts in final metric distributions, occurred-event rates, run status mix, turn counts, and cost distributions. You can pass either a manifest file or a scenario directory; when given a scenario directory, it auto-discovers distribution manifests under `regressions/`. This is intended for behavioral analysis across multiple runs rather than binary pass/fail on a single trajectory.

Concrete scenario-local examples are included in:

- `scenarios/sweden-ai-2030/regressions/`
- `scenarios/ai-safety-race/regressions/`

### Run a combined quality check

```bash
python -m scenario_lab.cli quality-check scenarios/sweden-ai-2030 --max-runs 5
python -m scenario_lab.cli quality-check scenarios/ai-safety-race --fail-on-diff
```

`quality-check` combines run integrity checks with any auto-discovered pairwise regression and distribution manifests for a scenario. By default it fails on structural errors; `--fail-on-diff` additionally makes pairwise regression differences fail the command.

### Run many scenarios in parallel

```bash
python -m scenario_lab.cli batch-run scenarios/sweden-ai-2030 --repeat 10 --max-concurrency 4
python -m scenario_lab.cli batch-run scenarios/sweden-ai-2030 --variants --max-concurrency 4
python -m scenario_lab.cli batch-run scenarios/sweden-ai-2030/variants/quick-test.yaml scenarios/sweden-ai-2030/variants/high-adoption.yaml --max-concurrency 2
```

Use `--repeat` when you want to run the same scenario multiple times. Use `--variants` when you want to expand a scenario directory to all YAML files in `variants/`.

`batch-run` launches multiple isolated child processes and limits concurrency with `--max-concurrency`, which is safer than starting many foreground runs manually. In an interactive terminal it shows an inline batch dashboard with one row per job, including current turn, current activity, and the latest warning.

### Resume many incomplete runs in parallel

```bash
python -m scenario_lab.cli batch-resume scenarios/sweden-ai-2030 --max-concurrency 4
python -m scenario_lab.cli batch-resume scenarios/sweden-ai-2030/runs --max-concurrency 4 --turns 10
```

`batch-resume` discovers incomplete `run-*` directories and resumes them in parallel. You can target a specific run directory, a `runs/` directory, or a scenario directory. In an interactive terminal it uses the same inline batch dashboard as `batch-run`.

### Calibrate from existing runs

```bash
python -m scenario_lab.cli calibrate scenarios/sweden-ai-2030
python -m scenario_lab.cli calibrate scenarios/sweden-ai-2030 --max-runs 10
```

This analyzes saved runs without making new API calls.

### Audit configured models

```bash
python -m scenario_lab.cli audit-models
python -m scenario_lab.cli audit-models scenarios/sweden-ai-2030
python -m scenario_lab.cli audit-models scenarios/sweden-ai-2030 --json
```

This helps catch stale or poor model choices before they quietly affect run quality or cost.

### Generate a visualization

```bash
python -m scenario_lab.cli visualize scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS
```

This command requires `plotly`.

## What a Run Produces

Each run is saved in a timestamped directory:

```text
scenarios/<scenario>/runs/run-YYYYMMDD-HHMMSS/
├── config.json
├── summary.json
├── costs.json
└── turn-XX/
    ├── 1-events.json
    ├── 2-actors/
    ├── 3-metric-rules.md
    ├── 3-metric-rules-metadata.json
    ├── 4-metrics.json
    ├── 4-world-state.md
    ├── 5-constitutional-check.json   # if the scenario uses a constitution
    ├── 5-notepad.md
    └── 6-historical-summary.md
```

If two runs start in the same second, Scenario Lab now adds a numeric suffix instead of reusing the same directory (for example `run-YYYYMMDD-HHMMSS-01`).

Batch commands also write per-job logs under `scenarios/<scenario>/runs/batch-logs/`.

This structure is one of the main strengths of the project: you can inspect intermediate artifacts instead of treating the simulation as a black box.

## Scenario Structure

A scenario usually lives in its own directory under `scenarios/` and includes:

```text
scenarios/my-scenario/
├── scenario.yaml
├── metrics.md
├── metric-rules.md
├── events.md
├── constitution.md           # optional
├── system-prompts/           # optional
├── user-prompts/             # optional
├── background/
│   ├── context.md
│   └── actors/
│       ├── actor-a.md
│       └── actor-b.md
└── variants/                 # optional
```

At a high level:

- `scenario.yaml` defines time scale, turn count, actors, models, and general configuration
- `metrics.md` defines the tracked metrics and their ranges
- `metric-rules.md` defines the starting quantitative rules of the world
- `events.md` defines external events and their trigger logic
- `background/` provides the contextual material the models use
- `constitution.md` adds hard plausibility constraints when needed

## Creating New Scenarios

The recommended workflow is to build new scenarios together with a terminal-based AI coding agent (for example Claude Code, OpenAI Codex, or Gemini CLI), then iterate based on test runs.

Use the docs as separate sources of truth:

- [docs/SCENARIO_CREATION_WITH_AGENT.md](docs/SCENARIO_CREATION_WITH_AGENT.md) (process/workflow)
- [docs/SCENARIO_TECHNICAL_REFERENCE.md](docs/SCENARIO_TECHNICAL_REFERENCE.md) (technical format/specification)
- [docs/REGRESSION_TESTING.md](docs/REGRESSION_TESTING.md) (saved-run regression workflow)

In short:

1. Create a scenario directory (optionally with `source-material/` for background input).
2. Ask the agent to build the scenario in that directory.
3. Let the agent interview you for missing requirements, draft files, and run validation.
4. Run short simulations, review outcomes, and iterate.

## Included Example Scenario

The main example scenario is `scenarios/sweden-ai-2030`.

It explores how AI development, adoption, labor-market pressure, and public sentiment might evolve in Sweden from 2026 onward. It is a good starting point for understanding how Scenario Lab is intended to be used:

- it has multiple actors with different incentives
- it includes exogenous events
- it tracks both technical and social metrics
- it is rich enough for analysis, but still practical to run repeatedly

If you want to understand the project quickly, this is the best place to start.

## Reading Results

The most useful way to work with Scenario Lab is usually:

1. Run the same scenario multiple times.
2. Compare the trajectories in `summary.json`.
3. Inspect the turn folders where runs diverge.
4. Look at the events, rule changes, and narratives that caused the divergence.

This is where the framework becomes valuable: it does not just generate futures, it preserves the causal chain that led to them.

## Contributing and Further Documentation

The main architecture document is:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

That document is the canonical reference for how the system is intended to work.

Useful places to look next:

- `scenarios/` for example scenarios
- `templates/` for prompt templates
- `tests/` for automated checks and evals

## Security

Scenario Lab uses a few simple but important safety measures:

- sandboxed Jinja2 template rendering
- safe YAML loading
- path validation for scenario inheritance
- API keys loaded from environment variables
- a safe expression evaluator instead of `eval()`

## License

Apache-2.0
