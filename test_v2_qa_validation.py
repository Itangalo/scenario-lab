#!/usr/bin/env python3
"""
Test V2 QA Validation

Tests the quality assurance validation system.
"""
import asyncio
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.core.qa_validator import QAValidator, ValidationResult, load_qa_validator, save_validation_report
from scenario_lab.services.world_update_phase_v2 import WorldUpdatePhaseV2
from scenario_lab.models.state import ScenarioState, WorldState, Decision
from scenario_lab.utils.api_client import LLMResponse


# Test validation-rules.yaml
TEST_VALIDATION_RULES = """
validation_model: "openai/gpt-4o-mini"
run_after_each_turn: true

checks:
  actor_decision_consistency:
    enabled: true
    prompt_template: |
      Review this actor's decision for consistency with their profile.

      Actor Profile:
      {actor_profile}

      World State:
      {world_state}

      Actor's Reasoning:
      {actor_reasoning}

      Actor's Action:
      {actor_action}

      Is this decision consistent with the actor's goals, constraints, and expertise?

      Respond with:
      PASSED: Yes/No
      ISSUES: (list any inconsistencies)
      SEVERITY: Low/Medium/High
      EXPLANATION: (brief explanation)

  world_state_coherence:
    enabled: true
    prompt_template: |
      Review the world state update for logical coherence.

      Previous World State:
      {previous_world_state}

      Actor Actions:
      {actor_actions}

      New World State:
      {new_world_state}

      Does the new world state logically follow from the actions taken?

      Respond with:
      PASSED: Yes/No
      ISSUES: (list any incoherencies)
      SEVERITY: Low/Medium/High
      EXPLANATION: (brief explanation)

  information_access_consistency:
    enabled: false
"""

# Mock validation responses
MOCK_VALIDATION_PASSED = """PASSED: Yes
ISSUES: None
SEVERITY: -
EXPLANATION: The decision is consistent with the actor's profile and goals."""

MOCK_VALIDATION_FAILED = """PASSED: No
ISSUES: Actor's action contradicts their stated constraint about cautious development
SEVERITY: High
EXPLANATION: The actor has a constraint requiring careful safety testing, but the action suggests rushing deployment."""


async def test_validation_rules_loading():
    """Test loading validation rules from YAML"""
    print("=" * 70)
    print("TEST 1: Loading validation rules")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write test rules YAML
        rules_file = Path(tmpdir) / "validation-rules.yaml"
        with open(rules_file, 'w') as f:
            f.write(TEST_VALIDATION_RULES)

        # Load validator
        validator = QAValidator(rules_file)

        assert validator.is_enabled()
        assert validator.should_run_after_turn()
        assert validator.validation_model == "openai/gpt-4o-mini"

        print(f"  ✓ Loaded validation rules")
        print(f"  ✓ Validation model: {validator.validation_model}")
        print(f"  ✓ Run after each turn: {validator.should_run_after_turn()}")

        # Check individual checks
        checks = validator.validation_rules.get('checks', {})
        assert 'actor_decision_consistency' in checks
        assert checks['actor_decision_consistency']['enabled']
        assert 'world_state_coherence' in checks
        assert checks['world_state_coherence']['enabled']

        print(f"  ✓ Actor decision consistency check: enabled")
        print(f"  ✓ World state coherence check: enabled")

    print()
    print("✅ Test 1 passed: Validation rules loaded correctly")
    print()
    return True


