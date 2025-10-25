"""
API Utilities - Robust API call handling with retry logic

Supports multiple LLM backends:
- OpenRouter (cloud API)
- Ollama (local models)
- llama.cpp (local models)
"""
import time
import requests
import os
from typing import Callable, Any, Optional


def api_call_with_retry(
    api_func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retryable_status_codes: tuple = (502, 503, 504, 429)
) -> Any:
    """
    Execute an API call with exponential backoff retry logic

    Args:
        api_func: Function that makes the API call (should return requests.Response)
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        backoff_factor: Multiplier for delay after each retry
        retryable_status_codes: HTTP status codes that should trigger retries

    Returns:
        The result from api_func

    Raises:
        requests.exceptions.HTTPError: If all retries fail or non-retryable error
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            result = api_func()

            # If it's a requests.Response object, check status
            if isinstance(result, requests.Response):
                result.raise_for_status()

            return result

        except requests.exceptions.HTTPError as e:
            last_exception = e

            # Check if this is a retryable error
            if e.response is not None and e.response.status_code in retryable_status_codes:
                if attempt < max_retries:
                    # Retryable error - wait and retry
                    print(f"⚠️  API error {e.response.status_code}: {str(e)}")
                    print(f"   Retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
                    continue
                else:
                    # Out of retries
                    print(f"❌ API error {e.response.status_code} after {max_retries} retries")
                    raise
            else:
                # Non-retryable error - fail immediately
                raise

        except requests.exceptions.RequestException as e:
            # Network errors, connection errors, etc.
            last_exception = e

            if attempt < max_retries:
                print(f"⚠️  Network error: {str(e)}")
                print(f"   Retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)
                continue
            else:
                print(f"❌ Network error after {max_retries} retries")
                raise

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


def make_openrouter_call(
    url: str,
    headers: dict,
    payload: dict,
    max_retries: int = 3
) -> requests.Response:
    """
    Make an OpenRouter API call with automatic retry logic

    Args:
        url: API endpoint URL
        headers: Request headers
        payload: Request payload
        max_retries: Maximum number of retry attempts

    Returns:
        requests.Response object with successful response

    Raises:
        requests.exceptions.HTTPError: If all retries fail
    """
    def api_call():
        return requests.post(url, headers=headers, json=payload, timeout=120)

    return api_call_with_retry(api_call, max_retries=max_retries)


def is_local_model(model: str) -> bool:
    """
    Check if a model string indicates a local model

    Args:
        model: Model identifier (e.g., "ollama/llama3.1:70b", "openai/gpt-4o-mini")

    Returns:
        True if model is local, False otherwise
    """
    return model.startswith('ollama/') or model.startswith('local/')


def make_ollama_call(
    model: str,
    messages: list,
    max_retries: int = 3,
    base_url: Optional[str] = None
) -> dict:
    """
    Make a call to local Ollama instance

    Args:
        model: Ollama model name (e.g., "llama3.1:70b", "qwen2.5:72b")
        messages: List of message dicts with 'role' and 'content'
        max_retries: Maximum number of retry attempts
        base_url: Ollama API URL (default: http://localhost:11434)

    Returns:
        Response dict with 'message' and 'usage' keys

    Raises:
        requests.exceptions.HTTPError: If all retries fail
    """
    if base_url is None:
        base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')

    url = f"{base_url}/v1/chat/completions"

    payload = {
        "model": model,
        "messages": messages
    }

    def api_call():
        return requests.post(url, json=payload, timeout=300)

    response = api_call_with_retry(api_call, max_retries=max_retries)
    return response.json()


def make_llm_call(
    model: str,
    messages: list,
    api_key: Optional[str] = None,
    max_retries: int = 3
) -> tuple[str, int]:
    """
    Make an LLM API call using the appropriate backend

    Automatically routes to:
    - Ollama for models starting with "ollama/" or "local/"
    - OpenRouter for all other models

    Args:
        model: Model identifier (e.g., "openai/gpt-4o-mini", "ollama/llama3.1:70b")
        messages: List of message dicts with 'role' and 'content'
        api_key: API key for cloud providers (not needed for local)
        max_retries: Maximum number of retry attempts

    Returns:
        Tuple of (response_text, tokens_used)

    Raises:
        requests.exceptions.HTTPError: If all retries fail
    """
    if is_local_model(model):
        # Strip the "ollama/" or "local/" prefix
        local_model = model.split('/', 1)[1]

        result = make_ollama_call(local_model, messages, max_retries)

        response_text = result['choices'][0]['message']['content']
        tokens_used = result.get('usage', {}).get('total_tokens', 0)

        return response_text, tokens_used

    else:
        # Use OpenRouter for cloud models
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages
        }

        response = make_openrouter_call(url, headers, payload, max_retries)
        data = response.json()

        response_text = data['choices'][0]['message']['content']
        tokens_used = data.get('usage', {}).get('total_tokens', 0)

        return response_text, tokens_used
