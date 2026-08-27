# Metric rules – design notes

(ECHO 2026-08-27) Worked out in conversation 27 August 2026, before any rules file exists. This is the physics the scenario should implement, not the file itself. The seven metrics are defined in `../metrics.md`.

## Naming

Two metrics are renamed so the split between them is visible in the names themselves.

- `eu_ai_sovereignty` (was `eu_ai_autonomy`) – the AI muscles the Union has: compute on its own soil and under its own law, frontier-level talent, the ability to run capable systems nobody else can switch off, and the bargaining position that follows.
- `eu_political_capital` (was `eu_room_to_act`) – the political and therefore economic capital available for AI policy: what can be started, funded, enforced and held together at once.

"Room to act" sounded like a capability, which is where the two blurred. "Sovereignty" is the term of art for the first bundle and speaks to the Europe 2031 readership in its own vocabulary; its one cost is that it sounds normatively good where "autonomy" was neutral. A minimal alternative is to rename only the capital metric, which removes most of the confusion on its own.

## The lever map

Sort the seven by how far the EU can actually move them. This ordering determines everything else.

- Strong: `resilience`, `eu_ai_sovereignty`, `eu_political_capital`.
- Moderate: `public_sentiment`.
- Weak: `ai_safety` and `openweight_capability` – reach only through market-access conditions and international agreement.
- Nearly none: `ai_capability`.

This is uncomfortable and it is correct. The EU does not set the frontier's pace, and rules that let it turn the scenario into a fantasy. The payoff is that the strategic question falls straight out of the map: spend on what you control, or spend trying to influence what you do not.

## Capability

`ai_capability` is exogenous, with exactly one exception: an international agreement that actually binds both leading powers. That should be rare, expensive and reversible – a lever that exists without being cheap.

Growth rates are arm-defining and must appear **only** in `variants/*.rules.patch.md`. Any rate in the base file leaks the trajectory.

Growth should be sub-linear near the top of the scale, so the acceleration arm does not pin at 100 and censor the arm that separates most clearly. Where end values are censored anyway, report time-to-threshold instead.

## Open weights

`openweight_capability` tracks `ai_capability` at a lag, and the lag is the policy-relevant variable. It narrows by default – distillation and efficiency gains are the normal state, not an event – and widens only with release restrictions that actually bind. It never exceeds `ai_capability`.

## The incident engine – two channels

Frequency and severity come from different places, and the two channels keep all four risk metrics load-bearing.

- **Misuse incidents** (cyber and biological harm caused by an actor who wants it) are driven by `openweight_capability`. Proliferated capability is what a non-state attacker actually has in hand.
- **Accident and loss-of-control incidents** are driven by the gap between `ai_capability` and `ai_safety`. These originate inside the laboratories, where assurance is the thing that failed.
- **Both are damped by `resilience`**, which governs severity rather than frequency.

Stated compactly: frontier capability creates the possibility, open capability creates the frequency, safety prevents the lab-origin class, resilience shrinks the consequences of both. A single-channel engine would leave one of the four decorative.

## Safety

`ai_safety` measures assurance that has landed on deployed systems, not effort spent. It therefore falls when capability advances without matching assurance – it can drop sharply with no reduction in spending at all. Sharp falls belong with `opaque_reasoning`, `capability_jump` and `rsi_onset`.

EU leverage over it is weak by construction: market-access conditions, international agreement, and pressure on developers who need the single market. That weakness is the point.

## Two insurance metrics

`resilience` insures against incidents; `eu_ai_sovereignty` insures against coercion. Neither prevents the event – the attack still lands, access still gets denied – they change what it costs.

Both should decay in relative terms as `ai_capability` rises, because a static defence weakens against a moving offence. Standing still has to cost something, or every run builds once and coasts.

Sovereignty is slow in both directions. Compute takes years, and that slowness is what makes late action expensive and the timing question real.

## Sovereignty and political capital

**The flow costs, the stock pays.** Building sovereignty drains political capital while it is being built – that is the implementation load the actor already carries. Having sovereignty pays capital back: something to bargain with, successes to point at, less humiliation feeding sentiment.

This produces the timing dynamic the document is about. Early investment is expensive exactly when capital is scarce, and it compounds. Late investment costs the same and never gets to compound.

**Guard:** sovereignty must remain a contributor to political capital, never the dominant term. Europe 2031's claim is not that muscles help but that muscles are *necessary* – that without compute there is no agency at all. If sovereignty dominates the capital equation, the rules assume that conclusion instead of testing it. Runs must still be able to reach 2032 with real political capital and little sovereignty, on cohesion, instruments and legitimacy alone.

## Political capital – the attribution rule

Negative events move `eu_political_capital` in **either** direction, and the sign follows from the world rather than from the Game Master's judgment. It is a function of two things already on the record: where the harm originated, and whether the EU had acted beforehand.

- External origin, prior action taken: reads as vindication. Capital rises.
- External origin, no prior action: reads as *why did you not see this coming*. Capital falls.
- Internal origin – an EU-deployed system, a regulatory failure, an automated-decision scandal: capital falls hard, regardless of anything else.

This makes the reader's earlier choices decide whether a shock strengthens or breaks them, which is the proactive-versus-reactive question rendered as mechanics instead of asked afterwards.

**Damper against the obvious exploit.** If every externally caused shock raises capital, the dominant strategy is to be attacked repeatedly by foreigners. The vindication bonus therefore decays when the same class of harm recurs and the response demonstrably did not work. Being attacked twice is someone else's fault; being attacked five times is your own.

## Political asymmetry, and the trade-off with attribution

A measure costs less political capital if a relevant incident occurred in the last few turns. Keep this alongside the attribution rule – together they are a genuine trade-off rather than a contradiction.

- Waiting makes the **next measure** cheaper.
- Acting early makes the **shock itself** strengthen you.

Neither dominates, and which one pays depends on an arm the reader cannot see. That is exactly the property a fork needs.

## Public sentiment

`public_sentiment` must move in both directions or it collapses into a single-dimensional goodness score. Low sentiment makes restriction cheap and makes adoption, infrastructure and any partnership with foreign providers expensive. High sentiment does the reverse.

It falls with incidents, labour displacement, visible dependency humiliation and price shocks; it rises with delivered benefit – `adoption_success`, `medical_breakthrough`, defensive wins.

## The divergence requirement

`eu_ai_sovereignty` and `eu_political_capital` must be able to move apart, since the claim that they are one quantity is what the scenario exists to test. Write explicit paths for both directions.

- Sovereignty rising while capital falls: a large compute push that eats political capital and provokes backlash.
- Capital high with sovereignty low: a cohesive Union with strong instruments and almost no compute – roughly 2026 itself.

If the rules never produce either, they have coupled the two and begged the question.
