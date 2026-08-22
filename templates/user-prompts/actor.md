{% if background_context %}
## Fixed Background (unchanged all run)

This is the world as it stood at the start. It does not change, and it outranks
the evolving narrative on any fact it states — if the narrative drifts away from
something fixed here, the narrative is wrong.

{{background_context}}

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
{{world_state}}

---

{% if triggered_events %}
This turn, the following external events have occurred:

{{triggered_events}}
{% else %}
No special events occur this turn.
{% endif %}

---

Use the background information to determine (1) whether your goals should be adjusted and (2) which actions you want to take during the turn.

Actions should align with your goals and be realistic given time and other resources. Your actions will be evaluated by a Game Master, who determines how they affect the world. Bold actions can have greater impact, but also greater risk of failure.

{% if output_language %}
Please write your response in {{output_language}}.
{% endif %}

Respond with a Markdown text containing the following sections:

* Heading level 2: Goals
* Brief description of your goals in a bullet list
* Optional heading level 3: Reason for changes (only if goals changed)
* Brief description of why goals changed (only if goals changed)
* Heading level 2: Actions
* One paragraph for each action, describing at an appropriate level each action you intend to carry out during the turn.
