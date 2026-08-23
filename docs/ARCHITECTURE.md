# Scenario Lab Architecture

This document serves as the "ground truth" for the Scenario Lab architecture. It describes how the system is intended to work and should be updated before adding new functionality.

## 1. Design Philosophy: Pure LLM Architecture

V4 represents a radical simplification from previous versions. Instead of complex Python game logic, **we lean into the LLM**.

- **LLMs handle ALL complexity:** Narrative generation, metric updates, rule interpretation, and event evaluation are all performed by the LLM.
- **Python is minimal orchestration:** The Python code is strictly for loading data, constructing prompts, calling APIs, and persisting results to files. It does *not* contain game rules or simulation logic.
- **No communication phases:** There are no complex multi-step communication protocols between actors.
- **No hybrid architecture:** We do not mix Python-based rules with LLM-based reasoning. The simulation is purely LLM-driven.
- **One simple turn loop:** The simulation proceeds in a linear sequence of steps for each turn.

## 2. Core Concepts

### Metrics
- **Definition:** Pure quantitative values representing the state of the world (e.g., `ai_capability`, `unemployment`, `public_sentiment`).
- **Structure:** Each metric has a unique ID, a value, min/max bounds, a unit, and optional reference points for interpretation.
- **Handling:** Metrics are passed to the LLM as JSON and updated by the LLM as JSON. The Python code only validates that values are within bounds (clamping if necessary).

### Metric Rules
- **Definition:** Quantitative rules describing how metrics change over time or in relation to each other.
- **Examples:** "ai_capability doubles every 6 months", "high unemployment decreases public_sentiment".
- **Evolution:** The LLM reviews and updates these rules *every turn* based on world events. This allows the "physics" of the simulation to evolve.
- **Guardrails:** Rule evolution can be constrained per scenario via `rule_evolution` config. Scenarios may freeze substantive rule changes through an early turn window and cap the number of allowed changes per turn. When a turn should not materially change the rules, the intended output is a version bump plus a changelog line stating `No material rule changes.`
- **Versioning:** Each rules update increments a version number (v1, v2, v3...) to track rule evolution over time.
- **Changelog:** All rule modifications require a structured changelog documenting:
  * **What changed** (Added/Modified/Removed rules)
  * **Motivation** (why the change is needed based on simulation state)
  * **Expected impact** (how this will affect future metrics)
- **Transparency:** Versioning and changelogs make rule evolution visible and debuggable across turns.

### World State
- **Definition:** A narrative description of what happened during the turn, plus a persistent summary of history.
- **Components:**
  * `narrative`: Detailed description of the *current* turn.
  * `historical_summary`: Concise summary of all *previous* turns.
- **Purpose:** It serves as the shared context for all actors in the next turn. There is no information asymmetry; all actors see the same world state.

### Actors
- **Definition:** Simulation participants (governments, organizations, companies) with defined goals and behaviors.
- **Statements:** Each actor holds a **statement ledger** – a list of what it stands for, wants, and is, tagged with a changeability tier: `position` (working stances, move with strategy), `commitment` (staked positions whose reversal costs something someone will collect), and `identity` (what the actor would have to stop being to drop). Absolutes live outside the ledger in `constitution.md`. See *Actor Statement Ledgers* below.
- **Actions:** Actors review their statements and describe actions each turn. These are descriptive text, not structured data.

### Events
- **Definition:** Exogenous happenings with probabilities and conditions.
- **Evaluation:** The LLM evaluates whether conditions are met and calculates probabilities. The Python orchestrator then "rolls the dice" to see if the event actually triggers.
- **Deterministic Dice:** The roll for each event is derived from a recorded run seed: `random.Random(f"{seed}:{turn}:{event_id}").random()`. This makes the dice deterministic given the seed and independent of evaluation order, so `resume` and `branch` reproduce identical rolls without saving RNG state. Note that this only makes the dice deterministic – the LLM outputs (probabilities, narrative, actor actions) remain nondeterministic.
- **Full Provenance:** Every candidate event the LLM returns is recorded in `turn-XX/1-event-evaluations.json` with its `id`, evaluated `probability`, the `roll`, a `triggered` flag, and any extra fields the LLM returned (for example reasoning). Invalid or unknown entries are recorded with a `skipped` field describing the reason. The legacy `turn-XX/1-events.json` still contains only the triggered events in their original shape.
- **Event Forcing (counterfactuals):** A branch may force or suppress specific events on its first executed turn via `event_overrides`. Forced events trigger regardless of probability/roll; suppressed events never trigger (suppression wins if an id is both forced and suppressed). Affected entries are marked `"forced": true` or `"suppressed": true` in `1-event-evaluations.json`.
- **Emergent Events (optional):** With `emergent_events.enabled: true` in `scenario.yaml`, the Game Master may additionally propose novel exogenous events that are *not* in `events.md` — up to `emergent_events.max_per_turn` per turn (default 1). Each proposal must carry an `id` starting with `emergent_`, a `probability`, `"emergent": true`, and a short `description`. Python applies guardrails only: it validates the shape, caps the probability at `emergent_events.max_probability` (default 0.35, recorded as `probability_capped_from` when applied), enforces the per-turn limit, and rolls the same seeded dice as for listed events. Triggered emergent events flow into the actor/rules/metrics prompts using their proposed description and are added to the run's occurred-events list; their evaluation records are marked `"emergent": true`. When the feature is disabled (the default), unknown event ids are skipped exactly as before. This is the mechanism for exploring futures the scenario author did not enumerate, while keeping full provenance.
- **Probability Sampling (optional):** `llm.probability_samples: N` (default 1) makes the events step elicit the candidate list N times instead of once. Per event id, the probability used for the dice is the mean across valid samples, counting samples where the event was absent as 0 (absence ≈ conditions judged not met). The evaluation record then includes `probability_samples` (the per-sample values), `samples_present`, and `n_samples`, so probability uncertainty is visible in the artifact. Samples that end in a parse failure are excluded from the denominator; if every sample fails, the turn records the usual parse-failure marker. Multi-sample elicitation also naturally down-weights one-off emergent proposals, since an emergent event appearing in only one of N samples gets its probability divided by N.

### Constitutional Constraints
- **Definition:** Invariant "must-hold" rules that the LLM must respect throughout the simulation.
- **Purpose:** Prevent unrealistic outcomes by enforcing fundamental constraints on how the world works.
- **Examples:**
  * Economic: "Budget cannot exceed revenue without explicit borrowing"
  * Regulatory: "New legislation requires minimum 1 turn from proposal to effect"
  * Organizational: "Agency capacity grows max 30% per turn organically"
  * Physical: "Compute/hardware has supply constraints"
- **Format:** Optional `constitution.md` file per scenario with 5-15 short, clear constraints.
- **Enforcement:** Lightweight LLM-based "referee" step that validates metrics updates against the constitution.
- **Fallback Policy:** Constitutional enforcement can be configured per scenario via `constitutional_enforcement`, including maximum referee attempts and whether unresolved violations should be accepted or fall back to the previous state.
- **Philosophy:** Maintains pure LLM architecture while preventing common failure modes (instant budgets, magical scaling, etc.).

## 3. System Architecture

