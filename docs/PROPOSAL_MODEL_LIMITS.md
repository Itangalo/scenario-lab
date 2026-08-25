# Proposal: token and timeout limits should follow the model

References checked against the code on 2026-08-25. Verify before relying on them.

## The problem

Two limits govern every LLM call, and they are configured on the wrong axis.

- `llm.max_tokens`, overridable per task via `llm.max_tokens_by_task`
- `llm.call_timeout_seconds`, scenario-global with no override at all

Both actually depend on **which model runs the call**, not on which step it is.
A reasoning model needs a large budget and a long deadline whatever it is doing;
a fast instruct model needs neither.

This is not hypothetical. `stealth/ox-alpha` at the turn steps' `max_tokens:
3000` spent its entire budget on reasoning and returned no content, on every
call, until the budget was raised to 32000; it then exceeded the 300s deadline
and returned 502s until that was raised to 1800. Both had to be set on the whole
scenario, degrading the unattended simulation batches that shared the file, and
the timeout had to be reverted by hand afterwards because `synthesize` has no
`--override`.

## Why task-scoping cannot be fixed by adding a `call_timeout_by_task`

Fallback route lists make the model vary *within* one task:

```yaml
llm:
  events:
    - "openrouter:qwen/qwen3-235b-a22b-2507"
    - "openrouter:google/gemini-3-flash-preview"
```

`FallbackRouter` is constructed with one `max_tokens` for the whole list
(`scenario_lab/orchestrator.py:206`, and likewise in `analysis.py` and
`synthesis.py`), and `ProviderRegistry` with one `call_timeout_seconds` for all
providers. So every route in a list is handed the primary's limits.
`cold-war-endgame` has twelve such route entries today. A list pairing a
reasoning model with an instruct one is unconfigurable: whichever is not the
primary gets limits that do not fit it.

Task-scoped limits are structurally unable to express this. Model-scoped ones
are.

## Suggested shape

```yaml
llm:
  model: "openrouter:qwen/qwen3-235b-a22b-2507"
  analysis: "openrouter:stealth/ox-alpha"
  max_tokens: 3000
  call_timeout_seconds: 300
  max_tokens_by_task:
    rules: 3500
  model_limits:
    "openrouter:stealth/ox-alpha":
      max_tokens: 32000
      call_timeout_seconds: 1800
```

Keep `max_tokens_by_task`: `rules: 3500` in four scenarios is a genuine
task-shaped need at a fixed model, and removing it would be a regression.

**Composition.** Treat task and model entries as lower bounds and take the
larger, rather than establishing a precedence order. A task entry says "this
step needs room"; a model entry says "this model cannot work below this". The
rules step on ox-alpha then resolves to `max(3500, 32000)`, which is what is
wanted, and no one has to remember which key wins. The alternative — explicit
precedence, model over task — is more conventional and worth considering, but
is easier to get subtly wrong in exactly the case that motivated this.

## Implementation notes

- Limits must resolve **per route attempt**, not at router construction.
  `FallbackRouter` currently takes `max_tokens` once; it needs the resolved
  limit for the route it is about to try.
- `ProviderRegistry` holds one `call_timeout_seconds` for all providers and
  needs a per-provider or per-call deadline instead.
- Three call sites construct routers: `orchestrator.py`, `analysis.py`,
  `synthesis.py`. All three should resolve limits the same way; a single helper
  on the config object is preferable to repeating the rule.
- `validator.py` bounds `call_timeout_seconds` to `[10, 3600]`; per-model values
  need the same check, and unknown model keys in `model_limits` should warn
  rather than fail silently.
- `AGENTS.md`: this changes system behaviour, so `docs/ARCHITECTURE.md` is
  ground truth and gets updated as part of the work.

## Smaller adjacent gap

`synthesize` and `analyze` accept `--model` but no `--override`, so limits can
only be changed by editing the scenario file. Once limits follow the model this
matters less, since pointing `--model` at a model with declared limits would
carry them along.
