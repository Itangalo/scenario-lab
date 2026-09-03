# Europe 2032 – roadmap to the story

The goal is an interactive story: a reader takes the EU through 2026–2032, not knowing which of three AI trajectories they are on, choosing three times, and reaching one of twenty-four endings. `story/README.md` defines the tree and the naming. This file is the plan for getting there, and it is the document to read first in a new session. It is complemented with `design-notes.md`, used to remember decisions and important results.

This document keeps track of the work. Update it when the work moves along; it should always say where we are and what the next steps are.

## Phase 1 – the scenario stops moving

The gate for this phase is that the physics works well enough to have credible runs, on all four arms.

- [ ] All metrics should evolve in a credible way. This means, for example:
  - [ ] For acceleration, AI capacity will 
- [ ] **The declared floors are calibrated against a real batch.** `scenario.yaml` calls them first guesses. On the 36 runs they score 5/36 agency, 19/36 absorption, 24/36 legitimacy, 4/36 all three, and 0/12 acceleration runs clear anything. Either the Union is this weak once the accounting is honest — a legitimate finding — or the floors were set against the inflated sovereignty they no longer get. Decide which, and write it down.
- [ ] **Sovereignty accounting stays where it is or better.** Binding is 68% over 36 runs, up from 33%. Two named residual causes are in the design notes; both are optional.
- [ ] **A turn that drops a metric is caught.** One run of 2026-09-03 omitted `openweight_capability` from turn 1's JSON; the old value was carried forward and the run completed clean. Nothing checks metric completeness.

Deliberately *not* gates: the constitutional referee's 75% firing rate, and `openweight_frontier_release` moving the metric 1.2× an ordinary turn. Both are real and both are in the handoff. Neither changes the numbers the story is written from.

**Every rule change in this phase gets a batch that measures it.** The session of 2026-09-02/03 produced one clear positive (rule 2's midpoint: 0–8% → 16–27% of headroom used) and one clear negative (two prohibition clauses on step 3d: every difference inside one standard error, both targeted habits *up*). The negative cost an hour and was worth it. Assume nothing landed until a batch says so.

## Phase 2 – clear the ground

Once phase 1 closes, everything simulated before it is built on superseded physics.

- **Archive, don't delete.** `runs/` is gitignored and has been cleared twice already; findings survive only because they are written into `design-notes.md`. Before wiping, check that anything worth keeping is in that file.
- **`story/turn-01/` survives.** This was checked rather than assumed: the actor prompt never renders `metric_rules`, so none of the rule changes since turn-01 was drawn on 2026-08-31 could have altered the draw. What *did* change is two metric descriptions in `metrics.md` — `eu_political_capital` and `public_sentiment` each gained a sentence about sentiment feeding capital — which do reach the actor. That is a downstream mechanic, not a turn-1 consideration, and the pool split on measure category (28 of 30 in category 6) is very unlikely to move on it.
  - **Cheap check before trusting that:** draw 10 actor-only turn-1 responses under the current prompt and compare the category split against the recorded 28/2. Minutes, and about $0.01. If it holds, keep `opening.md` and both option files unchanged.
- ~~**`story/branch-A1/` and the `turn-0[2-5]-A1/` directories must be rebuilt.**~~ Removed 2026-09-03: built as a pilot on 2026-09-01, before the sovereignty accounting fix, rule 5's no-floor clause and both rule 2 changes, so its turns resolved under physics that no longer exists. In git history at `a7b5a3e` if the prose is wanted; the numbers are not.
- **The pinned turn-1 base runs must be regenerated per arm** (`story/pin-turn-1.py`), for the same reason: turn 1's *resolution* uses the metric rules even though its *actor response* does not.

## Phase 3 – the runs

Two independent bodies of work. Either order; 3a is one command and a wait, 3b needs judgement between stages.

### 3a – the statistics batch

20 runs per arm, 13 turns, 60 runs total. Serves the general statistics and doubles as the final proof that the scenario behaves.

- **780 turn-executions, about $5.40, about 3.8 hours** at 12 concurrent.
- One batch, one seed block, all three arms, no human input once launched.

### 3b – the story tree

42 blocks of four turns, each block ten simulations with one path selected at random; 18 option pools of ten actor-only draws. Three stages, because each stage's branches start from the previous stage's chosen path.

| stage | branches | turn-executions | cost | wall clock |
|---|---|---|---|---|
| turns 2–5 | 6 | 240 | $1.66 | 1.2 h |
| turns 6–9 | 12 | 480 | $3.31 | 2.4 h |
| turns 10–13 | 24 | 960 | $6.62 | 4.7 h |
| **total** | **42 blocks** | **1 680** | **$11.59** | **8.2 h** |

Plus 180 actor-only draws for the 18 option pools, about $0.22.

**Between stages sits a human decision** that cannot be automated: reading a pool of ten draws and choosing the two options that represent it, or saying plainly that the draws do not fall into two groups. `story/README.md` is explicit that inventing a split is the wrong answer, and the turn-1 pool is the worked example — 28 of 30 in one category, so the second option is presented as the minority draw it is.

**Whole programme: about $17 and 12 hours of wall clock.** Cheap enough that the constraint is attention, not credits: every stage of 3b needs someone to look at the pools.

## Standing facts

Measured on the 36-run batch of 2026-09-02/03, not estimated:

- **$0.0069 per turn-execution; $0.090 per 13-turn run.** By step: events $1.62 of $3.24, then metrics $0.54, actor $0.46, referee $0.53 combined.
- **3.4 turn-executions per minute at 12 concurrent.** Throughput is roughly flat in concurrency above about 8, so it is an API-side limit; more parallelism buys little.
- **Seeds are never reused, across branches or arms** — event-profile overlap at a shared seed is 0.625 against 0.210. Blocks used: 5101–5330, 5401–5834, 6101–6302, 7101–7312, 7401–7604, 7701–7904, 8001–8002, 8101–8504, 9101–9504. **Start at 10001.**
- **The harness kills background tasks at about 30 minutes.** Long batches go in a terminal tab or `nohup`, wrapped in `caffeinate -dimsu`, on mains power — `caffeinate -s` is ignored on battery and nothing stops clamshell sleep there.
- **Watch artefact files, not stdout.** Python block-buffers when redirected; `turn-XX/4-metrics.json` appearing is the reliable progress signal.

## Resuming this in a new session

1. Read this file, then `/HANDOFF.md` for where the last session stopped. `AGENTS.md` points here, which is the only mechanism needed — this does not belong in anyone's memory, because the repo is where it can be read by everyone and versioned alongside what it describes.
2. `git log --oneline -15` — commit messages here carry the reasoning and the numbers, deliberately.
3. Check which phase is open. If phase 1: the criteria above are the checklist. If phase 3: `story/README.md` and the branch logs say what is built.
4. Before believing any measurement, check the instrument. `/scripts/check_sovereignty.py` reported three different wrong answers on 2026-09-02/03 before its parser was right, and each wrong answer looked exactly as authoritative as the correct one.
