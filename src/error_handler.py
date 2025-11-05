"""
Error Handler - Enhanced error handling with detailed messages and recovery strategies

Provides:
- Rich error context capturing
- User-friendly error messages with suggested fixes
- Progressive fallback strategies
- Structured error reporting
"""
import sys
import traceback
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Minor issue, can continue
    MEDIUM = "medium"     # Issue but recoverable
    HIGH = "high"         # Critical, requires intervention
    FATAL = "fatal"       # Unrecoverable, must halt


class ErrorCategory(Enum):
    """Categories of errors for better handling"""
    API = "api"                   # API-related errors (rate limits, auth, timeouts)
    FILE = "file"                 # File system errors (missing files, permissions)
    YAML = "yaml"                 # YAML parsing/validation errors
    BUDGET = "budget"             # Budget/cost limit exceeded
    STATE = "state"               # State file corruption/incompatibility
    MODEL = "model"               # Model-related errors (not found, unsupported)
    VALIDATION = "validation"     # Data validation errors
    NETWORK = "network"           # Network connectivity errors
    CONFIGURATION = "configuration"  # Configuration errors
    UNKNOWN = "unknown"           # Uncategorized errors


@dataclass
class ErrorContext:
    """Rich context about an error"""
    error: Exception
    category: ErrorCategory
    severity: ErrorSeverity
    operation: str  # What was being attempted
    scenario_name: Optional[str] = None
    run_number: Optional[int] = None
    turn_number: Optional[int] = None
    actor_name: Optional[str] = None
    model_name: Optional[str] = None
    file_path: Optional[str] = None
    cost_so_far: Optional[float] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/reporting"""
        return {
            'error_type': type(self.error).__name__,
            'error_message': str(self.error),
            'category': self.category.value,
            'severity': self.severity.value,
            'operation': self.operation,
            'scenario_name': self.scenario_name,
            'run_number': self.run_number,
            'turn_number': self.turn_number,
            'actor_name': self.actor_name,
            'model_name': self.model_name,
            'file_path': self.file_path,
            'cost_so_far': self.cost_so_far,
            'additional_context': self.additional_context
        }


@dataclass
class RecoveryAction:
    """Describes a recovery action"""
    description: str
    command: Optional[str] = None
    automatic: bool = False  # Can be done automatically
    priority: int = 1  # Lower = higher priority


class ErrorHandler:
    """Enhanced error handler with user-friendly messages and recovery suggestions"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.error_history: List[ErrorContext] = []

    def handle_error(self, context: ErrorContext) -> Tuple[bool, List[RecoveryAction]]:
        """
        Handle an error with appropriate messaging and recovery suggestions

        Args:
            context: ErrorContext with full error details

        Returns:
            Tuple of (should_continue, recovery_actions)
            - should_continue: True if execution can continue, False if must halt
            - recovery_actions: List of suggested recovery actions
        """
        # Log the error
        self.error_history.append(context)

        # Format the error message
        message = self._format_error_message(context)

        # Get recovery suggestions
        recovery_actions = self._get_recovery_actions(context)

        # Display to user
        self._display_error(message, recovery_actions, context.severity)

        # Decide if we should continue
        should_continue = context.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]

        return should_continue, recovery_actions

    def _format_error_message(self, context: ErrorContext) -> str:
        """Format a user-friendly error message"""
        # Header with color coding (if terminal supports it)
        severity_symbols = {
            ErrorSeverity.LOW: "ℹ️",
            ErrorSeverity.MEDIUM: "⚠️",
            ErrorSeverity.HIGH: "❌",
            ErrorSeverity.FATAL: "🛑"
        }
        symbol = severity_symbols.get(context.severity, "❓")

        lines = [
            f"\n{symbol} ERROR: {context.category.value.upper()}",
            "=" * 70,
            f"What happened: {str(context.error)}",
            f"While: {context.operation}",
        ]

        # Add context details
        if context.scenario_name:
            lines.append(f"Scenario: {context.scenario_name}")
        if context.run_number is not None:
            lines.append(f"Run: {context.run_number}")
        if context.turn_number is not None:
            lines.append(f"Turn: {context.turn_number}")
        if context.actor_name:
            lines.append(f"Actor: {context.actor_name}")
        if context.model_name:
            lines.append(f"Model: {context.model_name}")
        if context.file_path:
            lines.append(f"File: {context.file_path}")
        if context.cost_so_far is not None:
            lines.append(f"Cost so far: ${context.cost_so_far:.4f}")

        # Add specific explanation based on error category
        explanation = self._get_error_explanation(context)
        if explanation:
            lines.append("")
            lines.append("Why this matters:")
            lines.append(explanation)

        return "\n".join(lines)

    def _get_error_explanation(self, context: ErrorContext) -> str:
        """Get category-specific error explanation"""
        explanations = {
            ErrorCategory.API: self._explain_api_error(context),
            ErrorCategory.FILE: self._explain_file_error(context),
            ErrorCategory.YAML: self._explain_yaml_error(context),
            ErrorCategory.BUDGET: self._explain_budget_error(context),
            ErrorCategory.STATE: self._explain_state_error(context),
            ErrorCategory.MODEL: self._explain_model_error(context),
            ErrorCategory.NETWORK: self._explain_network_error(context),
            ErrorCategory.CONFIGURATION: self._explain_configuration_error(context),
        }
        return explanations.get(context.category, "")

    def _explain_api_error(self, context: ErrorContext) -> str:
        """Explain API errors"""
        error_str = str(context.error).lower()

        if '429' in error_str or 'rate limit' in error_str:
            return (
                "You've hit the API rate limit. The API provider is throttling requests "
                "to prevent overload. This is common with free or low-tier API plans."
            )
        elif '401' in error_str or 'unauthorized' in error_str:
            return (
                "Authentication failed. Your API key may be invalid, expired, or not set. "
                "The API requires valid credentials to process requests."
            )
        elif '403' in error_str or 'forbidden' in error_str:
            return (
                "Access denied. Your API key may not have permission to use this model "
                "or feature. Check your API plan and model access."
            )
        elif '404' in error_str or 'not found' in error_str:
            return (
                "The requested resource (likely a model) was not found. The model name "
                "may be incorrect or the model may have been removed."
            )
        elif 'timeout' in error_str:
            return (
                "The API request timed out. The server took too long to respond, possibly "
                "due to high load or a complex request."
            )
        else:
            return "An API communication error occurred."

    def _explain_file_error(self, context: ErrorContext) -> str:
        """Explain file errors"""
        if isinstance(context.error, FileNotFoundError):
            return (
                "A required file could not be found. This may indicate incorrect paths "
                "in your configuration or missing scenario files."
            )
        elif isinstance(context.error, PermissionError):
            return (
                "Permission denied when accessing a file. Check file permissions and "
                "ensure you have read/write access to the directory."
            )
        else:
            return "A file system error occurred."

    def _explain_yaml_error(self, context: ErrorContext) -> str:
        """Explain YAML errors"""
        return (
            "The YAML file has syntax errors or is invalid. YAML is sensitive to "
            "indentation and special characters. Even a single extra space can cause errors."
        )

    def _explain_budget_error(self, context: ErrorContext) -> str:
        """Explain budget errors"""
        return (
            "The cost limit has been exceeded. Batch runs can be expensive, so the "
            "system enforces budget limits to prevent unexpected charges."
        )

    def _explain_state_error(self, context: ErrorContext) -> str:
        """Explain state errors"""
        return (
            "The scenario state file is corrupted or incompatible. This may happen if "
            "the file was manually edited or created by a different version."
        )

    def _explain_model_error(self, context: ErrorContext) -> str:
        """Explain model errors"""
        return (
            "There's an issue with the specified model. The model name may be incorrect, "
            "the model may not be available, or you may not have access to it."
        )

    def _explain_network_error(self, context: ErrorContext) -> str:
        """Explain network errors"""
        return (
            "A network connectivity issue prevented communication with the API. Check "
            "your internet connection and firewall settings."
        )

    def _explain_configuration_error(self, context: ErrorContext) -> str:
        """Explain configuration errors"""
        return (
            "The configuration is invalid or incomplete. Check that all required fields "
            "are present and have valid values."
        )

    def _get_recovery_actions(self, context: ErrorContext) -> List[RecoveryAction]:
        """Get category-specific recovery actions"""
        actions = {
            ErrorCategory.API: self._get_api_recovery_actions(context),
            ErrorCategory.FILE: self._get_file_recovery_actions(context),
            ErrorCategory.YAML: self._get_yaml_recovery_actions(context),
            ErrorCategory.BUDGET: self._get_budget_recovery_actions(context),
            ErrorCategory.STATE: self._get_state_recovery_actions(context),
            ErrorCategory.MODEL: self._get_model_recovery_actions(context),
            ErrorCategory.NETWORK: self._get_network_recovery_actions(context),
            ErrorCategory.CONFIGURATION: self._get_configuration_recovery_actions(context),
        }
        return actions.get(context.category, [])

    def _get_api_recovery_actions(self, context: ErrorContext) -> List[RecoveryAction]:
        """Get recovery actions for API errors"""
        error_str = str(context.error).lower()
        actions = []

        if '429' in error_str or 'rate limit' in error_str:
            actions.extend([
                RecoveryAction(
                    "Wait and retry (automatic retry already attempted)",
                    priority=1
                ),
                RecoveryAction(
                    "Reduce --max-parallel to fewer concurrent runs",
                    command="# Edit your batch config to set max_parallel: 1 or 2",
                    priority=2
                ),
                RecoveryAction(
                    "Use a different API key with higher rate limits",
                    command="export OPENROUTER_API_KEY=your_key_here",
                    priority=3
                )
            ])

        elif '401' in error_str or 'unauthorized' in error_str:
            actions.extend([
                RecoveryAction(
                    "Set or update your API key",
                    command="export OPENROUTER_API_KEY=your_api_key_here",
                    priority=1
                ),
                RecoveryAction(
                    "Verify your API key is valid at https://openrouter.ai/keys",
                    priority=2
                )
            ])

        elif '403' in error_str or 'forbidden' in error_str:
            actions.extend([
                RecoveryAction(
                    "Check your API plan has access to this model",
                    priority=1
                ),
                RecoveryAction(
                    "Try a different model that you have access to",
                    command="# Edit your scenario YAML to use a different model",
                    priority=2
                )
            ])

        elif '404' in error_str or 'not found' in error_str:
            actions.extend([
                RecoveryAction(
                    "Verify the model name is correct",
                    command="# Common models: openai/gpt-4o-mini, anthropic/claude-3-haiku",
                    priority=1
                ),
                RecoveryAction(
                    "Check available models at https://openrouter.ai/models",
                    priority=2
                )
            ])

        elif 'timeout' in error_str:
            actions.extend([
                RecoveryAction(
                    "Retry the request (automatic retry already attempted)",
                    priority=1
                ),
                RecoveryAction(
                    "Simplify the prompt to reduce processing time",
                    priority=2
                ),
                RecoveryAction(
                    "Try a faster model (e.g., gpt-4o-mini instead of gpt-4)",
                    priority=3
                )
            ])

        return actions

    def _get_file_recovery_actions(self, context: ErrorContext) -> List[RecoveryAction]:
        """Get recovery actions for file errors"""
        actions = []

        if isinstance(context.error, FileNotFoundError):
            if context.file_path:
                actions.append(
                    RecoveryAction(
                        f"Create the missing file: {context.file_path}",
                        command=f"touch {context.file_path}",
                        priority=1
                    )
                )
            actions.append(
                RecoveryAction(
                    "Verify the path in your configuration is correct",
                    priority=2
                )
            )
            actions.append(
                RecoveryAction(
                    "Check you're running from the correct directory",
                    command="pwd  # Should be in the scenario-lab root",
                    priority=3
                )
            )

        elif isinstance(context.error, PermissionError):
            if context.file_path:
                actions.append(
                    RecoveryAction(
                        f"Fix file permissions: chmod 644 {context.file_path}",
                        command=f"chmod 644 {context.file_path}",
                        priority=1
                    )
                )
            actions.append(
                RecoveryAction(
                    "Ensure you have write access to the directory",
                    command="ls -la",
                    priority=2
                )
            )

        return actions

    def _get_yaml_recovery_actions(self, context: ErrorContext) -> List[RecoveryAction]:
        """Get recovery actions for YAML errors"""
        actions = [
            RecoveryAction(
                "Check YAML syntax with a validator",
                command="python -c \"import yaml; yaml.safe_load(open('your_file.yaml'))\"",
                priority=1
            ),
            RecoveryAction(
                "Common YAML issues: indentation (must use spaces, not tabs), "
                "unquoted special characters (: @ #), missing colons",
                priority=2
            )
        ]

        if context.file_path:
            actions.insert(0, RecoveryAction(
                f"Review the file for syntax errors: {context.file_path}",
                command=f"cat {context.file_path}",
                priority=1
            ))

        return actions

    def _get_budget_recovery_actions(self, context: ErrorContext) -> List[RecoveryAction]:
        """Get recovery actions for budget errors"""
        actions = []

        # Suggest resuming with higher budget
        if context.scenario_name and context.run_number:
            run_dir = f"{context.scenario_name}/runs/run-{context.run_number:03d}"
            actions.append(
                RecoveryAction(
                    "Resume with increased budget limit",
                    command=f"python src/run_scenario.py --resume {run_dir}",
                    priority=1
                )
            )

        actions.extend([
            RecoveryAction(
                "Review the batch config and increase credit_limit",
                command="# Edit your batch config YAML file",
                priority=2
            ),
            RecoveryAction(
                "Use cheaper models to reduce costs",
                command="# Try openai/gpt-4o-mini or anthropic/claude-3-haiku",
                priority=3
            ),
            RecoveryAction(
                "Reduce the number of runs or turns",
                priority=4
            )
        ])

        if context.cost_so_far:
            actions.insert(0, RecoveryAction(
                f"Current cost: ${context.cost_so_far:.4f}",
                priority=0
            ))

        return actions

    def _get_state_recovery_actions(self, context: ErrorContext) -> List[RecoveryAction]:
        """Get recovery actions for state errors"""
        actions = [
            RecoveryAction(
                "Start a fresh run (previous state may be corrupted)",
                priority=1
            ),
            RecoveryAction(
                "If using --resume, verify the scenario-state.json file is valid",
                command="python -c \"import json; print(json.load(open('scenario-state.json')))\"",
                priority=2
            )
        ]

        return actions

    def _get_model_recovery_actions(self, context: ErrorContext) -> List[RecoveryAction]:
        """Get recovery actions for model errors"""
        actions = [
            RecoveryAction(
                "Verify model name format (e.g., 'openai/gpt-4o-mini')",
                priority=1
            ),
            RecoveryAction(
                "Check available models at https://openrouter.ai/models",
                priority=2
            ),
            RecoveryAction(
                "Try a common model: openai/gpt-4o-mini, anthropic/claude-3-haiku, "
                "meta-llama/llama-3.1-70b-instruct",
                priority=3
            )
        ]

        return actions

    def _get_network_recovery_actions(self, context: ErrorContext) -> List[RecoveryAction]:
        """Get recovery actions for network errors"""
        return [
            RecoveryAction(
                "Check your internet connection",
                command="ping -c 3 openrouter.ai",
                priority=1
            ),
            RecoveryAction(
                "Verify firewall isn't blocking outbound HTTPS connections",
                priority=2
            ),
            RecoveryAction(
                "Try again in a few moments (automatic retry already attempted)",
                priority=3
            )
        ]

    def _get_configuration_recovery_actions(self, context: ErrorContext) -> List[RecoveryAction]:
        """Get recovery actions for configuration errors"""
        actions = [
            RecoveryAction(
                "Use the interactive config wizard to create a valid configuration",
                command="python src/create_batch_config.py --interactive",
                priority=1
            ),
            RecoveryAction(
                "Review the example configs in experiments/ directory",
                command="ls experiments/",
                priority=2
            ),
            RecoveryAction(
                "Validate your config with dry-run mode",
                command="python src/batch_runner.py your_config.yaml --dry-run",
                priority=3
            )
        ]

        return actions

    def _display_error(self, message: str, recovery_actions: List[RecoveryAction],
                      severity: ErrorSeverity):
        """Display error message and recovery actions to user"""
        # Print main error message
        print(message, file=sys.stderr)

        # Print recovery actions
        if recovery_actions:
            print("\n" + "=" * 70, file=sys.stderr)
            print("💡 SUGGESTED ACTIONS:", file=sys.stderr)
            print("=" * 70, file=sys.stderr)

            # Sort by priority
            sorted_actions = sorted(recovery_actions, key=lambda a: a.priority)

            for i, action in enumerate(sorted_actions, 1):
                print(f"\n{i}. {action.description}", file=sys.stderr)
                if action.command:
                    print(f"   Command: {action.command}", file=sys.stderr)

        print("\n" + "=" * 70 + "\n", file=sys.stderr)

        # Log to file as well
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.FATAL]:
            logger.error(message)
            for action in recovery_actions:
                logger.info(f"Recovery action: {action.description}")


