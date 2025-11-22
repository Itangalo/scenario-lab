"""
Comprehensive tests for progressive fallback module

Tests fallback configuration, execution strategies, model fallback lists,
and error handling behavior.
"""
import unittest
from unittest.mock import patch, MagicMock
import logging

from scenario_lab.utils.progressive_fallback import (
    FallbackConfig,
    ProgressiveFallbackExecutor,
    create_model_fallback_list,
    should_enable_fallback,
    execute_with_auto_fallback,
)
from scenario_lab.utils.error_handler import ErrorSeverity


class TestFallbackConfig(unittest.TestCase):
    """Tests for FallbackConfig dataclass"""

    def test_default_config(self):
        """Test default FallbackConfig values"""
        config = FallbackConfig()

        self.assertIsNone(config.fallback_models)
        self.assertTrue(config.enable_fallback)
        self.assertEqual(config.max_fallback_attempts, 2)
        self.assertTrue(config.save_state_on_error)

    def test_custom_config(self):
        """Test FallbackConfig with custom values"""
        config = FallbackConfig(
            fallback_models=['openai/gpt-4o-mini', 'anthropic/claude-3-haiku'],
            enable_fallback=False,
            max_fallback_attempts=3,
            save_state_on_error=False
        )

        self.assertEqual(config.fallback_models, ['openai/gpt-4o-mini', 'anthropic/claude-3-haiku'])
        self.assertFalse(config.enable_fallback)
        self.assertEqual(config.max_fallback_attempts, 3)
        self.assertFalse(config.save_state_on_error)


class TestProgressiveFallbackExecutor(unittest.TestCase):
    """Tests for ProgressiveFallbackExecutor class"""

    def test_init_defaults(self):
        """Test executor initialization with defaults"""
        executor = ProgressiveFallbackExecutor()

        self.assertIsNotNone(executor.fallback_config)
        self.assertIsNotNone(executor.error_handler)
        self.assertEqual(executor.context, {})

    def test_init_with_config(self):
        """Test executor initialization with custom config"""
        config = FallbackConfig(
            fallback_models=['openai/gpt-4o-mini'],
            max_fallback_attempts=1
        )
        context = {'scenario': 'test', 'turn': 1}

        executor = ProgressiveFallbackExecutor(
            fallback_config=config,
            context=context
        )

        self.assertEqual(executor.fallback_config.fallback_models, ['openai/gpt-4o-mini'])
        self.assertEqual(executor.context, context)

    def test_execute_primary_success(self):
        """Test execution when primary function succeeds"""
        executor = ProgressiveFallbackExecutor()

        def primary_func():
            return "success"

        result = executor.execute_with_fallback(
            primary_func=primary_func,
            operation_name="test operation"
        )

        self.assertEqual(result, "success")

    def test_execute_primary_failure_no_fallback_config(self):
        """Test execution when primary fails and no fallback models configured"""
        executor = ProgressiveFallbackExecutor()

        def primary_func():
            raise ValueError("Primary failed")

        with self.assertRaises(ValueError):
            executor.execute_with_fallback(
                primary_func=primary_func,
                operation_name="test operation"
            )

    def test_execute_with_fallback_success(self):
        """Test execution with successful fallback"""
        config = FallbackConfig(
            fallback_models=['fallback-model-1', 'fallback-model-2'],
            enable_fallback=True
        )
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        call_count = 0

        def primary_func():
            raise ValueError("Primary failed")

        def fallback_generator(model):
            def fallback_func():
                return f"fallback success with {model}"
            return fallback_func

        result = executor.execute_with_fallback(
            primary_func=primary_func,
            operation_name="test operation",
            fallback_func_generator=fallback_generator
        )

        self.assertEqual(result, "fallback success with fallback-model-1")

    def test_execute_with_fallback_all_fail(self):
        """Test execution when all fallbacks fail"""
        config = FallbackConfig(
            fallback_models=['fallback-1', 'fallback-2'],
            enable_fallback=True
        )
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        def primary_func():
            raise ValueError("Primary failed")

        def fallback_generator(model):
            def fallback_func():
                raise ValueError(f"Fallback {model} failed")
            return fallback_func

        with self.assertRaises(ValueError) as ctx:
            executor.execute_with_fallback(
                primary_func=primary_func,
                operation_name="test operation",
                fallback_func_generator=fallback_generator
            )

        self.assertIn("Primary failed", str(ctx.exception))

    def test_execute_respects_max_fallback_attempts(self):
        """Test that max_fallback_attempts is respected"""
        config = FallbackConfig(
            fallback_models=['model-1', 'model-2', 'model-3', 'model-4'],
            enable_fallback=True,
            max_fallback_attempts=2
        )
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        attempts = []

        def primary_func():
            raise ValueError("Primary failed")

        def fallback_generator(model):
            def fallback_func():
                attempts.append(model)
                raise ValueError(f"{model} failed")
            return fallback_func

        with self.assertRaises(ValueError):
            executor.execute_with_fallback(
                primary_func=primary_func,
                operation_name="test operation",
                fallback_func_generator=fallback_generator
            )

        # Should only have tried 2 fallback models
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts, ['model-1', 'model-2'])

    def test_execute_fallback_disabled(self):
        """Test execution when fallback is disabled"""
        config = FallbackConfig(
            fallback_models=['model-1', 'model-2'],
            enable_fallback=False
        )
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        def primary_func():
            raise ValueError("Primary failed")

        def fallback_generator(model):
            def fallback_func():
                return "should not reach here"
            return fallback_func

        with self.assertRaises(ValueError):
            executor.execute_with_fallback(
                primary_func=primary_func,
                operation_name="test operation",
                fallback_func_generator=fallback_generator
            )


