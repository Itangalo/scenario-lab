{% if background_context %}
## Fixed Background (unchanged all run)

This is the world as it stood at the start. It does not change, and it outranks the evolving narrative on any fact it states — if the narrative drifts away from something fixed here, the narrative is wrong.

{{background_context}}

{% endif %}It is now turn {{turn}} which covers {{time_period}}.

The Metric Rules looked like this (possibly updated):

{{metric_rules}}

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

{% if has_world_store %}
Some tables in the store belong to the run rather than to any actor, and you are their only writer. They carry forward on their own; nothing you leave out can remove a record. Each carries the id the framework gave it; that id, not the record's name, is how you refer to it.

Under a `## Store changes` heading in your answer, write one JSON block holding your world writes, or `{"store": []}` when nothing changes:

```json
{"store": [{"op": "add", "table": "<world table>", "fields": {"<column>": "<value>"}, "grounds": "<one clause>"}]}
```

`op` is `add` (with `fields`), `update` (with `id` and `fields`), or `delete` (with `id`, and it must carry `grounds`). One malformed entry rejects that entry while the rest apply; an absent section is recorded as a fault. You cannot write actor tables, and actors cannot write these.

---
{% endif %}

Use this information to do the following:

* Determine how successful the actors are with their actions. This is based on how the world looks and your assessment of how likely they are to succeed.
* Based on the actors' actions and Metric Rules, determine Metrics for the next turn.
* Write a coherent narrative that tells what happens in the world during this turn.

{% if output_language %}
Please write your response in {{output_language}}.
{% endif %}

Important: You must use the exact headers '## Metrics', '## Narrative', and '## Notepad' as specified below{% if has_world_store %}, plus '## Store changes' for your world writes{% endif %}. Do not translate these headers, even if you are writing the content in another language.

Respond with a Markdown text with the following content:

* Heading level 2: Metrics
{% if has_metrics_store %}* A JSON object holding this turn's metric reports as the store's write form, in a ```json code fence: `{"store": [{"op": "update", "table": "metrics", "id": "<metric_id>", "adjust": <delta>, "grounds": "<one clause>"}]}`. Report **every** metric every turn -- an omission is re-asked, not carried silently. Where the rules state the change as a delta, submit the change with `adjust` and let the framework do the arithmetic; where the value is set rather than moved, give `"fields": {"<value column>": <level>}` instead. Give `fields` or `adjust`, not both.
{% else %}* A JSON object describing all metrics in a ```json code fence, in the following format: `{"metric1_name": value1, "metric2_name": value2}`
{% endif %}* Heading level 2: Narrative
* A coherent story about what happens in the world during the turn (max 400 words). You may use subheadings (level 3) if desired.
