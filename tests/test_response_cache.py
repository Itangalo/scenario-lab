"""
Tests for response_cache.py - LLM response caching system
"""
import pytest
import sys
import time
import tempfile
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from response_cache import (
    ResponseCache,
    CacheEntry,
    CacheStats,
    get_global_cache,
    cached_llm_call
)


class TestCacheEntry:
    """Test CacheEntry dataclass"""

    def test_cache_entry_creation(self):
        """Test creating a CacheEntry"""
        entry = CacheEntry(
            response="Test response",
            tokens_used=100,
            model="gpt-4o-mini",
            timestamp=time.time(),
            prompt_hash="abc123",
            hit_count=0
        )

        assert entry.response == "Test response"
        assert entry.tokens_used == 100
        assert entry.model == "gpt-4o-mini"
        assert entry.hit_count == 0


class TestCacheStats:
    """Test CacheStats dataclass"""

    def test_cache_stats_creation(self):
        """Test creating CacheStats"""
        stats = CacheStats()

        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.tokens_saved == 0
        assert stats.estimated_cost_saved == 0.0

    def test_hit_rate_calculation(self):
        """Test cache hit rate calculation"""
        stats = CacheStats(
            total_requests=100,
            cache_hits=75,
            cache_misses=25
        )

        assert stats.hit_rate == 75.0

    def test_hit_rate_zero_requests(self):
        """Test hit rate with zero requests"""
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_to_dict(self):
        """Test converting stats to dictionary"""
        stats = CacheStats(
            total_requests=100,
            cache_hits=75,
            cache_misses=25,
            tokens_saved=10000,
            estimated_cost_saved=0.05
        )

        d = stats.to_dict()

        assert d['total_requests'] == 100
        assert d['cache_hits'] == 75
        assert d['cache_misses'] == 25
        assert d['hit_rate'] == "75.0%"
        assert d['tokens_saved'] == 10000
        assert '$0.0500' in d['estimated_cost_saved']