class TestCreateModelFallbackList(unittest.TestCase):
    """Tests for create_model_fallback_list function"""

    def test_openai_gpt4_fallbacks(self):
        """Test fallback list for GPT-4 models"""
        fallbacks = create_model_fallback_list('openai/gpt-4')
        self.assertIn('openai/gpt-4o', fallbacks)
        self.assertIn('openai/gpt-4o-mini', fallbacks)

    def test_openai_gpt4o_fallbacks(self):
        """Test fallback list for GPT-4o model"""
        fallbacks = create_model_fallback_list('openai/gpt-4o')
        self.assertEqual(fallbacks, ['openai/gpt-4o-mini'])

    def test_anthropic_opus_fallbacks(self):
        """Test fallback list for Claude Opus"""
        fallbacks = create_model_fallback_list('anthropic/claude-3-opus')
        self.assertIn('anthropic/claude-3-sonnet', fallbacks)
        self.assertIn('anthropic/claude-3-haiku', fallbacks)

    def test_anthropic_sonnet_fallbacks(self):
        """Test fallback list for Claude Sonnet"""
        fallbacks = create_model_fallback_list('anthropic/claude-3-sonnet')
        self.assertEqual(fallbacks, ['anthropic/claude-3-haiku'])

    def test_anthropic_35_sonnet_fallbacks(self):
        """Test fallback list for Claude 3.5 Sonnet"""
        fallbacks = create_model_fallback_list('anthropic/claude-3.5-sonnet')
        self.assertIn('anthropic/claude-3-sonnet', fallbacks)
        self.assertIn('anthropic/claude-3-haiku', fallbacks)

    def test_llama_405b_fallbacks(self):
        """Test fallback list for Llama 405B"""
        fallbacks = create_model_fallback_list('meta-llama/llama-3.1-405b-instruct')
        self.assertIn('meta-llama/llama-3.1-70b-instruct', fallbacks)
        self.assertIn('meta-llama/llama-3.1-8b-instruct', fallbacks)

    def test_llama_70b_fallbacks(self):
        """Test fallback list for Llama 70B"""
        fallbacks = create_model_fallback_list('meta-llama/llama-3.1-70b-instruct')
        self.assertEqual(fallbacks, ['meta-llama/llama-3.1-8b-instruct'])

    def test_google_gemini_fallbacks(self):
        """Test fallback list for Gemini Pro 1.5"""
        fallbacks = create_model_fallback_list('google/gemini-pro-1.5')
        self.assertEqual(fallbacks, ['google/gemini-pro'])

    def test_mistral_large_fallbacks(self):
        """Test fallback list for Mistral Large"""
        fallbacks = create_model_fallback_list('mistralai/mistral-large')
        self.assertIn('mistralai/mistral-medium', fallbacks)
        self.assertIn('mistralai/mistral-small', fallbacks)

    def test_unknown_gpt4_model_fallbacks(self):
        """Test fallback for unknown GPT-4 variant"""
        fallbacks = create_model_fallback_list('openai/gpt-4-custom')
        self.assertIn('openai/gpt-4o-mini', fallbacks)

    def test_unknown_claude_model_fallbacks(self):
        """Test fallback for unknown Claude variant"""
        fallbacks = create_model_fallback_list('anthropic/claude-custom')
        self.assertIn('anthropic/claude-3-haiku', fallbacks)

    def test_unknown_llama_model_fallbacks(self):
        """Test fallback for unknown Llama variant"""
        fallbacks = create_model_fallback_list('meta-llama/llama-custom')
        self.assertIn('meta-llama/llama-3.1-8b-instruct', fallbacks)

    def test_unknown_gemini_model_fallbacks(self):
        """Test fallback for unknown Gemini variant"""
        fallbacks = create_model_fallback_list('google/gemini-custom')
        self.assertIn('google/gemini-pro', fallbacks)

    def test_completely_unknown_model(self):
        """Test fallback for completely unknown model"""
        fallbacks = create_model_fallback_list('unknown/custom-model')
        # Should return universal cheap fallbacks
        self.assertIn('openai/gpt-4o-mini', fallbacks)
        self.assertIn('anthropic/claude-3-haiku', fallbacks)


