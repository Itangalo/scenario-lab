## Current World State

**Turn:** {{turn}}
**Time Period:** {{time_period}}

## Current Metrics

```json
{{metrics_json}}
```

## Event to Evaluate

{{event_definition}}

---

Evaluate whether this event's conditions are met and calculate the exact probability. Respond with a JSON object containing `eligible` (boolean), `probability` (0.0-1.0), and `reasoning` (string).
