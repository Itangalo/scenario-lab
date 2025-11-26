"""
LLM Provider abstraction for Scenario Lab V3.
"""
import asyncio
import json
import logging
import os
import random
from typing import List, Dict, Protocol, Optional

import httpx
from .models import LLMConfig

logger = logging.getLogger(__name__)


class LLMConnectionError(Exception):
    """Custom exception for LLM connection errors."""
    pass


class LLMResponseError(Exception):
    """Custom exception for non-200 LLM API responses."""
    pass


class LLMRateLimitError(LLMResponseError):
    """Custom exception for 429 rate limit responses."""
    pass


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        response_format: Optional[Dict] = None,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            messages: A list of messages in the conversation history.
            model: The model to use for the completion.
            response_format: An optional dictionary specifying the response format (e.g., for JSON mode).

        Returns:
            The LLM's response as a string.
        """
        ...


class OpenRouterProvider:
    """
    OpenRouter API provider.
    """

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1", 
                 temperature: float = 0.7, max_tokens: int = 2000):
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60.0,
        )

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        response_format: Optional[Dict] = None,
    ) -> str:
        """Sends a completion request to the OpenRouter API."""
        max_retries = 3
        base_delay = 1.0  # seconds

        for attempt in range(max_retries):
            try:
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": model,
                        "messages": messages,
                        "response_format": response_format,
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                    },
                )
                response.raise_for_status()

                try:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Malformed JSON response: {response.text}")
                    if attempt < max_retries - 1:
                        messages.append({"role": "user", "content": "Please respond with valid JSON only."})
                        continue
                    else:
                        raise LLMResponseError(f"Malformed JSON response after retry: {response.text}") from e

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limit exceeded. Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
                    continue
                logger.error(f"HTTP error on attempt {attempt + 1}: {e.response.status_code} {e.response.text}")
                raise LLMResponseError(f"HTTP error: {e.response.status_code}") from e
            except httpx.RequestError as e:
                logger.error(f"Connection error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise LLMConnectionError("Failed to connect to LLM provider.") from e

        raise LLMResponseError("Failed to get a valid response after all retries.")


class LocalProvider:
    """
    Local model provider.
    """

    def __init__(self, base_url: str = "http://localhost:11434/v1", 
                 temperature: float = 0.7, max_tokens: int = 2000):
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = httpx.AsyncClient(timeout=60.0)

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        response_format: Optional[Dict] = None,
    ) -> str:
        """Sends a completion request to a local OpenAI-compatible endpoint."""
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "response_format": response_format,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} {e.response.text}")
            raise LLMResponseError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Connection error: {e}")
            raise LLMConnectionError("Failed to connect to local LLM provider.") from e
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Malformed JSON response: {response.text}")
            raise LLMResponseError(f"Malformed JSON response: {response.text}") from e


class MockProvider:
    """
    Mock provider for testing.
    Returns deterministic responses for testing the simulation loop.
    """

    def __init__(self, config: LLMConfig, scenario_config: Dict):
        self.config = config
        self.scenario_config = scenario_config

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str,
        response_format: Optional[Dict] = None,
    ) -> str:
        """Generate mock response based on the phase detected in the system prompt."""
        system_prompt = ""
        for message in messages:
            if message["role"] == "system":
                system_prompt = message["content"]
                break
        
        actor_name = self._get_current_actor(system_prompt)
        all_actors = self.scenario_config.get("actors", [])

        if "Phase 1" in system_prompt:
            return self._generate_phase1_response(actor_name, all_actors)
        elif "Phase 2" in system_prompt:
            return self._generate_phase2_response(actor_name, all_actors)
        elif "Phase 3" in system_prompt:
            return self._generate_phase3_response()
        else:
            return self._generate_default_response()

    def _get_current_actor(self, system_prompt: str) -> Optional[str]:
        try:
            return system_prompt.split("You are ")[1].split(",")[0]
        except IndexError:
            return None

    def _generate_phase1_response(self, actor_name: str, all_actors: List[str]) -> str:
        other_actors = [a for a in all_actors if a != actor_name]
        recipient = other_actors[0] if other_actors else "other"
        
        return json.dumps({
            "reasoning": f"As {actor_name}, I need to communicate with another actor.",
            "messages": [
                {
                    "to": recipient,
                    "content": f"This is a mock message from {actor_name}.",
                }
            ]
        })

    def _generate_phase2_response(self, actor_name: str, all_actors: List[str]) -> str:
        other_actors = [a for a in all_actors if a != actor_name]
        recipient = other_actors[0] if other_actors else "other"

        return json.dumps({
            "reasoning": f"As {actor_name}, I will reply to this message.",
            "messages": [
                {
                    "to": recipient,
                    "content": f"This is a mock reply from {actor_name}.",
                }
            ]
        })

    def _generate_phase3_response(self) -> str:
        response = {
            "reasoning": "Given the current situation, investing in research is prudent.",
            "actions": [
                {"name": "invest_research", "args": {"amount": 50}}
            ],
            "next_turn_goals": [
                "Continue AI development",
                "Monitor China's activities"
            ]
        }
        return json.dumps(response)

    def _generate_default_response(self) -> str:
        return json.dumps({"reasoning": "This is a default mock response.", "actions": [], "next_turn_goals": []})


def get_provider(config: LLMConfig, scenario_config: Dict, cli_provider: Optional[str] = None) -> LLMProvider:
    """
    Factory function to create the appropriate LLM provider.
    """
    provider_type = cli_provider or config.provider.lower()

    if provider_type == "openrouter":
        api_key = os.environ.get(config.api_key_env)
        if not api_key:
            raise ValueError(f"API key env var {config.api_key_env} not set.")
        return OpenRouterProvider(
            api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
    elif provider_type == "local":
        return LocalProvider(
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
    elif provider_type == "mock":
        return MockProvider(config, scenario_config)
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")