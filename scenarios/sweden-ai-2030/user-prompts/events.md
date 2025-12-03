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

{{world_state}}

---

The notepad contains the following information:

{{notepad}}

---

The list of potential external events looks like this:

{{events_list}}

---

Use the background information to determine which external events can occur in this turn. If the probability is specified as a formula or description, you should calculate the actual value.

Your response should be a JSON array with objects for each event whose conditions are met, in this format:

```json
[
  {"id": "event1_id", "probability": 0.10},
  {"id": "event2_id", "probability": 0.24}
]
```

The probability should be specified as a value between 0 and 1. If no event meets the conditions, respond with an empty array: `[]`

Respond *only* with this JSON array, nothing else.
