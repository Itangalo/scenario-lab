# Handoff – session of 2026-08-28/30

Twenty-four commits, `855bb9a` through `88f15bb`. Two threads ran through them: a batch of simulations for the Europe 2032 branching story, and a much longer thread that started when that batch turned out to have been running on a prompt nobody had read. By the end the fork itself had moved, and the two batches the session opened with are archived rather than current.

## Read these first

- [scenarios/europe-2032/story/README.md](scenarios/europe-2032/story/README.md) – the tree: its arms, its naming scheme, and how options and paths are made. Rewritten by Johan on 2026-08-30; it no longer carries the batch findings, which is a gap noted below
- [scenarios/europe-2032/story/turn-01/superseded-roads/README.md](scenarios/europe-2032/story/turn-01/superseded-roads/README.md) – why the three turn-1 roads were retired, and the re-draw that moved the fork
- [scenarios/europe-2032/sign-off/](scenarios/europe-2032/sign-off/) – the prompts as actually sent, each block labelled with the file it came from
- [scenarios/europe-2032/runs/archive/pre-priority-bias-2026-08/README.md](scenarios/europe-2032/runs/archive/pre-priority-bias-2026-08/README.md) – why 63 runs were retired and what is still citable in them

## What happened, in the order it mattered

**The acceleration batch ran.** Thirty runs, three roads, turns 2–5, $0.72. Capability ends 5–12 points above the plateau arm and safety 4 below it on every road; sentiment converges on 28 where plateau spread 11 points between roads. The repaired election machinery works: exactly one outcome in all 30 runs and all three reachable.

**Sovereignty did not move, in either arm, on any road.** Two batches now agree. This is the finding to settle before another batch, and most of the mechanics work below was an attempt to find out why.

**Then: `background/actors/eu.md` was mostly not being sent.** `load_actor` reads `## Long description` until the first `###` heading and stops, so 2,619 tokens – the ten measure categories, the rule that the Union cannot see which trajectory it is in – reached no prompt. Two thirty-run batches had run on it. The scenario behaved plausibly because `user-prompts/actor.md` happened to duplicate the operative parts.

That produced the sign-off tooling (`scripts/render_signoff.py`), provenance recording inside `PromptBuilder`, and a required phase in the create-scenario skill. **The loader bug itself is not fixed** – see below.

**Reading the sign-off documents then found the rest:** `background/context.md` was being sent twice in turn 1, the actor was never told how long a turn is, three paragraphs were indented into the prompt as literal whitespace, and the trajectory regime was named by label in eleven places including a rule whose only job was to forbid the Game Master from writing the labels the same prompt had just taught it.

**The measure mechanics were rebuilt three times.** Details below; the short version is that `Lead time:` was decoration – nothing read it, so every measure completed in two turns of priority whatever it declared.

## Where the mechanics landed

A measure now states when it finishes, judged once and copied forward:

```
`under implementation` — InvestAI Gigafactories
    (category 4, costs 3 per turn, started turn 1, finishes on turn 7)
```

- **Cost:** 3 a turn for a large measure, 2 for a small one, plus 1 for the priority. No floor.
- **Discount:** events carry `Cheapens: categories 4 and 5 by 2 for 4 turns`. 31 of 35 events have one. The Game Master reads it off the event record; it is a lookup, not a judgement.
- **Finishing turn:** moves only when the priority pulls it in, neglect pushes it out, or an event does either – and the reason is written into the line.
- **Effect:** nothing in the turn a measure is proposed; a share of the category range judged from how far along it is; full from the turn it finishes.
- **Portfolio:** starts with two inherited programmes, InvestAI Gigafactories and the June 2026 sovereignty package. The Frontier AI Initiative was dropped as dead.
- **No fixed-background block.** It was cut from this scenario on 2026-08-30: the opening is 2026 news rather than standing physics, and a block asserting that it outranks the narrative is right at turn 2 and wrong by turn 12. The mechanism stays in the default templates for scenarios that fix something that genuinely does not move. The cost was measured and accepted – structural facts decay out of the rolling summary because nothing happens to them, and a turn-5 summary retains no mention of ASML, of the compute gap, or of Mistral. Anything that must survive six years belongs in the metric rules or the event catalogue, which are read every turn.

### The lesson that cost the most to learn

Three designs failed before this one, all the same way: they asked the Game Master to carry a number forward and add to it. Fractions drifted, integers got stuck, a measure sat at `work 2 of 10` for four consecutive turns.

**Required, formatted output that the model has to write down is reliable. State it has to remember and update is not.** The `PORTFOLIO CHARGE` line is the proof, twice over: introduced because the capital drain was being skipped entirely, and then in an A/B on one seed – with the line, capital fell 48-39-30-24; without it, 45-43-40-43, the charge simply not applied, the Union ending richer than it started while carrying five unfinished measures. Rule 10 states the cost identically in both.

