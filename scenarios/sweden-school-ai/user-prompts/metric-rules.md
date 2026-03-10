It is now turn {{turn}} which covers {{time_period}}.

The current Metric Rules are:

{{metric_rules}}

The world state at the start of the turn is described as follows:

{% if historical_summary %}
## Previous History
{{historical_summary}}
{% endif %}

## Current Situation ({{time_period_lower}})
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

Use this information to assess whether Metric Rules should be updated.

Scenario-specific guidance:
- Keep `school_readiness` as the bridge between policy/tool activity and real AI competence in schools.
- Treat `school_readiness` as sticky institutional capacity, not as a hype-sensitive metric.
- Treat `student_productive_use` and `student_critical_literacy` as different student outcomes with different drivers.
- `student_productive_use` should mainly follow teacher support, assessment redesign, and structured classroom practice.
- `student_critical_literacy` should mainly follow source-criticism work, deepfake/media literacy teaching, and broader civic/ethical discussion.
- Use small, defensible rule changes when possible; do not let one successful turn justify a wholly different growth regime.
- Preserve the sense that Swedish school systems scale through delayed implementation, not instant national rollout.

{% if output_language %}
Please write your response in {{output_language}}.
{% endif %}

Respond with an updated list of Metric Rules in the same format as before.
