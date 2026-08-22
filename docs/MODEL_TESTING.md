# Model Testing Notes

Accumulated findings from running Scenario Lab scenarios with different LLMs. Use this when choosing a model for new runs or calibration.

Pricing should still be verified against OpenRouter before trusting older logged cost figures — newer runs use a cached OpenRouter pricing snapshot, but historical runs may reflect outdated pricing data.

**Model availability changes without warning.** As of 2026-08-21, two of the three previously recommended models – `x-ai/grok-4.1-fast` and `google/gemini-2.0-flash-001` – have been removed from the OpenRouter catalogue and return HTTP 404. `x-ai/grok-4.1-fast` was still configured in six scenarios and was the library default for the `summary`, `analysis`, and `referee` tasks, so those scenarios could not run at all until reconfigured. `audit-models` does not catch this: it checks name patterns and snapshot age, never whether the model still exists. Verify availability against the pricing cache before a batch, not after.

## ⚠️ ai-safety-race Results Before 2026-08-21 Are Unreliable

A prompt-rendering bug meant that `scenarios/ai-safety-race/system-prompts/actor.md` was never Jinja-rendered. Its `{% if actor_id == 'usa' %}` / `{% elif actor_id == 'china' %}` branches reached the model as literal text with both branches present, and the US branch came first. **Every model tested on this scenario played the United States for both actors.** China never advocated for itself, which is why `china_safety` sat frozen in run after run.

Fixed 2026-08-21 (system prompts now render through the sandboxed Jinja environment, with validation for undefined variables). Consequences for this document:

- Every ai-safety-race assessment below predates the fix and measured models under a broken prompt: `google/gemini-2.0-flash-001`, `x-ai/grok-4.1-fast`, `google/gemini-2.5-flash`, `moonshotai/kimi-k2`, `anthropic/claude-haiku-4-5`, `deepseek/deepseek-v3.2`, `mistralai/mistral-small-24b-instruct-2501`, `qwen/qwen3-30b-a3b-instruct-2507`, `nvidia/nemotron-3-ultra-550b-a55b:free`, `deepseek/deepseek-v4-flash-0731`.
- Constitutional-violation counts from those runs are not trustworthy. An actor arguing the wrong country's position will produce metric updates that look like constraint violations without the model having reasoned badly.
- Findings that do **not** depend on the actor prompt still stand: crashes, hangs, parse errors, empty or partial metrics payloads, hallucinated metric names, throughput, and cost.
- `qwen/qwen3-235b-a22b-2507` and `openai/gpt-5.4-nano` were tested on sweden-ai-2030, which has no Jinja in its overrides. Those assessments are unaffected.
- `deepseek/deepseek-v4-flash-0731` has since been re-run to completion against the fixed prompt (2026-08-22). Its assessment below reflects that run, not the earlier three-turn one.

Re-test candidates against the fixed prompt before trusting any comparison below.

## Summary

| Model | Prompt/M | Completion/M | Constitutional violations | Verdict |
|-------|----------|--------------|--------------------------|---------|
| google/gemini-2.0-flash-001 | $0.10 | $0.40 | 1/10 turns (ai-safety-race) | **REMOVED from OpenRouter 2026-08** |
| x-ai/grok-4.1-fast | $0.20 | $0.50 | 0/10 turns (ai-safety-race) | **REMOVED from OpenRouter 2026-08** |
| qwen/qwen3-235b-a22b-2507 | $0.09 | $0.55 | 0/40 (sweden-ai-2030); 9/10 approved, 0 arithmetic violations (ai-safety-race, **fixed prompt**) | **Recommended – the only verdict resting on a correct prompt** |
| openai/gpt-5.4-nano | $0.20 | $1.25 | 35/40 turns accepted with constitutional violations (sweden-ai-2030) | Avoid |
| google/gemini-2.5-flash | $0.30 | $2.50 | 10/10 turns (ai-safety-race) | Avoid |
| moonshotai/kimi-k2 | $0.55 | $2.20 | 6/10 turns (ai-safety-race) | Avoid |
| anthropic/claude-haiku-4-5 | $1.00 | $5.00 | 10/10 turns (ai-safety-race) | Avoid |
| deepseek/deepseek-v3.2 | $0.27 | $1.10 | – | Avoid (crashes) |
| mistralai/mistral-small-24b-instruct-2501 | $0.05 | $0.08 | 9/10 turns unresolved (ai-safety-race) | Avoid |
| qwen/qwen3-30b-a3b-instruct-2507 | $0.048 | $0.193 | 3/7 turns unresolved (ai-safety-race) | Avoid (hangs, hallucinates metrics) |
| nvidia/nemotron-3-ultra-550b-a55b:free | $0 | $0 | 2/3 approved before crash | Avoid (free tier drops responses) |
| deepseek/deepseek-v4-flash-0731 | $0.065 | $0.18 | 6/10 turns violated on first attempt, 2/10 left unresolved (ai-safety-race, **fixed prompt**, 10 turns) | Avoid for unattended work – never crashes, but 565s/turn and the referee cannot keep it in bounds |
| minimax/minimax-m3 | $0.23 | $0.96 | 3/3 approved, then crashed turn 4 | Avoid (reasoning budget exhaustion) |
| z-ai/glm-4.7-flash | $0.06 | $0.40 | 2/2 approved, 661s/turn | Avoid (far too slow) |

