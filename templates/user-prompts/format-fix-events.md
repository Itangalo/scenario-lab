The previous Events response was not valid JSON in the required schema.

Here is the previous response:

---
{{previous_response}}
---

Rewrite it to be a valid JSON array with objects for each event whose conditions are met, in this exact format:

```json
[
  {"id": "event1_id", "probability": 0.10},
  {"id": "event2_id", "probability": 0.24}
]
```

Requirements:
- Output **only** a JSON array (no Markdown, no code fences).
- Each object must have keys `id` (string) and `probability` (number between 0 and 1).
- If no events meet conditions, output `[]`.
