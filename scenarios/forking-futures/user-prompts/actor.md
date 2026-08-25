{# Scenario override. Two deviations from templates/user-prompts/actor.md:
   1. Both background_context and world_state are truncated at the <!-- GM-ONLY -->
      marker. The starting-state draw places this run's trajectory regime after
      that marker, so the Game Master steps see which future the run is in and
      the regulator does not. Without this the regime would reach the actor
      through the fixed background and through the turn-1 narrative, and the
      scenario's central question -- how a regulator commits capital before it
      knows -- would collapse.
   2. The actor's own previous response is rendered as "Your previous response".
      The regulator has no other memory substrate: the notepad is Game-Master-
      only and the historical summary is a lossy condensation. In prototype runs
      without this block the Portfolio silently shed, renamed and reinvented
      measures between turns, which corrupts every measure-status mechanic
      (capital drain, lead times, fully-implemented effects) and the category
      grouping that rq_no_regret depends on.
   Keep in sync with the default template when that changes. #}
{% if background_context %}
## Fixed Background (unchanged all run)

This is the world as it stood at the start. It does not change, and it outranks
the evolving narrative on any fact it states — if the narrative drifts away from
something fixed here, the narrative is wrong.

{{ background_context.split('<!-- GM-ONLY -->')[0] }}

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
{{ world_state.split('<!-- GM-ONLY -->')[0] }}

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

* Optional heading level 2: Statement changes — omit it, or write `No statement changes.`, when nothing has changed
* Heading level 2: Portfolio — one bullet per measure already in flight, in the
  form `` `status` — Measure name (category N): one clause on what changed ``,
  where status is one of *decided*, *under implementation*, *fully implemented*
  or *abandoned*. Write `Nothing in flight.` if there is nothing.
* Heading level 2: New measure — **at most one**. `None this turn.` is
  available, but it is a real choice with a real cost: idle capacity decays, and
  a turn you spend banking capital against a future that may never arrive is a
  turn the world moved and you did not. Propose unless you have a reason not to,
  and if you write `None this turn.`, say in one clause what you are waiting
  for. When you do propose one, give a heading
  plus one short sentence saying what it actually does, then three lines:
  `Category:` (1-9), `Capital cost:` (low/medium/high), `Lead time:` (turns to
  full effect), `Targeted effect:` (which metrics, which direction, roughly how
  much), and `Applies to:` (your own jurisdiction, the US, China, a coalition).
  Broadening a measure already in flight is not a new measure — record it under
  Portfolio instead.
* Heading level 2: Priority — name exactly one measure you are pushing hardest
  this turn, and one sentence on why it and not the others. Naming two, or
  none, is an invalid turn.
* Heading level 2: Actions
* One paragraph for each action, describing at an appropriate level each action you intend to carry out during the turn.

Three rules bind this response and you must not talk your way past any of them.
You may introduce **at most one new measure this turn**, however many good ideas
you have. Everything under Portfolio and Priority must be carried forward
accurately from what you recorded before, not re-invented. And every proposed
measure must carry its `Category:` line — a measure without one cannot be
compared against anything, which is most of why these runs exist.
