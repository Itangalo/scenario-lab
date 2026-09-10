# Europe 2032 – roadmap to the story

The goal is an interactive story: a reader takes the EU through 2026–2032, not knowing which of three AI trajectories they are on, choosing three times, and reaching one of twenty-four endings. `story/README.md` defines the tree and the naming. This file is the plan for getting there, and it is the document to read first in a new session. It is complemented with `design-notes.md`, used to remember decisions and important results.

This document keeps track of the work. Update it when the work moves along; it should always say where we are and what the next steps are.

## Phase 1 – the scenario stops moving

The gate for this phase is that the physics works well enough to have credible runs, on all three arms.

- [X] All metrics should evolve in a credible way. This means, for example:
  - For ai_capability and ai_safety: In the Acceleracion arm (A), the former will often hit the ceiling and the latter will often crash. In the other arms, it is more balanced.
  - For openweight_capability: This should trail ai_capability in basically all runs, all arms. For the Plateau arm (P), it should almost match ai_capability in the final rounds.
  - For eu_ai_sovereignty, eu_political_capital and public_sentiment: These metric should struggle. Some successes and some alarmingly low. Lower end on the A arm.
- [X] **Events are triggered roughly correctly, and their effects are managed roughly correctly.** The rule-5 decision was taken: the third term (events that take away or secure access to capacity) was added, and sovereignty moves with real spread (0–32 across arms) instead of sitting stuck. The 2028 election family holds exactly-one at turn 5 across every batch measured (15/15, 18/18, 15/15, and 60/60 on the rebuilt Stage-1 batch). See `design-notes.md`.
- [X] **The event list is fairly balanced.** All 35 events fire at least once across the 32-run corpus; per-listing fire rates run 1–16% and every event touches at least 5% of runs. Nothing in the catalogue is dead and nothing is scenery. Measured mostly before the open-weight fix, so the incident events gated at `openweight_capability` 55 and 65 were rolled with those branches shut — their true rates are higher than the table says, which does not change the conclusion.
- [X] **A turn that drops a metric is caught.** One run of 2026-09-03 omitted `openweight_capability` from turn 1's JSON; the old value was carried forward and the run completed clean. The metrics step now compares the parsed JSON against the scenario's metric ids, asks once for the omitted ones by name, and writes the outcome to `turn-XX/4-metrics-metadata.json` either way; anything still missing is filled from the value the run actually uses, so no artefact carries an absent key. The referee's correction step is guarded the same way, since a correction that drops a metric reverts it to last turn's value.

Deliberately *not* gates: Exact arithmetic correctness, rare occasions of mechanics malfunctioning (less than one in ten).

**Open 2026-09-03, closing 2026-09-04.** The soften branches (rate trims, resilience start, two dark-gated positives, two-step rule-10 trap) measured clean: arms separate, all four sovereignty-vs-capital quadrants populated, floors discriminate except agency — reset to ≥12, applied or not at Johan's call. Two known imperfections travel forward rather than block: plateau openweight trails by ~11–13 instead of "almost matching", and fire frequency ignores rate cuts (2.43→2.49 across three rounds — the events step compensates, recorded as listing behavior, not a defect to chase). US posture timing was corrected along the way (result turn 5, policies turn 6; rule 8 owns the line, prompt-gated per turn after two failed rounds taught that prohibitions don't hold). Full account in `design-notes.md`.

## Phase 2 – clear the ground (done 2026-09-04)