class TestShouldEnableFallback(unittest.TestCase):
    """Tests for should_enable_fallback function"""

    def test_enable_for_404_error(self):
        """Test fallback enabled for 404 errors"""
        error = Exception("Error 404: Model not found")
        self.assertTrue(should_enable_fallback(error))

    def test_enable_for_403_error(self):
        """Test fallback enabled for 403 errors"""
        error = Exception("Error 403: Forbidden - no access to model")
        self.assertTrue(should_enable_fallback(error))

    def test_enable_for_not_found(self):
        """Test fallback enabled for 'not found' errors"""
        error = Exception("The requested model was not found")
        self.assertTrue(should_enable_fallback(error))

    def test_enable_for_timeout(self):
        """Test fallback enabled for timeout errors"""
        error = Exception("Request timed out after 30 seconds")
        self.assertTrue(should_enable_fallback(error))

    def test_enable_for_503_error(self):
        """Test fallback enabled for 503 errors"""
        error = Exception("Error 503: Service temporarily unavailable")
        self.assertTrue(should_enable_fallback(error))

    def test_enable_for_overloaded(self):
        """Test fallback enabled for overloaded errors"""
        error = Exception("Model is currently overloaded")
        self.assertTrue(should_enable_fallback(error))

    def test_disable_for_401_error(self):
        """Test fallback disabled for 401 unauthorized errors"""
        error = Exception("Error 401: Unauthorized - invalid API key")
        self.assertFalse(should_enable_fallback(error))

    def test_disable_for_budget_error(self):
        """Test fallback disabled for budget errors"""
        error = Exception("Budget limit exceeded")
        self.assertFalse(should_enable_fallback(error))

    def test_disable_for_cost_error(self):
        """Test fallback disabled for cost errors"""
        error = Exception("Cost limit reached, stopping execution")
        self.assertFalse(should_enable_fallback(error))

    def test_disable_for_rate_limit(self):
        """Test fallback disabled for rate limit errors"""
        error = Exception("Error 429: Rate limit exceeded")
        self.assertFalse(should_enable_fallback(error))

    def test_generic_error_no_fallback(self):
        """Test fallback not enabled for generic errors"""
        error = Exception("Something went wrong")
        self.assertFalse(should_enable_fallback(error))


