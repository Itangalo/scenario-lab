It is now turn {{turn}} which covers {{time_period}}.

The Metric Rules looked like this (possibly updated):

{{metric_rules}}

The world state at the start of the turn is described as follows:

{{world_state}}

---

The notepad contains the following information:

{{notepad}}

---

This turn, the following external events have occurred:

{% if triggered_events %}
{{triggered_events}}
{% else %}
None
{% endif %}

---

The actors in the scenario describe their actions as follows:

{{actor_actions}}

---

Use this information to assess whether Metric Rules should be updated based on what has happened in the world and what the actors have done.

Respond with an updated list of Metric Rules in the same format as before.
