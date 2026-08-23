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

If the user is starting from a question or a topic rather than from source
material they already have, run the `frame-scenario` skill first. It settles
the research question and builds the information bank this skill drafts from.

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

0. Check for a `frame-scenario` handoff: `<scenario>/research-question.md`
   and `<scenario>/source-material/INDEX.md`. If both exist, read them first
   – the question, frame, and known gaps are already settled, and the index
   tells you what each file covers and how far to trust it.
1. Identify inputs: user description, files in `<scenario>/source-material/`,
   and any URLs the user provided (fetch them; save extracted text summaries
   to `source-material/` so the scenario is reproducible without the link).
2. Read everything. Build a working picture of: the system being simulated,
   candidate actors and their incentives, quantitative dimensions the material
   tracks or implies, key uncertainties and turning points, time frame.
3. Note explicitly what the material does NOT answer.

## Phase 2: Framing Checkpoint (required – do not draft before this)

**Skip this phase if `research-question.md` exists and records an approved
question.** The framing decisions were made there; re-asking them wastes the
user's attention and invites drift from what they approved. Instead, confirm
in one line that you are drafting to that frame, and raise anything in the
material that contradicts it. If nothing contradicts it, go straight to
Phase 3.

Otherwise, present to the user, concisely:

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

Where the source material carries provenance tags (`[user]`, `[source: …]`,
`[model]`, `[assumption]`), let them govern how firmly you commit: tagged
`[model]` or `[assumption]` claims belong in `design-notes.md` under
Assumptions, not asserted as fact in `background/context.md`. Carry the
"Known Gaps" section of `source-material/INDEX.md` into design-notes too.

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
   `openrouter:qwen/qwen3-235b-a22b-2507`), consider `rule_evolution.freeze_until_turn: 2`,
   and consider `emergent_events.enabled: true` (the purpose is exploring
   unknown futures) and `llm.probability_samples: 3` for better probabilities.
   Include a `research_questions:` block: copy the entry proposed in
   `research-question.md` if there is one, otherwise derive it from the
   framing checkpoint. Name the metrics and events that bear on each question
   – `validate` checks they exist, and `synthesize` uses them to answer the
   question with evidence rather than impressions. A scenario with no declared
   questions can still be synthesized, but only generically.
7. `constitution.md` – only if the domain has hard plausibility constraints
8. `design-notes.md` – central question, key design decisions, assumptions,
   weak spots, ideas deliberately left out

## Constraint Language (applies to actor goals and scenario rules alike)

Precision comes from **scope, not from stacked conditions**. A goal, preference,
or constraint is precise when a model can rule on edge cases without
interpreting: it names what action, by whom, under what kind of arrangement it
covers. "Will not support any government containing V" reads precise but is
not – "containing" collapses cabinet membership, formal agreements, and
external voting support into one word, and two models read it in opposite
directions, flipping the headline result (see
`scenarios/swedish-government-formation-2026/design-notes.md`, "Open
Question"). The failure was invisible in the prose and only surfaced in
behavior.

The wrong fix is piling qualifiers into the sentence until it covers every
case – that recreates the Rule Economy failure mode inside a single
formulation, and reading errors scale with length. The right fix is a short
scope-explicit statement, with the remaining edge cases resolved as recorded
rulings in the constraint ledger (Phase 3b), not as extra clauses. Keep the
verbatim source quote next to the operational statement: paraphrase is where
ambiguity enters, because a summary word can silently widen or narrow scope.

## Phase 3b: Constraint Interrogation (the ledger)

The outcome distribution is usually more sensitive to how a handful of
constraints are worded than to anything the ensemble randomizes. Find those
formulations before spending run money – a few model calls here are cheap
against a batch of runs conditioned on a misreading.

1. **Enumerate** the load-bearing constraints and goals: every "rules out /
   demands / will not accept / must have" across actor files, context, and
   constitution.
2. **Generate edge cases** for each – 3-5 concrete situations the simulation
   could plausibly produce, sitting near the constraint's boundary (external
   support vs. cabinet seat, budget cooperation vs. formal agreement, a
   one-off vote vs. a standing arrangement).
3. **Interrogate in two independent tracks** – two different models, or two
   independently prompted passes: each rules on every edge case as the actor
   would, from the drafted text alone. Compare *rulings, not prose*: two
   drafts routinely agree on wording while diverging on interpretation.