## Cost per Run (10 turns, correct pricing)

| Model | Scenario | Avg cost | Avg tokens |
|-------|----------|----------|------------|
| qwen/qwen3-235b-a22b-2507 | sweden-ai-2030 | ~$0.023 | ~302k |
| openai/gpt-5.4-nano | sweden-ai-2030 | ~$0.14 | ~368k |
| google/gemini-2.0-flash-001 | ai-safety-race | ~$0.05 | – |
| x-ai/grok-4.1-fast | sweden-ai-2030 | ~$0.12 | ~388k |
| x-ai/grok-4.1-fast | ai-safety-race | ~$0.44* | – |
| qwen/qwen3-235b-a22b-2507 | ai-safety-race | ~$0.042 | ~266k |
| mistralai/mistral-small-24b-instruct-2501 | ai-safety-race | ~$0.022 | ~394k |
| qwen/qwen3-30b-a3b-instruct-2507 | ai-safety-race | ~$0.035 (projected) | ~390k (6 turns: 260k) |
| anthropic/claude-haiku-4-5 | ai-safety-race | ~$1.30* | – |
| deepseek/deepseek-v4-flash-0731 | ai-safety-race | ~$0.067 | ~566k |

*Logged costs for older runs used incorrect pricing and have not been recalculated.

---

## Model Assessments

### google/gemini-2.0-flash-001

**Tested on:** ai-safety-race (1 run, 10 turns)

- 1/10 turns with minor violations (resource tradeoff, turn 4)
- Consistent formatting throughout
- Cooperative simulation character — coordination rose to 50, both actors achieved high safety. Possibly too cooperative to be dramatically interesting, but technically exemplary
- Cheapest tested model at ~$0.05/run
- Oldest and cheapest tested model; shows that mature models are not worse at structured simulation tasks

**Verdict:** Best stability/cost ratio tested so far. Good baseline for calibrating new scenarios.

---

### x-ai/grok-4.1-fast

**Tested on:** ai-safety-race (multiple runs), sweden-ai-2030 (16 runs)

- 0/10 constitutional violations in ai-safety-race (after events.md was updated with explicit lookup table for catastrophe events — an earlier run missed catastrophe events systematically when US capability passed 70)
- Metric runaway observed in sweden-ai-2030 (ai_capability reaching 448) — suggests weak internal consistency on exponential dynamics in that scenario
- Tends toward competitive dynamics and falling coordination in ai-safety-race; realistic arms-race feel
- High outcome variance in ai-safety-race: coordination collapsed to 8 in one run, rose to 86 in another

**Verdict:** Reliable default. Watch for metric drift in long runs with exponential dynamics.

---

### qwen/qwen3-235b-a22b-2507

**Tested on:** sweden-ai-2030 (4 runs, 2026-03-31)

- 0/40 constitutional violations (one violation in run-03 turn 10, corrected in retry — cost $0.024 vs avg $0.023)
- No crashes
- High narrative quality, detailed and coherent
- Large outcome variance (ai_capability 14.8–54.0) — expected for this scenario which has intentionally unstable dynamics
- Generates fewer completion tokens than Grok (~44k vs ~122k per run), contributing to low cost
- Cheapest tested model at ~$0.023/run

**Verdict:** Strong budget option. Stable, no constitutional violations, good narrative quality.

---

---

### qwen/qwen3-235b-a22b-2507 on the fixed prompt

**Tested on:** ai-safety-race (10 turns, completed, 2026-08-22, seed 20260821, `max_tokens: 3000`, **fixed actor prompt**)

