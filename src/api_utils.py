"""
API Utilities - Robust API call handling with retry logic

Supports multiple LLM backends:
- OpenRouter (cloud API)
- Ollama (local models)
- llama.cpp (local models)

Features:
- Automatic retry with exponential backoff
- Response caching to reduce costs
- Connection pooling for better performance
"""
import time
import requests
import os
import logging
from typing import Callable, Any, Optional
from response_cache import get_global_cache, cached_llm_call

logger = logging.getLogger(__name__)

# Global session for connection pooling
_http_session: Optional[requests.Session] = None


def get_http_session() -> requests.Session:
    """
    Get or create global HTTP session with connection pooling

    Connection pooling improves performance by reusing TCP connections
    """
    global _http_session

    if _http_session is None:
        _http_session = requests.Session()

        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,  # Number of connection pools
            pool_maxsize=20,      # Connections per pool
            max_retries=0         # We handle retries manually
        )
        _http_session.mount('http://', adapter)
        _http_session.mount('https://', adapter)

        logger.info("HTTP session with connection pooling initialized")

    return _http_session


def api_call_with_retry(
    api_func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retryable_status_codes: tuple = (502, 503, 504, 429),
    context: Optional[dict] = None
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
        context: Optional dict with context info (e.g., {'actor': 'name', 'turn': 1})

    Returns:
        The result from api_func

    Raises:
        requests.exceptions.HTTPError: If all retries fail or non-retryable error
    """
    delay = initial_delay
    last_exception = None
    context_str = ""

    if context:
        context_parts = [f"{k}={v}" for k, v in context.items()]
        context_str = f" [{', '.join(context_parts)}]"

    for attempt in range(max_retries + 1):
        try:
            result = api_func()

            # If it's a requests.Response object, check status
            if isinstance(result, requests.Response):
                result.raise_for_status()

            # Log successful retry if this wasn't the first attempt
            if attempt > 0:
                logger.info(f"API call succeeded after {attempt} retries{context_str}")

            return result

        except requests.exceptions.HTTPError as e:
            last_exception = e
            status_code = e.response.status_code if e.response is not None else None

            # Log error details
            error_details = {
                'status_code': status_code,
                'attempt': attempt + 1,
                'max_retries': max_retries
            }
            if context:
                error_details.update(context)

            # Try to get response body for more context
            response_body = ""
            if e.response is not None:
                try:
                    response_body = e.response.text[:500]  # First 500 chars
                except:
                    pass

            # Check if this is a retryable error
            if status_code in retryable_status_codes:
                if attempt < max_retries:
                    # Check for Retry-After header (rate limiting)
                    retry_after = None
                    if e.response is not None and hasattr(e.response, 'headers'):
                        try:
                            if 'Retry-After' in e.response.headers:
                                retry_after = float(e.response.headers['Retry-After'])
                                delay = min(retry_after, max_delay)
                        except (ValueError, KeyError, TypeError):
                            pass

                    # Retryable error - wait and retry
                    logger.warning(
                        f"API error {status_code}{context_str}: {str(e)[:200]}. "
                        f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})"
                    )
                    logger.debug(f"Response body: {response_body}")

                    time.sleep(delay)

                    # Only increase delay if we didn't get Retry-After header
                    if retry_after is None:
                        delay = min(delay * backoff_factor, max_delay)

                    continue
                else:
                    # Out of retries
                    logger.error(
                        f"API error {status_code}{context_str} after {max_retries} retries. "
                        f"Error: {str(e)[:200]}"
                    )
                    logger.debug(f"Final response body: {response_body}")
                    raise
            else:
                # Non-retryable error - fail immediately
                logger.error(
                    f"Non-retryable API error {status_code}{context_str}: {str(e)[:200]}"
                )
                logger.debug(f"Response body: {response_body}")
                raise

        except requests.exceptions.RequestException as e:
            # Network errors, connection errors, etc.
            last_exception = e

            if attempt < max_retries:
                logger.warning(
                    f"Network error{context_str}: {str(e)[:200]}. "
                    f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)
                continue
            else:
                logger.error(
                    f"Network error{context_str} after {max_retries} retries: {str(e)[:200]}"
                )
                raise

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


def make_openrouter_call(
    url: str,
    headers: dict,
    payload: dict,
    max_retries: int = 3,
    context: Optional[dict] = None
) -> requests.Response:
    """
    Make an OpenRouter API call with automatic retry logic and connection pooling

    Args:
        url: API endpoint URL
        headers: Request headers
        payload: Request payload
        max_retries: Maximum number of retry attempts
        context: Optional dict with context info for error logging

    Returns:
        requests.Response object with successful response

    Raises:
        requests.exceptions.HTTPError: If all retries fail
    """
    session = get_http_session()

    def api_call():
        return session.post(url, headers=headers, json=payload, timeout=120)

    return api_call_with_retry(api_call, max_retries=max_retries, context=context)


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
    base_url: Optional[str] = None,
    context: Optional[dict] = None
) -> dict:
    """
    Make a call to local Ollama instance with connection pooling

    Args:
        model: Ollama model name (e.g., "llama3.1:70b", "qwen2.5:72b")
        messages: List of message dicts with 'role' and 'content'
        max_retries: Maximum number of retry attempts
        base_url: Ollama API URL (default: http://localhost:11434)
        context: Optional dict with context info for error logging

    Returns:
        Response dict with 'message' and 'usage' keys

    Raises:
        requests.exceptions.HTTPError: If all retries fail
    """
    if base_url is None:
        base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')

    url = f"{base_url}/v1/chat/completions"
    session = get_http_session()

    payload = {
        "model": model,
        "messages": messages
    }

    def api_call():
        return session.post(url, json=payload, timeout=300)

    response = api_call_with_retry(api_call, max_retries=max_retries, context=context)
    return response.json()


def make_llm_call(
    model: str,
    messages: list,
    api_key: Optional[str] = None,
    max_retries: int = 3,
    context: Optional[dict] = None,
    use_cache: bool = True
) -> tuple[str, int]:
    """
    Make an LLM API call using the appropriate backend with optional caching

    Automatically routes to:
    - Ollama for models starting with "ollama/" or "local/"
    - OpenRouter for all other models

    Features:
    - Response caching to reduce costs
    - Connection pooling for better performance
    - Automatic retry with exponential backoff

    Args:
        model: Model identifier (e.g., "openai/gpt-4o-mini", "ollama/llama3.1:70b")
        messages: List of message dicts with 'role' and 'content'
        api_key: API key for cloud providers (not needed for local)
        max_retries: Maximum number of retry attempts
        context: Optional dict with context info (e.g., {'actor': 'name', 'turn': 1, 'operation': 'decision'})
        use_cache: Whether to use response caching (default: True)

    Returns:
        Tuple of (response_text, tokens_used)

    Raises:
        requests.exceptions.HTTPError: If all retries fail
    """
    import json

    # Add model to context for better error tracking
    call_context = {'model': model}
    if context:
        call_context.update(context)

    # Create cache key from messages (stable JSON representation)
    messages_str = json.dumps(messages, sort_keys=True)

    # Try cache first if enabled
    if use_cache:
        cache = get_global_cache()
        cached_result = cache.get(model, messages_str)
        if cached_result is not None:
            logger.debug(f"Cache hit for {model}: {len(messages)} messages")
            return cached_result

    # Cache miss or caching disabled - make actual API call
    def make_actual_call():
        if is_local_model(model):
            # Strip the "ollama/" or "local/" prefix
            local_model = model.split('/', 1)[1]

            result = make_ollama_call(local_model, messages, max_retries, context=call_context)

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

            response = make_openrouter_call(url, headers, payload, max_retries, context=call_context)
            data = response.json()

            response_text = data['choices'][0]['message']['content']
            tokens_used = data.get('usage', {}).get('total_tokens', 0)

            return response_text, tokens_used

    # Make call
    response_text, tokens_used = make_actual_call()

    # Store in cache if enabled
    if use_cache:
        cache = get_global_cache()
        cache.put(model, messages_str, response_text, tokens_used)
        logger.debug(f"Cached response for {model}: {len(messages)} messages")

    return response_text, tokens_used
