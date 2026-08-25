Compare the cohort syntheses below. Each cohort is a distinct condition under which the same scenario was run; the per-cohort reports were written from those runs alone, and the statistics were computed across all of them.

{% if output_language %}
Write the report in {{ output_language }}.
{% endif %}

{% if output_format == "json" %}
Return exactly one JSON object and no surrounding markdown.

Use this schema:
- `summary`: string – what differs between the cohorts and what holds everywhere, in 3-6 sentences
- `research_question_answers`: array of objects with `id`, `question`, `answer` (per cohort where answers differ), `frequency` (string), `conditions` (string – which cohorts or situations change the answer), `evidence_runs` (array of run directory names if given in the cohort reports), and `confidence` (one of "high", "medium", "low")
- `group_profiles`: array of objects with `cohort`, `n_runs`, `profile` (the cohort's characteristic trajectory in 2-3 sentences), and `key_traits`
- `between_group_differences`: array of objects with `aspect`, `cohorts_differ` (boolean), `description` (naming the cohorts on each side), and `evidence` (statistic or quoted finding)
- `similarities`: array of strings – what held in every cohort
- `simulation_caveats`: array of strings – artifacts of scenario design, cohort sizes, or model behavior rather than findings about the world
- `confidence_assessment`: string – how much weight this comparison can bear
{% else %}
Write a markdown report using exactly these `##` section headers in this order:

## Summary

## Cohorts Compared

{% if research_questions %}
## Research Questions

{% endif %}
## Between-Group Differences

## Similarities Across Cohorts

## Simulation Caveats

## Confidence Assessment

In `## Cohorts Compared`, use one `###` subsection per cohort, headed by the cohort value. Give each cohort's characteristic trajectory in a few sentences: where it ended up, what drove it there, and how it relates to the other cohorts.
{% if research_questions %}
In `## Research Questions`, use one `###` subsection per declared question, headed by the question id. Answer per cohort where the answers differ, name the cohorts on each side, then give the overall answer.
{% endif %}
In `## Between-Group Differences`, cover each aspect where cohorts genuinely diverge: what differs, which cohorts sit on which side, and the statistic or finding that shows it. Include aspects examined but found *not* to differ, labeled as such.
{% endif %}

The cohort statistics are authoritative for all counts and values. The per-cohort syntheses are informed summaries – compare them, but let the statistics decide anything countable.

## Scenario Definition

```json
{{ scenario_metadata_json }}
```

{% if research_questions %}
## Declared Research Questions

These are the questions this scenario was built to answer. Compare the cohorts' answers to each explicitly.

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
This scenario declares no research questions, so there is nothing specific you are obliged to answer; the framing of the comparison is yours.
{% endif %}

## Cohort Statistics

Computed deterministically from every run in each cohort. Ground truth for anything countable. Grouped by: {{ group_by }}

```json
{{ cohort_stats_json }}
```

## Per-Cohort Syntheses

One full synthesis per cohort, written from that cohort's runs alone.

{{ per_cohort_reports_markdown }}
