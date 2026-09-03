# Europe 2032 – roadmap to the story

The goal is an interactive story: a reader takes the EU through 2026–2032, not knowing which of three AI trajectories they are on, choosing three times, and reaching one of twenty-four endings. `story/README.md` defines the tree and the naming. This file is the plan for getting there, and it is the document to read first in a new session. It is complemented with `design-notes.md`, used to remember decisions and important results.

This document keeps track of the work. Update it when the work moves along; it should always say where we are and what the next steps are.

## Phase 1 – the scenario stops moving

The gate for this phase is that the physics works well enough to have credible runs, on all four arms.

- [X] All metrics should evolve in a credible way. This means, for example:
  - For ai_capability and ai_safety: In the Acceleracion arm (A), the former will often hit the ceiling and the latter will often crash. In the other arms, it is more balanced.
  - For openweight_capability: This should trail ai_capability in basically all runs, all arms. For the Plateau arm (P), it should almost match ai_capability in the final rounds.
  - For eu_ai_sovereignty, eu_political_capital and public_sentiment: These metric should struggle. Some successes and some alarmingly low. Lower end on the A arm.
- [ ] **Events are triggered roughly correctly, and their effects are managed roughly correctly.** Triggering holds: `scripts/check_events.py` over 416 turns finds 26 of 2496 required listings missing, about 1%, and the 2028 election family complete in every due turn. Effects do not, for one coherent half of the catalogue: ten events with four or more firings move the metrics no differently from an ordinary turn, five of them the geopolitical ones whose only plausible target is `eu_ai_sovereignty` — which rule 5 closes to everything but a category 4 completion. **This needs a decision, not a fix:** either rule 5 gets a third term for events that directly remove or secure access to capacity, or sovereignty is accepted as a stock only the Union's own measures move and `rq_sovereignty_and_agency` stops listing five events that cannot reach its metrics. See `design-notes.md`.
- [X] **The event list is fairly balanced.** All 35 events fire at least once across the 32-run corpus; per-listing fire rates run 1–16% and every event touches at least 5% of runs. Nothing in the catalogue is dead and nothing is scenery. Measured mostly before the open-weight fix, so the incident events gated at `openweight_capability` 55 and 65 were rolled with those branches shut — their true rates are higher than the table says, which does not change the conclusion.
- [X] **A turn that drops a metric is caught.** One run of 2026-09-03 omitted `openweight_capability` from turn 1's JSON; the old value was carried forward and the run completed clean. The metrics step now compares the parsed JSON against the scenario's metric ids, asks once for the omitted ones by name, and writes the outcome to `turn-XX/4-metrics-metadata.json` either way; anything still missing is filled from the value the run actually uses, so no artefact carries an absent key. The referee's correction step is guarded the same way, since a correction that drops a metric reverts it to last turn's value.

Deliberately *not* gates: Exact arithmetic correctness, rare occasions of mechanics malfunctioning (less than one in ten).

**Open on 2026-09-03, waiting on one batch.** Two changes were made to the remaining gate and neither is measured yet: rule 5 gained a third term so an event that takes away or secures access to capacity can reach `eu_ai_sovereignty`, and constitutional invariant 2 was bound to the two metrics it names, having been applied to sovereignty and reverting 64% of the falls it objected to. Six acceleration runs of 13 turns, seeds 10002–10007, are the measurement: does sovereignty now move, and does it move so far that it sits on its floor instead. Both are failures; the metric has to end somewhere in between. `scripts/check_sovereignty.py` reads the first and `scripts/check_events.py --effects` the second.

## Phase 2 – clear the ground

Once phase 1 closes, everything simulated before it is built on superseded physics.

- **Archive, don't delete.** `runs/` is gitignored and has been cleared twice already; findings survive only because they are written into `design-notes.md`. Before wiping, check that anything worth keeping is in that file. Note that an acceptable option is to prune the design notes -- not every old decision needs to be saved.
- **`story/turn-01/` survives** unless new checks reveal that it is obsolete.
  - **Cheap check before trusting that:** draw 10 actor-only turn-1 responses under the current prompt and compare the category split against the recorded 28/2. Minutes, and about $0.01. If it holds, keep `opening.md` and both option files unchanged.
  - **The pinned turn-1 base runs must be regenerated per arm** (`story/pin-turn-1.py`): turn 1's *resolution* uses the metric rules even though its *actor response* does not.

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
- **Seeds are never reused, across branches or arms** — event-profile overlap at a shared seed is 0.625 against 0.210. Blocks used: 5101–5330, 5401–5834, 6101–6302, 7101–7312, 7401–7604, 7701–7904, 8001–8002, 8101–8504, 9101–9504, 10001–10007. **Start at 10101.**
- **The harness kills background tasks at about 30 minutes.** Long batches go in a terminal tab or `nohup`, wrapped in `caffeinate -dimsu`, on mains power — `caffeinate -s` is ignored on battery and nothing stops clamshell sleep there.
- **Watch artefact files, not stdout.** Python block-buffers when redirected; `turn-XX/4-metrics.json` appearing is the reliable progress signal.

## Resuming this in a new session

1. Read this file. `AGENTS.md` points here, which is the only mechanism needed.
2. `git log --oneline -15` — commit messages here carry the reasoning and the numbers, deliberately.
3. Check which phase is open. If phase 1: the criteria above are the checklist. If phase 3: `story/README.md` and the branch logs say what is built.
4. Before believing any measurement, check the instrument. `/scripts/check_sovereignty.py` reported three different wrong answers on 2026-09-02/03 before its parser was right, and each wrong answer looked exactly as authoritative as the correct one.