4. **Divergence between tracks means the text underdetermines behavior.**
   Resolve it by researching what the real actor has actually said – never by
   picking the reading you find more plausible. Agreement is weaker evidence
   than it looks (both tracks can share a misreading), so spot-check rulings
   against the verbatim quotes.
5. **Write `<scenario>/constraint-ledger.md`**: one entry per constraint –
   the operational statement, the verbatim source quote with provenance tag,
   the edge-case rulings, and each ruling marked **settled by source**,
   **settled by research**, or **open**.
6. **"Open" is a finding, not a failure.** An edge case with no real-world
   answer (the actor genuinely has not decided) is live uncertainty: model it
   as an event or a branch dimension of the ensemble, and report results
   conditional on it. Never silently condition the whole ensemble on one
   reading of an open ruling.
7. **Fold settled rulings back** into the actor files and context so no
   downstream model has to interpret the original formulation again.

## Rule Economy (check at every iteration)

Rules and constraints accumulate. Each one is added to stop a specific drift you
just watched happen, which makes every individual addition feel justified — and
the set as a whole grows past what a model can apply consistently. The failure
mode then changes character: early runs fail because nothing drives the process,
later runs fail because the model *misreads* a rule. Reading errors scale with
how much there is to read.

Watch for these signatures, and treat any of them as a sign to consolidate
rather than extend:

- **A rule that exists to counteract another rule.** "Metric X is capped at 50"
  plus "except when Y, in which case the cap does not apply" is one idea written
  as two rules. Replace both with a single statement of what the metric *means*,
  and let the exception fall out of it.
- **A clarification added because a rule was misapplied.** If you find yourself
  writing "note that this does not mean...", the original rule was pointing at
  the wrong thing.
- **Unresolved violations rising.** When `max_attempts_reached` starts appearing,
  the model cannot satisfy the set even when told exactly what is wrong. That is
  over-constraint or mutual conflict, not carelessness.
- **A rule that never fires.** If no run ever violates it and no narrative ever
  cites it, it is dead text taking up attention.

Two structural habits prevent most of this:

1. **Separate invariants from modelling choices.** Invariants are facts of the
   world — arithmetic, law, physics. They are short, they never conflict, and
   they almost never need revision. Modelling choices are your decisions about
   how a metric should behave. Both may live in `constitution.md`, but the
   accretion happens entirely in the second group, so audit it separately and
   hold it to a much smaller budget.
2. **Put mechanical limits on the metric, not in prose.** A per-turn rate limit,
   a floor, a ceiling — these belong in `metrics.md` as properties of the metric
   where they apply uniformly, not as a numbered constraint that covers whichever
   metrics you happened to be thinking about. A constraint written for one metric
   silently leaves its neighbours unbounded.

When a constraint set passes roughly a dozen entries, stop and ask what single
underlying statement three of them are approximating. It is usually there.

## Phase 4: Review Checkpoint

1. Run `python -m scenario_lab.cli validate scenarios/<name>` – fix errors.
2. Run `python -m scenario_lab.cli describe scenarios/<name>` and show the
   output to the user (this is the at-a-glance overview).
3. Run `python -m scenario_lab.cli estimate scenarios/<name>` and report cost.
4. Summarize the assumptions from design-notes.md.
5. Present `constraint-ledger.md`, leading with the open rulings and how each
   will be handled (event, branch dimension, or explicit limitation). The
   ledger – not the prose files – is the reviewable artifact: it is where a
   domain expert can say "no, that actor has never said that" at the
   granularity where errors flip results. When the scenario is used for real
   decisions, expert sign-off on the ledger is the gate before any runs are
   paid for.

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
- The rule set is still small enough to be applied consistently — see Rule
  Economy above, and check the constitutional-check artifacts for unresolved
  violations, which are the earliest sign that it is not

## Phase 6: Handoff

Report to the user: what was built, the describe overview, smoke-test verdict,
remaining weak spots, and the recommended next step. That next step is
normally:

1. `batch-run scenarios/<name> --repeat 10` with cheap models
2. `synthesize scenarios/<name> --dry-run` to see the cost shape
3. `synthesize scenarios/<name>` for the answer, which will address the
   declared research questions explicitly

`ensemble` remains useful alongside it for the raw distributions, and costs
nothing. Update design-notes.md to match the final state.
