# Design notes – Europe 2032

Decisions taken and results worth remembering. `ROADMAP.md` tracks the work; this file is why the scenario is shaped the way it is, and what the runs showed before they were deleted.

**The runs behind almost everything here are gone.** `runs/`, `actor-samples/` and the old `calibration-runs/` are gitignored, and they have been cleared three times. Nothing below can be re-derived without paying for the batch again — about $3 and two hours for thirty-six 13-turn runs. That is the whole reason this file exists.

**Read the dates.** A number measured before a rule changed describes a world the scenario no longer produces. Superseded figures are marked where they stand rather than deleted, because knowing what a change moved is worth more than a tidy file.

## Why turn 1 stopped being a fork

The three roads that used to fork at turn 1 – sovereign compute, resilience surge, evaluator access – were retired on 2026-08-30. The road files themselves are gone; what mattered about them is here. Three things had gone wrong with them:

- They open their portfolio with `Nothing in flight.`, from a prompt that told the actor the inherited programmes belonged in its reasoning and never in the list. The prompt now seeds two of them directly.
- They declare `Capital cost:` and `Lead time:`, which the rebuilt mechanics do not read.
- Road A launches a compute programme alongside the inherited InvestAI Gigafactories, which the prompt now names as the one move the Union cannot credibly make.

**Re-drawing did not work, and the reason is the useful part.** Twenty fresh draws under the current prompt returned 16 category 6 measures and 4 category 5, and **no category 4 at all**. The spread the three roads were selected from no longer exists. Whether that is the guard against duplicating the Gigafactories working as intended, or overshooting so far that sovereignty has left the actor's turn-1 repertoire, is not established – and it bears directly on the open question above.

Turn 1 is now a single fixed opening at `story/turn-01/opening.md`, shared by every arm and every reader, and the fork moved to turn 2.

## What the first batches settled

Two batches of thirty, archived 2026-08-29, plus four smoke runs from 2026-08-27 whose directories were deleted 2026-09-03. What survived them:

- **The 2028 election machinery works, as a mutually exclusive event group.** It had fired in only 22 of 30 plateau runs despite a condition saying it always happens, because `probability_samples: 3` averages the events step's draws and the model omitted the event from some of them. As a group: exactly one outcome in all 30 acceleration runs, and all three reachable — 18 consolidation, 7 retrenchment, 5 alliance, against an alliance that had been unreachable rather than merely rare.
- **Seeds must not be shared across branches or arms.** Both batches reused 700001–700010 by index. Event-profile overlap between two branches at the same seed is 0.625 against 0.210 at different seeds; across arms, 0.271 against 0.099. Three branches sharing a seed are substantially the same world. This is why the roadmap tracks used seed blocks.
- **Three prompt fixes came out of the smoke runs**, all long since applied: the turn-1 portfolio starts empty, an action may not smuggle in a second instrument, and event ids are banned from the narrative. A fourth followed from the actor restating its standing commitment in prose instead of entering it in the ledger — the commitment is now seeded in `background/actors/eu.md` so it exists from turn 1 in every run.
- **Still worth watching, and never resolved:** the actor tagged a cyber-resilience measure as category 4 when it belongs in category 6. Category tags are what `rq_no_regret` groups on, so a mis-tag lands directly in an analysis result.

## Political capital: what controlled it, and why those numbers are not quotable

Three batches of four 13-turn runs on verification-bounded, mid-2026-09-01, each changing one thing. **Every figure they produced was measured while sovereignty was inflating** — the accounting defect described below was live throughout — so the magnitudes are unreliable and are not repeated here. Three things survive the contamination:

- **The completion bonus was not the lever, and halving it did the opposite of what was predicted** — the prediction was −10 and the result was +8.4. The reasoning that picked it did arithmetic on the one term the notepad records and never counted the others, because everything else was applied inside the Game Master's reasoning and left no trace.
- **`eu_ai_sovereignty` crossing 40 is what controls the balance**, because rule 6 pays a dividend every turn above that gate. The direction was later confirmed the hard way: once the accounting was fixed and sovereignty stopped inflating, almost nothing crossed 40 and median final capital fell from 32 to 21.
- **The measurement gap is the thing to fix first.** Three consecutive changes had their effects inferred rather than read. That lesson produced the required-output-line pattern, and then its limit — see below.

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

## A negative result: two more prohibitions bought nothing (ECHO 2026-09-02)

