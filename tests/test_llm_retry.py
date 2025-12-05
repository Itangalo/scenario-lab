import pytest
import httpx
from unittest.mock import MagicMock, patch
from scenario_lab.llm import LLMClient, LLMError

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("Error", request=None, response=self)

def test_llm_client_network_error_retry():
    """
    Test that LLMClient retries on transient network errors (httpx.NetworkError).
    Currently, this test is expected to FAIL or behave incorrectly until the fix is implemented.
    We want to ensure that a temporary network glitch doesn't cause immediate failure.
    """
    client = LLMClient(api_key="fake_key", model="test/model")

    # Mock the post method
    with patch("httpx.Client.post") as mock_post:
        # Configure the mock to raise a NetworkError on the first call, 
        # then succeed on the second call.
        # "Peer closed connection" is often a RemoteProtocolError or similar, which inherits from NetworkError
        mock_post.side_effect = [
            httpx.ReadError("Peer closed connection"),  # Fail 1st
            MockResponse(
                json_data={
                    "choices": [{"message": {"content": "Success after retry"}}]
                }
            )  # Succeed 2nd
        ]

        # Attempt to complete
        # BEFORE FIX: This will likely raise LLMError because it won't retry on ReadError
        # AFTER FIX: This should succeed and return "Success after retry"
        try:
            response = client.complete("System", "User")
            assert response.content == "Success after retry"
            print("\nSUCCESS: Client retried and recovered from network error.")
        except LLMError as e:
            print(f"\nFAILURE (Expected before fix): Client failed to retry. Error: {e}")
            raise e
        except Exception as e:
            print(f"\nUNEXPECTED ERROR: {e}")
            raise e
            
        # Verify it was called twice (initial + retry)
        assert mock_post.call_count == 2
