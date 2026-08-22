Revise the following metrics update for Turn {{turn}} ({{time_period}}) so it complies with the Constitutional Constraints.

## Previous Metrics

{{previous_metrics_json}}

## Current Proposed Metrics

{{new_metrics_json}}

## Current Narrative

{{narrative}}

## Game Master's Notepad (persistent record)

{{notepad}}

This is the authoritative record of what has already happened in this run. Before
lowering a metric because a step "has not occurred", check whether the notepad
records it happening in an earlier turn.

## Constitutional Violations To Fix

{{violations}}

Please return a corrected version of the proposal.

- Keep any compliant parts unchanged if possible
- Only change what is necessary to resolve the listed violations
- Keep the narrative aligned with the corrected metrics
- Prefer moving violating metrics back toward the previous values
- If implementation should be delayed, say so in the narrative instead of implying same-turn success

{% if output_language %}
Write the narrative in {{output_language}}.
{% endif %}

Respond using the exact headers `## Metrics` and `## Narrative`.
