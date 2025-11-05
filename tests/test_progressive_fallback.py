"""
Tests for progressive_fallback.py - Smart fallback strategies
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from progressive_fallback import (
    FallbackConfig,
    ProgressiveFallbackExecutor,
    create_model_fallback_list,
    should_enable_fallback,
    execute_with_auto_fallback
)
from error_handler import ErrorHandler


class TestFallbackConfig:
    """Test FallbackConfig"""

    def test_fallback_config_defaults(self):
        """Test default FallbackConfig values"""
        config = FallbackConfig()

        assert config.fallback_models is None
        assert config.enable_fallback is True
        assert config.max_fallback_attempts == 2
        assert config.save_state_on_error is True

    def test_fallback_config_custom(self):
        """Test custom FallbackConfig"""
        config = FallbackConfig(
            fallback_models=['model1', 'model2'],
            enable_fallback=False,
            max_fallback_attempts=3
        )

        assert config.fallback_models == ['model1', 'model2']
        assert config.enable_fallback is False
        assert config.max_fallback_attempts == 3


class TestCreateModelFallbackList:
    """Test creating smart fallback model lists"""

    def test_openai_gpt4_fallback(self):
        """Test fallback for GPT-4"""
        fallbacks = create_model_fallback_list('openai/gpt-4')

        assert 'openai/gpt-4o' in fallbacks
        assert 'openai/gpt-4o-mini' in fallbacks

    def test_openai_gpt4o_fallback(self):
        """Test fallback for GPT-4o"""
        fallbacks = create_model_fallback_list('openai/gpt-4o')

        assert 'openai/gpt-4o-mini' in fallbacks
        assert len(fallbacks) == 1

    def test_anthropic_opus_fallback(self):
        """Test fallback for Claude Opus"""
        fallbacks = create_model_fallback_list('anthropic/claude-3-opus')

        assert 'anthropic/claude-3-sonnet' in fallbacks
        assert 'anthropic/claude-3-haiku' in fallbacks

    def test_anthropic_sonnet_fallback(self):
        """Test fallback for Claude Sonnet"""
        fallbacks = create_model_fallback_list('anthropic/claude-3-sonnet')

        assert 'anthropic/claude-3-haiku' in fallbacks

    def test_meta_llama_405b_fallback(self):
        """Test fallback for Llama 405B"""
        fallbacks = create_model_fallback_list('meta-llama/llama-3.1-405b-instruct')

        assert 'meta-llama/llama-3.1-70b-instruct' in fallbacks
        assert 'meta-llama/llama-3.1-8b-instruct' in fallbacks

    def test_unknown_gpt4_model_fallback(self):
        """Test fallback for unknown GPT-4 variant"""
        fallbacks = create_model_fallback_list('openai/gpt-4-custom')

        assert 'openai/gpt-4o-mini' in fallbacks

    def test_unknown_claude_model_fallback(self):
        """Test fallback for unknown Claude variant"""
        fallbacks = create_model_fallback_list('anthropic/claude-custom')

        assert 'anthropic/claude-3-haiku' in fallbacks

    def test_completely_unknown_model_fallback(self):
        """Test fallback for completely unknown model"""
        fallbacks = create_model_fallback_list('some-provider/unknown-model')

        # Should provide universal cheap fallbacks
        assert 'openai/gpt-4o-mini' in fallbacks or 'anthropic/claude-3-haiku' in fallbacks


class TestShouldEnableFallback:
    """Test logic for determining when to enable fallback"""

    def test_enable_for_404_error(self):
        """Test enabling fallback for 404 (not found) errors"""
        error = Exception("404 Model not found")
        assert should_enable_fallback(error) is True

    def test_enable_for_403_error(self):
        """Test enabling fallback for 403 (forbidden) errors"""
        error = Exception("403 Forbidden - no access to model")
        assert should_enable_fallback(error) is True

    def test_enable_for_timeout(self):
        """Test enabling fallback for timeout errors"""
        error = Exception("Request timed out")
        assert should_enable_fallback(error) is True

    def test_enable_for_503_error(self):
        """Test enabling fallback for 503 (service unavailable) errors"""
        error = Exception("503 Service unavailable")
        assert should_enable_fallback(error) is True

    def test_disable_for_401_error(self):
        """Test disabling fallback for 401 (unauthorized) errors"""
        error = Exception("401 unauthorized - invalid API key")
        assert should_enable_fallback(error) is False

    def test_disable_for_budget_error(self):
        """Test disabling fallback for budget errors"""
        error = Exception("Budget limit exceeded")
        assert should_enable_fallback(error) is False

    def test_disable_for_rate_limit(self):
        """Test disabling fallback for 429 rate limit errors"""
        error = Exception("429 rate limit exceeded")
        assert should_enable_fallback(error) is False


class TestProgressiveFallbackExecutor:
    """Test ProgressiveFallbackExecutor"""

    def test_executor_creation(self):
        """Test creating a ProgressiveFallbackExecutor"""
        config = FallbackConfig(fallback_models=['model1', 'model2'])
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        assert executor.fallback_config == config
        assert executor.error_handler is not None
        assert executor.context == {}

    def test_executor_with_context(self):
        """Test creating executor with context"""
        context = {'scenario': 'test', 'turn': 5}
        executor = ProgressiveFallbackExecutor(context=context)

        assert executor.context == context

    def test_successful_primary_execution(self):
        """Test successful execution on first try"""
        executor = ProgressiveFallbackExecutor()

        def primary_func():
            return "success"

        result = executor.execute_with_fallback(
            primary_func,
            "Test operation"
        )

        assert result == "success"

    def test_fallback_when_primary_fails(self):
        """Test fallback when primary function fails"""
        config = FallbackConfig(
            fallback_models=['model1', 'model2'],
            enable_fallback=True
        )
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        # Primary fails, first fallback succeeds
        def primary_func():
            raise Exception("404 Model not found")

        def fallback_gen(model):
            if model == 'model1':
                return lambda: "fallback success"
            else:
                return lambda: "should not reach"

        result = executor.execute_with_fallback(
            primary_func,
            "Test operation",
            fallback_func_generator=fallback_gen
        )

        assert result == "fallback success"

    def test_all_fallbacks_fail(self):
        """Test when all fallbacks fail"""
        config = FallbackConfig(
            fallback_models=['model1', 'model2'],
            enable_fallback=True
        )
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        def primary_func():
            raise ValueError("Primary failed")

        def fallback_gen(model):
            return lambda: (_ for _ in ()).throw(ValueError(f"Fallback {model} failed"))

        # Capture stderr to avoid polluting test output
        import sys
        from io import StringIO
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        with pytest.raises(ValueError, match="Primary failed"):
            executor.execute_with_fallback(
                primary_func,
                "Test operation",
                fallback_func_generator=fallback_gen
            )

        sys.stderr = old_stderr

    def test_fallback_disabled(self):
        """Test that fallback is skipped when disabled"""
        config = FallbackConfig(
            fallback_models=['model1', 'model2'],
            enable_fallback=False
        )
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        def primary_func():
            raise ValueError("Primary failed")

        def fallback_gen(model):
            return lambda: "should not be called"

        # Capture stderr
        import sys
        from io import StringIO
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        with pytest.raises(ValueError, match="Primary failed"):
            executor.execute_with_fallback(
                primary_func,
                "Test operation",
                fallback_func_generator=fallback_gen
            )

        sys.stderr = old_stderr

    def test_max_fallback_attempts_respected(self):
        """Test that max_fallback_attempts is respected"""
        config = FallbackConfig(
            fallback_models=['model1', 'model2', 'model3', 'model4'],
            enable_fallback=True,
            max_fallback_attempts=2  # Only try first 2
        )
        executor = ProgressiveFallbackExecutor(fallback_config=config)

        attempts = []

        def primary_func():
            raise Exception("404 Model not found")

        def fallback_gen(model):
            def fallback():
                attempts.append(model)
                raise Exception(f"{model} failed")
            return fallback

        # Capture stderr
        import sys
        from io import StringIO
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        with pytest.raises(Exception):
            executor.execute_with_fallback(
                primary_func,
                "Test operation",
                fallback_func_generator=fallback_gen
            )

        sys.stderr = old_stderr

        # Should only try first 2 fallback models
        assert len(attempts) == 2
        assert attempts == ['model1', 'model2']


class TestExecuteWithAutoFallback:
    """Test the convenience function execute_with_auto_fallback"""

    def test_auto_fallback_success(self):
        """Test successful execution without fallback"""
        def func():
            return "success"

        def fallback_gen(model):
            return lambda: "fallback"

        result = execute_with_auto_fallback(
            func,
            "Test operation",
            "openai/gpt-4",
            fallback_gen,
            enable_fallback=True
        )

        assert result == "success"

    def test_auto_fallback_disabled(self):
        """Test auto fallback when disabled"""
        def func():
            return "success"

        def fallback_gen(model):
            return lambda: "fallback"

        result = execute_with_auto_fallback(
            func,
            "Test operation",
            "openai/gpt-4",
            fallback_gen,
            enable_fallback=False
        )

        assert result == "success"

    def test_auto_fallback_triggers_on_404(self):
        """Test that auto fallback triggers on 404 errors"""
        attempts = []

        def func():
            attempts.append('primary')
            raise Exception("404 Model not found")

        def fallback_gen(model):
            def fallback():
                attempts.append(model)
                if model == 'openai/gpt-4o':
                    return "fallback success"
                raise Exception("Still failing")
            return fallback

        # Capture stderr
        import sys
        from io import StringIO
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        result = execute_with_auto_fallback(
            func,
            "Test operation",
            "openai/gpt-4",  # Will fallback to gpt-4o and gpt-4o-mini
            fallback_gen,
            enable_fallback=True
        )

        sys.stderr = old_stderr

        assert result == "fallback success"
        assert 'primary' in attempts
        assert 'openai/gpt-4o' in attempts

    def test_auto_fallback_no_trigger_on_auth_error(self):
        """Test that auto fallback doesn't trigger on auth errors"""
        def func():
            raise Exception("401 unauthorized")

        def fallback_gen(model):
            return lambda: "should not be called"

        # Capture stderr
        import sys
        from io import StringIO
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        with pytest.raises(Exception, match="401"):
            execute_with_auto_fallback(
                func,
                "Test operation",
                "openai/gpt-4",
                fallback_gen,
                enable_fallback=True
            )

        sys.stderr = old_stderr


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
