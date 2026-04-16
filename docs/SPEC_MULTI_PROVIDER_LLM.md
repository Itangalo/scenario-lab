# Spec: Multi-Provider LLM Support

## Problem

All LLM traffic today flows through a single `LLMClient` in `scenario_lab/llm.py` that is hardcoded to OpenRouter's chat-completions endpoint. Model strings, retry logic, response parsing, and pricing lookup all assume OpenRouter conventions. This blocks three things we want:

- Calling Anthropic directly (for prompt caching, better rate limits, and first-class SDK support).
- Adding further providers later (local models via Ollama, OpenAI direct, Google direct) without a second refactor.
- Cross-provider fallback (e.g. Anthropic → OpenRouter → local) rather than only fallback within OpenRouter.

## Goal

Introduce a provider abstraction so that each LLM backend is an interchangeable adapter. Scenario configs specify a route as `(provider, model)`. The orchestrator no longer knows about HTTP, auth, or provider-specific payload shapes – it asks a router for a completion.

This spec covers only OpenRouter (migrated from current code) and Anthropic (new). Ollama and other providers are explicitly out of scope but the design must make adding them trivial.

## Non-goals

- Prompt caching, streaming, tool use, or batch APIs. The first iteration must expose the same `complete(system, user) -> LLMResponse` surface the orchestrator uses today. Caching is planned for a follow-up.
- Changing orchestration, simulation logic, or scenario file format beyond the LLM config section.
- Rewriting `MockLLMClient` usage sites. Mocks must continue to work with the existing tests.

## Design

### Core concepts

- `ModelRoute` – a dataclass `(provider: str, model: str)`. Replaces bare model strings as the unit the orchestrator passes around.
- `LLMProvider` – abstract base class. One concrete subclass per backend. Owns auth, endpoint, message formatting, and usage parsing for that backend.
- `ProviderRegistry` – maps provider name → provider instance. Created once per run.
- `FallbackRouter` – holds an ordered list of `ModelRoute`. Its `complete(system, user)` tries each route in order, delegating to the right provider, with retries on transient errors. Replaces the current in-class fallback loop in `LLMClient`.

### Config shape

Scenario YAMLs use either a prefix-shorthand string or an explicit dict. Both forms normalize to `ModelRoute` during loading.

Shorthand:

```yaml
llm:
  events: "anthropic:claude-opus-4-6"
  actors: "openrouter:x-ai/grok-4.1-fast"
```

Dict (equivalent):

```yaml
llm:
  events:
    provider: anthropic
    model: claude-opus-4-6
```

Fallback lists mix forms freely:

```yaml
llm:
  events:
    - "anthropic:claude-opus-4-6"
    - provider: openrouter
      model: x-ai/grok-4.1-fast
```

Per-actor dicts keep working; values are routes (shorthand or dict) instead of bare strings.

A bare string without a `provider:` prefix is an error at load time. (No implicit default – we migrate all existing scenarios in the same PR.)

### Provider interface

New file `scenario_lab/providers/base.py`:

```python
class LLMProvider(ABC):
    name: ClassVar[str]

    @abstractmethod
    def complete(
        self,
        system: str,
        user: str,
        *,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse: ...

    def close(self) -> None: ...
```

`LLMResponse` stays in `scenario_lab/llm.py`. Extend `TokenUsage` with a `provider: str` field (alongside existing `model`) so cost tracking can disambiguate identical model IDs served by different providers.

### Concrete providers

`scenario_lab/providers/openrouter.py` – extracts the current `LLMClient` body (HTTP call, `_extract_content_from_response`, 429/timeout handling) into a provider. No behavior change.

`scenario_lab/providers/anthropic.py` – uses the official `anthropic` SDK (`pip install anthropic`). Key mapping details:

- Auth: `ANTHROPIC_API_KEY` env var, same pattern as current `OPENROUTER_API_KEY`.
- Call: `client.messages.create(model=..., system=system, messages=[{"role": "user", "content": user}], max_tokens=..., temperature=...)`.
- Response: concatenate `TextBlock.text` entries from `message.content`.
- Usage: `message.usage.input_tokens` → `prompt_tokens`, `message.usage.output_tokens` → `completion_tokens`, sum → `total_tokens`. Cache fields (`cache_creation_input_tokens`, `cache_read_input_tokens`) are read and stored on `TokenUsage` as new optional fields, but first iteration doesn't set `cache_control` on any blocks.
- Errors: map `anthropic.RateLimitError` to the same retry path the OpenRouter provider uses; map `anthropic.APIStatusError` to a generic provider failure that moves the router to the next route.

