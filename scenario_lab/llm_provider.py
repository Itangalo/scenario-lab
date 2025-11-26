"""
LLM Provider abstraction for Scenario Lab V3.
"""

import json
import logging
import random
from typing import List, Dict, Protocol, Optional

from .models import LLMConfig

logger = logging.getLogger(__name__)

class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    def complete(
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

class MockProvider:
    """
    Mock provider for testing.
    Returns deterministic responses for testing the simulation loop.
    """

    def __init__(self, config: LLMConfig, scenario_config: Dict):
        self.config = config
        self.scenario_config = scenario_config

    def complete(
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

        if "Phase 1" in system_prompt:
            return self._generate_phase1_response()
        elif "Phase 2" in system_prompt:
            return self._generate_phase2_response()
        elif "Phase 3" in system_prompt:
            return self._generate_phase3_response()
        else:
            return self._generate_default_response()

    def _get_current_actor(self, system_prompt: str) -> Optional[str]:
        # A bit brittle, but for a mock it's fine.
        # "You are ActorName,"
        try:
            return system_prompt.split("You are ")[1].split(",")[0]
        except IndexError:
            return None

    def _generate_phase1_response(self) -> str:
        """Generates a mock response for Phase 1 (communication)."""
        # In Phase 1, actors can send messages. Let's make a mock message.
        # This part of the prompt is not yet implemented in the engine,
        # so this is a placeholder.
        return json.dumps({
            "reasoning": "I need to communicate with another actor.",
            "messages": [
                {
                    "to": "China",
                    "content": "This is a mock message from the USA.",
                }
            ]
        })


    def _generate_phase2_response(self) -> str:
        """Generates a mock response for Phase 2 (response)."""
        # In Phase 2, actors can reply. Let's simulate a 50% chance of replying.
        if random.random() > 0.5:
            return json.dumps({
                "reasoning": "I will reply to this message.",
                "messages": [
                    {
                        "to": "USA",
                        "content": "This is a mock reply from China.",
                    }
                ]
            })
        else:
            return json.dumps({
                "reasoning": "I will not reply.",
                "messages": []
            })


    def _generate_phase3_response(self) -> str:
        """Generates a mock response for Phase 3 (action)."""
        response = {
            "reasoning": "Given the current situation, investing in research is prudent.",
            "actions": [
                {"name": "invest_research", "arguments": {"amount": 50}}
            ],
            "next_turn_goals": [
                "Continue AI development",
                "Monitor China's activities"
            ]
        }
        return json.dumps(response)

    def _generate_default_response(self) -> str:
        """Generates a default mock response."""
        return json.dumps({"reasoning": "This is a default mock response.", "actions": [], "next_turn_goals": []})


def get_provider(config: LLMConfig, scenario_config: Dict) -> LLMProvider:
    """
    Factory function to create the appropriate LLM provider.

    Args:
        config: LLM configuration
        scenario_config: The main scenario configuration.

    Returns:
        Instantiated LLM provider

    Raises:
        ValueError: If provider type is not supported
    """
    provider_type = config.provider.lower()

    if provider_type == "mock":
        return MockProvider(config, scenario_config)
    else:
        # For now, we only support mock.
        # In the future, we would add OpenRouterProvider, LocalProvider, etc.
        raise ValueError(f"Unsupported provider type: {provider_type}")