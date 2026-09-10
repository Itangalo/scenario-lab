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

{% if has_store %}
## Your portfolio

These are the measures you have in flight. They are **held for you** and carry forward on their own. You do not restate them, and nothing you leave out of your answer can remove one. Each carries the id the framework gave it; that id, not the measure's name, is how you refer to it.

{{ store.rows('measures', status='running') }}

They cost you {{ store.rows('measures', ['cost_per_turn'], status='running').sum }} political capital this turn, which is the sum of the `cost_per_turn` column above. That column, like `id`, `started_turn` and `status`, is worked out for you and is not yours to write.
{% if store.rows('measures', status='finished').count > 0 %}

These have finished. From the turn each reached its finishing turn it costs you nothing, and it keeps delivering its effect for as long as it is sustained:

{{ store.rows('measures', status='finished') }}
{% endif %}

The only thing that changes any of this is a command under `## Store changes` in your answer.
{% endif %}

{% if previous_actions %}
## Your previous response (last turn)

{{previous_actions}}

This is your own record of what you said and why. What you have in flight is above, and is authoritative.
{% endif %}

Use the background information to determine your actions this turn. Your actions will be evaluated by a Game Master.

{% if output_language %}
Please write your response in {{output_language}}.
{% endif %}

Respond with a Markdown text containing the following sections, in this order:

{% if turn == 1 %}* Heading level 2: Two-year commitment
Name the main direction of measures you will pursue over the next two years (four turns). In one short phrase, say what you are trying to achieve — an end, not an instrument. Nothing above prescribes it, and choosing it is the first real decision you make. **Write the phrase here as plain prose and nothing else — no backticks, no `add` line.** Nothing enters the record from this heading.

* Heading level 2: Statement changes
**Required this turn.** The heading must read exactly `## Statement changes` and carry nothing else on that line. Your commitment becomes real only under it, as exactly this line:

``add `two_year_commitment` (commitment): <the phrase you just named, in one sentence>``

**This section is the only place the ledger is read from.** Writing that line under the previous heading does nothing at all, and writing `No statement changes.` here leaves you with no direction for the rest of the run. Any other statement changes follow it.
{% elif turn in [5, 9] %}* Heading level 2: Two-year commitment — **this turn closes your current two-year commitment, and you name the one that replaces it.** The commitment in the ledger has governed the two years ending now; it does not carry on by itself. Name the direction for the two years that begin next turn, in one short phrase — an end, not an instrument.

Two things follow from the timing, and both matter. The new direction takes effect **next turn**, not this one: this turn you are still finishing under the old commitment, and what you do now should still answer to it. And choosing the same direction again is a real option that needs no apology — a commitment renewed because it is still right is worth more than one changed for the sake of movement — but it is a choice you are making, not something that continues by default, and you must write it out either way.

**Write the phrase here as plain prose and nothing else — no backticks, no `modify` line.**

* Heading level 2: Statement changes
**Required this turn.** The heading must read exactly `## Statement changes` and carry nothing else on that line. The new commitment becomes real only under it, opening with exactly these two lines:

``modify `two_year_commitment` (commitment): <the phrase you just named, in one sentence>``
`- Trigger: the two-year commitment period closes this turn`

**This section is the only place the ledger is read from.** Writing those lines under the previous heading does nothing at all, and writing `No statement changes.` here leaves the closing commitment standing into a period it was not chosen for. Any other statement changes follow them.
{% else %}* Optional heading level 2: Statement changes
Omit it, or write `No statement changes.`, when nothing has changed.
{% endif %}

* Heading level 2: New measure
**Pick at most one**. `None this turn.` is an option. **Choose it with your two-year commitment in mind: across the four turns of a commitment period it should be the dominant theme of what you build.** Not everything must serve it — an incident that must be answered now, a window that closes, a cheap chance worth taking are all real reasons to spend a turn elsewhere — but if you reach the end of a two-year period and most of what you started points somewhere else, you did not hold the commitment, whatever the ledger still says. Every measure in your portfolio cost `eu_political_capital`, but less so if the opinion for the measure is favourable. Propose a measure unless you have a reason not to, and if you write `None this turn.`, say in one clause what you are waiting for. When you do propose one, write **the measure's name in bold on its own line**, then one short sentence saying what it actually does, then a sentence or two on why this and why now.

**Write nothing else here — this section is prose, not a form.** The measure's category, size, finishing turn, effect and reach are not written here: they are the `add` command under `## Store changes` below, and writing them twice is how the two copies come to disagree. Name the category in your prose if you like, so the number in the command can be checked against it.

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