async def test_actor_decision_validation():
    """Test actor decision validation"""
    print("=" * 70)
    print("TEST 2: Actor decision validation")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        rules_file = Path(tmpdir) / "validation-rules.yaml"
        with open(rules_file, 'w') as f:
            f.write(TEST_VALIDATION_RULES)

        validator = QAValidator(rules_file)

        # Test data
        actor_profile = {
            'name': 'AI Developer',
            'goals': ['Advance AI capabilities safely', 'Maintain high safety standards'],
            'constraints': ['Must ensure adequate safety testing before deployment'],
            'expertise': {'domain': 'AI development'},
            'decision_style': 'Cautious'
        }

        world_state = "The AI development landscape is rapidly evolving."
        actor_reasoning = "We need to accelerate development to stay competitive."
        actor_action = "Deploy new AI system with minimal testing."

        # Mock LLM response (validation should fail)
        mock_response = LLMResponse(
            content=MOCK_VALIDATION_FAILED,
            tokens_used=200,
            input_tokens=150,
            output_tokens=50,
            model='openai/gpt-4o-mini'
        )

        with patch('scenario_lab.core.qa_validator.make_llm_call_async', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await validator.validate_actor_decision(
                actor_profile=actor_profile,
                world_state=world_state,
                actor_reasoning=actor_reasoning,
                actor_action=actor_action,
                turn=1
            )

        assert result is not None
        assert not result.passed  # Should fail due to inconsistency
        assert len(result.issues) > 0
        assert result.severity == "High"

        print(f"  ✓ Validation executed")
        print(f"  ✓ Result: {'PASSED' if result.passed else 'FAILED'}")
        print(f"  ✓ Severity: {result.severity}")
        print(f"  ✓ Issues found: {len(result.issues)}")
        if result.issues:
            print(f"    - {result.issues[0][:80]}...")

    print()
    print("✅ Test 2 passed: Actor decision validation works")
    print()
    return True


async def test_world_state_coherence_validation():
    """Test world state coherence validation"""
    print("=" * 70)
    print("TEST 3: World state coherence validation")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        rules_file = Path(tmpdir) / "validation-rules.yaml"
        with open(rules_file, 'w') as f:
            f.write(TEST_VALIDATION_RULES)

        validator = QAValidator(rules_file)

        # Test data
        previous_world_state = "Two nations are in diplomatic negotiations."
        actor_actions = {
            'Nation A': 'Propose a trade agreement',
            'Nation B': 'Accept the trade agreement'
        }
        new_world_state = "A trade agreement has been successfully negotiated between Nation A and Nation B."

        # Mock LLM response (validation should pass)
        mock_response = LLMResponse(
            content=MOCK_VALIDATION_PASSED,
            tokens_used=150,
            input_tokens=120,
            output_tokens=30,
            model='openai/gpt-4o-mini'
        )

        with patch('scenario_lab.core.qa_validator.make_llm_call_async', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            result = await validator.validate_world_state_update(
                previous_world_state=previous_world_state,
                actor_actions=actor_actions,
                new_world_state=new_world_state,
                turn=1
            )

        assert result is not None
        assert result.passed  # Should pass - coherent update
        assert len(result.issues) == 0

        print(f"  ✓ Validation executed")
        print(f"  ✓ Result: {'PASSED' if result.passed else 'FAILED'}")
        print(f"  ✓ Check name: {result.check_name}")

    print()
    print("✅ Test 3 passed: World state coherence validation works")
    print()
    return True


async def test_validation_cost_tracking():
    """Test validation cost tracking"""
    print("=" * 70)
    print("TEST 4: Validation cost tracking")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        rules_file = Path(tmpdir) / "validation-rules.yaml"
        with open(rules_file, 'w') as f:
            f.write(TEST_VALIDATION_RULES)

        validator = QAValidator(rules_file)

        # Create a validation result
        validation_result = ValidationResult(
            check_name="test_check",
            passed=True,
            tokens_used=250
        )

        # Create cost record
        cost_record = validator.create_cost_record(validation_result, turn=1)

        assert cost_record.phase == "qa_validation"
        assert cost_record.model == validator.validation_model
        assert cost_record.input_tokens > 0
        assert cost_record.output_tokens > 0
        assert cost_record.cost > 0

        print(f"  ✓ Cost record created")
        print(f"  ✓ Phase: {cost_record.phase}")
        print(f"  ✓ Model: {cost_record.model}")
        print(f"  ✓ Total tokens: {cost_record.input_tokens + cost_record.output_tokens}")
        print(f"  ✓ Cost: ${cost_record.cost:.6f}")

    print()
    print("✅ Test 4 passed: Validation cost tracking works")
    print()
    return True


async def test_validation_report_generation():
    """Test validation report generation"""
    print("=" * 70)
    print("TEST 5: Validation report generation")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create validation results
        results = [
            ValidationResult(
                check_name="actor_decision_consistency",
                passed=True,
                tokens_used=200
            ),
            ValidationResult(
                check_name="world_state_coherence",
                passed=False,
                issues=["World state does not reflect action consequences"],
                severity="Medium",
                tokens_used=180
            )
        ]

        # Save report
        report_path = Path(tmpdir) / "validation-report-001.md"
        await save_validation_report(results, report_path, turn=1)

        assert report_path.exists()

        # Read and verify
        content = report_path.read_text()
        assert "QA Validation Report - Turn 1" in content
        assert "**Total Checks:** 2" in content
        assert "**Passed:** 1" in content
        assert "**Failed:** 1" in content
        assert "actor_decision_consistency" in content
        assert "world_state_coherence" in content

        print(f"  ✓ Report generated: {report_path.name}")
        print(f"  ✓ Report contains summary")
        print(f"  ✓ Report contains all checks")
        print(f"  ✓ Report size: {len(content)} characters")

    print()
    print("✅ Test 5 passed: Validation report generation works")
    print()
    return True


async def test_integration_with_world_update_phase():
    """Test QA validation integration with world update phase"""
    print("=" * 70)
    print("TEST 6: Integration with world update phase")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup validator
        rules_file = Path(tmpdir) / "validation-rules.yaml"
        with open(rules_file, 'w') as f:
            f.write(TEST_VALIDATION_RULES)

        validator = QAValidator(rules_file)

        # Create initial state with decisions
        state = ScenarioState(
            scenario_id="test",
            scenario_name="Test Scenario",
            run_id="test-run",
            scenario_config={"num_turns": 5},
            world_state=WorldState(turn=0, content="Initial state")
        )
        state = state.with_started()

        # Add decisions
        state = state.with_decision("Actor1", Decision(
            actor="Actor1",
            turn=0,
            goals=["Goal 1"],
            reasoning="Reasoning 1",
            action="Action 1"
        ))

        # Create world update phase with QA validator
        world_update_phase = WorldUpdatePhaseV2(
            scenario_name="Test Scenario",
            world_state_model="openai/gpt-4o-mini",
            qa_validator=validator
        )

        # Mock responses
        mock_world_update = LLMResponse(
            content="""**UPDATED STATE:**
The situation has evolved based on Actor1's action.

**KEY CHANGES:**
- Action 1 was implemented
- State progressed

**CONSEQUENCES:**
- New situation emerged""",
            tokens_used=400,
            input_tokens=300,
            output_tokens=100,
            model='openai/gpt-4o-mini'
        )

        mock_validation = LLMResponse(
            content=MOCK_VALIDATION_PASSED,
            tokens_used=150,
            input_tokens=120,
            output_tokens=30,
            model='openai/gpt-4o-mini'
        )

        with patch('scenario_lab.services.world_update_phase_v2.make_llm_call_async', new_callable=AsyncMock) as mock_world_llm:
            mock_world_llm.return_value = mock_world_update

            with patch('scenario_lab.core.qa_validator.make_llm_call_async', new_callable=AsyncMock) as mock_val_llm:
                mock_val_llm.return_value = mock_validation

                state = await world_update_phase.execute(state)

        print(f"  ✓ World update phase executed")
        print(f"  ✓ Turn incremented to: {state.turn}")
        print(f"  ✓ Validation executed (LLM called)")

        # Check costs include both world update and validation
        assert len(state.costs) >= 2  # At least world update + validation
        validation_costs = [c for c in state.costs if c.phase == "qa_validation"]
        assert len(validation_costs) > 0

        print(f"  ✓ Validation costs tracked: {len(validation_costs)} records")

    print()
    print("✅ Test 6 passed: Integration with world update phase works")
    print()
    return True


async def run_all_tests():
    """Run all QA validation tests"""
    print()
    print("=" * 70)
    print("V2 QA VALIDATION TESTS")
    print("=" * 70)
    print()

    tests = [
        test_validation_rules_loading,
        test_actor_decision_validation,
        test_world_state_coherence_validation,
        test_validation_cost_tracking,
        test_validation_report_generation,
        test_integration_with_world_update_phase,
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
    print("QA VALIDATION TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL QA VALIDATION TESTS PASSED")
        print()
        print("Phase 3.4 Complete: QA Validation")
        print("  ✓ Validation rules loading from YAML")
        print("  ✓ Actor decision consistency validation")
        print("  ✓ World state coherence validation")
        print("  ✓ Validation cost tracking")
        print("  ✓ Validation report generation")
        print("  ✓ Integration with world update phase")
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
