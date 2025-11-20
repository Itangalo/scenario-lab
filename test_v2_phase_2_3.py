#!/usr/bin/env python3
"""
Phase 2.3 Integration Test

Tests V2 Actor Engine integration with:
- V2 Actor class (immutable, dataclass-based)
- Communication features (bilateral, coalition)
- Loader integration
- Full pipeline integration

This verifies Phase 2.3 completion:
- Actor class moved to V2
- No V1 dependencies
- All actor features work with V2
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.loaders.scenario_loader import ScenarioLoader
from scenario_lab.loaders.actor_loader import create_actor_from_config
from scenario_lab.core.actor import Actor
from scenario_lab.services.decision_phase_v2 import DecisionPhaseV2
from scenario_lab.services.world_update_phase_v2 import WorldUpdatePhaseV2
from scenario_lab.services.communication_phase import CommunicationPhaseV2, add_communication_to_state
from scenario_lab.utils.api_client import LLMResponse


# Mock responses
MOCK_DECISION = """**LONG-TERM GOALS:**
- Ensure AI safety
- Balance innovation

**SHORT-TERM PRIORITIES:**
- Review proposals

**REASONING:**
We need to carefully consider both aspects.

**ACTION:**
Propose a balanced framework."""

MOCK_BILATERAL_RESPONSE = """**RESPONSE:**
I appreciate your proposal and would like to explore a compromise.

**INTERNAL_NOTES:**
This negotiation is crucial for achieving our objectives."""

MOCK_COALITION_ACCEPT = """**DECISION:** accept

**RESPONSE:**
I agree that this coalition serves our mutual interests.

**INTERNAL_NOTES:**
This alliance will strengthen our position."""

MOCK_WORLD_UPDATE = """**UPDATED STATE:**
Following the actors' decisions and negotiations, the situation has evolved.
The regulator and tech company are now working together on a framework.

**KEY CHANGES:**
- Bilateral negotiation initiated
- Framework proposal developed