### File Structure & Loading (`loader.py`)
- **`scenario.yaml`**: Configuration (time scale, actors, LLM settings, output language).
  * **LLM Settings:** Includes per-task model configuration (`events`, `actors`, `rules`, `metrics`, `summary`, `analysis`, `referee`).
  * **Token Budgets:** Supports global `llm.max_tokens` plus optional per-task overrides via `llm.max_tokens_by_task` (for example, higher cap for `rules` to reduce truncation).
  * **Structured Outputs:** Optional `llm.structured_outputs: auto | true | false` (default `auto`) controls provider-native structured outputs for the events step. YAML booleans are normalized to the canonical strings at load time.
  * **Probability Sampling:** Optional `llm.probability_samples` (integer ≥ 1, default 1) controls how many times the events step elicits candidate events per turn; probabilities are aggregated as described under Events above.
  * **Emergent Events Policy:** Optional `emergent_events` block (`enabled`, default false; `max_per_turn`, default 1; `max_probability`, default 0.35) lets the Game Master propose novel exogenous events not listed in `events.md`.
  * **Rule Evolution Policy:** Optional `rule_evolution.freeze_until_turn` and `rule_evolution.max_changes_per_turn` let scenarios make early rules effectively fixed and keep later rule edits small.
  * **Constitutional Enforcement Policy:** Optional `constitutional_enforcement.max_attempts` and `constitutional_enforcement.on_failure` tune how hard the referee gate is.
  * **Logging:** Optional `logging.llm_io` enables per-call LLM prompt/response transcripts. It can also be turned on per run with the `--log-llm-io` CLI flag.
  * **Run-time Config Fields:** `config.json` additionally records `random_seed` (the dice RNG seed for the run), `logging.llm_io`, and, for branch counterfactuals, `event_overrides: {"turn": N, "force": [...], "suppress": [...]}`. `random_seed` and `event_overrides` are set at run time rather than declared in `scenario.yaml`. When a run is given a starting-state draw, `config.json` also records `initial_state` (see Starting-State Draws below).
- **Markdown Resources**: `metrics.md`, `events.md`, `metric-rules.md`, `background/*.md`.
- **Optional Resources**:
  * `constitution.md`: Constitutional constraints (invariant rules) for the scenario.
- **Inheritance:** Scenarios can inherit from others via the `base` field in `scenario.yaml`.

### Actor Statement Ledgers (`statements.py`, `orchestrator.py`)

Every actor carries a ledger of statements that persists across turns and changes only through explicit, structured proposals. The mechanism exists because two earlier designs failed in measured runs: goal re-derivation from prose (actors re-invented their goals each turn, unrecorded) and rules evolution with mandatory re-emission (one rewrite per turn, always the rule nearest the action – format pressure became drift). The statements design removes the slot whose emptiness looks like an incomplete answer.

- **Storage:** Statements are authored per actor in `background/actors/<id>.md` under `### Statements`, one per bullet: `` - `statement_id` (tier): text ``. The loader rejects the old `### Initial goals` section with a pointing error rather than silently reading prose. The live ledger is carried forward **verbatim by Python**; actors never restate their statements, so silent drift is structurally impossible.
- **Tiers:** `position`, `commitment`, `identity`. The tier is defined by what the actor has *staked* on the statement, not by whether it was announced publicly – sunk investment, organizational culture and doctrine count as stakes. Tier semantics are scenario-authoring data; the machinery is framework code.
- **Proposal grammar:** An optional `## Statement changes` section in the actor output holds one proposal per bullet: `modify` (with full replacement text), `add`, `reclassify <id> to <tier>`, or `retire`, plus indented `- Trigger:` / `- Grounds:` lines. An absent section or the literal line `No statement changes.` means the ledger carries forward untouched.
- **Structural check (Python, formatting-only):** Unknown ids, invalid tiers, missing replacement text, identical-to-current text, and missing `Trigger:` on gated proposals are rejected with a recorded reason – mirroring how unknown event ids are skipped. Deliberately absent: any cap, budget, cooldown or counter. Rule evolution's `max_changes_per_turn: 1` behaved as a quota ("exactly one"), and nothing here recreates that shape.
- **Relevance check (LLM, gated tiers only):** A `commitment` or `identity` change must name a triggering development from this turn's inputs. A cheap referee model (`referee` route) answers one binary question per proposal: quote the passage the trigger refers to, then BEARS or UNRELATED on whether it bears on *this specific statement*. A verbatim quote plus BEARS applies the change; anything else rejects it with reasoning attached. The check deliberately stops at relevance and never judges merit – merit varies between referees and would re-import cross-run variance; merit is charged for in the world instead (below). Covered by the opt-in eval suite in `tests/evals/statement-relevance/`.
- **Tier transitions:** Downgrades (`identity` → `commitment` → `position`) require grounds at the *current* tier – de-committing has a cost just as reversing does. Upgrades need no trigger (staking yourself is self-binding, paid later) but must appear in the actor's actions.
- **Persistence:** Every turn writes the full ledger plus a changelog of all proposals with verdicts to `turn-XX/2-actors/<actor_id>-statements.md`. A diff between consecutive turns is empty unless a change was accepted, so erosion is visible in the artifacts rather than hidden in narrative.
- **World pricing:** Accepted changes ride into the Game Master step with the actor's actions (`last_actions` already carries the whole response). The GM template instructs it to treat a changed commitment- or identity-tier statement as a public event: narrate it, let other actors react next turn, and price it in whatever metrics the scenario provides. This is where reversal cost lives – diegetically, not as a Python rule.
- **Resume and branch:** Ledgers are restored from the last completed turn's `<actor_id>-statements.md` files, exactly like notepad and rules.
- **Prompt contract:** The default templates make *reviewing* mandatory but *changing* optional: task 2 instructs the actor to check each statement against what happened and what it plans, adjust stale positions, name triggers for staked reversals – or write `No statement changes.` after checking. Frequency norms ("in most turns you change nothing") were removed after they produced fully frozen ledgers across two scenarios of different character; quantity norms are avoided entirely because they read as quotas.

### Starting-State Draws (`loader.py`, `--initial-state`)

By default a scenario has exactly one starting world: the values declared in `metrics.md`. Runs then differ only in their event dice. Some questions instead hinge on uncertainty in the *starting* world, where the interesting variation is present before turn 1 (for example an election result that is still unknown, where small shifts change which coalitions are arithmetically possible at all).

- **Mechanism:** `run`, `describe`, and `batch-run` accept a JSON file of starting-state overrides. `load_scenario(path, initial_state=...)` applies it immediately after loading, before any turn executes.
- **File format:** A JSON object with three optional keys: `metrics` (metric id to number), `context` (markdown appended to `background/context.md` and to the initial world state), and `notes` (free text for provenance). Unknown top-level keys are rejected.
- **Strictness:** Unknown metric ids and out-of-bounds values are hard errors, not clamped. A draw that misses in either way indicates a broken generator, and silently repairing it would bias the batch while hiding the cause.
- **Batches:** `batch-run --initial-states <dir>` assigns one distinct draw per job in sorted order. Too few draws for the number of jobs is an error rather than a cycle, because reusing draws would silently narrow the distribution the batch reports on.
- **Provenance:** The applied draw is recorded in the run's `config.json` under `initial_state`, so results can be traced back to the world they started from. `branch` inherits it with the rest of the parent config.
- **Data, not code:** Scenario Lab *reads* the draw as data and never executes generator code. Producing the draws is a deliberate, separate step owned by the user; a scenario may ship a generator script in its own directory, but nothing in the loading path runs it. See Security Architecture below for why this boundary matters.

### Termination Conditions (`orchestrator.py`, `scenario.yaml`)

Some scenarios have a definite finish – a government forms, a deadline passes, a war ends. Without a stopping rule the loop runs every turn to `max_turns` regardless, which spends money simulating a world whose answer is already settled and invites the model to contradict its own resolution.