The two residual causes named above each got a clause in step 3d — write only the terms you are charging, and stop at the total — and were measured against the same two arms over eight runs of eight turns, seeds 8401–8504 against 8101–8204 truncated to turn 8.

| | before | after | |
|---|---|---|---|
| revises the total (`= 31 → adjusted to 28`) | 22% | 30% | not distinguishable |
| decay written where the rise was under 2 | 23% | 32% | not distinguishable |
| total is applied | 57% | 65% | not distinguishable |
| terms sum to total | 55% | 52% | not distinguishable |

Every difference sits inside one standard error, and both habits the clauses targeted went up rather than down. Net drift moved −2.3 to +0.1 per run while its range widened, which is not an improvement either. The clauses were reverted.

**The distinction worth keeping.** Step 3d worked when it changed the shape of the computation — the line now runs from a figure to a figure, and the figure it ends at is the metric. These two clauses only told the Game Master to stop doing things, on a step that already carries five numbered rules and four required output lines. Prohibition is not the same instrument as reformulation, and this step appears to be saturated with the first.

Whether the residual −4 drift can be removed at all is open. It would need a 13-turn batch to measure, because at eight turns the drift is mean −2.3 and negative in only four runs of eight, against −3.8 and seven of eight over the full thirteen.

## Open weights were pinned, and the event that should move them is inert (ECHO 2026-09-03)

Found by looking at the 36-run batch rather than by suspecting it: `openweight_capability` ended at 46.5 under acceleration while `ai_capability` ended at 92.9, a 46-point gap no rule intended.

Rule 2 said the metric "should normally be set between old value and last turn's value of `ai_capability`". The bottom of that range is the old value, so leaving the metric where it stood was legal every turn, and nothing selected within the range. Across all 36 runs the Game Master used **0–8% of the available headroom** per turn, in every arm. The rule was being obeyed exactly, and obeying it meant standing still.

**What it was costing was the proliferation half of the event catalogue.** Several events key off open-weight thresholds — `cyber_major_incident`'s gate opens at 55 and gains 8 points above 65, `bio_uplift_findings` gains 6 above 55, `election_voided` 5 above 60. Across 36 runs the metric reached 55 in one run, and 60 and 65 in none. The dice were being rolled at odds that could not occur.

Rule 2 now sets the metric around the midpoint of its old value and last turn's capability. Four acceleration runs against the twelve from the same night:

| | before | after |
|---|---|---|
| headroom used per turn | 1–8% | 16–27% |
| `openweight_capability` at turn 13 | 46.5 | 72.1 |
| gap to `ai_capability` | 46.5 | 20.4 |
| runs ever reaching 55 / 60 / 65 | 1 / 0 / 0 of 12 | 4 / 4 / 4 of 4 |

The midpoint behaves as a proportional controller: it closes a fifth to a quarter of the gap a turn while capability keeps moving, so the two converge to a stable separation of about 20 rather than meeting. That separation is now a modelled quantity instead of an artefact of a rule's floor.

**The event is a separate failure and is not fixed.** `openweight_frontier_release` was to make the metric "jump to at most 5 below `ai_capability` at a stroke" — read as a ceiling, not a destination. It fired 32 times across the 36-run batch and landed in its band **none** of them; after the midpoint change it fired 7 times in 4 runs and landed in the band **none** of them, the resulting gap improving only because the floor beneath it had risen. That bullet has been folded into the midpoint clause as "higher if `openweight_frontier_release` just occurred", which removes a line that did no work but states a direction where the old one stated a number:

| | release turns | ordinary turns |
|---|---|---|
| original rule | rise 5.00 (n=3) | 0.39 |
| midpoint + the old bullet | 3.21 (n=7) | 2.70 |
| folded | 2.90 (n=5) | 2.45 |

An event whose description calls it irreversible — "on private hardware permanently and beyond recall" — now moves the metric 1.2× what an uneventful turn does, against 13× under the original rule. The trend is fixed and the shock is not. Accepted deliberately for now.

**The untested version, if this is revisited:** a destination inside the clause that already moves, rather than a direction — "set around the midpoint; in the turn `openweight_frontier_release` occurs, set it instead to 5–10 below `ai_capability`." One bullet, one reading, but a number in it.

**Where the right sentence was the whole time.** `events.md` states the intent unambiguously in that event's Description, and the sign-off coverage table has marked that heading **NO** for as long as it has existed: only `Condition:` and `Probability:` are rendered into the events prompt. The correct instruction was written, reviewed, and never sent to anything.

