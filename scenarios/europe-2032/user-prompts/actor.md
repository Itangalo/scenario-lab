{# Scenario override. One deviation from templates/user-prompts/actor.md: The actor's own previous response is rendered as "Your previous response". The EU has no other memory substrate: the notepad is Game-Master-only and the historical summary is a lossy condensation. In prototype runs without this block the Portfolio silently shed, renamed and reinvented measures between turns, which corrupts every measure-status mechanic (capital drain, lead times, fully-implemented effects) and the category grouping that rq_no_regret depends on.

   Also: the default template's "Fixed Background" block is deliberately absent. It renders background/context.md, or a compact restatement of it, in every prompt from turn 2 onward. This scenario does not want it. The opening description is 2026 news, not standing physics, and the run spends six years making most of it false -- a block asserting that it "outranks the evolving narrative" is right at turn 2 and wrong by turn 12. The cost is real and was measured rather than assumed: structural facts decay out of the rolling summary because nothing happens to them, and by turn 5 a summary retains no mention of ASML, of the compute gap, or of Mistral. That is accepted. Anything the Union must not forget for six years belongs in the metric rules or the event catalogue, which are read every turn, not in a block of background nobody re-reads.

   Keep in sync with the default template when that changes. #}
It is now turn {{turn}}, which covers {{time_period}}. Each turn covers {{ time_scale.replace(' per turn', '') }}, so that is the span your actions have to land in.

Current metrics look like this:

```json
{{metrics_json}}
```

The world state at the start of the turn is described as follows:

{% if historical_summary %}
## Previous History
{{historical_summary}}
{% endif %}

## Current Situation ({{time_period_lower}})
{{ world_state }}

---

{% if triggered_events %}
This turn, the following external events have occurred:

{{triggered_events}}
{% else %}
No special events occur this turn.
{% endif %}

---

{% if statement_ledger %}
## Your statements

{{statement_ledger}}

These carry forward unchanged unless you explicitly propose a change.
{% endif %}

{% if previous_actions %}
## Your previous response (last turn)

{{previous_actions}}

This record is the authority on what you have in flight. Your `## Portfolio` this turn must carry every measure in it forward. A measure disappears from your books only by an explicit decision recorded under Actions, never by being left out.
{% endif %}

Use the background information to determine your actions this turn. Your actions will be evaluated by a Game Master.

{% if output_language %}
Please write your response in {{output_language}}.
{% endif %}

Respond with a Markdown text containing the following sections, in this order:

{% if turn == 1 %}* Heading level 2: Two-year commitment
You must add a `commitment` describing the main direction of measures you want to take during the next two years (four rounds). It is a statement like the others, held at commitment tier. In one short phrase, name what you are trying to achieve across the years ahead — an end, not an instrument. Nothing above prescribes it. It must be exactly one line, in exactly this form:**

``add `two_year_commitment` (commitment): <the direction you named above, in one sentence>``

Write the phrase under this heading and nothing else.

* Optional heading level 2: Statement changes
Omit it, or write `No statement changes.`, when nothing has changed in the existing statements.
{% elif turn in [2, 6, 10] %}* Heading level 2: Two-year commitment — **your two-year commitment has run its term and expires this turn.** The one in the ledger covered the two years now ending; it does not carry into the next four turns on its own. Name the direction for the two years ahead, in one short phrase — an end, not an instrument.

Choosing the same direction again is a real option and needs no apology: a commitment renewed because it is still right is worth more than one changed for the sake of movement. But it is a choice you are making now, not something that continues by default, and you must write it out either way.

Write the phrase under this heading, and enter it in the ledger under Statement changes as:

``modify `two_year_commitment` (commitment): <the direction for the two years ahead>``
`- Trigger: the two-year commitment period ended this turn`

* Heading level 2: Statement changes — **required this turn**, and it must carry the two lines above. Any other statement changes follow them.
{% else %}* Optional heading level 2: Statement changes
Omit it, or write `No statement changes.`, when nothing has changed.
{% endif %}

* Heading level 2: Portfolio
One bullet per measure already in flight, copied straight from the portfolio passed onto you, on the form ``Measure name (category N, costs C per turn, started turn X, finishes on turn Y): short description``. Write `Nothing in flight.` if there is nothing.

A measure whose finishing turn the run has now reached is **finished**: say so on its line this turn, and drop it from the portfolio from the next turn on. It stops costing you political capital and keeps delivering its effect for as long as it is sustained. Finishing is the one way a measure leaves your books without a decision.
{% if turn == 1 %}
Open your portfolio with exactly these two, and carry them forward as you would any other measure:

- ``InvestAI Gigafactories (category 4, costs 3 per turn, started turn 1, finishes on turn 7): €200bn fund for four to five sites``
- ``Tech sovereignty package (category 4, costs 3 per turn, started turn 1, finishes on turn 6): Targets €200bn of private capital for AI data centres by 2036 and proposes accelerated-permitting zones``
{% endif %}
You may choose to drop measures from your portfolio, to save `eu_political_capital`. If you want to drop a measure, list them in the following way: ``Canceled measure: Name of measure.  Short statement on why you choose to cancel it.``

* Heading level 2: New measure
**Pick at most one**. `None this turn.` is an option. **Choose it with your two-year commitment in mind: across the four turns of a commitment period it should be the dominant theme of what you build.** Not everything must serve it — an incident that must be answered now, a window that closes, a cheap chance worth taking are all real reasons to spend a turn elsewhere — but if you reach the end of a two-year period and most of what you started points somewhere else, you did not hold the commitment, whatever the ledger still says. Every measure in your portfolio cost `eu_political_capital`, but less so if the opinion for the measure is favourable. Propose a measure unless you have a reason not to, and if you write `None this turn.`, say in one clause what you are waiting for. When you do propose one, give a heading plus one short sentence saying what it actually does, then five lines:
`Category:` (**number and name together, copied from the list below** — for example `Category: 6 (Preparedness and resilience)`). Measures you invent are welcome and get the category they most resemble, or `10 (Other)`.
`Size:` (large or small — large costs 3 political capital a turn, small costs 2, every turn until it finishes, less whatever the world has made easier).
`Finishes on turn:` (the turn it is actually in force, judged from how big the thing is: a directive needing drafting and a vote is two or three turns out, a capability that has to be built and staffed six or more).
`Targeted effect:` (which metrics, which direction, roughly how much).
`Applies to:` (your own jurisdiction, particular member states, the US, China, a coalition, the frontier developers directly).

**There are ten categories for measures, and only these may be used. Each carries an anchor — the measure it most typically means — and, in brackets, others that belong to it:**

1. **Evaluation and oversight.** Anchor: *Third-party pre-release evaluation* — independent assessment of a model's dangerous capabilities before release. (Also: audits, external review of testing procedures, pre-registration of training runs, agent-behaviour evaluations.)
2. **Transparency and reporting.** Anchor: *Incident reporting* — serious incidents and near-misses reported to a common body. (Also: whistleblower protection, shared safety cases, a public registry of deployed systems.)
3. **Limits and restrictions.** Anchor: *Intolerable-risk thresholds* — red lines that halt development or deployment when crossed. (Also: KYC for compute, prohibitions on high-risk applications, open-weight release thresholds, licensing regimes.)
4. **Sovereignty and industrial capacity.** Anchor: *Compute on EU soil* — data centres built and legally anchored inside the Union at a pace set by the race, not by ordinary permitting. (Also: accelerated siting and grid connection, electricity build-out, chip and lithography policy, retaining and attracting frontier talent, funding an EU frontier effort, partnership terms with foreign hyperscalers that bolt capacity to EU jurisdiction.)
5. **Public technical capacity and research.** Anchor: *Institution-building* — your own evaluation capability and funded safety research. (Also: vetted researcher access, advanced model access for public evaluators, weight-security audits, interpretability programmes.)
6. **Preparedness and resilience.** Anchor: *Contingency plans with exercises* — rehearsed procedures for fast-moving incident classes. (Also: cyber hardening of critical services, biological detection and response capacity, loss-of-control emergency protocols with escalation thresholds, cross-border mutual aid.)
7. **Labour and social protection.** Anchor: *Flexicurity-style transition* — wage insurance and retraining paired with employer flexibility to restructure. (Also: safety-net investment, transition funds tied to automating employers, reform of employment protection.)
8. **International coordination and leverage.** Anchor: *Middle-power coalition* — coordinating with other states holding pieces of the supply chain so that leverage is exercised jointly rather than picked off. (Also: binding accords, standing negotiation forums, mutual recognition of safety evaluations, export-control alignment, use of the Anti-Coercion Instrument.)
9. **Diffusion, adoption and public trust.** Anchor: *Public-sector adoption programme* — putting capable AI to work in health, administration and education. (Also: procurement rules that favour or exclude particular providers, digital signatures for trusted sources, regulation of AI companions aimed at minors, education programmes.)
10. **Other.** Anything fitting nowhere else, including combinations and inventions.

Categories 4, 7 and 9 are not decoration. Diffusion breadth buys economic gain but also attack surface and misuse exposure; public trust determines how much capital you have when incidents arrive; industrial and infrastructure pace feeds capability growth. If your strongest lever turns out not to point at the frontier at all, that is a real finding, not a mistake.
Copy the pair exactly; never invent a name of your own for a number, and never write a number without its name. Read the name before you write the number: standing up your own evaluation or monitoring capability is 5, hardening critical services against attack is 6, and 4 is compute, chips, energy and talent on EU soil — the three are routinely confused, and the tag is how measures are compared across runs. Broadening a measure already in flight is not a new measure — record it under Portfolio instead. This applies with full force to the programmes you inherited: building EU compute *is* the Gigafactories line, and reviving, redirecting or re-funding it belongs in the Portfolio and in your Priority, not here as a fresh initiative under a new name. Standing up a parallel compute programme while the inherited one sits stalled is the one move the Union cannot credibly make.

* Heading level 2: Priority
Name at most one measure you are pushing hardest this turn, and one sentence on why it and not the others. In most turns this should be a measure that serves your two-year commitment. Naming a priority that serves something else is allowed – say in that same sentence what the world demanded that outranked your own direction.

Four rules bind this response and you must not talk your way past any of them. You must open with your **Standing commitment** — chosen and entered in the ledger if this is your first turn, restated or explicitly redirected if it is not. You may introduce **at most one new measure this turn**, however many good ideas you have. Everything under Portfolio and Priority must be carried forward accurately from what you recorded before, not re-invented. And every proposed measure must carry its `Category:` line — a measure without one cannot be compared against anything, which is most of why these runs exist.
