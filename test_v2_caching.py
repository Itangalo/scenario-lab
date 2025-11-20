#!/usr/bin/env python3
"""
Test V2 Response Caching

Tests the cache integration with V2 API client.
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch
import tempfile

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.utils.api_client import make_llm_call_async, LLMResponse
from scenario_lab.utils.response_cache import get_global_cache, reset_global_cache
import os


# Mock LLM response
MOCK_RESPONSE_TEXT = "This is a test response from the LLM."


async def test_cache_miss_then_hit():
    """Test cache miss followed by cache hit"""
    print("=" * 70)
    print("TEST 1: Cache miss then cache hit")
    print("=" * 70)
    print()

    # Reset cache
    reset_global_cache()

    # Set cache to use temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['SCENARIO_CACHE_DIR'] = tmpdir
        os.environ['SCENARIO_CACHE_ENABLED'] = 'true'

        # Reset cache to pick up new env vars
        reset_global_cache()
        cache = get_global_cache()

        # Clear cache stats
        cache.reset_stats()

        model = "openai/gpt-4o-mini"
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"}
        ]

        mock_response = LLMResponse(
            content=MOCK_RESPONSE_TEXT,
            tokens_used=50,
            input_tokens=30,
            output_tokens=20,
            model=model,
            cached=False
        )

        # First call - should be a cache miss
        with patch('scenario_lab.utils.api_client.make_openrouter_call') as mock_api:
            mock_api.return_value = {
                'choices': [{'message': {'content': MOCK_RESPONSE_TEXT}}],
                'usage': {'total_tokens': 50, 'prompt_tokens': 30, 'completion_tokens': 20}
            }

            response1 = await make_llm_call_async(
                model=model,
                messages=messages,
                api_key="test-key",
                use_cache=True
            )

            assert response1.cached is False, "First call should not be cached"
            assert response1.content == MOCK_RESPONSE_TEXT
            assert mock_api.call_count == 1, "API should be called once"

        print("  ✓ First call made to API (cache miss)")
        print(f"  ✓ Response: {response1.content[:30]}...")

        # Second call - should be a cache hit
        response2 = await make_llm_call_async(
            model=model,
            messages=messages,
            api_key="test-key",
            use_cache=True
        )

        assert response2.cached is True, "Second call should be cached"
        assert response2.content == MOCK_RESPONSE_TEXT
        print("  ✓ Second call served from cache (cache hit)")

        # Check cache stats
        stats = cache.get_stats()
        assert stats.cache_hits == 1, f"Expected 1 cache hit, got {stats.cache_hits}"
        assert stats.cache_misses == 1, f"Expected 1 cache miss, got {stats.cache_misses}"
        assert stats.hit_rate == 50.0, f"Expected 50% hit rate, got {stats.hit_rate}"

        print(f"  ✓ Cache stats: {stats.cache_hits} hits, {stats.cache_misses} misses, {stats.hit_rate:.1f}% hit rate")
        print(f"  ✓ Tokens saved: {stats.tokens_saved}")
        print(f"  ✓ Cost saved: ${stats.estimated_cost_saved:.4f}")

    print()
    print("✅ Test 1 passed: Cache miss then hit works")
    print()
    return True


async def test_cache_disabled():
    """Test with caching disabled"""
    print("=" * 70)
    print("TEST 2: Cache disabled")
    print("=" * 70)
    print()

    # Reset cache
    reset_global_cache()

    model = "openai/gpt-4o-mini"
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 3+3?"}
    ]

    mock_response = {
        'choices': [{'message': {'content': MOCK_RESPONSE_TEXT}}],
        'usage': {'total_tokens': 50, 'prompt_tokens': 30, 'completion_tokens': 20}
    }

    # Call twice with caching disabled
    with patch('scenario_lab.utils.api_client.make_openrouter_call') as mock_api:
        mock_api.return_value = mock_response

        response1 = await make_llm_call_async(
            model=model,
            messages=messages,
            api_key="test-key",
            use_cache=False
        )

        response2 = await make_llm_call_async(
            model=model,
            messages=messages,
            api_key="test-key",
            use_cache=False
        )

        # API should be called twice (no caching)
        assert mock_api.call_count == 2, f"Expected 2 API calls, got {mock_api.call_count}"
        assert response1.cached is False
        assert response2.cached is False

    print("  ✓ Both calls made to API (caching disabled)")
    print("  ✓ No cache hits")

    print()
    print("✅ Test 2 passed: Cache can be disabled")
    print()
    return True


async def test_different_prompts():
    """Test that different prompts don't collide in cache"""
    print("=" * 70)
    print("TEST 3: Different prompts (no collision)")
    print("=" * 70)
    print()

    # Reset cache
    reset_global_cache()

    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['SCENARIO_CACHE_DIR'] = tmpdir
        reset_global_cache()

        model = "openai/gpt-4o-mini"
        messages1 = [{"role": "user", "content": "What is 2+2?"}]
        messages2 = [{"role": "user", "content": "What is 3+3?"}]

        with patch('scenario_lab.utils.api_client.make_openrouter_call') as mock_api:
            mock_api.return_value = {
                'choices': [{'message': {'content': MOCK_RESPONSE_TEXT}}],
                'usage': {'total_tokens': 50, 'prompt_tokens': 30, 'completion_tokens': 20}
            }

            # Call with first prompt
            response1 = await make_llm_call_async(model=model, messages=messages1, api_key="test-key")

            # Call with second prompt
            response2 = await make_llm_call_async(model=model, messages=messages2, api_key="test-key")

            # Both should be cache misses (different prompts)
            assert response1.cached is False
            assert response2.cached is False
            assert mock_api.call_count == 2

        print("  ✓ Two different prompts made two API calls")
        print("  ✓ No cache collision")

    print()
    print("✅ Test 3 passed: Different prompts don't collide")
    print()
    return True


async def run_all_tests():
    """Run all caching tests"""
    print()
    print("=" * 70)
    print("V2 RESPONSE CACHING TESTS")
    print("=" * 70)
    print()

    tests = [
        test_cache_miss_then_hit,
        test_cache_disabled,
        test_different_prompts,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("=" * 70)
    print("CACHING TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL CACHING TESTS PASSED")
        print()
        print("Phase 3.2 Complete: Response Caching")
        print("  ✓ Cache integration with V2 API client")
        print("  ✓ Cache hit/miss tracking")
        print("  ✓ Cost savings calculation")
        print("  ✓ Can be disabled via parameter")
        print("  ✓ Different prompts don't collide")
        print()
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
