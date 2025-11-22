"""
Tests for Response Cache module

Tests caching functionality, TTL, statistics, and disk persistence.
"""
import pytest
import time
import tempfile
import os
from unittest.mock import patch, MagicMock

from scenario_lab.utils.response_cache import (
    ResponseCache,
    CacheEntry,
    CacheStats,
    get_global_cache,
    reset_global_cache,
)


class TestCacheEntry:
    """Tests for CacheEntry dataclass"""

    def test_create_cache_entry(self):
        """Test creating a cache entry"""
        entry = CacheEntry(
            response="test response",
            tokens_used=100,
            input_tokens=70,
            output_tokens=30,
            model="openai/gpt-4o-mini",
            timestamp=time.time(),
            prompt_hash="abc123"
        )

        assert entry.response == "test response"
        assert entry.tokens_used == 100
        assert entry.input_tokens == 70
        assert entry.output_tokens == 30
        assert entry.model == "openai/gpt-4o-mini"
        assert entry.hit_count == 0


class TestCacheStats:
    """Tests for CacheStats dataclass"""

    def test_initial_stats(self):
        """Test initial cache statistics"""
        stats = CacheStats()

        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.tokens_saved == 0
        assert stats.estimated_cost_saved == 0.0

    def test_hit_rate_zero_requests(self):
        """Test hit rate with zero requests"""
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        stats = CacheStats(
            total_requests=100,
            cache_hits=30,
            cache_misses=70
        )
        assert stats.hit_rate == 30.0

    def test_to_dict(self):
        """Test converting stats to dictionary"""
        stats = CacheStats(
            total_requests=100,
            cache_hits=50,
            cache_misses=50,
            tokens_saved=10000,
            estimated_cost_saved=0.5
        )

        result = stats.to_dict()

        assert result['total_requests'] == 100
        assert result['cache_hits'] == 50
        assert result['cache_misses'] == 50
        assert result['hit_rate'] == "50.0%"
        assert result['tokens_saved'] == 10000
        assert result['estimated_cost_saved'] == "$0.5000"


