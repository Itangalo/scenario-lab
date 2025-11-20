#!/usr/bin/env python3
"""
Test V2 Progressive Fallback

Tests the progressive fallback system for resilient execution.
"""
import sys
from pathlib import Path
from io import StringIO
from typing import Callable

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.utils.progressive_fallback import (
    FallbackConfig, ProgressiveFallbackExecutor,
    create_model_fallback_list, should_enable_fallback,
    execute_with_auto_fallback
)
from scenario_lab.utils.error_handler import ErrorHandler


def test_fallback_config():
    """Test FallbackConfig dataclass"""
    print("=" * 70)
    print("TEST 1: FallbackConfig")
    print("=" * 70)
    print()

    # Default config
    config = FallbackConfig()
    assert config.enable_fallback is True
    assert config.max_fallback_attempts == 2
    print(f"  ✓ Default config created")
    print(f"  ✓ enable_fallback: {config.enable_fallback}")
    print(f"  ✓ max_fallback_attempts: {config.max_fallback_attempts}")

    # Custom config
    config = FallbackConfig(
        fallback_models=['model1', 'model2', 'model3'],
        enable_fallback=True,
        max_fallback_attempts=3
    )
    assert len(config.fallback_models) == 3
    assert config.max_fallback_attempts == 3
    print(f"  ✓ Custom config created with {len(config.fallback_models)} fallback models")

    print()
    print("✅ Test 1 passed: FallbackConfig works correctly")
    print()
    return True


def test_create_model_fallback_list():
    """Test smart fallback list generation"""
    print("=" * 70)
    print("TEST 2: Smart fallback list generation")
    print("=" * 70)
    print()

    # Test OpenAI models
    fallbacks = create_model_fallback_list('openai/gpt-4')
    assert 'openai/gpt-4o-mini' in fallbacks
    print(f"  ✓ gpt-4 fallbacks: {fallbacks}")

    fallbacks = create_model_fallback_list('openai/gpt-4o')
    assert 'openai/gpt-4o-mini' in fallbacks
    print(f"  ✓ gpt-4o fallbacks: {fallbacks}")

    # Test Anthropic models
    fallbacks = create_model_fallback_list('anthropic/claude-3-opus')
    assert 'anthropic/claude-3-haiku' in fallbacks
    print(f"  ✓ claude-3-opus fallbacks: {fallbacks}")

    fallbacks = create_model_fallback_list('anthropic/claude-3-sonnet')
    assert 'anthropic/claude-3-haiku' in fallbacks
    print(f"  ✓ claude-3-sonnet fallbacks: {fallbacks}")

    # Test Meta models
    fallbacks = create_model_fallback_list('meta-llama/llama-3.1-70b-instruct')
    assert 'meta-llama/llama-3.1-8b-instruct' in fallbacks
    print(f"  ✓ llama-3.1-70b fallbacks: {fallbacks}")

    # Test generic fallback for unknown model
    fallbacks = create_model_fallback_list('unknown/model')
    assert len(fallbacks) >= 1
    print(f"  ✓ Unknown model fallbacks: {fallbacks}")

    print()
    print("✅ Test 2 passed: Fallback list generation works correctly")
    print()
    return True


def test_should_enable_fallback():
    """Test fallback enablement logic"""
    print("=" * 70)
    print("TEST 3: Fallback enablement logic")
    print("=" * 70)
    print()

    # Should enable fallback for:
    # - Model not found (404)
    assert should_enable_fallback(Exception("404 Model not found"))
    print(f"  ✓ Enables fallback for 404 errors")

    # - Model access denied (403)
    assert should_enable_fallback(Exception("403 Forbidden"))
    print(f"  ✓ Enables fallback for 403 errors")

    # - Timeout
    assert should_enable_fallback(Exception("Request timed out"))
    print(f"  ✓ Enables fallback for timeout errors")

    # - Model overloaded (503)
    assert should_enable_fallback(Exception("503 Service unavailable"))
    print(f"  ✓ Enables fallback for 503 errors")

    # Should NOT enable fallback for:
    # - Auth errors (401)
    assert not should_enable_fallback(Exception("401 Unauthorized"))
    print(f"  ✓ Disables fallback for auth errors")

    # - Rate limits (429)
    assert not should_enable_fallback(Exception("429 Rate limit exceeded"))
    print(f"  ✓ Disables fallback for rate limit errors")

    # - Budget errors
    assert not should_enable_fallback(Exception("Budget limit exceeded"))
    print(f"  ✓ Disables fallback for budget errors")

    print()
    print("✅ Test 3 passed: Fallback enablement logic works correctly")
    print()
    return True


