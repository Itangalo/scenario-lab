"""FallbackRouter: tries an ordered list of ModelRoutes until one succeeds."""

import time
from typing import Callable, Optional

from .llm import (
    LLMError,
    LLMRateLimitError,
    LLMResponse,
    LLMTransientError,
    LLMUnsupportedStructuredError,
)
from .models import ModelRoute, ResolvedLimits
from .providers.registry import ProviderRegistry


class FallbackRouter:
    """Routes completion requests through an ordered list of ModelRoutes.

    For each route, retries up to ``MAX_RETRIES`` times on transient errors –
    rate limits, connection and read timeouts, wall-clock deadline overruns,
    and malformed responses – backing off between attempts. After exhausting
    retries on a route it falls through to the next one. After all routes
    fail, raises LLMError.

    Errors that say the request itself was unacceptable (a rejected model, an
    exhausted reasoning budget) are *not* retried: repeating them identically
    cannot succeed, so the router moves straight to the next route.

    Limits follow the model, not the step: when ``limits_resolver`` is given,
    max_tokens and the call deadline are resolved per route attempt (see
    ``LLMConfig.resolve_limits``), so a fallback list can pair a reasoning
    model with an instruct one without either inheriting the other's limits.
    """

    MAX_RETRIES = 3

    def __init__(
        self,
        routes: list[ModelRoute],
        registry: ProviderRegistry,
        *,
        temperature: float,
        max_tokens: Optional[int] = None,
        limits_resolver: Optional[Callable[[ModelRoute], ResolvedLimits]] = None,
    ) -> None:
        if not routes:
            raise ValueError("FallbackRouter requires at least one route.")
        if limits_resolver is None and max_tokens is None:
            raise ValueError(
                "FallbackRouter needs either max_tokens or a limits_resolver."
            )
        self._routes = routes
        self._registry = registry
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._limits_resolver = limits_resolver

    def _limits_for(self, route: ModelRoute) -> "tuple[int, Optional[int]]":
        """Resolve (max_tokens, call deadline) for one route attempt.

        The deadline is None when no resolver is configured, meaning providers
        keep their own instance defaults.
        """
        if self._limits_resolver is not None:
            limits = self._limits_resolver(route)
            return limits.max_tokens, limits.call_timeout_seconds
        assert self._max_tokens is not None
        return self._max_tokens, None

    @property
    def primary_route(self) -> ModelRoute:
        return self._routes[0]

    def complete(self, system: str, user: str) -> LLMResponse:
        """Try each route in order; return the first successful response."""
        last_error = None  # type: Optional[Exception]

        for route_index, route in enumerate(self._routes):
            is_fallback = route_index > 0
            if is_fallback:
                print(f"  → Falling back to: {route}")

            provider = self._registry.get(route.provider)
            max_tokens, call_timeout = self._limits_for(route)

            for attempt in range(self.MAX_RETRIES):
                try:
                    response = provider.complete(
                        system,
                        user,
                        model=route.model,
                        temperature=self._temperature,
                        max_tokens=max_tokens,
                        call_timeout_seconds=call_timeout,
                    )
                    if is_fallback:
                        print(f"  ✓ Fallback successful ({route})")
                    return response

                except LLMRateLimitError as e:
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"  Rate limit hit ({route}), waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    last_error = LLMError(f"Rate limit exhausted for {route}")
                    print(f"  ✗ {route} unavailable (rate limit)")
                    break

                except LLMTransientError as e:
                    # Transport-level failure: the request never got a verdict,
                    # so the same route deserves another attempt. Without this,
                    # one slow response ended a whole run for the many
                    # scenarios that configure a single route.
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = 2 ** attempt
                        print(
                            f"  Transient network error ({route}): {e}; "
                            f"retrying in {wait_time}s "
                            f"({attempt + 1}/{self.MAX_RETRIES})..."
                        )
                        time.sleep(wait_time)
                        continue
                    last_error = e
                    print(f"  ✗ {route} unavailable after {self.MAX_RETRIES} attempts: {e}")
                    break

                except LLMError as e:
                    # The request was seen and rejected – retrying it unchanged
                    # cannot help, so move to the next route immediately.
                    last_error = e
                    print(f"  ✗ {route} failed: {e}")
                    break

                except Exception as e:
                    if attempt < self.MAX_RETRIES - 1:
                        print(
                            f"  Transient error ({type(e).__name__}) on {route}, "
                            f"retrying ({attempt + 1}/{self.MAX_RETRIES})..."
                        )
                        time.sleep(1)
                        continue
                    last_error = LLMError(f"Error from {route}: {e}")
                    print(f"  ✗ {route} error: {e}")
                    break

        routes_tried = ", ".join(str(r) for r in self._routes)
        raise LLMError(
            f"All routes failed ({routes_tried}). Last error: {last_error}"
        )

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: dict,
        schema_name: str,
    ) -> LLMResponse:
        """Try each route in order for a schema-constrained completion.

        ``LLMUnsupportedStructuredError`` propagates immediately without trying
        other routes – the caller decides whether to fall back to the legacy
        text-parsing path (``auto``) or treat it as fatal (``true``). Rate limits
        and transient errors retry/fall through exactly like ``complete``.
        """
        last_error = None  # type: Optional[Exception]

        for route_index, route in enumerate(self._routes):
            is_fallback = route_index > 0
            if is_fallback:
                print(f"  → Falling back to: {route}")

            provider = self._registry.get(route.provider)
            max_tokens, call_timeout = self._limits_for(route)

            for attempt in range(self.MAX_RETRIES):
                try:
                    response = provider.complete_structured(
                        system,
                        user,
                        model=route.model,
                        temperature=self._temperature,
                        max_tokens=max_tokens,
                        schema=schema,
                        schema_name=schema_name,
                        call_timeout_seconds=call_timeout,
                    )
                    if is_fallback:
                        print(f"  ✓ Fallback successful ({route})")
                    return response

                except LLMUnsupportedStructuredError:
                    # Not a transient/route failure – let the caller decide.
                    raise

                except LLMRateLimitError:
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = 2 ** attempt
                        print(f"  Rate limit hit ({route}), waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    last_error = LLMError(f"Rate limit exhausted for {route}")
                    print(f"  ✗ {route} unavailable (rate limit)")
                    break

                except LLMTransientError as e:
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = 2 ** attempt
                        print(
                            f"  Transient network error ({route}): {e}; "
                            f"retrying in {wait_time}s "
                            f"({attempt + 1}/{self.MAX_RETRIES})..."
                        )
                        time.sleep(wait_time)
                        continue
                    last_error = e
                    print(f"  ✗ {route} unavailable after {self.MAX_RETRIES} attempts: {e}")
                    break

                except LLMError as e:
                    last_error = e
                    print(f"  ✗ {route} failed: {e}")
                    break

                except Exception as e:
                    if attempt < self.MAX_RETRIES - 1:
                        print(
                            f"  Transient error ({type(e).__name__}) on {route}, "
                            f"retrying ({attempt + 1}/{self.MAX_RETRIES})..."
                        )
                        time.sleep(1)
                        continue
                    last_error = LLMError(f"Error from {route}: {e}")
                    print(f"  ✗ {route} error: {e}")
                    break

        routes_tried = ", ".join(str(r) for r in self._routes)
        raise LLMError(
            f"All routes failed ({routes_tried}). Last error: {last_error}"
        )

    def close(self) -> None:
        """No-op: provider lifecycle is managed by ProviderRegistry."""
        pass