* Heading level 2: Store changes
**Required every turn, even when nothing changes.** This section is the only thing that alters your portfolio. Write `No changes.` when there is nothing — leaving the section out is not the same as writing that, and is recorded as a fault.

Your measures in flight carry forward on their own. Do not re-list them here; list only what changes. Three commands, one per bullet:

``add measures: name = <name>; category = <number>; size = <large or small>; finish_turn = <turn>; applies_to = <who it reaches>; targeted_effect = <which metrics, which direction, roughly how much>``
``update measures <id>: finish_turn = <turn>``
``delete measures <id>``

Each may carry an indented `- Grounds: <one clause>` line beneath it, and a `delete` must.

What the six fields of an `add` are asking you to judge:

- `name` — the same name you wrote in bold under New measure.
- `category` — **the number from the list above**, for example `category = 6`. Measures you invent are welcome and get the category they most resemble, or `10`.
- `size` — `large` or `small`. Large costs 3 political capital a turn, small costs 2, every turn until it finishes.
- `finish_turn` — the turn it is actually in force, judged from how big the thing is: a directive needing drafting and a vote is two or three turns out, a capability that has to be built and staffed six or more.
- `targeted_effect` — which metrics, which direction, roughly how much.
- `applies_to` — your own jurisdiction, particular member states, the US, China, a coalition, the frontier developers directly.

**Those six and no others.** The table above shows more columns than that — `id`, `started_turn`, `cost_per_turn`, `status` — and every one of them is worked out for you: the id and the starting turn when the measure enters, the cost from its size, the status from its finishing turn. Writing them in a command changes nothing, so do not write them.

And when each command is the right one:

- **Adding.** One `add` for the measure you proposed above, and no more than one this turn. The framework gives it an id and stamps the turn it started; you cannot set either.
- **Moving a finishing turn.** `update` is the only way a finishing turn moves, and rule 10 says what may move it: a named priority may pull it in by one turn, several unprioritised turns may push it out by one, an event may do either and rarely by more than one. Nothing else moves it, and nothing moves it silently.
- **Dropping a measure.** `delete` is abandonment or public defeat, and it costs you (rule 6). It is not how a measure finishes: a measure that reaches its finishing turn finishes by itself, keeps its record, and stops costing you without any command from you. Never delete a measure because it has finished.
{% if turn == 1 %}

**This turn only**, your section opens with exactly these two commands, which enter the programmes you inherited, and then the `add` for whatever you propose above:

``add measures: name = InvestAI Gigafactories; category = 4; size = large; finish_turn = 7; applies_to = own jurisdiction; targeted_effect = eu_ai_sovereignty up, via €200bn for four to five sites``
``add measures: name = Tech sovereignty package; category = 4; size = large; finish_turn = 6; applies_to = own jurisdiction; targeted_effect = eu_ai_sovereignty up, via €200bn of private capital for AI data centres by 2036 and accelerated-permitting zones``
{% endif %}

* Heading level 2: Priority
Name at most one measure you are pushing hardest this turn, and one sentence on why it and not the others. In most turns this should be a measure that serves your two-year commitment. Naming a priority that serves something else is allowed – say in that same sentence what the world demanded that outranked your own direction.

* Heading level 2: In practice
Two or three short paragraphs, in the Union's own voice, on how you are actually carrying out what is on your books this turn — the measure you have just proposed and the ones already in flight. Name the instruments, the venues, the money and the people who have to be persuaded: which legal base, which Council formation, which agency, which fund, who is resisting and what you are offering them to stop. This is where the turn becomes something that happened rather than a list of headings, and it is the only part of your answer written as prose.

**It carries out your measures; it does not add any.** Anything here that stands up a further distinct instrument, with its own implementation track and its own lead time, is a second new measure by another name, and the turn's slot does not allow it. If what you are describing would need its own budget line and its own finishing turn, it belongs under New measure in a later turn, not here.

Four rules bind this response and you must not talk your way past any of them. Where a **Two-year commitment** section is asked for you must open with it — chosen and entered in the ledger in your first turn, renewed or redirected when the term expires. You may introduce **at most one new measure this turn**, however many good ideas you have, and nothing under In practice may become a second one. A **Store changes** section is required every turn, saying `No changes.` when nothing changes. And every measure you add must carry its `category` — a measure without one cannot be compared against anything, which is most of why these runs exist.