## What thirty-six runs looked like, before the rule 2 fix (ECHO 2026-09-03)

Twelve runs per arm, 13 turns, seeds 9101–9312. The directories are deleted; this table is what is left of them.

**Superseded in one column and everything downstream of it.** This batch ran before rule 2 was given a target, so `openweight_capability` is the pinned ~45 described above. Since open-weight thresholds gate `cyber_major_incident` and add to three other events, the incident-driven metrics — safety, resilience, sentiment — were all measured with those branches shut. Treat this as the baseline the fix was measured against, not as a description of the current scenario.

| turn 13, median | acceleration | verification-bounded | plateau |
|---|---|---|---|
| `ai_capability` | 92.9 | 72.1 | 66.0 |
| `openweight_capability` | 46.5 | 44.6 | 45.4 |
| `ai_safety` | **3.2** | 15.5 | 23.2 |
| `resilience` | 47.7 | 49.7 | 47.5 |
| `eu_ai_sovereignty` | 23.2 | 27.7 | 31.5 |
| `eu_political_capital` | 17.1 | 26.3 | 23.3 |
| `public_sentiment` | 29.5 | 27.2 | 30.6 |

**The arms separate cleanly on capability** — 92.9 / 72.1 / 66.0, with verification-bounded extremely tight at 70.5–73.5. That was the design intent and it holds.

**`ai_safety` pins to its floor under acceleration:** ≤5 in 9 of 12 runs by a median of turn 8, ending at 0.0 in several, against 2 of 12 under verification-bounded and 1 of 12 under plateau. A metric on its stop carries no information, and rule 11 prices lab-origin incidents off the capability−safety gap.

**Sovereignty does not move on any arm** — 23.2 / 27.7 / 31.5 from a start of 22 — and crosses rule 6's dividend gate at 40 in 4 of 36 runs (0 acceleration, 1 verification-bounded, 3 plateau). The pre-fix batches averaged 42.1 at turn 13; that was the inflation, and this is what the metric does when the accounting is honest.

**Scored against the declared floors** — agency ≥40, absorption ≥50, legitimacy ≥25:

| | agency | absorption | legitimacy | all three |
|---|---|---|---|---|
| acceleration | 0/12 | 5/12 | 9/12 | **0/12** |
| verification-bounded | 3/12 | 7/12 | 6/12 | 2/12 |
| plateau | 2/12 | 7/12 | 9/12 | 2/12 |
| **all** | **5/36** | 19/36 | 24/36 | **4/36** |

Median final political capital across all 36 was 21, with 17 of 36 below the paralysis threshold of 20. Either the Union is this weak once the accounting is honest — a legitimate finding for a scenario built to ask whether agency depends on holding capacity — or the floors were set against sovereignty figures the scenario no longer produces. That decision is open, and it is a phase 1 item in `ROADMAP.md`.

## What the events actually do, measured for the first time (ECHO 2026-09-03)

Two phase 1 gates ask whether events trigger correctly and whether the list is balanced, and until now nothing read the event artefacts. `scripts/check_events.py` does, over the 32 multi-turn runs of 2026-09-03 (seeds 9105–9312 pre-rule-2-fix, 9401–9504 after) — 416 turns. **Most of the corpus predates the open-weight fix**, so the incident events gated on `openweight_capability` at 55 and 65 were rolled with those branches shut; listing and effect are not sensitive to that, firing rates for `cyber_major_incident` and `bio_uplift_findings` are.

**Listing holds. 26 of 2496 required listings are missing, about 1%.** The six always-eligible events must appear every turn whatever the world does; `taiwan_blockade` accounts for 16 of the misses and `bio_incident` 7, almost all in turns 8–13. The 2028 election family was complete in every one of its due turns, which is the machinery that failed before the group mechanism existed. This is inside the roadmap's stated tolerance of one in ten, and it is the first time the claim has been checked rather than assumed.

**Balance holds, in the sense that nothing is dead.** All 35 events fire at least once; per-listing fire rates run 1–16% for the ordinary catalogue, and every event touches at least 5% of runs. The extremes are `eval_anomaly_reports` (16% per listing, 57% of runs) and `bio_incident` (1%, 10% of runs) — both consistent with what their entries say they are.

