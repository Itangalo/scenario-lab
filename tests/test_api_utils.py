"""
Tests for api_utils module - API retry logic
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api_utils import api_call_with_retry, make_openrouter_call, is_local_model, make_llm_call
import requests


class TestApiCallWithRetry(unittest.TestCase):
    """Test api_call_with_retry function"""

    def _create_failing_response(self, status_code):
        """Helper to create a mock response that raises HTTPError"""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = status_code
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        return mock_response

    def _create_success_response(self):
        """Helper to create a successful mock response"""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        return mock_response

    def test_success_on_first_attempt(self):
        """Test successful API call on first attempt"""
        mock_response = self._create_success_response()
        api_func = Mock(return_value=mock_response)

        result = api_call_with_retry(api_func, max_retries=3)

        self.assertEqual(result, mock_response)
        self.assertEqual(api_func.call_count, 1)

    def test_retry_on_502_error(self):
        """Test retry logic for 502 Bad Gateway error"""
        fail_response = self._create_failing_response(502)
        success_response = self._create_success_response()

        call_count = [0]
        def api_func():
            call_count[0] += 1
            return fail_response if call_count[0] == 1 else success_response

        with patch('time.sleep'):
            result = api_call_with_retry(api_func, max_retries=3)

        self.assertEqual(result, success_response)
        self.assertEqual(call_count[0], 2)

    def test_retry_on_503_error(self):
        """Test retry logic for 503 Service Unavailable error"""
        fail_response = self._create_failing_response(503)
        success_response = self._create_success_response()

        call_count = [0]
        def api_func():
            call_count[0] += 1
            return fail_response if call_count[0] == 1 else success_response

        with patch('time.sleep'):
            result = api_call_with_retry(api_func, max_retries=3)

        self.assertEqual(result, success_response)
        self.assertEqual(call_count[0], 2)

    def test_retry_on_504_error(self):
        """Test retry logic for 504 Gateway Timeout error"""
        fail_response = self._create_failing_response(504)
        success_response = self._create_success_response()

        call_count = [0]
        def api_func():
            call_count[0] += 1
            return fail_response if call_count[0] == 1 else success_response

        with patch('time.sleep'):
            result = api_call_with_retry(api_func, max_retries=3)

        self.assertEqual(result, success_response)
        self.assertEqual(call_count[0], 2)

    def test_retry_on_429_rate_limit(self):
        """Test retry logic for 429 Rate Limit error"""
        fail_response = self._create_failing_response(429)
        success_response = self._create_success_response()

        call_count = [0]
        def api_func():
            call_count[0] += 1
            return fail_response if call_count[0] == 1 else success_response

        with patch('time.sleep'):
            result = api_call_with_retry(api_func, max_retries=3)

        self.assertEqual(result, success_response)
        self.assertEqual(call_count[0], 2)

    def test_no_retry_on_400_error(self):
        """Test that 400 errors (non-retryable) fail immediately"""
        fail_response = self._create_failing_response(400)
        api_func = Mock(return_value=fail_response)

        with self.assertRaises(requests.exceptions.HTTPError):
            api_call_with_retry(api_func, max_retries=3)

        # Should only try once for non-retryable errors
        self.assertEqual(api_func.call_count, 1)

    def test_no_retry_on_404_error(self):
        """Test that 404 errors (non-retryable) fail immediately"""
        fail_response = self._create_failing_response(404)
        api_func = Mock(return_value=fail_response)

        with self.assertRaises(requests.exceptions.HTTPError):
            api_call_with_retry(api_func, max_retries=3)

        self.assertEqual(api_func.call_count, 1)

    def test_max_retries_exceeded(self):
        """Test that function fails after max retries"""
        fail_response = self._create_failing_response(502)
        api_func = Mock(return_value=fail_response)

        with patch('time.sleep'):
            with self.assertRaises(requests.exceptions.HTTPError):
                api_call_with_retry(api_func, max_retries=2)

        # Should try initial attempt + 2 retries = 3 total
        self.assertEqual(api_func.call_count, 3)

    def test_exponential_backoff_delay(self):
        """Test that delays follow exponential backoff pattern"""
        fail_response = self._create_failing_response(502)
        api_func = Mock(return_value=fail_response)

        with patch('api_utils.time.sleep') as mock_sleep:
            try:
                api_call_with_retry(api_func, max_retries=3, initial_delay=1.0, backoff_factor=2.0)
            except requests.exceptions.HTTPError:
                pass

        # Check that sleep was called with increasing delays
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        self.assertEqual(len(sleep_calls), 3)
        self.assertEqual(sleep_calls[0], 1.0)
        self.assertEqual(sleep_calls[1], 2.0)
        self.assertEqual(sleep_calls[2], 4.0)

    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay"""
        fail_response = self._create_failing_response(502)
        api_func = Mock(return_value=fail_response)

        with patch('api_utils.time.sleep') as mock_sleep:
            try:
                api_call_with_retry(
                    api_func,
                    max_retries=5,
                    initial_delay=10.0,
                    max_delay=15.0,
                    backoff_factor=2.0
                )
            except requests.exceptions.HTTPError:
                pass

        # Check that no delay exceeds max_delay
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        for delay in sleep_calls:
            self.assertLessEqual(delay, 15.0)

    def test_network_error_retry(self):
        """Test retry on network connection errors"""
        success_response = self._create_success_response()

        call_count = [0]
        def api_func():
            call_count[0] += 1
            if call_count[0] == 1:
                raise requests.exceptions.ConnectionError("Network error")
            return success_response

        with patch('api_utils.time.sleep'):
            result = api_call_with_retry(api_func, max_retries=3)

        self.assertIsNotNone(result)
        self.assertEqual(call_count[0], 2)


