Revise the following metrics update for Turn {{turn}} ({{time_period}}) so it complies with the Constitutional Constraints.

## Previous Metrics

{{previous_metrics_json}}

## Current Proposed Metrics

{{new_metrics_json}}

## Current Narrative

{{narrative}}

## Constitutional Violations To Fix

{{violations}}

Please return a corrected version of the proposal.

- Keep any compliant parts unchanged if possible
- Only change what is necessary to resolve the listed violations
- Keep the narrative aligned with the corrected metrics

{% if output_language %}
Write the narrative in {{output_language}}.
{% endif %}

Respond using the exact headers `## Metrics` and `## Narrative`.
