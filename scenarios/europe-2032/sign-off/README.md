# Prompt sign-off

Generated from `run-20260829-192725`. These documents exist because a scenario file that never reaches a prompt changes nothing, and nothing else in the pipeline will tell you which ones those are.

Read them once when the scenario is built, and again after any change to the templates, the scenario's prompt overrides, or the background files. Sign off by saying so in the scenario's design notes, with the date.

## Documents

- [actor-turn-1](actor-turn-1.md) – `sign-off/actor-turn-1.md`
- [actor-turn-2](actor-turn-2.md) – `sign-off/actor-turn-2.md`
- [game-master-turn-2](game-master-turn-2.md) – `sign-off/game-master-turn-2.md`
- [events-turn-2](events-turn-2.md) – `sign-off/events-turn-2.md`

## Source coverage

Every heading in the scenario's background and definition files, and whether the text under it reached any of the prompts above. A **NO** is not automatically wrong, and there are three ordinary reasons for one. The heading may be documentation rather than instruction. Its content may reach the model through a different channel – an event's prose section is design rationale, while the operative text is the per-event `Condition:` and `Probability:` fields the events prompt renders from. Or it may belong to a mechanism that only becomes live in a later turn than the two sampled here, which these documents cannot show and whose absence proves nothing. What a **NO** must never be is unexamined: the failure this whole exercise exists to catch looks exactly like one of the three benign cases until you check.

| source file | heading | in a prompt |
|---|---|---|
| `background/actors/eu.md` | Short description | yes |
| `background/actors/eu.md` | Long description | yes |
| `background/actors/eu.md` | What you are | **NO** |
| `background/actors/eu.md` | Your instruments | **NO** |
| `background/actors/eu.md` | Your mandate — two purposes, unreconciled | **NO** |
| `background/actors/eu.md` | One proposal per turn, and a stated priority | **NO** |
| `background/actors/eu.md` | Your standing commitment | **NO** |
| `background/actors/eu.md` | How a measure is stated | **NO** |
| `background/actors/eu.md` | The categories, with one anchor each | **NO** |
| `background/actors/eu.md` | How every measure is judged | **NO** |
| `background/actors/eu.md` | Implementation phases | **NO** |
| `background/actors/eu.md` | Scope | **NO** |
| `background/actors/eu.md` | What you do not know | **NO** |
| `background/actors/eu.md` | Statements | yes |
| `background/actors/eu.md` | Behavioral traits | yes |
| `background/context.md` | What this simulation is for | yes |
| `background/context.md` | The starting point | yes |
| `background/context.md` | The frontier | yes |
| `background/context.md` | Washington took control of frontier models in three months | yes |
| `background/context.md` | Incidents and new capabilities | yes |
| `background/context.md` | Where the EU stands | yes |
| `background/context.md` | What is genuinely contested | yes |
| `background/context.md` | The Union's problem | yes |
| `background/fixed-facts.md` | Fixed facts, as of the second half of 2026 | yes |
| `background/fixed-facts.md` | The frontier | yes |
| `background/fixed-facts.md` | Washington holds the frontier | yes |
| `background/fixed-facts.md` | What has already gone wrong | yes |
| `background/fixed-facts.md` | Where the Union stands | yes |
| `background/fixed-facts.md` | The Union's problem | yes |
| `constitution.md` | Invariants | yes |
| `constitution.md` | Modelling choices | yes |
| `events.md` | The gate mechanism | **NO** |
| `events.md` | Regime conditioning | **NO** |
| `events.md` | Arithmetic of probabilities | **NO** |
| `events.md` | Measures referred to in conditions | **NO** |
| `events.md` | The opening turn | **NO** |
| `events.md` | The 2028 US presidential election | **NO** |
| `events.md` | Test Shot Against Critical Infrastructure | **NO** |
| `events.md` | Anti-AI Backlash Becomes a Campaign Platform | yes |
| `events.md` | Security Hawks Set the Terms | yes |
| `events.md` | The Alliance Argument Gains Ground | yes |
| `events.md` | The 2028 US Presidential Election – Consolidation | yes |
| `events.md` | The 2028 US Presidential Election – Alliance | yes |
| `events.md` | The 2028 US Presidential Election – Retrenchment | yes |
| `events.md` | Major Cyber Incident | yes |
| `events.md` | Defensive Breakthrough | yes |
| `events.md` | Human-Infective Design Demonstrated | yes |
| `events.md` | Biological Incident | yes |
| `events.md` | Evaluation Anomalies Surface | yes |
| `events.md` | Capability Jump | yes |
| `events.md` | Recursive Self-Improvement Begins | **NO** |
| `events.md` | Verification Frontier Widens | yes |
| `events.md` | Evidence of a Bending Curve | yes |
| `events.md` | Reasoning Stops Being Legible | **NO** |
| `events.md` | Medicine Delivers | **NO** |
| `events.md` | Open Weights Reach the Frontier | **NO** |
| `events.md` | Loss-of-Control Incident | yes |
| `events.md` | Assurance Breakthrough | yes |
| `events.md` | Labour Displacement Wave | **NO** |
| `events.md` | AI Investment Collapse | yes |
| `events.md` | Taiwan Tension Rises | yes |
| `events.md` | Taiwan Blockade | yes |
| `events.md` | Export Control Escalation | yes |
| `events.md` | Narrow Binding Agreement | **NO** |
| `events.md` | An Election Is Voided | yes |
| `events.md` | Frontier Access Denied | yes |
| `events.md` | Coercion Over ASML | yes |
| `events.md` | Access Secured on Its Own Terms | yes |
| `events.md` | Member State Defection | yes |
| `events.md` | Backlash Turns Physical | **NO** |
| `events.md` | Adoption Delivers | yes |
| `events.md` | Automated Decision Scandal | yes |
| `metric-rules.md` | Metric Rules | yes |
| `metric-rules.md` | The frontier | yes |
| `metric-rules.md` | The incident engine | yes |
| `metric-rules.md` | The Union's two stocks | yes |
| `metric-rules.md` | The public and the world's mood | yes |
| `metric-rules.md` | What the Union does not control | yes |
| `metrics.md` | Metrics | **NO** |
| `metrics.md` | ai_capability | yes |
| `metrics.md` | openweight_capability | yes |
| `metrics.md` | ai_safety | yes |
| `metrics.md` | resilience | yes |
| `metrics.md` | eu_ai_sovereignty | yes |
| `metrics.md` | eu_political_capital | yes |
| `metrics.md` | public_sentiment | yes |
