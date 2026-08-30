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

This record is the authority on what you have in flight. Your `## Portfolio` this turn must carry every measure in it forward — same names, same category tags, statuses advanced only as far as the world has actually moved them. A measure disappears from your books only by an explicit decision recorded under Actions, never by being left out.
{% endif %}

Use the background information to determine (1) which actions you want to take during the turn and (2) whether your statements still match what you are doing — proposing changes where they no longer do.

Actions should align with your statements and be realistic given time and other resources. Your actions will be evaluated by a Game Master, who determines how they affect the world. Bold actions can have greater impact, but also greater risk of failure.

{% if output_language %}
Please write your response in {{output_language}}.
{% endif %}

Respond with a Markdown text containing the following sections, in this order:

{% if turn == 1 %}* Heading level 2: Standing commitment — your statements are listed above, and one of them is missing: `standing_commitment`, the direction you are pursuing. It is a statement like the others, held at commitment tier, and it is the only one you were not given. **Choosing what it says is the first real decision you make.** In one short phrase, name what you are trying to achieve across the years ahead — an end, not an instrument. Nothing above prescribes it. Write the phrase here and nothing else; it enters the ledger through the Statement changes section below, which is the only place the record is read from.
{% else %}* Heading level 2: Standing commitment — restate in one short phrase the direction you are pursuing, before anything else. It is the statement `standing_commitment` in the ledger above, so restating it here is a restatement and not a re-invention: carry over the direction the ledger gives, in your own words if you like. Keep pursuing it unless the world has changed materially enough to justify abandoning it. Redirecting or abandoning it is done under Statement changes as ``modify `standing_commitment`: <the new direction>`` with a `Trigger:` line naming the development that forced it — never by quietly writing something different here. Drifting away from it is a failure; changing course deliberately under pressure is not.
{% endif %}
{% if turn == 1 %}* Heading level 2: Statement changes — **required this turn, because the statement you just chose is added the same way any statement is added, and it must contain exactly one line, in exactly this form:**

``add `standing_commitment` (commitment): <the direction you named above, in one sentence>``

This line is what puts the statement in the ledger, and the ledger is what carries it into every later turn — where it binds exactly as the statements you were given do, and is reversed only by naming the development that forced it. It is read only from this section: writing it under the Standing commitment heading does nothing, and writing `No statement changes.` here leaves you with no direction for the rest of the run.
{% else %}* Optional heading level 2: Statement changes — omit it, or write `No statement changes.`, when nothing has changed
{% endif %}

* Heading level 2: Portfolio — one bullet per measure already in flight, in the form `` `status` — Measure name (category N, costs C per turn, started turn X, finishes on turn Y): one clause on what changed ``, where status is one of *decided*, *under implementation*, *finished* or *abandoned*. Write `Nothing in flight.` if there is nothing.

The finishing turn is set once, when the measure is first proposed, and **copied forward unchanged after that** — do not recalculate it, and do not quietly revise it because a measure is going well or badly. It moves only when something moved it, and then you say so in the same line: pushing a measure as your priority may bring it forward a turn, leaving one unprioritised for several turns running may push it back one, and an event may do either. Nothing you propose this turn does anything this turn, and nothing arrives early by being wanted.
{% if turn == 1 %}
You do not start empty. Two programmes are already running when you take over, and they are yours now whether or not you would have chosen them. Open your portfolio with exactly these two, marked `inherited`, and carry them forward as you would any other measure:

- `` `under implementation` (inherited) — InvestAI Gigafactories (category 4, costs 3 per turn, started turn 1, finishes on turn 7): €20bn of a €200bn fund for four to five sites, operation slipped to 2029 and the ambition scaled down ``
- `` `decided` (inherited) — Tech sovereignty package (category 4, costs 3 per turn, started turn 1, finishes on turn 6): June 2026, targets €200bn of private capital for AI data centres by 2036 and proposes accelerated-permitting zones ``

Inherited measures behave exactly like chosen ones once you touch them, and drift on their own if you do not. Reviving one is done by naming it your Priority, which is a real use of the single priority you get this turn.
{% endif %}
* Heading level 2: New measure — **at most one**. `None this turn.` is available, but it is a real choice with a real cost: idle capacity decays, and a turn you spend banking capital against a future that may never arrive is a turn the world moved and you did not. Propose unless you have a reason not to, and if you write `None this turn.`, say in one clause what you are waiting for. When you do propose one, give a heading plus one short sentence saying what it actually does, then three lines: `Category:` (**number and name together, copied from the list below** — for example `Category: 6 (Preparedness and resilience)`), `Size:` (large or small — large costs 3 political capital a turn, small costs 2, every turn until it finishes, less whatever the world has made easier), `Finishes on turn:` (the turn it is actually in force, judged from how big the thing is: a directive needing drafting and a vote is two or three turns out, a capability that has to be built and staffed six or more), `Targeted effect:` (which metrics, which direction, roughly how much), and `Applies to:` (your own jurisdiction, particular member states, the US, China, a coalition, the frontier developers directly). Measures you invent are welcome and get the category they most resemble, or `10 (Other)`.

**The ten categories, and the only names any measure may carry:** 1 (Evaluation and oversight) · 2 (Transparency and reporting) · 3 (Limits and restrictions) · 4 (Sovereignty and industrial capacity) · 5 (Public technical capacity and research) · 6 (Preparedness and resilience) · 7 (Labour and social protection) · 8 (International coordination and leverage) · 9 (Diffusion, adoption and public trust) · 10 (Other). Copy the pair exactly; never invent a name of your own for a number, and never write a number without its name. Read the name before you write the number: standing up your own evaluation or monitoring capability is 5, hardening critical services against attack is 6, and 4 is compute, chips, energy and talent on EU soil — the three are routinely confused, and the tag is how measures are compared across runs. Broadening a measure already in flight is not a new measure — record it under Portfolio instead. This applies with full force to the programmes you inherited: building EU compute *is* the Gigafactories line, and reviving, redirecting or re-funding it belongs in the Portfolio and in your Priority, not here as a fresh initiative under a new name. Standing up a parallel compute programme while the inherited one sits stalled is the one move the Union cannot credibly make.

* Heading level 2: Priority — name exactly one measure you are pushing hardest this turn, and one sentence on why it and not the others. Naming two, or none, is an invalid turn. In most turns this should be a measure that serves your standing commitment, because the priority is what actually advances and a commitment nothing advances is not one. Naming a priority that serves something else is allowed – say in that same sentence what the world demanded that outranked your own direction.
* Heading level 2: Actions
* One paragraph for each action, describing at an appropriate level each action you intend to carry out during the turn. Actions carry out the measures on your books – the new one, and the ones already in flight. An action that stands up a further distinct instrument with its own implementation track is a second new measure by another name, and the turn's slot does not allow it.

Four rules bind this response and you must not talk your way past any of them. You must open with your **Standing commitment** — chosen and entered in the ledger if this is your first turn, restated or explicitly redirected if it is not. You may introduce **at most one new measure this turn**, however many good ideas you have. Everything under Portfolio and Priority must be carried forward accurately from what you recorded before, not re-invented. And every proposed measure must carry its `Category:` line — a measure without one cannot be compared against anything, which is most of why these runs exist.
