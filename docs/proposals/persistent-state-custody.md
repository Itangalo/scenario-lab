# Proposal: who holds persistent state

Status: **built, 2026-09-10**, opened 2026-09-09. The mechanism below is implemented as `scenario_lab/store.py` and europe-2032's measure portfolio runs on it. Three things named here are **not** built and remain open: the re-ask hook, tracking of unresolved deferrals, and moving statements into the store. Everything below is kept as written — it is the design record, and the measurement it reports is of the design that was replaced.

What changed from the design as written here:

- **It is called the `store`, not the `ledger`.** The proposal made the name conditional on statements moving in; they have not, so "ledger" stays with statements. `scripts/check_ledger.py` is now `scripts/check_portfolio_drift.py`, and it grew a `--store` mode that audits the new design instead of the old one.
- **`when_past` is `when_reached`,** because europe-2032's rule 10 says a measure is finished when the current turn *reaches* its finishing turn, and a column named for "past" that means ">=" is a trap.
- **`scope: world` is rejected at load** rather than accepted. It needs a writer, the only candidate is the step that also writes the narrative and the metrics JSON, and half-wiring it would let a scenario depend on a table nothing writes to.
- **Reads are rendered for the metrics step only.** The rules step, which rewrites the rule set from its own output, is given the source. Handing it totals would make it write those totals back as the rule. The validator warns when a scenario pairs store expressions with live rule evolution.
- **A branch inherits by value.** The open question is answered by the existing implementation: `create_branch` copies the turn directories wholesale.
- **Category is an `integer`, not an `enum` of 1–10,** in europe-2032. The prompt teaches the actor to write `Category: 6 (Preparedness and resilience)`, and an enum would reject that — losing a measure to punctuation is the failure this mechanism exists to remove.

See the *Declared Persistent State: the Store* section of `../ARCHITECTURE.md` for what was built.

Out of scope here: whether to re-run any europe-2032 simulations because of this. That is a separate decision.

## The defect

An actor's measure portfolio is not held by the framework. The actor re-emits it in its own output every turn, so an entry survives only if the model remembers to write it again. Measured with `scripts/check_portfolio_drift.py` over the 150-run statistics batch (unpinned, fresh initial draws, the cleanest sample available):

| | count | share |
|---|---|---|
| measures proposed | 1 481 | |
| entered the portfolio at some later turn | 1 386 | 93.6% |
| never entered, run states a reason | 29 | 2.0% |
| **never entered, no reason stated** | **66** | **4.5%** |

| | count | share |
|---|---|---|
| measure-turn transitions | 5 626 | |
| carried forward | 4 733 | 84.1% |
| left with a stated cause (finished or cancelled) | 859 | 15.3% |
| **vanished, no stated cause** | **34** | **0.6%** |

The 42 story path runs give 7.8% and 0.8% for the two unexplained rates — worse, but they are pinned and a smaller sample, so weight the batch.

**These figures were corrected on 2026-09-09 and the first version of them was understated.** `parse_actor_turn` treated a `###` sub-heading as the end of the `## New measure` section, so a measure whose name was written that way was invisible to the instrument – indistinguishable from a turn where the actor proposed nothing. The proposal originally recorded 1 391 proposals and 64 unexplained non-entries (4.6%); the true counts are 1 481 and 66 (4.5%). The rates barely moved and every conclusion below stands, but the absolute counts were low by about 6%, and 17 turns of this batch are *still* unreadable and excluded from the denominator. The transitions half of the table was unaffected. See `tests/test_actor_parsing.py`.

Never-entering is the larger failure and the worse one: a measure that never arrives is invisible from the first moment, while one that vanishes appeared at least once and can be caught by comparing consecutive turns. At roughly three proposals per run, expect a measure to go missing in something like one run in seven.

It is not only a narrative problem. The metrics step charges political capital per measure in flight, so a measure that silently drops out **stops costing anything**, and a run that loses one looks slightly better-resourced than it should.

There is a third failure mode the table above splits out but does not name: **the deferral that never resolves**. The 29 non-entries with a stated reason are, by definition, proposals the run explained away at the time and then never returned to. That is 2.0% on top of the 4.5%, so the honest figure for "the actor proposed a measure and it never became one" is 95 of 1 481, or 6.4%.

One instance reached the story, and it is of that third kind: on the A2 branch the European AI Assurance Directorate — the measure the reader chooses at turn 1 — is deferred in the turn-1 world state with a stated reason, and then never mentioned again from turn 2 to 9 except once, and never enters the portfolio. Recorded in `scenarios/europe-2032/story/README.md` under known faults. It matters for the design because a custody mechanism would not have caught it: nothing was lost from a ledger, and the deferral was legitimate when made. Only something tracking open proposals across turns would notice that one was never resolved.

## The framework already solved this once, for a different kind of state

