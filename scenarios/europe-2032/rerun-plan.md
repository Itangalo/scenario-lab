# Rerun plan: all story simulations on Muse Spark + store branch

Goal: re-run every simulation the story stands on (statistics batch + story tree), with `openrouter:meta/muse-spark-1.3-contributor` on the `store-v2-world-scope-and-metrics` branch. One full-scale shot, so this plan gates scale-up on a measured checkpoint rather than on confidence.

Status: plan written 2026-09-10. Pilot (10 runs, 4/3/3 across arms) done and audited; main batch not launched.

## Locked decisions

- **Branch: `store-v2-world-scope-and-metrics`, kept outside main.** Runs record model, schema and seed in `config.json`, so provenance does not need a merge. Fallback if the checkpoint fails is `main` (pre-store architecture) with the new model -- itself unverified, and silent-drift-prone, which is why it is the fallback and not the plan.
- **Model for every turn task:** `openrouter:meta/muse-spark-1.3-contributor` with `reasoning_effort: minimal` (both in `scenario.yaml`). Without `minimal` the model spends the whole 3000-token budget reasoning and returns nothing parseable -- observed, not theorised. Analysis/synthesis keep their 32000-token task budgets.
- **Why the store branch:** its failure modes announce themselves per turn (absent sections, rejections, unparsed entries in changelogs) while the old architecture drifts silently. The story was already bitten once by silent drift (the A2 turn-1 choice that never entered any portfolio).

## Pilot results (the baseline the checkpoint compares against)

10 runs, 13 turns, 130 turn-executions, all exit 0, 2026-09-10:

- 0 missing `## Store changes` sections, actor and world, in 130 turns.
- Charges: 129 lines, 100% name the measures in flight, 100% add up (via `check_portfolio_drift.py --charges`, fixed for rule-10/two-total line shapes in the process).
- Election family exactly-one at turn 5, 10/10 (3 consolidation, 3 alliance, 4 retrenchment). Standing record undecided → pending → winner → stable, 10/10.
- `two_year_commitment`: added turn 1, modified turns 5 and 9, applied 10/10.
- GM scheduling moves landed 1–9 per run, all with grounds. Posture transitions verified live (closes the old turn-5/6 residual).
- Metrics: 0 omissions, 0 bounds violations. 14 sovereignty-line-vs-JSON mismatches, all coinciding with referee corrections (61 corrected turns; the 47 not touching sovereignty still match) -- mechanism behavior, logged separately, not a defect.
- Never-entered: 8 lost adds (~7%, worse than the 4.5% markdown baseline), all two shapes, both fixed and verified against the real failed blocks (nested `grounds` hoists; double-close `[{...}}]` salvages; missing commas/truncations still fail). Post-fix expectation is near zero on observed shapes; unobserved quirks at scale are the residual risk.
- Referee: 123 approved, 7 deadlocks, all from the referee misreading invariant 2 as delta-proportionality. Constitution item 2 now states levels-not-deltas explicitly. **Zero live runs behind that edit.**

## Before launching: open decision

- **Event-list review is still pending** (ROADMAP Phase 4 open questions). The rerun bakes the current list in. Either review first, or accept the list as-is for this generation. Do not start the batch with this undecided.

## Pre-launch checklist

1. `git log --oneline -3` on the branch; `git status` clean except the untracked `events (pruned).md`, which is live working material -- stage explicit paths only, never `git add -A`.
2. `python -m scenario_lab.cli validate scenarios/europe-2032/variants/acceleration.yaml` (and the other two arms).
3. Provenance draws: a draws dir with one JSON per job, each carrying `notes: "batch=<tag>"` in its top level, so `--filter <tag>` isolates the batch afterwards. Fresh 64-bit seeds by default; pass `--seed` only where a run must repeat another (pin-turn turn-1 identity).
4. Mains power, `caffeinate`, disk space for `--log-llm-io` transcripts (required -- the audit needs them).

## Launch

One command per arm (repeat counts per the story's needs -- 50/arm for the statistics batch; story-tree blocks follow the 3b procedure below, not these counts):

```bash
caffeinate -i scripts/run-notify.sh LOGFILE -- python -m scenario_lab.cli batch-run scenarios/europe-2032/variants/acceleration.yaml --repeat N --max-concurrency 6 --validate --log-llm-io --initial-states DRAWS/ >> LOGFILE 2>&1
```

Poll with `grep -q RUN_DONE LOGFILE`, never with sleep+pgrep. Throughput reference: 10×13 turns took ~25 minutes at concurrency 6.

## Checkpoint (mandatory before full scale)

After the first ~15–20 completed runs:

```bash
python scripts/check_portfolio_drift.py scenarios/europe-2032 --store --filter <tag>
python scripts/check_portfolio_drift.py scenarios/europe-2032 --charges --filter <tag>
```

Plus: grep changelogs for missing sections, referee `max_attempts_reached` rate, posture transitions (undecided → pending → winner → stable).

**Abort and fall back to `main` if:** never-entered above ~3% post-fix shapes, any missing-section fault, any posture deviation, referee-deadlock rate far above the ~5% pilot rate, or any new unparseable-block shape. A fifth of the budget spent learning this is the pilot-first rule, not a loss.

## Story-tree rerun notes

Follow the ROADMAP 3b procedure (pin-turn, 10 reps, first-run path unless a fault promotes). Two store-branch specifics: pin-turn inherits store state through branch/resume (covered by tests, unexercised at story scale -- watch the first pinned block end to end), and the turn-1 pool procedure is unchanged except turn 1 no longer seeds programmes (seeds arrive at turn 0; the actor's first add is its own).

## Done looks like

Statistics batch per 3a counts, story blocks per 3b manifests, audits re-run per batch tag with numbers recorded here, sign-off re-rendered from a run of the new generation.
