"""Tests for safe expression evaluator security."""

import pytest
from scenario_lab.validator import eval_probability_formula, SafeExpressionEvaluator


def test_safe_basic_arithmetic():
    """Test that basic arithmetic operations work."""
    assert eval_probability_formula("10 + 5", {}) == 15.0
    assert eval_probability_formula("10 - 5", {}) == 5.0
    assert eval_probability_formula("10 * 5", {}) == 50.0
    assert eval_probability_formula("10 / 5", {}) == 2.0
    assert eval_probability_formula("10 ** 2", {}) == 100.0
    assert eval_probability_formula("10 % 3", {}) == 1.0
    assert eval_probability_formula("10 // 3", {}) == 3.0


def test_safe_unary_operations():
    """Test that unary operations work."""
    assert eval_probability_formula("-5", {}) == -5.0
    assert eval_probability_formula("+5", {}) == 5.0
    assert eval_probability_formula("-(10 + 5)", {}) == -15.0


def test_safe_comparisons():
    """Test that comparison operations work."""
    evaluator = SafeExpressionEvaluator({})
    assert evaluator.eval("10 > 5") is True
    assert evaluator.eval("10 < 5") is False
    assert evaluator.eval("10 >= 10") is True
    assert evaluator.eval("10 <= 10") is True
    assert evaluator.eval("10 == 10") is True
    assert evaluator.eval("10 != 5") is True


def test_safe_boolean_operations():
    """Test that boolean operations work."""
    evaluator = SafeExpressionEvaluator({"x": 10, "y": 5})
    assert evaluator.eval("x > 5 and y < 10") is True
    assert evaluator.eval("x > 15 or y < 10") is True
    assert evaluator.eval("x > 5 and y > 10") is False


def test_safe_functions():
    """Test that min/max functions work."""
    assert eval_probability_formula("min(10, 5)", {}) == 5.0
    assert eval_probability_formula("max(10, 5)", {}) == 10.0
    assert eval_probability_formula("min(1, 2, 3)", {}) == 1.0
    assert eval_probability_formula("max(1, 2, 3)", {}) == 3.0


def test_safe_variable_references():
    """Test that variable references from context work."""
    context = {"unemployment": 8.5, "ai_capability": 120}
    assert eval_probability_formula("unemployment", context) == 8.5
    assert eval_probability_formula("unemployment / 100", context) == 0.085
    assert eval_probability_formula("2 * unemployment / 100", context) == 0.17
    assert eval_probability_formula("min(unemployment, 50) / 100", context) == 0.085
    assert eval_probability_formula("min(ai_capability, 100) / 100", context) == 1.0


def test_safe_complex_expressions():
    """Test that complex valid expressions work."""
    context = {"unemployment": 10.0, "ai_capability": 80}

    # Nested arithmetic
    assert eval_probability_formula("(unemployment + 5) * 2", context) == 30.0

    # Multiple operations
    assert eval_probability_formula("unemployment / 100 + ai_capability / 1000", context) == 0.18

    # Nested functions
    assert eval_probability_formula("min(max(unemployment, 5), 15)", context) == 10.0


def test_rejects_imports():
    """Test that import statements are rejected."""
    with pytest.raises(ValueError, match="not allowed"):
        eval_probability_formula("__import__('os')", {})


def test_rejects_attribute_access():
    """Test that attribute access is rejected."""
    with pytest.raises(ValueError, match="unsupported operation"):
        eval_probability_formula("unemployment.__class__", {"unemployment": 10})


def test_rejects_subscripting():
    """Test that subscripting is rejected."""
    with pytest.raises(ValueError, match="unsupported operation"):
        eval_probability_formula("x[0]", {"x": [1, 2, 3]})


def test_rejects_list_comprehensions():
    """Test that list comprehensions are rejected."""
    with pytest.raises(ValueError, match="unsupported operation"):
        eval_probability_formula("[x for x in range(10)]", {})


def test_rejects_lambda():
    """Test that lambda functions are rejected."""
    with pytest.raises(ValueError, match="simple function calls|unsupported"):
        eval_probability_formula("(lambda x: x + 1)(5)", {})


def test_rejects_dangerous_builtins():
    """Test that dangerous built-in functions are rejected."""
    # eval
    with pytest.raises((ValueError, NameError)):
        eval_probability_formula("eval('1 + 1')", {})

    # exec
    with pytest.raises((ValueError, NameError)):
        eval_probability_formula("exec('print(1)')", {})

    # open
    with pytest.raises((ValueError, NameError)):
        eval_probability_formula("open('/etc/passwd')", {})

    # __import__
    with pytest.raises(ValueError, match="not allowed"):
        eval_probability_formula("__import__('os')", {})


def test_rejects_assignments():
    """Test that assignments are rejected."""
    with pytest.raises(SyntaxError, match="Invalid syntax"):
        eval_probability_formula("x = 10", {})


def test_rejects_undefined_variables():
    """Test that undefined variables raise NameError."""
    with pytest.raises(NameError, match="not defined"):
        eval_probability_formula("undefined_var / 100", {"unemployment": 10})


def test_rejects_disallowed_functions():
    """Test that functions other than min/max are rejected."""
    with pytest.raises(ValueError, match="not allowed"):
        eval_probability_formula("abs(-5)", {})

    with pytest.raises(ValueError, match="not allowed"):
        eval_probability_formula("sum([1, 2, 3])", {})

    with pytest.raises(ValueError, match="not allowed"):
        eval_probability_formula("len([1, 2, 3])", {})


def test_syntax_errors():
    """Test that syntax errors are properly reported."""
    with pytest.raises(SyntaxError, match="Invalid syntax"):
        eval_probability_formula("unemployment / / 100", {"unemployment": 10})

    with pytest.raises(SyntaxError, match="Invalid syntax"):
        eval_probability_formula("10 +", {})


def test_prevents_infinite_loops():
    """Test that expressions that could cause infinite loops are rejected.

    Note: Since we only allow arithmetic and functions, infinite loops
    aren't possible with our restricted AST. But this test documents
    that while loops are rejected.
    """
    with pytest.raises(SyntaxError, match="Invalid syntax"):
        eval_probability_formula("while True: pass", {})


def test_prevents_dos_via_computation():
    """Test that computationally expensive operations complete.

    Note: With our restrictions, the only way to create expensive
    computations is through large exponents. Python handles this fine.
    """
    # This should complete without hanging
    result = eval_probability_formula("2 ** 100", {})
    assert result == 2 ** 100


def test_prevents_resource_exhaustion():
    """Test that we can't exhaust resources through expression complexity.

    Note: Python's AST parser itself has recursion limits that prevent
    stack exhaustion from deeply nested expressions.
    """
    # Deeply nested expression should still work
    nested = "(" * 50 + "5" + ")" * 50
    assert eval_probability_formula(nested, {}) == 5.0


def test_real_world_formulas():
    """Test real-world probability formulas from scenarios."""
    context = {
        "unemployment": 8.5,
        "ai_capability": 120,
        "public_sentiment": 60,
        "ai_adoption_sweden": 45
    }

    # Simple percentage
    result = eval_probability_formula("unemployment / 100", context)
    assert result == 0.085

    # Scaled formula
    result = eval_probability_formula("2 * unemployment / 100", context)
    assert result == 0.17

    # Clamped formula
    result = eval_probability_formula("min(unemployment, 50) / 100", context)
    assert result == 0.085

    # Combined metrics
    result = eval_probability_formula("(unemployment + ai_adoption_sweden) / 200", context)
    assert result == 0.2675
