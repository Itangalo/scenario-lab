"""
Tests for Prompt Builder module

Tests prompt construction for actor decisions and communications.
"""
import pytest

from scenario_lab.core.prompt_builder import (
    build_actor_system_prompt,
    build_decision_prompt,
    build_communication_decision_prompt,
    build_bilateral_response_prompt,
    build_messages_for_llm,
)


class TestBuildActorSystemPrompt:
    """Tests for build_actor_system_prompt function"""

    def test_scenario_prompt_only(self):
        """Test building with only scenario prompt"""
        result = build_actor_system_prompt("You are in a simulation.")

        assert result == "You are in a simulation."

    def test_actor_prompt_only(self):
        """Test building with only actor prompt"""
        result = build_actor_system_prompt("", "You are the President.")

        assert result == "You are the President."

    def test_combined_prompts(self):
        """Test building with both prompts"""
        result = build_actor_system_prompt(
            "You are in a simulation.",
            "You are the President."
        )

        assert "You are in a simulation." in result
        assert "You are the President." in result
        assert "\n\n" in result

    def test_empty_prompts(self):
        """Test building with empty prompts"""
        result = build_actor_system_prompt("", None)
        assert result == ""

    def test_none_scenario_prompt(self):
        """Test with None scenario prompt"""
        result = build_actor_system_prompt(None, "Actor prompt")
        assert result == "Actor prompt"


class TestBuildDecisionPrompt:
    """Tests for build_decision_prompt function"""

    def test_basic_decision_prompt(self):
        """Test building a basic decision prompt"""
        system_prompt, user_prompt = build_decision_prompt(
            world_state="The world is at peace.",
            turn=1,
            total_turns=10,
            actor_name="TestActor"
        )

        assert "Turn 1 of 10" in user_prompt
        assert "The world is at peace." in user_prompt
        assert "LONG-TERM GOALS" in user_prompt
        assert "ACTION" in user_prompt

    def test_decision_prompt_with_scenario_prompt(self):
        """Test decision prompt includes scenario system prompt"""
        system_prompt, user_prompt = build_decision_prompt(
            world_state="Test",
            turn=1,
            total_turns=10,
            scenario_system_prompt="You are in a geopolitical simulation."
        )

        assert "geopolitical simulation" in system_prompt

    def test_decision_prompt_with_actor_prompt(self):
        """Test decision prompt includes actor system prompt"""
        system_prompt, user_prompt = build_decision_prompt(
            world_state="Test",
            turn=1,
            total_turns=10,
            scenario_system_prompt="Scenario prompt",
            actor_system_prompt="You are the US President."
        )

        assert "Scenario prompt" in system_prompt
        assert "US President" in system_prompt

    def test_decision_prompt_with_other_actors_decisions(self):
        """Test decision prompt includes other actors' decisions"""
        other_decisions = {
            "China": "We will increase tariffs.",
            "Russia": "We will remain neutral."
        }

        system_prompt, user_prompt = build_decision_prompt(
            world_state="Trade tensions rising.",
            turn=3,
            total_turns=10,
            other_actors_decisions=other_decisions
        )

        assert "Other Actors' Decisions" in user_prompt
        assert "China" in user_prompt
        assert "increase tariffs" in user_prompt
        assert "Russia" in user_prompt

    def test_decision_prompt_with_communications_context(self):
        """Test decision prompt includes communications context"""
        system_prompt, user_prompt = build_decision_prompt(
            world_state="Test",
            turn=1,
            total_turns=10,
            communications_context="Private message from China: Let's cooperate."
        )

        assert "Private message from China" in user_prompt

    def test_decision_prompt_with_recent_goals(self):
        """Test decision prompt includes recent goals"""
        system_prompt, user_prompt = build_decision_prompt(
            world_state="Test",
            turn=5,
            total_turns=10,
            recent_goals="Maintain economic stability\nProtect national security"
        )

        assert "Your Recent Goals" in user_prompt
        assert "economic stability" in user_prompt

    def test_decision_prompt_json_mode(self):
        """Test decision prompt in JSON mode"""
        system_prompt, user_prompt = build_decision_prompt(
            world_state="Test",
            turn=1,
            total_turns=10,
            json_mode=True
        )

        assert "JSON" in user_prompt
        assert "long_term" in user_prompt
        assert "short_term" in user_prompt
        assert "reasoning" in user_prompt
        assert "action" in user_prompt

    def test_decision_prompt_markdown_mode(self):
        """Test decision prompt in markdown mode (default)"""
        system_prompt, user_prompt = build_decision_prompt(
            world_state="Test",
            turn=1,
            total_turns=10,
            json_mode=False
        )

        assert "**LONG-TERM GOALS:**" in user_prompt
        assert "**ACTION:**" in user_prompt

    def test_turn_numbers_in_prompt(self):
        """Test that turn numbers are correctly included"""
        system_prompt, user_prompt = build_decision_prompt(
            world_state="Test",
            turn=7,
            total_turns=15
        )

        assert "Turn 7 of 15" in user_prompt
        assert "turn 7 of 15" in user_prompt.lower()


