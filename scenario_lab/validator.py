"""Scenario validator."""

from pathlib import Path
from typing import List, Set, Any, Tuple
import re
import ast
import operator
from datetime import datetime
from .models import Scenario
from .loader import load_scenario
from .model_audit import collect_model_hygiene_warnings


class ValidationResult:
    def __init__(self, errors: List[str] = None, warnings: List[str] = None):
        self.errors = errors or []
        self.warnings = warnings or []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


# Helper functions

def extract_metric_references(text: str) -> Set[str]:
    """Extract metric ID references from text.

    Looks for patterns like:
    - metric_name
    - Common metric naming patterns (lowercase with underscores)
    """
    # Match words that look like metric IDs (lowercase_with_underscores)
    # This is a heuristic - we'll check against actual metric IDs
    pattern = r'\b([a-z][a-z0-9_]*)\b'
    potential_refs = set(re.findall(pattern, text))
    return potential_refs


def is_static_probability(prob_str: str) -> bool:
    """Check if probability is static (e.g., '10 procent per runda')."""
    # Check for common static patterns
    static_patterns = [
        r'\d+\s*%',  # "10%"
        r'\d+\s*procent',  # "10 procent"
        r'\d+\s*percent',  # "10 percent"
        r'0\.\d+',  # "0.1"
    ]

    for pattern in static_patterns:
        if re.search(pattern, prob_str.lower()):
            return True
    return False


def parse_static_probability(prob_str: str) -> float:
    """Parse static probability string to float [0, 1]."""
    # Extract number
    match = re.search(r'(\d+(?:\.\d+)?)', prob_str)
    if not match:
        return 0.0

    value = float(match.group(1))

    # If it looks like a percentage, convert to [0, 1]
    if '%' in prob_str or 'procent' in prob_str.lower() or 'percent' in prob_str.lower():
        value = value / 100.0

    # If already decimal, use as-is
    if 0 <= value <= 1:
        return value

    # If > 1, assume percentage
    if value > 1:
        return value / 100.0

    return value


class SafeExpressionEvaluator(ast.NodeVisitor):
    """AST-based safe expression evaluator for probability formulas.

    Allows only:
    - Arithmetic operators: +, -, *, /, //, %, **
    - Comparison operators: <, <=, >, >=, ==, !=
    - Boolean operators: and, or, not
    - Functions: min(), max()
    - Literals: numbers
    - Variables: metric names from context

    Rejects:
    - Imports, attribute access, subscripting
    - Assignments, control flow
    - Function definitions
    - Any other potentially dangerous operations
    """

    # Allowed operators
    ALLOWED_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    ALLOWED_COMPARISONS = {
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
    }

    ALLOWED_BOOL_OPS = {
        ast.And: lambda x, y: x and y,
        ast.Or: lambda x, y: x or y,
    }

    ALLOWED_FUNCTIONS = {
        'min': min,
        'max': max,
    }

    def __init__(self, context: dict):
        """Initialize evaluator with variable context.

        Args:
            context: Dict mapping variable names to values
        """
        self.context = context

    def eval(self, expression: str) -> Any:
        """Evaluate an expression safely.

        Args:
            expression: String expression to evaluate

        Returns:
            Result of evaluation

        Raises:
            ValueError: If expression contains unsafe operations
            SyntaxError: If expression has invalid syntax
        """
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            raise SyntaxError(f"Invalid syntax in expression: {e}")

        return self.visit(tree.body)

    def visit_BinOp(self, node):
        """Handle binary operations (+, -, *, /, etc.)."""
        op_type = type(node.op)
        if op_type not in self.ALLOWED_OPS:
            raise ValueError(f"Operation {op_type.__name__} not allowed")

        left = self.visit(node.left)
        right = self.visit(node.right)
        op_func = self.ALLOWED_OPS[op_type]

        return op_func(left, right)

    def visit_UnaryOp(self, node):
        """Handle unary operations (-, +)."""
        op_type = type(node.op)
        if op_type not in self.ALLOWED_OPS:
            raise ValueError(f"Unary operation {op_type.__name__} not allowed")

        operand = self.visit(node.operand)
        op_func = self.ALLOWED_OPS[op_type]

        return op_func(operand)

    def visit_Compare(self, node):
        """Handle comparison operations (<, >, ==, etc.)."""
        left = self.visit(node.left)

        for op, comparator in zip(node.ops, node.comparators):
            op_type = type(op)
            if op_type not in self.ALLOWED_COMPARISONS:
                raise ValueError(f"Comparison {op_type.__name__} not allowed")

            right = self.visit(comparator)
            op_func = self.ALLOWED_COMPARISONS[op_type]

            if not op_func(left, right):
                return False
            left = right

        return True

    def visit_BoolOp(self, node):
        """Handle boolean operations (and, or)."""
        op_type = type(node.op)
        if op_type not in self.ALLOWED_BOOL_OPS:
            raise ValueError(f"Boolean operation {op_type.__name__} not allowed")

        op_func = self.ALLOWED_BOOL_OPS[op_type]
        values = [self.visit(value) for value in node.values]

        result = values[0]
        for value in values[1:]:
            result = op_func(result, value)

        return result

    def visit_Call(self, node):
        """Handle function calls (min, max only)."""
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are allowed")

        func_name = node.func.id
        if func_name not in self.ALLOWED_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' not allowed")

        # Evaluate arguments
        args = [self.visit(arg) for arg in node.args]

        # Call the function
        func = self.ALLOWED_FUNCTIONS[func_name]
        return func(*args)

    def visit_Name(self, node):
        """Handle variable names (metric IDs from context)."""
        var_name = node.id
        if var_name not in self.context:
            raise NameError(f"Variable '{var_name}' not defined in context")

        return self.context[var_name]

    def visit_Constant(self, node):
        """Handle numeric constants."""
        return node.value

    # Python 3.7 compatibility - ast.Num is deprecated in 3.8+
    def visit_Num(self, node):
        """Handle numeric constants (Python 3.7 compatibility)."""
        return node.n

    def generic_visit(self, node):
        """Reject any node types not explicitly handled."""
        raise ValueError(
            f"Expression contains unsupported operation: {type(node).__name__}. "
            f"Only arithmetic, comparisons, min/max functions, and variable references are allowed."
        )


