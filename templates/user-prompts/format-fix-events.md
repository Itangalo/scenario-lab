The previous Events response was not valid JSON in the required schema.

Here is the previous response:

---
{{previous_response}} ---

Rewrite it to be a valid JSON array with objects for each event whose conditions are met, in this exact format:

```json
[
  {"id": "event1_id", "probability": 0.10},
  {"id": "event2_id", "probability": 0.24}
]
```

Requirements:

- Each element must be a JSON object with exactly two keys: `id` (a string) and `probability` (a number between 0 and 1).
- Do NOT use `["event_name", 0.25]` — each event must be its own `{"id": ..., "probability": ...}` object.
- If no events meet conditions, output `[]`.
- Respond only with the JSON, nothing else.