- **Archive, don't delete.** Before the wipe, every batch's findings were written into `design-notes.md` — including the 15-run emergent-examples batch, which was wiped before its keep-value was recognized and partially recovered from the dashboard page (probabilities, transcripts and costs irrecoverable; the lesson is archive-before-wipe, not apology-after). `runs/` was otherwise wiped (247 MB freed).
- **`story/turn-01/` did not survive the check.** The ten-draw check failed decisively (2/10 category-6 vs recorded 28/30) after repeated actor-prompt changes. Replaced from a fresh 30-draw pool (`turn-01/pool-20260904/`, split cat4 12 / cat5 10 / cat1 5 / cat3 2 / cat6 1): `option-02-1.md` is build, `option-02-2.md` is know-and-constrain, both straight picks. Reader choice is now build vs know-and-constrain.
- **Pinned turn-1 base runs regenerated**, six of them (both options × three arms, fresh seeds, `run-pin-{A,V,P}-o{1,2}`) — the roadmap said per arm, but each branch needs its own foundation since resolution differs per arm and response per option. Verified verbatim actor output and arm-ordered capability.

## Phase 3 – the runs

Two independent bodies of work. Either order; 3a is one command and a wait, 3b needs judgement between stages.

### 3a – the statistics batch

50 runs per arm, 13 turns, 150 runs total. Serves the general statistics and doubles as the final proof that the scenario behaves. (Scaled up from 20/arm 2026-09-07: 60 runs were judged too thin a comparison base for 24 story endings.)

- **1 950 turn-executions, about $13.50, about 7–9 hours** at 8–12 concurrent. Measured basis ($0.0069/turn-execution across the Stage 2–3 batches); the CLI estimator says $0.23/run ($34.50 total) but consistently quotes ~2.5× measured spend — treat that as the ceiling.
- One command per arm (`batch-run --repeat 50` on each variant), fresh random seeds by default, no human input once launched.
- **Batch launched overnight 2026-09-08** as a single `batch-run scenarios/europe-2032 --variants --repeat 50 --max-concurrency 10` (150 jobs). Separation from the story-block runs is by provenance-only initial-state draws: every job carries `notes: "batch=stats-20260908; draw=NNN"` in its `config.json`, so `--filter batch=stats-20260908` isolates the batch and `--group-by scenario` splits the arms. Draws, launcher, AC-power gate, and 20-minute monitor live in `stats-batch-20260908/` (logs: `batch.log`, `progress.log`, `watcher.log`). Commitments kept (story comparison stays apples-to-apples).

### 3b – the story tree

42 blocks of four turns, each block ten simulations; the path is the first run per block unless a fault promotes rep 2 (A11: sentiment skipped rule-7 incident penalties; P11: openweight frozen by GM inertia — both in `story/README.md`). Option pools of ten actor-only draws, extended where N=10 shows no honest split. Three stages, because each stage's branches start from the previous stage's chosen path.

**Stage 1 (turns 2–5) batch complete 2026-09-05.** Pilot-first procedure after a tainted 60-run batch: an early-election prompt bug (Jinja if/else with no neither-case) had 48 runs declaring winners in turns 2–4. Fixed three-way, render-verified per turn. Rebuilt whole overnight (60 runs, 10 per branch, committed in git): exactly-one holds 60/60 at turn 5, zero named postures before turn 6, first run per branch selected as the story path (`story/README.md` branch log, prose in `story/stage-1/`). Procedure, not just caution: this is the second batch lost to verify-after-scale.

**Stage 2 (turns 6–9) batch complete 2026-09-06.** 12 blocks × 10 reps (120 runs) via new `story/pin-turn.py`: each block branches its Stage-1 path run at turn 5, pins turn-6 events (branch fixture) and actor (chosen option sample), runs turns 6–9 normally. Pilot-verified (events pinned, actor verbatim, posture activates turn 6). Sequential launch proved too slow (~10 min/rep); 8-wide xargs finished the batch. Manifest in `story/stage-2-blocks.json`; path per block is the first run, except A11 and P11 where documented faults promoted rep 2 (see `story/README.md`).

**Stage 3 (turns 10–13) batch complete 2026-09-07.** 24 blocks × 10 reps (240 runs) via `pin-turn.py`: each branches its Stage-2 path at turn 9, pins turn-10 events (fixture, fresh `--seed` each per seed rule) and actor (chosen option), runs turns 10–13 normally. Same 8-wide procedure with 20-minute report chunks; resume-safe task regen throughout, 92 killed-mid-run partials removed before commit. One genuine rep failure (timeout SIGTERM, rerun clean) and one timeout-killed final rep finished via plain `resume` (turns 10–12 pinned artifacts intact, only turn 13 drawn normally). Manifest in `story/stage-3-blocks.json`; path per block is the first run.