class TestMakeOpenRouterCall(unittest.TestCase):
    """Test make_openrouter_call wrapper function"""

    def _create_success_response(self):
        """Helper to create a successful mock response"""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        return mock_response

    def _create_failing_response(self, status_code):
        """Helper to create a mock response that raises HTTPError"""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = status_code
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        return mock_response

    @patch('api_utils.requests.post')
    def test_successful_call(self, mock_post):
        """Test successful OpenRouter API call"""
        mock_response = self._create_success_response()
        mock_post.return_value = mock_response

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": "Bearer test_key"}
        payload = {"model": "test-model", "messages": []}

        result = make_openrouter_call(url, headers, payload, max_retries=3)

        self.assertEqual(result, mock_response)
        mock_post.assert_called_once_with(url, headers=headers, json=payload, timeout=120)

    @patch('api_utils.requests.post')
    def test_retry_on_failure(self, mock_post):
        """Test that OpenRouter call retries on failure"""
        fail_response = self._create_failing_response(502)
        success_response = self._create_success_response()

        mock_post.side_effect = [fail_response, success_response]

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": "Bearer test_key"}
        payload = {"model": "test-model", "messages": []}

        with patch('api_utils.time.sleep'):
            result = make_openrouter_call(url, headers, payload, max_retries=3)

        self.assertEqual(result, success_response)
        self.assertEqual(mock_post.call_count, 2)


class TestLocalLLMSupport(unittest.TestCase):
    """Test local LLM support functions"""

    def test_is_local_model_ollama(self):
        """Test detection of Ollama models"""
        self.assertTrue(is_local_model('ollama/llama3.1:70b'))
        self.assertTrue(is_local_model('ollama/qwen2.5:72b'))
        self.assertTrue(is_local_model('ollama/mistral'))

    def test_is_local_model_local_prefix(self):
        """Test detection of local/ prefixed models"""
        self.assertTrue(is_local_model('local/my-model'))
        self.assertTrue(is_local_model('local/custom-llm:latest'))

    def test_is_local_model_cloud(self):
        """Test that cloud models are not detected as local"""
        self.assertFalse(is_local_model('openai/gpt-4o-mini'))
        self.assertFalse(is_local_model('anthropic/claude-3-5-sonnet'))
        self.assertFalse(is_local_model('meta-llama/llama-3.1-70b-instruct'))

    @patch('api_utils.make_ollama_call')
    def test_make_llm_call_routes_to_ollama(self, mock_ollama):
        """Test that ollama/ models route to make_ollama_call"""
        mock_ollama.return_value = {
            'choices': [{'message': {'content': 'test response'}}],
            'usage': {'total_tokens': 100}
        }

        response, tokens = make_llm_call(
            model='ollama/llama3.1:70b',
            messages=[{'role': 'user', 'content': 'test'}]
        )

        self.assertEqual(response, 'test response')
        self.assertEqual(tokens, 100)
        mock_ollama.assert_called_once()
        # Check that the ollama/ prefix was stripped
        call_args = mock_ollama.call_args
        self.assertEqual(call_args[0][0], 'llama3.1:70b')

    @patch('api_utils.make_openrouter_call')
    def test_make_llm_call_routes_to_openrouter(self, mock_openrouter):
        """Test that cloud models route to OpenRouter"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'test response'}}],
            'usage': {'total_tokens': 150}
        }
        mock_openrouter.return_value = mock_response

        response, tokens = make_llm_call(
            model='openai/gpt-4o-mini',
            messages=[{'role': 'user', 'content': 'test'}],
            api_key='test-key'
        )

        self.assertEqual(response, 'test response')
        self.assertEqual(tokens, 150)
        mock_openrouter.assert_called_once()

    @patch('api_utils.make_ollama_call')
    def test_make_llm_call_local_prefix(self, mock_ollama):
        """Test that local/ prefix also routes to Ollama"""
        mock_ollama.return_value = {
            'choices': [{'message': {'content': 'local response'}}],
            'usage': {'total_tokens': 50}
        }

        response, tokens = make_llm_call(
            model='local/custom-model',
            messages=[{'role': 'user', 'content': 'test'}]
        )

        self.assertEqual(response, 'local response')
        self.assertEqual(tokens, 50)
        # Check prefix was stripped
        call_args = mock_ollama.call_args
        self.assertEqual(call_args[0][0], 'custom-model')


if __name__ == '__main__':
    unittest.main()