- **Declaration:** an optional `termination` block in `scenario.yaml`, each entry with an `id`, a `when` expression, and an optional `description`.
- **Evaluation:** after each completed turn, in Python, against current metric values. Deliberately *not* an LLM judgement: whether a run is over must be reproducible from the artifacts.
- **Safety:** `when` is evaluated by the same sandboxed AST evaluator as event probability formulas (`validator.eval_boolean_expression`), so it is no more powerful than a probability formula. Comparisons and boolean operators were already supported.
- **Robustness:** a condition that cannot be evaluated warns once per turn and is treated as unmet, so a bad expression cannot silently end every run at turn 1.
- **Validation:** `validate` rejects conditions referencing unknown metrics and warns when a condition is already true at the scenario's starting values.
- **Persistence:** the triggering condition is written to `summary.json` under `termination` as soon as it fires, so an interrupted run still records why it stopped.
- **Ordering:** conditions are checked in declaration order and the first match wins.

### The Turn Loop (`orchestrator.py`)
Each turn executes the following steps in order:

1. **Events Step**:
  * **Input:** World state (history + current), current metrics, list of potential events.
  * **LLM Task:** Determine which events meet their conditions and calculate their probabilities.
  * **Python Action:** Parse JSON response, roll the seeded dice for each candidate, and determine triggered events. If parsing fails, the orchestrator retries once with a dedicated “format-fix” prompt to coerce valid JSON before giving up for the turn.
  * **Structured Outputs:** Controlled by `llm.structured_outputs` (`auto` | `true` | `false`, default `auto`). When active, the events call uses the provider's native structured-output capability (`complete_structured` with the schema in `schemas.py`), which skips text parsing and the format-fix retry entirely. In `auto` mode, an unsupported model triggers a one-line info message, a silent fallback to the legacy parse path, and a per-run flag so structured output is not retried every turn. In `true` mode, lack of support is a hard error. The schema mirrors exactly what the prompt template asks for (objects with `id` and `probability`) – prompt semantics are unchanged.
  * **Parse-Failure Marker:** If the legacy path exhausts the format-fix retry and the turn proceeds with zero events, the orchestrator records `[{"parse_failure": true, "triggered": false}]` in `1-event-evaluations.json` and prints a warning, so a parse failure cannot be mistaken for "no events this turn".
  * **Persistence:** Writes both `1-events.json` (triggered events only, legacy shape) and `1-event-evaluations.json` (full per-candidate record: probability, roll, triggered, skipped reasons, force/suppress flags) at the same incremental point.
  * **Determinism:** Dice rolls come from a stable RNG derived from the run seed (`random.Random(f"{seed}:{turn}:{event_id}")`), not from a global unseeded generator.
  * **Overrides:** If `event_overrides` is set for this turn, forced events trigger regardless of the roll and suppressed events never trigger.
  * **Emergent Events:** When `emergent_events.enabled` is true, the prompt additionally invites up to `max_per_turn` novel exogenous proposals (`"emergent": true` plus a `description`). Python validates the shape, caps the probability at `max_probability`, rolls the same seeded dice, and records the proposal with `"emergent": true` in `1-event-evaluations.json`. Ids are normalized to start with `emergent_` (recorded as `id_normalized_from` if changed). When structured outputs are active, an extended item schema (adding required `emergent` and `description` fields) is used so both listed and emergent entries validate strictly.
  * **Probability Sampling:** When `llm.probability_samples > 1`, the candidate list is elicited that many times and per-event probabilities are aggregated (mean with absent-as-zero over valid samples) before the single dice roll. Per-sample values are persisted in the evaluation record.

2. **Actors Step**:
   * **Input:** World state (history + current), metrics, triggered events, and the actor's own statement ledger.
   * **LLM Task:** For *each* actor, review its statements against the turn's developments, optionally propose statement changes, and describe actions for the turn.
   * **Parallelization:** Actor prompts are independent and are executed in parallel with bounded concurrency.
   * **Statement Processing:** After all actor outputs return, `_process_statement_changes` parses proposals, applies the structural check and the gated relevance check, updates ledgers, and persists `<actor_id>-statements.md` per actor – before the rules step runs, so accepted changes reach the GM with the actions.

3. **Rules Step**:
  * **Input:** World state, triggered events, all actor actions, current rules (with version number).
  * **LLM Task:** Review and update the list of Metric Rules with:
    - Incremented version number (v1 → v2 → v3...)
    - Complete changelog documenting all Added/Modified/Removed rules
    - Motivation for each change (grounded in simulation state)
    - Expected impact on future metrics
    - Or an explicit no-op changelog entry when the prior rules still hold
  * **Freeze Handling:** If `turn <= rule_evolution.freeze_until_turn`, the orchestrator skips the rules LLM call entirely, writes a versioned carry-forward rules file with `No material rule changes.`, and records metadata indicating that the step was skipped due to freeze policy.
  * **Sanity Check:** Optional validation step to check for:
    - Complete and accurate changelog
    - Internal consistency (no contradictory rules)
    - Grounding in narrative/metrics/events
    - Compliance with scenario rule-evolution policy (for example frozen early turns or too many rule changes)
  * **Parser Tolerance:** The Python parser remains formatting-oriented, but tolerates common LLM presentation noise such as an outer fenced Markdown code block and parenthetical annotations after changelog rule names (for example, "`rule_name` (rule 2)").
  * **No-op Parsing:** The parser also accepts changelog sections that explicitly say `No material rule changes.` and treats them as valid carry-forward updates rather than malformed changelogs.
  * **Length Handling:** If rules output is truncated (`finish_reason=length`) or missing complete rules content, the orchestrator retries once with a concise-output instruction set to recover a complete `## Rules` section.
  * **Policy Handling:** Outside frozen turns, if the rules output violates configured rule-evolution guardrails, the orchestrator retries once with stricter instructions. If it still fails, the orchestrator carries the previous rules forward in a new versioned wrapper instead of accepting a broad rewrite that the scenario disallows.

4. **Metrics Step**:
  * **Input:** World state, triggered events, actor actions, updated rules.
  * **LLM Task:**
    * Determine success of actor actions.
    * Calculate new metric values.
    * Write a narrative summary of the turn.
    * Update the "Notepad" (persistent and secret game master notes).
  * **Realism Guidance:** The default prompt instructs the Game Master to avoid consensus bias: most turns should include at least one meaningful setback or friction point, actor conflicts should show up in outcomes, and a turn where every actor succeeds cleanly should prompt reassessment. This counters the LLM tendency toward smooth cooperative narratives that understate real-world friction.
  * **Output Parsing:** Requires verbatim headers (`## Metrics`, `## Narrative`, `## Notepad`) for reliable parsing.
  * **Failure Handling:** If the metrics response cannot be parsed, the orchestrator retries once with a "format-fix" prompt to enforce the required headers/JSON. If it still fails, previous metric values are kept for that turn.

5. **Constitutional Referee Step (Optional)**:
  * **Condition:** Only runs if scenario has a `constitution.md` file.
  * **Input:** Constitution constraints, proposed metrics updates, narrative explaining the changes.
  * **LLM Task:** Review the metrics update against constitutional constraints and validate that:
    - Economic constraints are respected (budgets, resources)
    - Regulatory timelines are realistic (legislation, agreements)
    - Organizational changes are feasible (capacity growth, hiring)
    - Physical constraints are honored (compute, infrastructure)
  * **Output:** Either "APPROVED" or "VIOLATIONS: [list of issues]"
  * **Parser Tolerance:** The parser accepts those responses even when the whole referee output is wrapped in a single outer fenced Markdown code block.
  * **Retry Logic:** If violations are found, the orchestrator makes one additional LLM correction pass:
    - The referee first returns structured violations
    - A dedicated correction prompt asks the LLM to minimally revise the metrics and narrative so they comply
    - The referee then validates the revised output once more
    - If the revised output still violates the constitution or cannot be parsed, the orchestrator follows the scenario's configured fallback policy: either continue with the latest proposal or keep the previous state
  * **Model:** Uses dedicated `referee` model (default: qwen/qwen3-235b-a22b-2507) for cost-effective validation.
  * **Metadata:** Saves detailed validation results to `5-constitutional-check.json` including:
    - Status (approved, violations_found, max_attempts_reached, parse_error)
    - Number of iterations
    - List of violations found per iteration
    - Final action taken
  * **Cost:** Minimal - uses fast, cheap model with short max_tokens (1000).