Reading prose for all 24 paths in `story/stage-3/`, machine-verified; turn 13 framed as where the scenario ends, not a finale. Manifests in `story/stage-1-blocks.json`, `story/stage-2-blocks.json`, `story/stage-3-blocks.json`; reading prose in `story/stage-1/`, `story/stage-2/`, `story/stage-3/` with two-year commitments up top.

| stage | branches | turn-executions | cost (est. → actual) | wall clock |
|---|---|---|---|---|
| turns 2–5 | 6 | 240 | $1.66 → **$1.17** | 1.2 h |
| turns 6–9 | 12 | 480 | $3.31 → **$2.51** | 2.4 h |
| turns 10–13 | 24 | 960 | $6.62 → **$4.95** | 4.7 h |
| **total** | **42 blocks** | **1 680** | **$11.59 → $8.63** | **8.2 h** |

Plus actor-only draws for the option pools: 6 turn-6 pools (10 each; A2/V2/P2 extended to 30) + 12 turn-10 pools (10 each; A12/V11/P11/P12/P22 extended to 20) — 290 samples, **$0.21** actual against about $0.22 estimated for the originally planned 180.

**Between stages sits a human decision** that cannot be automated: reading a pool of ten draws and choosing the two options that represent it, or saying plainly that the draws do not fall into two groups. `story/README.md` is explicit that inventing a split is the wrong answer, and the turn-1 pool is the worked example — 28 of 30 in one category, so the second option is presented as the minority draw it is.

**Whole programme: about $17 estimated, $8.84 measured (batches $8.63 + pools $0.21), and roughly 12 hours of wall clock including one paused evening.** Cheap enough that the constraint is attention, not credits: every stage of 3b needs someone to look at the pools.

## Phase 4 – the story (open)

The runs are evidence. This phase is the thing a reader walks through, and it is where the work now is. `story/README.md` holds the tree layout and the writing rules; this section holds the state, the tools and the order of work.

**What exists.**

- `story/tree.json` — the editorial source of truth: which run each of the 42 blocks follows, which option leads into it, and how honest each choice's split is. Generated from the branch-log tables in `story/README.md` and verified against every run's `config.json` before it was written.
- `story/extract_tree.py` — builds `story/tree/`, one directory per node, 169 turns and 38 choices. Each holds a machine-extracted `data.json` and a hand-written `narrative.md` (or `choice.md`). It never overwrites prose whose front matter says `status: written`; `data.json` is derived and always rewritten, so it is safe to re-run at any time.
- `story/check_tree.py` — structure, numbers, events, arm leakage, in-world framing, calendar time, the 2028 US result, provenance. `--self-test` plants a fault of each kind and fails if any goes uncaught; run it before believing anything the checker says. `--continuity` walks all 24 reader paths and reports threads referenced before they have happened, and events that fired in a written turn and never reached the page.
- `scripts/build_story.py` — the reader: one self-contained page built from the written nodes, stopping wherever the writing has got to. Output `story.html`, gitignored and regenerated. `story/preamble.md` and `story/postamble.md` are authored text, edited like any other prose rather than living in the generator.

**State, 2026-09-08.** 39 of 207 nodes written: turn 1, both turn-1 options, the 24 turns of 2027–2028, and the twelve turn-6 choice pages. Both checkers clean. Remaining: the 48 turns of 2029–2030, the 24 turn-10 choice pages, and the 96 turns of 2031–2032. A draft of what exists is published as a private artifact for readability feedback.

**Order of work.** Forward, stage by stage, because a turn has to know what the reader has already been told: Stage 2's 48 turns, then the 24 turn-10 choices, then Stage 3's 96 turns. Within a stage, one block at a time.

