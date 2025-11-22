"""
Tests for Error Handler module

Tests error classification, context creation, and recovery suggestions.
"""
import pytest
from unittest.mock import MagicMock, patch
import requests

from scenario_lab.utils.error_handler import (
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    RecoveryAction,
    ErrorHandler,
    classify_error,
)


class TestErrorSeverity:
    """Tests for ErrorSeverity enum"""

    def test_severity_values(self):
        """Test that severity values are correct"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.FATAL.value == "fatal"


class TestErrorCategory:
    """Tests for ErrorCategory enum"""

    def test_category_values(self):
        """Test that category values are correct"""
        assert ErrorCategory.API.value == "api"
        assert ErrorCategory.FILE.value == "file"
        assert ErrorCategory.YAML.value == "yaml"
        assert ErrorCategory.BUDGET.value == "budget"
        assert ErrorCategory.STATE.value == "state"
        assert ErrorCategory.MODEL.value == "model"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestErrorContext:
    """Tests for ErrorContext dataclass"""

    def test_create_error_context(self):
        """Test creating an error context"""
        error = ValueError("Test error")
        context = ErrorContext(
            error=error,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            operation="Loading configuration"
        )

        assert context.error == error
        assert context.category == ErrorCategory.VALIDATION
        assert context.severity == ErrorSeverity.HIGH
        assert context.operation == "Loading configuration"

    def test_error_context_with_all_fields(self):
        """Test error context with all optional fields"""
        error = RuntimeError("Test")
        context = ErrorContext(
            error=error,
            category=ErrorCategory.API,
            severity=ErrorSeverity.MEDIUM,
            operation="Making API call",
            scenario_name="test-scenario",
            run_number=1,
            turn_number=5,
            actor_name="TestActor",
            model_name="openai/gpt-4o",
            file_path="/path/to/file",
            cost_so_far=1.50,
            additional_context={"key": "value"}
        )

        assert context.scenario_name == "test-scenario"
        assert context.run_number == 1
        assert context.turn_number == 5
        assert context.actor_name == "TestActor"
        assert context.model_name == "openai/gpt-4o"
        assert context.file_path == "/path/to/file"
        assert context.cost_so_far == 1.50
        assert context.additional_context == {"key": "value"}

    def test_to_dict(self):
        """Test converting error context to dictionary"""
        error = ValueError("Test error message")
        context = ErrorContext(
            error=error,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            operation="Test operation",
            scenario_name="test"
        )

        result = context.to_dict()

        assert result['error_type'] == 'ValueError'
        assert result['error_message'] == 'Test error message'
        assert result['category'] == 'validation'
        assert result['severity'] == 'high'
        assert result['operation'] == 'Test operation'
        assert result['scenario_name'] == 'test'


class TestRecoveryAction:
    """Tests for RecoveryAction dataclass"""

    def test_create_recovery_action(self):
        """Test creating a recovery action"""
        action = RecoveryAction(
            description="Retry the operation",
            command="scenario-lab run --resume",
            automatic=False,
            priority=1
        )

        assert action.description == "Retry the operation"
        assert action.command == "scenario-lab run --resume"
        assert action.automatic is False
        assert action.priority == 1

    def test_default_values(self):
        """Test default values for recovery action"""
        action = RecoveryAction(description="Simple action")

        assert action.command is None
        assert action.automatic is False
        assert action.priority == 1


class TestClassifyError:
    """Tests for classify_error function"""

    def test_classify_file_not_found(self):
        """Test classifying FileNotFoundError"""
        error = FileNotFoundError("File not found: /path/to/file")

        context = classify_error(error, operation="Loading file")

        assert context.category == ErrorCategory.FILE
        assert context.severity == ErrorSeverity.HIGH

    def test_classify_permission_error(self):
        """Test classifying PermissionError"""
        error = PermissionError("Access denied")

        context = classify_error(error, operation="Writing file")

        assert context.category == ErrorCategory.FILE
        assert context.severity == ErrorSeverity.HIGH

    def test_classify_rate_limit_error(self):
        """Test classifying 429 rate limit error"""
        error = RuntimeError("HTTP 429: Rate limit exceeded")

        context = classify_error(error, operation="API call")

        assert context.category == ErrorCategory.API
        assert context.severity == ErrorSeverity.MEDIUM  # Retryable

    def test_classify_unauthorized_error(self):
        """Test classifying 401 unauthorized error"""
        error = RuntimeError("HTTP 401: Unauthorized")

        context = classify_error(error, operation="API call")

        assert context.category == ErrorCategory.API
        assert context.severity == ErrorSeverity.HIGH

    def test_classify_forbidden_error(self):
        """Test classifying 403 forbidden error"""
        error = RuntimeError("HTTP 403: Forbidden")

        context = classify_error(error, operation="API call")

        assert context.category == ErrorCategory.API
        assert context.severity == ErrorSeverity.HIGH

    def test_classify_timeout_error(self):
        """Test classifying timeout error"""
        error = RuntimeError("Request timed out")

        context = classify_error(error, operation="API call")

        assert context.category == ErrorCategory.API
        assert context.severity == ErrorSeverity.MEDIUM

    def test_classify_network_error(self):
        """Test classifying network error"""
        error = RuntimeError("Network connection failed")

        context = classify_error(error, operation="API call")

        assert context.category == ErrorCategory.NETWORK
        assert context.severity == ErrorSeverity.MEDIUM

    def test_classify_budget_error(self):
        """Test classifying budget/cost error"""
        error = RuntimeError("Budget limit exceeded: cost over $5.00")

        context = classify_error(error, operation="Running scenario")

        assert context.category == ErrorCategory.BUDGET
        assert context.severity == ErrorSeverity.HIGH

    def test_classify_model_error(self):
        """Test classifying model not found error"""
        error = RuntimeError("Model not found: invalid-model")

        context = classify_error(error, operation="Making decision")

        assert context.category == ErrorCategory.MODEL
        assert context.severity == ErrorSeverity.HIGH

    def test_classify_state_error(self):
        """Test classifying state corruption error"""
        error = RuntimeError("State file corrupted")

        context = classify_error(error, operation="Loading state")

        assert context.category == ErrorCategory.STATE
        assert context.severity == ErrorSeverity.HIGH

    def test_classify_unknown_error(self):
        """Test classifying unknown error"""
        error = Exception("Some random error")

        context = classify_error(error, operation="Unknown operation")

        assert context.category == ErrorCategory.UNKNOWN
        assert context.severity == ErrorSeverity.MEDIUM

    def test_classify_with_context_fields(self):
        """Test that classify_error passes context fields"""
        error = ValueError("Test")

        context = classify_error(
            error,
            operation="Test operation",
            scenario_name="test-scenario",
            turn_number=3,
            actor_name="TestActor"
        )

        assert context.operation == "Test operation"
        assert context.scenario_name == "test-scenario"
        assert context.turn_number == 3
        assert context.actor_name == "TestActor"


class TestErrorHandler:
    """Tests for ErrorHandler class"""

    def test_init(self):
        """Test ErrorHandler initialization"""
        handler = ErrorHandler(verbose=True)

        assert handler.verbose is True
        assert handler.error_history == []

    @patch('builtins.print')
    def test_handle_error_records_history(self, mock_print):
        """Test that handle_error records error in history"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=ValueError("Test"),
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            operation="Test operation"
        )

        handler.handle_error(context)

        assert len(handler.error_history) == 1
        assert handler.error_history[0] == context

    @patch('builtins.print')
    def test_handle_error_returns_should_continue(self, mock_print):
        """Test that handle_error returns correct should_continue value"""
        handler = ErrorHandler()

        # Low severity - should continue
        low_context = ErrorContext(
            error=ValueError("Test"),
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.LOW,
            operation="Test"
        )
        should_continue, _ = handler.handle_error(low_context)
        assert should_continue is True

        # Medium severity - should continue
        medium_context = ErrorContext(
            error=ValueError("Test"),
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            operation="Test"
        )
        should_continue, _ = handler.handle_error(medium_context)
        assert should_continue is True

        # High severity - should not continue
        high_context = ErrorContext(
            error=ValueError("Test"),
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.HIGH,
            operation="Test"
        )
        should_continue, _ = handler.handle_error(high_context)
        assert should_continue is False

        # Fatal severity - should not continue
        fatal_context = ErrorContext(
            error=ValueError("Test"),
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.FATAL,
            operation="Test"
        )
        should_continue, _ = handler.handle_error(fatal_context)
        assert should_continue is False

    @patch('builtins.print')
    def test_handle_error_returns_recovery_actions(self, mock_print):
        """Test that handle_error returns recovery actions"""
        handler = ErrorHandler()

        # API rate limit error should have recovery actions
        context = ErrorContext(
            error=RuntimeError("HTTP 429 rate limit"),
            category=ErrorCategory.API,
            severity=ErrorSeverity.MEDIUM,
            operation="API call"
        )

        _, recovery_actions = handler.handle_error(context)

        assert isinstance(recovery_actions, list)
        assert len(recovery_actions) > 0


