Actor: {{actor_name}}

## The statement being changed

`{{statement_id}}` ({{statement_tier}}): {{statement_text}}

## What the actor proposes

{{proposal_summary}}

## The development the actor names as its trigger

{{trigger}}

## The inputs available this turn

### Events that occurred

{{triggered_events}}

### World state

{{world_state}}

{% if previous_actions %}
### What actors did last turn

{{previous_actions}}
{% endif %}

---

Find the named development in the inputs above and quote it verbatim. Then rule
whether it bears on this specific statement, or is merely something else that
happened. Respond with the JSON object only.