def eval_probability_formula(formula: str, context: dict) -> float:
    """Safely evaluate a probability formula using AST parsing.

    Args:
        formula: Mathematical expression (may reference metrics)
        context: Dict of metric_id -> value

    Returns:
        Evaluated result as float

    Raises:
        ValueError: If formula contains unsafe operations
        SyntaxError: If formula has invalid syntax
        NameError: If formula references undefined variables

    Examples:
        >>> eval_probability_formula("10 + 5", {})
        15.0
        >>> eval_probability_formula("unemployment / 100", {"unemployment": 8.5})
        0.085
        >>> eval_probability_formula("min(unemployment, 50) / 100", {"unemployment": 60})
        0.5
    """
    evaluator = SafeExpressionEvaluator(context)
    result = evaluator.eval(formula)
    return float(result)


def eval_boolean_expression(expression: str, context: dict) -> bool:
    """Evaluate a boolean expression over metric values, safely.

    Uses the same AST-based evaluator as probability formulas, so termination
    conditions cannot execute code any more than a probability formula can.

    Args:
        expression: Expression such as "snap_election_risk >= 100"
        context: Mapping of metric id to current value

    Returns:
        The expression's truth value

    Raises:
        ValueError: If the expression is unsafe or malformed
        NameError: If it references a variable that is not a known metric
    """
    evaluator = SafeExpressionEvaluator(context)
    return bool(evaluator.eval(expression))


def is_valid_model_route(value: object) -> bool:
    """Check a configured model entry, which is a ModelRoute after loading.

    Config values are parsed into ``ModelRoute(provider, model)`` before
    validation runs, so checking them as raw strings does not work. Doing so
    had two silent consequences: single-model entries matched neither the
    ``str`` nor the ``list`` branch and were never checked at all, while every
    fallback list failed with "invalid model in fallback list" regardless of
    what it contained.

    The ``vendor/model`` shape is an OpenRouter convention, not a universal
    one: Anthropic model ids such as ``claude-sonnet-4-6`` carry no slash, so
    the check is applied per provider rather than to every route.
    """
    from .models import ModelRoute

    if isinstance(value, ModelRoute):
        if not value.provider or not value.model:
            return False
        if value.provider == "openrouter":
            return is_valid_model_string(value.model)
        return True
    if isinstance(value, str):
        # A literal that has not been through the loader.
        provider, sep, remainder = value.partition(":")
        if sep:
            if provider == "openrouter":
                return is_valid_model_string(remainder)
            return bool(provider and remainder)
        return is_valid_model_string(value)
    return False