The first model verdict in this project that rests on a correctly rendered actor prompt, and the strongest result recorded here.

- **9/10 turns approved cleanly** by the constitutional referee; turn 10 ended `max_attempts_reached`. Six turns needed a single referee iteration, three needed two
- **Zero arithmetic constitutional violations across all 10 turns**, checked independently against the constitution: no capability decrease (C6), no resource-tradeoff sum above 10 (C2), no safety erosion beyond -5 (C7), no coordination jump above 10 (C4), no belief shift above 15 (C3), and `catastrophe_threshold` held at exactly 70 throughout (C1)
- **Catastrophe mechanics exercised:** `us_capability` reached 72.5, crossing the immutable threshold of 70, and `global_catastrophe` fired
- **China now plays China.** Its safety metric rose 16 → 28.3 over the run. Under the broken prompt it sat frozen at a single value in every run by every model, because no actor ever argued China's side. This is the clearest confirmation that the prompt fix works
- 137s/turn at 185 tok/s; $0.0042/turn, ~$0.042 for the full run – the cheapest completed run of any model tested
- One rules-output truncation, which recovered

**One interruption, not a model failure.** The first attempt died at turn 3 with `Connection/timeout error … The read operation timed out` during the rules step: httpx's 120s read timeout fired correctly, but `FallbackRouter` classifies `LLMError` as non-retryable and moved on, and with a single configured route that ended the run. `resume` picked it up from turn 3 with no rework. See the robustness note below.

**Verdict:** Recommended, and now on evidence rather than inheritance. Best constitutional compliance, cheapest completed run, and second-fastest of everything tested.


### openai/gpt-5.4-nano

**Tested on:** sweden-ai-2030 (4 runs, 2026-04-01)

- Poor at following the scenario's formal game rules and output contracts
- 35/40 turns ended as `accepted_with_violations`; only 5/40 were approved after referee review, and only 1 turn was approved on the first pass
- Repeated rule-output formatting problems: fenced markdown wrappers, missing parseable changelog entries, and recurring "Metric rules header not found" warnings
- Metrics output was not reliable: one run produced empty `4-metrics.json` files in turns 8 and 9, and other runs produced partial metric payloads with only `ai_capability`
- The runs completed and persisted to disk, but mostly because the orchestrator tolerated malformed outputs and constitutional failures rather than because the model stayed within the rules
- More expensive than qwen/qwen3-235b-a22b-2507 while much worse at rule-following

**Verdict:** Avoid for full scenario runs where formal rule-following matters. GPT-5.4-nano is bad at following the game rules in Scenario Lab.

---

### google/gemini-2.5-flash

**Tested on:** ai-safety-race (1 run, 10 turns, ~$0.26/run)

- Constitutional violations in all 10 turns
- Most common problems: capability decreases (forbidden) not corrected, resource tradeoff violations, safety diminishing returns ignored, "accepted_with_violations" used as an escape instead of correction
- China's safety stagnated almost completely (15→16 over 10 turns) — model seems to misinterpret safety investments as unprofitable for China
- US capability reached max 49, China 43 — catastrophe mechanics not tested

**Verdict:** Avoid. Worse than older Gemini despite higher cost.

---

### moonshotai/kimi-k2

**Tested on:** ai-safety-race (1 run, 10 turns, cost unknown — no costs.json)

- Constitutional violations in 6/10 turns
- Critical problems: US capability fell 45.5→36.0 (–9.5 points) in turn 8, flagged but never corrected; coordination collapsed 17 points without narrative justification (max is 10); parse error in constitutional check turn 7
- Multiple turns received "accepted_with_violations" without correction
- US capability reached max 47.5 — catastrophe mechanics not tested
- Creative and detailed narratives, but poor rule-following undermines simulation integrity

**Verdict:** Avoid. Ignores constitutional corrections.

---

### anthropic/claude-haiku-4-5

**Tested on:** ai-safety-race (1 run, 10 turns, ~$1.30/run*)

- Worst tested — constitutional violations in all 10 turns, zero turns approved without comment
- Parse errors in turns 2, 4, and 6 meant constitutional referee was effectively skipped every third turn
- Recurring violations: simultaneous maximum investment in capability and safety without resource tradeoff (Constraint 2); beliefs changing too much without trigger events (Constraint 3); coordination jumping too fast (+14 in turn 5, Constraint 4/10); catastrophe probability calculated on actual metrics rather than actors' beliefs (Constraint 8)
- Catastrophe mechanics partially worked: US capability reached 70 in turn 8 but no event was evaluated until turn 9, then escalated to 41% → 99% probability
- Diplomatic overdrive — coordination and agreements advance too quickly

