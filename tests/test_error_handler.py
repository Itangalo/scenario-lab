"""
Tests for error_handler.py - Enhanced error handling with user-friendly messages
"""
import pytest
import sys
from io import StringIO
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from error_handler import (
    ErrorHandler,
    ErrorContext,
    ErrorCategory,
    ErrorSeverity,
    RecoveryAction,
    classify_error
)


class TestErrorContext:
    """Test ErrorContext creation and serialization"""

    def test_error_context_creation(self):
        """Test creating an ErrorContext"""
        error = ValueError("Test error")
        context = ErrorContext(
            error=error,
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH,
            operation="Testing API call",
            scenario_name="test-scenario",
            turn_number=5,
            cost_so_far=1.234
        )

        assert context.error == error
        assert context.category == ErrorCategory.API
        assert context.severity == ErrorSeverity.HIGH
        assert context.operation == "Testing API call"
        assert context.scenario_name == "test-scenario"
        assert context.turn_number == 5
        assert context.cost_so_far == 1.234

    def test_error_context_to_dict(self):
        """Test converting ErrorContext to dict"""
        error = ValueError("Test error")
        context = ErrorContext(
            error=error,
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.MEDIUM,
            operation="Reading file",
            file_path="/path/to/file.yaml"
        )

        context_dict = context.to_dict()

        assert context_dict['error_type'] == 'ValueError'
        assert context_dict['error_message'] == 'Test error'
        assert context_dict['category'] == 'file'
        assert context_dict['severity'] == 'medium'
        assert context_dict['operation'] == 'Reading file'
        assert context_dict['file_path'] == '/path/to/file.yaml'


class TestClassifyError:
    """Test error classification"""

    def test_classify_file_not_found(self):
        """Test classifying FileNotFoundError"""
        error = FileNotFoundError("File not found")
        context = classify_error(error, operation="Loading config")

        assert context.category == ErrorCategory.FILE
        assert context.severity == ErrorSeverity.HIGH
        assert context.operation == "Loading config"

    def test_classify_permission_error(self):
        """Test classifying PermissionError"""
        error = PermissionError("Permission denied")
        context = classify_error(error, operation="Writing file")

        assert context.category == ErrorCategory.FILE
        assert context.severity == ErrorSeverity.HIGH

    def test_classify_yaml_error(self):
        """Test classifying YAML errors"""
        import yaml
        try:
            yaml.safe_load("invalid: yaml: syntax:")
        except yaml.YAMLError as e:
            context = classify_error(e, operation="Parsing YAML")
            assert context.category == ErrorCategory.YAML
            assert context.severity == ErrorSeverity.HIGH

    def test_classify_api_401_error(self):
        """Test classifying API 401 (unauthorized) error"""
        error = Exception("401 unauthorized")
        context = classify_error(error, operation="API call")

        assert context.category == ErrorCategory.API
        assert context.severity == ErrorSeverity.HIGH

    def test_classify_api_429_error(self):
        """Test classifying API 429 (rate limit) error"""
        error = Exception("429 rate limit exceeded")
        context = classify_error(error, operation="API call")

        assert context.category == ErrorCategory.API
        assert context.severity == ErrorSeverity.MEDIUM  # Retryable

    def test_classify_api_timeout(self):
        """Test classifying API timeout"""
        error = Exception("Request timed out")
        context = classify_error(error, operation="API call")

        assert context.category == ErrorCategory.API
        assert context.severity == ErrorSeverity.MEDIUM

    def test_classify_budget_error(self):
        """Test classifying budget errors"""
        error = Exception("Budget limit exceeded")
        context = classify_error(error, operation="Running scenario")

        assert context.category == ErrorCategory.BUDGET
        assert context.severity == ErrorSeverity.HIGH

    def test_classify_model_error(self):
        """Test classifying model errors"""
        error = Exception("Model not found: gpt-5")
        context = classify_error(error, operation="LLM call")

        assert context.category == ErrorCategory.MODEL
        assert context.severity == ErrorSeverity.HIGH

    def test_classify_with_context(self):
        """Test classifying error with additional context"""
        error = ValueError("Invalid config")
        context = classify_error(
            error,
            operation="Loading config",
            scenario_name="test-scenario",
            turn_number=3,
            cost_so_far=2.5
        )

        assert context.scenario_name == "test-scenario"
        assert context.turn_number == 3
        assert context.cost_so_far == 2.5