6. **Summarization Step**:
  * **Input:** Current `historical_summary` and the new `narrative` from Metrics Step.
  * **LLM Task:** Condense the new narrative and append it to the historical summary, keeping the total length manageable.
  * **Purpose:** Prevent context window explosion over long simulations.

### Prompt Engineering (`prompts.py` & Templates)
- **Jinja2 Templates:** All prompts – system and user alike – are rendered through a `SandboxedEnvironment` (SSTI protection, since scenario-supplied templates are untrusted). Templates live in `scenarios/{name}/system-prompts/` and `scenarios/{name}/user-prompts/`, defaulting to `templates/system-prompts/` and `templates/user-prompts/` when absent.
- **User prompt context:** `turn`, `time_period`, `metrics_json`, `world_state`, `historical_summary`, `notepad`, `output_language`, and individual metric variables (`metric_X`). Built by `_get_common_context`.
- **System prompt context:** a deliberately smaller set, since system prompts are built without a turn: `scenario_name`, `scenario_description`, `actors_list`, `metrics_list`, `constitution`, `output_language`, `actor_id`, `actor_name`, `actor_description`, `actor_short_description`, and `metric_X`. Built by `_get_system_prompt_context`. `actor_id` is what lets an actor system prompt branch on which actor it is speaking for.
- **Output Language:** The `output_language` setting injects instructions into templates to control the language of the LLM's response (e.g., "Please write your response in Swedish").
- **Validation:** `validate_prompt_overrides` parses every scenario override, erroring on invalid Jinja syntax and warning on variables the render context does not supply. This matters because Jinja renders an undefined variable as empty text rather than raising, so a typo or a wrong-context variable silently degrades the prompt while the file still looks correct.

**History (2026-08):** System prompts were previously not Jinja-rendered. They went through a plain string replace that handled five placeholders, all written without inner spaces (`{{actor_name}}`). A scenario override authored as a Jinja template therefore reached the model as raw template source with *every* conditional branch present simultaneously. This was found in `ai-safety-race`, whose `system-prompts/actor.md` branches on `actor_id`: because the US branch came first, every model tested played the US for both actors, and China's safety metric never moved. Nothing errored, and the affected runs looked superficially valid. The constitutional-referee prompts had always been Jinja-rendered, so the fix aligned the remaining paths with that precedent and with this document, which already specified Jinja for all prompts.

### LLM Providers and Routing (`providers/`, `router.py`)

**Call bounding and failure diagnosis (2026-08):** Three failure modes were found while evaluating candidate models, all of which destroyed or stalled runs without saying why.

- **Wall-clock deadline per call.** `OpenRouterProvider` streams the response body and checks elapsed time against a single deadline (`llm.call_timeout_seconds`, default 300s), raising `LLMCallTimeoutError`. httpx's timeout applies per read operation, so a trickling provider resets it forever; calls were observed blocking 11-23 minutes at near-zero CPU on an open socket. Streaming was chosen over a watchdog thread because it bounds the call without leaving an orphaned thread behind when the deadline fires.
- **Reasoning-budget exhaustion.** A reasoning model that fills its whole token budget with reasoning returns empty content beside a populated `reasoning` field. This now raises `LLMReasoningBudgetError` with the finish reason and token count. It is an `LLMError`, so `FallbackRouter` moves to the next route instead of making three identical retries that are guaranteed to fail the same way.
- **Transient failures are retried; rejections are not.** `LLMTransientError` covers transport-level failures (connection errors, read timeouts, wall-clock deadline overruns) where the request never received a verdict. `FallbackRouter` retries these on the same route with exponential backoff before falling through. Errors meaning the request itself was unacceptable – a rejected model, an exhausted reasoning budget – still move straight to the next route, since repeating them unchanged cannot succeed. Before this, provider timeouts were raised as plain `LLMError` and classified as non-retryable, so one slow response ended an entire run for the many scenarios configuring a single route; it killed a 10-turn qwen3-235b run at turn 3.
- **Provider errors are surfaced, not discarded.** When a payload carries no `choices` or no content, OpenRouter's own `error` object is included in the raised message. Previously the reason (rate limited, no capacity) was dropped and the user saw only "did not include choices".

**ModelRoute:** Every model reference in configuration is a `ModelRoute(provider, model)` dataclass. YAML syntax is `"provider:model"`, for example `"openrouter:qwen/qwen3-235b-a22b-2507"` or `"anthropic:claude-sonnet-4-6"`. String literals without a provider prefix are rejected at load time.

**Provider abstraction (`providers/`):** Each backend is an `LLMProvider` subclass with a `complete(system, user, *, model, temperature, max_tokens)` method:

- `OpenRouterProvider` – HTTP via `httpx`, reads `OPENROUTER_API_KEY`.
- `AnthropicProvider` – official `anthropic` SDK, reads `ANTHROPIC_API_KEY`. System prompts are sent as cache-controlled blocks (ephemeral prompt caching) by default, since a task's system prompt is stable across turns while the user prompt changes; cache write/read tokens are priced with their 1.25x/0.1x multipliers in `cost.py`. Caching can be disabled via the provider constructor (`enable_prompt_caching=False`).

New providers can be registered without changing orchestrator code.

**Structured outputs:** Providers additionally expose `complete_structured(system, user, *, model, temperature, max_tokens, schema, schema_name)` for schema-constrained completions (currently used by the events step only). `schema` is the JSON schema of the expected *array*; the returned `LLMResponse` carries the parsed payload in `structured_data` and a JSON serialization in `content` (so transcript logging keeps working unchanged).

- `OpenRouterProvider` sends `response_format: {"type": "json_schema", "json_schema": {..., "strict": true}}`. Models that reject it (any 4xx other than 429, or non-JSON content) raise `LLMUnsupportedStructuredError`.
- `AnthropicProvider` implements it as a forced tool call (`tools` + `tool_choice: {"type": "tool", "name": ...}`) whose `input_schema` wraps the array under an `events` object property; the tool-use input is unwrapped back to the array, so both providers return the same shape.
- The `LLMProvider` base class default raises `LLMUnsupportedStructuredError`, so new providers get graceful fallback for free.
- `FallbackRouter.complete_structured` threads the call through routes like `complete`, except that `LLMUnsupportedStructuredError` propagates immediately (no route fallback) – the caller decides whether to fall back to text parsing (`auto`) or fail hard (`true`). Token usage and cost accounting work identically for structured calls.

**ProviderRegistry:** One instance per run. Lazily creates built-in providers on first access so that a run using only OpenRouter never touches `ANTHROPIC_API_KEY`. Custom providers can be registered explicitly before the run starts.

**FallbackRouter (`router.py`):** Wraps an ordered list of `ModelRoute`s and one `ProviderRegistry`. On each call it tries routes left-to-right:

