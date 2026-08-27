{# Scenario override. One deviation from templates/user-prompts/actor.md:
   The actor's own previous response is rendered as "Your previous response".
   The EU has no other memory substrate: the notepad is Game-Master-only
   and the historical summary is a lossy condensation. In prototype runs without
   this block the Portfolio silently shed, renamed and reinvented measures
   between turns, which corrupts every measure-status mechanic (capital drain,
   lead times, fully-implemented effects) and the category grouping that
   rq_no_regret depends on.

   The regime is not hidden here any more. It reaches the Game Master through
   the variant's patched events and metric_rules, which are never rendered into
   an actor prompt, so there is nothing for this template to withhold. The
   <!-- GM-ONLY --> truncation this override used to carry is gone with the
   draws it was written for.
   Keep in sync with the default template when that changes. #}
{% if background_context %}
## Fixed Background (unchanged all run)

This is the world as it stood at the start. It does not change, and it outranks
the evolving narrative on any fact it states — if the narrative drifts away from
something fixed here, the narrative is wrong.

{{ background_context }}

{% endif %}It is now turn {{turn}} which covers {{time_period}}.

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

This record is the authority on what you have in flight. Your `## Portfolio`
this turn must carry every measure in it forward — same names, same category
tags, statuses advanced only as far as the world has actually moved them. A
measure disappears from your books only by an explicit decision recorded under
Actions, never by being left out.
{% endif %}

Use the background information to determine (1) which actions you want to take during the turn and (2) whether your statements still match what you are doing — proposing changes where they no longer do.

Actions should align with your statements and be realistic given time and other resources. Your actions will be evaluated by a Game Master, who determines how they affect the world. Bold actions can have greater impact, but also greater risk of failure.

{% if output_language %}
Please write your response in {{output_language}}.
{% endif %}

Respond with a Markdown text containing the following sections, in this order:

{% if turn == 1 %}* Heading level 2: Standing commitment — **this is your first turn, and you have no standing commitment yet. Choose one now.** In one short phrase, name the direction you intend to pursue across the years ahead: what you are trying to achieve, not which instrument you will use. It is yours to choose and nothing above prescribes it. Write the phrase here and nothing else — it is recorded in the Statement changes section below, and that is the only place the record is read from.
{% else %}* Heading level 2: Standing commitment — restate in one short phrase the direction you are pursuing, before anything else. It is held in your statement ledger under the id `standing_commitment`, so restating it here is a restatement and not a re-invention: carry over the direction the ledger gives, in your own words if you like. Keep pursuing it unless the world has changed materially enough to justify abandoning it. Redirecting or abandoning it is done under Statement changes as ``modify `standing_commitment`: <the new direction>`` with a `Trigger:` line naming the development that forced it — never by quietly writing something different here. Drifting away from it is a failure; changing course deliberately under pressure is not.
{% endif %}
{% if turn == 1 %}* Heading level 2: Statement changes — **required this turn, and it must contain exactly one line, in exactly this form:**

  ``add `standing_commitment` (commitment): <the direction you named above, in one sentence>``

  This line is what puts your commitment in the ledger, and the ledger is what carries it into every later turn. It is read only from this section: writing it under the Standing commitment heading does nothing, and writing `No statement changes.` here loses the commitment for the rest of the run.
{% else %}* Optional heading level 2: Statement changes — omit it, or write `No statement changes.`, when nothing has changed
{% endif %}
* Heading level 2: Portfolio — one bullet per measure already in flight, in the
  form `` `status` — Measure name (category N): one clause on what changed ``,
  where status is one of *decided*, *under implementation*, *fully implemented*
  or *abandoned*. Write `Nothing in flight.` if there is nothing – and on turn 1
  there is nothing. The programmes described in the fixed background (InvestAI,
  the Frontier AI Initiative, the Scientific Panel, the sovereignty package) are
  the world you inherited, not measures you chose; they belong in your reasoning
  and never in this list.
* Heading level 2: New measure — **at most one**. `None this turn.` is
  available, but it is a real choice with a real cost: idle capacity decays, and
  a turn you spend banking capital against a future that may never arrive is a
  turn the world moved and you did not. Propose unless you have a reason not to,
  and if you write `None this turn.`, say in one clause what you are waiting
  for. When you do propose one, give a heading
  plus one short sentence saying what it actually does, then three lines:
  `Category:` (**number and name together, copied from the list below** — for
  example `Category: 6 (Preparedness and resilience)`), `Capital cost:`
  (low/medium/high), `Lead time:` (turns to full effect), `Targeted effect:`
  (which metrics, which direction, roughly how much), and `Applies to:` (your
  own jurisdiction, particular member states, the US, China, a coalition, the
  frontier developers directly). Measures you invent are welcome and get the
  category they most resemble, or `10 (Other)`.

  **The ten categories, and the only names any measure may carry:** 1
  (Evaluation and oversight) · 2 (Transparency and reporting) · 3 (Limits and
  restrictions) · 4 (Sovereignty and industrial capacity) · 5 (Public technical
  capacity and research) · 6 (Preparedness and resilience) · 7 (Labour and
  social protection) · 8 (International coordination and leverage) · 9
  (Diffusion, adoption and public trust) · 10 (Other). Copy the pair exactly;
  never invent a name of your own for a number, and never write a number
  without its name. Read the name before you write the number: standing up your
  own evaluation or monitoring capability is 5, hardening critical services
  against attack is 6, and 4 is compute, chips, energy and talent on EU soil —
  the three are routinely confused, and the tag is how measures are compared
  across runs.
  Broadening a measure already in flight is not a new measure — record it under
  Portfolio instead.
* Heading level 2: Priority — name exactly one measure you are pushing hardest
  this turn, and one sentence on why it and not the others. Naming two, or
  none, is an invalid turn.
* Heading level 2: Actions
* One paragraph for each action, describing at an appropriate level each action you intend to carry out during the turn. Actions carry out the measures on your books – the new one, and the ones already in flight. An action that stands up a further distinct instrument with its own implementation track is a second new measure by another name, and the turn's slot does not allow it.

Four rules bind this response and you must not talk your way past any of them.
You must open with your **Standing commitment** — chosen and entered in the
ledger if this is your first turn, restated or explicitly redirected if it is
not. You may introduce **at most one new measure this turn**, however many
good ideas you have. Everything under Portfolio and Priority must be carried forward
accurately from what you recorded before, not re-invented. And every proposed
measure must carry its `Category:` line — a measure without one cannot be
compared against anything, which is most of why these runs exist.
