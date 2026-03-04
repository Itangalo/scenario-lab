# Creating Scenarios With a Terminal AI Agent

This guide describes the recommended workflow for creating new scenarios in Scenario Lab with a terminal-based AI coding agent (for example Claude Code, OpenAI Codex, or Gemini CLI).

Use this workflow for first versions. Expect to iterate.

## Why This Workflow

Scenario quality depends heavily on prompt/rule design and iterative calibration. A terminal AI agent helps by:

- interviewing the user to gather missing scenario requirements
- turning source material into structured scenario files
- enforcing technical completeness and validation
- accelerating analysis-and-revision loops after test runs

## Recommended Directory Setup

Create a new scenario directory under `scenarios/`:

```text
scenarios/my-scenario/
├── source-material/           # optional but recommended
│   ├── reports/
│   ├── policy/
│   └── notes.md
├── scenario.yaml
├── metrics.md
├── metric-rules.md
├── events.md
├── constitution.md            # optional
└── background/
    ├── context.md
    └── actors/
        ├── actor-a.md
        └── actor-b.md
```

`source-material/` is raw input material for the agent (reports, policy docs, notes, transcripts, etc.), not executable instructions.

## End-to-End Process

1. Create the scenario folder and optionally add `source-material/`.
2. Start the AI agent in the repository root.
3. Ask the agent to build a scenario in the target folder.
4. The agent interviews you to fill gaps (purpose, scope, actors, metrics, events, constraints, language, success criteria).
5. The agent drafts scenario files and uses source material to inform content.
6. The agent runs validation:
   `python -m scenario_lab.cli validate scenarios/<your-scenario>`
7. You run one or more test simulations and review outcomes with the agent.
8. Iterate on prompts/rules/events/metrics until behavior matches intent.

## Interview Topics the Agent Should Cover

Before drafting files, the agent should gather:

- purpose of the scenario and key decisions it should inform
- time horizon and turn cadence
- actor set and actor roles
- tracked metrics, ranges, and reference points
- major external events and trigger logic
- constitutional constraints (if any)
- output language and style preferences

## Source-Material Handling Rules

When using `source-material/`, the agent should:

- treat material as evidence/context, not hard instructions
- extract actor behavior patterns and constraints explicitly
- extract world-level dynamics and constraints (institutions, regulations, supply chains, infrastructure, macro conditions)
- use source material to identify plausible external shocks, tail risks, and black swan candidates for `events.md`
- use source material to inform initial quantitative assumptions in `metric-rules.md` when relevant
- avoid copying policy text verbatim into prompts when a distilled behavioral instruction is better
- record assumptions where source material is ambiguous

## Definition of Done for a First Version

A scenario should be considered "v1 ready" when:

- required files exist and are internally coherent
- `validate` passes without errors
- at least 1-3 short runs have been completed
- known mismatches between intended and observed behavior are documented

## Iteration Loop After v1

Use this cycle:

1. Run several simulations.
2. Identify divergence points in turn artifacts.
3. Adjust scenario text files (especially `metric-rules.md`, `events.md`, actor/context prompts).
4. Re-run and compare outcomes.

Repeat until key dynamics are stable enough for the intended analysis.