- Rate limits (`LLMRateLimitError`): up to three retries with exponential backoff on the same route.
- Non-retryable errors (`LLMError`): move to the next route immediately.
- Malformed responses (`ValueError`): up to three retries, then move on.
- After all routes are exhausted: raises `LLMError` with the list of attempted routes.

**LLM shared types (`llm.py`):** `LLMResponse`, `LLMError`, `LLMRateLimitError`, `LLMParseError`, `LLMUnsupportedStructuredError`, and `MockLLMClient` (used by the test suite). `LLMResponse.get_usage()` extracts a `TokenUsage` object from the raw response, with `provider` set to the originating backend.

**Pricing (`pricing/`):**

- `pricing/openrouter.py` – `OpenRouterPricingCache`: fetches from OpenRouter's model catalog, caches locally in `.scenario-lab-cache/openrouter-pricing.json`, falls back to the bundled seed in `data/openrouter_pricing_seed.json`.
- `pricing/anthropic.py` – `AnthropicPricingCache`: fetches from LiteLLM's model catalog (filters `litellm_provider == "anthropic"`), caches in `.scenario-lab-cache/anthropic-pricing.json`, falls back to the bundled seed in `data/anthropic_pricing_seed.json`.
- `pricing/__init__.py` exposes `get_pricing_for(route: ModelRoute)` which dispatches to the correct cache based on `route.provider`.

### Persistence (`output.py`)
- **Incremental Writing:** Results are saved to disk *immediately* after each step of the turn loop.
- **Event Evaluations:** `1-event-evaluations.json` is written incrementally at the same point as `1-events.json` and captures the full per-candidate provenance for the turn.
- **LLM I/O Transcripts:** When `logging.llm_io` is enabled, every LLM call is written at call time to `turn-XX/llm-io/NN-<task>.md` (task name, model, system/user prompts, raw response, token counts, cost). `NN` is a per-turn sequence number and task names are sanitized for filenames (for example `events:format_fix` becomes `events-format_fix`). This is implemented as a thin recording wrapper around the per-task LLM clients in the orchestrator, so logging is not scattered across call sites.
- **Structure:** Each run gets a timestamped directory. If a timestamp collides, the writer appends a numeric suffix (for example `run-20260304-102254-01`) instead of reusing the same directory. Each turn gets a subdirectory.
- **Crash Resilience:** If the simulation crashes, all progress up to the last successful step is preserved.
- **Resumption:** The directory structure and `summary.json` support resuming crashed runs or extending completed runs.

### Batch Execution (`cli.py`)
- **CLI Command:** `python -m scenario_lab.cli batch-run <target...> [options]`
- **Target Types:** Accepts scenario directories and variant YAML files. With `--variants`, a scenario directory expands to all YAML files in its `variants/` directory.
- **Repeat Runs:** `--repeat N` runs each resolved target N times, which supports Monte Carlo-style repeated runs of the same scenario without repeating the path manually.
- **Starting-State Draws:** `--initial-states <dir>` assigns one distinct JSON draw per job, so a batch can explore a distribution of starting worlds rather than only a distribution of event outcomes.
- **Execution Model:** Batch jobs run as separate child processes that invoke the normal `run` command. This keeps each simulation isolated while preserving the same orchestration and persistence behavior as single runs.
- **Live Status:** In interactive terminals, batch commands stream child output into an inline dashboard that shows one row per job, including current turn, current activity, and the latest warning.
- **Concurrency Control:** Uses bounded parallelism via `--max-concurrency` rather than launching every job at once.
- **Logging:** Each batch job writes its stdout/stderr to a per-job log file under the owning scenario's `runs/batch-logs/` directory.
- **Model Checks:** Batch jobs bypass interactive model preflight prompts so unattended runs do not block on TTY input.
- **Batch Resume:** `python -m scenario_lab.cli batch-resume <target...> [options]` resumes multiple runs with the same bounded-concurrency/process-isolation model. Scenario directories and `runs/` directories expand to incomplete `run-*` directories automatically; explicit run directories are resumed directly.

### Run Analysis (`analysis.py`)
- **CLI Command:** `python -m scenario_lab.cli analyze <run-dir> [options]`
- **Purpose:** Generates a post-run analysis report from persisted artifacts in a completed run directory.
- **Inputs:** Reads the run snapshot (`config.json`, `summary.json`, optional `costs.json`) plus per-turn artifacts such as triggered events, actor outputs, metric rules, metrics, world-state narrative, referee results, notepad, and historical summary.
- **Scenario Context:** Also reloads the owning scenario definition so the analysis step sees the intended metrics, events, actors, initial metric rules, and optional constitution.
- **Prompting:** Uses the same template override pattern as simulation prompts, with default templates under `templates/system-prompts/analysis.md` and `templates/user-prompts/analysis.md`, and optional scenario overrides under `system-prompts/analysis.md` and `user-prompts/analysis.md`.
- **Context Handling:** Attempts to include rich turn-level artifacts directly; if the prompt would become too large, long artifact sections are truncated into a more condensed context before the final analysis call.
- **Output:** Saves `analysis.md` by default, or `analysis.json` with `--json`. `--no-save` leaves the report unsaved and prints only a short top-line summary to stdout.

### Resume & Branching (`resume.py`)

**Module:** `scenario_lab/resume.py` provides core functionality for loading and manipulating run state.

**Key Functions:**
- `detect_last_turn(run_dir)`: Finds the highest completed turn by validating turn directory structure.
- `validate_run_directory(run_dir)`: Checks for required files (`config.json`, `summary.json`, turn directories).
- `get_scenario_path_from_run(run_dir)`: Navigates from run directory to scenario directory.
- `load_run_state(run_dir, from_turn, state_modifications)`: Loads complete scenario state from disk, with optional modifications.
- `create_branch(parent_run_dir, from_turn, output_base, state_modifications, config_overrides)`: Creates a new branched run.

**Resume Implementation:**
- **CLI Command:** `python -m scenario_lab.cli resume <run_dir> [options]`
- **Options:**
  * `--from-turn N`: Resume from specific turn (default: auto-detect last completed)
  * `--turns N`: Total turns to run (overrides config)
  * `--model X`: Override all LLM models
  * `--override key=value`: Override any config value
  * `--log-llm-io`: Write per-call LLM transcripts under `turn-XX/llm-io/`
- **Seed Handling:** Resume reads `random_seed` from the saved `config.json` so dice rolls stay reproducible. Legacy runs without a seed get a fresh one generated and written back into `config.json`.
- **Behavior:**
  * Loads state from the specified turn (metrics, narrative, rules, notepad, historical summary, occurred events)
  * Continues execution in the *same* run directory (no duplication)
  * Updates `summary.json` with `resumed_at` and `resumed_from_turn` metadata
  * Useful for: crashed runs, extending completed scenarios, switching to better/cheaper models
- **State Loading:**
  * Reads `turn-XX/4-metrics.json` to restore metric values
  * Reads `turn-XX/4-world-state.md` to restore narrative
  * Reads `turn-XX/3-metric-rules.md` to restore rules
  * Reads `turn-XX/5-notepad.md` to restore game master notes
  * Reads `turn-XX/6-historical-summary.md` to restore turn history
  * Reads `summary.json` to restore occurred events list

