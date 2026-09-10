# Proposal: the store, part two — world scope, reporting, and metrics

Status: **implemented** on `store-v2-world-scope-and-metrics`, 2026-09-10, in four steps (selector/reducers; world scope + JSON; reporting/range/adjust; metrics adapter). Part one *is* implemented and running; this is what it becomes.

Read `persistent-state-custody.md` first for why the store exists, what the old design cost, and which arguments were already settled. Read the *Declared Persistent State: the Store* section of `../ARCHITECTURE.md` for what is live today. This file is written to be a sufficient brief on its own for a session that has none of the conversation behind it.

## Where part one landed

Built and committed on `generalized-ledger`, 2026-09-10, twelve commits. `scenario_lab/store.py` holds declared persistent state: a scenario declares tables in `scenario.yaml`, each column declaring an `owner` (`system` / `actor` / `derived`) and a type; actors emit `add` / `update` / `delete` commands under one `## Store changes` header and never restate what they hold. europe-2032's measure portfolio runs on it. 940 tests pass.

Six verification runs, 4–8 turns each, took 85 commands across 35 turns. No entry was ever lost — that part is structural rather than lucky, and it is the defect the whole thing was built to remove. What the runs actually found is recorded in `../../scenarios/europe-2032/design-notes.md`; the short version is that four separate bugs surfaced, three of them in the hand-rolled command grammar, and the fourth was a semantic boundary nobody had written down.

That distribution matters for the decisions below: **the custody model held; the text parser was where the cost was.**

## What is wrong with part one

**A store only actors can write to is not a generalised store.** `scope: world` is rejected at load today. That was an honest stopgap — a world table needs a writer and the only candidate also produces the narrative and the metrics JSON — but it was then defended as though it were a principle, and it is not one. Alliances, treaty registers, standing conditions and permanent changes to the world are not owned by any actor, and they are exactly the state the original proposal said the mechanism was for.

**The read surface is six near-duplicate methods.** `sum`, `min`, `max`, `mean`, `count`, `rows`, each taking a table and a column and a filter. Adding column selection to `rows` would have meant a seventh decision about argument order.

**Rows render every column.** Measured on turn 8 of `run-20260910-011256`: the ten-column table is ~570 tokens against ~170 for the four columns a reader of the charge actually needs. It is pennies in money and real in attention — and it caused a live incident. The actor saw a `cost_per_turn` column, copied it into a command, and six measures were rejected in one eight-turn run before that was made a note rather than a refusal.

## The design

### 1. `scope: world`, and a writer for it

A world table belongs to the run, not to an actor. It is written by the Game Master step, read by every step, and persisted with everything else.

This is the enabling change: `reporting_required`, `range` and metrics all depend on it, and none of them is worth building without it.

### 2. All writes are JSON

**Decided: yes, and this is the most consequential decision in the document.**

Part one's commands are a hand-rolled markdown grammar, and three of the four bugs the verification runs found were in it: a numbered list was unreadable, a delete carrying its reason inline lost the whole command, `delete measures M7, M8` deleted M7 and silently kept M8. Each fix was correct and each was a patch against a model quirk rather than a contract.

A JSON write form replaces that with a schema, and — the decisive part — makes the store eligible for provider-native structured outputs. `llm.structured_outputs` (`auto` | `true` | `false`) and `schemas.py` already exist for the events step, with a documented fallback when a model does not support it. The events step's experience is the precedent: when structured output is active it "skips text parsing and the format-fix retry entirely".

Shape, one block per writing step:

```json
{"store": [
  {"op": "add", "table": "measures",
   "fields": {"name": "Compute build-out", "category": 4, "size": "large", "finish_turn": 7},
   "grounds": "the access denial in turn 3"},
  {"op": "update", "table": "measures", "id": "M2", "fields": {"finish_turn": 5}},
  {"op": "delete", "table": "measures", "id": "M1", "grounds": "publicly defeated"}
]}
```

Two things to preserve from part one, both learned the hard way:

- **Per-entry rejection, not per-block.** One malformed entry is rejected with a reason and the rest apply, exactly as the events step skips one bad candidate and as the current command loop does. A whole turn's state changes must not be lost to one bad field. This is the one real cost of moving to JSON and it is fully mitigable.
- **An absent block is a fault, not a declaration.** The section-missing check is what makes the larger half of the original defect detectable at all. It survives the format change.

Forgiving normalisation on write stays (`**Large**` → `large`, `turn 7` → `7`). A model that writes JSON still writes `"size": "Large"`.

### 3. `reporting_required`, with a re-ask

A flag per table or per column. Default off: **omitted means unchanged**, which is the silence-means-persistence rule the whole store rests on. Set, it means the writer must report the value every turn and an omission is a fault.

This unifies the two custody models already in the codebase. Statements and measures are silence-means-persistence; metrics are silence-means-omission-fault. Those are two settings of one dial, not two mechanisms.

**It must re-ask, not only warn.** `orchestrator.py:_complete_metrics` today detects an omitted metric, re-asks once with a targeted prompt, records the outcome in `4-metrics-metadata.json` whether or not the repair worked, and writes carried-forward values explicitly so no artifact has a missing key. A flag that only warns would regress metrics when they move onto the store.