def is_valid_model_string(model: str) -> bool:
    """Check if a bare model name follows the expected ``vendor/name`` format.

    Examples: google/gemini-3-flash-preview, qwen/qwen3-235b-a22b-2507
    """
    if not isinstance(model, str):
        return False

    # Must contain a slash
    if '/' not in model:
        return False

    parts = model.split('/')
    if len(parts) != 2:
        return False

    provider, model_name = parts

    # Both parts should be non-empty
    if not provider or not model_name:
        return False

    return True


# Validation functions

def validate_metric_references(scenario: Scenario) -> List[str]:
    """Check that all metric references are valid.

    Checks:
    - Actor descriptions reference valid metrics
    - Event conditions reference valid metrics
    - Event probabilities reference valid metrics
    - Metric rules reference valid metrics

    Returns:
        List of validation errors
    """
    errors = []
    valid_metric_ids = set(scenario.metrics.metrics.keys())

    # Check actor descriptions
    # Prose in rules and actor files may legitimately name an event as well as a
    # metric -- "once snap_election_date_announced has fired" is exactly the kind
    # of rule the events system exists to support. Check against both, or such a
    # rule cannot be written using the event's own id.
    valid_identifiers = set(valid_metric_ids) | {event.id for event in scenario.events}

    for actor_id, actor in scenario.actors.items():
        text = f"{actor.short_description} {actor.long_description}"
        referenced_metrics = extract_metric_references(text)

        # Only flag if the reference looks like a metric ID AND exists in our metrics
        for metric in referenced_metrics:
            # Skip common English words that aren't metrics
            if metric in ['the', 'a', 'an', 'and', 'or', 'to', 'of', 'in', 'for', 'on', 'with', 'as', 'by', 'at', 'from', 'is', 'are', 'be', 'has', 'have', 'will', 'can', 'may']:
                continue
            # Only check metrics that could plausibly be metric IDs (contain underscore or match a known metric pattern)
            if '_' in metric or metric in valid_identifiers:
                if metric not in valid_identifiers:
                    errors.append(
                        f"Actor '{actor_id}' may reference unknown metric or event '{metric}'"
                    )

    # Check events
    for event in scenario.events:
        # Check conditions - look for metric-like patterns
        referenced_metrics = extract_metric_references(event.condition)
        for metric in referenced_metrics:
            if '_' in metric and metric not in valid_metric_ids:
                errors.append(f"Event '{event.id}' condition references unknown metric '{metric}'")

        # Check probability formulas - only if it looks like a formula (not natural language or static)
        if not is_static_probability(event.probability) and is_formula_probability(event.probability, valid_metric_ids):
            referenced_metrics = extract_metric_references(event.probability)
            for metric in referenced_metrics:
                # Skip mathematical keywords
                if metric in ['min', 'max', 'abs']:
                    continue
                if metric not in valid_metric_ids:
                    errors.append(f"Event '{event.id}' probability references unknown metric '{metric}'")

    # Check metric rules for cross-references
    if scenario.metric_rules:
        referenced_metrics = extract_metric_references(scenario.metric_rules)
        for metric in referenced_metrics:
            if '_' in metric and metric not in valid_identifiers:
                errors.append(
                    f"Metric rules reference unknown metric or event '{metric}'"
                )

    return errors


def is_formula_probability(prob_str: str, valid_metrics: Set[str]) -> bool:
    """Check if probability string looks like a mathematical formula.

    A formula is:
    - Contains only metric IDs, numbers, and operators
    - No complex natural language

    Examples of formulas:
    - "unemployment / 100"
    - "2 * unemployment / 100"
    - "min(unemployment, 50) / 100"

    Examples of natural language (not formulas):
    - "Double the value of unemployment, in percent"
    - "15 percent rounds 1-2, 10 percent rounds 3-4"
    """
    # If it contains words like "the", "of", "value", "round", it's natural language
    natural_language_words = ['the', 'of', 'value', 'round', 'double', 'triple', 'half', 'twice']
    for word in natural_language_words:
        if re.search(rf'\b{word}\b', prob_str.lower()):
            return False

    # If it contains metric IDs and math operators, it's likely a formula
    # Extract all word-like tokens
    tokens = re.findall(r'\b[a-z_][a-z0-9_]*\b', prob_str.lower())

    # Check if all tokens are either metrics or math functions
    math_functions = {'min', 'max', 'abs'}
    for token in tokens:
        if token not in valid_metrics and token not in math_functions:
            # Unknown token - probably natural language
            return False

    # If we got here, it looks like a formula
    return True


