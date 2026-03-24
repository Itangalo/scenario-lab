# Regression Testing with Saved Runs

This document describes the first layer of Scenario Lab's saved-run regression workflow.

The goal is not to replace prompt-level evals or scenario validation. The goal is to make it easier to detect when a code or prompt change causes meaningful changes in previously captured run outputs.

The workflow now has two distinct layers:

- strict run-integrity checks for structural correctness
- artifact and distribution comparisons for behavioral review

## Why This Exists

Scenario Lab already persists rich run artifacts:

- summary history
- per-turn metrics
- per-turn event outputs
- rule versions
- cost reports

That makes saved-run comparison a practical foundation for regression checks.

## Available Commands

### Check One Run's Structural Integrity

```bash
python -m scenario_lab.cli check-run-integrity path/to/run
python -m scenario_lab.cli check-run-integrity path/to/run --json
python -m scenario_lab.cli check-run-integrity tests/fixtures/regression/pairwise/run-baseline
```

This is the hard-failure layer. It checks:

- required files exist
- required JSON files parse correctly
- turn directories are sequential
- actor output directories are present and non-empty
- `summary.json` history matches per-turn `4-metrics.json`
- `summary.json.final_metrics` matches the last saved turn
- optional `costs.json` fields are structurally valid

If this check fails, treat it as a true regression or run-corruption signal.

### Compare Two Runs Directly

```bash
python -m scenario_lab.cli compare-runs path/to/baseline-run path/to/candidate-run
python -m scenario_lab.cli compare-runs path/to/baseline-run path/to/candidate-run --json
python -m scenario_lab.cli compare-runs path/to/baseline-run path/to/candidate-run --fail-on-diff
```

This command compares:

- final metrics
- per-turn metrics
- occurred events
- per-turn event differences
- rules versions
- total cost

`--fail-on-diff` returns exit code `1` when any difference is detected, which makes the command usable in scripts or CI.

This command is best used for observability and review. In a stochastic system like Scenario Lab, a difference between two single runs is not automatically a regression.

### Run a Regression Manifest

```bash
python -m scenario_lab.cli check-regressions regressions.yaml
python -m scenario_lab.cli check-regressions regressions.yaml --json
python -m scenario_lab.cli check-regressions regressions.yaml --fail-on-diff
python -m scenario_lab.cli check-regressions tests/fixtures/regression/pairwise-regressions.yaml
python -m scenario_lab.cli check-regressions scenarios/sweden-ai-2030
```

This command runs one or more suites of saved-run comparisons and prints one summary report per manifest.

You can pass either:

- a manifest file
- a scenario directory with `regressions/`

When given a scenario directory, the command auto-discovers pairwise manifests from `regressions/`.

### Compare Distributions Across Run Sets

```bash
python -m scenario_lab.cli compare-distributions distributions.yaml
python -m scenario_lab.cli compare-distributions distributions.yaml --json
python -m scenario_lab.cli compare-distributions tests/fixtures/regression/distribution-comparison.yaml
python -m scenario_lab.cli compare-distributions scenarios/ai-safety-race
```

This command compares two sets of saved runs at the distribution level. It is the preferred tool for behavioral change detection when single-run variation is expected.

You can pass either:

- a manifest file
- a scenario directory with `regressions/`

When given a scenario directory, the command auto-discovers distribution manifests from `regressions/`.

It summarizes:

- final metric distributions
- occurred-event rates
- run status counts
- turn-count distributions
- cost distributions

## Manifest Format

Minimal example:

```yaml
comparisons:
  - label: sweden-quick
    baseline: scenarios/sweden-ai-2030/runs/run-20260324-101500
    candidate: scenarios/sweden-ai-2030/runs/run-20260324-102200
```

Multiple comparisons:

```yaml
comparisons:
  - label: sweden-quick
    baseline: fixtures/sweden/run-baseline
    candidate: fixtures/sweden/run-candidate

  - label: safety-race-branch
    baseline: fixtures/ai-safety-race/run-branch-a
    candidate: fixtures/ai-safety-race/run-branch-b
```

Rules:

- `comparisons` is required and must be a non-empty list
- each comparison must include:
  - `label`
  - `baseline`
  - `candidate`
- `baseline` and `candidate` must point to saved run directories
- relative paths are resolved relative to the manifest file location

The repository includes a working example at:

- `tests/fixtures/regression/pairwise-regressions.yaml`
- `scenarios/sweden-ai-2030/regressions/pairwise-example.yaml`
- `scenarios/ai-safety-race/regressions/pairwise-example.yaml`

## Distribution Manifest Format

Minimal example:

```yaml
comparisons:
  - label: sweden-distribution
    baseline:
      glob: fixtures/sweden/baseline/run-*
    candidate:
      glob: fixtures/sweden/candidate/run-*
```

Explicit run lists are also supported:

```yaml
comparisons:
  - label: branch-study
    baseline:
      runs:
        - fixtures/branch-study/baseline/run-a
        - fixtures/branch-study/baseline/run-b
    candidate:
      runs:
        - fixtures/branch-study/candidate/run-a
        - fixtures/branch-study/candidate/run-b
```

Rules:

- `comparisons` is required and must be a non-empty list
- each comparison must include:
  - `label`
  - `baseline`
  - `candidate`
- each `baseline`/`candidate` block must define either:
  - `glob`
  - `runs`
- relative paths and globs are resolved relative to the manifest file location

The repository includes a working example at:

- `tests/fixtures/regression/distribution-comparison.yaml`
- `scenarios/sweden-ai-2030/regressions/distribution-example.yaml`
- `scenarios/ai-safety-race/regressions/distribution-example.yaml`

## Suggested Workflow

1. Capture one or more reference runs you care about.
2. Store them somewhere stable and inspectable.
3. Create a regression manifest that points to those runs.
4. Run `check-run-integrity` on saved fixtures when you need hard validation.
5. After changing prompts, parsers, orchestration, or output logic, run `check-regressions`.
6. When the question is behavioral rather than structural, run `compare-distributions`.
7. Review differences before deciding whether they are intended improvements or regressions.

## What Counts as a Good Regression Fixture

Use saved runs that are:

- cheap enough to keep rerunning when needed
- representative of important scenario behaviors
- stable enough that differences are meaningful
- small enough to inspect manually when a diff appears

In practice, short runs and branch-point fixtures are often better than long expensive runs for this purpose.

## Current Scope

This workflow is intentionally modest. It currently compares saved artifacts that already exist on disk. It does not yet:

- define metric tolerances
- auto-generate baseline fixtures
- replace scenario-level eval datasets

It also deliberately does not treat a single surprising run as a binary regression. The intended split is:

- structural breakage: hard failure
- single-run differences: review signal
- multi-run distribution shifts: behavioral signal

Those are natural next steps, but this first layer already provides practical value by making artifact-level diffs much easier to run and review.
