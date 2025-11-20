#!/usr/bin/env python3
"""
Tests for V2 Actor Class

Tests the immutable Actor dataclass and its convenience methods.
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.core.actor import Actor
from scenario_lab.utils.api_client import LLMResponse


# Mock responses
MOCK_DECISION_RESPONSE = """**LONG-TERM GOALS:**
- Ensure AI safety regulations are effective
- Balance innovation with public safety

**SHORT-TERM PRIORITIES:**
- Review current proposals
- Engage with stakeholders

**REASONING:**
Given the current situation, we need to carefully consider both innovation and safety.

**ACTION:**
Propose a framework that includes mandatory safety testing."""

MOCK_BILATERAL_RESPONSE = """**RESPONSE:**
I appreciate your concerns and would like to explore a compromise that addresses both our interests.

**INTERNAL_NOTES:**
This negotiation is crucial. I need to maintain my principles while finding common ground."""

MOCK_COALITION_RESPONSE = """**DECISION:** accept

**RESPONSE:**
I agree that this coalition serves our mutual interests. Let's coordinate our efforts.

**INTERNAL_NOTES:**
This alliance will strengthen my position. I'm committed to the coalition's goals."""


async def test_actor_creation():
    """Test Actor creation from dict"""
    print("Test 1: Actor creation from dict")

    actor_data = {
        'name': 'AI Safety Regulator',
        'short_name': 'regulator',
        'llm_model': 'openai/gpt-4o-mini',
        'system_prompt': 'You are a regulator.',
        'description': 'Government regulator',
        'goals': ['Ensure AI safety', 'Balance innovation'],
        'constraints': ['Must follow legal framework'],
        'expertise': {'domain': 'AI policy'},
        'decision_style': 'Cautious'
    }

    actor = Actor.from_dict(actor_data, scenario_system_prompt="Test scenario", json_mode=False)

    assert actor.name == 'AI Safety Regulator'
    assert actor.short_name == 'regulator'
    assert actor.llm_model == 'openai/gpt-4o-mini'
    assert actor.system_prompt == 'You are a regulator.'
    assert len(actor.goals) == 2
    assert actor.scenario_system_prompt == "Test scenario"
    assert actor.json_mode is False

    print("  ✓ Actor created successfully from dict")
    print("  ✓ All fields set correctly")
    return True


async def test_actor_to_dict():
    """Test Actor conversion to dict"""
    print("\nTest 2: Actor to dict conversion")

    actor = Actor(
        name='Tech Company',
        short_name='tech-co',
        llm_model='openai/gpt-4o-mini',
        system_prompt='You are a tech company.',
        goals=['Innovate', 'Profit'],
        scenario_system_prompt="Test scenario"
    )

    config = actor.to_dict()

    assert config['name'] == 'Tech Company'
    assert config['short_name'] == 'tech-co'
    assert len(config['goals']) == 2
    assert 'scenario_system_prompt' not in config  # Scenario context not in dict

    print("  ✓ Actor converted to dict")
    print("  ✓ Dict contains all config fields")
    print("  ✓ Scenario context excluded from dict")
    return True


async def test_actor_make_decision():
    """Test Actor.make_decision() with mocked LLM"""
    print("\nTest 3: Actor decision making (mocked LLM)")

    actor = Actor(
        name='AI Safety Regulator',
        short_name='regulator',
        llm_model='openai/gpt-4o-mini',
        system_prompt='You are a regulator.',
        scenario_system_prompt="Test scenario"
    )

    mock_response = LLMResponse(
        content=MOCK_DECISION_RESPONSE,
        tokens_used=500,
        input_tokens=350,
        output_tokens=150,
        model='openai/gpt-4o-mini'
    )

    with patch('scenario_lab.core.actor.make_llm_call_async', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response

        decision = await actor.make_decision(
            world_state="Test world state",
            turn=1,
            total_turns=5
        )

        assert 'goals' in decision
        assert 'reasoning' in decision
        assert 'action' in decision
        assert 'raw_response' in decision
        assert 'tokens_used' in decision
        assert decision['tokens_used'] == 500
        assert decision['model'] == 'openai/gpt-4o-mini'

        # Verify LLM was called
        assert mock_llm.call_count == 1

    print("  ✓ Decision made successfully")
    print("  ✓ Decision contains all expected fields")
    print("  ✓ Token usage tracked")
    print("  ✓ LLM called once")
    return True


async def test_actor_respond_to_bilateral():
    """Test Actor.respond_to_bilateral() with mocked LLM"""
    print("\nTest 4: Actor bilateral response (mocked LLM)")

    actor = Actor(
        name='Tech Company',
        short_name='tech-co',
        llm_model='openai/gpt-4o-mini',
        system_prompt='You are a tech company.',
        scenario_system_prompt="Test scenario"
    )

    mock_response = LLMResponse(
        content=MOCK_BILATERAL_RESPONSE,
        tokens_used=300,
        input_tokens=200,
        output_tokens=100,
        model='openai/gpt-4o-mini'
    )

    with patch('scenario_lab.core.actor.make_llm_call_async', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response

        response = await actor.respond_to_bilateral(
            world_state="Test world state",
            turn=1,
            total_turns=5,
            initiator="AI Safety Regulator",
            message="We should work together on this proposal."
        )

        assert 'response' in response
        assert 'internal_notes' in response
        assert 'tokens_used' in response
        assert len(response['response']) > 0
        assert len(response['internal_notes']) > 0
        assert response['tokens_used'] == 300

        # Verify LLM was called
        assert mock_llm.call_count == 1

    print("  ✓ Bilateral response generated")
    print("  ✓ Response contains public and private parts")
    print("  ✓ Token usage tracked")
    return True


async def test_actor_respond_to_coalition():
    """Test Actor.respond_to_coalition() with mocked LLM"""
    print("\nTest 5: Actor coalition response (mocked LLM)")

    actor = Actor(
        name='Civil Society',
        short_name='civil-society',
        llm_model='openai/gpt-4o-mini',
        system_prompt='You represent civil society.',
        scenario_system_prompt="Test scenario"
    )

    mock_response = LLMResponse(
        content=MOCK_COALITION_RESPONSE,
        tokens_used=250,
        input_tokens=150,
        output_tokens=100,
        model='openai/gpt-4o-mini'
    )

    with patch('scenario_lab.core.actor.make_llm_call_async', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response

        response = await actor.respond_to_coalition(
            world_state="Test world state",
            turn=1,
            total_turns=5,
            proposer="AI Safety Regulator",
            members=["AI Safety Regulator", "Civil Society", "Tech Company"],
            purpose="Coordinate on AI safety framework"
        )

        assert 'decision' in response
        assert 'response' in response
        assert 'internal_notes' in response
        assert response['decision'] == 'accept'
        assert len(response['response']) > 0
        assert response['tokens_used'] == 250

        # Verify LLM was called
        assert mock_llm.call_count == 1

    print("  ✓ Coalition response generated")
    print("  ✓ Decision parsed correctly (accept)")
    print("  ✓ Response and internal notes present")
    return True


async def test_actor_immutability():
    """Test that Actor is immutable"""
    print("\nTest 6: Actor immutability")

    actor = Actor(
        name='Test Actor',
        short_name='test',
        llm_model='openai/gpt-4o-mini'
    )

    # Try to modify - should raise FrozenInstanceError
    try:
        actor.name = 'New Name'
        print("  ✗ FAILED: Actor should be immutable")
        return False
    except Exception:
        print("  ✓ Actor is immutable (frozen dataclass)")
        return True


async def test_actor_with_communications_context():
    """Test Actor decision with communication context"""
    print("\nTest 7: Actor decision with communication context")

    actor = Actor(
        name='Test Actor',
        short_name='test',
        llm_model='openai/gpt-4o-mini',
        scenario_system_prompt="Test scenario"
    )

    mock_response = LLMResponse(
        content=MOCK_DECISION_RESPONSE,
        tokens_used=500,
        input_tokens=350,
        output_tokens=150,
        model='openai/gpt-4o-mini'
    )

    communications_context = """## Private Communications

