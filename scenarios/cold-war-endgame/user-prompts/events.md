It is now turn {{turn}} which covers {{time_period}}.

{% if turn == 1 %}
This is the first turn, so there is no previous history. Current metrics look like this:
{% else %}
Current metrics look like this:
{% endif %}

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

---

The list of potential external events looks like this:

{{events_list}}

{% if event_history %}
---

## What has actually fired so far

This is the run's own record, not a summary of it. Judge any condition that
depends on what has happened — gate windows above all — against this list and
nothing else. The narrative and the historical summary condense and lose dates;
they are not evidence that an event occurred, and atmosphere is not an event.

{{event_history}}

Windows are counted in completed turns and exclude the current one.
{% endif %}

---

TASK: Evaluate which events have their conditions met this turn. For each qualifying event, determine the probability as a number between 0 and 1.

IMPORTANT: For events with turn-number conditions (e.g., "Turn is 5 or earlier"), the current turn is {{turn}}.

OUTPUT FORMAT — this is critical:
Your entire response must be a single JSON array. Each element is an object with exactly two keys:
- "id": the event ID string
- "probability": a number between 0 and 1

Example of correct output:
[{"id": "chernobyl", "probability": 0.25}, {"id": "arms_treaty", "probability": 0.20}]

If no events qualify, output: []

Do not include any text, explanation, or markdown outside the JSON array.
