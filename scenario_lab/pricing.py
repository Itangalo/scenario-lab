"""OpenRouter pricing lookup with a local JSON cache."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import json
import os

import httpx


MODELS_API_URL = "https://openrouter.ai/api/v1/models"
USER_MODELS_API_URL = "https://openrouter.ai/api/v1/models/user"
DEFAULT_PRICING = {"prompt": 5.0, "completion": 15.0}
DEFAULT_CACHE_TTL_HOURS = 72
BUNDLED_PRICING_PATH = (
    Path(__file__).resolve().parent / "data" / "openrouter_pricing_seed.json"
)
DEFAULT_CACHE_PATH = (
    Path(__file__).resolve().parent.parent
    / ".scenario-lab-cache"
    / "openrouter-pricing.json"
)


def _now_utc() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)


def _parse_timestamp(value: object) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp."""
    if not isinstance(value, str) or not value.strip():
        return None

    normalized = value.strip().replace("Z", "+00:00")
    try:
        timestamp = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _extract_pricing(model_entry: object) -> Optional[dict]:
    """Extract prompt/completion pricing from an OpenRouter model entry."""
    if not isinstance(model_entry, dict):
        return None

    pricing = model_entry.get("pricing")
    if not isinstance(pricing, dict):
        return None

    try:
        prompt = float(pricing.get("prompt", 0.0)) * 1_000_000
        completion = float(pricing.get("completion", 0.0)) * 1_000_000
    except (TypeError, ValueError):
        return None

    return {
        "prompt": round(prompt, 4),
        "completion": round(completion, 4),
    }


def _normalize_snapshot(data: object) -> Optional[dict]:
    """Normalize a pricing snapshot loaded from disk."""
    if not isinstance(data, dict):
        return None

    raw_models = data.get("models")
    if not isinstance(raw_models, dict):
        return None

    models: dict[str, dict[str, float]] = {}
    for model_id, raw_pricing in raw_models.items():
        if not isinstance(model_id, str) or not isinstance(raw_pricing, dict):
            continue
        try:
            prompt = float(raw_pricing["prompt"])
            completion = float(raw_pricing["completion"])
        except (KeyError, TypeError, ValueError):
            continue
        models[model_id] = {
            "prompt": round(prompt, 4),
            "completion": round(completion, 4),
        }

    if not models:
        return None

    fetched_at = data.get("fetched_at")
    return {
        "fetched_at": fetched_at if isinstance(fetched_at, str) else None,
        "models": models,
        "source": data.get("source", "unknown"),
    }


def load_pricing_snapshot(path: Path) -> Optional[dict]:
    """Load a pricing snapshot from JSON."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    return _normalize_snapshot(raw)


def fetch_openrouter_pricing_snapshot(api_key: Optional[str] = None) -> Optional[dict]:
    """Fetch the OpenRouter model catalog and convert it into a pricing snapshot."""
    resolved_api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    request_options = []
    if resolved_api_key:
        request_options.append(
            (
                USER_MODELS_API_URL,
                {"Authorization": f"Bearer {resolved_api_key}"},
            )
        )
    request_options.append((MODELS_API_URL, {}))

    data: Optional[dict] = None
    for url, headers in request_options:
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                candidate = response.json()
        except Exception:
            continue

        if isinstance(candidate, dict):
            data = candidate
            break

    if data is None:
        return None

    raw_models = data.get("data")
    if not isinstance(raw_models, list):
        return None

    models: dict[str, dict[str, float]] = {}
    for entry in raw_models:
        if not isinstance(entry, dict):
            continue
        model_id = entry.get("id")
        if not isinstance(model_id, str):
            continue
        pricing = _extract_pricing(entry)
        if pricing is None:
            continue
        models[model_id] = pricing

    if not models:
        return None

    return {
        "fetched_at": _now_utc().isoformat().replace("+00:00", "Z"),
        "models": models,
        "source": "openrouter",
    }


class OpenRouterPricingCache:
    """Pricing cache backed by a local JSON file and OpenRouter refreshes."""

    def __init__(
        self,
        cache_path: Optional[Path] = None,
        bundled_path: Optional[Path] = None,
        ttl_hours: Optional[int] = None,
    ):
        """Initialize pricing cache settings."""
        ttl_from_env = os.environ.get("SCENARIO_LAB_PRICING_TTL_HOURS")
        resolved_ttl_hours = ttl_hours
        if resolved_ttl_hours is None and ttl_from_env:
            try:
                resolved_ttl_hours = int(ttl_from_env)
            except ValueError:
                resolved_ttl_hours = DEFAULT_CACHE_TTL_HOURS
        if resolved_ttl_hours is None or resolved_ttl_hours < 1:
            resolved_ttl_hours = DEFAULT_CACHE_TTL_HOURS

        cache_override = os.environ.get("SCENARIO_LAB_PRICING_CACHE")
        if cache_path is not None:
            resolved_cache_path = Path(cache_path)
        elif cache_override:
            resolved_cache_path = Path(cache_override)
        else:
            resolved_cache_path = DEFAULT_CACHE_PATH

        self.cache_path = resolved_cache_path
        self.bundled_path = bundled_path or BUNDLED_PRICING_PATH
        self.ttl = timedelta(hours=resolved_ttl_hours)
        self._snapshot: Optional[dict] = None
        self._refresh_attempted = False

    def get_model_pricing(self, model: str) -> Optional[dict]:
        """Return pricing for a model, refreshing the cache if needed."""
        snapshot = self._load_snapshot()
        model_missing = snapshot is None or model not in snapshot["models"]
        cache_stale = self._is_snapshot_stale(snapshot)

        if (model_missing or cache_stale) and not self._refresh_attempted:
            self.refresh()
            self._refresh_attempted = True
            snapshot = self._load_snapshot(force_reload=True)

        if snapshot is None:
            return None

        pricing = snapshot["models"].get(model)
        if pricing is None:
            return None

        return {
            "prompt": pricing["prompt"],
            "completion": pricing["completion"],
        }

    def refresh(self) -> bool:
        """Fetch the latest pricing snapshot and persist it locally."""
        snapshot = fetch_openrouter_pricing_snapshot()
        if snapshot is None:
            return False

        self._snapshot = snapshot
        self._write_snapshot(snapshot)
        return True

    def _load_snapshot(self, force_reload: bool = False) -> Optional[dict]:
        """Load runtime cache first, then fall back to bundled seed data."""
        if self._snapshot is not None and not force_reload:
            return self._snapshot

        runtime_snapshot = load_pricing_snapshot(self.cache_path)
        bundled_snapshot = load_pricing_snapshot(self.bundled_path)
        self._snapshot = runtime_snapshot or bundled_snapshot
        return self._snapshot

    def _is_snapshot_stale(self, snapshot: Optional[dict]) -> bool:
        """Check whether a snapshot is older than the configured TTL."""
        if snapshot is None:
            return True

        fetched_at = _parse_timestamp(snapshot.get("fetched_at"))
        if fetched_at is None:
            return True

        return _now_utc() - fetched_at > self.ttl

    def _write_snapshot(self, snapshot: dict) -> None:
        """Write a snapshot to the runtime cache path."""
        payload = json.dumps(snapshot, indent=2, ensure_ascii=False)
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(payload, encoding="utf-8")
        except OSError:
            # A failed cache write should not break cost estimation.
            return


_DEFAULT_PRICING_CACHE = OpenRouterPricingCache()


def get_pricing_cache() -> OpenRouterPricingCache:
    """Return the process-wide pricing cache."""
    return _DEFAULT_PRICING_CACHE