class TestErrorHandlerRecoveryActions:
    """Tests for ErrorHandler recovery action generation"""

    def test_api_rate_limit_recovery(self):
        """Test recovery actions for rate limit errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=RuntimeError("HTTP 429 rate limit exceeded"),
            category=ErrorCategory.API,
            severity=ErrorSeverity.MEDIUM,
            operation="API call"
        )

        actions = handler._get_api_recovery_actions(context)

        assert len(actions) > 0
        descriptions = [a.description for a in actions]
        assert any("retry" in d.lower() for d in descriptions)

    def test_api_unauthorized_recovery(self):
        """Test recovery actions for unauthorized errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=RuntimeError("HTTP 401 unauthorized"),
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH,
            operation="API call"
        )

        actions = handler._get_api_recovery_actions(context)

        descriptions = [a.description.lower() for a in actions]
        assert any("api key" in d for d in descriptions)

    def test_file_not_found_recovery(self):
        """Test recovery actions for file not found errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=FileNotFoundError("/path/to/file"),
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.HIGH,
            operation="Loading file",
            file_path="/path/to/file"
        )

        actions = handler._get_file_recovery_actions(context)

        assert len(actions) > 0
        descriptions = [a.description.lower() for a in actions]
        assert any("create" in d or "path" in d for d in descriptions)

    def test_budget_recovery(self):
        """Test recovery actions for budget errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=RuntimeError("Budget exceeded"),
            category=ErrorCategory.BUDGET,
            severity=ErrorSeverity.HIGH,
            operation="Running batch",
            cost_so_far=5.50
        )

        actions = handler._get_budget_recovery_actions(context)

        descriptions = [a.description.lower() for a in actions]
        assert any("budget" in d or "cost" in d or "cheaper" in d for d in descriptions)