**This phase costs no API credit.** The simulator's job ended when the runs finished. The prose is written by hand; the only machine steps are extraction, checking and building the page. The constraint is attention, not credits.

**Open questions, none blocking.**

- **The event list has not been re-read since the store redesign.** Standing conditions (US posture), scheduling moves and seeded portfolios changed what the catalogue must carry and what the store now guarantees; the list may hold events the store makes redundant and lack ones the new machinery enables. Deferred deliberately until the prompt overhaul settles -- review it next, before any measured batch.

- **Length.** The written turns run 280–340 words against a 250 budget. Whether to tighten is a judgement to make on reader feedback, not in advance — but it should be settled before the remaining 144 turns are written, not after.
- **The agency floor is stated twice with two values.** `scenario.yaml` says `eu_political_capital` ≥ 40; phase 1 above records it as reset to ≥12, applied or not at Johan's call. Capital sits at or near 0 on several Stage-3 paths, so which number is live decides whether most endings read as failures.
- **The portfolio drifts.** The actor restates its own measure portfolio each turn, so measures fall out of it: 109 of 387 proposals never reach the next turn's portfolio, and only 40 of those are explained by the run. One consequence is already in the story — on A2 the reader's turn-1 choice never enters the portfolio at all. Fixing it means moving the ledger into Python or the referee, which would invalidate the built tree, so it is recorded in `story/README.md` and deferred. Prose written from a portfolio should be checked against that turn's world state.
- **Whether the arm is revealed at the end.** Thematically right — the reader finds out the way the Union would — but it means putting the arm names into the page, which weakens the concealment enforced everywhere else. Not decided.

## Standing facts

Measured on the 36-run batch of 2026-09-02/03, not estimated (predates OpenRouter prompt caching and parallel sample elicitation — wall-clock per turn is lower now, costs slightly lower on cached reads):

- **$0.0069 per turn-execution; $0.090 per 13-turn run.** By step: events $1.62 of $3.24, then metrics $0.54, actor $0.46, referee $0.53 combined.
- **3.4 turn-executions per minute at 12 concurrent.** Throughput is roughly flat in concurrency above about 8, so it is an API-side limit; more parallelism buys little. (Parallel elicitation triples the events step internally since 2026-09-04; batch-level concurrency guidance unchanged.)
- **Seeds are never reused, across branches or arms** — event-profile overlap at a shared seed is 0.625 against 0.210, and three branches sharing a seed are substantially the same world. Nothing has to be tracked to hold this: `--seed` left off draws a random 64-bit seed and `config.json` records it, so collision is not a thing that happens. Pass `--seed` only where a run must repeat another one — `pin-turn-1.py` needs turn 1 identical across arms. The ledger of used blocks that used to sit here was bookkeeping against a risk the default already removes.
- **The harness kills background tasks at about 30 minutes.** Long batches go in a terminal tab or `nohup`, wrapped in `caffeinate -dimsu`, on mains power — `caffeinate -s` is ignored on battery and nothing stops clamshell sleep there.
- **Watch artefact files, not stdout.** Python block-buffers when redirected; `turn-XX/4-metrics.json` appearing is the reliable progress signal.

## Resuming this in a new session

1. Read this file. `AGENTS.md` points here, which is the only mechanism needed.
2. `git log --oneline -15` — commit messages here carry the reasoning and the numbers, deliberately.
3. Check which phase is open. Phase 4 is, and has been since 2026-09-07. If phase 1: the criteria above are the checklist. If phase 3: `story/README.md` and the branch logs say what is built. If phase 4: `story/README.md` holds the writing rules and the session procedure, and `grep -l 'status: written' story/tree/*/*.md | wc -l` says how far it has got.
4. Before believing any measurement, check the instrument. `/scripts/check_sovereignty.py` reported three different wrong answers on 2026-09-02/03 before its parser was right, and each wrong answer looked exactly as authoritative as the correct one.
