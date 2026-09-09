# Proposal: who holds persistent state

Status: **open**, opened 2026-09-09. Nothing is implemented. This records a measured defect, the design conversation around it, and what a future session needs in order to continue without redoing the work.

Out of scope here: whether to re-run any europe-2032 simulations because of this. That is a separate decision.

## The defect

An actor's measure portfolio is not held by the framework. The actor re-emits it in its own output every turn, so an entry survives only if the model remembers to write it again. Measured with `scripts/check_ledger.py` over the 150-run statistics batch (unpinned, fresh initial draws, the cleanest sample available):

| | count | share |
|---|---|---|
| measures proposed | 1 391 | |
| entered the portfolio at some later turn | 1 299 | 93.4% |
| never entered, run states a reason | 28 | 2.0% |
| **never entered, no reason stated** | **64** | **4.6%** |

| | count | share |
|---|---|---|
| measure-turn transitions | 5 626 | |
| carried forward | 4 733 | 84.1% |
| left with a stated cause (finished or cancelled) | 859 | 15.3% |
| **vanished, no stated cause** | **34** | **0.6%** |

The 42 story path runs give 7.8% and 0.8% for the two unexplained rates — worse, but they are pinned and a smaller sample, so weight the batch.

Never-entering is the larger failure and the worse one: a measure that never arrives is invisible from the first moment, while one that vanishes appeared at least once and can be caught by comparing consecutive turns. At roughly three proposals per run, expect a measure to go missing in something like one run in seven.

It is not only a narrative problem. The metrics step charges political capital per measure in flight, so a measure that silently drops out **stops costing anything**, and a run that loses one looks slightly better-resourced than it should.

One instance reached the story: on the A2 branch the European AI Assurance Directorate — the measure the reader chooses at turn 1 — never enters the portfolio at any turn from 2 to 9. It carries normally on V2 and P2, which choose the same option. Recorded in `scenarios/europe-2032/story/README.md` under known faults.

## The framework already solved this once, for a different kind of state

This is the part a future session should start from.

`docs/ARCHITECTURE.md`, *Actor Statement Ledgers*: statements are authored per actor, tiered, and **carried forward verbatim by Python**. "Actors never restate their statements, so silent drift is structurally impossible." The same section records why: two earlier designs failed in measured runs, goal re-derivation from prose and rules evolution with mandatory re-emission, where "format pressure became drift".

The portfolio is a third instance of the same design error, in the same actor output, in the same turn. In any europe-2032 run you can read both: `turn-XX/2-actors/eu-statements.md` is stable across turns because Python owns it; the `## Portfolio` section of `turn-XX/2-actors/eu.md` loses entries because the model owns it.

`docs/proposals/adjustable-statements.md` states the principle that decides this proposal: **silence means persistence**. And ARCHITECTURE draws the conclusion already, before anyone noticed the portfolio has the problem: "anything a scenario needs an actor to hold across a resume or a branch is safer as a statement than as prose the actor restates each turn."

## The three options considered

1. **Accept it.** Defensible for the already-built europe-2032 tree, where the alternative is discarding 420 committed runs. Not defensible as a framework property.
2. **A stronger but still cheap model.** Johan's bound: twice the cost is acceptable, five times is not. Plausible at these rates — 0.6% and 4.6% are the kind of thing a better model may absorb. Two cautions: it reduces the rate of a *silent* failure rather than making it visible, and `docs/MODEL_TESTING.md` currently has one "Recommended" verdict and "Avoid" for everything else, so a switch means redoing that testing. Cheap to evaluate now: `check_ledger.py` needs no framework change, so a twenty-run batch on a candidate gives a comparable number for a few dollars.
3. **Python execution around phases.** Johan's framing: the framework should support scenario-supplied scripts that run before or after phases, able to signal an invalid reply or produce output for the next phase. Explicitly not one-off code for a single scenario.

## Where the discussion landed

Johan's constraint, in his words: *"I still want 'lean into LLM' as a basic principle, so using Python for rules that may change is wrong. But using it for verifying that the ledger is valid is a proper case; that's constitution, not flexible rules."*

And his correction to an over-general claim of mine, which is the load-bearing design point: **measures carried forward is a special case.** It appears in some scenarios and not most. Other scenarios will need to carry other things — alliances, permanent changes to the world, descriptions of particular world or actor elements. So the general mechanism is not "ledger checking". It is custody of **declared persistent state**, where each scenario declares what persists and the framework guarantees it.

The constitution is where such declarations already live. europe-2032's invariant 4 — "The American posture, once elected, is standing … It may not be dropped, reinterpreted or replaced by a different posture later in the run" — is exactly this category, and today it is enforced only by an LLM referee. `design-notes.md` records that it took two failed rounds and a Jinja gate to make hold, under the heading lesson *"prohibitions don't hold"*.

## Open design questions

- **Custody or verification?** Two different fixes. *Custody* moves the portfolio to the statement-ledger model: Python carries it, the actor proposes deltas, silence means persistence. That makes the defect structurally impossible rather than detected, and it is the approach the framework has already validated. *Verification* keeps re-emission and adds a check that re-asks. Custody is stronger; verification is a smaller change and is the only option for state the model must be free to reshape.
- **If hooks, key them to declarations rather than phases.** A check belongs to an invariant, not to a step: "the posture is standing" wants checking after the notepad, "portfolio entries persist" after the actor step. Phase-keyed hooks make every scenario write its own dispatch; declaration-keyed hooks let the scenario author write the assertion and the framework decide when to run it.
- **A hook must be able to re-ask, not only to reject.** The precedent is the metrics repair at `orchestrator.py:1690–1745`, which detects an omitted metric, re-asks once with a targeted prompt, and writes the outcome to `4-metrics-metadata.json` whether or not the repair worked. Rejection alone stalls a run; "these three are missing, account for them" produces a turn where the world either restores them or says why they are gone.
- **What the scenario declares, and in what file.** Statements are declared in the actor file. A portfolio is closer to world state. Constitution invariants are prose. A future design has to say where a persistence declaration is authored and how it names what it covers.
- **Migration cost.** Changing custody changes run behaviour, so runs made after it are not strictly comparable with the 570 already committed.

## Reproducing the numbers

```
python scripts/check_ledger.py scenarios/europe-2032 --filter batch=stats-20260908
python scripts/check_ledger.py scenarios/europe-2032          # every run in the scenario
```

Name matching is deliberately loose — the Game Master paraphrases measure names between turns — so a reported miss means no portfolio entry shared a distinctive word with the proposal. Before believing any of it, read the script: the first version of this measurement conflated never-entered with vanished and checked only the following turn, and reported a materially worse picture than the corrected one above.
