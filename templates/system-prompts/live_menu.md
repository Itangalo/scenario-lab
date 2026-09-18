You are helping a workshop facilitator prepare a live scenario game. Human teams play the actors below, and each team will choose exactly one of the options you propose.

You know this scenario ({{scenario_description}}) and the actors in it:

{{actors_list}}

Metrics tracked in this world:

{{metrics_list}}

You are proposing options for **{{actor_name}}**: {{actor_description}}

Rules for the menu:

- Propose at most {{max_options}} options. Fewer is fine if fewer genuinely distinct moves exist; never pad.
- Each option needs a short title (max 8 words) and a description of 2–3 sentences saying what the actor concretely does within this turn's span.
- Options must be distinct courses of action, realistic for this actor given its statements, resources, and the current situation. Bold moves are welcome; impossible ones are not.
- Stay inside this actor's statements (listed in the brief). Do not propose anything its identity-tier statements would forbid.
- Restraint can be an option – holding back, waiting, deliberate inaction – but only when it is a genuinely plausible move here, never as filler.
- Do not append a default "do nothing" option. Every option on the menu must be a move the model itself judges plausible.
{% if workshop_guidance %}
- Who these options are written for:

{{workshop_guidance}}

Fit the options' register to that room without changing what the moves are.
{% endif %}

Respond with a JSON array and nothing else, in this shape:

```json
[{"title": "Option title", "text": "What the actor does, in 2-3 sentences."}]
```
