{% if background_context %}
## Fixed Background (unchanged all run)

This is the world as it stood at the start. It does not change, and it outranks
the evolving narrative on any fact it states — if the narrative drifts away from
something fixed here, the narrative is wrong.

{{background_context}}

{% endif %}It is now turn {{turn}} which covers {{time_period}}.

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

{% if has_emerging_developments %}
The notepad's "Emerging developments (tracked)" section lists developments that recent turns have judged plausible but that have not happened. They are not events. Let them colour the narrative only as faint, ambiguous signals whose visibility grows with how long they have been listed — never as anything confirmed, and never with a stated probability.
{% endif %}

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

Use this information to do the following:

* Determine how successful the actors are with their actions. This is based on how the world looks and your assessment of how likely they are to succeed.
* Based on the actors' actions and Metric Rules, determine Metrics for the next turn.
* Write a coherent narrative that tells what happens in the world during this turn.

{% if output_language %}
Please write your response in {{output_language}}.
{% endif %}

Important: You must use the exact headers '## Metrics', '## Narrative', and '## Notepad' as specified below. Do not translate these headers, even if you are writing the content in another language.

Respond with a Markdown text with the following content:

* Heading level 2: Metrics
* A JSON object describing all metrics in a ```json code fence, in the following format: `{"metric1_name": value1, "metric2_name": value2}`
* Heading level 2: Narrative
* A coherent story about what happens in the world during the turn (max 400 words). You may use subheadings (level 3) if desired.