This is the part a future session should start from.

`docs/ARCHITECTURE.md`, *Actor Statement Ledgers*: statements are authored per actor, tiered, and **carried forward verbatim by Python**. "Actors never restate their statements, so silent drift is structurally impossible." The same section records why: two earlier designs failed in measured runs, goal re-derivation from prose and rules evolution with mandatory re-emission, where "format pressure became drift".

The portfolio is a third instance of the same design error, in the same actor output, in the same turn. In any europe-2032 run you can read both: `turn-XX/2-actors/eu-statements.md` is stable across turns because Python owns it; the `## Portfolio` section of `turn-XX/2-actors/eu.md` loses entries because the model owns it.

`docs/proposals/adjustable-statements.md` states the principle that decides this proposal: **silence means persistence**. And ARCHITECTURE draws the conclusion already, before anyone noticed the portfolio has the problem: "anything a scenario needs an actor to hold across a resume or a branch is safer as a statement than as prose the actor restates each turn."

## The three options considered

1. **Accept it.** Defensible for the already-built europe-2032 tree, where the alternative is discarding 420 committed runs. Not defensible as a framework property.
2. **A stronger but still cheap model.** Johan's bound: twice the cost is acceptable, five times is not. Plausible at these rates — 0.6% and 4.5% are the kind of thing a better model may absorb. Two cautions: it reduces the rate of a *silent* failure rather than making it visible, and `docs/MODEL_TESTING.md` currently has one "Recommended" verdict and "Avoid" for everything else, so a switch means redoing that testing. Cheap to evaluate now: `check_portfolio_drift.py` needs no framework change, so a twenty-run batch on a candidate gives a comparable number for a few dollars.
3. **Python execution around phases.** Johan's framing: the framework should support scenario-supplied scripts that run before or after phases, able to signal an invalid reply or produce output for the next phase. Explicitly not one-off code for a single scenario.

## Where the discussion landed

Johan's constraint, in his words: *"I still want 'lean into LLM' as a basic principle, so using Python for rules that may change is wrong. But using it for verifying that the ledger is valid is a proper case; that's constitution, not flexible rules."*

And his correction to an over-general claim of mine, which is the load-bearing design point: **measures carried forward is a special case.** It appears in some scenarios and not most. Other scenarios will need to carry other things — alliances, permanent changes to the world, descriptions of particular world or actor elements. So the general mechanism is not "ledger checking". It is custody of **declared persistent state**, where each scenario declares what persists and the framework guarantees it.

The constitution is where such declarations already live. europe-2032's invariant 4 — "The American posture, once elected, is standing … It may not be dropped, reinterpreted or replaced by a different posture later in the run" — is exactly this category, and today it is enforced only by an LLM referee. `design-notes.md` records that it took two failed rounds and a Jinja gate to make hold, under the heading lesson *"prohibitions don't hold"*.

## The shape it should take (settled 2026-09-09)

Johan's proposal, and the design conversation around it. Nothing here is implemented; this section exists so a clean session can start building rather than re-deriving.

The idea: a generalised store of records, like a set of small CSV tables, with (a) commands the actor emits to add, update and delete records, (b) a read syntax usable inside `metric-rules.md`, and (c) a few aggregations over the records – sum, min, max, mean, count – optionally filtered.

The motivation is Johan's, and it reframes the problem: `metric-rules.md` is overloaded, and much of what it asks for is arithmetic rather than judgement. Rule 6 alone asks the Game Master to sum a portfolio, apply a per-size charge to each entry, check a gate at 40, compare two metrics, charge a priority, handle finishes and abandonments, and price events by origin – in the same call where it writes the narrative. Using an LLM for that is both the wrong use of its power and a way of reducing it, by making it attend to too many things at once. The measured consequence is in `../../scenarios/europe-2032/design-notes.md`: the sovereignty line's own terms sum to the total it states in 51-70% of turns, and three attempts to fix that from the prompt side produced the conclusion that "prohibition is not the same instrument as reformulation, and this step appears to be saturated with the first".

The payoff is that a rule stays readable and stays true. `metric-rules.md` can say "Reduce political capital by {{ ledger.sum('measures', 'cost_per_turn') }}" and remain the single place the physics is written down, while the arithmetic happens in Python before the model ever sees the prompt.

### Reads render before the model sees them; use the Jinja that is already there

`metric-rules.md` is currently read as raw text and injected as a context variable (`prompts.py:85`); its own content is never rendered. So the read syntax needs a rendering pass that does not exist yet – and it should be the `SandboxedEnvironment` already at `prompts.py:55` rather than a second, parallel interpolation syntax. That inherits the sandbox, Jinja's filters, and the validator's existing undefined-variable check, and removes a bespoke parser from the design. Checked before proposing it: no scenario's `metric-rules.md` or `events.md` contains `{{`, `{%` or `{#` today, so nothing collides.