### Router

`scenario_lab/router.py`:

```python
class FallbackRouter:
    def __init__(
        self,
        routes: list[ModelRoute],
        registry: ProviderRegistry,
        *,
        temperature: float,
        max_tokens: int,
    ): ...

    def complete(self, system: str, user: str) -> LLMResponse: ...

    @property
    def primary_route(self) -> ModelRoute: ...

    def close(self) -> None: ...
```

Retry policy mirrors the current `LLMClient`:

- Up to 3 attempts per route on rate-limit / timeout / network errors, exponential backoff on 429.
- On exhaustion or non-retryable error, move to the next route and log a fallback message in the same format as today.
- After all routes fail, raise `LLMError` with the full list of attempted routes.

The orchestrator's client-reuse logic (share one client across tasks that use the same primary model) becomes route-reuse: if two tasks share the same primary route, they share one `FallbackRouter` instance.

### Pricing

Split pricing per provider:

- `scenario_lab/pricing/openrouter.py` – existing `OpenRouterPricingCache`, unchanged.
- `scenario_lab/pricing/anthropic.py` – new `AnthropicPricingCache`. Anthropic does not publish a price-list endpoint, so fetch from a maintained third-party source (LiteLLM's `https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json`), filter to `anthropic/*` entries, and cache locally with the same TTL+seed mechanism OpenRouter uses. Bundle a seed JSON at `scenario_lab/data/anthropic_pricing_seed.json` so estimates work offline on first install.
- `scenario_lab/pricing/__init__.py` – exposes `get_pricing_for(route: ModelRoute) -> dict | None` that dispatches to the right cache.

`CostCalculator.get_model_pricing` takes a `ModelRoute` (or `TokenUsage`, which now carries `provider`). The default-pricing fallback and unknown-model warnings move here unchanged.

Open question for the user: the LiteLLM source is third-party and updates on their cadence. If you want Anthropic-only control, we can instead maintain the seed manually and skip the remote fetch. Flag this before implementation.

### Code changes by file

1. `scenario_lab/models.py`
   - Add `ModelRoute` dataclass.
   - `LLMConfig` fields keep their names but their values are now `ModelRoute | list[ModelRoute] | dict[str, ModelRoute | list[ModelRoute]]`. Remove the old `Union[str, List[str]]` annotations.
   - `get_actor_models` → `get_actor_routes`. Same semantics, returns routes.
   - `normalize_to_list` → operates on routes.

2. `scenario_lab/loader.py`
   - New helper `parse_route(value) -> ModelRoute` that accepts `"provider:model"` strings and `{provider, model}` dicts.
   - New helper `parse_routes(value) -> list[ModelRoute]` for fallback lists.
   - `LLMConfig` construction runs every model field through these helpers. Clear error message when provider prefix is missing.

3. `scenario_lab/providers/` – new package with `base.py`, `openrouter.py`, `anthropic.py`, `registry.py`.

4. `scenario_lab/router.py` – new module with `FallbackRouter`.

5. `scenario_lab/llm.py`
   - Keep `LLMResponse`, `LLMError`, `LLMRateLimitError`, `LLMParseError` (they're provider-agnostic).
   - Delete `LLMClient` body; keep a thin deprecation shim only if tests outside our control depend on it. Otherwise remove.
   - `MockLLMClient` stays, but gains a `provider` attribute (defaults to `"mock"`) and exposes the same `complete(system, user)` surface the router uses. Rename to `MockRouter` if cleaner.

6. `scenario_lab/orchestrator.py`
   - Replace every `LLMClient(...)` call with `FallbackRouter(routes=..., registry=..., ...)`.
   - Reuse logic keys on primary route instead of primary model string.
   - `_owned_clients` → `_owned_routers`.

7. `scenario_lab/analysis.py`
   - Same swap: build a `FallbackRouter` from `llm_config.analysis`.

8. `scenario_lab/cost.py` + `scenario_lab/pricing.py`
   - Split pricing per provider (see above).
   - `TokenUsage` gains `provider: str`. Populate it from the router/provider at call sites.
   - `CostCalculator` takes routes/usage-with-provider; update all call sites.

9. `scenario_lab/model_audit.py`, `scenario_lab/validator.py`
   - Audit findings are reported per route (include provider in the scope/message).
   - Legacy-family regexes run against the model portion of the route, unchanged.
   - `model-policy.yaml` may need a `provider` key per rule; if untouched, rules apply to all providers.

10. `scenario_lab/cli.py`
    - `audit-models`, `estimate`, `validate`, and any user-facing model listings show `provider:model`.
    - The existing `refresh-pricing` command refreshes both caches. Add a `--provider` flag to scope to one.

### Config migration

Write a one-shot migration script `scripts/migrate_llm_config.py` that:

- Walks `scenarios/**/*.yaml`.
- For every string/list value under `llm:` that lacks a provider prefix, rewrites it as `openrouter:<original>`.
- Leaves already-prefixed values alone.
- Prints a diff and requires `--apply` to write.

Run it in the same PR and commit the result. All 7 affected files today are OpenRouter-only, so the migration is mechanical.

### Tests

Update existing tests and add new ones:

- `tests/test_llm.py` → split into `tests/test_providers_openrouter.py` (HTTP mocked via `httpx.MockTransport`) and `tests/test_providers_anthropic.py` (SDK mocked via `monkeypatch` on `anthropic.Anthropic`).
- New `tests/test_router.py` – covers single-route success, fallback after 429 exhaustion, fallback across providers, full exhaustion raises `LLMError`, retry-reuse of primary route.
- New `tests/test_loader_routes.py` – parse shorthand, parse dict, parse mixed fallback list, error on missing prefix, per-actor dict.
- `tests/test_pricing.py` – extend with Anthropic pricing cache: seed-only offline, remote fetch, TTL refresh.
- `tests/test_orchestrator_integration.py`, `tests/test_output.py` – update `MockLLMClient` usages to the new surface.
- Eval tests (`tests/evals/**`) – update to construct a router instead of an `LLMClient`.

### Docs to update

- `docs/ARCHITECTURE.md` – LLM client section becomes "LLM providers and routing". Add a short diagram of the provider/router/cache split.
- `docs/MODEL_TESTING.md` – examples use the new `provider:model` syntax.
- `README.md` – env vars section lists both `OPENROUTER_API_KEY` and `ANTHROPIC_API_KEY`; mention that both are optional but at least one must be set for real runs.
- `docs/ROADMAP.md` – mark this spec as in progress; add a follow-up item for prompt caching.

## Acceptance criteria

1. `python -m scenario_lab.cli validate scenarios/sweden-ai-2030` passes against the migrated config.
2. `python -m scenario_lab.cli run scenarios/sweden-ai-2030 --turns 1` runs successfully against OpenRouter (unchanged behavior).
3. A scenario with `events: "anthropic:claude-opus-4-6"` runs a turn against the Anthropic SDK and records a `CostDetails` entry whose `provider` is `"anthropic"` and whose pricing came from the Anthropic cache.
4. A fallback list `["anthropic:...", "openrouter:..."]` falls over to the OpenRouter route when the Anthropic route is forced to raise (test via monkeypatched provider).
5. `python -m scenario_lab.cli audit-models` prints routes as `provider:model` and flags legacy families regardless of provider.
6. `python -m scenario_lab.cli refresh-pricing` refreshes both caches; `--provider anthropic` refreshes only the Anthropic cache.
7. No remaining references to `LLMClient` outside the shim (if any) and `MockLLMClient`.
8. `pytest` green, including evals that can run offline.

## Implementation order (suggested for Sonnet)

1. Introduce `ModelRoute` + loader parsing + migration script. Ship the YAML migration as its own commit so diffs stay readable.
2. Extract `providers/base.py` + `providers/openrouter.py` + `ProviderRegistry`. Wire `FallbackRouter` to use only OpenRouter. Delete old `LLMClient`. Tests green.
3. Add `providers/anthropic.py` and Anthropic pricing cache. Add the end-to-end test for an Anthropic route.
4. Update `audit-models`, CLI pricing refresh, docs.
5. Run full test suite and a one-turn live run against each provider.

## Open questions to resolve before starting

- Anthropic pricing source: LiteLLM's JSON vs. a hand-maintained seed. Default in this spec is LiteLLM with seed fallback; confirm or switch.
- Keep `LLMClient` as a deprecation shim for one release, or delete outright? Default: delete, since the project is pre-1.0 and all call sites are in-repo.