def classify_error(error: Exception, **kwargs) -> ErrorContext:
    """
    Classify an error and create an ErrorContext

    Args:
        error: The exception that occurred
        **kwargs: Additional context fields (operation, scenario_name, etc.)

    Returns:
        ErrorContext with appropriate category and severity
    """
    error_type = type(error).__name__
    error_str = str(error).lower()

    # Default values
    category = ErrorCategory.UNKNOWN
    severity = ErrorSeverity.MEDIUM

    # Classify by exception type
    if isinstance(error, FileNotFoundError):
        category = ErrorCategory.FILE
        severity = ErrorSeverity.HIGH
    elif isinstance(error, PermissionError):
        category = ErrorCategory.FILE
        severity = ErrorSeverity.HIGH
    elif 'yaml' in error_type.lower() or 'yaml' in type(error).__module__.lower():
        category = ErrorCategory.YAML
        severity = ErrorSeverity.HIGH
    elif 'validation' in error_type.lower():
        category = ErrorCategory.VALIDATION
        severity = ErrorSeverity.HIGH

    # Classify by error message
    elif any(code in error_str for code in ['401', '403', '404', '429', 'unauthorized', 'forbidden', 'rate limit']):
        category = ErrorCategory.API
        if '429' in error_str or 'rate limit' in error_str:
            severity = ErrorSeverity.MEDIUM  # Retryable
        elif '401' in error_str or 'unauthorized' in error_str:
            severity = ErrorSeverity.HIGH  # Needs user action
        elif '403' in error_str or 'forbidden' in error_str:
            severity = ErrorSeverity.HIGH
        elif '404' in error_str:
            severity = ErrorSeverity.HIGH

    elif 'timeout' in error_str or 'timed out' in error_str:
        category = ErrorCategory.API
        severity = ErrorSeverity.MEDIUM

    elif 'network' in error_str or 'connection' in error_str:
        category = ErrorCategory.NETWORK
        severity = ErrorSeverity.MEDIUM

    elif 'budget' in error_str or 'cost' in error_str or 'credit' in error_str:
        category = ErrorCategory.BUDGET
        severity = ErrorSeverity.HIGH

    elif 'state' in error_str or 'corrupted' in error_str:
        category = ErrorCategory.STATE
        severity = ErrorSeverity.HIGH

    elif 'model' in error_str and ('not found' in error_str or 'unsupported' in error_str):
        category = ErrorCategory.MODEL
        severity = ErrorSeverity.HIGH

    elif 'config' in error_str or 'invalid' in error_str:
        category = ErrorCategory.CONFIGURATION
        severity = ErrorSeverity.HIGH

    return ErrorContext(
        error=error,
        category=category,
        severity=severity,
        **kwargs
    )