class TestResponseCache:
    """Test ResponseCache functionality"""

    def test_cache_creation(self):
        """Test creating a ResponseCache"""
        cache = ResponseCache(
            cache_dir=None,
            ttl=3600,
            max_memory_entries=1000,
            enabled=True
        )

        assert cache.enabled is True
        assert cache.ttl == 3600
        assert cache.max_memory_entries == 1000
        assert cache.get_size() == 0

    def test_cache_disabled(self):
        """Test cache with caching disabled"""
        cache = ResponseCache(enabled=False)

        cache.put("model", "prompt", "response", 100)
        result = cache.get("model", "prompt")

        assert result is None
        assert cache.get_size() == 0

    def test_put_and_get(self):
        """Test putting and getting from cache"""
        cache = ResponseCache(enabled=True)

        cache.put("gpt-4o-mini", "test prompt", "test response", 100)
        result = cache.get("gpt-4o-mini", "test prompt")

        assert result is not None
        response, tokens = result
        assert response == "test response"
        assert tokens == 100

    def test_cache_miss(self):
        """Test cache miss"""
        cache = ResponseCache(enabled=True)

        result = cache.get("gpt-4o-mini", "nonexistent prompt")

        assert result is None
        assert cache.stats.cache_misses == 1

    def test_cache_hit(self):
        """Test cache hit"""
        cache = ResponseCache(enabled=True)

        # Put then get
        cache.put("gpt-4o-mini", "test prompt", "test response", 100)
        result = cache.get("gpt-4o-mini", "test prompt")

        assert result is not None
        assert cache.stats.cache_hits == 1
        assert cache.stats.total_requests == 1

    def test_cache_hit_increments(self):
        """Test that multiple cache hits increment counter"""
        cache = ResponseCache(enabled=True)

        cache.put("gpt-4o-mini", "test prompt", "test response", 100)

        # Get 3 times
        for _ in range(3):
            cache.get("gpt-4o-mini", "test prompt")

        assert cache.stats.cache_hits == 3
        assert cache.stats.total_requests == 3

    def test_tokens_saved_tracking(self):
        """Test that tokens saved are tracked"""
        cache = ResponseCache(enabled=True)

        cache.put("gpt-4o-mini", "prompt1", "response1", 100)
        cache.put("gpt-4o-mini", "prompt2", "response2", 200)

        # Hit both
        cache.get("gpt-4o-mini", "prompt1")
        cache.get("gpt-4o-mini", "prompt2")

        assert cache.stats.tokens_saved == 300

    def test_cost_saved_estimation(self):
        """Test cost savings estimation"""
        cache = ResponseCache(enabled=True)

        cache.put("gpt-4o-mini", "test prompt", "test response", 1000)
        cache.get("gpt-4o-mini", "test prompt")

        # Should estimate roughly $0.002 for 1K tokens
        assert cache.stats.estimated_cost_saved > 0
        assert cache.stats.estimated_cost_saved < 0.01

    def test_different_models_separate_cache(self):
        """Test that different models have separate cache entries"""
        cache = ResponseCache(enabled=True)

        cache.put("gpt-4o-mini", "same prompt", "response1", 100)
        cache.put("gpt-4", "same prompt", "response2", 200)

        result1 = cache.get("gpt-4o-mini", "same prompt")
        result2 = cache.get("gpt-4", "same prompt")

        assert result1[0] == "response1"
        assert result2[0] == "response2"

    def test_ttl_expiration(self):
        """Test that entries expire after TTL"""
        cache = ResponseCache(enabled=True, ttl=1)  # 1 second TTL

        cache.put("gpt-4o-mini", "test prompt", "test response", 100)

        # Should hit immediately
        result1 = cache.get("gpt-4o-mini", "test prompt")
        assert result1 is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should miss after expiration
        result2 = cache.get("gpt-4o-mini", "test prompt")
        assert result2 is None

    def test_no_expiration_with_ttl_zero(self):
        """Test that TTL=0 means no expiration"""
        cache = ResponseCache(enabled=True, ttl=0)

        cache.put("gpt-4o-mini", "test prompt", "test response", 100)

        # Wait a bit
        time.sleep(0.5)

        # Should still hit
        result = cache.get("gpt-4o-mini", "test prompt")
        assert result is not None

    def test_max_entries_eviction(self):
        """Test that oldest entries are evicted when max is reached"""
        cache = ResponseCache(enabled=True, max_memory_entries=5)

        # Add 6 entries
        for i in range(6):
            cache.put("gpt-4o-mini", f"prompt{i}", f"response{i}", 100)
            time.sleep(0.01)  # Ensure different timestamps

        # Should have evicted oldest (prompt0)
        assert cache.get_size() == 5
        assert cache.get("gpt-4o-mini", "prompt0") is None
        assert cache.get("gpt-4o-mini", "prompt5") is not None

    def test_clear_cache(self):
        """Test clearing the cache"""
        cache = ResponseCache(enabled=True)

        cache.put("gpt-4o-mini", "prompt1", "response1", 100)
        cache.put("gpt-4o-mini", "prompt2", "response2", 200)

        assert cache.get_size() == 2

        cache.clear()

        assert cache.get_size() == 0
        assert cache.get("gpt-4o-mini", "prompt1") is None

    def test_get_size(self):
        """Test getting cache size"""
        cache = ResponseCache(enabled=True)

        assert cache.get_size() == 0

        cache.put("gpt-4o-mini", "prompt1", "response1", 100)
        assert cache.get_size() == 1

        cache.put("gpt-4o-mini", "prompt2", "response2", 200)
        assert cache.get_size() == 2

    def test_reset_stats(self):
        """Test resetting cache statistics"""
        cache = ResponseCache(enabled=True)

        cache.put("gpt-4o-mini", "test prompt", "test response", 100)
        cache.get("gpt-4o-mini", "test prompt")

        assert cache.stats.cache_hits == 1

        cache.reset_stats()

        assert cache.stats.cache_hits == 0
        assert cache.stats.total_requests == 0

    def test_disk_cache_persistence(self):
        """Test saving and loading cache from disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create cache and add entries
            cache1 = ResponseCache(cache_dir=tmpdir, enabled=True)
            cache1.put("gpt-4o-mini", "prompt1", "response1", 100)
            cache1.put("gpt-4o-mini", "prompt2", "response2", 200)

            # Create new cache instance (should load from disk)
            cache2 = ResponseCache(cache_dir=tmpdir, enabled=True)

            # Should have loaded entries
            assert cache2.get_size() == 2
            result = cache2.get("gpt-4o-mini", "prompt1")
            assert result is not None
            assert result[0] == "response1"

    def test_disk_cache_skips_expired(self):
        """Test that loading from disk skips expired entries"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create cache with short TTL
            cache1 = ResponseCache(cache_dir=tmpdir, enabled=True, ttl=1)
            cache1.put("gpt-4o-mini", "test prompt", "test response", 100)

            # Wait for expiration
            time.sleep(1.1)

            # Create new cache instance (should not load expired entry)
            cache2 = ResponseCache(cache_dir=tmpdir, enabled=True, ttl=1)
            assert cache2.get_size() == 0

    def test_compute_cache_key_consistent(self):
        """Test that cache key computation is consistent"""
        cache = ResponseCache(enabled=True)

        key1 = cache._compute_cache_key("gpt-4o-mini", "test prompt")
        key2 = cache._compute_cache_key("gpt-4o-mini", "test prompt")

        assert key1 == key2

    def test_compute_cache_key_different_for_different_inputs(self):
        """Test that different inputs produce different cache keys"""
        cache = ResponseCache(enabled=True)

        key1 = cache._compute_cache_key("gpt-4o-mini", "prompt1")
        key2 = cache._compute_cache_key("gpt-4o-mini", "prompt2")
        key3 = cache._compute_cache_key("gpt-4", "prompt1")

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3