class TestErrorHandlerExplanations:
    """Tests for error explanation messages"""

    def test_api_rate_limit_explanation(self):
        """Test explanation for rate limit errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=RuntimeError("HTTP 429 rate limit"),
            category=ErrorCategory.API,
            severity=ErrorSeverity.MEDIUM,
            operation="Test"
        )

        explanation = handler._explain_api_error(context)

        assert "rate limit" in explanation.lower()
        assert "throttling" in explanation.lower()

    def test_api_unauthorized_explanation(self):
        """Test explanation for unauthorized errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=RuntimeError("HTTP 401 unauthorized"),
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH,
            operation="Test"
        )

        explanation = handler._explain_api_error(context)

        assert "authentication" in explanation.lower()
        assert "api key" in explanation.lower()

    def test_file_not_found_explanation(self):
        """Test explanation for file not found errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=FileNotFoundError("file.yaml"),
            category=ErrorCategory.FILE,
            severity=ErrorSeverity.HIGH,
            operation="Test"
        )

        explanation = handler._explain_file_error(context)

        assert "could not be found" in explanation.lower()

    def test_yaml_error_explanation(self):
        """Test explanation for YAML errors"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=ValueError("YAML parse error"),
            category=ErrorCategory.YAML,
            severity=ErrorSeverity.HIGH,
            operation="Test"
        )

        explanation = handler._explain_yaml_error(context)

        assert "yaml" in explanation.lower()
        assert "indentation" in explanation.lower()


class TestErrorHandlerFormatting:
    """Tests for error message formatting"""

    def test_format_includes_operation(self):
        """Test that formatted message includes operation"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=ValueError("Test error"),
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            operation="Loading scenario configuration"
        )

        message = handler._format_error_message(context)

        assert "Loading scenario configuration" in message

    def test_format_includes_context_details(self):
        """Test that formatted message includes context details"""
        handler = ErrorHandler()
        context = ErrorContext(
            error=ValueError("Test"),
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH,
            operation="Test",
            scenario_name="test-scenario",
            turn_number=5,
            actor_name="TestActor",
            cost_so_far=2.50
        )

        message = handler._format_error_message(context)

        assert "test-scenario" in message
        assert "5" in message
        assert "TestActor" in message
        assert "2.50" in message

    def test_format_includes_severity_symbol(self):
        """Test that formatted message includes severity symbol"""
        handler = ErrorHandler()

        for severity in ErrorSeverity:
            context = ErrorContext(
                error=ValueError("Test"),
                category=ErrorCategory.UNKNOWN,
                severity=severity,
                operation="Test"
            )

            message = handler._format_error_message(context)

            # Should contain some symbol or indicator
            assert "ERROR" in message


class TestErrorHandlerIntegration:
    """Integration tests for error handler"""

    @patch('builtins.print')
    def test_full_error_handling_workflow(self, mock_print):
        """Test complete error handling workflow"""
        handler = ErrorHandler(verbose=True)

        # Classify an error
        error = requests.exceptions.HTTPError("429 Too Many Requests")
        context = classify_error(
            error,
            operation="Making LLM API call",
            scenario_name="test-scenario",
            turn_number=3,
            actor_name="US President",
            model_name="openai/gpt-4o"
        )

        # Handle the error
        should_continue, recovery_actions = handler.handle_error(context)

        # Verify results
        assert context.category == ErrorCategory.API
        assert should_continue is True  # Rate limits are retryable
        assert len(recovery_actions) > 0
        assert len(handler.error_history) == 1
