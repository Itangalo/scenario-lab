"""
Tests for API error handling and retry logic
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api_utils import api_call_with_retry, make_llm_call


class TestAPIRetryLogic(unittest.TestCase):
    """Test exponential backoff and retry logic"""

    @patch('api_utils.time.sleep')  # Mock sleep to speed up tests
    def test_successful_call_no_retry(self, mock_sleep):
        """Test that successful calls don't retry"""
        mock_func = Mock(return_value="success")

        result = api_call_with_retry(mock_func, max_retries=3)

        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 1)
        mock_sleep.assert_not_called()

    @patch('api_utils.time.sleep')
    def test_retry_on_502_error(self, mock_sleep):
        """Test retry on 502 Bad Gateway error"""
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.text = "Bad Gateway"
        mock_response.headers = {}

        error = requests.exceptions.HTTPError(response=mock_response)

        # First 2 calls fail with 502, third succeeds
        mock_func = Mock(side_effect=[error, error, "success"])

        result = api_call_with_retry(mock_func, max_retries=3, initial_delay=0.1)

        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('api_utils.time.sleep')
    def test_retry_on_503_error(self, mock_sleep):
        """Test retry on 503 Service Unavailable error"""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_response.headers = {}

        error = requests.exceptions.HTTPError(response=mock_response)

        # First call fails, second succeeds
        mock_func = Mock(side_effect=[error, "success"])

        result = api_call_with_retry(mock_func, max_retries=3, initial_delay=0.1)

        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 2)
        mock_sleep.assert_called_once()

    @patch('api_utils.time.sleep')
    def test_retry_on_429_rate_limit(self, mock_sleep):
        """Test retry on 429 Rate Limit error"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.headers = {}

        error = requests.exceptions.HTTPError(response=mock_response)

        # First call fails, second succeeds
        mock_func = Mock(side_effect=[error, "success"])

        result = api_call_with_retry(mock_func, max_retries=3, initial_delay=0.1)

        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 2)
        mock_sleep.assert_called_once()

    @patch('api_utils.time.sleep')
    def test_retry_after_header_respected(self, mock_sleep):
        """Test that Retry-After header is respected"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.headers = {'Retry-After': '5.0'}

        error = requests.exceptions.HTTPError(response=mock_response)

        # First call fails, second succeeds
        mock_func = Mock(side_effect=[error, "success"])

        result = api_call_with_retry(
            mock_func,
            max_retries=3,
            initial_delay=1.0,
            max_delay=10.0
        )

        self.assertEqual(result, "success")
        # Should sleep for 5.0s as specified in Retry-After header
        mock_sleep.assert_called_once_with(5.0)

    @patch('api_utils.time.sleep')
    def test_exponential_backoff(self, mock_sleep):
        """Test that delay increases exponentially"""
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.text = "Bad Gateway"
        mock_response.headers = {}

        error = requests.exceptions.HTTPError(response=mock_response)

        # All calls fail to test backoff progression
        mock_func = Mock(side_effect=[error, error, error, error])

        with self.assertRaises(requests.exceptions.HTTPError):
            api_call_with_retry(
                mock_func,
                max_retries=3,
                initial_delay=1.0,
                backoff_factor=2.0
            )

        # Should have slept with delays: 1.0, 2.0, 4.0
        self.assertEqual(mock_sleep.call_count, 3)
        calls = [call.args[0] for call in mock_sleep.call_args_list]
        self.assertEqual(calls, [1.0, 2.0, 4.0])

    @patch('api_utils.time.sleep')
    def test_max_retries_exhausted(self, mock_sleep):
        """Test that error is raised after max retries"""
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.text = "Bad Gateway"
        mock_response.headers = {}

        error = requests.exceptions.HTTPError(response=mock_response)

        # All calls fail
        mock_func = Mock(side_effect=error)

        with self.assertRaises(requests.exceptions.HTTPError):
            api_call_with_retry(mock_func, max_retries=2, initial_delay=0.1)

        # Should have tried 3 times (initial + 2 retries)
        self.assertEqual(mock_func.call_count, 3)

    @patch('api_utils.time.sleep')
    def test_non_retryable_error_fails_immediately(self, mock_sleep):
        """Test that non-retryable errors (4xx) fail immediately"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_response.headers = {}

        error = requests.exceptions.HTTPError(response=mock_response)

        mock_func = Mock(side_effect=error)

        with self.assertRaises(requests.exceptions.HTTPError):
            api_call_with_retry(mock_func, max_retries=3, initial_delay=0.1)

        # Should NOT retry - only called once
        self.assertEqual(mock_func.call_count, 1)
        mock_sleep.assert_not_called()

    @patch('api_utils.time.sleep')
    def test_network_error_retry(self, mock_sleep):
        """Test retry on network errors"""
        error = requests.exceptions.ConnectionError("Connection failed")

        # First call fails, second succeeds
        mock_func = Mock(side_effect=[error, "success"])

        result = api_call_with_retry(mock_func, max_retries=3, initial_delay=0.1)

        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 2)
        mock_sleep.assert_called_once()

    @patch('api_utils.time.sleep')
    def test_context_logging(self, mock_sleep):
        """Test that context is included in error logs"""
        mock_response = Mock()
        mock_response.status_code = 502
        mock_response.text = "Bad Gateway"
        mock_response.headers = {}

        error = requests.exceptions.HTTPError(response=mock_response)

        # First call fails, second succeeds
        mock_func = Mock(side_effect=[error, "success"])

        context = {'actor': 'TestActor', 'turn': 5, 'operation': 'decision'}

        # Capture logs
        with patch('api_utils.logger') as mock_logger:
            result = api_call_with_retry(
                mock_func,
                max_retries=3,
                initial_delay=0.1,
                context=context
            )

            # Verify context was included in warning log
            self.assertTrue(mock_logger.warning.called)
            warning_call = mock_logger.warning.call_args[0][0]
            self.assertIn('actor=TestActor', warning_call)
            self.assertIn('turn=5', warning_call)
            self.assertIn('operation=decision', warning_call)


class TestMakeLLMCallErrorHandling(unittest.TestCase):
    """Test make_llm_call error handling with context"""

    @patch('api_utils.make_openrouter_call')
    def test_context_passed_to_openrouter(self, mock_openrouter):
        """Test that context is passed through to API calls"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'total_tokens': 100}
        }
        mock_openrouter.return_value = mock_response

        context = {'actor': 'TestActor', 'turn': 3}

        result = make_llm_call(
            model='openai/gpt-4o-mini',
            messages=[{'role': 'user', 'content': 'test'}],
            api_key='test-key',
            context=context,
            use_cache=False  # Disable cache for testing
        )

        # Verify context was passed to make_openrouter_call
        self.assertTrue(mock_openrouter.called)
        call_kwargs = mock_openrouter.call_args[1]
        self.assertIn('context', call_kwargs)
        self.assertEqual(call_kwargs['context']['actor'], 'TestActor')
        self.assertEqual(call_kwargs['context']['turn'], 3)
        self.assertEqual(call_kwargs['context']['model'], 'openai/gpt-4o-mini')


if __name__ == '__main__':
    unittest.main()