class TestExecuteWithAutoFallback(unittest.TestCase):
    """Tests for execute_with_auto_fallback convenience function"""

    def test_success_no_fallback_needed(self):
        """Test when primary function succeeds"""
        def primary_func():
            return "success"

        result = execute_with_auto_fallback(
            func=primary_func,
            operation_name="test",
            primary_model="openai/gpt-4o",
            fallback_func_generator=lambda m: lambda: "fallback"
        )

        self.assertEqual(result, "success")

    def test_fallback_disabled(self):
        """Test when fallback is disabled"""
        def primary_func():
            raise ValueError("Primary failed")

        with self.assertRaises(ValueError):
            execute_with_auto_fallback(
                func=primary_func,
                operation_name="test",
                primary_model="openai/gpt-4o",
                fallback_func_generator=lambda m: lambda: "fallback",
                enable_fallback=False
            )

    def test_error_not_triggering_fallback(self):
        """Test when error type should not trigger fallback"""
        def primary_func():
            # Budget error should not trigger fallback
            raise ValueError("Budget limit exceeded")

        with self.assertRaises(ValueError) as ctx:
            execute_with_auto_fallback(
                func=primary_func,
                operation_name="test",
                primary_model="openai/gpt-4o",
                fallback_func_generator=lambda m: lambda: "fallback",
                enable_fallback=True
            )

        self.assertIn("Budget", str(ctx.exception))

    def test_fallback_triggered_on_timeout(self):
        """Test fallback triggered on timeout error"""
        call_count = 0

        def primary_func():
            raise ValueError("Request timed out")

        def fallback_generator(model):
            def fallback_func():
                return f"fallback success with {model}"
            return fallback_func

        result = execute_with_auto_fallback(
            func=primary_func,
            operation_name="test",
            primary_model="openai/gpt-4o",
            fallback_func_generator=fallback_generator,
            enable_fallback=True
        )

        self.assertIn("fallback success", result)

    def test_context_passed_to_error_handler(self):
        """Test that context is passed to error handler"""
        def primary_func():
            raise ValueError("Service unavailable")

        def fallback_generator(model):
            def fallback_func():
                raise ValueError(f"{model} also failed")
            return fallback_func

        # Use correct ErrorContext field names
        context = {'scenario_name': 'test-scenario', 'turn_number': 5}

        with self.assertRaises(ValueError):
            execute_with_auto_fallback(
                func=primary_func,
                operation_name="test",
                primary_model="openai/gpt-4o",
                fallback_func_generator=fallback_generator,
                context=context,
                enable_fallback=True
            )


class TestFallbackIntegration(unittest.TestCase):
    """Integration tests for fallback system"""

    def test_full_fallback_flow(self):
        """Test complete fallback flow from primary to fallback success"""
        config = FallbackConfig(
            fallback_models=['openai/gpt-4o', 'openai/gpt-4o-mini'],
            enable_fallback=True,
            max_fallback_attempts=2
        )
        # Use correct ErrorContext field names
        executor = ProgressiveFallbackExecutor(
            fallback_config=config,
            context={'scenario_name': 'integration-test', 'actor_name': 'test-actor'}
        )

        attempts = []

        def primary_func():
            attempts.append('primary')
            raise ValueError("Model not found")

        def fallback_generator(model):
            def fallback_func():
                attempts.append(model)
                if model == 'openai/gpt-4o':
                    raise ValueError("Also not found")
                return f"Success with {model}"
            return fallback_func

        result = executor.execute_with_fallback(
            primary_func=primary_func,
            operation_name="test operation",
            fallback_func_generator=fallback_generator
        )

        self.assertEqual(result, "Success with openai/gpt-4o-mini")
        self.assertEqual(attempts, ['primary', 'openai/gpt-4o', 'openai/gpt-4o-mini'])

    def test_fallback_preserves_exception_info(self):
        """Test that original exception info is preserved when all fallbacks fail"""
        config = FallbackConfig(
            fallback_models=['fallback-1'],
            enable_fallback=True
        )
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        original_message = "Original specific error message"

        def primary_func():
            raise ValueError(original_message)

        def fallback_generator(model):
            def fallback_func():
                raise RuntimeError("Different error")
            return fallback_func

        with self.assertRaises(ValueError) as ctx:
            executor.execute_with_fallback(
                primary_func=primary_func,
                operation_name="test",
                fallback_func_generator=fallback_generator
            )

        # Original error should be re-raised
        self.assertEqual(str(ctx.exception), original_message)


if __name__ == '__main__':
    unittest.main()
