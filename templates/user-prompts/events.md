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

This is the run's own record, not a summary of it. Judge any condition that depends on what has happened — gate windows above all — against this list and nothing else. The narrative and the historical summary condense and lose dates; they are not evidence that an event occurred, and atmosphere is not an event.

{{event_history}}

Windows are counted in completed turns and exclude the current one.
{% endif %}

---

Use the background information to determine which external events can occur in this turn. If the probability is specified as a formula or description, you should calculate the actual value.

Eligibility is binary, and listing is not harmless: every entry you output gets rolled. An event whose Condition is not satisfied this turn must be omitted from the array entirely — including it "just in case" with a small probability is an error of the same weight as omitting an eligible one. When a condition is genuinely uncertain, judge conservatively and omit.

IMPORTANT: For events with date-specific conditions (e.g., "September 2026 is included"), check if the current time period ({{time_period}}) covers that date.

- If the current period is "January-June 2026", it does NOT cover September 2026.
- If the current period is "July-December 2026", it DOES cover September 2026.

{% if emergent_events_enabled %}
In addition to the listed events, you may propose up to {{ emergent_max_per_turn }} novel *emergent* event(s) this turn: exogenous developments that are not on the list but are plausible given the world state. Use this sparingly, for genuinely consequential surprises (technological, political, economic, natural, or social). Requirements:

- An emergent event must be exogenous: not an action by one of the actors, and not a restatement of something already in the narrative or history.
- Give it an id starting with `emergent_` (snake_case), a description of 1-3 sentences, and an honest probability that it happens during this turn's time window (maximum {{ emergent_max_probability }}).
- Do not re-propose emergent events that already occurred in previous turns.
{% if has_emerging_developments %}
- **Emerging developments.** The notepad's "Emerging developments (tracked)" section lists proposals from recent turns that were judged plausible but did not happen. While an entry stays plausible, list it again in your array — same id, same description — with the probability you judge it to have **now**, read from the world as it currently stands, at most {{ emergent_max_probability }}. Do not escalate it because it was listed before: a development that has not happened is not thereby more likely, and last turn's figure is not evidence about this turn. Some pressures build and the figure should rise; others are answered, overtaken or quietly resolved and the figure should fall. If it is no longer plausible, omit it and it is gone. An entry that has been listed without firing is normally in its last window; do not carry entries indefinitely.
{% endif %}
- If nothing novel is warranted, propose none. Most turns should have none.

Your response should be a JSON array where every object has four fields: `id`, `probability`, `emergent`, and `description`. For listed events, set `"emergent": false` and `"description": ""`.

```json
[
  {"id": "event1_id", "probability": 0.10, "emergent": false, "description": ""},
  {"id": "emergent_example_id", "probability": 0.08, "emergent": true, "description": "One to three sentences describing the novel event."}
]
```

The probability should be specified as a value between 0 and 1. If no event meets the conditions and no emergent event is warranted, respond with an empty array: `[]`
{% else %}
Your response should be a JSON array with objects for each event whose conditions are met, in this format:

```json
[
  {"id": "event1_id", "probability": 0.10},
  {"id": "event2_id", "probability": 0.24}
]
```

The probability should be specified as a value between 0 and 1. If no event meets the conditions, respond with an empty array: `[]`
{% endif %}

Respond *only* with this JSON array, nothing else.