**Effect does not hold, for a specific and coherent half of the catalogue.** Comparing the mean metric movement on an event's firing turns against an ordinary turn of the same arm, ten events with four or more firings are indistinguishable from a turn where nothing happened. Five of them are the geopolitical ones: `member_state_defection` (49 firings, largest difference 0.3), `export_control_escalation` (41, 0.6), `eu_frontier_access_denied` (27, 0.7), `supply_chain_coercion` (24, 0.9), `taiwan_tension_rise` (24, 0.9).

**The cause is in the rules, not in the prompt.** The descriptions do reach the metrics step — `_format_triggered_events` renders each fired event's full description into it. What is missing is a channel. Rule 5 gives `eu_ai_sovereignty` exactly two terms, a category 4 completion and the capability decay, so no event can move it however directly it bears on the Union's capacity to act. Rule 6 does give events a route into `eu_political_capital`, and the events that use it — `ai_investment_collapse` at −1.8, `backlash_physical` at −1.1 — are the ones the rule's own wording fits. The five inert events are the ones whose natural target is sovereignty, and sovereignty is closed.

**Being named in the rules is not what decides it.** Median largest movement is 2.2 for the eight events the metric rules name and 1.5 for the 24 they do not, and the largest single mover in the corpus (`medical_breakthrough`, +4.6 on sentiment, n=5) is unnamed. The Game Master prices an unnamed event from its description perfectly well. It does not price one whose only plausible target is a metric the rules have closed.

**What this leaves open.** Whether events should reach sovereignty at all is a design decision, not a defect to fix silently: the metric was deliberately made hard to move, and the 2026-09-02 work establishes that its accounting only started binding once it was tightened. The choice is between a third term in rule 5 for events that directly remove or secure the Union's access to capacity, and accepting that sovereignty is a stock that only the Union's own finished measures move — in which case `rq_sovereignty_and_agency` should stop listing five events that cannot affect its metrics.

## The floor at 22 was the referee, not the Game Master (ECHO 2026-09-03)

The 2026-09-02 notes record runs writing `net unchanged due to floor at 22.0` and conclude that the Game Master was inventing a bound that does not exist. Rule 5 was given a no-floor clause, and the sentence kept appearing. It was not an invention. It was a description of what the constitutional referee was about to do.

Constitutional invariant 2 reads "Capability is accumulated and does not fall" and names `ai_capability` and `openweight_capability`. The referee has been applying it to `eu_ai_sovereignty`, in as many words: on `run-20260903-121626` turn 3 it wrote "Invariant 2 violated: `eu_ai_sovereignty` decreased from 22.0 to 20.0 despite no narrative or notepad indication of catastrophic physical destruction of the compute base ... Sovereignty may stagnate or grow slowly, but cannot fall absent this extreme condition." The turn was corrected and approved, and the metric ended at 22.0.

Measured over 1421 turns of the 2026-09-02 and 09-03 corpus, on the 326 turns whose `SOVEREIGNTY:` line states a fall:

| the referee | turns | metric did not move at all |
|---|---|---|
| objected to the fall | 185 | 118 (**64%**) |
| said nothing of it | 141 | 28 (20%) |

The asymmetry runs the other way for rises: a line stating a rise ends with the metric unmoved in 17% of turns, against 39% for a line stating a fall. A referee that objects to a fall is three times as likely to see it cancelled as one that does not.

**This is the best available explanation for a metric that does not move on any arm.** The 36-run batch put sovereignty at 23.2 / 27.7 / 31.5 at turn 13 from a start of 22, and crossing rule 6's gate at 40 in 4 of 36 runs. Rule 5's decay was added deliberately so that a fast frontier erodes the estate; a bound at the starting value cancels the decay every time it bites, which turns a metric with two signed terms into a ratchet that can only rise.

It also revises a conclusion in the notes above. The 2026-09-02 finding that the sovereignty line binds in 68% of turns was measured against a metric whose falls were being reverted downstream of the line, so part of the residual non-binding was never the line's fault at all.

**Invariant 2 now names its two metrics in its heading and states in full that it reaches no other**, with sovereignty spelled out, since a heading reading "does not fall" is what a model matches against. The three prohibitions that failed on 2026-09-02 were prohibitions on a saturated step; this is a scope correction on a check that was reading its own remit too widely, which is a different instrument.

**Not yet measured:** whether the correction lets sovereignty move, and whether rule 5's new event term together with an unblocked decay drives the metric to its floor instead. A metric on its stop carries no information either way.
