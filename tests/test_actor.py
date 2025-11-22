"""
Tests for Actor module

Tests Actor dataclass, conversions, and decision-making methods.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from scenario_lab.core.actor import Actor
from scenario_lab.utils.api_client import LLMResponse


class TestActorCreation:
    """Tests for Actor creation"""

    def test_create_actor_basic(self):
        """Test creating an actor with basic fields"""
        actor = Actor(
            name="United States",
            short_name="us",
            llm_model="openai/gpt-4o-mini"
        )

        assert actor.name == "United States"
        assert actor.short_name == "us"
        assert actor.llm_model == "openai/gpt-4o-mini"

    def test_create_actor_full(self):
        """Test creating an actor with all fields"""
        actor = Actor(
            name="United States",
            short_name="us",
            llm_model="openai/gpt-4o-mini",
            system_prompt="You are the US President.",
            description="The leader of the United States.",
            goals=["Maintain global leadership", "Protect economy"],
            constraints=["Cannot declare war unilaterally"],
            expertise={"foreign_policy": 0.9, "economics": 0.8},
            decision_style="Pragmatic and measured",
            scenario_system_prompt="You are in a simulation.",
            json_mode=True
        )

        assert actor.system_prompt == "You are the US President."
        assert len(actor.goals) == 2
        assert len(actor.constraints) == 1
        assert actor.expertise["foreign_policy"] == 0.9
        assert actor.json_mode is True

    def test_actor_is_immutable(self):
        """Test that Actor is immutable (frozen dataclass)"""
        actor = Actor(
            name="Test",
            short_name="test",
            llm_model="model"
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            actor.name = "Changed"


class TestActorFromDict:
    """Tests for Actor.from_dict class method"""

    def test_from_dict_basic(self):
        """Test creating actor from dictionary with basic fields"""
        data = {
            "name": "China",
            "short_name": "cn",
            "llm_model": "openai/gpt-4o"
        }

        actor = Actor.from_dict(data)

        assert actor.name == "China"
        assert actor.short_name == "cn"
        assert actor.llm_model == "openai/gpt-4o"

    def test_from_dict_full(self):
        """Test creating actor from dictionary with all fields"""
        data = {
            "name": "China",
            "short_name": "cn",
            "llm_model": "openai/gpt-4o",
            "system_prompt": "You are the Chinese government.",
            "description": "The People's Republic of China.",
            "goals": ["Economic growth", "Regional influence"],
            "constraints": ["Internal stability priority"],
            "expertise": {"manufacturing": 0.95},
            "decision_style": "Long-term strategic"
        }

        actor = Actor.from_dict(
            data,
            scenario_system_prompt="Geopolitical simulation",
            json_mode=True
        )

        assert actor.system_prompt == "You are the Chinese government."
        assert actor.scenario_system_prompt == "Geopolitical simulation"
        assert actor.json_mode is True

    def test_from_dict_missing_optional(self):
        """Test creating actor from dictionary with missing optional fields"""
        data = {
            "name": "Test",
            "short_name": "test",
            "llm_model": "model"
        }

        actor = Actor.from_dict(data)

        assert actor.system_prompt == ""
        assert actor.description == ""
        assert actor.goals == []
        assert actor.constraints == []
        assert actor.expertise == {}
        assert actor.decision_style == ""


class TestActorToDict:
    """Tests for Actor.to_dict method"""

    def test_to_dict_basic(self):
        """Test converting actor to dictionary"""
        actor = Actor(
            name="Test Actor",
            short_name="test",
            llm_model="openai/gpt-4o-mini",
            goals=["Goal 1", "Goal 2"]
        )

        result = actor.to_dict()

        assert result["name"] == "Test Actor"
        assert result["short_name"] == "test"
        assert result["llm_model"] == "openai/gpt-4o-mini"
        assert result["goals"] == ["Goal 1", "Goal 2"]

    def test_to_dict_excludes_scenario_prompt(self):
        """Test that to_dict excludes scenario-level context"""
        actor = Actor(
            name="Test",
            short_name="test",
            llm_model="model",
            scenario_system_prompt="This should not be in to_dict"
        )

        result = actor.to_dict()

        # scenario_system_prompt is not part of basic actor config
        assert "scenario_system_prompt" not in result

    def test_to_config_dict(self):
        """Test to_config_dict method"""
        actor = Actor(
            name="Test",
            short_name="test",
            llm_model="model"
        )

        result = actor.to_config_dict()

        assert "name" in result
        assert "short_name" in result
        assert "llm_model" in result


class TestActorMakeDecision:
    """Tests for Actor.make_decision method"""

    @pytest.mark.asyncio
    @patch('scenario_lab.core.actor.make_llm_call_async')
    async def test_make_decision_basic(self, mock_llm_call):
        """Test basic decision making"""
        mock_llm_call.return_value = LLMResponse(
            content="""**LONG-TERM GOALS:**
