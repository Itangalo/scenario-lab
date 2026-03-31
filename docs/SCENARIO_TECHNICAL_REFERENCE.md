# Scenario Technical Reference

This document defines the technical scenario contract used by Scenario Lab.
It is implementation-aligned with the current loader/validator behavior.

## Scope

This reference covers:

- scenario file and folder structure
- file formats and parsing rules
- config schema and validation constraints
- supported prompt override files

This reference does not describe scenario design workflow. Use `docs/SCENARIO_CREATION_WITH_AGENT.md` for process guidance.

## Scenario Directory Contract

Expected scenario root:

```text
scenarios/<scenario-id>/
├── scenario.yaml
├── metrics.md
├── events.md
├── metric-rules.md
├── constitution.md                    # optional
├── system-prompts/                    # optional
├── user-prompts/                      # optional
└── background/
    ├── context.md
    └── actors/
        └── <actor_id>.md              # one file per actor in scenario.yaml
```

Required for successful loading:

- `scenario.yaml`
- `metrics.md`
- `events.md`
- `metric-rules.md`
- `background/context.md`
- `background/actors/<actor_id>.md` for every actor in `scenario.yaml`

## `scenario.yaml`

Required top-level fields:

- `name` (string)
- `description` (string)
- `start_date` (string)
- `time_scale` (string)
- `max_turns` (integer)
- `actors` (list of actor IDs)

Optional top-level fields:

- `output_language` (string)
- `base` (relative path to a base scenario YAML)
- `llm` (object)
- `rule_evolution` (object)
- `constitutional_enforcement` (object)

### `start_date` and `time_scale`

Accepted `start_date` formats:

- `YYYY-MM-DD`
- `YYYY-MM`
- `YYYY`

`time_scale` must contain a quantity and a supported unit:

- `day` / `days`
- `week` / `weeks`
- `month` / `months`
- `year` / `years`

Examples:

- `2 weeks per turn`
- `6 months`
- `1 year per turn`

### `max_turns`

Validation constraints:

- minimum: `1`
- maximum: `100`

### `base` Inheritance

If `base` is present:

- the base YAML is loaded first
- current scenario values override base values
- dictionary values are deep-merged recursively
- scalar values and lists are replaced by override values

Security constraint:

- `base` must resolve inside the scenarios directory structure (path traversal outside this scope is rejected)

### `llm` Configuration

Supported shapes:

1. Legacy single-model shape:

```yaml
llm:
  model: provider/model-name
  temperature: 0.7
  max_tokens: 2000
```

2. Per-task shape:

```yaml
llm:
  events: provider/model-name
  actors: provider/model-name
  rules: provider/model-name
  metrics: provider/model-name
  summary: provider/model-name
  referee: provider/model-name
  temperature: 0.7
  max_tokens: 2000
  max_tokens_by_task:
    rules: 3000
```

Model values can be:

- a string (`provider/model`)
- a fallback list (`[provider/model-a, provider/model-b]`)
- for `actors`, also a dict (`actor_id -> model string or fallback list`)

Validation rules:

- model strings must use `provider/model` format
- `temperature` must be in `[0, 2]`
- `max_tokens` and `max_tokens_by_task[*]` must be integers in `[100, 100000]`
- `max_tokens_by_task` keys must be one of:
  - `events`, `actors`, `rules`, `metrics`, `summary`, `referee`

### `rule_evolution`

Optional guardrails for how freely `metric-rules.md` may change during runs:

```yaml
rule_evolution:
  freeze_until_turn: 2
  max_changes_per_turn: 4
```

Supported fields:

- `freeze_until_turn` (integer, default `0`)
- `max_changes_per_turn` (integer, default `6`)

Behavior:

- when `turn <= freeze_until_turn`, the rules LLM step is skipped and the previous rules are carried forward in a new versioned wrapper
- after the freeze window, rule updates are expected to stay within `max_changes_per_turn`

### `constitutional_enforcement`

Optional guardrails for the constitutional referee retry/fallback policy:

```yaml
constitutional_enforcement:
  max_attempts: 2
  on_failure: accept_with_violations
```

Supported fields:

- `max_attempts` (integer, default `2`)
- `on_failure` (string, one of `accept_with_violations` or `revert_to_previous`)

## `metrics.md`

Canonical metric block format:

```markdown
## metric_id
**Description:** ...
**ID:** metric_id
**Min:** 0
**Max:** 100
**Unit:** percent
**Start value:** 50
**Reference points:**
- 0: description
- 50: description
```

Parsing behavior:

- each `##` heading starts a new metric
- heading text is used as metric ID
- reference points are parsed from `- number: text`
- accepted start-value labels:
  - `Start value`
  - `Starting value`
  - `Value`

Validation:

- metric start value must be within `[min, max]`
- `min < max`

## `events.md`

Canonical event block format:

```markdown
## Event Name
**ID:** event_id
**Condition:** ...
**Probability:** ...
**Can repeat:** Yes
**Description:** ...
```

Parsing behavior:

- an event is only materialized if `ID` exists
- `Can repeat` is true for `yes` or `true` (case-insensitive)

Probability values support:

- static values (for example `10%`, `10 percent`, `0.1`)
- formulas (for example `unemployment / 100`, `min(risk_index, 50) / 100`)
- natural-language probability descriptions (accepted; interpreted by LLM)

Formula validation allows:

- arithmetic operators
- comparisons
- boolean operators
- `min()` and `max()`
- metric variable references

## `metric-rules.md`

`metric-rules.md` is loaded as raw markdown text.

Recommended format:

- numbered rules (`1.`, `2.`, `3.`) with clear quantitative relationships

The file may evolve during simulation and is versioned in turn outputs.

## `background/context.md`

`background/context.md` is loaded as raw markdown text and used as initial world narrative.

## Actor Files (`background/actors/<actor_id>.md`)

Canonical format:

```markdown
# Actor Name

## Short description
One sentence.

## Long description
Detailed actor context.

### Initial goals
- Goal 1
- Goal 2

### Behavioral traits
- Trait 1
- Trait 2
```

Parsing behavior:

- `# ...` sets actor display name
- `## Short description` is parsed into `short_description`
- `## Long description` is parsed into `long_description`
- `### Initial goals` is parsed into `initial_goals`
- `### Behavioral traits` (and `### Behavioural traits` / `### Traits`) is parsed into `behavioral_traits`
- goals/traits support `-`, `*`, and numbered list items (`1.`)
- legacy `## Initial goals` / `## Behavioral traits` sections are not parsed as goals/traits

Validation warnings are emitted when an actor is missing:

- short description
- initial goals
- behavioral traits

## Prompt Overrides

Scenario-specific prompt override directories are optional.

### `system-prompts/`

Recognized files:

- `events.md`
- `actor.md`
- `metric-rules.md`
- `metrics-update.md`
- `constitutional-referee.md`
- `constitutional-referee-correction.md`
- `actor_<actor_id>.md` (actor-specific system prompt)

### `user-prompts/`

Recognized files:

- `events.md`
- `actor.md`
- `metric-rules.md`
- `metrics-update.md`
- `constitutional-referee.md`
- `constitutional-referee-correction.md`

Notes:

- default shared templates also include summarization and format-fix prompts under `templates/`
- scenario-local overrides are currently supported only for the files listed above

## Validation Command

Run:

```bash
python -m scenario_lab.cli validate scenarios/<scenario-id>
```

Validation reports:

- structural errors (missing actor files, invalid config values, etc.)
- metric range errors
- event probability errors/warnings
- actor/content warnings