class TestCachedLLMCall:
    """Test the cached_llm_call convenience function"""

    def test_cached_llm_call_first_call(self):
        """Test first call goes to API"""
        call_count = [0]

        def api_call():
            call_count[0] += 1
            return "response", 100

        # Clear cache first
        cache = get_global_cache()
        cache.clear()

        result = cached_llm_call("gpt-4o-mini", "test prompt", api_call)

        assert result == ("response", 100)
        assert call_count[0] == 1

    def test_cached_llm_call_second_call_cached(self):
        """Test second call uses cache"""
        call_count = [0]

        def api_call():
            call_count[0] += 1
            return "response", 100

        # Clear cache first
        cache = get_global_cache()
        cache.clear()

        # First call
        cached_llm_call("gpt-4o-mini", "test prompt 2", api_call)

        # Second call (should use cache)
        result = cached_llm_call("gpt-4o-mini", "test prompt 2", api_call)

        assert result == ("response", 100)
        assert call_count[0] == 1  # Only called once


class TestGlobalCache:
    """Test global cache singleton"""

    def test_get_global_cache(self):
        """Test getting global cache instance"""
        cache1 = get_global_cache()
        cache2 = get_global_cache()

        # Should be same instance
        assert cache1 is cache2

    def test_global_cache_configuration_from_env(self):
        """Test that global cache respects environment variables"""
        # Save original env
        original_enabled = os.environ.get('SCENARIO_CACHE_ENABLED')
        original_dir = os.environ.get('SCENARIO_CACHE_DIR')

        try:
            # Set env vars
            os.environ['SCENARIO_CACHE_ENABLED'] = 'false'
            os.environ['SCENARIO_CACHE_DIR'] = '/tmp/test_cache'

            # Force recreation of global cache
            import response_cache
            response_cache._global_cache = None

            cache = get_global_cache()

            assert cache.enabled is False

        finally:
            # Restore original env
            if original_enabled:
                os.environ['SCENARIO_CACHE_ENABLED'] = original_enabled
            elif 'SCENARIO_CACHE_ENABLED' in os.environ:
                del os.environ['SCENARIO_CACHE_ENABLED']

            if original_dir:
                os.environ['SCENARIO_CACHE_DIR'] = original_dir
            elif 'SCENARIO_CACHE_DIR' in os.environ:
                del os.environ['SCENARIO_CACHE_DIR']

            # Force recreation for future tests
            response_cache._global_cache = None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