Keep the query surface closed and small: `sum`, `min`, `max`, `mean`, `count`, one equality filter, no joins, no arithmetic between aggregates. Every one of those extensions is individually reasonable and together they are a query language with its own bugs, and a wrong aggregate looks exactly as authoritative as a right one. Give it a `--self-test` from the first commit, in the pattern `story/check_tree.py` already uses.

**Render the itemised rows next to any total.** `design-notes.md` records that the portfolio charge binds *because* "the total cannot be known without summing it". Handing over a pre-computed number risks the Game Master ceasing to attend to the portfolio at all, so the narrative drifts free of the ledger rather than the reverse. Show the rows and the sum.

### Writes go under a declared header; reads may appear anywhere

Reads have no side effects, so they can sit wherever the prose needs them. Writes must not, for three reasons in order of weight:

- **Atomicity under the referee loop.** `constitutional_enforcement.max_attempts: 4` means a turn can be re-run up to four times. Commands scattered through prose mutate state partially on a partial re-emission, leaving a portfolio that is half of attempt 2 and half of attempt 3. A declared section can be treated as the complete declaration for the turn and applied as one transaction – replace, never append.
- **A missing section is detectable; a missing inline command is not.** That is exactly the never-entered failure, the larger half of this defect at 4.5%. Require the section even when it says `No changes.`, as statements already require `No statement changes.`, and absence becomes a fault a hook can re-ask about.
- **Accidental mutation.** The Game Master narrates what actors say and quotes rule text. Free-floating syntax means any quoted string containing the pattern writes to state. The repository already runs a sandboxed Jinja environment because of a real template-injection issue; a second, looser surface is not worth it.

The counter-argument for inline commands – that a command written beside its justification is more accurate – is better served by carrying the justification *in* the command, the way statement proposals carry indented `Trigger:` and `Grounds:` lines.

### The schema is declared in `scenario.yaml`, and declares provenance per column

The most useful thing a schema can do here is say **who owns each column**, because that is what turns a rule from an instruction into an invariant. Rule 10 currently asks that a measure's line "is copied forward in the portfolio, unchanged. Three things can move it. Nothing moves it silently" – a rule the model obeys by remembering, and measurably does not. With ownership declared, `started_turn` simply cannot be rewritten.

Three provenances: `actor` (declared in a command; a judgement), `system` (stamped by the framework), `derived` (computed from a declared map).

```yaml
ledger:
  measures:
    scope: actor            # actor | world
    columns:
      id:            {owner: system,  type: text}
      name:          {owner: actor,   type: text, required: true}
      category:      {owner: actor,   type: enum, values: [1,2,3,4,5,6,7,8,9]}
      size:          {owner: actor,   type: enum, values: [large, small]}
      started_turn:  {owner: system,  type: turn}
      finish_turn:   {owner: actor,   type: turn, required: true}
      cost_per_turn: {owner: derived, from: size, map: {large: 3, small: 2}}
      status:        {owner: derived, from: finish_turn, when_past: finished, else: running}
```

- **Python assigns ids; the actor never keys on names.** `scripts/check_portfolio_drift.py` carries a `STOPWORDS` list and a `words()` fuzzy matcher with the comment "the Game Master paraphrases names", and the 2026-09-09 benchmark shows one measure appearing as "EU AI Incident Response Corps", "Establish the EU AI Incident Response Corps with Pub…" and "European AI Incident Response Corps". Names are not keys. `storage-add` gets a framework-assigned id back, the id is rendered beside every row in the prompt, and later commands address it. The fuzzy matcher then audits history instead of running the system.
- **Types few, forgiving on write, strict in store.** `integer`, `number`, `text`, `turn`, `enum`. Normalise on write – lowercase, strip backticks and asterisks – because models write `Large`, `` `large` `` and `**large**`. The precedent is `structured_outputs`, where "YAML booleans are normalized to the canonical strings at load time". What will not normalise is rejected loudly into the turn's changelog.
- **Derivation is lookup only.** A map is data, not logic, and it keeps rule 6's numbers in scenario config where they are readable and versioned rather than in Python. No expressions, no conditionals beyond a single map, no cross-table joins. When a scenario wants more than a lookup, that is the signal the thing is judgement and belongs to the LLM.
- **Validate references *to* the schema, not only the schema.** An undefined Jinja variable renders as empty text, so a mistyped column silently zeroes an arithmetic term and the rule stops applying with nothing recording it. The validator already warns that undefined variables "render as empty text" and that a `model_limits` key matching no route will never apply; the same warning is needed for a ledger column named in a template and absent from the schema. The cautionary case is `openweight_frontier_release`, where "the correct instruction was written, reviewed, and never sent to anything".
- **Record the resolved schema in `config.json`,** beside `patches` and for the same reason `reasoning_effort` is now recorded: a schema change is a physics change, and two batches under different schemas are not comparable.
- **Keep it closed.** The actor may not create tables or columns at runtime, and an unknown column in a command is a rejection rather than an addition – the rule the patch loader already enforces, where "a typo'd key must not silently become an addition". Every mechanism here that grew informally had to be measured and clamped later.

