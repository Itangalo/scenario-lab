"""
Tests for API Client module

Tests LLM API calls, retry logic, connection pooling, and caching integration.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
import requests

from scenario_lab.utils.api_client import (
    LLMResponse,
    get_http_session,
    api_call_with_retry,
    is_local_model,
    make_ollama_call,
    make_openrouter_call,
    make_llm_call,
    make_llm_call_async,
)


class TestLLMResponse:
    """Tests for LLMResponse dataclass"""

    def test_create_response(self):
        """Test creating an LLM response"""
        response = LLMResponse(
            content="Hello world",
            tokens_used=50,
            input_tokens=20,
            output_tokens=30,
            model="openai/gpt-4o-mini",
            cached=False
        )

        assert response.content == "Hello world"
        assert response.tokens_used == 50
        assert response.input_tokens == 20
        assert response.output_tokens == 30
        assert response.model == "openai/gpt-4o-mini"
        assert response.cached is False

    def test_default_values(self):
        """Test default values for LLM response"""
        response = LLMResponse(content="Test", tokens_used=10)

        assert response.input_tokens == 0
        assert response.output_tokens == 0
        assert response.model == ""
        assert response.cached is False


class TestGetHttpSession:
    """Tests for get_http_session function"""

    def test_returns_session(self):
        """Test that get_http_session returns a requests.Session"""
        # Reset the global session
        import scenario_lab.utils.api_client as api
        api._http_session = None

        session = get_http_session()

        assert isinstance(session, requests.Session)

    def test_returns_same_session(self):
        """Test that get_http_session returns the same session (singleton)"""
        session1 = get_http_session()
        session2 = get_http_session()

        assert session1 is session2


class TestIsLocalModel:
    """Tests for is_local_model function"""

    def test_ollama_model_is_local(self):
        """Test that ollama models are identified as local"""
        assert is_local_model("ollama/llama3.1:70b") is True
        assert is_local_model("ollama/mistral") is True

    def test_local_prefix_is_local(self):
        """Test that local/ prefix models are identified as local"""
        assert is_local_model("local/my-model") is True

    def test_cloud_models_not_local(self):
        """Test that cloud models are not identified as local"""
        assert is_local_model("openai/gpt-4o") is False
        assert is_local_model("anthropic/claude-3-opus") is False
        assert is_local_model("google/gemini-pro") is False


class TestApiCallWithRetry:
    """Tests for api_call_with_retry function"""

    def test_successful_call_no_retry(self):
        """Test successful API call without retry"""
        mock_func = Mock(return_value="success")

        result = api_call_with_retry(mock_func)

        assert result == "success"
        mock_func.assert_called_once()

    def test_retry_on_500_error(self):
        """Test retry on 500 server error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)

        call_count = [0]

        def api_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise requests.exceptions.HTTPError(response=mock_response)
            return "success"

        result = api_call_with_retry(api_func, max_retries=3, initial_delay=0.01)

        assert result == "success"
        assert call_count[0] == 3

    def test_retry_on_429_rate_limit(self):
        """Test retry on 429 rate limit error"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {}
        mock_response.text = "Rate limited"

        call_count = [0]

        def api_func():
            call_count[0] += 1
            if call_count[0] < 2:
                error = requests.exceptions.HTTPError(response=mock_response)
                error.response = mock_response
                raise error
            return "success"

        result = api_call_with_retry(api_func, max_retries=3, initial_delay=0.01)

        assert result == "success"
        assert call_count[0] == 2

    def test_no_retry_on_401_unauthorized(self):
        """Test no retry on 401 unauthorized"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        def api_func():
            error = requests.exceptions.HTTPError(response=mock_response)
            error.response = mock_response
            raise error

        with pytest.raises(requests.exceptions.HTTPError):
            api_call_with_retry(api_func, max_retries=3, initial_delay=0.01)

    def test_respects_retry_after_header(self):
        """Test that Retry-After header is respected"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '0.05'}
        mock_response.text = "Rate limited"

        call_count = [0]

        def api_func():
            call_count[0] += 1
            if call_count[0] < 2:
                error = requests.exceptions.HTTPError(response=mock_response)
                error.response = mock_response
                raise error
            return "success"

        # This should use the Retry-After header value
        result = api_call_with_retry(api_func, max_retries=3, initial_delay=0.01)

        assert result == "success"

    def test_max_retries_exceeded(self):
        """Test that exception is raised when max retries exceeded"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"

        def api_func():
            error = requests.exceptions.HTTPError(response=mock_response)
            error.response = mock_response
            raise error

        with pytest.raises(requests.exceptions.HTTPError):
            api_call_with_retry(api_func, max_retries=2, initial_delay=0.01)

    def test_network_error_retry(self):
        """Test retry on network errors"""
        call_count = [0]

        def api_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise requests.exceptions.ConnectionError("Network error")
            return "success"

        result = api_call_with_retry(api_func, max_retries=3, initial_delay=0.01)

        assert result == "success"
        assert call_count[0] == 2

    def test_context_included_in_logs(self):
        """Test that context is included in error handling"""
        mock_func = Mock(return_value="success")
        context = {'actor': 'TestActor', 'turn': 1}

        result = api_call_with_retry(mock_func, context=context)

        assert result == "success"


