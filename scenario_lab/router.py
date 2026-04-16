"""FallbackRouter: tries an ordered list of ModelRoutes until one succeeds."""

import time
from typing import Optional

from .llm import LLMError, LLMRateLimitError, LLMResponse
from .models import ModelRoute
from .providers.registry import ProviderRegistry


class FallbackRouter:
    """Routes completion requests through an ordered list of ModelRoutes.

    For each route, retries up to *max_retries* times on transient errors
    (rate limits, timeouts, network errors, malformed responses). After
    exhausting retries on a route it falls through to the next one.
    After all routes fail, raises LLMError.
    """

    MAX_RETRIES = 3

    def __init__(
        self,
        routes: list[ModelRoute],
        registry: ProviderRegistry,
        *,
        temperature: float,
        max_tokens: int,
    ) -> None:
        if not routes:
            raise ValueError("FallbackRouter requires at least one route.")
        self._routes = routes
        self._registry = registry
        self._temperature = temperature
        self._max_tokens = max_tokens

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

            for attempt in range(self.MAX_RETRIES):
                try:
                    response = provider.complete(
                        system,
                        user,
                        model=route.model,
                        temperature=self._temperature,
                        max_tokens=self._max_tokens,
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

                except LLMError as e:
                    # Non-retryable provider error – move to next route immediately
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