Building it here also funds the hook part one left undesigned. One re-ask mechanism serves two triggers: a required report that is absent, and a declared write block that is absent.

### 4. `range` on a column

`{min: 0, max: 100}`, or `range: [0, 100]`.

**An open decision, and it must be made deliberately:** two out-of-bounds policies already exist in the codebase and they disagree. `Metrics.update_from_dict` (`models.py:77`) clamps silently. `apply_initial_state` treats out-of-bounds as a hard error, because "a draw that names an unknown metric or lands out of bounds indicates a broken sampler, and clamping it would bias the batch while hiding the cause."

Recommendation: a per-column policy, defaulting to **clamp-and-record** for metrics — the established behaviour, but written into the turn's changelog rather than happening nowhere. A silent clamp is the quiet wrongness this project usually refuses; a clamp that leaves a trace is not.

### 5. `adjust` — submit the change, not the new value

**Recommended, and it is the highest-value item here after world scope.**

Today a metrics response carries levels: `{"eu_political_capital": 43}`. The rules that produce that number are written as deltas — rule 6 is a list of terms, `−3` per large measure, `−1` for the priority, `+2 to +5` on finishing. So the model computes a sum of deltas, adds it to a level, and reports the level. The addition is the step it does worst, and it is the last piece of arithmetic still on the model's side.

An `adjust` form moves it to Python:

```json
{"op": "update", "table": "metrics", "id": "eu_political_capital",
 "adjust": -9, "grounds": "portfolio charge 8, priority 1"}
```

`design-notes.md` records the precise shape of the failure this addresses: the sovereignty line "ended at a *delta* while the JSON carried a *level*, so nothing connected the two ends." That was patched by making the prose line end at a level. `adjust` removes the second end entirely.

Both forms stay available. Some values are set rather than adjusted — a posture read off an event record, a level the narrative establishes.

Two requirements:

- **The artifact records prior value, the adjustment, and the result.** A wrong delta compounds forever, where a wrong absolute value self-corrects next turn. That is the real risk of this form and the only defence is that the trail is legible.
- **Clamping interacts with it.** `adjust: -5` against a value of 3 with a floor of 0 loses 2, and the loss must be recorded, not absorbed.

### 6. One selector, many reducers

Replace the six read methods with `rows()` plus reducers:

```
store.rows('measures', status='running').count
store.rows('measures', ['cost_per_turn'], status='running').sum
store.rows('measures', ['cost_per_turn'], status='running').max
store.rows('measures', ['id', 'name', 'cost_per_turn'], status='running')
```

A bare selector renders the markdown table; a reduced one yields a number. So "render the itemised rows beside any total" — the discipline the charge depends on, because the total cannot be known without summing it — becomes writing the same selector twice, once bare and once reduced.

Verified to work under `SandboxedEnvironment`: properties resolve, `__str__` renders the table, underscored attributes stay blocked.

Rules:

- **Reduce only when exactly one column is selected.** `rows('measures', ['cost_per_turn', 'category']).sum` has no defensible answer and must be a validation error, not a guess.
- Reducers are `count`, `sum`, `min`, `max`, `mean`. No joins, no arithmetic between reducers. The closed-surface argument from part one is unchanged: every extension is individually reasonable and collectively a query language with its own bugs, and a wrong aggregate looks exactly as authoritative as a right one.
- An empty `mean`/`min`/`max` renders `(none)`, not `0`. These values are read as prose; an authoritative-looking zero where there is no answer is worse than a visible gap.
- Column selection also fixes the token and attention cost above, and the charge should select `['id', 'name', 'cost_per_turn']` while "finishing this turn" keeps the wide row — the Game Master prices the completion bonus from `targeted_effect`, and since part one moved those fields out of the actor's prose the store is the only place that text now lives.

### 7. Metrics as a world table

The point of the previous six.

```yaml
store:
  metrics:
    scope: world
    reporting_required: true
    write_form: json
    columns:
      id:    {owner: system, type: text}
      value: {owner: world,  type: number, range: [0, 100], on_out_of_range: clamp}
```

The judgement stays with the LLM. The store holds values it can be trusted about, and `metric-rules.md` reads them into prose the model still judges:

> `openweight_capability` should be around half-way between {{ store.rows('metrics', ['value'], id='openweight_capability').max }} and {{ store.rows('metrics', ['value'], id='ai_capability').max }}

That is the division the project wants and `AGENTS.md` rule 1 requires: Python for values, the LLM for rules and judgement. It is what rule 6 already does for the portfolio charge, generalised.

**Behind an adapter.** `scenario.metrics` keeps its interface, backed by the store. Eleven modules in the package read metrics, plus the analysis tooling, event eligibility gates and termination conditions through `build_expression_env`, plus 570 committed runs of artifacts. The adapter is what contains that.

**The metrics step keeps emitting JSON**, which after decision 2 is simply the store's write form. No new output format for the step `design-notes.md` already calls saturated.

## Open questions

