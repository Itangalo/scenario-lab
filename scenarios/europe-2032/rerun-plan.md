# Rerun plan: all story simulations on Muse Spark + store branch

Goal: re-run every simulation the story stands on (statistics batch + story tree), with `openrouter:meta/muse-spark-1.3-contributor` on the `store-v2-world-scope-and-metrics` branch. One full-scale shot, so this plan gates scale-up on a measured checkpoint rather than on confidence.

Status: plan written 2026-09-10. Pilot (10 runs, 4/3/3 across arms) done and audited; main batch (150 runs, batch=stats-20260910-spark-storev2, 50/arm) completed 2026-09-10 ~21:48 (one transient OpenRouter 502 on acceleration draw-058 at turn 7, resumed clean to 13 turns). Full audit below -- checkpoint PASSED, no fallback needed.

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

## Before launching: open decision -- RESOLVED 2026-09-10

- **Event-list review is done** (`europe-2032: event catalogue re-read and overhaul`). Catalogue back at 37 events: cut the three campaign events (mechanically idle), `capability_plateau_evidence`, `verification_widens`, `election_annulled`, `backlash_physical`; added three catastrophic "all bets are off" events, `us_labs_nationalised`, `knowledge_work_augmented`, `embodied_ai_deployment`, `research_breakthrough`; rewrote `opaque_reasoning`, `automated_decision_scandal`, `us_china_agreement`; rule 5's take-away list extended; all three arm patches updated; base validates and every arm loads.
- **Consequence for the pilot baselines:** election, posture, commitment, charge and custody findings stand (untouched mechanics). Fire-rate balance does NOT transfer -- new probabilities are first guesses, uncalibrated, and the old balance measurement was taken on the superseded list. The checkpoint's event checks are structural (family resolves, posture transitions, no missing sections), not distributional. Redo the balance measurement against the new list from an early batch chunk before trusting any rate.
- Starting context was sharpened the same day (Millennium Prize, pivotal agent incident, training-cluster takeover) -- sign-off predates it and re-renders with the new generation.

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

**Checkpoint result (21 runs, draws 001–021, 2026-09-10 ~18:27, PASSED):** store 273 turns, 0 missing actor sections, 0 missing world sections, 0 rejected, 1 unparsed + 1 described-but-unrecorded (same turn -- run-20260910-180017 t10, op object missing its closing brace; known malformed-JSON residual family, ~0.5% vs ~3% abort line). Charges 257 lines, 100%/100%. Election exactly-one 21/21 at turn 5 (12 consolidation, 5 alliance, 4 retrenchment). Posture 21/21 clean. Deadlocks 6/273 (2.2%, below ~5% pilot).

**Full-batch audit (150 runs, 1950 turns, filter stats-20260910-spark-storev2, 2026-09-10):**

- Store: 1521 commands applied, 0 missing sections (actor and world), 1 rejected, 3 unparsed lines (all malformed-JSON residual shapes), 3 argued-but-unrecorded (0.2% -- the re-ask-hook case; actor moves on without retrying, narrative never revisits the lost measure).
- Charges: 1876/1878 terms match the rows in flight (99.9%), 1872/1878 lines add up (99.7%). Every residual individually read: 3 one-turn undercharges where the GM gave a new measure a free first turn (202412t1 −3, 194821t1 −3, 194806t9 −2) -- the rules never state explicitly when a new measure starts costing, so one clarifying sentence belongs in rule 6/10 before 3b; 2 total slips (194821t1 states −10 for −7; 202534t12 states −4 for −5 at capital 23); 2 declared oddities (201434t7 openly records a void priority cost; 185240t1 dangles "+ 1 more for the priority" with no grand total); 1 silent-but-correct void (185234t8, capital 8). The checker grew four shapes in the process (hyphenated names like Tier-1, parenthetical figures, subtotal-first two-totals, void phrasings incl. "waived"/"uncharged"/"without effect", proximity-bound void detection).
- Referee note: with the single-model config format the referee (constitutional verdicts + statement-relevance) silently runs the cheap default `qwen3-235b`, not Spark -- matches the pilot so comparability holds, but the plan's "every turn task" needs that footnote. The GM (world state, notepad, metrics, charges) is Spark throughout.
- Catastrophes: ~15-20% of runs touch one, firing as early as turn 7 and stacking; all gate-checked clean (one bio fired at shut-gate 1%). Repeat catastrophic loss-of-control fired twice in one run -- absorbed narratively as persistence, still supports the decided change to Can repeat: No (held for post-batch).
- Batch-logging bug fixed along the way: the non-terminal fallback in `execute_batch_specs` re-printed the stored warning on every subsequent child line (thousands of duplicates); now prints on transition only, with regression test. Uncommitted, like the checker extensions.

**Abort and fall back to `main` if:** never-entered above ~3% post-fix shapes, any missing-section fault, any posture deviation, referee-deadlock rate far above the ~5% pilot rate, or any new unparseable-block shape. A fifth of the budget spent learning this is the pilot-first rule, not a loss.

## Story-tree rerun notes

Follow the ROADMAP 3b procedure (pin-turn, 10 reps, first-run path unless a fault promotes). Two store-branch specifics: pin-turn inherits store state through branch/resume (covered by tests, unexercised at story scale -- watch the first pinned block end to end), and the turn-1 pool procedure is unchanged except turn 1 no longer seeds programmes (seeds arrive at turn 0; the actor's first add is its own).

## Done looks like

Statistics batch per 3a counts, story blocks per 3b manifests, audits re-run per batch tag with numbers recorded here, sign-off re-rendered from a run of the new generation.