### Naming, and whether statements move in

**Call it the ledger only if statements move into it.** "Ledger" is already overloaded three ways: `ARCHITECTURE.md` has the actor *statement ledger*, `story/README.md` says the portfolio "is not a reliable ledger", and `check_portfolio_drift.py` measures neither. If statements become one table among several, that overload collapses into one coherent meaning. If they stay separate, two things called ledger is worse than picking another word, and "store" is the honest fallback. Either way `check_portfolio_drift.py` wants renaming when this lands, since it exists to measure drift the design makes impossible.

**Statements should move in eventually, but not first, and not as part of the same change.** They are the same shape – declared persistent state, mutated by structured commands, carried by Python – and ARCHITECTURE already invites it. But they carry semantics a generic store would flatten: the tier system, the gated relevance check where a `commitment` or `identity` change must name a triggering development and a referee demands a verbatim quote, and world pricing, where an accepted change is narrated as a public event. So the ledger needs **per-table mutation policy** from the first design, or statements cannot move without losing what makes them work.

Sequence it: build the ledger for the state that has no custody at all, prove it on the portfolio, then move statements if the tier and relevance semantics survive as table policy. Statements are the one piece of persistent state in this system that demonstrably does not drift, and rebuilding a working mechanism for architectural tidiness is how it gets lost – `rule_evolution` is frozen for precisely that shape of reason. The unification is worth having and is not urgent; the portfolio fix is.

## Open design questions

- **Custody or verification?** Settled as custody for the portfolio, but the question stays open for state the model must be free to reshape. Two different fixes. *Custody* moves the portfolio to the statement-ledger model: Python carries it, the actor proposes deltas, silence means persistence. That makes the defect structurally impossible rather than detected, and it is the approach the framework has already validated. *Verification* keeps re-emission and adds a check that re-asks. Custody is stronger; verification is a smaller change and is the only option for state the model must be free to reshape.
- **If hooks, key them to declarations rather than phases.** A check belongs to an invariant, not to a step: "the posture is standing" wants checking after the notepad, "portfolio entries persist" after the actor step. Phase-keyed hooks make every scenario write its own dispatch; declaration-keyed hooks let the scenario author write the assertion and the framework decide when to run it.
- **A hook must be able to re-ask, not only to reject.** The precedent is the metrics repair at `orchestrator.py:1690–1745`, which detects an omitted metric, re-asks once with a targeted prompt, and writes the outcome to `4-metrics-metadata.json` whether or not the repair worked. Rejection alone stalls a run; "these three are missing, account for them" produces a turn where the world either restores them or says why they are gone.
- ~~**What the scenario declares, and in what file.**~~ Settled above: a `ledger:` block in `scenario.yaml`, one entry per table, columns declaring owner and type. Statements stay where they are for now.
- **Migration cost.** Changing custody changes run behaviour, so runs made after it are not strictly comparable with the 570 already committed.

## Still open after 2026-09-09

- **The re-ask hook is load-bearing and undesigned.** Custody protects what got into the ledger; it does nothing about a measure the actor describes in prose and never writes a command for. That is the never-entered failure, 4.5% and the larger half of the defect, and it needs the hook described above under *A hook must be able to re-ask*.
- **The unresolved deferral is untouched by any of this.** The A2 case in `../../scenarios/europe-2032/story/README.md`: a proposal correctly deferred with a stated reason, and never revisited. Nothing is lost from a ledger, so custody cannot see it. It needs tracking of open proposals across turns, which is a third mechanism.
- **Whether `metric-rules.md` should be rendered per turn at all.** Rendering it means the rules a run used are no longer a static file, and reproducing an old turn means reproducing the ledger state it rendered against. Probably fine, since `config.json` already records enough to rebuild, but it should be decided rather than discovered.
- **What happens on resume and branch.** Ledgers need restoring from the last completed turn exactly as statement ledgers and the notepad already are, and `branch` needs to decide whether a child inherits the parent's ledger by value or by reference.

## Reproducing the numbers

```
python scripts/check_portfolio_drift.py scenarios/europe-2032 --filter batch=stats-20260908
python scripts/check_portfolio_drift.py scenarios/europe-2032          # every run in the scenario
```

Name matching is deliberately loose — the Game Master paraphrases measure names between turns — so a reported miss means no portfolio entry shared a distinctive word with the proposal. Before believing any of it, read the script: the first version of this measurement conflated never-entered with vanished and checked only the following turn, and reported a materially worse picture than the corrected one above.
