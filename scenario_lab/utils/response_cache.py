"""
Response Cache - Intelligent caching of LLM responses to reduce costs and improve performance

V2 Migration Notes:
- Works with V2 LLMResponse dataclass
- Integrates with V2 API client
- Supports async operations
- No V1 dependencies

Features:
- In-memory and disk-backed caching
- Configurable TTL (time-to-live)
- Cache statistics (hits, misses, savings)
- Automatic cache invalidation
- Content-based cache keys (hash of prompt + model)
"""
import hashlib
import json
import time
import os
import logging
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached response entry"""
    response: str
    tokens_used: int
    input_tokens: int
    output_tokens: int
    model: str
    timestamp: float
    prompt_hash: str
    hit_count: int = 0


@dataclass
class CacheStats:
    """Statistics about cache performance"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    tokens_saved: int = 0
    estimated_cost_saved: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_requests': self.total_requests,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': f"{self.hit_rate:.1f}%",
            'tokens_saved': self.tokens_saved,
            'estimated_cost_saved': f"${self.estimated_cost_saved:.4f}"
        }


class ResponseCache:
    """
    Intelligent cache for LLM responses (V2)

    Caches responses based on content hash of (model + messages).
    Supports both in-memory and disk-backed storage.
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        ttl: int = 3600,  # 1 hour default
        max_memory_entries: int = 1000,
        enabled: bool = True
    ):
        """
        Initialize response cache

        Args:
            cache_dir: Directory for disk cache (None = memory only)
            ttl: Time-to-live in seconds (0 = no expiration)
            max_memory_entries: Maximum entries in memory cache
            enabled: Whether caching is enabled
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.max_memory_entries = max_memory_entries
        self.enabled = enabled

        # In-memory cache
        self.memory_cache: Dict[str, CacheEntry] = {}

        # Statistics
        self.stats = CacheStats()

        # Setup disk cache
        if cache_dir:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
            self._load_disk_cache()

        logger.info(
            f"Response cache initialized: "
            f"enabled={enabled}, ttl={ttl}s, "
            f"disk={'yes' if cache_dir else 'no'}"
        )

    def _compute_cache_key(self, model: str, messages: List[Dict[str, str]]) -> str:
        """
        Compute cache key from model and messages

        Uses SHA256 hash of concatenated model + messages JSON
        """
        messages_json = json.dumps(messages, sort_keys=True)
        content = f"{model}::{messages_json}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry has expired"""
        if self.ttl == 0:
            return False

        age = time.time() - entry.timestamp
        return age > self.ttl

    def _load_disk_cache(self):
        """Load cache entries from disk"""
        if not self.cache_dir:
            return

        cache_file = os.path.join(self.cache_dir, 'response_cache.json')
        if not os.path.exists(cache_file):
            return

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            loaded = 0
            for key, entry_dict in data.items():
                entry = CacheEntry(**entry_dict)

                # Skip expired entries
                if not self._is_expired(entry):
                    self.memory_cache[key] = entry
                    loaded += 1

            logger.info(f"Loaded {loaded} entries from disk cache")

        except Exception as e:
            logger.warning(f"Failed to load disk cache: {e}")

    def _save_disk_cache(self):
        """Save cache entries to disk"""
        if not self.cache_dir:
            return

        cache_file = os.path.join(self.cache_dir, 'response_cache.json')

        try:
            # Convert entries to dict format
            data = {
                key: asdict(entry)
                for key, entry in self.memory_cache.items()
                if not self._is_expired(entry)
            }

            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(data)} entries to disk cache")

        except Exception as e:
            logger.warning(f"Failed to save disk cache: {e}")

    def get(
        self,
        model: str,
        messages: List[Dict[str, str]]
    ) -> Optional[CacheEntry]:
        """
        Get cached response if available

        Args:
            model: Model identifier
            messages: Input messages list

        Returns:
            CacheEntry if cached, None otherwise
        """
        if not self.enabled:
            return None

        self.stats.total_requests += 1

        cache_key = self._compute_cache_key(model, messages)

        # Check memory cache
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]

            # Check expiration
            if self._is_expired(entry):
                del self.memory_cache[cache_key]
                self.stats.cache_misses += 1
                logger.debug(f"Cache expired for key {cache_key[:8]}...")
                return None

            # Cache hit!
            entry.hit_count += 1
            self.stats.cache_hits += 1
            self.stats.tokens_saved += entry.tokens_used

            # Estimate cost saved using V2 model pricing
            from scenario_lab.utils.model_pricing import estimate_cost

            cost_saved = estimate_cost(
                model=entry.model,
                estimated_input_tokens=entry.input_tokens,
                estimated_output_tokens=entry.output_tokens
            )
            self.stats.estimated_cost_saved += cost_saved

            logger.debug(
                f"Cache hit for {model}: {cache_key[:8]}... "
                f"(hit #{entry.hit_count})"
            )

            return entry

        # Cache miss
        self.stats.cache_misses += 1
        logger.debug(f"Cache miss for {model}: {cache_key[:8]}...")
        return None

    def put(
        self,
        model: str,
        messages: List[Dict[str, str]],
        response: str,
        tokens_used: int,
        input_tokens: int,
        output_tokens: int
    ):
        """
        Store response in cache

        Args:
            model: Model identifier
            messages: Input messages list
            response: Model response
            tokens_used: Total number of tokens used
            input_tokens: Input tokens
            output_tokens: Output tokens
        """
        if not self.enabled:
            return

        cache_key = self._compute_cache_key(model, messages)

        # Create cache entry
        entry = CacheEntry(
            response=response,
            tokens_used=tokens_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            timestamp=time.time(),
            prompt_hash=cache_key,
            hit_count=0
        )

        # Store in memory
        self.memory_cache[cache_key] = entry

        # Enforce max memory entries (LRU-style eviction)
        if len(self.memory_cache) > self.max_memory_entries:
            # Remove oldest entry
            oldest_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k].timestamp
            )
            del self.memory_cache[oldest_key]
            logger.debug(f"Evicted oldest cache entry: {oldest_key[:8]}...")

        # Save to disk if enabled
        if self.cache_dir:
            self._save_disk_cache()

        logger.debug(f"Cached response for {model}: {cache_key[:8]}...")

    def clear(self):
        """Clear all cache entries"""
        self.memory_cache.clear()

        if self.cache_dir:
            cache_file = os.path.join(self.cache_dir, 'response_cache.json')
            if os.path.exists(cache_file):
                os.remove(cache_file)

        logger.info("Cache cleared")

    def get_stats(self) -> CacheStats:
        """Get current cache statistics"""
        return self.stats

    def reset_stats(self):
        """Reset cache statistics"""
        self.stats = CacheStats()
        logger.info("Cache statistics reset")

    def get_size(self) -> int:
        """Get number of entries in cache"""
        return len(self.memory_cache)

    def print_stats(self):
        """Print cache statistics"""
        print("\n" + "=" * 60)
        print("CACHE STATISTICS")
        print("=" * 60)
        print(f"Total requests:      {self.stats.total_requests}")
        print(f"Cache hits:          {self.stats.cache_hits}")
        print(f"Cache misses:        {self.stats.cache_misses}")
        print(f"Hit rate:            {self.stats.hit_rate:.1f}%")
        print(f"Tokens saved:        {self.stats.tokens_saved:,}")
        print(f"Estimated savings:   ${self.stats.estimated_cost_saved:.4f}")
        print(f"Cache size:          {self.get_size()} entries")
        print("=" * 60 + "\n")


# Global cache instance (singleton pattern)
_global_cache: Optional[ResponseCache] = None


def get_global_cache() -> ResponseCache:
    """Get or create global cache instance"""
    global _global_cache

    if _global_cache is None:
        # Check environment variables for configuration
        enabled = os.environ.get('SCENARIO_CACHE_ENABLED', 'true').lower() == 'true'
        base_cache_dir = os.environ.get('SCENARIO_CACHE_DIR', '.cache/responses')
        ttl = int(os.environ.get('SCENARIO_CACHE_TTL', '3600'))

        # Support run-scoped cache: Each run gets its own cache directory
        # This prevents different runs from sharing cached responses
        run_id = os.environ.get('SCENARIO_RUN_ID')
        if run_id:
            cache_dir = os.path.join(base_cache_dir, run_id)
        else:
            cache_dir = base_cache_dir

        _global_cache = ResponseCache(
            cache_dir=cache_dir if enabled else None,
            ttl=ttl,
            enabled=enabled
        )

    return _global_cache


def reset_global_cache():
    """Reset global cache instance (useful for testing)"""
    global _global_cache
    _global_cache = None