**Branch Implementation:**
- **CLI Command:** `python -m scenario_lab.cli branch <run_dir> --from-turn N [options]`
- **Options:**
  * `--from-turn N`: **Required** - Turn number to branch from
  * `--modify-metric id=value`: Modify metric value(s) for "what-if" scenarios (repeatable)
  * `--modify-narrative "text"`: Replace narrative text
  * `--model X`: Override all LLM models
  * `--override key=value`: Override any config value
  * `--turns N`: Total turns to run from branch point
  * `--seed INT`: Override the dice RNG seed (default: keep the parent run's seed)
  * `--force-event EVENT_ID` / `--suppress-event EVENT_ID`: Repeatable counterfactual controls applied to the first turn executed in the branch. Event ids are validated against the scenario; an unknown id fails with a clear error. The overrides are recorded in the new run's `config.json` as `event_overrides` and reflected in `1-event-evaluations.json`.
  * `--log-llm-io`: Write per-call LLM transcripts under `turn-XX/llm-io/`
- **Behavior:**
  * Creates a *new* timestamped run directory (same-second collisions get a numeric suffix, so concurrent branch creation is safe)
  * Copies turn directories 1 through N from parent run
  * Loads state from turn N and applies modifications
  * Continues execution from turn N+1 in new directory
  * Useful for: "what-if" experiments, sensitivity analysis, model comparison
- **Metadata Tracking:**
  * `config.json` includes: `parent_run`, `branch_turn`, `branch_created_at`, `state_modifications`, `config_overrides`
  * `summary.json` includes: `metadata` object with parent run reference, branch point, and all modifications
  * Preserves full lineage for analysis and reproducibility
- **State Modifications:**
  * Metrics: Modified values are clamped to min/max bounds with warnings
  * Narrative: Completely replaces the world state narrative
  * Notepad: Replaces game master notes
  * Rules: Replaces metric rules markdown
  * Persistence: Modified branch-point state is written back to copied turn files and reflected in `summary.json` immediately

**Orchestrator Integration:**
- `run_simulation()` now accepts `start_turn` parameter (default: 1)
- Turn loop iterates from `start_turn` to `max_turns` instead of 1 to `max_turns`
- No other orchestrator changes needed - pre-loaded scenario state works seamlessly

**File Structure for Resume/Branch:**
```
run-YYYYMMDD-HHMMSS/
├── config.json                   # Contains metadata for branched runs
├── summary.json                  # Contains resume/branch metadata
└── turn-XX/                      # Validated for completeness before loading
    ├── 1-events.json
    ├── 1-event-evaluations.json # Full per-candidate event record (optional for legacy runs)
    ├── llm-io/                  # Per-call LLM transcripts (only when llm_io logging is on)
    ├── 2-actors/*.md
    ├── 2-actors/<actor_id>-statements.md  # Full statement ledger + proposal changelog
    ├── 3-metric-rules.md         # Versioned rules with changelog
    ├── 3-metric-rules-metadata.json  # Rules version and changelog metadata
    ├── 4-metrics.json            # Source of truth for metric values
    ├── 4-world-state.md          # Source of truth for narrative
    ├── 5-constitutional-check.json   # Constitutional validation results (if constitution exists)
    ├── 5-notepad.md              # Source of truth for GM notes
    └── 6-historical-summary.md   # Source of truth for history
```

**Metric Rules Format:**
Each `3-metric-rules.md` file includes:
- Version number in header (e.g., "# Metric Rules v3 (Turn 4)")
- Changelog section documenting all changes from previous version
- Full set of current rules

**Constitutional Validation Metadata:**
The `5-constitutional-check.json` file (when present) includes:
- Status: approved, violations_found, max_attempts_reached, or parse_error
- Iterations: Number of validation attempts
- Violations found: List of violations per iteration with details
- Final action: Whether metrics were accepted or corrected

**Future Extensions:**
- Batch branch: Create multiple branches from a batch of runs
- Parallel execution for resume/branch operations

### Validation (`validator.py`)

**Purpose:** Catch errors before expensive LLM calls by validating scenario structure, references, and configuration.

**Key Validation Functions:**

1. **Metric Reference Validation** (`validate_metric_references`):
   - Checks that all metric references in actor descriptions, event conditions, event probabilities, and metric rules point to existing metrics
   - Prevents runtime failures from undefined metric references

2. **Event Probability Validation** (`validate_event_probabilities`):
   - Validates that probability formulas are valid mathematical expressions
   - Uses a **secure AST-based evaluator** that prevents code injection attacks
   - Only allows safe operations: arithmetic (+, -, *, /, //, %, **), comparisons (<, >, ==, etc.), min/max functions, and metric variable references
   - Rejects dangerous operations: imports, attribute access, arbitrary function calls, assignments, control flow
   - Verifies formulas evaluate to valid range [0, 1] with sample data
   - Handles both static probabilities (e.g., "10 procent per runda") and dynamic formulas (e.g., "unemployment / 100")
   - **Security:** Uses `SafeExpressionEvaluator` class that parses expressions into Abstract Syntax Trees (AST) and validates each operation before execution, eliminating the security risks of Python's `eval()` function

3. **Model Hygiene Checks** (`model_audit.py` + `validate_scenario` warnings):
   - Applies local heuristic warnings to configured LLM model names before expensive runs
   - Flags clearly legacy model families (for example GPT-3.5 / Claude 2 style names)
   - Flags dated snapshot models older than a configured age threshold (currently 180 days)
   - Reads optional repository policy from `model-policy.yaml` to make hygiene rules editable without code changes
   - Policy supports:
     - `max_snapshot_age_days`: override the snapshot age threshold
     - `allowed_patterns`: optional regex allowlist; if non-empty, models outside it are warned
     - `blocked_patterns`: regex denylist; matching models are warned
   - Static validation remains local and deterministic; optional run-time replacement suggestions may query OpenRouter's model catalog for current pricing and capability metadata
   - Replacement selection prefers models that are both newer and cheaper than the current one when such candidates exist, while preserving modality compatibility

3. **LLM Configuration Validation** (`validate_llm_config`):
   - Validates model strings follow OpenRouter format
   - Ensures temperature is in valid range [0, 2]
   - Checks max_tokens is reasonable (> 100, < 100000)
   - Validates all task-specific model configurations (events, actors, rules, metrics, summary)

4. **Actor Reference Validation** (`validate_actor_references`):
   - Ensures all actors in scenario.yaml have corresponding files
   - Detects orphaned actor files

5. **Date and Time Scale Validation** (`validate_time_config`):
   - Validates start_date is in correct format (YYYY-MM-DD, YYYY-MM, or YYYY)
   - Checks time_scale is parseable (days/weeks/months/years)
   - Ensures max_turns doesn't exceed reasonable limits

6. **Model Route Validation** (`is_valid_model_route`, used by `validate_llm_config`):
   - Validates each configured entry as a `ModelRoute`, covering single models, fallback lists, and per-actor dicts
   - Provider-aware: `vendor/model` is required for `openrouter`, while other providers (Anthropic ids like `claude-sonnet-4-6`) only need a non-empty model
   - **Why it matters:** the previous check predated the `ModelRoute` migration and compared raw strings. Single models matched neither branch and were silently unvalidated; every fallback list failed regardless of contents, which read as a scenario error rather than a validator bug.

7. **Prompt Override Validation** (`validate_prompt_overrides`):
   - Parses every `system-prompts/` and `user-prompts/` override as Jinja; invalid syntax is an error
   - Warns when an override references a variable the render context does not supply, checked against the union of contexts across all actors
   - **Why it matters:** Jinja renders undefined variables as empty text instead of raising, so a misspelled or wrong-context variable produces a silently degraded prompt. This check exists because exactly that failure went undetected across multiple model evaluations (see the prompt-engineering history note above).

8. **Research Question Validation** (`validate_research_questions`):
   - Checks that every metric and event id named by a declared research question actually exists in the scenario (error)
   - Enforces unique question ids and non-empty question text
   - Warns when a question names neither metrics nor events, since synthesis can then only answer it qualitatively
   - **Why it matters:** This is the check that catches a question the scenario cannot answer *before* runs are spent on it. Without it, `synthesize` would produce a confident but ungrounded answer.

**Integration:**
- `validate_scenario(scenario_path)`: Runs all validation checks and returns `ValidationResult` with errors and warnings
- CLI command: `python -m scenario_lab.cli validate scenarios/sweden-ai-2030`
- Auto-validation: `--validate` flag on run command to validate before executing

**Value:**
- **Cost Savings:** Catch errors before LLM API calls
- **Developer Experience:** Fast feedback on scenario design
- **Reliability:** Fewer runtime failures
- **Documentation:** Validation errors help users understand requirements

### Cost Tracking (`cost.py`, `output.py`)

**Purpose:** Track token usage and estimate costs to help users budget and optimize LLM API spending.

**Token Usage Tracking:**
- `TokenUsage` dataclass stores `prompt_tokens`, `completion_tokens`, `total_tokens`, `model`, and `provider`. Anthropic responses also populate `cache_creation_input_tokens` and `cache_read_input_tokens`.
- Token counts are extracted from every LLM response via `LLMResponse.get_usage()`.
- The orchestrator converts token usage into `CostDetails` and records them in `CostTracker`.
- Cost estimation dispatches to the correct pricing cache based on `usage.provider`.

**Pricing Caches:**
- OpenRouter: seed in `scenario_lab/data/openrouter_pricing_seed.json`, runtime cache in `.scenario-lab-cache/openrouter-pricing.json`, refreshed from OpenRouter's model catalog.
- Anthropic: seed in `scenario_lab/data/anthropic_pricing_seed.json`, runtime cache in `.scenario-lab-cache/anthropic-pricing.json`, refreshed from LiteLLM's model catalog.
- Both caches refresh automatically when a model is missing or the snapshot is stale; each falls back to its bundled seed if a refresh fails.

**Cost Reporting:**
- Saved to `costs.json` in run directory with detailed breakdown.
- Tracks costs by turn, by task (events, actors, rules, metrics, summary), and by model.
- Includes total tokens, total cost, and averages.

**CLI Commands:**
- `estimate`: Pre-run cost estimation based on scenario configuration.
- `costs`: Display cost report for completed runs with optional `--detailed` breakdown.
- `refresh-pricing`: Refresh pricing caches; `--provider {openrouter,anthropic}` scopes to one provider.

**Value:**
- Budget control and planning
- Model selection guidance (cost vs. quality trade-offs)
- Optimization of expensive steps
- Transparency in API spending

### Progress Tracking (`progress.py`)

**Purpose:** Provide real-time feedback during long-running simulations to improve user experience.

**ProgressTracker Class:**
- Tracks current turn, step, and timing information
- Displays turn headers with ETA estimates
- Updates step status (in_progress, completed)
- Records turn completion times for ETA calculation

**Features:**
- Turn-level progress with numbered headers
- Step-by-step status updates (Events, Actors, Rules, Metrics)
- Estimated time remaining based on average turn duration
- Cost information during execution (if tracking enabled)

**CLI Options:**
- Default: Progress tracking enabled
- `--no-progress`: Disable for cleaner logs
- `--quiet`: Minimal output mode

**Display Format:**
```
============================================================
TURN 3/10
Estimated time remaining: 14.5 minutes
Cost so far: $0.15 | Projected total: $0.50
============================================================
  [Events] ✓ Complete
  [Actors] Processing...
```

**Value:**
- User feedback for long operations (2-5 minutes per turn)
- Debugging aid to identify slow steps
- Progress monitoring for batch runs

### CLI (`cli.py`)
- **Entry Point:** `python -m scenario_lab.cli`.
- **Commands:** `run`, `batch-run`, `batch-resume`, `resume`, `branch`, `validate`, `describe`, `audit-models`, `visualize`, `costs`, `estimate`, `refresh-pricing`, `calibrate`, `ensemble`, `model-sensitivity`, `causal-impact`, `compare-runs`, `check-run-integrity`, `check-regressions`, `compare-distributions`, `quality-check`, `analyze`
- **Overrides:** Supports `--override key=value` to modify configuration at runtime (e.g., `--override output_language=Spanish`).
- **Validation:** Supports `--validate` flag to validate scenarios before running
- **Model Preflight:** `run` performs model hygiene checks by default and can be bypassed with `--skip-model-checks`
- **Progress:** Supports `--no-progress` and `--quiet` flags for output control

### Ensemble Analysis (`ensemble.py`)
- **CLI Command:** `python -m scenario_lab.cli ensemble <scenario-dir> [options]`
- **Purpose:** Analyzes all completed runs of a scenario as an ensemble without making any API calls.
- **Inputs:** Reads `config.json`, `summary.json`, `costs.json`, and per-turn `4-metrics.json`, `1-events.json`, and `1-event-evaluations.json` (optional, absent in legacy runs) from every completed run directory.
- **Report Sections:** Run overview (N, status mix, turn counts, cost); per-metric trajectories (mean/min/max/p10/p50/p90 per turn, with per-turn N reflecting runs that ended early); event statistics (overall occurrence rate, per-turn occurrence counts, mean evaluated probability vs realized frequency when evaluation data is available); divergence detection (metric × turn with the largest IQR jump, event associations via mean-split); narrative diversity (pairwise lexical Jaccard similarity of each run's final historical summary – a cheap local check for storyline monoculture behind diverging metrics, with a caveat raised when mean similarity ≥ 0.5); automatic caveats for small N and mixed model configs.
- **Output:** Markdown to stdout, or `--output file.md` for file output; `--json` emits the raw data structure.

### Cross-Run Synthesis (`synthesis.py`)
- **CLI Command:** `python -m scenario_lab.cli synthesize <scenario-dir> [options]`
- **Purpose:** Joins the two halves of batch analysis. `analysis.py` reads one run in depth but knows nothing of the others; `ensemble.py` counts across all runs but reads none of them. Synthesis makes one LLM call over every run's structured analysis, grounded in the ensemble statistics, to answer "what does this world tend to do".
- **Per-run analysis pass:** For each completed run, reuses `analysis.json` when present and readable, otherwise calls `generate_run_analysis(..., json_output=True)` to create it. Because a completed run is immutable, a readable cached analysis is always still valid for it; `--refresh-analyses` forces regeneration. Missing analyses are generated in parallel (`--max-concurrency`, default 4). A run whose analysis fails is recorded as a failure and excluded from the prompt rather than aborting the command, and the exclusion is stated in the prompt and the CLI output.
- **Division of labor:** Python discovers runs, generates/caches per-run analyses, computes the ensemble statistics, condenses context, and counts. The LLM does the judging. No world rules live in this module.
- **Prompting:** Default templates at `templates/system-prompts/synthesis.md` and `templates/user-prompts/synthesis.md`. The system prompt establishes that ensemble statistics are authoritative for anything countable while per-run analyses are individual readings to be attributed to their runs, and requires that recurring narrative shapes or implausible event rates be reported as possible simulation artifacts rather than findings about the world.
- **Research questions:** When the scenario declares `research_questions` (see `loader.parse_research_questions`), they are rendered into the prompt and answered explicitly, each with a frequency, the conditions the answer depends on, and evidencing run names – before any undeclared findings. With none declared, the prompt states that the framing is the model's own.
- **Context Handling:** Three densities (`full`, `condensed`, `minimal`) chosen by the same fit-to-window loop as `analysis.py`. Density controls which analysis sections are included per run (full: summary, turning points, event analysis, actor patterns, caveats; minimal: summary only), their truncation limits, and whether ensemble metric trajectories are sent whole or trimmed to first/middle/last turn per metric. Event statistics, divergence, and narrative diversity are always sent whole – they are the countable evidence.
- **Output:** Saves `synthesis.md` in the scenario directory by default, or `synthesis.json` with `--json`; `--output` overrides the path and `--no-save` prints without saving. `--dry-run` reports which runs would need a new analysis and makes no API calls.
- **Cost shape:** One analysis call per uncached run, plus exactly one synthesis call. A repeat `synthesize` over the same runs costs one call.

### Model Sensitivity Analysis (`model_sensitivity.py`)
- **CLI Command:** `python -m scenario_lab.cli model-sensitivity <scenario-dir> [options]`
- **Purpose:** Groups completed runs by their LLM configuration and compares outcomes across groups. Helps distinguish scenario stochasticity from model-driven variation.
- **Grouping:** Runs are grouped by the sorted set of task→model assignments from each run's `config.json` `llm` block. Runs with identical model configs form one group.
- **Report Sections:** Groups found with N and model(s); per-metric final-value distributions per group (mean/min/max/p10/p90); event occurrence rates per group; a robustness summary labeling metrics/events as sensitive (groups disagree) or robust (groups agree), using a 20% observed-range threshold for metrics and a 0.30 rate-difference threshold for events; caveats for single-group and small sample sizes.
- **Single-group behavior:** If all runs use the same model, the report states clearly that sensitivity cannot be assessed and points at `variants/` + `batch-run` as the workflow to create multiple groups.
- **Output:** Same `--json` / `--output` options as `ensemble`.

### Scenario Overview (`describe.py`)
- **CLI Command:** `python -m scenario_lab.cli describe <scenario-dir> [options]`
- **Purpose:** Renders any scenario definition as a compact one-page markdown overview: identity and time frame, actors with goals, metrics with start values/ranges/reference-point count, events with conditions and probabilities, metric-rule count, constitution presence, LLM configuration (per-task routes, probability sampling, emergent-events policy, rule-evolution guardrails), custom prompt overrides, and directory contents (background files, variants, completed runs).
- **Role in authoring:** This is the "show what was created at a glance" step of the scenario-creation workflow (see `.claude/skills/create-scenario/`): after drafting or editing scenario files, `describe` gives the human a reviewable summary without reading every file. It reads only the scenario definition – no API calls.
- **Output:** Markdown to stdout, `--output file.md`, or `--json` for the raw structure.

### Causal Impact Analysis (`causal.py`)
- **CLI Command:** `python -m scenario_lab.cli causal-impact <scenario-or-run-dir> --event EVENT_ID [options]`
- **Purpose:** Estimates a specific event's causal effect on final metrics by running matched batches of forced and suppressed branches and comparing the outcome distributions. This upgrades the ensemble's descriptive event associations into branch-point counterfactuals.
- **Workflow:** Picks a baseline parent run (latest completed run without `event_overrides`, or an explicit run directory), plans `--repeats` seed-matched pairs per event (one forced + one suppressed branch sharing the same dice seed, so all *other* events roll identically within a pair), executes them as `branch` child processes through the shared batch executor, then analyzes the resulting groups.
- **Analysis:** Groups completed branch runs by inspecting `event_overrides` in their `config.json` (no extra bookkeeping files). Reports per-metric forced/suppressed means, the mean effect (forced − suppressed), and seed-paired mean effects where pairs exist, plus caveats about small N, unpaired runs, and world-model reliability.
- **Options:** `--repeats` (default 5), `--from-turn` (default 1; overrides apply to the following turn), `--turns`, `--max-concurrency`, `--seed`, `--report-only` (analyze existing branches without running new ones), `--dry-run` (print planned branch commands), `--json`, `--output`.
- **Cost:** Each pair costs two branch runs. Without `--event`, the command lists available events and exits, pointing at `ensemble` divergence associations for candidate selection.

## 4. Evaluation & Testing
- **Unit Tests:** Standard pytest suite for Python logic.
- **LLM Evals:** Specialized suite in `tests/evals/llm-event-conditions/` to benchmark LLM performance on logic, math, and hallucination prevention.
- **Statement Relevance Evals:** Opt-in live-LLM suite in `tests/evals/statement-relevance/` (`pytest -m integration`) exercising the relevance referee on fixed cases: real triggers accepted (including slow pressure), invented ones rejected, laundered ones (real quote, wrong statement) rejected.
- **Security Tests:** Comprehensive security test suite in `tests/test_security.py` covering path traversal, template injection, and code execution prevention.

## 5. Security Architecture

Scenario Lab implements defense-in-depth security measures to protect against common vulnerabilities:

### Template Security
- **Sandboxed Jinja2 Environment:** All user-provided templates (custom system/user prompts) are rendered using Jinja2's `SandboxedEnvironment`.
- **Protection Against SSTI:** The sandbox prevents Server-Side Template Injection attacks by blocking access to dangerous attributes (`__class__`, `__mro__`, `__bases__`) and preventing code execution.
- **Implementation:** `prompts.py` creates a sandboxed environment in `__init__` and uses `jinja_env.from_string()` for all template rendering.

### Path Security
- **Base Scenario Validation:** The `base` field in `scenario.yaml` is validated to prevent path traversal attacks. Base scenarios must be within the scenarios directory structure.
- **Actor ID Validation:** (Pending - Issue #3) Actor IDs should be validated to prevent path traversal in output file creation.
- **Implementation:** `loader.py` uses `Path.relative_to()` to ensure base paths don't escape allowed directories.

### Input Security
- **Safe YAML Loading:** Uses `yaml.safe_load()` instead of `yaml.load()` to prevent arbitrary object deserialization.
- **Data-Only Starting States:** Starting-state draws are parsed with `json.loads` and validated field by field. Scenario files cannot declare a script for Scenario Lab to execute, and the loading path never runs generator code. This preserves the same guarantee as the sandboxed template environment and the AST-based probability evaluator: content inside a scenario directory is data to be read, never code to be run.
- **AST-Based Expression Evaluation:** Event probability formulas are evaluated using a safe AST-based evaluator, not `eval()`. Only allows basic arithmetic operations and metric variable references.
- **API Key Handling:** API keys are only loaded from environment variables, never hardcoded or logged.

### Security Testing
- **15+ Security Tests:** Comprehensive test coverage in `tests/test_security.py`:
  - Path traversal prevention (3 tests)
  - Template injection prevention (6 tests)
  - Code execution prevention
  - File access prevention
- **Continuous Validation:** All security tests run as part of the standard test suite.

### Fixed Vulnerabilities
See [SECURITY_AUDIT.md](../SECURITY_AUDIT.md) for detailed audit results and fixes:
- ✅ Path Traversal in Base Scenario Loading (Fixed 2025-12-07)
- ✅ Jinja2 Template Injection (Fixed 2025-12-08)

## 6. Extension Guidelines
- **Update This Document first:** This document must be the ground truth and reflect how the project should work. Before adding or changing substantial functionality, it should be described here.
- **New Features:** Must not break the "Pure LLM" philosophy. Avoid adding game logic to Python.
- **Prompts:** Modify templates, not Python code, whenever possible.
- **No backwards Compatibility:** As the project is still in an early phase, there is no need for backwards compatibility. Old scenarios (e.g., `sweden-ai-2030`) and other files are either updated or deleted when changing data models.
- **Language:** Both code and scenarios should be written in English. Code comments, documentation, scenario files (YAML, Markdown), and all technical content should use English for consistency and broader accessibility.
