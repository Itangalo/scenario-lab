{% if background_context %}
## Fixed Background (unchanged all run)

This is the world as it stood at the start. It does not change, and it outranks the evolving narrative on any fact it states — if the narrative drifts away from something fixed here, the narrative is wrong.

{{background_context}}

{% endif %}It is now turn {{turn}}, which covers {{time_period}}. Each turn covers {{ time_scale.replace(' per turn', '') }}, so that is the span your actions have to land in.

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
## Your statements

{{statement_ledger}}

These carry forward unchanged unless you explicitly propose a change.
{% endif %}

{% if has_store %}
## Your persistent records

Some records are **held for you** and carry forward on their own. You do not restate them, and nothing you leave out of your answer can remove one. Each carries the id the framework gave it; that id, not the record's name, is how you refer to it.

The only thing that changes any of this is a JSON block under `## Store changes` in your answer.
{% endif %}

Use the background information to determine (1) which actions you want to take during the turn and (2) whether your statements still match what you are doing — proposing changes where they no longer do.

Actions should align with your statements and be realistic given time and other resources. Your actions will be evaluated by a Game Master, who determines how they affect the world. Bold actions can have greater impact, but also greater risk of failure.

{% if output_language %}
Please write your response in {{output_language}}.
{% endif %}

Respond with a Markdown text containing the following sections:

* Optional heading level 2: Statement changes — omit it, or write `No statement changes.`, when nothing has changed
* Heading level 2: Actions
* One paragraph for each action, describing at an appropriate level each action you intend to carry out during the turn.
{% if has_store %}
* Heading level 2: Store changes — **required every turn, even when nothing changes.** Under it, one JSON block holding your writes, or `No changes.` when there is nothing:

```json
{"store": [{"op": "add", "table": "<table>", "fields": {"<column>": "<value>"}, "grounds": "<one clause>"}]}
```

`op` is `add` (with `fields`), `update` (with `id` and `fields`), or `delete` (with `id`, and it must carry `grounds`). List only what changes; everything else carries forward on its own. Leaving the section out is not the same as writing that, and is recorded as a fault.
{% endif %}
