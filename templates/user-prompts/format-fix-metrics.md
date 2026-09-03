The previous Metrics Update response did not match the required format.

Here is the previous response:

---
{{previous_response}} ---

Rewrite it so it matches **exactly** this Markdown structure:

## Metrics
```json
{"metric1_id": 12.3, "metric2_id": 45}
```

## Narrative
<narrative text>

## Notepad
<notepad text>

Requirements:

- Use the exact headers `## Metrics`, `## Narrative`, and `## Notepad` (do not translate them).
- The `## Metrics` section must contain a valid JSON object inside a ```json code fence.
- The JSON object should include metric IDs as keys and numbers as values.
- Preserve the original meaning; do not add new metrics or story content beyond what was already implied.
{% if missing_metrics %}
The JSON object must carry **every** metric. The previous response left these out, with the value each one holds going into this turn:

{{ missing_metrics }}

A metric that is absent from the JSON is not held at its old value by anything that reads it downstream. If the previous response reasoned about one of these without listing it, list it now with the value that reasoning arrived at. If it did not reason about it at all, list it at the value shown above.
{% endif %}
