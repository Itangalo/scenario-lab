# Instructions for Agents

You are working on **Scenario Lab**, an AI-powered scenario simulation framework.

This file is the repository-specific instruction source for coding agents. Human-facing project overview and usage belong in `README.md`. System design details belong in `docs/ARCHITECTURE.md`.

When helping create a new scenario from scratch, use:

- [docs/SCENARIO_CREATION_WITH_AGENT.md](docs/SCENARIO_CREATION_WITH_AGENT.md) for process/workflow
- [docs/SCENARIO_TECHNICAL_REFERENCE.md](docs/SCENARIO_TECHNICAL_REFERENCE.md) for file format and validation contract

Claude Code has two skills covering this pipeline: `frame-scenario` (rough topic to approved research question, then a provenance-tagged information bank) and `create-scenario` (information bank to validated, smoke-tested scenario files). Start with the former when the user has a question, the latter when they already have material.

## Working on the europe-2032 scenario

When working on the europe-2032 scenario, read [scenarios/europe-2032/ROADMAP.md](scenarios/europe-2032/ROADMAP.md) and [scenarios/europe-2032/story/README.md](scenarios/europe-2032/story/README.md).

## Critical Ground Truth

Before proposing or implementing any change to system behavior, you must read:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

This includes changes to:

- system architecture
- simulation logic
- orchestration behavior
- data models
- prompt structure when it changes how the system works

If your change alters intended behavior, verify it against `docs/ARCHITECTURE.md` and update that document before or during implementation.

## Core Rules (Do Not Break)

1. **Preserve the pure LLM architecture.**
   Do not move scenario logic into Python. Rules, calculations, narrative reasoning, and world evolution belong in prompts and LLM outputs. Python is for orchestration, parsing, validation, persistence, and reporting.

2. **Use the template system for prompt changes.**
   Do not hardcode prompt text in Python when a prompt/template change is the right solution. Default prompt changes belong in `templates/`. Scenario-specific prompt overrides belong inside the relevant scenario directory.

3. **Preserve incremental persistence.**
   Results must be written to disk as the run progresses. Do not redesign flows so data is only saved at the end. Crash resilience and resumability are core properties of the project.

4. **Keep Python-side checks lightweight.**
   Validation, parsers, retries, and guardrails are fine. But do not turn Python into the source of truth for world rules or simulation outcomes.

5. **Keep code changes typed and explicit.**
   Maintain type hints in Python code and prefer clear, minimal orchestration over clever abstractions.

## Project Map

- `scenario_lab/`: core package (loader, orchestrator, LLM client, CLI, output, validators)
- `templates/`: shared prompt templates
- `scenarios/`: scenario definitions, background material, variants, and run outputs
- `tests/`: automated tests
- `tests/evals/event-conditions-flat/`: fast prompt-level event-condition evals
- `tests/evals/llm-event-conditions/`: fuller scenario-based event-condition evals

## Working Defaults

- **Running a scenario:**
  `python -m scenario_lab.cli run scenarios/sweden-ai-2030`

- **Validating before running:**
  `python -m scenario_lab.cli validate scenarios/sweden-ai-2030`

- **Estimating cost:**
  `python -m scenario_lab.cli estimate scenarios/sweden-ai-2030 --turns 10`

- **Auditing model choices:**
  `python -m scenario_lab.cli audit-models`

- **Synthesizing a batch of runs into one answer:**
  `python -m scenario_lab.cli synthesize scenarios/sweden-ai-2030 --dry-run` first (shows how many analysis calls it would make), then without the flag

- **Resuming a run:**
  `python -m scenario_lab.cli resume scenarios/<scenario>/runs/run-YYYYMMDD-HHMMSS`

- **Branching for what-if analysis:**
  `python -m scenario_lab.cli branch scenarios/<scenario>/runs/run-YYYYMMDD-HHMMSS --from-turn N`

## Practical Guidance

1. **Use small, cheap runs while iterating.**
   When testing changes, prefer short runs and inexpensive models when possible. Scale up only after the behavior looks right.

2. **Caffeinate and monitor long runs.**
   When doing runs taking longer than 15 minutes, set a caffeinate to keep the computer awake and launch through `scripts/run-notify.sh LOGFILE -- <command>`: it waits on the child PID, appends a stable `RUN_DONE exit=N` marker to the log, and fires a desktop notification with sound. Poll completion with `grep -q RUN_DONE LOGFILE`, never with sleep+pgrep (which has missed endings repeatedly). If errors occurs, resolve them when reasonably small and then resume, otherwise stop the run.

3. **Treat prompts as first-class implementation.**
   If behavior is wrong, check the prompt and scenario content before adding Python logic.

4. **Use the eval suites when changing event-condition behavior.**
   If you change event-condition prompting, parsing, or evaluation behavior, run the relevant evals in `tests/evals/`.

5. **Do not rely on stale examples.**
   Some historical docs or examples may lag behind the current CLI or current model recommendations. Prefer the current code and `docs/ARCHITECTURE.md` over older phrasing.