- Maintain stability

**SHORT-TERM PRIORITIES:**
- Address crisis

**REASONING:**
Given the situation, we need to act.

**ACTION:**
We will implement sanctions.""",
            tokens_used=100,
            input_tokens=70,
            output_tokens=30,
            model="openai/gpt-4o-mini"
        )

        actor = Actor(
            name="Test Actor",
            short_name="test",
            llm_model="openai/gpt-4o-mini"
        )

        result = await actor.make_decision(
            world_state="Test world state",
            turn=1,
            total_turns=10
        )

        assert "goals" in result
        assert "reasoning" in result
        assert "action" in result
        assert result["tokens_used"] == 100

    @pytest.mark.asyncio
    @patch('scenario_lab.core.actor.make_llm_call_async')
    async def test_make_decision_with_communications(self, mock_llm_call):
        """Test decision making with communications context"""
        mock_llm_call.return_value = LLMResponse(
            content="**ACTION:** Test action",
            tokens_used=50
        )

        actor = Actor(
            name="Test",
            short_name="test",
            llm_model="model"
        )

        await actor.make_decision(
            world_state="Test",
            turn=1,
            total_turns=10,
            communications_context="Private message received"
        )

        # Check that communications context was passed to LLM
        call_args = mock_llm_call.call_args
        messages = call_args[1]['messages']
        user_message = messages[-1]['content']
        assert "Private message received" in user_message

    @pytest.mark.asyncio
    @patch('scenario_lab.core.actor.make_llm_call_async')
    async def test_make_decision_includes_context(self, mock_llm_call):
        """Test that decision includes proper context for error logging"""
        mock_llm_call.return_value = LLMResponse(
            content="**ACTION:** Test",
            tokens_used=50
        )

        actor = Actor(
            name="Test Actor",
            short_name="test",
            llm_model="model"
        )

        await actor.make_decision(
            world_state="Test",
            turn=5,
            total_turns=10
        )

        # Check context was passed
        call_kwargs = mock_llm_call.call_args[1]
        assert call_kwargs['context']['phase'] == 'decision'
        assert call_kwargs['context']['actor'] == 'test'
        assert call_kwargs['context']['turn'] == 5


class TestActorRespondToBilateral:
    """Tests for Actor.respond_to_bilateral method"""

    @pytest.mark.asyncio
    @patch('scenario_lab.core.actor.make_llm_call_async')
    async def test_respond_to_bilateral_basic(self, mock_llm_call):
        """Test basic bilateral response"""
        mock_llm_call.return_value = LLMResponse(
            content="""**RESPONSE:**
Thank you for the proposal. We are interested.

**INTERNAL_NOTES:**
This could benefit us strategically.""",
            tokens_used=80
        )

        actor = Actor(
            name="Test",
            short_name="test",
            llm_model="model"
        )

        result = await actor.respond_to_bilateral(
            world_state="Test state",
            turn=2,
            total_turns=10,
            initiator="China",
            message="Let's cooperate."
        )

        assert "response" in result
        assert "internal_notes" in result
        assert "interested" in result["response"]

    @pytest.mark.asyncio
    @patch('scenario_lab.core.actor.make_llm_call_async')
    async def test_respond_to_bilateral_includes_initiator(self, mock_llm_call):
        """Test that bilateral response includes initiator name"""
        mock_llm_call.return_value = LLMResponse(
            content="**RESPONSE:** OK\n**INTERNAL_NOTES:** Think about it",
            tokens_used=50
        )

        actor = Actor(
            name="Test",
            short_name="test",
            llm_model="model"
        )

        await actor.respond_to_bilateral(
            world_state="Test",
            turn=1,
            total_turns=10,
            initiator="Russia",
            message="Hello"
        )

        # Check initiator is in the prompt
        call_args = mock_llm_call.call_args
        messages = call_args[1]['messages']
        user_message = messages[-1]['content']
        assert "Russia" in user_message


class TestActorRespondToCoalition:
    """Tests for Actor.respond_to_coalition method"""

    @pytest.mark.asyncio
    @patch('scenario_lab.core.actor.make_llm_call_async')
    async def test_respond_to_coalition_accept(self, mock_llm_call):
        """Test accepting a coalition proposal"""
        mock_llm_call.return_value = LLMResponse(
            content="""**DECISION:** accept