class TestBuildCommunicationDecisionPrompt:
    """Tests for build_communication_decision_prompt function"""

    def test_basic_communication_prompt(self):
        """Test building a basic communication decision prompt"""
        system_prompt, user_prompt = build_communication_decision_prompt(
            world_state="Test state",
            turn=2,
            total_turns=10,
            other_actors=["China", "Russia", "EU"]
        )

        assert "Turn 2 of 10" in user_prompt
        assert "Communication Phase" in user_prompt
        assert "China, Russia, EU" in user_prompt
        assert "INITIATE_BILATERAL" in user_prompt
        assert "TARGET_ACTOR" in user_prompt

    def test_communication_prompt_with_system_prompts(self):
        """Test communication prompt includes system prompts"""
        system_prompt, user_prompt = build_communication_decision_prompt(
            world_state="Test",
            turn=1,
            total_turns=10,
            other_actors=["Actor1"],
            scenario_system_prompt="Scenario context",
            actor_system_prompt="Actor context"
        )

        assert "Scenario context" in system_prompt
        assert "Actor context" in system_prompt

    def test_communication_prompt_lists_all_actors(self):
        """Test that all other actors are listed"""
        other_actors = ["China", "Russia", "EU", "Japan", "India"]

        system_prompt, user_prompt = build_communication_decision_prompt(
            world_state="Test",
            turn=1,
            total_turns=10,
            other_actors=other_actors
        )

        for actor in other_actors:
            assert actor in user_prompt


class TestBuildBilateralResponsePrompt:
    """Tests for build_bilateral_response_prompt function"""

    def test_basic_bilateral_response(self):
        """Test building a basic bilateral response prompt"""
        system_prompt, user_prompt = build_bilateral_response_prompt(
            world_state="Test state",
            turn=3,
            total_turns=10,
            initiator="China",
            message="Let's form a trade agreement."
        )

        assert "Turn 3 of 10" in user_prompt
        assert "China" in user_prompt
        assert "trade agreement" in user_prompt
        assert "RESPONSE" in user_prompt
        assert "INTERNAL_NOTES" in user_prompt

    def test_bilateral_response_private_notice(self):
        """Test that bilateral response mentions privacy"""
        system_prompt, user_prompt = build_bilateral_response_prompt(
            world_state="Test",
            turn=1,
            total_turns=10,
            initiator="Actor1",
            message="Secret proposal"
        )

        assert "private" in user_prompt.lower()

    def test_bilateral_response_with_system_prompts(self):
        """Test bilateral response includes system prompts"""
        system_prompt, user_prompt = build_bilateral_response_prompt(
            world_state="Test",
            turn=1,
            total_turns=10,
            initiator="Actor1",
            message="Hello",
            scenario_system_prompt="Scenario context",
            actor_system_prompt="Actor context"
        )

        assert "Scenario context" in system_prompt
        assert "Actor context" in system_prompt


class TestBuildMessagesForLLM:
    """Tests for build_messages_for_llm function"""

    def test_messages_with_system_prompt(self):
        """Test building messages with system prompt"""
        messages = build_messages_for_llm(
            system_prompt="You are an AI assistant.",
            user_prompt="Hello, how are you?"
        )

        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == "You are an AI assistant."
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == "Hello, how are you?"

    def test_messages_without_system_prompt(self):
        """Test building messages without system prompt"""
        messages = build_messages_for_llm(
            system_prompt="",
            user_prompt="Hello!"
        )

        assert len(messages) == 1
        assert messages[0]['role'] == 'user'
        assert messages[0]['content'] == "Hello!"

    def test_messages_none_system_prompt(self):
        """Test building messages with None system prompt"""
        messages = build_messages_for_llm(
            system_prompt=None,
            user_prompt="Test"
        )

        assert len(messages) == 1
        assert messages[0]['role'] == 'user'


class TestPromptBuilderIntegration:
    """Integration tests for prompt builder"""

    def test_full_decision_workflow(self):
        """Test full decision prompt workflow"""
        # Build system prompt
        system_prompt = build_actor_system_prompt(
            "You are participating in a geopolitical simulation.",
            "You are the President of the United States."
        )

        # Build decision prompt
        _, user_prompt = build_decision_prompt(
            world_state="Trade tensions are rising between the US and China.",
            turn=5,
            total_turns=20,
            actor_name="US President",
            scenario_system_prompt=system_prompt,
            other_actors_decisions={
                "China": "We will impose retaliatory tariffs."
            },
            communications_context="Private message from EU: We support free trade.",
            recent_goals="Protect American jobs\nMaintain global leadership"
        )

        # Build messages
        messages = build_messages_for_llm(system_prompt, user_prompt)

        assert len(messages) == 2
        assert "geopolitical simulation" in messages[0]['content']
        assert "President of the United States" in messages[0]['content']
        assert "Trade tensions" in messages[1]['content']
        assert "China" in messages[1]['content']
        assert "Turn 5 of 20" in messages[1]['content']

    def test_communication_workflow(self):
        """Test full communication workflow"""
        system_prompt, user_prompt = build_communication_decision_prompt(
            world_state="Test state",
            turn=1,
            total_turns=10,
            other_actors=["China", "Russia"]
        )

        messages = build_messages_for_llm(system_prompt, user_prompt)

        assert messages[-1]['role'] == 'user'
        assert "China" in messages[-1]['content']
        assert "Russia" in messages[-1]['content']