**From Regulator:** We should coordinate our approach.
"""

    with patch('scenario_lab.core.actor.make_llm_call_async', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_response

        decision = await actor.make_decision(
            world_state="Test world state",
            turn=1,
            total_turns=5,
            communications_context=communications_context
        )

        assert 'action' in decision
        assert mock_llm.call_count == 1

        # Verify communications context was passed in prompt
        call_args = mock_llm.call_args
        messages = call_args[1]['messages']
        user_prompt = next(m['content'] for m in messages if m['role'] == 'user')
        assert 'Private Communications' in user_prompt or 'Regulator' in user_prompt

    print("  ✓ Decision made with communication context")
    print("  ✓ Communication context included in prompt")
    return True


async def test_actor_loader_integration():
    """Test actor loader integration"""
    print("\nTest 8: Actor loader integration")

    from scenario_lab.loaders.actor_loader import create_actor_from_config

    actor_config = {
        'name': 'AI Safety Regulator',
        'short_name': 'regulator',
        'llm_model': 'openai/gpt-4o-mini',
        'system_prompt': 'You are a regulator.',
        'goals': ['Ensure AI safety'],
    }

    actor = create_actor_from_config(actor_config, scenario_system_prompt="Test")

    assert isinstance(actor, Actor)
    assert actor.name == 'AI Safety Regulator'
    assert actor.scenario_system_prompt == "Test"

    print("  ✓ Actor created from loader")
    print("  ✓ Loader integration working")
    return True


async def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("V2 ACTOR TESTS")
    print("=" * 70)
    print()

    tests = [
        test_actor_creation,
        test_actor_to_dict,
        test_actor_make_decision,
        test_actor_respond_to_bilateral,
        test_actor_respond_to_coalition,
        test_actor_immutability,
        test_actor_with_communications_context,
        test_actor_loader_integration,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL TESTS PASSED")
        print()
        print("V2 Actor features verified:")
        print("  - Immutable dataclass design")
        print("  - Creation from dicts and conversion to dicts")
        print("  - Decision making with mocked LLMs")
        print("  - Bilateral communication responses")
        print("  - Coalition responses")
        print("  - Communication context handling")
        print("  - Loader integration")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
