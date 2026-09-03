{# Scenario override. Identical to templates/user-prompts/events.md except for:
   1. The paragraph mandating that the six always-eligible events appear in every turn's array. Without it the model filters the gated escalations out when their gate is shut, which makes precursors look perfectly predictive and destroys the monitoring problem the scenario is built on.
   2. The emerging-developments protocol: how many developments to keep in play is a judgement about how fast this particular world is moving, and a proposal's description must never characterise the long run as settled. Keep in sync with the default template when that changes, including the
   emergent-events block, which an override must carry itself. #}
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

**Six events are marked "Always eligible" and must appear in every turn's array, without exception:** `cyber_major_incident`, `bio_incident`, `loss_of_control_incident`, `capability_jump`, `taiwan_blockade`, `ai_investment_collapse`. For those six, and for no other events in the list, conditions are never unmet – only their probability changes. Give each of them its gate-open probability when its gate is open, and its gate-shut probability when it is not. The gate-shut probabilities are small but never zero, and dropping these events from the array because their gate is shut is an error: it removes the surprise the scenario exists to study, by making every escalation look as though it must have been preceded by a warning. `rsi_onset` is different: its availability depends on this run's own figures and on a declared eligibility expression, so it appears in your array exactly when it appears in the list above.

**In the turn covering the second half of 2028, all three election outcomes must appear in your array:** `election_consolidation`, `election_alliance` and `election_retrenchment`. They are a mutually exclusive family and exactly one of them will be fired, whatever you return; your figures are weights against each other, not chances of happening alone, so only their ratio matters. Omitting one is a weight of zero and silently removes a possible future – if you judge an outcome nearly impossible, say so with a small weight rather than by leaving it out. Outside that turn they are not eligible and must not be listed.

IMPORTANT: For events with date-specific conditions (e.g., "September 2026 is included"), check if the current time period ({{time_period}}) covers that date.

- If the current period is "January-June 2026", it does NOT cover September 2026.
- If the current period is "July-December 2026", it DOES cover September 2026.

{% if emergent_events_enabled %}
In addition to the listed events, you may propose up to {{ emergent_max_per_turn }} novel *emergent* event(s) this turn: exogenous developments that are not on the list but are plausible given the world state. Requirements:

- An emergent event must be exogenous: not an action by one of the actors, and not a restatement of something already in the narrative or history.
- Give it an id starting with `emergent_` (snake_case), a description of 1-3 sentences, and an honest probability that it happens during this turn's time window (maximum {{ emergent_max_probability }}).
- Do not re-propose emergent events that already occurred in previous turns.
{% if has_emerging_developments %}
- **Emerging developments.** The notepad's "Emerging developments (tracked)" section lists proposals from recent turns that were judged plausible but did not happen. While an entry stays plausible, list it again — same id, same description — with the probability you judge it to have **now**, read from the world as it currently stands, at most {{ emergent_max_probability }}. Do not escalate it because it was listed before: a development that has not happened is not thereby more likely, and last turn's figure is not evidence about this turn. Some pressures build and the figure should rise; others are answered, overtaken or quietly resolved and the figure should fall. If it is no longer plausible, omit it and it is gone.
{% endif %}
- **How many to keep in play depends on how fast this world is moving.** Judge that from what has actually happened to capability, incidents and investment — a fast-moving world supports 3–4 live developments escalating quickly; a stagnant one only 0–2, escalating slowly. The aim is that across a run several tracked developments materialise or fade rather than none.
- **Institutional reactions belong here, not on the list.** When the Union's own portfolio gives them footing — a flagship restriction in force, measures spanning many jurisdictions, standards with real pull — propose emergent events such as `emergent_court_challenge` (a court suspends a core provision), `emergent_member_state_noncompliance` (a member state quietly stops implementing), or `emergent_rival_standards_body` (a competing bloc launches lighter rules). These cannot be timed from metrics alone; they arise from what the EU has actually built, which you can see and it cannot.
- **Constructive wildcards belong here too.** Not every unlisted development is a threat: propose positive emergents with the same honesty, such as `emergent_joint_attribution_pact` (states hit by the same attack pool response), `emergent_biosurveillance_breakthrough` (detection gets faster everywhere at once), or `emergent_talent_return_wave` (researchers come home to EU labs). A world where nothing unlisted ever helps is as rigged as one where nothing unlisted ever hurts.
- If nothing novel is warranted and nothing is being tracked, propose none.

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