class TestResponseCache:
    """Tests for ResponseCache class"""

    def test_init_defaults(self):
        """Test cache initialization with defaults"""
        cache = ResponseCache()

        assert cache.enabled is True
        assert cache.ttl == 3600
        assert cache.max_memory_entries == 1000
        assert len(cache.memory_cache) == 0

    def test_init_disabled(self):
        """Test cache initialization when disabled"""
        cache = ResponseCache(enabled=False)
        assert cache.enabled is False

    def test_compute_cache_key_deterministic(self):
        """Test that cache key computation is deterministic"""
        cache = ResponseCache()
        messages = [{"role": "user", "content": "Hello"}]

        key1 = cache._compute_cache_key("model", messages)
        key2 = cache._compute_cache_key("model", messages)

        assert key1 == key2

    def test_compute_cache_key_different_for_different_models(self):
        """Test that different models produce different keys"""
        cache = ResponseCache()
        messages = [{"role": "user", "content": "Hello"}]

        key1 = cache._compute_cache_key("model1", messages)
        key2 = cache._compute_cache_key("model2", messages)

        assert key1 != key2

    def test_compute_cache_key_different_for_different_messages(self):
        """Test that different messages produce different keys"""
        cache = ResponseCache()

        key1 = cache._compute_cache_key("model", [{"role": "user", "content": "Hello"}])
        key2 = cache._compute_cache_key("model", [{"role": "user", "content": "World"}])

        assert key1 != key2

    def test_put_and_get(self):
        """Test storing and retrieving from cache"""
        cache = ResponseCache()
        model = "openai/gpt-4o-mini"
        messages = [{"role": "user", "content": "Test message"}]

        # Store
        cache.put(
            model=model,
            messages=messages,
            response="Test response",
            tokens_used=100,
            input_tokens=70,
            output_tokens=30
        )

        # Retrieve
        entry = cache.get(model, messages)

        assert entry is not None
        assert entry.response == "Test response"
        assert entry.tokens_used == 100

    def test_get_returns_none_for_missing(self):
        """Test that get returns None for missing entries"""
        cache = ResponseCache()
        messages = [{"role": "user", "content": "Not cached"}]

        entry = cache.get("model", messages)
        assert entry is None

    def test_get_when_disabled_returns_none(self):
        """Test that get returns None when cache is disabled"""
        cache = ResponseCache(enabled=False)
        messages = [{"role": "user", "content": "Test"}]

        # Put should also be ignored
        cache.put("model", messages, "response", 100, 70, 30)

        entry = cache.get("model", messages)
        assert entry is None

    def test_cache_expiration(self):
        """Test that expired entries are not returned"""
        cache = ResponseCache(ttl=1)  # 1 second TTL
        messages = [{"role": "user", "content": "Test"}]

        cache.put("model", messages, "response", 100, 70, 30)

        # Should be available immediately
        assert cache.get("model", messages) is not None

        # Wait for expiration
        time.sleep(1.5)

        # Should be expired
        assert cache.get("model", messages) is None

    def test_cache_no_expiration_with_zero_ttl(self):
        """Test that TTL of 0 means no expiration"""
        cache = ResponseCache(ttl=0)
        messages = [{"role": "user", "content": "Test"}]

        # Manually set timestamp to far in the past
        cache.put("model", messages, "response", 100, 70, 30)
        key = cache._compute_cache_key("model", messages)
        cache.memory_cache[key].timestamp = 0  # Very old

        # Should still be available
        entry = cache.get("model", messages)
        assert entry is not None

    def test_max_memory_entries_eviction(self):
        """Test that old entries are evicted when max is reached"""
        cache = ResponseCache(max_memory_entries=3)

        # Add 4 entries
        for i in range(4):
            messages = [{"role": "user", "content": f"Message {i}"}]
            cache.put("model", messages, f"Response {i}", 100, 70, 30)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        # Should only have 3 entries
        assert cache.get_size() == 3

        # Oldest (message 0) should be evicted
        messages0 = [{"role": "user", "content": "Message 0"}]
        assert cache.get("model", messages0) is None

        # Newest (message 3) should still be there
        messages3 = [{"role": "user", "content": "Message 3"}]
        assert cache.get("model", messages3) is not None

    def test_cache_statistics(self):
        """Test that cache statistics are tracked correctly"""
        cache = ResponseCache()
        messages = [{"role": "user", "content": "Test"}]

        # Initial stats
        assert cache.stats.total_requests == 0

        # Miss
        cache.get("model", messages)
        assert cache.stats.total_requests == 1
        assert cache.stats.cache_misses == 1

        # Put and hit
        cache.put("model", messages, "response", 100, 70, 30)
        cache.get("model", messages)

        assert cache.stats.total_requests == 2
        assert cache.stats.cache_hits == 1
        assert cache.stats.tokens_saved == 100

    def test_clear_cache(self):
        """Test clearing the cache"""
        cache = ResponseCache()
        messages = [{"role": "user", "content": "Test"}]

        cache.put("model", messages, "response", 100, 70, 30)
        assert cache.get_size() == 1

        cache.clear()
        assert cache.get_size() == 0

    def test_reset_stats(self):
        """Test resetting cache statistics"""
        cache = ResponseCache()
        messages = [{"role": "user", "content": "Test"}]

        cache.get("model", messages)  # Creates a miss
        assert cache.stats.cache_misses == 1

        cache.reset_stats()
        assert cache.stats.cache_misses == 0

    def test_get_size(self):
        """Test get_size method"""
        cache = ResponseCache()

        assert cache.get_size() == 0

        cache.put("model", [{"role": "user", "content": "1"}], "r1", 100, 70, 30)
        assert cache.get_size() == 1

        cache.put("model", [{"role": "user", "content": "2"}], "r2", 100, 70, 30)
        assert cache.get_size() == 2


