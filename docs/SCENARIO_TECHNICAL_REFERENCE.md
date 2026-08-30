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
    ├── fixed-facts.md                 # optional
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
- `research_questions` (list)
- `base` (relative path to a base scenario YAML)
- `llm` (object)
- `emergent_events` (object)
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

### `research_questions`

Optional declaration of what the scenario exists to answer. Consumed by the `synthesize` command, which answers each declared question explicitly before reporting anything undeclared.

Two accepted shapes, mixable in one list:

```yaml
research_questions:
  - "Does public trust recover after a major incident?"
  - id: rq_regulator_timing
    question: "Under what conditions does the regulator act before an incident rather than after?"
    metrics: [regulatory_pressure, public_trust]
    events: [major_incident]
    notes: "The central question; everything else is secondary."
```

Fields on the mapping form:

- `question` (string, required)
- `id` (string, optional – derived from the question text when omitted)
- `metrics` (string or list of strings, optional) – metric IDs bearing on the question
- `events` (string or list of strings, optional) – event IDs bearing on the question
- `notes` (string, optional)

Validation:

- `research_questions` must be a list; each entry must be a string or a mapping with non-empty `question`
- `id` values must be unique within the scenario
- every id in `metrics` must exist in `metrics.md`, and every id in `events` must exist in `events.md` (error) – this is what catches a question the scenario cannot answer before runs are spent on it
- a question naming neither metrics nor events produces a warning: synthesis can then answer it only qualitatively

Inheritance: `research_questions` is a list, so a scenario declaring its own replaces the base's entirely rather than appending.

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
  - `events`, `actors`, `rules`, `metrics`, `summary`, `analysis`, `synthesis`, `referee`
- `probability_samples` must be an integer in `[1, 10]`
- `call_timeout_seconds` must be an integer in `[10, 3600]`

#### `llm.call_timeout_seconds`

Wall-clock deadline for a single LLM call, in seconds (default `300`):

```yaml
llm:
  call_timeout_seconds: 300
```

This bounds the whole request, not each read. The HTTP client's own timeout applies per read operation, so a provider that emits bytes slowly resets it indefinitely and a call can block for as long as the connection stays open – observed in practice as single calls running 11 to 23 minutes with the process idle. Exceeding the deadline raises `LLMCallTimeoutError`, which `FallbackRouter` treats as a route failure and moves past.

Raise it for slow reasoning models; lower it for unattended batches where a stalled run is worse than a failed one.

#### `llm.probability_samples`

Optional multi-sample probability elicitation for the events step (default `1`):

```yaml
llm:
  probability_samples: 3
```

With `N > 1`, the events step elicits the candidate-event list `N` times per turn. Per event, the probability used for the dice roll is the mean across valid samples, counting samples where the event was absent as `0` (absence means the conditions were judged not met). The per-sample values are recorded in `1-event-evaluations.json` as `probability_samples`, together with `samples_present` and `n_samples`. Each sample repeats the full events call, so cost for the events step scales linearly with `N`.

### `emergent_events`

Optional policy allowing the Game Master to propose novel exogenous events that are not listed in `events.md`:

```yaml
emergent_events:
  enabled: true
  max_per_turn: 1
  max_probability: 0.35
```

Supported fields:

- `enabled` (boolean, default `false`)
- `max_per_turn` (integer in `[1, 5]`, default `1`)
- `max_probability` (number in `(0, 1]`, default `0.35`)

Behavior:

- when enabled, the events prompt invites up to `max_per_turn` emergent proposals per turn, each with `"emergent": true`, an id starting with `emergent_`, and a 1–3 sentence description
- proposed probabilities above `max_probability` are capped (the original value is recorded as `probability_capped_from`)
- emergent proposals roll the same seeded dice as listed events and are fully recorded in `1-event-evaluations.json` with `"emergent": true`
- triggered emergent events are passed to the actor/rules/metrics prompts using their proposed description and added to the run's occurred-events list
- when disabled, unknown event ids are skipped exactly as before

Note: scenarios that override `user-prompts/events.md` must include the emergent-events instructions themselves (see `templates/user-prompts/events.md` for the default wording); otherwise the model is never told it may propose emergent events.

### `event_groups`

Optional. Declares families of events that cannot co-occur, so that exactly one — or at most one — resolves.

```yaml
event_groups:
  - id: us_election_2028
    members: [election_consolidation, election_alliance, election_retrenchment]
    resolution: exactly_one        # or at_most_one
    due_turns: [5]
    default: election_consolidation
    select_by:                     # optional: decide from the run's history instead of dice
      kind: most_recent_event
      map:
        campaign_backlash: election_retrenchment
        campaign_atlanticist: election_alliance
        campaign_security_hawk: election_consolidation
      precedence: [campaign_backlash, campaign_atlanticist, campaign_security_hawk]
```

Fields:

- `id` (string, required) — unique across groups
- `members` (list, required) — at least two event ids, each defined in `events.md`
- `resolution` (string) — `exactly_one` or `at_most_one` (default `at_most_one`)
- `due_turns` (list of integers, optional for `at_most_one`, **required** for `exactly_one`) — the turns in which the group resolves; omitted means every turn
- `default` (string, **required** for `exactly_one`) — the member that wins when every weight is zero
- `select_by` (mapping, optional) — deterministic selection from the event record; `kind` must be `most_recent_event`, `map` sends a source event id to the member it elects, and `precedence` orders sources that fired in the same turn (defaults to `map` order)

Behavior:

- one seeded roll per group per turn, independent of member count
- weights come from the probabilities the events step returned for the members; a member the model omitted counts as zero
- `select_by` ignores the dice entirely and reads only events that fired in turns *before* the resolving turn
- a branch's forced event wins its group; a suppressed member is weighted zero
- the winner enters `occurred_events` and `event_log` as an ordinary event; losers are recorded with `suppressed_by_group`

Validation: unknown members, a member in two groups, fewer than two members, a `due_turn` outside `1..max_turns`, an `exactly_one` group missing `due_turns` or `default`, and a `default` or `select_by` target that is not a member are all errors. A repeatable member in an `exactly_one` group is a warning.

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

## `background/fixed-facts.md` (optional)

The compact standing restatement of `context.md`, loaded as raw markdown. The full context is the world state in turn 1 and is replaced by the Game Master's narrative after it, so from turn 2 onward every prompt carries a fixed-background block to keep the scenario's settled facts from decaying. That block renders this file when it exists and the whole of `context.md` when it does not, which is why a long opening description is worth restating here: only the facts that must not drift belong in it, not the scene-setting.

Write it as facts rather than as narration, and keep it short: it is repeated in every prompt of every turn from turn 2 to the end of the run, which is where a paragraph of scene-setting becomes thousands of wasted tokens. **The file is inserted verbatim under a heading the template supplies, with a sentence already explaining what it is and that it outranks the evolving narrative** – so it needs no title, no introduction and no explanation of its own purpose, and any it carries will be sent to the model as content. Headings inside it are usually not worth their lines either. Do not put anything here that is not also true in `context.md`; the two must not be able to disagree. Nothing renders it in turn 1, where `context.md` itself is the world state, so it never duplicates the opening.

Check the result in the prompt sign-off documents rather than assuming it: `python scripts/render_signoff.py <run-dir>` shows both turns side by side, with each block labelled by the file it came from.

### `termination` (optional)

Ends a run before `max_turns` when the scenario reaches its own finish line.

```yaml
termination:
  - id: government_formed
    when: "viability_left_bloc >= 100 or viability_right_bloc >= 100"
    description: "A government has been formed"
  - id: snap_election_called
    when: "snap_election_risk >= 100"
    description: "Four votes failed; an extraordinary election is called"
```

- `when` is evaluated in Python after each turn, against current metric values, using the same safe evaluator as event probability formulas. Arithmetic, comparisons, boolean operators, `min()` and `max()`, and metric references are allowed; nothing else is.
- Conditions are checked in order and the first match ends the run.
- Validation rejects unknown metric references and warns if a condition is already true at the starting values, which would end every run at turn 1.
- The triggering condition is recorded in the run's `summary.json` under `termination`.

Use this whenever the scenario has a definite end. Without it, a run that resolves at turn 8 keeps simulating through turn 20, which costs money and lets the narrative drift away from its own conclusion.

## Starting-State Draws (optional)

A scenario normally starts from the values declared in `metrics.md`, so repeated runs differ only in their event dice. When the *starting* world is itself uncertain, a run can be given a draw: a JSON file that sets metric values and adds context before turn 1.

```json
{
  "metrics": { "seats_left_bloc": 168, "seats_right_bloc": 181 },
  "context": "## Election Result\n\nThe Liberals fell below the threshold.",
  "notes": "draw 07, sampler seed 12345"
}
```

All three keys are optional; unknown top-level keys are rejected.

- `metrics` – metric id to number. Ids must exist in `metrics.md` and values must fall inside the declared bounds. Both are hard errors, never clamped: a miss means the generator is broken, and repairing it silently would bias the batch.
- `context` – markdown appended to `background/context.md` and to the initial world narrative.
- `notes` – free text, recorded for provenance.

Usage:

```bash
# Inspect the world one draw starts from, without running anything
python -m scenario_lab.cli describe scenarios/<id> --initial-state draws/draw-07.json

# One run from one draw
python -m scenario_lab.cli run scenarios/<id> --initial-state draws/draw-07.json

# A batch where each run gets its own draw, assigned in sorted order
python -m scenario_lab.cli batch-run scenarios/<id> --repeat 20 --initial-states draws/
```

`--initial-states` needs at least as many `.json` files as there are runs; too few is an error rather than a cycle, since reusing draws would narrow the distribution the batch reports on. The applied draw is stored in each run's `config.json` under `initial_state`.

Scenario Lab reads draws as data and never runs generator code. A scenario that needs draws should ship its generator as an ordinary script in its own directory and document how to run it; generating the draws stays a deliberate step you take, not something loading a scenario triggers.

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

### Rendering and Available Variables

Both override directories are rendered as Jinja templates in a sandboxed environment. Conditionals, loops, and spaced placeholders (`{{ actor_name }}`) all work, and legacy space-free placeholders (`{{actor_name}}`) behave identically.

`system-prompts/` templates receive:

- `scenario_name`, `scenario_description`
- `actors_list`, `metrics_list` (pre-rendered text blocks)
- `constitution` (empty string when the scenario defines none)
- `output_language`
- `actor_id`, `actor_name`, `actor_description`, `actor_short_description` (populated only for actor prompts)
- `metric_<metric_id>` for every metric, carrying its current value

`user-prompts/` templates receive a turn-aware context instead: `turn`, `time_period`, `metrics_json`, `world_state`, `historical_summary`, `notepad`, `output_language`, and `metric_<metric_id>`.

Because system prompts are built without a turn number, turn-specific variables are unavailable there – reference them from a user prompt instead.

Validation parses every override: invalid Jinja syntax is an error, and a variable the context does not supply is a warning. Heed the warning. Jinja renders an undefined variable as empty text rather than failing, so the resulting prompt is silently missing whatever that variable was meant to carry while the file itself still reads correctly.

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