**Verdict:** Avoid. Most expensive tested model with worst results. Parse errors in constitutional referee are the critical issue.

---

### deepseek/deepseek-v3.2

**Tested on:** ai-safety-race (3 batch runs, all crashed)

- Crashed consistently at turn 1, step 5 (constitutional referee)
- Model ID received an automatic date suffix (`-20251201`) from the code which may have contributed
- No complete runs achieved

**Verdict:** Not usable without further debugging.

---

---

### mistralai/mistral-small-24b-instruct-2501

**Tested on:** ai-safety-race (1 run, 10 turns, 2026-08-21, seed 20260821)

- Only 1/10 turns approved cleanly by the constitutional referee; 8/10 ended `max_attempts_reached`, 1 ended `parse_error`
- Failure mode is specifically *referee* quality, not metric generation. As referee it hedges instead of judging – turn 1 produced "which is within the limit… however the narrative implies a more aggressive tradeoff" for four separate constraints, none of them actual violations. The correction loop cannot converge on non-violations, so every turn burns its attempts and continues regardless
- Metrics output itself was well-formed throughout: no empty or partial `4-metrics.json`, no hallucinated metric names
- Only 2 rules-output retries across the run
- Catastrophe mechanics were exercised: `us_capability` reached 71 against the immutable threshold of 70 and `global_catastrophe` fired – further than most tested models reach
- Cheapest completion pricing of any candidate, and the run completed without intervention at ~$0.022

**Verdict:** Avoid as a single model for all tasks. Might be worth retesting as the `metrics`/`actors` model with a stronger `referee`, since its metric contract compliance was clean and only its refereeing failed.

---

### qwen/qwen3-30b-a3b-instruct-2507

**Tested on:** ai-safety-race (1 run, **incomplete** – hung at turn 7, 2026-08-21, seed 20260821)

- Better constitutional compliance than mistral-small: 4/7 turns approved cleanly, 2 ended `max_attempts_reached`
- But much worse at output contracts. Across 6 completed turns: 4 rules-output truncations (`finish_reason=length`), 5 rules-policy retries, and 1 empty metrics file
- **Hallucinated metric names** not present in the scenario: `us_safety_investment`, `china_safety_investment`, `ai_incident`, and `notepad`. The last two are structural names from the framework leaking into the metrics payload, which suggests it is confusing prompt scaffolding for scenario content
- Final metrics were left incomplete (`us_capability`, `china_capability`, `coordination_level` all absent) – the same partial-payload failure recorded for gpt-5.4-nano
- Retries made turns slow and expensive: 130–172s per turn versus ~30s for mistral-small, and ~$0.021 for 6 turns (~$0.035 projected for 10) despite lower headline pricing
- **The run hung indefinitely on turn 7** – 23 minutes blocked on a single established HTTPS connection to OpenRouter with no bytes logged, at 1.9s total CPU. Killed manually

**Verdict:** Avoid. The hallucinated metric names and partial metric payloads are disqualifying on their own; the hang makes it unusable for unattended batches.

---

---

---

### deepseek/deepseek-v4-flash-0731

**Tested on:** ai-safety-race twice – 3 turns on the broken actor prompt (2026-08-21), then **10 turns to completion on the fixed prompt** (2026-08-22, seed 20260821, `max_tokens: 32000`, `call_timeout_seconds: 900`). The completed run supersedes the earlier one.

**Stability: excellent.** Ten turns, no crash, no transient retries, no rules truncation, no format-fix invocations, no hallucinated metric names, no empty or partial metrics payloads. It is the only reasoning model of the five tested that has ever finished a run. Structured outputs are supported natively.

**Actor differentiation confirmed the prompt fix.** Final metrics show China acting as itself – `china_capability` 43 against `us_capability` 51, and `china_belief_threshold` 70 against `us_belief_threshold` 56. Under the broken prompt `china_safety` sat frozen because both actors played the United States. That failure mode is gone.

**Constitutional compliance: poor, and this is the finding that matters.**

| Turn | Referee status | Iterations | Violated on first attempt |
|------|---------------|------------|---------------------------|
| 1–3 | approved | 1 | no |
| 4 | approved | 2 | yes |
| 5 | approved | 1 | no |
| 6, 7, 8 | approved | 2 | yes |
| 9, 10 | **max_attempts_reached** | 2 | yes, unresolved |