def test_successful_primary_execution():
    """Test successful execution without fallback"""
    print("=" * 70)
    print("TEST 4: Successful primary execution")
    print("=" * 70)
    print()

    config = FallbackConfig(
        fallback_models=['fallback-model-1', 'fallback-model-2'],
        enable_fallback=True
    )
    executor = ProgressiveFallbackExecutor(fallback_config=config)

    # Define a successful function
    def successful_func():
        return "Success!"

    result = executor.execute_with_fallback(
        primary_func=successful_func,
        operation_name="Test operation"
    )

    assert result == "Success!"
    print(f"  ✓ Primary function executed successfully")
    print(f"  ✓ Result: {result}")
    print(f"  ✓ No fallback needed")

    print()
    print("✅ Test 4 passed: Successful primary execution works correctly")
    print()
    return True


def test_fallback_after_primary_failure():
    """Test fallback execution after primary failure"""
    print("=" * 70)
    print("TEST 5: Fallback after primary failure")
    print("=" * 70)
    print()

    # Suppress stderr (error messages are printed there)
    original_stderr = sys.stderr
    sys.stderr = StringIO()

    try:
        config = FallbackConfig(
            fallback_models=['fallback-model-1', 'fallback-model-2'],
            enable_fallback=True,
            max_fallback_attempts=2
        )
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        # Track which functions were called
        calls = []

        def failing_primary():
            calls.append('primary')
            raise Exception("404 Model not found")

        def fallback_generator(model: str) -> Callable:
            def fallback_func():
                calls.append(model)
                if model == 'fallback-model-1':
                    # First fallback also fails
                    raise Exception("Fallback 1 failed")
                else:
                    # Second fallback succeeds
                    return f"Success with {model}"
            return fallback_func

        result = executor.execute_with_fallback(
            primary_func=failing_primary,
            operation_name="Test operation with fallback",
            fallback_func_generator=fallback_generator
        )

        assert 'primary' in calls
        assert 'fallback-model-1' in calls
        assert 'fallback-model-2' in calls
        assert result == "Success with fallback-model-2"

        print(f"  ✓ Primary function failed as expected")
        print(f"  ✓ Tried fallback models: {calls[1:]}")
        print(f"  ✓ Second fallback succeeded")
        print(f"  ✓ Result: {result}")

    finally:
        sys.stderr = original_stderr

    print()
    print("✅ Test 5 passed: Fallback execution works correctly")
    print()
    return True


def test_all_attempts_fail():
    """Test when all attempts (primary + fallbacks) fail"""
    print("=" * 70)
    print("TEST 6: All attempts fail")
    print("=" * 70)
    print()

    # Suppress stderr (error messages are printed there)
    original_stderr = sys.stderr
    sys.stderr = StringIO()

    try:
        config = FallbackConfig(
            fallback_models=['fallback-model-1'],
            enable_fallback=True,
            max_fallback_attempts=1
        )
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        def failing_primary():
            raise Exception("404 Model not found")

        def failing_fallback_generator(model: str) -> Callable:
            def fallback_func():
                raise Exception(f"{model} also failed")
            return fallback_func

        try:
            executor.execute_with_fallback(
                primary_func=failing_primary,
                operation_name="Test all failures",
                fallback_func_generator=failing_fallback_generator
            )
            # Should not reach here
            assert False, "Should have raised an exception"

        except Exception as e:
            # Expected to raise
            assert "404" in str(e) or "not found" in str(e).lower()
            print(f"  ✓ All attempts failed as expected")
            print(f"  ✓ Exception raised: {str(e)[:60]}...")

    finally:
        sys.stderr = original_stderr

    print()
    print("✅ Test 6 passed: All failures handled correctly")
    print()
    return True