The same pattern fixed the discount, which failed twice as a judgement call and worked immediately as a lookup against data on the events.

## Open, in the order I would take them

1. **The measure mechanics are rebuilt but never batched.** Finishing turns, flat 3/2 costs and the event-driven discount have been through four-turn smoke tests only. Whether sovereignty now moves is unknown, and it is the question two batches failed to answer.
2. **`Cheapens:` reaches no prompt, so the discount is not the lookup it is described as.** The event loader parses `Condition`, `Probability`, `Can repeat`, `Description` and `Eligible`, and silently discards anything else – so all 31 `Cheapens:` lines are dead text, in the same way `background/actors/eu.md` was dead text. The discount does fire, but the Game Master infers a plausible value from metric rule 10's description of a field it cannot see, which is also why the citation names whichever event fired most recently rather than the one whose window is open. Fix: put `cheapens` on the `Event` model, parse it, and render it wherever events are listed, including the triggered-events block the Game Master receives. Add a validator warning for an unrecognised `**Field:**` in `events.md` while you are there – it would have caught this the moment it was written, and will catch the next one.
3. **Nothing holds the batch findings any more.** The story README was rewritten around the tree and no longer records what the two batches showed: that sovereignty did not move in either arm on any road, that the election machinery was broken and is now repaired, or the measured seed overlap behind the seeds rule. They survive in this file and in the archive README, both of which are session artifacts. They want a calibration note of their own.
4. **A dangling reference.** `story/turn-01/superseded-roads/README.md` says the re-draw finding "is in the story README". It is not – the rewrite dropped it. The finding itself is worth keeping: 20 fresh draws under the current prompt returned 16 category 6 and 4 category 5, and no category 4 at all, so the spread the three roads were selected from no longer exists.
5. **The tree is larger than it looks.** The naming scheme implies 56 turn pieces per arm and 168 across the three, plus 42 options, each built from ten or more simulations. Worth sizing deliberately before building, at roughly seven minutes per turn per run.
6. **`load_actor` still truncates.** Blast radius is five actor files in three scenarios (34 of 39 lose only markup). Repairing it pushes several thousand words into those actors' prompts at once – a deliberate, calibrated change, not a tidy-up.
7. **The sign-off documents are current** as of `run-20260830-185157`, which is after every change in this session. Regenerate after any prompt change: run 2 turns with `--log-llm-io`, then `python scripts/render_signoff.py <run-dir>`. A regeneration is what found the `Cheapens:` defect, four hours after the field was added, and the set before it went stale within the hour – these are snapshots taken at a decision point, not something the repo keeps true.

## Things that will bite you if nobody says them

- **Seeds must be unique per run.** Both existing batches reused 700001–700010 across roads and arms. Measured overlap between two roads at the same seed is 0.625 against 0.210 at different seeds – three roads sharing a seed are substantially the same world.
- **`events.md` prose is not rendered.** `_format_events_list` sends only the parsed per-event fields. The framing sections – the gate mechanism, the election weighting – reach no prompt. Editing them changes nothing.
- **`--max-concurrency` defaults to 4.** A 30-run batch is three waves at that setting. Each turn is 7 sequential LLM calls; a turn takes 4–10 minutes and cannot be parallelised within a run.
- **stdout is block-buffered.** Watch a run through its artifact files, not its log.
- **A rule the model is asked to remember is a rule that will be skipped.** The `PORTFOLIO CHARGE` line proves it twice: introduced because the capital drain was being ignored entirely, then A/B tested on one seed – with the line, capital fell 48-39-30-24; without it, 45-43-40-43 and the charge simply not applied. Metric rule 10 states the cost identically in both.
- **Silent failure is this codebase's characteristic bug.** Truncated actor background, unrendered event prose, dead `Cheapens:` fields, statement proposals lost to a code-span wrapper. None of them errored; all of them looked like working scenarios. Assume anything not visible in a sign-off document is not reaching the model.
- **Johan commits directly on `main`** in this project and does not branch.

## Where turn 1 went

The fork moved from turn 1 to turn 2 on 2026-08-30, and turn 1 became a single fixed opening at `story/turn-01/opening.md` – one pinned actor response, shared by every arm and every reader, with the two inherited programmes already in its portfolio. The three roads that used to fork there are in `turn-01/superseded-roads/`, kept as the provenance of the archived batches and for nothing else. `story/pin-turn-1.py` still builds the turn-1 bases from a pinned response; it now takes one rather than three.

## Untracked and deliberate

`scenarios/forking-futures/archive/` predates this session and was left alone – that scenario is out of scope and its references were removed from europe-2032.
