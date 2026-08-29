Analyze the completed run described below.

{% if output_language %}
Write the report in {{ output_language }}.
{% endif %}

{% if output_format == "json" %}
Return exactly one JSON object and no surrounding markdown.

Use this schema:
- `summary`: string
- `key_metrics_overview`: array of objects with `metric_id`, `start_value`, `end_value`, `direction`, `delta`, and `commentary`
- `turning_points`: array of objects with `turn`, `time_period`, `description`, `impact`, and `why_it_mattered`
- `event_analysis`: object with `triggered_events`, `not_triggered_events`, and `impact_assessment`
- `actor_behavior_patterns`: array of objects with `actor_id`, `actor_name`, and `analysis`
- `rule_evolution`: string
- `constitutional_interventions`: string or null
- `observations_and_caveats`: array of strings
{% else %}
Write a markdown report using exactly these `##` section headers in this order:

## Summary
## Key Metrics Overview
## Turning Points
## Event Analysis
## Actor Behavior Patterns
## Rule Evolution
## Constitutional Interventions
## Observations and Caveats

In `## Key Metrics Overview`, include a markdown table with start value, end value, direction, and delta for each metric.
{% endif %}

Use the supplied metric overview as the baseline for exact start/end values. If `context_mode` is `condensed` or `minimal`, some long per-turn artifacts were truncated for context-window reasons. Work only from the evidence that remains in the prompt.

## Run Metadata
```json
{{ run_metadata_json }}
```

## Metric Overview
```json
{{ metric_overview_json }}
```

## Scenario Metrics
{{ scenario_metrics_markdown }}

## Scenario Events
{{ scenario_events_markdown }}

## Scenario Actors
{{ scenario_actors_markdown }}

## Initial Metric Rules
{{ scenario_metric_rules_markdown }}

## Constitution
{{ scenario_constitution_markdown }}

## Turn Artifacts
{{ turn_artifacts_markdown }}
