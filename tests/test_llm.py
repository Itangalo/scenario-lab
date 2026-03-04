import pytest
import httpx
import os
import json
from unittest.mock import MagicMock, patch
from scenario_lab.llm import LLMClient, LLMError, LLMParseError, LLMResponse

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("Error", request=None, response=self)

def test_llm_client_init_missing_key():
    """Test LLMClient initialization fails without API key."""
    # Ensure env var is cleared
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY not set"):
            LLMClient()

def test_llm_client_init_with_key():
    """Test LLMClient initialization with explicit key."""
    client = LLMClient(api_key="test_key")
    assert client.api_key == "test_key"

def test_llm_client_network_error_retry():
    """
    Test that LLMClient retries on transient network errors (httpx.NetworkError).
    """
    client = LLMClient(api_key="fake_key", model="test/model")

    # Mock the post method
    with patch("httpx.Client.post") as mock_post:
        # Configure: Fail 1st (network error), Succeed 2nd
        mock_post.side_effect = [
            httpx.ReadError("Peer closed connection"),
            MockResponse(
                json_data={
                    "choices": [{"message": {"content": "Success after retry"}}]
                }
            )
        ]

        response = client.complete("System", "User")
        assert response.content == "Success after retry"
        
        # Verify it was called twice (initial + retry)
        assert mock_post.call_count == 2

def test_llm_response_parsing():
    """Test LLMResponse parsing methods."""
    
    # 1. Extract JSON from code block
    resp = LLMResponse(content='Here is the json:\n```json\n{"key": "value"}\n```', raw_response={})
    assert resp.extract_json() == {"key": "value"}
    
    # 2. Extract JSON from raw content
    resp = LLMResponse(content='{"key": "value"}', raw_response={})
    assert resp.extract_json() == {"key": "value"}
    
    # 3. Extract JSON array
    resp = LLMResponse(content='```json\n[{"id": "1"}]\n```', raw_response={})
    assert resp.extract_json_array() == [{"id": "1"}]
    
    # 4. Fail on invalid JSON
    resp = LLMResponse(content='Not json', raw_response={})
    with pytest.raises(json.JSONDecodeError):
        resp.extract_json()

def test_extract_metrics_and_narrative():
    """Test extracting metrics, narrative, and notepad."""
    
    content = """
## Metrics
```json
{"metric1": 10}
```

## Narrative
This is the narrative.

## Notepad
This is the notepad.
"""
    resp = LLMResponse(content=content, raw_response={})
    metrics, narrative, notepad = resp.extract_metrics_and_narrative()
    
    assert metrics == {"metric1": 10}
    assert narrative == "This is the narrative."
    assert notepad == "This is the notepad."

def test_extract_metrics_malformed():
    """Test extraction failure when metrics missing."""
    resp = LLMResponse(content="No metrics here", raw_response={})
    with pytest.raises(LLMParseError, match="Could not find metrics"):
        resp.extract_metrics_and_narrative()


def test_get_finish_reason():
    """LLMResponse should expose finish_reason when present."""
    resp = LLMResponse(
        content="x",
        raw_response={"choices": [{"finish_reason": "length"}]},
    )
    assert resp.get_finish_reason() == "length"
