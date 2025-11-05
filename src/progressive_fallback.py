"""
Progressive Fallback - Smart fallback strategies for resilient execution

Provides progressive retry and fallback:
1. First attempt with specified model
2. Retry with exponential backoff (via api_utils)
3. Fallback to alternative model if configured
4. Save state and halt with recovery instructions
"""
from typing import Optional, List, Callable, Any, Dict
from dataclasses import dataclass
import logging

from error_handler import ErrorHandler, ErrorContext, classify_error, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior"""
    # Alternative models to try (in order)
    fallback_models: Optional[List[str]] = None

    # Whether to enable automatic fallback
    enable_fallback: bool = True

    # Maximum number of fallback attempts
    max_fallback_attempts: int = 2

    # Whether to save state before halting on error
    save_state_on_error: bool = True


class ProgressiveFallbackExecutor:
    """
    Execute operations with progressive fallback strategies

    Execution flow:
    1. Try primary approach (with automatic retries via api_utils)
    2. If that fails, try fallback models (if configured)
    3. If all fallbacks fail, save state and provide recovery instructions
    """

    def __init__(self,
                 fallback_config: Optional[FallbackConfig] = None,
                 error_handler: Optional[ErrorHandler] = None,
                 context: Optional[Dict[str, Any]] = None):
        """
        Initialize progressive fallback executor

        Args:
            fallback_config: Configuration for fallback behavior
            error_handler: ErrorHandler instance for user-friendly messages
            context: Context dict for error reporting (scenario, turn, actor, etc.)
        """
        self.fallback_config = fallback_config or FallbackConfig()
        self.error_handler = error_handler or ErrorHandler()
        self.context = context or {}

    def execute_with_fallback(self,
                             primary_func: Callable,
                             operation_name: str,
                             fallback_func_generator: Optional[Callable[[str], Callable]] = None
                             ) -> Any:
        """
        Execute a function with progressive fallback

        Args:
            primary_func: Primary function to execute
            operation_name: Description of operation for error messages
            fallback_func_generator: Optional function that takes a fallback model name
                                    and returns a callable to try with that model

        Returns:
            Result from successful execution

        Raises:
            Exception: If all attempts (including fallbacks) fail
        """
        # Track all errors encountered
        errors = []

        # Try primary function
        try:
            logger.info(f"Executing: {operation_name}")
            return primary_func()

        except Exception as e:
            errors.append(('primary', str(e)))
            logger.warning(f"Primary attempt failed for {operation_name}: {str(e)[:200]}")

            # Classify and handle the error
            error_context = classify_error(
                e,
                operation=operation_name,
                **self.context
            )

            # If this is a fatal error or fallback is disabled, handle and raise
            if (error_context.severity == ErrorSeverity.FATAL or
                not self.fallback_config.enable_fallback or
                not self.fallback_config.fallback_models or
                not fallback_func_generator):

                should_continue, recovery_actions = self.error_handler.handle_error(error_context)

                if not should_continue:
                    raise
                else:
                    # For some errors we can continue despite the issue
                    logger.warning(f"Continuing despite error: {str(e)[:100]}")
                    raise  # Re-raise to let caller handle

            # Try fallback models
            if self.fallback_config.fallback_models and fallback_func_generator:
                for i, fallback_model in enumerate(self.fallback_config.fallback_models):
                    if i >= self.fallback_config.max_fallback_attempts:
                        break

                    try:
                        logger.info(
                            f"Trying fallback model {i+1}/{len(self.fallback_config.fallback_models)}: "
                            f"{fallback_model}"
                        )

                        fallback_func = fallback_func_generator(fallback_model)
                        result = fallback_func()

                        logger.info(f"Fallback succeeded with model: {fallback_model}")
                        return result

                    except Exception as fallback_error:
                        errors.append((fallback_model, str(fallback_error)))
                        logger.warning(
                            f"Fallback model {fallback_model} failed: "
                            f"{str(fallback_error)[:200]}"
                        )
                        continue

            # All attempts failed - create comprehensive error context
            final_error_context = classify_error(
                e,  # Use original error
                operation=f"{operation_name} (tried {len(errors)} approaches)",
                **self.context
            )

            # Add all errors to context
            final_error_context.additional_context['all_attempts'] = errors

            # Handle with user-friendly message
            should_continue, recovery_actions = self.error_handler.handle_error(final_error_context)

            # Re-raise the original error
            raise


def create_model_fallback_list(primary_model: str) -> List[str]:
    """
    Create a smart fallback list based on primary model

    Args:
        primary_model: The primary model being used

    Returns:
        List of alternative models to try (cheapest to most expensive)
    """
    # Map of model -> cheaper alternatives
    fallback_map = {
        # OpenAI models
        'openai/gpt-4': ['openai/gpt-4o', 'openai/gpt-4o-mini'],
        'openai/gpt-4-turbo': ['openai/gpt-4o', 'openai/gpt-4o-mini'],
        'openai/gpt-4o': ['openai/gpt-4o-mini'],
        'openai/o1-preview': ['openai/gpt-4o', 'openai/gpt-4o-mini'],
        'openai/o1-mini': ['openai/gpt-4o-mini'],

        # Anthropic models
        'anthropic/claude-3-opus': ['anthropic/claude-3-sonnet', 'anthropic/claude-3-haiku'],
        'anthropic/claude-3-sonnet': ['anthropic/claude-3-haiku'],
        'anthropic/claude-3.5-sonnet': ['anthropic/claude-3-sonnet', 'anthropic/claude-3-haiku'],

        # Meta models
        'meta-llama/llama-3.1-405b-instruct': [
            'meta-llama/llama-3.1-70b-instruct',
            'meta-llama/llama-3.1-8b-instruct'
        ],
        'meta-llama/llama-3.1-70b-instruct': ['meta-llama/llama-3.1-8b-instruct'],

        # Google models
        'google/gemini-pro-1.5': ['google/gemini-pro'],

        # Mistral models
        'mistralai/mistral-large': ['mistralai/mistral-medium', 'mistralai/mistral-small'],
        'mistralai/mistral-medium': ['mistralai/mistral-small'],
    }

    # Get specific fallbacks if available
    if primary_model in fallback_map:
        return fallback_map[primary_model]

    # Generic fallbacks based on model family
    if 'gpt-4' in primary_model.lower():
        return ['openai/gpt-4o-mini']
    elif 'claude' in primary_model.lower():
        return ['anthropic/claude-3-haiku']
    elif 'llama' in primary_model.lower():
        return ['meta-llama/llama-3.1-8b-instruct']
    elif 'gemini' in primary_model.lower():
        return ['google/gemini-pro']

    # Universal cheap fallback
    return ['openai/gpt-4o-mini', 'anthropic/claude-3-haiku']


def should_enable_fallback(error: Exception) -> bool:
    """
    Determine if an error should trigger fallback attempts

    Args:
        error: The exception that occurred

    Returns:
        True if fallback should be attempted, False otherwise
    """
    error_str = str(error).lower()

    # Enable fallback for:
    # - Model not found (404)
    # - Model access denied (403)
    # - Model timeout (might work with faster model)
    # - Model overloaded (503)

    enable_conditions = [
        '404' in error_str,
        '403' in error_str,
        'not found' in error_str,
        'forbidden' in error_str,
        'timeout' in error_str or 'timed out' in error_str,
        '503' in error_str,
        'overloaded' in error_str,
        'unavailable' in error_str
    ]

    # Don't enable fallback for:
    # - Authentication errors (need to fix API key, not try different model)
    # - Budget errors (need to increase budget, not try different model)
    # - Rate limits (need to wait, not try different model)

    disable_conditions = [
        '401' in error_str and 'unauthorized' in error_str,
        'budget' in error_str,
        'cost' in error_str,
        '429' in error_str and 'rate' in error_str
    ]

    if any(disable_conditions):
        return False

    return any(enable_conditions)


def execute_with_auto_fallback(
    func: Callable,
    operation_name: str,
    primary_model: str,
    fallback_func_generator: Callable[[str], Callable],
    context: Optional[Dict[str, Any]] = None,
    enable_fallback: bool = True
) -> Any:
    """
    Convenience function to execute with automatic model fallback

    Args:
        func: Primary function to execute
        operation_name: Description of operation
        primary_model: Primary model being used
        fallback_func_generator: Function that creates a new callable with fallback model
        context: Context dict for error reporting
        enable_fallback: Whether to enable automatic fallback

    Returns:
        Result from successful execution
    """
    if not enable_fallback:
        # No fallback - just execute
        return func()

    try:
        return func()
    except Exception as e:
        # Check if this error should trigger fallback
        if not should_enable_fallback(e):
            raise

        # Create fallback config with smart model list
        fallback_models = create_model_fallback_list(primary_model)

        fallback_config = FallbackConfig(
            fallback_models=fallback_models,
            enable_fallback=True,
            max_fallback_attempts=min(2, len(fallback_models))
        )

        # Create executor and try with fallback
        executor = ProgressiveFallbackExecutor(
            fallback_config=fallback_config,
            context=context
        )

        # Note: first attempt already failed, so we directly try fallbacks
        errors = [('primary', str(e))]

        for i, fallback_model in enumerate(fallback_models[:fallback_config.max_fallback_attempts]):
            try:
                logger.info(
                    f"Trying fallback model {i+1}/{len(fallback_models)}: {fallback_model}"
                )

                fallback_func = fallback_func_generator(fallback_model)
                result = fallback_func()

                logger.info(f"Fallback succeeded with model: {fallback_model}")
                return result

            except Exception as fallback_error:
                errors.append((fallback_model, str(fallback_error)))
                logger.warning(
                    f"Fallback model {fallback_model} failed: "
                    f"{str(fallback_error)[:200]}"
                )
                continue

        # All attempts failed
        error_context = classify_error(
            e,
            operation=f"{operation_name} (tried {len(errors)} models)",
            model_name=primary_model,
            **(context or {})
        )
        error_context.additional_context['all_attempts'] = errors

        error_handler = ErrorHandler()
        error_handler.handle_error(error_context)

        # Re-raise original error
        raise
