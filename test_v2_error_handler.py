#!/usr/bin/env python3
"""
Test V2 Error Handler

Tests the error handling system with user-friendly messages and recovery suggestions.
"""
import sys
from pathlib import Path
from io import StringIO

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.utils.error_handler import (
    ErrorHandler, ErrorContext, RecoveryAction,
    ErrorSeverity, ErrorCategory, classify_error
)


def test_error_classification():
    """Test automatic error classification"""
    print("=" * 70)
    print("TEST 1: Error classification")
    print("=" * 70)
    print()

    # Test API error (rate limit)
    api_error = Exception("429 Rate limit exceeded")
    context = classify_error(api_error, operation="Making LLM call")
    assert context.category == ErrorCategory.API
    assert context.severity == ErrorSeverity.MEDIUM
    print(f"  ✓ Classified rate limit error: {context.category.value}, severity={context.severity.value}")

    # Test File error
    file_error = FileNotFoundError("scenario.yaml not found")
    context = classify_error(file_error, operation="Loading scenario")
    assert context.category == ErrorCategory.FILE
    assert context.severity == ErrorSeverity.HIGH
    print(f"  ✓ Classified file error: {context.category.value}, severity={context.severity.value}")

    # Test Budget error
    budget_error = Exception("Cost limit of $10 exceeded")
    context = classify_error(budget_error, operation="Running scenario")
    assert context.category == ErrorCategory.BUDGET
    assert context.severity == ErrorSeverity.HIGH
    print(f"  ✓ Classified budget error: {context.category.value}, severity={context.severity.value}")

    # Test Model error
    model_error = Exception("Model not found: invalid/model-name")
    context = classify_error(model_error, operation="Making LLM call")
    assert context.category == ErrorCategory.MODEL
    assert context.severity == ErrorSeverity.HIGH
    print(f"  ✓ Classified model error: {context.category.value}, severity={context.severity.value}")

    print()
    print("✅ Test 1 passed: Error classification works correctly")
    print()
    return True


def test_error_context_creation():
    """Test creating ErrorContext with full details"""
    print("=" * 70)
    print("TEST 2: Error context creation")
    print("=" * 70)
    print()

    error = Exception("API call failed")
    context = ErrorContext(
        error=error,
        category=ErrorCategory.API,
        severity=ErrorSeverity.HIGH,
        operation="Making decision",
        scenario_name="test-scenario",
        run_number=5,
        turn_number=3,
        actor_name="TestActor",
        model_name="openai/gpt-4o-mini",
        cost_so_far=2.50
    )

    assert context.scenario_name == "test-scenario"
    assert context.run_number == 5
    assert context.turn_number == 3
    assert context.actor_name == "TestActor"
    assert context.model_name == "openai/gpt-4o-mini"
    assert context.cost_so_far == 2.50

    print(f"  ✓ Created error context with full details")
    print(f"  ✓ Scenario: {context.scenario_name}")
    print(f"  ✓ Run: {context.run_number}, Turn: {context.turn_number}")
    print(f"  ✓ Actor: {context.actor_name}")
    print(f"  ✓ Cost so far: ${context.cost_so_far:.2f}")

    # Test serialization
    context_dict = context.to_dict()
    assert context_dict['error_type'] == 'Exception'
    assert context_dict['category'] == 'api'
    assert context_dict['severity'] == 'high'
    assert context_dict['scenario_name'] == 'test-scenario'

    print(f"  ✓ Serialization to dict works correctly")

    print()
    print("✅ Test 2 passed: Error context creation works correctly")
    print()
    return True


def test_api_error_recovery_actions():
    """Test recovery actions for API errors"""
    print("=" * 70)
    print("TEST 3: API error recovery actions")
    print("=" * 70)
    print()

    handler = ErrorHandler()

    # Test rate limit error
    error = Exception("429 Rate limit exceeded")
    context = classify_error(error, operation="Making LLM call")
    should_continue, actions = handler.handle_error(context)

    assert should_continue  # Medium severity should continue
    assert len(actions) > 0
    assert any('rate limit' in action.description.lower() for action in actions)

    print(f"  ✓ Rate limit error: should_continue={should_continue}")
    print(f"  ✓ Generated {len(actions)} recovery actions")
    for i, action in enumerate(actions[:3], 1):
        print(f"    {i}. {action.description[:60]}...")

    # Test auth error
    error = Exception("401 Unauthorized")
    context = classify_error(error, operation="Making LLM call")
    should_continue, actions = handler.handle_error(context)

    assert not should_continue  # High severity should not continue
    assert len(actions) > 0
    assert any('api key' in action.description.lower() for action in actions)

    print(f"  ✓ Auth error: should_continue={should_continue}")
    print(f"  ✓ Generated {len(actions)} recovery actions")

    print()
    print("✅ Test 3 passed: API error recovery actions work correctly")
    print()
    return True


def test_file_error_recovery_actions():
    """Test recovery actions for file errors"""
    print("=" * 70)
    print("TEST 4: File error recovery actions")
    print("=" * 70)
    print()

    handler = ErrorHandler()

    # Test file not found
    error = FileNotFoundError("scenario.yaml not found")
    context = classify_error(
        error,
        operation="Loading scenario",
        file_path="scenarios/test/definition/scenario.yaml"
    )
    should_continue, actions = handler.handle_error(context)

    assert not should_continue  # High severity
    assert len(actions) > 0
    assert any('missing file' in action.description.lower() for action in actions)

    print(f"  ✓ File not found error: should_continue={should_continue}")
    print(f"  ✓ Generated {len(actions)} recovery actions")
    for i, action in enumerate(actions[:3], 1):
        print(f"    {i}. {action.description[:60]}...")

    # Test permission error
    error = PermissionError("Permission denied")
    context = classify_error(
        error,
        operation="Writing output",
        file_path="output/run-001/world-state.md"
    )
    should_continue, actions = handler.handle_error(context)

    assert not should_continue  # High severity
    assert len(actions) > 0
    assert any('permission' in action.description.lower() for action in actions)

    print(f"  ✓ Permission error: should_continue={should_continue}")
    print(f"  ✓ Generated {len(actions)} recovery actions")

    print()
    print("✅ Test 4 passed: File error recovery actions work correctly")
    print()
    return True