class TestErrorHandler:
    """Test ErrorHandler functionality"""

    def test_error_handler_creation(self):
        """Test creating an ErrorHandler"""
        handler = ErrorHandler(verbose=True)
        assert handler.verbose is True
        assert handler.error_history == []

    def test_handle_low_severity_error(self):
        """Test handling a low severity error"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=ValueError("Minor issue"),
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            operation="Validating input"
        )

        # Capture stderr to avoid polluting test output
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        should_continue, actions = handler.handle_error(context)

        sys.stderr = old_stderr

        assert should_continue is True
        assert len(handler.error_history) == 1

    def test_handle_high_severity_error(self):
        """Test handling a high severity error"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=FileNotFoundError("Critical file missing"),
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.HIGH,
            operation="Loading scenario",
            file_path="/path/to/scenario.yaml"
        )

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        should_continue, actions = handler.handle_error(context)

        sys.stderr = old_stderr

        assert should_continue is False
        assert len(actions) > 0
        assert len(handler.error_history) == 1

    def test_handle_fatal_error(self):
        """Test handling a fatal error"""
        handler = ErrorHandler()
        # Create a fatal error by classifying and then upgrading severity
        context = ErrorContext(
            error=Exception("Fatal system error"),
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.FATAL,
            operation="Critical operation"
        )

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        should_continue, actions = handler.handle_error(context)

        sys.stderr = old_stderr

        assert should_continue is False

    def test_api_error_recovery_actions(self):
        """Test recovery actions for API errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=Exception("401 unauthorized"),
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH,
            operation="Making API call"
        )

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        should_continue, actions = handler.handle_error(context)

        sys.stderr = old_stderr

        # Should suggest setting API key
        assert any('API key' in action.description for action in actions)
        assert any('OPENROUTER_API_KEY' in (action.command or '') for action in actions)

    def test_rate_limit_recovery_actions(self):
        """Test recovery actions for rate limit errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=Exception("429 rate limit exceeded"),
            category=ErrorCategory.API,
            severity=ErrorSeverity.MEDIUM,
            operation="Making API call"
        )

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        should_continue, actions = handler.handle_error(context)

        sys.stderr = old_stderr

        # Should suggest reducing parallel requests
        assert any('parallel' in action.description.lower() for action in actions)

    def test_file_not_found_recovery_actions(self):
        """Test recovery actions for file not found errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=FileNotFoundError("File not found"),
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.HIGH,
            operation="Loading file",
            file_path="/path/to/file.yaml"
        )

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        should_continue, actions = handler.handle_error(context)

        sys.stderr = old_stderr

        # Should suggest creating the file or checking path
        assert len(actions) > 0
        assert any('/path/to/file.yaml' in action.description for action in actions)

    def test_yaml_error_recovery_actions(self):
        """Test recovery actions for YAML errors"""
        handler = ErrorHandler()
        import yaml
        try:
            yaml.safe_load("invalid: yaml: syntax:")
        except yaml.YAMLError as e:
            context = classify_error(
                e,
                operation="Parsing YAML",
                file_path="/path/to/config.yaml"
            )

            # Capture stderr
            old_stderr = sys.stderr
            sys.stderr = StringIO()

            should_continue, actions = handler.handle_error(context)

            sys.stderr = old_stderr

            # Should suggest checking YAML syntax
            assert any('YAML' in action.description for action in actions)
            assert any('syntax' in action.description.lower() for action in actions)

    def test_budget_error_recovery_actions(self):
        """Test recovery actions for budget errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=Exception("Budget limit exceeded"),
            category=ErrorCategory.BUDGET,
            severity=ErrorSeverity.HIGH,
            operation="Running batch",
            scenario_name="test-scenario",
            run_number=5,
            cost_so_far=12.50
        )

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        should_continue, actions = handler.handle_error(context)

        sys.stderr = old_stderr

        # Should suggest resuming or increasing budget
        assert any('resume' in action.description.lower() for action in actions)
        assert any('$12.50' in action.description for action in actions)

    def test_model_error_recovery_actions(self):
        """Test recovery actions for model errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=Exception("Model not found: gpt-5"),
            category=ErrorCategory.MODEL,
            severity=ErrorSeverity.HIGH,
            operation="LLM call"
        )

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        should_continue, actions = handler.handle_error(context)

        sys.stderr = old_stderr

        # Should suggest checking model name
        assert any('model' in action.description.lower() for action in actions)
        assert any('openrouter.ai' in action.description.lower() for action in actions)

    def test_error_explanation_api(self):
        """Test API error explanations"""
        handler = ErrorHandler()

        # Test 429 explanation
        explanation = handler._explain_api_error(ErrorContext(
            error=Exception("429 rate limit"),
            category=ErrorCategory.API,
            severity=ErrorSeverity.MEDIUM,
            operation="API call"
        ))
        assert "rate limit" in explanation.lower()

        # Test 401 explanation
        explanation = handler._explain_api_error(ErrorContext(
            error=Exception("401 unauthorized"),
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH,
            operation="API call"
        ))
        assert "authentication" in explanation.lower()

    def test_error_history_tracking(self):
        """Test that errors are tracked in history"""
        handler = ErrorHandler()

        # Handle multiple errors
        for i in range(3):
            context = ErrorContext(
                error=ValueError(f"Error {i}"),
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                operation=f"Operation {i}"
            )

            # Capture stderr
            old_stderr = sys.stderr
            sys.stderr = StringIO()

            handler.handle_error(context)

            sys.stderr = old_stderr

        assert len(handler.error_history) == 3
        assert handler.error_history[0].operation == "Operation 0"
        assert handler.error_history[2].operation == "Operation 2"


class TestRecoveryAction:
    """Test RecoveryAction functionality"""

    def test_recovery_action_creation(self):
        """Test creating a RecoveryAction"""
        action = RecoveryAction(
            description="Fix the problem",
            command="python fix.py",
            automatic=True,
            priority=1
        )

        assert action.description == "Fix the problem"
        assert action.command == "python fix.py"
        assert action.automatic is True
        assert action.priority == 1

    def test_recovery_action_without_command(self):
        """Test RecoveryAction without command"""
        action = RecoveryAction(
            description="Check something manually",
            priority=2
        )

        assert action.description == "Check something manually"
        assert action.command is None
        assert action.automatic is False
        assert action.priority == 2


class TestErrorFormatting:
    """Test error message formatting"""

    def test_format_error_message_basic(self):
        """Test basic error message formatting"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=ValueError("Test error"),
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH,
            operation="Making API call"
        )

        message = handler._format_error_message(context)

        assert "ERROR" in message
        assert "API" in message.upper()
        assert "Test error" in message
        assert "Making API call" in message

    def test_format_error_message_with_context(self):
        """Test error message formatting with full context"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=FileNotFoundError("File missing"),
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.HIGH,
            operation="Loading scenario",
            scenario_name="test-scenario",
            run_number=3,
            turn_number=5,
            actor_name="TestActor",
            model_name="gpt-4o-mini",
            file_path="/path/to/file.yaml",
            cost_so_far=2.5
        )

        message = handler._format_error_message(context)

        assert "test-scenario" in message
        assert "Run: 3" in message
        assert "Turn: 5" in message
        assert "TestActor" in message
        assert "gpt-4o-mini" in message
        assert "/path/to/file.yaml" in message
        assert "$2.5" in message

    def test_format_includes_explanation(self):
        """Test that formatted message includes explanation"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=Exception("429 rate limit"),
            category=ErrorCategory.API,
            severity=ErrorSeverity.MEDIUM,
            operation="API call"
        )

        message = handler._format_error_message(context)

        # Should include explanation about what this means
        assert "Why this matters" in message or "rate limit" in message.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