Six of ten turns produced constitutional violations on the first attempt. The referee corrected four of them. **Turns 9 and 10 hit `max_attempts_reached` and were persisted with the violations intact.**

Two violations recurred rather than being one-off slips:

- **`coordination_level` repeatedly breached its +10-per-turn cap** – +16 on turn 6, +12 on turn 7, +16 on turn 8. The model kept narrating diplomatic breakthroughs and moving the metric to match the story rather than to match the rule. It ended at 76.
- **`china_capability` decreased twice** (43→40, 43→41) although the constitution allows capability to fall only after catastrophic infrastructure destruction, which the narrative never described.

The pattern is consistent: it writes a plausible narrative and then sets metrics to fit the narrative, overriding explicit numeric constraints. That is a worse failure than a crash for unattended batch work, because the run completes and the artifacts look valid.

**Throughput and cost.** 565s/turn measured across the ten turns – 85 minutes for one run. $0.0671 and 566k tokens for 10 turns. The token figure is inflated by `max_tokens: 32000` and is not directly comparable with models run at default budgets; the wall-clock figure is real regardless.

**Verdict:** Avoid for unattended work. It has the best stability record of any reasoning model tested and is the only one to finish a run, but stability is not the same as compliance. At 565s/turn a 20-run batch would take over a day, and one turn in five would be persisted with an unresolved violation. `qwen/qwen3-235b-a22b-2507` remains the recommendation: 9/10 turns approved with zero arithmetic violations on the same scenario and fixed prompt, at roughly a quarter of the time per turn.


### minimax/minimax-m3

**Tested on:** ai-safety-race (5 turns requested, **crashed at turn 4**, 2026-08-21, seed 20260821, `max_tokens: 32000`, fixed actor prompt)

- First model evaluated after the actor-prompt fix, so its constitutional results are trustworthy
- 3/3 turns approved cleanly by the referee with a single iteration each, and no contract failures in those turns
- **Crashed in turn 4's events step** (`complete_structured`): `Response payload did not include assistant content`, three identical retries, then `All routes failed` killed the run
- Cause is reasoning-budget exhaustion: it spent the entire 32000-token budget on `reasoning` and emitted no content. Raising the budget did not help – it scaled its reasoning to fill the space
- The failure landed on the structured-output path, where schema conformance and open-ended reasoning appear to interact badly
- 224s/turn, 167 tok/s, $0.0179/turn (~$0.18 per 10 turns)

**Verdict:** Avoid until reasoning-budget exhaustion is handled by the engine. Quality while running was good; it simply cannot be trusted to finish.

---

### z-ai/glm-4.7-flash

**Tested on:** ai-safety-race (5 turns requested, stopped after 2 for being too slow, 2026-08-21, seed 20260821, `max_tokens: 32000`, fixed actor prompt)

- 2/2 turns approved cleanly, but only after a transient retry in turn 1
- **661s/turn, 70 tok/s – the slowest model tested by a wide margin.** Turn 1 alone took 892s, of which roughly 11 minutes was a single constitutional-referee call that produced no output while the process sat blocked on an open socket
- Hallucinated the metric name `metric_id` – the schema's own placeholder field name – echoed back as if it were a scenario metric
- Cheapest per run of the reasoning models at $0.0110/turn, but that is meaningless at this speed: a 10-turn run would take about 110 minutes

**Verdict:** Avoid. Not unstable enough to disqualify on correctness alone, but the throughput makes batch work impossible.


## Reasoning Models Are a Poor Fit

Probed 2026-08-21. Several of the cheapest current models are reasoning models that emit `reasoning` tokens before `content`:

| Model | Output tokens for a trivial JSON task | Reasoning model |
|-------|---------------------------------------|-----------------|
| openai/gpt-oss-120b | failed at max_tokens=50, needed 400 | yes |
| qwen/qwen3.7-flash | 220 | yes |
| z-ai/glm-4.7-flash | 190 | yes |
| deepseek/deepseek-v4-flash-0731 | 39 | yes |
| google/gemma-4-26b-a4b-it | 6 | no |
| qwen/qwen3-30b-a3b-instruct-2507 | 12 | no |
| mistralai/mistral-small-24b-instruct-2501 | 12 | no |

