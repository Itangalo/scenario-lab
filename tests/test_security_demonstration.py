"""Security demonstration tests - shows what attacks are now prevented.

This file demonstrates the security improvements from replacing eval() with
the safe AST-based expression evaluator.
"""

import pytest
from scenario_lab.validator import eval_probability_formula


def test_prevents_file_access():
    """Prevent reading files from disk."""
    malicious_formulas = [
        "open('/etc/passwd').read()",
        "open('secret.txt', 'r').read()",
        "__import__('pathlib').Path('/etc/passwd').read_text()",
    ]

    for formula in malicious_formulas:
        with pytest.raises((ValueError, NameError, SyntaxError)):
            eval_probability_formula(formula, {})


def test_prevents_code_execution():
    """Prevent arbitrary code execution."""
    malicious_formulas = [
        "exec('import os; os.system(\"rm -rf /\")')",
        "eval('__import__(\"os\").system(\"ls\")')",
        "__import__('subprocess').run(['ls'])",
    ]

    for formula in malicious_formulas:
        with pytest.raises((ValueError, NameError, SyntaxError)):
            eval_probability_formula(formula, {})


def test_prevents_network_access():
    """Prevent network requests."""
    malicious_formulas = [
        "__import__('urllib').request.urlopen('http://evil.com')",
        "__import__('requests').get('http://evil.com')",
        "__import__('socket').socket().connect(('evil.com', 80))",
    ]

    for formula in malicious_formulas:
        with pytest.raises((ValueError, NameError, SyntaxError)):
            eval_probability_formula(formula, {})


def test_prevents_module_imports():
    """Prevent importing any modules."""
    malicious_formulas = [
        "__import__('os')",
        "__import__('sys')",
        "__import__('subprocess')",
        "import os",  # SyntaxError in eval mode
    ]

    for formula in malicious_formulas:
        with pytest.raises((ValueError, NameError, SyntaxError)):
            eval_probability_formula(formula, {})


def test_prevents_attribute_access_attacks():
    """Prevent accessing object attributes for privilege escalation."""
    malicious_formulas = [
        "(1).__class__.__bases__[0].__subclasses__()",
        "[].__class__.__mro__",
        "unemployment.__class__",
    ]

    for formula in malicious_formulas:
        with pytest.raises((ValueError, SyntaxError)):
            eval_probability_formula(formula, {"unemployment": 10})


def test_prevents_environment_access():
    """Prevent access to environment variables and system info."""
    malicious_formulas = [
        "__import__('os').environ['SECRET_KEY']",
        "__import__('os').getenv('AWS_SECRET_KEY')",
    ]

    for formula in malicious_formulas:
        with pytest.raises((ValueError, NameError)):
            eval_probability_formula(formula, {})


def test_safe_formulas_still_work():
    """Ensure legitimate formulas continue to work correctly."""
    context = {"unemployment": 10.0, "ai_capability": 80}

    # These should all work fine
    safe_formulas = [
        ("unemployment / 100", 0.1),
        ("2 * unemployment / 100", 0.2),
        ("min(unemployment, 50) / 100", 0.1),
        ("max(unemployment, 5) / 100", 0.1),
        ("(unemployment + ai_capability) / 200", 0.45),
        ("unemployment ** 2 / 10000", 0.01),
    ]

    for formula, expected in safe_formulas:
        result = eval_probability_formula(formula, context)
        assert abs(result - expected) < 0.001, f"Formula '{formula}' failed"


def test_comparison_of_old_vs_new_approach():
    """Document what the old eval() approach would have allowed vs. new approach.

    This is a documentation test showing the security improvement.
    """

    # OLD APPROACH (unsafe eval with restricted context):
    # Would still be vulnerable to:
    # 1. Attribute access attacks: (1).__class__.__bases__
    # 2. Infinite loops: while True: pass (though SyntaxError in eval mode)
    # 3. Resource exhaustion: 2**999999999 (would hang)
    # 4. Some __import__ tricks with string manipulation

    # NEW APPROACH (AST-based safe evaluator):
    # ✅ Prevents all attribute access
    # ✅ Only allows whitelisted operations
    # ✅ No way to import or execute code
    # ✅ Exponential operations complete safely (Python handles them)
    # ✅ Clear error messages for rejected operations

    # Demonstrate a formula that works with new approach but is actually safe
    context = {"unemployment": 10}
    result = eval_probability_formula("unemployment / 100", context)
    assert result == 0.1

    # Demonstrate formulas that are now properly rejected
    with pytest.raises(ValueError, match="not allowed|unsupported"):
        eval_probability_formula("().__class__", {})

    with pytest.raises(ValueError, match="unsupported operation"):
        eval_probability_formula("[x for x in [1,2,3]]", {})
