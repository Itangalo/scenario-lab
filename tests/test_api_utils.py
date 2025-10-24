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

from api_utils import api_call_with_retry, make_openrouter_call
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


if __name__ == '__main__':
    unittest.main()