This matters because scenarios set `max_tokens` around 2000–3500. A reasoning model spends part of that budget before producing any content, so it will intermittently return nothing parseable, and the headline price understates real cost because reasoning tokens are billed. When the budget runs out mid-reasoning the provider raises `ValueError: Response payload did not include assistant content`, which is opaque about the real cause.

Prefer instruct (non-thinking) variants. This is consistent with the project's own history: the best-performing model tested here is `qwen3-235b-a22b-2507`, the instruct variant, while the thinking variant remains untested.

**Empirical record after testing five reasoning models (2026-08-21):**

| Model | Outcome |
|-------|---------|
| openai/gpt-oss-120b | Failed during probing; needed 400 tokens to answer a 12-token question |
| nvidia/nemotron-3-ultra-550b-a55b:free | Crashed turn 3 (`did not include choices`) |
| minimax/minimax-m3 | Crashed turn 4 (`did not include assistant content`) |
| z-ai/glm-4.7-flash | Survived, but 661s/turn and one hallucinated metric |
| deepseek/deepseek-v4-flash-0731 | Completed 10/10 turns with zero contract failures – the only reasoning model to finish a run |

Four of five failed or were unusable. The fifth finished, but see its assessment: surviving a run and reasoning within constraints turned out to be different things. Raising `max_tokens` to 32000 did not prevent budget exhaustion; the models scaled their reasoning to fill whatever budget they were given.

**Reasoning capability is discoverable before spending anything.** OpenRouter's `/models` endpoint lists `reasoning` in `supported_parameters`, and that flag matched empirical probing exactly across all six models checked. `audit-models` could warn on this without guessing.

## Robustness Gaps Found During Model Testing – All Fixed 2026-08-21

Four gaps turned model failures into run-destroying, undiagnosable events. All are now addressed; the model verdicts above were collected before the fixes.

- **No total request deadline** → fixed. `OpenRouterProvider` streams the response and enforces `llm.call_timeout_seconds` (default 300s) across the whole call, raising `LLMCallTimeoutError`. httpx's timeout applies per read, so a trickling provider reset it forever; calls were observed blocking 11–23 minutes at near-zero CPU. Streaming was chosen over a watchdog thread so nothing is orphaned when the deadline fires.
- **Reasoning-budget exhaustion retried blindly** → fixed. Empty content beside a populated `reasoning` field now raises `LLMReasoningBudgetError` naming the finish reason and token count. Being an `LLMError`, it makes the router move on rather than repeat three identical attempts that cannot succeed. This is what killed nemotron and minimax.
- **Provider errors discarded** → fixed. OpenRouter's own `error` object is included in the raised message, so a free-tier limit reads as a free-tier limit instead of "did not include choices".
- **`audit-models` blind to withdrawn and reasoning models** → fixed. It now checks the live catalog: a configured model absent from it is flagged as possibly withdrawn, and `supported_parameters` containing `reasoning` is flagged with the budget risk. `--offline` skips the check. Running it across `scenarios/` immediately flagged `x-ai/grok-4.1-fast` in six scenarios.

**Defaults migrated 2026-08-22.** `summary`, `analysis`, and `referee` now default to `qwen/qwen3-235b-a22b-2507`, and all seven scenarios plus the sweden-ai-2030 variants were swept off the withdrawn model. `_default_main` stays `google/gemini-3-flash-preview`: the catalog lists it as reasoning-capable, but probing shows it does not reason unprompted (11 output tokens for a trivial JSON task, no `reasoning` field), so it carries none of the budget risk.

The sweep exposed a further bug, now fixed. `validate_llm_config` predated the `ModelRoute` migration and still checked raw strings: single-model entries matched neither its `str` nor its `list` branch and **were never validated at all**, while every fallback list failed with "invalid model in fallback list" regardless of contents. `is_valid_model_route` replaces it and is provider-aware, since `vendor/model` is an OpenRouter convention that Anthropic ids such as `claude-sonnet-4-6` do not follow. All seven scenarios validate cleanly for the first time.

## Other Qwen3-235b Variants (pricing only, not tested)

| Model | Prompt/M | Completion/M | Notes |
|-------|----------|--------------|-------|
| qwen/qwen3-235b-a22b | $0.455 | $1.82 | Older variant |
| qwen/qwen3-235b-a22b-thinking-2507 | $0.15 | $1.50 | Thinking mode |

## Not Yet Tested

- google/gemma-4-26b-a4b-it (non-reasoning, $0.05/$0.25 – the most promising untested budget candidate)
- meta-llama/llama-3.3-70b-instruct