def validate_event_probabilities(scenario: Scenario) -> Tuple[List[str], List[str]]:
    """Validate that probability formulas are evaluable.

    Checks:
    - Static probabilities are in valid format
    - Formulas are valid Python expressions
    - Natural language descriptions are accepted (LLM will interpret)

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []
    valid_metric_ids = set(scenario.metrics.metrics.keys())

    for event in scenario.events:
        prob = event.probability

        # Check if it's a static probability (e.g., "10 percent", "5%", "0.1")
        if is_static_probability(prob):
            try:
                value = parse_static_probability(prob)
                if not 0 <= value <= 1:
                    errors.append(f"Event '{event.id}' static probability {value} outside valid range [0, 1]")
                elif value < 0.001:
                    warnings.append(f"Event '{event.id}' has very low probability ({value:.1%})")
            except Exception as e:
                # If it fails to parse but has "percent" in it, it might be natural language
                if 'percent' in prob.lower() or '%' in prob:
                    # Skip - LLM will interpret
                    continue
                errors.append(f"Event '{event.id}' has unparseable probability: {e}")
            continue

        # Check if it looks like a formula (vs. natural language)
        if not is_formula_probability(prob, valid_metric_ids):
            # Natural language - LLM will interpret, skip validation
            continue

        # It's a formula - validate it
        try:
            # Create test context with sample metric values (50 for all)
            test_context = {m_id: 50.0 for m_id in valid_metric_ids}

            # Try to evaluate
            result = eval_probability_formula(prob, test_context)

            # Check result is valid
            if not isinstance(result, (int, float)):
                errors.append(f"Event '{event.id}' probability formula doesn't return a number")
            elif result < 0:
                errors.append(f"Event '{event.id}' probability formula returns negative value: {result}")
            elif result > 1:
                # Could be percentage - warn but don't error
                warnings.append(f"Event '{event.id}' probability formula returns value > 1: {result} (remember to use 0-1 range, not 0-100)")

        except NameError as e:
            # Likely undefined metric reference
            errors.append(f"Event '{event.id}' probability formula references undefined metric: {e}")
        except SyntaxError as e:
            errors.append(f"Event '{event.id}' has invalid probability formula syntax: {e}")
        except Exception as e:
            errors.append(f"Event '{event.id}' probability formula error: {e}")

    return errors, warnings


def validate_llm_config(scenario: Scenario) -> List[str]:
    """Validate LLM configuration.

    Checks:
    - Model strings follow OpenRouter format
    - Temperature is in valid range [0, 2]
    - Max tokens is reasonable (> 100, < 100000)

    Returns:
        List of validation errors and warnings
    """
    errors = []
    config = scenario.config.llm

    # Validate temperature
    if not 0 <= config.temperature <= 2:
        errors.append(f"Temperature {config.temperature} outside valid range [0, 2]")

    # Validate max_tokens
    if config.max_tokens < 100:
        errors.append(f"max_tokens {config.max_tokens} is too low (minimum 100)")
    elif config.max_tokens > 100000:
        errors.append(f"max_tokens {config.max_tokens} is unusually high (maximum 100000)")

    # Validate probability sampling
    if not isinstance(config.probability_samples, int) or config.probability_samples < 1:
        errors.append(
            f"probability_samples {config.probability_samples!r} must be an integer >= 1"
        )
    elif config.probability_samples > 10:
        errors.append(
            f"probability_samples {config.probability_samples} is unusually high (maximum 10); "
            "each sample repeats the full events call"
        )

    # Validate the per-call wall-clock deadline
    timeout = getattr(config, "call_timeout_seconds", 300)
    if not isinstance(timeout, int) or timeout < 10:
        errors.append(
            f"llm.call_timeout_seconds {timeout!r} must be an integer >= 10 seconds"
        )
    elif timeout > 3600:
        errors.append(
            f"llm.call_timeout_seconds {timeout} is unusually high (maximum 3600); "
            f"a single call blocking for an hour will stall a whole batch"
        )

    # Validate emergent events policy
    emergent = scenario.config.emergent_events
    if not isinstance(emergent.max_per_turn, int) or emergent.max_per_turn < 1:
        errors.append(
            f"emergent_events.max_per_turn {emergent.max_per_turn!r} must be an integer >= 1"
        )
    elif emergent.max_per_turn > 5:
        errors.append(
            f"emergent_events.max_per_turn {emergent.max_per_turn} is unusually high (maximum 5)"
        )
    if not isinstance(emergent.max_probability, (int, float)) or not 0 < emergent.max_probability <= 1:
        errors.append(
            f"emergent_events.max_probability {emergent.max_probability!r} must be in (0, 1]"
        )

    # Validate per-task max_tokens overrides
    valid_tasks = {"events", "actors", "rules", "metrics", "summary", "analysis", "synthesis", "referee"}
    for task, value in config.max_tokens_by_task.items():
        if task not in valid_tasks:
            errors.append(f"max_tokens_by_task has invalid task '{task}'")
            continue
        if not isinstance(value, int):
            errors.append(f"max_tokens_by_task['{task}'] must be an integer, got {type(value).__name__}")
            continue
        if value < 100:
            errors.append(f"max_tokens_by_task['{task}']={value} is too low (minimum 100)")
        elif value > 100000:
            errors.append(f"max_tokens_by_task['{task}']={value} is unusually high (maximum 100000)")

    # Validate model strings for each task
    task_fields = ["events", "rules", "metrics", "summary", "analysis", "referee"]

    for task in task_fields:
        model_value = getattr(config, task)

        if isinstance(model_value, list):
            for m in model_value:
                if not is_valid_model_route(m):
                    errors.append(f"Task '{task}' has invalid model in fallback list: '{m}'")
        elif not is_valid_model_route(model_value):
            errors.append(f"Task '{task}' has invalid model string: '{model_value}'")

    # Validate actors field (can be a route, a fallback list, or a per-actor dict)
    if isinstance(config.actors, list):
        for m in config.actors:
            if not is_valid_model_route(m):
                errors.append(f"Actors model has invalid model in fallback list: '{m}'")
    elif isinstance(config.actors, dict):
        for actor_id, model_value in config.actors.items():
            if isinstance(model_value, list):
                for m in model_value:
                    if not is_valid_model_route(m):
                        errors.append(f"Actor '{actor_id}' has invalid model in fallback list: '{m}'")

    return errors


def validate_prompt_overrides(scenario: Scenario) -> Tuple[List[str], List[str]]:
    """Validate scenario prompt overrides against the render context they get.

    Prompt overrides are Jinja templates, and Jinja renders an undefined
    variable as an empty string rather than raising. A typo, or a variable the
    prompt type does not receive, therefore produces a silently degraded prompt
    that still looks fine in the file. This check surfaces those before a run.

    Returns:
        (errors, warnings) – syntax problems are errors, unknown variables are
        warnings, since a template may legitimately define its own via ``set``.
    """
    from jinja2 import TemplateSyntaxError, meta
    from jinja2.sandbox import SandboxedEnvironment

    from .prompts import PromptBuilder

    errors: List[str] = []
    warnings: List[str] = []

    if not scenario.custom_system_prompts and not scenario.custom_user_prompts:
        return errors, warnings

    env = SandboxedEnvironment()
    builder = PromptBuilder(scenario)

    # The union of names any actor could see, so an actor-branching prompt
    # validates against the same vocabulary the renderer will supply.
    known: Set[str] = set(builder._get_system_prompt_context(None))
    for actor_id in scenario.actors:
        known |= set(builder._get_system_prompt_context(actor_id))

    for name, source in sorted(scenario.custom_system_prompts.items()):
        try:
            parsed = env.parse(source)
        except TemplateSyntaxError as exc:
            errors.append(f"system-prompts/{name}.md has invalid Jinja syntax: {exc}")
            continue

        unknown = sorted(meta.find_undeclared_variables(parsed) - known)
        if unknown:
            warnings.append(
                f"system-prompts/{name}.md references undefined variable(s) "
                f"{', '.join(unknown)}; Jinja renders these as empty text"
            )

    for name, source in sorted(scenario.custom_user_prompts.items()):
        try:
            env.parse(source)
        except TemplateSyntaxError as exc:
            errors.append(f"user-prompts/{name}.md has invalid Jinja syntax: {exc}")

    return errors, warnings


def validate_termination(scenario: Scenario) -> Tuple[List[str], List[str]]:
    """Validate termination conditions against the metrics they reference.

    A condition that cannot be evaluated is worse than none: it fires a warning
    every turn and the run silently plays out to max_turns anyway. Catching it
    here costs nothing; catching it after a paid batch costs the batch.

    Returns:
        (errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []

    conditions = scenario.config.termination
    if not conditions:
        return errors, warnings

    seen: set = set()
    context = {m.id: m.value for m in scenario.metrics.metrics.values()}

    for condition in conditions:
        if condition.id in seen:
            errors.append(f"termination: duplicate condition id '{condition.id}'")
        seen.add(condition.id)

        try:
            eval_boolean_expression(condition.when, context)
        except Exception as exc:
            errors.append(
                f"termination['{condition.id}']: cannot evaluate \"{condition.when}\" – {exc}. "
                f"Available metrics: {', '.join(sorted(context))}"
            )
            continue

        # A condition already true at the start values would end every run at
        # turn 1, which is almost always a mistake rather than an intention.
        try:
            if eval_boolean_expression(condition.when, context):
                warnings.append(
                    f"termination['{condition.id}'] is already true at the scenario's "
                    f"starting metric values, so every run would end at turn 1"
                )
        except Exception:
            pass

    return errors, warnings


def validate_research_questions(scenario: Scenario) -> Tuple[List[str], List[str]]:
    """Validate declared research questions against what the scenario measures.

    The point of this check is to catch a question the scenario cannot answer
    before runs are spent on it: a question hinging on a metric that does not
    exist, or on an event that was never defined, will produce a confident but
    ungrounded answer during synthesis.

    Returns:
        (errors, warnings)
    """
    errors: List[str] = []
    warnings: List[str] = []

    questions = scenario.config.research_questions
    if not questions:
        return errors, warnings

    valid_metrics = set(scenario.metrics.metrics.keys())
    valid_events = {event.id for event in scenario.events if event.id}

    seen_ids: Set[str] = set()
    for rq in questions:
        if not rq.id:
            errors.append("Research question found without an id")
            continue
        if rq.id in seen_ids:
            errors.append(f"Duplicate research question id: '{rq.id}'")
        seen_ids.add(rq.id)

        if not rq.question.strip():
            errors.append(f"Research question '{rq.id}' has no question text")

        for metric_id in rq.metrics:
            if metric_id not in valid_metrics:
                errors.append(
                    f"Research question '{rq.id}' references unknown metric "
                    f"'{metric_id}' (defined metrics: {', '.join(sorted(valid_metrics)) or 'none'})"
                )

        for event_id in rq.events:
            if event_id not in valid_events:
                errors.append(
                    f"Research question '{rq.id}' references unknown event '{event_id}'"
                )

        if not rq.metrics and not rq.events:
            warnings.append(
                f"Research question '{rq.id}' names no metrics or events; "
                f"synthesis can only answer it qualitatively"
            )

    return errors, warnings


def validate_actor_references(scenario: Scenario) -> List[str]:
    """Validate that scenario.yaml actors match actor files.

    Checks:
    - All actors in config have corresponding files
    - No orphaned actor files (already in base validator)

    Returns:
        List of validation errors
    """
    errors = []

    # Check all configured actors have definitions
    for actor_id in scenario.config.actor_ids:
        if actor_id not in scenario.actors:
            errors.append(f"Actor '{actor_id}' defined in config but missing description file")

    return errors


def validate_time_config(scenario: Scenario) -> List[str]:
    """Validate start_date and time_scale.

    Checks:
    - start_date is in valid format (YYYY-MM-DD, YYYY-MM, or YYYY)
    - time_scale includes a supported unit (days/weeks/months/years)
    - max_turns doesn't exceed reasonable limits

    Returns:
        List of validation errors
    """
    errors = []

    # Validate start_date format
    start_date = scenario.config.start_date
    if start_date:
        # Accept YYYY-MM-DD, YYYY-MM, or YYYY formats
        if not re.match(r'^\d{4}(-\d{2}){0,2}$', start_date):
            errors.append(
                f"start_date '{start_date}' has invalid format "
                f"(expected YYYY-MM-DD, YYYY-MM, or YYYY)"
            )
        else:
            parts = start_date.split("-")
            try:
                if len(parts) == 1:
                    datetime.strptime(start_date, '%Y')
                elif len(parts) == 2:
                    datetime.strptime(start_date, '%Y-%m')
                else:
                    datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                errors.append(f"start_date '{start_date}' is not a valid date")

    time_scale = (scenario.config.time_scale or "").lower()
    if not re.search(r'\b\d+\s*(day|days|week|weeks|month|months|year|years)\b', time_scale):
        errors.append(
            f"time_scale '{scenario.config.time_scale}' is not parseable "
            f"(expected forms like '2 weeks per turn' or '6 months')"
        )

    # Validate max_turns
    if scenario.config.max_turns < 1:
        errors.append(f"max_turns must be at least 1, got {scenario.config.max_turns}")
    elif scenario.config.max_turns > 100:
        errors.append(f"max_turns {scenario.config.max_turns} exceeds reasonable limit (100)")

    return errors


def validate_scenario(scenario_path: Path) -> ValidationResult:
    """Run all validation checks on a scenario.

    Performs comprehensive validation including:
    - Structural validation (config, actors, metrics, events)
    - Metric reference validation
    - Event probability validation
    - LLM configuration validation
    - Actor reference validation
    - Time configuration validation
    """
    errors = []
    warnings = []

    try:
        scenario = load_scenario(scenario_path)
    except Exception as e:
        return ValidationResult(errors=[f"Failed to load scenario: {str(e)}"])

    # 1. Basic Config Validation
    if not scenario.config.name:
        errors.append("Scenario name is missing")
    if not scenario.config.actor_ids:
        errors.append("No actors defined in config")

    # 2. Basic Actor Validation
    for actor_id in scenario.config.actor_ids:
        if actor_id not in scenario.actors:
            errors.append(f"Actor '{actor_id}' defined in config but missing description file")
        else:
            actor = scenario.actors[actor_id]
            if not actor.name:
                warnings.append(f"Actor '{actor_id}' has no display name")
            if not actor.short_description:
                warnings.append(f"Actor '{actor_id}' has no short description")
            if not actor.initial_goals:
                warnings.append(
                    f"Actor '{actor_id}' has no initial goals "
                    f"(consider adding '### Initial goals' under '## Long description')"
                )
            if not actor.behavioral_traits:
                warnings.append(
                    f"Actor '{actor_id}' has no behavioral traits "
                    f"(consider adding '### Behavioral traits' under '## Long description')"
                )

    # 3. Basic Metrics Validation
    if not scenario.metrics.metrics:
        warnings.append("No metrics defined")

    for m_id, metric in scenario.metrics.metrics.items():
        if metric.min_value >= metric.max_value:
            errors.append(f"Metric '{m_id}': min value must be less than max value")
        if not (metric.min_value <= metric.value <= metric.max_value):
            errors.append(f"Metric '{m_id}': start value {metric.value} outside range [{metric.min_value}, {metric.max_value}]")

    # 4. Basic Events Validation
    if not scenario.events:
        warnings.append("No events defined")

    for event in scenario.events:
        if not event.id:
            errors.append("Event found without ID")
        if not event.condition:
            warnings.append(f"Event '{event.id}' has no condition")

    # 5. Basic Content Validation
    if not scenario.context.strip():
        warnings.append("Context description is empty")

    if not scenario.metric_rules.strip():
        warnings.append("Metric rules are empty")

    # 6. Comprehensive Validation (New)
    errors.extend(validate_metric_references(scenario))
    event_probability_errors, event_probability_warnings = validate_event_probabilities(scenario)
    errors.extend(event_probability_errors)
    warnings.extend(event_probability_warnings)
    errors.extend(validate_llm_config(scenario))
    warnings.extend(collect_model_hygiene_warnings(scenario.config.llm, scope=scenario_path.name))
    errors.extend(validate_actor_references(scenario))
    errors.extend(validate_time_config(scenario))
    rq_errors, rq_warnings = validate_research_questions(scenario)
    errors.extend(rq_errors)
    warnings.extend(rq_warnings)
    term_errors, term_warnings = validate_termination(scenario)
    errors.extend(term_errors)
    warnings.extend(term_warnings)
    prompt_errors, prompt_warnings = validate_prompt_overrides(scenario)
    errors.extend(prompt_errors)
    warnings.extend(prompt_warnings)

    return ValidationResult(errors, warnings)
