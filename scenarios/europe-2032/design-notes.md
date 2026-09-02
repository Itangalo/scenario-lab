# Design notes – Europe 2032

What the runs so far have shown, and why the scenario is built the way it is. The findings below outlived the runs that produced them: two batches of thirty were archived on 2026-08-29 and the measure mechanics were rebuilt after them, so nothing here should be re-derived from those runs, only remembered.

## The open question

**Sovereignty did not move.** Across two arms and three roads, `eu_ai_sovereignty` ended within three points of its starting 22 in every case – including the road that opened with a high-cost category 4 compute programme and pursued it for four turns.

| arm | road | sovereignty at turn 5 |
|---|---|---|
| plateau | A build | 24.0 |
| plateau | B absorb | 24.5 |
| plateau | C reach | 24.0 |
| acceleration | A build | 25.0 |
| acceleration | B absorb | 25.0 |
| acceleration | C reach | 24.5 |

Two candidate causes were identified and one was fixed. The fixed one: nothing read a measure's declared `Lead time:`, so every measure completed in two turns of priority whatever it claimed, and rule 10's clause advancing unprioritised measures only above `eu_political_capital` 55 never fired because the runs sat at 34–45. Measures now carry a stated finishing turn instead. **Whether that was the whole cause is unknown** – it has been through four-turn smoke tests only, and the question wants a batch.

The second candidate is untested: that the actor was rationally routing around a wall. Road A's compute programme read `under implementation` in 9 of 10 acceleration runs at turn 5 whatever the Union did, always for the same reasons in prose – legal anchoring deadlocked, an ECJ referral, procurement frozen.

## What else those batches settled

- **The 2028 election machinery works.** It fired in 22 of 30 plateau runs despite a condition saying it always happens, because `probability_samples: 3` averages the events step's draws and the model omitted the event from some of them. Resolved as a mutually exclusive event group: exactly one outcome in all 30 acceleration runs, and all three reachable – 18 consolidation, 7 retrenchment, 5 alliance, against an alliance that had been unreachable rather than rare.
- **Seeds must not be shared across branches or arms.** Both batches reused 700001–700010 by index. Event-profile overlap between two branches at the same seed is 0.625 against 0.210 at different seeds; across arms, 0.271 against 0.099. Three branches sharing a seed are substantially the same world.
- **The arms separate on capability and safety, not on the Union's room to act.** Acceleration ends 5–12 points above plateau on capability and 4 below on safety, on every road. Public sentiment converges on 28 in all three acceleration roads where plateau spread 11 points between them: under acceleration the public reads the world rather than the Union's choice of instrument.

## Why turn 1 stopped being a fork

The three roads that used to fork at turn 1 – sovereign compute, resilience surge, evaluator access – were retired on 2026-08-30 and are in `story/turn-01/superseded-roads/`. Three things had gone wrong with them:

- They open their portfolio with `Nothing in flight.`, from a prompt that told the actor the inherited programmes belonged in its reasoning and never in the list. The prompt now seeds two of them directly.
- They declare `Capital cost:` and `Lead time:`, which the rebuilt mechanics do not read.
- Road A launches a compute programme alongside the inherited InvestAI Gigafactories, which the prompt now names as the one move the Union cannot credibly make.

**Re-drawing did not work, and the reason is the useful part.** Twenty fresh draws under the current prompt returned 16 category 6 measures and 4 category 5, and **no category 4 at all**. The spread the three roads were selected from no longer exists. Whether that is the guard against duplicating the Gigafactories working as intended, or overshooting so far that sovereignty has left the actor's turn-1 repertoire, is not established – and it bears directly on the open question above.

Turn 1 is now a single fixed opening at `story/turn-01/opening.md`, shared by every arm and every reader, and the fork moved to turn 2.

## Calibrating political capital, and what actually controlled it

Three batches of four 13-turn runs on the verification-bounded arm, each changing one thing, because the runs themselves are not kept and the numbers would otherwise be lost.

| batch | change | finals | mean | sovereignty crosses 40 |
|---|---|---|---|---|
| A | baseline after the by-metric rewrite | 38, 38, 28, 43 | 36.8 | t10, t7, t10, t7 |
| B | completion bonus `+4..+8` → `+2..+5` | 45, 48, 45, 43 | 45.2 | t8, t7, t8, t10 |
| C | in-flight effect capped at half the finished figure | 30, 36, 31, 20 | 29.2 | t9, t13, never, never |

**The completion bonus was not the lever, and halving it did the opposite of what was predicted.** The reasoning that picked it was arithmetic on the one term the notepad records — six to eight completions at `+4 to +8` — and it never counted the others, because only the portfolio charge and the proposal bonus are written down. Everything else is applied inside the Game Master's reasoning and leaves no trace. The prediction was −10; the result was +8.4.

**`eu_ai_sovereignty` crossing 40 is what controls the balance.** Rule 6 pays `+1 to +3` a turn above that gate, and in A and B every run collected it for four to seven turns. Batch C's cap slows in-flight accumulation, so two runs never crossed at all and a third crossed at turn 13 — and the mean fell by 16. Nothing else moved comparably in any batch.

**The cap buys lower capital by making the Union less effective, not by making action cost more.** Resilience fell from 55, 51, 55, 53 to 42, 38, 44, 53, so only one run of four still clears the `absorption` floor of 50. That is a real trade and it was accepted deliberately. If a later pass wants the capital distribution without the effectiveness cost, the levers are on the cost side — the per-turn charge, the priority cost, or lowering rule 9's gate below 40 so that runs which do build sovereignty are still paid for it.