class TestMakeOllamaCall:
    """Tests for make_ollama_call function"""

    @patch('scenario_lab.utils.api_client.get_http_session')
    def test_successful_call(self, mock_get_session):
        """Test successful Ollama API call"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Hello'}}],
            'usage': {'total_tokens': 50, 'prompt_tokens': 30, 'completion_tokens': 20}
        }
        mock_response.raise_for_status.return_value = None
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session

        result = make_ollama_call(
            model="llama3.1:70b",
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert 'choices' in result
        assert result['choices'][0]['message']['content'] == 'Hello'

    @patch('scenario_lab.utils.api_client.get_http_session')
    def test_uses_default_base_url(self, mock_get_session):
        """Test that default base URL is used"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {'choices': [{'message': {'content': 'Hi'}}]}
        mock_response.raise_for_status.return_value = None
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session

        make_ollama_call("model", [{"role": "user", "content": "Hi"}])

        call_args = mock_session.post.call_args
        assert 'localhost:11434' in call_args[0][0]


class TestMakeOpenrouterCall:
    """Tests for make_openrouter_call function"""

    @patch('scenario_lab.utils.api_client.get_http_session')
    def test_successful_call(self, mock_get_session):
        """Test successful OpenRouter API call"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Hello from GPT'}}],
            'usage': {'total_tokens': 100}
        }
        mock_response.raise_for_status.return_value = None
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session

        result = make_openrouter_call(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            api_key="test-api-key"
        )

        assert 'choices' in result

    @patch('scenario_lab.utils.api_client.get_http_session')
    def test_authorization_header_set(self, mock_get_session):
        """Test that authorization header is set correctly"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {'choices': [{'message': {'content': 'Hi'}}]}
        mock_response.raise_for_status.return_value = None
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session

        make_openrouter_call("model", [{"role": "user", "content": "Hi"}], "my-api-key")

        call_kwargs = mock_session.post.call_args[1]
        assert call_kwargs['headers']['Authorization'] == 'Bearer my-api-key'


