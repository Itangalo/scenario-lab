# Prompt sign-off

Generated from `run-20260923-085922`. These documents exist because a scenario file that never reaches a prompt changes nothing, and nothing else in the pipeline will tell you which ones those are.

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
| `background/actors/alphabet.md` | Short description | yes |
| `background/actors/alphabet.md` | Long description | yes |
| `background/actors/alphabet.md` | Statements | yes |
| `background/actors/alphabet.md` | Behavioral traits | yes |
| `background/actors/china_government.md` | Short description | yes |
| `background/actors/china_government.md` | Long description | **NO** |
| `background/actors/china_government.md` | Statements | **NO** |
| `background/actors/china_government.md` | Behavioral traits | **NO** |
| `background/actors/tencent.md` | Short description | yes |
| `background/actors/tencent.md` | Long description | yes |
| `background/actors/tencent.md` | Statements | yes |
| `background/actors/tencent.md` | Behavioral traits | yes |
| `background/actors/us_government.md` | Short description | yes |
| `background/actors/us_government.md` | Long description | **NO** |
| `background/actors/us_government.md` | Statements | **NO** |
| `background/actors/us_government.md` | Behavioral traits | **NO** |
| `background/context.md` | January 2026: The Race Is On, the Rules Are Not | yes |
| `background/context.md` | The Four Players | yes |
| `background/context.md` | Compute, Taiwan, and Secrets | yes |
| `background/context.md` | What the Next Eight Years Decide | yes |
| `background/fixed-facts.md` | Fixed facts (standing restatement of context.md) | yes |
| `constitution.md` | Invariants (facts of this world, not modelling choices) | yes |
| `constitution.md` | Modelling choices (audited separately, kept small) | yes |
| `events.md` | Frontier Breakthrough | yes |
| `events.md` | Cyber Espionage Operation | yes |
| `events.md` | Model-Weight Exfiltration | **NO** |
| `events.md` | Taiwan Semiconductor Crisis | yes |
| `events.md` | Taiwan De-escalation | yes |
| `events.md` | Bilateral AI Summit | yes |
| `events.md` | Joint Safety Breakthrough | yes |
| `events.md` | Treaty Defection Exposed | **NO** |
| `events.md` | Preventive Strike Attempt | **NO** |
| `events.md` | Autonomous Weapons Deployment | **NO** |
| `events.md` | Warning-Shot AI Incident | **NO** |
| `events.md` | Outside-Startup Diffusion Shock | yes |
| `events.md` | US Presidential Election 2028 | yes |
| `events.md` | US Presidential Election 2032 | yes |
| `metric-rules.md` | Metric Rules v1 (Turn 0 – Initial) | **NO** |
| `metric-rules.md` | Rules | yes |
| `metric-rules.md` | Standing conditions | yes |
| `metrics.md` | us_capability | yes |
| `metrics.md` | china_capability | yes |
| `metrics.md` | safety_progress | yes |
| `metrics.md` | global_stability | yes |
| `metrics.md` | us_china_tension | yes |
| `metrics.md` | agreement_strength | yes |
| `research-question.md` | Research Question | **NO** |
| `research-question.md` | Why This Question | **NO** |
| `research-question.md` | Frame | **NO** |
| `research-question.md` | Criteria Check | **NO** |
| `research-question.md` | Out of Scope | **NO** |
| `research-question.md` | Approved | **NO** |
