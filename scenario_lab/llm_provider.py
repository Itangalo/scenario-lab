"""
LLM Provider abstraction for Scenario Lab V3.

Provides a unified interface for multiple LLM backends:
- OpenRouter (primary): Claude, GPT, Llama, etc.
- Local: Ollama, llama.cpp, etc.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .models import LLMConfig


logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized response from an LLM provider."""
    content: str
    model: str
    usage: Dict[str, int]
    raw_response: Dict[str, Any]
    function_calls: List[Dict[str, Any]] = None  # For structured outputs


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        """
        Initialize the provider with configuration.

        Args:
            config: LLM configuration from scenario.yaml
        """
        self.config = config
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            system_prompt: System/instruction prompt
            user_prompt: User/task prompt
            temperature: Optional override for temperature
            max_tokens: Optional override for max tokens

        Returns:
            LLMResponse with content and metadata
        """
        pass

    @abstractmethod
    def generate_with_functions(
        self,
        system_prompt: str,
        user_prompt: str,
        functions: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a response with function calling capability.

        Args:
            system_prompt: System/instruction prompt
            user_prompt: User/task prompt
            functions: List of function definitions for structured output
            temperature: Optional override for temperature
            max_tokens: Optional override for max tokens

        Returns:
            LLMResponse with content and function calls
        """
        pass


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter API provider.

    Supports Claude, GPT, Llama, and other models via OpenRouter.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)

        # Get API key from environment
        api_key_env = config.api_key_env or "OPENROUTER_API_KEY"
        self.api_key = os.environ.get(api_key_env)

        if not self.api_key:
            raise ValueError(
                f"API key not found in environment variable: {api_key_env}"
            )

        self.base_url = "https://openrouter.ai/api/v1"

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate response from OpenRouter API."""
        # TODO: Implement with httpx or requests
        # For now, return stub response
        logger.warning("OpenRouterProvider.generate() is a stub implementation")

        return LLMResponse(
            content="[STUB] LLM response would go here",
            model=self.model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            raw_response={}
        )

    def generate_with_functions(
        self,
        system_prompt: str,
        user_prompt: str,
        functions: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate response with function calling from OpenRouter API."""
        # TODO: Implement with httpx or requests
        # For now, return stub response
        logger.warning(
            "OpenRouterProvider.generate_with_functions() is a stub implementation"
        )

        return LLMResponse(
            content="[STUB] LLM response with functions would go here",
            model=self.model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            raw_response={},
            function_calls=[]
        )


class LocalProvider(LLMProvider):
    """
    Local model provider.

    Supports Ollama, llama.cpp, and other local inference servers.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)

        # Get endpoint from config or use default
        self.endpoint = os.environ.get("LOCAL_LLM_ENDPOINT", "http://localhost:11434")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate response from local model."""
        # TODO: Implement with httpx
        # For now, return stub response
        logger.warning("LocalProvider.generate() is a stub implementation")

        return LLMResponse(
            content="[STUB] Local LLM response would go here",
            model=self.model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            raw_response={}
        )

    def generate_with_functions(
        self,
        system_prompt: str,
        user_prompt: str,
        functions: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate response with function calling from local model."""
        # TODO: Implement with httpx
        # For now, return stub response
        logger.warning(
            "LocalProvider.generate_with_functions() is a stub implementation"
        )

        return LLMResponse(
            content="[STUB] Local LLM response with functions would go here",
            model=self.model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            raw_response={},
            function_calls=[]
        )


class MockProvider(LLMProvider):
    """
    Mock provider for testing.

    Returns deterministic responses for testing the simulation loop.
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.call_count = 0

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate mock response."""
        self.call_count += 1

        logger.info(f"MockProvider.generate() called (call #{self.call_count})")

        return LLMResponse(
            content=f"[MOCK] Response #{self.call_count}",
            model="mock-model",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            raw_response={"mock": True}
        )

    def generate_with_functions(
        self,
        system_prompt: str,
        user_prompt: str,
        functions: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate mock response with function calls."""
        self.call_count += 1

        logger.info(
            f"MockProvider.generate_with_functions() called (call #{self.call_count})"
        )

        return LLMResponse(
            content=f"[MOCK] Response with functions #{self.call_count}",
            model="mock-model",
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            raw_response={"mock": True},
            function_calls=[
                {
                    "name": "mock_action",
                    "arguments": {"param": "value"}
                }
            ]
        )


def create_provider(config: LLMConfig) -> LLMProvider:
    """
    Factory function to create the appropriate LLM provider.

    Args:
        config: LLM configuration

    Returns:
        Instantiated LLM provider

    Raises:
        ValueError: If provider type is not supported
    """
    provider_type = config.provider.lower()

    if provider_type == "openrouter":
        return OpenRouterProvider(config)
    elif provider_type == "local":
        return LocalProvider(config)
    elif provider_type == "mock":
        return MockProvider(config)
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")