class TestMakeLLMCall:
    """Tests for make_llm_call function"""

    @patch('scenario_lab.utils.api_client.get_global_cache')
    @patch('scenario_lab.utils.api_client.make_ollama_call')
    def test_routes_to_ollama_for_local_model(self, mock_ollama, mock_cache):
        """Test that local models are routed to Ollama"""
        mock_cache.return_value.get.return_value = None

        mock_ollama.return_value = {
            'choices': [{'message': {'content': 'Hello'}}],
            'usage': {'total_tokens': 50, 'prompt_tokens': 30, 'completion_tokens': 20}
        }

        response = make_llm_call(
            model="ollama/llama3.1:70b",
            messages=[{"role": "user", "content": "Hi"}]
        )

        mock_ollama.assert_called_once()
        assert response.content == "Hello"

    @patch('scenario_lab.utils.api_client.get_global_cache')
    @patch('scenario_lab.utils.api_client.make_openrouter_call')
    def test_routes_to_openrouter_for_cloud_model(self, mock_openrouter, mock_cache):
        """Test that cloud models are routed to OpenRouter"""
        mock_cache.return_value.get.return_value = None

        mock_openrouter.return_value = {
            'choices': [{'message': {'content': 'Hello from cloud'}}],
            'usage': {'total_tokens': 100, 'prompt_tokens': 60, 'completion_tokens': 40}
        }

        response = make_llm_call(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            api_key="test-key"
        )

        mock_openrouter.assert_called_once()
        assert response.content == "Hello from cloud"

    @patch('scenario_lab.utils.api_client.get_global_cache')
    def test_returns_cached_response(self, mock_cache):
        """Test that cached responses are returned"""
        mock_entry = Mock()
        mock_entry.response = "Cached response"
        mock_entry.tokens_used = 50
        mock_entry.input_tokens = 30
        mock_entry.output_tokens = 20
        mock_entry.model = "openai/gpt-4o-mini"
        mock_cache.return_value.get.return_value = mock_entry

        response = make_llm_call(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}]
        )

        assert response.content == "Cached response"
        assert response.cached is True

    @patch('scenario_lab.utils.api_client.get_global_cache')
    @patch('scenario_lab.utils.api_client.make_openrouter_call')
    def test_stores_response_in_cache(self, mock_openrouter, mock_cache):
        """Test that responses are stored in cache"""
        mock_cache_instance = Mock()
        mock_cache_instance.get.return_value = None
        mock_cache.return_value = mock_cache_instance

        mock_openrouter.return_value = {
            'choices': [{'message': {'content': 'New response'}}],
            'usage': {'total_tokens': 100}
        }

        make_llm_call(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            api_key="test-key"
        )

        mock_cache_instance.put.assert_called_once()

    @patch('scenario_lab.utils.api_client.get_global_cache')
    @patch('scenario_lab.utils.api_client.make_openrouter_call')
    def test_cache_disabled(self, mock_openrouter, mock_cache):
        """Test that cache can be disabled"""
        mock_openrouter.return_value = {
            'choices': [{'message': {'content': 'Response'}}],
            'usage': {'total_tokens': 50}
        }

        response = make_llm_call(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            api_key="test-key",
            use_cache=False
        )

        mock_cache.assert_not_called()
        assert response.cached is False

    def test_raises_error_without_api_key(self):
        """Test that missing API key raises error for cloud models"""
        import os
        old_key = os.environ.pop('OPENROUTER_API_KEY', None)

        try:
            with pytest.raises(ValueError, match="API key required"):
                make_llm_call(
                    model="openai/gpt-4o-mini",
                    messages=[{"role": "user", "content": "Hi"}],
                    use_cache=False
                )
        finally:
            if old_key:
                os.environ['OPENROUTER_API_KEY'] = old_key


class TestMakeLLMCallAsync:
    """Tests for make_llm_call_async function"""

    @pytest.mark.asyncio
    @patch('scenario_lab.utils.api_client.make_llm_call')
    async def test_async_call_wraps_sync(self, mock_sync):
        """Test that async call wraps sync call"""
        mock_sync.return_value = LLMResponse(
            content="Async response",
            tokens_used=50
        )

        response = await make_llm_call_async(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            api_key="test-key"
        )

        assert response.content == "Async response"
        mock_sync.assert_called_once()


class TestLLMResponseTokenEstimation:
    """Tests for token estimation when not provided by API"""

    @patch('scenario_lab.utils.api_client.get_global_cache')
    @patch('scenario_lab.utils.api_client.make_openrouter_call')
    def test_estimates_tokens_when_not_provided(self, mock_openrouter, mock_cache):
        """Test that tokens are estimated when API doesn't provide breakdown"""
        mock_cache.return_value.get.return_value = None

        # Response with only total_tokens
        mock_openrouter.return_value = {
            'choices': [{'message': {'content': 'Response'}}],
            'usage': {'total_tokens': 100}
        }

        response = make_llm_call(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            api_key="test-key"
        )

        # Should estimate 70% input, 30% output
        assert response.input_tokens == 70
        assert response.output_tokens == 30