class TestResponseCacheDiskPersistence:
    """Tests for disk persistence functionality"""

    def test_disk_cache_save_and_load(self):
        """Test saving and loading from disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create cache and add entry
            cache1 = ResponseCache(cache_dir=tmpdir, ttl=3600)
            messages = [{"role": "user", "content": "Test"}]
            cache1.put("model", messages, "response", 100, 70, 30)

            # Create new cache instance (should load from disk)
            cache2 = ResponseCache(cache_dir=tmpdir, ttl=3600)

            # Should be able to retrieve
            entry = cache2.get("model", messages)
            assert entry is not None
            assert entry.response == "response"

    def test_disk_cache_expired_entries_not_loaded(self):
        """Test that expired entries are not loaded from disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create cache with short TTL
            cache1 = ResponseCache(cache_dir=tmpdir, ttl=1)
            messages = [{"role": "user", "content": "Test"}]
            cache1.put("model", messages, "response", 100, 70, 30)

            # Wait for expiration
            time.sleep(1.5)

            # Create new cache instance
            cache2 = ResponseCache(cache_dir=tmpdir, ttl=1)

            # Should not find expired entry
            assert cache2.get_size() == 0

    def test_clear_removes_disk_cache(self):
        """Test that clear removes disk cache file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ResponseCache(cache_dir=tmpdir)
            messages = [{"role": "user", "content": "Test"}]
            cache.put("model", messages, "response", 100, 70, 30)

            cache_file = os.path.join(tmpdir, 'response_cache.json')
            assert os.path.exists(cache_file)

            cache.clear()
            assert not os.path.exists(cache_file)


class TestGlobalCache:
    """Tests for global cache functions"""

    def test_get_global_cache_creates_singleton(self):
        """Test that get_global_cache returns same instance"""
        reset_global_cache()

        cache1 = get_global_cache()
        cache2 = get_global_cache()

        assert cache1 is cache2

    def test_reset_global_cache(self):
        """Test that reset clears the global cache"""
        cache1 = get_global_cache()
        reset_global_cache()
        cache2 = get_global_cache()

        assert cache1 is not cache2

    @patch.dict(os.environ, {'SCENARIO_CACHE_ENABLED': 'false'})
    def test_global_cache_respects_env_disabled(self):
        """Test that global cache respects SCENARIO_CACHE_ENABLED=false"""
        reset_global_cache()
        cache = get_global_cache()
        assert cache.enabled is False
        reset_global_cache()  # Clean up

    @patch.dict(os.environ, {'SCENARIO_CACHE_TTL': '7200'})
    def test_global_cache_respects_env_ttl(self):
        """Test that global cache respects SCENARIO_CACHE_TTL"""
        reset_global_cache()
        cache = get_global_cache()
        assert cache.ttl == 7200
        reset_global_cache()  # Clean up


class TestCacheIntegration:
    """Integration tests for cache with model pricing"""

    @patch('scenario_lab.utils.response_cache.estimate_cost')
    def test_cost_savings_calculated_on_hit(self, mock_estimate):
        """Test that cost savings are calculated on cache hit"""
        mock_estimate.return_value = 0.001  # $0.001

        cache = ResponseCache()
        messages = [{"role": "user", "content": "Test"}]

        # Put entry
        cache.put("openai/gpt-4o-mini", messages, "response", 100, 70, 30)

        # Hit should calculate savings
        cache.get("openai/gpt-4o-mini", messages)

        mock_estimate.assert_called_once()
        assert cache.stats.estimated_cost_saved > 0

    def test_hit_count_incremented(self):
        """Test that hit count is incremented on cache hit"""
        cache = ResponseCache()
        messages = [{"role": "user", "content": "Test"}]

        cache.put("model", messages, "response", 100, 70, 30)

        # First hit
        entry1 = cache.get("model", messages)
        assert entry1.hit_count == 1

        # Second hit
        entry2 = cache.get("model", messages)
        assert entry2.hit_count == 2