def test_fallback_disabled():
    """Test execution with fallback disabled"""
    print("=" * 70)
    print("TEST 7: Fallback disabled")
    print("=" * 70)
    print()

    # Suppress stderr
    original_stderr = sys.stderr
    sys.stderr = StringIO()

    try:
        config = FallbackConfig(
            fallback_models=['fallback-model-1'],
            enable_fallback=False  # Disabled
        )
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        calls = []

        def failing_primary():
            calls.append('primary')
            raise Exception("Some error")

        def fallback_generator(model: str) -> Callable:
            def fallback_func():
                calls.append(model)
                return "Should not be called"
            return fallback_func

        try:
            executor.execute_with_fallback(
                primary_func=failing_primary,
                operation_name="Test with fallback disabled",
                fallback_func_generator=fallback_generator
            )
            assert False, "Should have raised an exception"

        except Exception:
            # Fallback should not have been tried
            assert 'primary' in calls
            assert len(calls) == 1  # Only primary was called
            print(f"  ✓ Primary function failed")
            print(f"  ✓ Fallback was not tried (disabled)")
            print(f"  ✓ Calls: {calls}")

    finally:
        sys.stderr = original_stderr

    print()
    print("✅ Test 7 passed: Fallback disabled works correctly")
    print()
    return True


def test_execute_with_auto_fallback():
    """Test convenience function for auto fallback"""
    print("=" * 70)
    print("TEST 8: Auto fallback convenience function")
    print("=" * 70)
    print()

    # Suppress stderr
    original_stderr = sys.stderr
    sys.stderr = StringIO()

    try:
        calls = []

        def failing_func():
            calls.append('primary')
            # 404 error should trigger fallback
            raise Exception("404 Model not found")

        def fallback_generator(model: str) -> Callable:
            def fallback_func():
                calls.append(model)
                return f"Success with {model}"
            return fallback_func

        result = execute_with_auto_fallback(
            func=failing_func,
            operation_name="Auto fallback test",
            primary_model="openai/gpt-4",
            fallback_func_generator=fallback_generator,
            enable_fallback=True
        )

        assert 'primary' in calls
        assert len(calls) > 1  # Fallback was tried
        assert 'Success with' in result

        print(f"  ✓ Primary failed with 404 error")
        print(f"  ✓ Auto fallback triggered")
        print(f"  ✓ Calls: {calls}")
        print(f"  ✓ Result: {result}")

    finally:
        sys.stderr = original_stderr

    print()
    print("✅ Test 8 passed: Auto fallback works correctly")
    print()
    return True


def run_all_tests():
    """Run all progressive fallback tests"""
    print()
    print("=" * 70)
    print("V2 PROGRESSIVE FALLBACK TESTS")
    print("=" * 70)
    print()

    tests = [
        test_fallback_config,
        test_create_model_fallback_list,
        test_should_enable_fallback,
        test_successful_primary_execution,
        test_fallback_after_primary_failure,
        test_all_attempts_fail,
        test_fallback_disabled,
        test_execute_with_auto_fallback,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("=" * 70)
    print("PROGRESSIVE FALLBACK TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL PROGRESSIVE FALLBACK TESTS PASSED")
        print()
        print("Phase 3.6 Complete: Progressive Fallback")
        print("  ✓ FallbackConfig dataclass")
        print("  ✓ Smart fallback list generation (OpenAI, Anthropic, Meta, etc.)")
        print("  ✓ Fallback enablement logic (404, 403, timeout → enable)")
        print("  ✓ Primary execution")
        print("  ✓ Fallback after primary failure")
        print("  ✓ All attempts fail handling")
        print("  ✓ Fallback disabled mode")
        print("  ✓ Auto fallback convenience function")
        print()
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
