---
name: create-scenario
description: >
  Guided pipeline for creating a new Scenario Lab scenario from incomplete
  descriptions and source material (files, URLs, notes). Automates ingest,
  extraction, drafting, validation, and smoke testing, with explicit human
  checkpoints for decisions only the user can make. Triggers: "create a
  scenario", "build a scenario from", "new scenario based on", "skapa ett
  scenario", "bygg ett scenario utifrån", "gör om X till ett scenario".
---

# Create Scenario: From Source Material to Validated Draft

You are building a Scenario Lab scenario. Your job is to automate everything
that can be automated, ask the user only what you genuinely cannot decide or
find, and show what you created in a reviewable form at each checkpoint.

Contracts and process background (read before drafting, do not duplicate here):

- `docs/SCENARIO_TECHNICAL_REFERENCE.md` – file formats and validation contract
- `docs/SCENARIO_CREATION_WITH_AGENT.md` – process rationale and interview gate
- `scenarios/sweden-ai-2030/` – reference example of a complete scenario

## Ask-When-Needed Rules

Apply these throughout all phases:

- **Ask** when the answer materially shapes the scenario AND cannot be found
  in the source material: the central question, time frame, metric selection,
  which uncertainties matter, success criteria.
- **Default and log** when a reasonable choice exists: naming details, metric
  ranges with obvious bounds, event probability first-guesses, model choices
  (default to cheap models for drafts). Record every such assumption in
  `<scenario>/design-notes.md` under an "Assumptions" heading.
- **Never silently invent** facts about the real world that the source
  material contradicts or does not support. Flag weak spots in design-notes.
- Batch questions: at most one focused round of questions per checkpoint,
  not a drip of single questions.

## Phase 1: Ingest

1. Identify inputs: user description, files in `<scenario>/source-material/`,
   and any URLs the user provided (fetch them; save extracted text summaries
   to `source-material/` so the scenario is reproducible without the link).
2. Read everything. Build a working picture of: the system being simulated,
   candidate actors and their incentives, quantitative dimensions the material
   tracks or implies, key uncertainties and turning points, time frame.
3. Note explicitly what the material does NOT answer.

## Phase 2: Framing Checkpoint (required – do not draft before this)

Present to the user, concisely:

- **The central question** the scenario should explore (your proposal, 1-2
  sentences). This drives every other choice.
- **Proposed frame:** time scale and horizon, 3-6 metrics with rough ranges,
  3-6 actors, the main uncertainties to make endogenous (events) vs. fixed
  background assumptions.
- **Your open questions** – only the ones matching the ask-when-needed rules.

For "alternative futures from an existing narrative" tasks, the default
approach is: model the *starting state and driving forces* from the source
material, then let simulation runs explore where the world can go – do not
hard-code the source narrative's own timeline as the expected outcome. The
narrative's turning points become candidate *events* with probabilities, not
scripted certainties.

Wait for answers/approval before Phase 3.

## Phase 3: Draft

Draft in this order (each file informs the next):

1. `background/context.md` – world state at start, grounded in source material
2. `metrics.md` – with reference points for interpretability (format: see
   technical reference; reference points make GM updates much better)
3. `background/actors/<id>.md` – one per actor: incentives, resources,
   behavioral tendencies; conflicting interests between actors are essential
4. `events.md` – exogenous uncertainties; conditions + probabilities; prefer
   `can_repeat: false` for structural shifts
5. `metric-rules.md` – starting "physics"; few, clear, quantitative
6. `scenario.yaml` – config; start with cheap models (e.g.
   `openrouter:x-ai/grok-4.1-fast`), consider `rule_evolution.freeze_until_turn: 2`,
   and consider `emergent_events.enabled: true` (the purpose is exploring
   unknown futures) and `llm.probability_samples: 3` for better probabilities
7. `constitution.md` – only if the domain has hard plausibility constraints
8. `design-notes.md` – central question, key design decisions, assumptions,
   weak spots, ideas deliberately left out

## Phase 4: Review Checkpoint

1. Run `python -m scenario_lab.cli validate scenarios/<name>` – fix errors.
2. Run `python -m scenario_lab.cli describe scenarios/<name>` and show the
   output to the user (this is the at-a-glance overview).
3. Run `python -m scenario_lab.cli estimate scenarios/<name>` and report cost.
4. Summarize the assumptions from design-notes.md.

Wait for approval before spending API money in Phase 5.

## Phase 5: Smoke Test and Iterate

1. Run a short cheap simulation:
   `python -m scenario_lab.cli run scenarios/<name> --turns 3`
2. Read the run artifacts (narratives, metrics, event evaluations, rules
   changelog) and assess against the checklist below. Do not just check that
   it ran – check that it behaves.
3. Fix issues (prompts and scenario files first, per repo rules), rerun,
   then present findings + the trajectory to the user.

Smoke-test quality checklist:

- Metrics move plausibly and within intended dynamics (not stuck, not wild)
- Events trigger at sane rates; evaluated probabilities look calibrated
- Actors act in character and in conflict where interests conflict
- Narrative contains friction/setbacks, not smooth consensus
- Rules changelog is grounded, not rewriting physics every turn
- Nothing in the run contradicts source material or the constitution

## Phase 6: Handoff

Report to the user: what was built, the describe overview, smoke-test verdict,
remaining weak spots, and the recommended next step (typically
`batch-run --repeat 10` with cheap models, then `ensemble`). Update
design-notes.md to match the final state.
