# Model Testing Notes

Accumulated findings from running Scenario Lab scenarios with different LLMs. Use this when choosing a model for new runs or calibration.

Pricing should still be verified against OpenRouter before trusting older logged cost figures — newer runs use a cached OpenRouter pricing snapshot, but historical runs may reflect outdated pricing data.

## Summary

| Model | Prompt/M | Completion/M | Constitutional violations | Verdict |
|-------|----------|--------------|--------------------------|---------|
| google/gemini-2.0-flash-001 | $0.10 | $0.40 | 1/10 turns (ai-safety-race) | Recommended |
| x-ai/grok-4.1-fast | $0.20 | $0.50 | 0/10 turns (ai-safety-race) | Recommended |
| qwen/qwen3-235b-a22b-2507 | $0.071 | $0.10 | 0/40 turns (sweden-ai-2030) | Recommended |
| openai/gpt-5.4-nano | $0.20 | $1.25 | 35/40 turns accepted with constitutional violations (sweden-ai-2030) | Avoid |
| google/gemini-2.5-flash | $0.30 | $2.50 | 10/10 turns (ai-safety-race) | Avoid |
| moonshotai/kimi-k2 | $0.55 | $2.20 | 6/10 turns (ai-safety-race) | Avoid |
| anthropic/claude-haiku-4-5 | $1.00 | $5.00 | 10/10 turns (ai-safety-race) | Avoid |
| deepseek/deepseek-v3.2 | $0.27 | $1.10 | – | Avoid (crashes) |

## Cost per Run (10 turns, correct pricing)

| Model | Scenario | Avg cost | Avg tokens |
|-------|----------|----------|------------|
| qwen/qwen3-235b-a22b-2507 | sweden-ai-2030 | ~$0.023 | ~302k |
| openai/gpt-5.4-nano | sweden-ai-2030 | ~$0.14 | ~368k |
| google/gemini-2.0-flash-001 | ai-safety-race | ~$0.05 | – |
| x-ai/grok-4.1-fast | sweden-ai-2030 | ~$0.12 | ~388k |
| x-ai/grok-4.1-fast | ai-safety-race | ~$0.44* | – |
| anthropic/claude-haiku-4-5 | ai-safety-race | ~$1.30* | – |

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

## Other Qwen3-235b Variants (pricing only, not tested)

| Model | Prompt/M | Completion/M | Notes |
|-------|----------|--------------|-------|
| qwen/qwen3-235b-a22b | $0.455 | $1.82 | Older variant |
| qwen/qwen3-235b-a22b-thinking-2507 | $0.15 | $1.50 | Thinking mode |

## Not Yet Tested

- openai/gpt-4o-mini
- meta-llama/llama-3.3-70b-instruct