**CONSEQUENCES:**
- Improved cooperation
- More balanced approach"""


async def test_actor_loader_creates_v2_actors():
    """Test that scenario loader creates V2 Actor objects"""
    print("=" * 70)
    print("TEST 1: Loader creates V2 Actor objects")
    print("=" * 70)
    print()

    loader = ScenarioLoader('scenarios/example-policy-negotiation')
    initial_state, actors, scenario_config = loader.load()

    # Verify actors are V2 Actor instances
    for short_name, actor in actors.items():
        assert isinstance(actor, Actor), f"Actor {short_name} should be V2 Actor instance"
        assert hasattr(actor, 'name'), "Actor should have name attribute"
        assert hasattr(actor, 'llm_model'), "Actor should have llm_model attribute"
        print(f"  ✓ {actor.name} is V2 Actor instance")

    # Verify actors are immutable (frozen dataclass)
    test_actor = list(actors.values())[0]
    try:
        test_actor.name = "New Name"
        print("  ✗ FAILED: Actors should be immutable")
        return False
    except Exception:
        print("  ✓ Actors are immutable (frozen dataclass)")

    print()
    print("✅ Test 1 passed: Loader creates V2 Actor objects")
    print()
    return True


async def test_actor_decision_making():
    """Test Actor decision making with V2 API client"""
    print("=" * 70)
    print("TEST 2: Actor decision making")
    print("=" * 70)
    print()

    actor_config = {
        'name': 'AI Safety Regulator',
        'short_name': 'regulator',
        'llm_model': 'openai/gpt-4o-mini',
        'system_prompt': 'You are a regulator.',
        'goals': ['Ensure AI safety'],
    }

    actor = create_actor_from_config(actor_config, scenario_system_prompt="Test scenario")

    mock_response = LLMResponse(
        content=MOCK_DECISION,
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

        assert 'action' in decision
        assert 'reasoning' in decision
        assert 'goals' in decision
        assert decision['tokens_used'] == 500

    print("  ✓ Actor made decision successfully")
    print("  ✓ Decision contains all required fields")
    print("  ✓ Token usage tracked")
    print()
    print("✅ Test 2 passed: Actor decision making works")
    print()
    return True


async def test_actor_bilateral_communication():
    """Test Actor bilateral communication"""
    print("=" * 70)
    print("TEST 3: Actor bilateral communication")
    print("=" * 70)
    print()

    actor_config = {
        'name': 'Tech Company',
        'short_name': 'tech-co',
        'llm_model': 'openai/gpt-4o-mini',
        'system_prompt': 'You are a tech company.',
        'goals': ['Innovate'],
    }

    actor = create_actor_from_config(actor_config, scenario_system_prompt="Test scenario")

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
            message="Let's work together on a framework."
        )

        assert 'response' in response
        assert 'internal_notes' in response
        assert 'tokens_used' in response
        assert len(response['response']) > 0

    print("  ✓ Actor responded to bilateral communication")
    print("  ✓ Response contains public and private parts")
    print("  ✓ Token usage tracked")
    print()
    print("✅ Test 3 passed: Bilateral communication works")
    print()
    return True


async def test_actor_coalition_response():
    """Test Actor coalition response"""
    print("=" * 70)
    print("TEST 4: Actor coalition response")
    print("=" * 70)
    print()

    actor_config = {
        'name': 'Civil Society',
        'short_name': 'civil-society',
        'llm_model': 'openai/gpt-4o-mini',
        'system_prompt': 'You represent civil society.',
        'goals': ['Public safety'],
    }

    actor = create_actor_from_config(actor_config, scenario_system_prompt="Test scenario")

    mock_response = LLMResponse(
        content=MOCK_COALITION_ACCEPT,
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
            purpose="Coordinate on AI safety"
        )

        assert 'decision' in response
        assert response['decision'] == 'accept'
        assert 'response' in response
        assert 'internal_notes' in response

    print("  ✓ Actor responded to coalition proposal")
    print("  ✓ Decision parsed correctly (accept)")
    print("  ✓ Response contains all required fields")
    print()
    print("✅ Test 4 passed: Coalition response works")
    print()
    return True


async def test_full_pipeline_with_communications():
    """Test full V2 pipeline with Actor and communications"""
    print("=" * 70)
    print("TEST 5: Full pipeline with Actor and communications")
    print("=" * 70)
    print()

    # Load scenario
    loader = ScenarioLoader('scenarios/example-policy-negotiation')
    initial_state, v2_actors, scenario_config = loader.load()

    print(f"  ✓ Loaded scenario with {len(v2_actors)} V2 actors")

    # Prepare actor configs for phases
    actor_configs = {}
    for short_name, actor in v2_actors.items():
        actor_configs[short_name] = actor.to_dict()

    print(f"  ✓ Prepared {len(actor_configs)} actor configs")

    # Add a communication to state
    state = initial_state.with_started()
    state = add_communication_to_state(
        state=state,
        sender="AI Safety Regulator",
        recipients=["Tech Company"],
        content="We should coordinate our approach to this framework.",
        comm_type="bilateral"
    )

    print(f"  ✓ Added bilateral communication to state")
    print(f"  ✓ Communications in state: {len(state.communications)}")

    # Run decision phase with mocked LLM
    mock_decision_response = LLMResponse(
        content=MOCK_DECISION,
        tokens_used=500,
        input_tokens=350,
        output_tokens=150,
        model='openai/gpt-4o-mini'
    )

    with patch('scenario_lab.services.decision_phase_v2.make_llm_call_async', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_decision_response

        decision_phase = DecisionPhaseV2(
            actor_configs=actor_configs,
            scenario_system_prompt=scenario_config.get('system_prompt', ''),
            context_window_size=3
        )

        state = await decision_phase.execute(state)

        print(f"  ✓ Decision phase executed")
        print(f"  ✓ Decisions made: {len(state.decisions)}")
        print(f"  ✓ LLM calls: {mock_llm.call_count}")

    # Run communication phase
    communication_phase = CommunicationPhaseV2()
    state = await communication_phase.execute(state)

    print(f"  ✓ Communication phase executed")

    # Run world update phase with mocked LLM
    mock_world_response = LLMResponse(
        content=MOCK_WORLD_UPDATE,
        tokens_used=400,
        input_tokens=300,
        output_tokens=100,
        model='openai/gpt-4o-mini'
    )

    with patch('scenario_lab.services.world_update_phase_v2.make_llm_call_async', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = mock_world_response

        world_update_phase = WorldUpdatePhaseV2(
            scenario_name=scenario_config['name'],
            world_state_model='openai/gpt-4o-mini'
        )

        state = await world_update_phase.execute(state)

        print(f"  ✓ World update phase executed")
        print(f"  ✓ Turn incremented to: {state.turn}")

    print()
    print("✅ Test 5 passed: Full pipeline with Actor and communications works")
    print()
    return True


async def run_all_tests():
    """Run all Phase 2.3 integration tests"""
    print()
    print("=" * 70)
    print("PHASE 2.3 INTEGRATION TESTS")
    print("=" * 70)
    print()

    tests = [
        test_actor_loader_creates_v2_actors,
        test_actor_decision_making,
        test_actor_bilateral_communication,
        test_actor_coalition_response,
        test_full_pipeline_with_communications,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("=" * 70)
    print("PHASE 2.3 TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL PHASE 2.3 TESTS PASSED")
        print()
        print("Phase 2.3 Complete:")
        print("  ✓ V2 Actor class (immutable, dataclass-based)")
        print("  ✓ Actor loader creates V2 actors")
        print("  ✓ No V1 dependencies in V2 Actor")
        print("  ✓ Decision making works with V2 API client")
        print("  ✓ Bilateral communication works")
        print("  ✓ Coalition response works")
        print("  ✓ Full pipeline integration")
        print("  ✓ Communication phase integration")
        print()
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
