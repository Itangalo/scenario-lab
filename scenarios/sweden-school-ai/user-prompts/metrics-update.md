It is now turn {{turn}} which covers {{time_period}}.

The Metric Rules looked like this (possibly updated):

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

Use this information to:

- Determine how successful the actors are with their actions.
- Based on the actors' actions and Metric Rules, determine Metrics for the next turn.
- Write a coherent narrative that tells what happens in the world during this turn.
- Update the notepad so delayed policy, implementation, and controversy effects are remembered.

Scenario-specific guidance:
- Distinguish pilot success from national-average change.
- Treat `school_readiness` as the mechanism that turns plans into real school capacity.
- Keep `school_readiness` sticky: it should usually move gradually and only fall when there is an explicit controversy, blockage, or implementation setback.
- Treat `student_productive_use` and `student_critical_literacy` as distinct. Do not move both upward just because students or teachers used AI more often.
- `student_productive_use` means productive learning use with adult support.
- `student_critical_literacy` means source criticism, deepfake resilience, basic technical intuition, and social/ethical understanding.
- Keep narrative claims consistent with the metric reference points.
- If actors launch big initiatives this turn, store rollout details in the notepad even when the main effects are delayed.

{% if output_language %}
Please write your response in {{output_language}}.
{% endif %}

Important: You must use the exact headers '## Metrics', '## Narrative', and '## Notepad'. Do not translate these headers.

Respond with a Markdown text with the following content:

- Heading level 2: Metrics
- A JSON object describing all metrics in a ```json code fence, in the following format: `{"metric1_name": value1, "metric2_name": value2}`
- Heading level 2: Narrative
- A coherent story about what happens in the world during the turn (max 400 words). You may use subheadings (level 3) if desired.
- Heading level 2: Notepad