- **Reproducibility.** With metrics in the store, `metric-rules.md` renders against store state, so reproducing an old turn means reproducing the state it rendered against. This was already open in part one; metrics sharpen it. `config.json` plus per-turn store JSON should suffice, but it should be verified rather than assumed.
- **`range` policy**, above. Clamp-and-record is the recommendation, not a decision.
- **Whether `adjust` should carry its terms** rather than a single number — `{"adjust": -9, "terms": ["Gigafactories -3", "priority -1"]}`. The notepad line already does this in prose. Attractive, and deliberately not specified here: build the single number first and see whether the prose line still earns its place.
- **Does any of this change what a run means?** It changes run behaviour, so runs made after it are not comparable with those before. `config.json` records the resolved schema so the populations can be told apart.

## Sequence

1. **Selector and reducers, with column selection.** Self-contained, no scope change, needed regardless. Narrow europe-2032's three call sites while doing it.
2. **`scope: world` and the Game Master writer, with JSON as the write form.** The enabling change. Convert the actor path to JSON in the same step so there is one write form and not two.
3. **`reporting_required` with re-ask, and `range`.**
4. **Metrics onto the store, behind an adapter.**

## What to measure

Every mechanism in this repository that grew informally had to be measured and clamped later, so:

- `scripts/check_portfolio_drift.py --store` and `--charges` already exist and are the pattern. `--charges` compares the Game Master's itemised charge line against what the store computes, and reports two things separately: whether the terms are the measures actually in flight, and whether the line adds up to its own total.
- Baseline as of 2026-09-10, after part one's corrections: the line adds up in 15 of 15, and its terms match in 13 of 15. For contrast, `design-notes.md` records the sovereignty line's terms summing to its stated total in 51–70% of turns, where nothing supplies a figure to anchor against.
- **Step 4's whole justification is arithmetic quality**, so it needs a before-and-after. Rule 2's `openweight_capability` midpoint is the clean case: it is currently a computation the Game Master performs in prose, and it is exactly what a rendered term would replace.
- Step 2 should be measured for parse failures, not just correctness. The claim behind JSON is that structured outputs remove a class of bug; the four found in part one's grammar are the baseline it should be checked against.

## Which base this assumes

**Part one's code lives on `generalized-ledger` and nowhere else.** `main` carries the part-one *proposal* and none of the implementation: no `scenario_lab/store.py`, no wiring through loader, prompts, orchestrator, output, resume and validator, no europe-2032 migration, no `scripts/check_portfolio_drift.py`, none of the 940 tests. As of 2026-09-10 the branch is fourteen commits ahead of `main` and `main` is zero ahead of it.

This proposal is written as an extension of part one, and branching from `generalized-ledger` is the recommended base. Only one piece of part one is actually *replaced* by the design above — the markdown command parser, superseded by decision 2. Everything else is additive: world scope, the reporting flag, ranges, `adjust` and the chained read surface all sit on top of machinery that already exists and is tested.

Starting from `main` instead means rebuilding part one to reach the point this document starts from. That is a defensible choice if the intent is a clean design rather than an accreted one, but it should be a decision rather than a side effect of picking a branch, and the list below is what must not be lost either way.

## What to salvage if rebuilding from scratch

None of this is design; it is knowledge that cost measured runs to acquire, and rewriting from the design alone would relearn it the same way.

- **`tests/test_store.py` and `tests/test_store_integration.py`.** Several tests exist because of a specific incident, and each names it in its docstring. The four that matter most: a two-id delete that kept the second record; an unwritable column costing the whole command; a trailing "No other changes." reading as a fault; a turn column accepting a non-positive turn. Under a JSON write form the parsing tests change shape, but every *semantic* test survives unchanged.
- **The normalisation rules.** Models write `Large`, `` `large` `` and `**large**` for one value, and `finishes on turn 7` for the number 7. Forgiving on write, strict in store, and loud rejection for what will not normalise. JSON does not remove this: a model writing JSON still writes `"size": "Large"`.
- **The per-turn transaction.** `Store.begin_turn` restores a pre-turn snapshot before applying, so a turn re-run under `constitutional_enforcement.max_attempts` replaces its own previous application instead of appending. Without it a turn executed twice doubles a portfolio.
- **Derivation as lookup only**, one step deep, with a map over an enum required to cover every value.
- **Ids assigned by Python, never names as keys.** `check_portfolio_drift.py` needs a stopword list and a fuzzy matcher because the Game Master paraphrases names between turns.
- **The two audit modes and their baselines**, which are the only way to tell an improvement from noise.
- **The europe-2032 prompt corrections**, which are not in the framework at all and are easy to lose: the finishing-turn boundary, the priority charged on top of the framework's figure, `## New measure` as prose rather than a form, and the four computed columns named as not-yours-to-write.

## For a fresh session

Everything needed is in this file, `persistent-state-custody.md`, the *Declared Persistent State* section of `../ARCHITECTURE.md`, and the store section of `../SCENARIO_TECHNICAL_REFERENCE.md` — the last two on `generalized-ledger` only.

Start at step 1. It is independent of the rest, touches only the read surface, and can be measured against the six existing runs without touching custody.
