It is now turn {{turn}}, which covers {{time_period}}. Each turn covers {{ time_scale.replace(' per turn', '') }}, so that is the span the options have to land in.

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

{% if statement_ledger %}
## {{actor_name}}'s statements

{{statement_ledger}}

Options must stay inside these statements.
{% endif %}
{% if samples_text %}
---

Below are {{samples_text | length}} independently sampled drafts of what {{actor_name}} might do this turn. Distill them – merging near-duplicates, dropping the implausible – into your menu. You are not bound to them; invent better options where the drafts miss something obvious.

{% for sample in samples_text %}
### Draft {{loop.index}}

{{sample}}

{% endfor %}
{% endif %}
{% if output_language %}
Please write option titles and descriptions in {{output_language}}. The JSON keys ("title", "text") stay in English.
{% endif %}
{% if workshop_guidance %}
Who these options are written for:

{{workshop_guidance}}

Fit the options' register to that room without changing what the moves are.
{% endif %}

Propose at most {{max_options}} options for {{actor_name}} as a JSON array and nothing else.