**The measurement gap is the thing to fix first if this is revisited.** Three consecutive changes had their effects inferred rather than read, because the positive terms are invisible. A `CAPITAL LEDGER` line in the notepad — charge, completions, dividend, attribution, lend, each itemised — would make the next comparison arithmetic instead of guesswork, and it is the same shape as the two lines that already work reliably.

## Why the sovereignty line did not bind (ECHO 2026-09-02)

The `SOVEREIGNTY:` line was added on 2026-09-01 because the three earlier required lines had each turned an unreliable mechanic reliable. It was written in 156 of 156 turns and changed nothing. `scripts/check_sovereignty.py` reads a run's notepad lines against the metric values it actually applied, and over the batch of twelve that prompted the question it reproduces the hand-count and adds two things the hand-count could not see.

| | before | after |
|---|---|---|
| line written | 156/156 (100%) | 156/156 (100%) |
| the line's own terms sum to the total it states | 99/142 (70%) | 71/140 (51%) |
| **that total equals the change actually applied** | **45/136 (33%)** | **94/139 (68%)** |
| the line starts from the value the metric actually held | – | 137/138 (99%) |
| a measure credited with finishing in more than one turn | 13, in 9 of 12 runs | 9, in 6 of 12 runs |
| the longest such repeat | 6 consecutive turns | 3 turns |
| a move above +2 with no completion named | 7 turns, largest +6 | 1 turn, largest +3 |
| largest gap between the line and the metric | −18.0 | −5.0 |

Twelve runs each side, four per arm, thirteen turns, seeds 7701–7904 before and 8101–8304 after.

**Two figures in this table were reported wrong earlier on 2026-09-02, in the design notes and in commit `70066bb`'s message: a baseline of 21% binding and 59% after.** Both came from the checker, which was resolving every stated total as a change. The Game Master mixes levels and changes freely — `= 33` after 32 is a level, `= −1` after 22 is a change, and the same line may end at one and append the other — so a level read as a change invented drift that was never there, including a spurious 32-point gap in each cohort. `resolve_claim` now decides from the value the metric held going in, and the test table in `tests/test_check_sovereignty.py` pins the six shapes. The corrected figures are above; the direction and the size of the improvement survive the correction, and the baseline was never as bad as first reported.

**The line is copied forward.** The clearest case runs `SOVEREIGNTY: InvestAI Gigafactories finished +5, Mandatory Compute Residency finished +5, capability rose 1 −1 = +9` word for word through turns 8 to 12, while the applied change over those turns was +4, +12, +5, 0, 0 and the narrative beside it said in plain prose that the money had already been paid. This is the same failure as the annuity bug fixed on 2026-09-02 in `d86af31`, reappearing one level up: the figure no longer persists in the rules, but the *sentence* persists in the notepad, and copying it re-pays the completion.

**The Game Master could not see the numbers.** `metrics_json` is rendered into the events prompt and into the actor prompt. It was never rendered into the metrics prompt — the one step whose output is the next set of metric values had to recover the current ones from the previous turn's narrative prose. Every rule that asks it to reason from a level (rule 6's gate at 40, rule 5's decay, an accounting line that starts from last turn's figure) therefore depended on how legibly the narrative happened to restate the number. It is now in all three prompts, and in the default template too, because the same hole was there for every scenario.

**A floor at 22 was being invented.** Runs wrote `net unchanged due to floor at 22.0` and held sovereignty at its start value. There is no floor: the metric's range is 0–100 and 22 is the opening reference point on the scale. Rule 5's decay, added deliberately in `61fcb5c` so that a fast frontier erodes the estate, was being cancelled by a bound that does not exist. Rule 5 now says so.

**What did not improve is the line's internal arithmetic**, which fell from 70% to 51%. The cause is visible and separate from binding: the Game Master now lists rule 5's decay term even in turns where its condition does not hold — `20 last turn, no completion, Gigafactories in flight +0, capability rose 1.0 −1 = 20` — and then correctly declines to charge it, because the rise was under 2. The level is right and the sum is not. More terms named per line means more chances to name one that is not being charged. The fix is a clause saying not to write a term you are not applying, and it was deliberately not made during the batch so that the batch measured one change.

**What the pattern's limit actually is.** The handoff's reading was that writing something down only works when the writing is the mechanism. That holds, and it is sharper than it looked: the portfolio charge binds because the total cannot be known without summing it, and the sovereignty line did not because it ended at a *delta* while the JSON carried a *level*, so nothing connected the two ends. The line now starts at last turn's figure and ends at this turn's, and the number it ends at is the one written into the metrics JSON — there is no second number for the two to disagree about. Binding doubled, from a third of turns to two thirds. It did not reach one: what survives is an `→ adjusted to N` clause appended after a total has been reached, which is the same escape the `→ net +1` clause used to be, and which the rewritten step 3d names but does not prevent.

## The constitutional referee is not the backstop it looks like (ECHO 2026-09-02)

Measured over the same batch of twelve: the referee raised at least one violation in **117 of 156 turns (75%)**, naming `eu_ai_sovereignty` in 76 of them, and ran a mean of 2.13 iterations per turn against a maximum of 4. It reached `corrected_and_approved` and the run continued.

It was not missing the bug. On `run-20260902-155512` turn 5 it wrote that sovereignty rose 28.0 to 41.0 while "the notepad shows only +1 from prior momentum, with no justification for an additional +12" — an exact description of the defect that batch was run to investigate — and the turn was approved after correction. A check that fires on three quarters of turns carries no information in any single turn, and nothing downstream reads it. Its output sits in `turn-XX/5-constitutional-check.json` and no analysis path opens the file.
