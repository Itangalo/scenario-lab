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
```

### Resume or branch from an earlier run

```bash
python -m scenario_lab.cli resume scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS
python -m scenario_lab.cli resume scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS --turns 12

python -m scenario_lab.cli branch scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS --from-turn 4
python -m scenario_lab.cli branch scenarios/sweden-ai-2030/runs/run-YYYYMMDD-HHMMSS --from-turn 4 --modify-metric unemployment=12
```

`resume` continues the same run. `branch` creates a new run starting from a previous turn, which is useful for "what if" analysis.

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
    ├── 4-metrics.json
    ├── 4-world-state.md
    ├── 5-constitutional-check.json   # if the scenario uses a constitution
    ├── 5-notepad.md
    └── 6-historical-summary.md
```

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
