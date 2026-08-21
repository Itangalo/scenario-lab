Synthesize the ensemble of runs described below.

{% if output_language %}
Write the report in {{ output_language }}.
{% endif %}

{% if output_format == "json" %}
Return exactly one JSON object and no surrounding markdown.

Use this schema:
- `summary`: string – what this world tends to do, in 3-6 sentences
- `research_question_answers`: array of objects with `id`, `question`, `answer`, `frequency` (string, e.g. "14 of 20 runs"), `conditions` (string – what the answer depends on), `evidence_runs` (array of run directory names), and `confidence` (one of "high", "medium", "low")
- `outcome_patterns`: array of objects with `label`, `description`, `run_count`, `example_runs` (array), and `distinguishing_factors` (string)
- `recurring_turning_points`: array of objects with `description`, `typical_turns` (string), `run_count`, and `effect`
- `actor_dynamics`: array of objects with `actor_id`, `pattern`, and `variation`
- `surprises_and_outliers`: array of objects with `description`, `run_count`, `example_runs` (array), and `why_it_matters`
- `simulation_caveats`: array of strings – possible artifacts of scenario design or model behavior rather than findings about the world
- `confidence_assessment`: string – how much weight this ensemble can bear, given run count and variance
{% else %}
Write a markdown report using exactly these `##` section headers in this order:

## Summary
{% if research_questions %}
## Research Questions
{% endif %}
## Outcome Patterns
## Recurring Turning Points
## Actor Dynamics
## Surprises and Outliers
## Simulation Caveats
## Confidence Assessment

{% if research_questions %}
In `## Research Questions`, use one `###` subsection per declared question, headed by the question id. Answer directly in the first sentence, then give frequency, conditions, and the runs that evidence it.
{% endif %}
In `## Outcome Patterns`, describe the distinct ways runs ended, with a run count and example run names for each. Include patterns that occurred once, labeled as such.
{% endif %}

The ensemble statistics are authoritative for all counts and distributions. The per-run analyses are individual readings – aggregate them, but attribute claims drawn from them to the runs they came from.

{% if research_questions %}
## Declared Research Questions

These are the questions this scenario was built to answer. Answer each one explicitly, and answer them before reporting anything undeclared.

{% for rq in research_questions %}
### {{ rq.id }}

{{ rq.question }}
{% if rq.metrics %}
- Bearing metrics: {{ rq.metrics | join(", ") }}
{% endif %}
{% if rq.events %}
- Bearing events: {{ rq.events | join(", ") }}
{% endif %}
{% if rq.notes %}
- Notes: {{ rq.notes }}
{% endif %}

{% endfor %}
{% else %}
This scenario declares no research questions, so there is nothing specific you are obliged to answer. Report what the runs show, and be explicit that the framing is yours rather than the scenario author's.
{% endif %}

## Scenario Definition

```json
{{ scenario_metadata_json }}
```

### Metrics

{{ scenario_metrics_markdown }}

### Events

{{ scenario_events_markdown }}

### Actors

{{ scenario_actors_markdown }}

## Ensemble Statistics

These are computed from every run without an LLM in the loop. Treat them as ground truth.

```json
{{ ensemble_statistics_json }}
```

## Per-Run Analyses

{{ per_run_analyses_markdown }}