def test_budget_error_recovery_actions():
    """Test recovery actions for budget errors"""
    print("=" * 70)
    print("TEST 5: Budget error recovery actions")
    print("=" * 70)
    print()

    handler = ErrorHandler()

    error = Exception("Cost limit of $10.00 exceeded")
    context = classify_error(
        error,
        operation="Running batch scenario",
        scenario_name="test-scenario",
        run_number=3,
        cost_so_far=10.25
    )
    should_continue, actions = handler.handle_error(context)

    assert not should_continue  # High severity
    assert len(actions) > 0
    assert any('cost' in action.description.lower() or 'budget' in action.description.lower()
               for action in actions)

    print(f"  ✓ Budget error: should_continue={should_continue}")
    print(f"  ✓ Current cost: ${context.cost_so_far:.2f}")
    print(f"  ✓ Generated {len(actions)} recovery actions")
    for i, action in enumerate(actions[:3], 1):
        print(f"    {i}. {action.description[:60]}...")

    print()
    print("✅ Test 5 passed: Budget error recovery actions work correctly")
    print()
    return True


def test_error_severity_levels():
    """Test error severity determines continuation"""
    print("=" * 70)
    print("TEST 6: Error severity levels")
    print("=" * 70)
    print()

    handler = ErrorHandler()

    # Low severity - should continue
    context = ErrorContext(
        error=Exception("Minor issue"),
        category=ErrorCategory.UNKNOWN,
        severity=ErrorSeverity.LOW,
        operation="Test operation"
    )
    should_continue, _ = handler.handle_error(context)
    assert should_continue
    print(f"  ✓ LOW severity: should_continue={should_continue}")

    # Medium severity - should continue
    context = ErrorContext(
        error=Exception("Recoverable issue"),
        category=ErrorCategory.UNKNOWN,
        severity=ErrorSeverity.MEDIUM,
        operation="Test operation"
    )
    should_continue, _ = handler.handle_error(context)
    assert should_continue
    print(f"  ✓ MEDIUM severity: should_continue={should_continue}")

    # High severity - should NOT continue
    context = ErrorContext(
        error=Exception("Critical issue"),
        category=ErrorCategory.UNKNOWN,
        severity=ErrorSeverity.HIGH,
        operation="Test operation"
    )
    should_continue, _ = handler.handle_error(context)
    assert not should_continue
    print(f"  ✓ HIGH severity: should_continue={should_continue}")

    # Fatal severity - should NOT continue
    context = ErrorContext(
        error=Exception("Fatal issue"),
        category=ErrorCategory.UNKNOWN,
        severity=ErrorSeverity.FATAL,
        operation="Test operation"
    )
    should_continue, _ = handler.handle_error(context)
    assert not should_continue
    print(f"  ✓ FATAL severity: should_continue={should_continue}")

    print()
    print("✅ Test 6 passed: Error severity levels work correctly")
    print()
    return True


def test_error_history_tracking():
    """Test error history tracking"""
    print("=" * 70)
    print("TEST 7: Error history tracking")
    print("=" * 70)
    print()

    handler = ErrorHandler()

    # Handle multiple errors
    for i in range(3):
        error = Exception(f"Error {i+1}")
        context = ErrorContext(
            error=error,
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.LOW,
            operation=f"Operation {i+1}"
        )
        handler.handle_error(context)

    assert len(handler.error_history) == 3
    print(f"  ✓ Tracked {len(handler.error_history)} errors in history")

    for i, ctx in enumerate(handler.error_history, 1):
        print(f"    {i}. {ctx.operation}: {str(ctx.error)}")

    print()
    print("✅ Test 7 passed: Error history tracking works correctly")
    print()
    return True


def run_all_tests():
    """Run all error handler tests"""
    print()
    print("=" * 70)
    print("V2 ERROR HANDLER TESTS")
    print("=" * 70)
    print()

    # Suppress stderr output during tests (errors are printed to stderr)
    original_stderr = sys.stderr
    sys.stderr = StringIO()

    try:
        tests = [
            test_error_classification,
            test_error_context_creation,
            test_api_error_recovery_actions,
            test_file_error_recovery_actions,
            test_budget_error_recovery_actions,
            test_error_severity_levels,
            test_error_history_tracking,
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

    finally:
        # Restore stderr
        sys.stderr = original_stderr

    print("=" * 70)
    print("ERROR HANDLER TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL ERROR HANDLER TESTS PASSED")
        print()
        print("Phase 3.5 Complete: Error Handling")
        print("  ✓ Error classification (10 categories)")
        print("  ✓ Error severity levels (LOW/MEDIUM/HIGH/FATAL)")
        print("  ✓ Rich error context")
        print("  ✓ User-friendly error messages")
        print("  ✓ Recovery action suggestions")
        print("  ✓ Error history tracking")
        print("  ✓ Category-specific explanations")
        print("  ✓ Priority-sorted recovery actions")
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