**RESPONSE:** We would be happy to join this coalition.
**INTERNAL_NOTES:** This aligns with our interests.""",
            tokens_used=100
        )

        actor = Actor(
            name="Test",
            short_name="test",
            llm_model="model"
        )

        result = await actor.respond_to_coalition(
            world_state="Test",
            turn=3,
            total_turns=10,
            proposer="EU",
            members=["US", "UK", "Japan"],
            purpose="Economic cooperation"
        )

        assert result["decision"] == "accept"
        assert "happy to join" in result["response"]

    @pytest.mark.asyncio
    @patch('scenario_lab.core.actor.make_llm_call_async')
    async def test_respond_to_coalition_reject(self, mock_llm_call):
        """Test rejecting a coalition proposal"""
        mock_llm_call.return_value = LLMResponse(
            content="""**DECISION:** reject
**RESPONSE:** We cannot join at this time.
**INTERNAL_NOTES:** This would harm our other relationships.""",
            tokens_used=100
        )

        actor = Actor(
            name="Test",
            short_name="test",
            llm_model="model"
        )

        result = await actor.respond_to_coalition(
            world_state="Test",
            turn=3,
            total_turns=10,
            proposer="EU",
            members=["US", "UK"],
            purpose="Military alliance"
        )

        assert result["decision"] == "reject"

    @pytest.mark.asyncio
    @patch('scenario_lab.core.actor.make_llm_call_async')
    async def test_respond_to_coalition_default_reject(self, mock_llm_call):
        """Test that ambiguous response defaults to reject"""
        mock_llm_call.return_value = LLMResponse(
            content="We will consider this proposal carefully.",
            tokens_used=50
        )

        actor = Actor(
            name="Test",
            short_name="test",
            llm_model="model"
        )

        result = await actor.respond_to_coalition(
            world_state="Test",
            turn=3,
            total_turns=10,
            proposer="EU",
            members=["US"],
            purpose="Test"
        )

        # Should default to reject when decision is ambiguous
        assert result["decision"] == "reject"


class TestActorEquality:
    """Tests for Actor equality and hashing"""

    def test_actors_with_same_data_equal(self):
        """Test that actors with same data are equal"""
        actor1 = Actor(
            name="Test",
            short_name="test",
            llm_model="model"
        )
        actor2 = Actor(
            name="Test",
            short_name="test",
            llm_model="model"
        )

        assert actor1 == actor2

    def test_actors_with_different_data_not_equal(self):
        """Test that actors with different data are not equal"""
        actor1 = Actor(
            name="Test1",
            short_name="test1",
            llm_model="model"
        )
        actor2 = Actor(
            name="Test2",
            short_name="test2",
            llm_model="model"
        )

        assert actor1 != actor2


class TestActorRoundTrip:
    """Tests for Actor serialization round-trip"""

    def test_to_dict_from_dict_roundtrip(self):
        """Test that to_dict and from_dict preserve data"""
        original = Actor(
            name="Test Actor",
            short_name="test",
            llm_model="openai/gpt-4o-mini",
            system_prompt="Test prompt",
            description="Test description",
            goals=["Goal 1", "Goal 2"],
            constraints=["Constraint 1"],
            expertise={"skill": 0.8},
            decision_style="Analytical"
        )

        data = original.to_dict()
        restored = Actor.from_dict(data)

        assert restored.name == original.name
        assert restored.short_name == original.short_name
        assert restored.llm_model == original.llm_model
        assert restored.system_prompt == original.system_prompt
        assert restored.goals == original.goals
        assert restored.constraints == original.constraints
        assert restored.expertise == original.expertise
