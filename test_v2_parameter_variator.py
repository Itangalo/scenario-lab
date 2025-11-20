#!/usr/bin/env python3
"""
Test V2 Parameter Variator

Tests the parameter variation system for batch execution.
"""
import sys
import tempfile
from pathlib import Path
import yaml

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.batch.parameter_variator import ParameterVariator


def test_simple_actor_model_variation():
    """Test simple actor model variation"""
    print("=" * 70)
    print("TEST 1: Simple actor model variation")
    print("=" * 70)
    print()

    variations_config = [
        {
            'type': 'actor_model',
            'actor': 'Actor1',
            'values': ['openai/gpt-4o', 'openai/gpt-4o-mini']
        }
    ]

    variator = ParameterVariator('dummy_path', variations_config)
    variations = variator.generate_variations()

    assert len(variations) == 2
    assert variations[0]['variation_id'] == 1
    assert variations[1]['variation_id'] == 2

    print(f"  ✓ Generated {len(variations)} variations")
    for var in variations:
        print(f"    - Variation {var['variation_id']}: {var['description']}")
        print(f"      Modifications: {var['modifications']}")

    # Check modifications
    assert 'Actor1' in variations[0]['modifications']['actor_models']
    assert variations[0]['modifications']['actor_models']['Actor1'] == 'openai/gpt-4o'
    assert variations[1]['modifications']['actor_models']['Actor1'] == 'openai/gpt-4o-mini'

    print()
    print("✅ Test 1 passed: Simple actor model variation works")
    print()
    return True


def test_cartesian_product_variations():
    """Test Cartesian product of multiple dimensions"""
    print("=" * 70)
    print("TEST 2: Cartesian product variations")
    print("=" * 70)
    print()

    variations_config = [
        {
            'type': 'actor_model',
            'actor': 'Actor1',
            'values': ['openai/gpt-4o', 'openai/gpt-4o-mini']
        },
        {
            'type': 'actor_model',
            'actor': 'Actor2',
            'values': ['anthropic/claude-3-haiku', 'anthropic/claude-3-sonnet']
        }
    ]

    variator = ParameterVariator('dummy_path', variations_config)
    variations = variator.generate_variations()

    # Should be 2 x 2 = 4 combinations
    assert len(variations) == 4
    print(f"  ✓ Generated {len(variations)} variations (2 x 2 Cartesian product)")

    for var in variations:
        print(f"    - Variation {var['variation_id']}: {var['description']}")

    # Check that we have all combinations
    actor1_models = set()
    actor2_models = set()
    for var in variations:
        mods = var['modifications']['actor_models']
        actor1_models.add(mods['Actor1'])
        actor2_models.add(mods['Actor2'])

    assert len(actor1_models) == 2
    assert len(actor2_models) == 2

    print(f"  ✓ All combinations present")
    print(f"    - Actor1 models: {actor1_models}")
    print(f"    - Actor2 models: {actor2_models}")

    print()
    print("✅ Test 2 passed: Cartesian product works correctly")
    print()
    return True


def test_three_dimension_variations():
    """Test three-dimensional variation space"""
    print("=" * 70)
    print("TEST 3: Three-dimensional variation space")
    print("=" * 70)
    print()

    variations_config = [
        {
            'type': 'actor_model',
            'actor': 'Actor1',
            'values': ['model-a1', 'model-a2']
        },
        {
            'type': 'actor_model',
            'actor': 'Actor2',
            'values': ['model-b1', 'model-b2']
        },
        {
            'type': 'actor_model',
            'actor': 'Actor3',
            'values': ['model-c1', 'model-c2', 'model-c3']
        }
    ]

    variator = ParameterVariator('dummy_path', variations_config)
    variations = variator.generate_variations()

    # Should be 2 x 2 x 3 = 12 combinations
    expected_count = 2 * 2 * 3
    assert len(variations) == expected_count
    print(f"  ✓ Generated {len(variations)} variations (2 x 2 x 3 Cartesian product)")

    # Verify variation count method
    assert variator.get_variation_count() == expected_count
    print(f"  ✓ get_variation_count() returns {expected_count}")

    # Verify estimate_total_runs
    runs_per_variation = 5
    total_runs = variator.estimate_total_runs(runs_per_variation)
    assert total_runs == expected_count * runs_per_variation
    print(f"  ✓ estimate_total_runs(5) = {total_runs} ({expected_count} × 5)")

    print()
    print("✅ Test 3 passed: Three-dimensional variations work correctly")
    print()
    return True


def test_no_variations():
    """Test behavior with no variations specified"""
    print("=" * 70)
    print("TEST 4: No variations specified")
    print("=" * 70)
    print()

    variations_config = []

    variator = ParameterVariator('dummy_path', variations_config)
    variations = variator.generate_variations()

    # Should return single base configuration
    assert len(variations) == 1
    assert variations[0]['variation_id'] == 1
    assert variations[0]['description'] == 'Base configuration'
    assert variations[0]['modifications'] == {}

    print(f"  ✓ Generated 1 variation (base configuration)")
    print(f"  ✓ Description: {variations[0]['description']}")

    print()
    print("✅ Test 4 passed: No variations returns base configuration")
    print()
    return True


def test_scenario_parameter_variation():
    """Test scenario parameter variation (not just actor models)"""
    print("=" * 70)
    print("TEST 5: Scenario parameter variation")
    print("=" * 70)
    print()

    variations_config = [
        {
            'type': 'scenario_parameter',
            'parameter': 'max_turns',
            'values': [5, 10, 15]
        }
    ]

    variator = ParameterVariator('dummy_path', variations_config)
    variations = variator.generate_variations()

    assert len(variations) == 3
    print(f"  ✓ Generated {len(variations)} variations for scenario parameter")

    for i, var in enumerate(variations):
        expected_value = [5, 10, 15][i]
        assert var['modifications']['scenario_overrides']['max_turns'] == expected_value
        print(f"    - Variation {var['variation_id']}: max_turns={expected_value}")

    print()
    print("✅ Test 5 passed: Scenario parameter variation works")
    print()
    return True


def test_mixed_variations():
    """Test mixed actor model and scenario parameter variations"""
    print("=" * 70)
    print("TEST 6: Mixed actor and scenario parameter variations")
    print("=" * 70)
    print()

    variations_config = [
        {
            'type': 'actor_model',
            'actor': 'Actor1',
            'values': ['model-a', 'model-b']
        },
        {
            'type': 'scenario_parameter',
            'parameter': 'max_turns',
            'values': [5, 10]
        }
    ]

    variator = ParameterVariator('dummy_path', variations_config)
    variations = variator.generate_variations()

    # Should be 2 x 2 = 4 combinations
    assert len(variations) == 4
    print(f"  ✓ Generated {len(variations)} mixed variations (2 x 2)")

    for var in variations:
        print(f"    - Variation {var['variation_id']}: {var['description']}")
        mods = var['modifications']
        assert 'Actor1' in mods['actor_models']
        assert 'max_turns' in mods['scenario_overrides']

    print()
    print("✅ Test 6 passed: Mixed variations work correctly")
    print()
    return True


def test_apply_variation_to_scenario():
    """Test applying variation to create modified scenario"""
    print("=" * 70)
    print("TEST 7: Apply variation to scenario")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create base scenario
        base_dir = Path(tmpdir) / 'base_scenario'
        base_dir.mkdir()

        # Create scenario.yaml
        scenario_config = {
            'name': 'Test Scenario',
            'max_turns': 10,
            'turn_duration': '1 month'
        }
        with open(base_dir / 'scenario.yaml', 'w') as f:
            yaml.safe_dump(scenario_config, f)

        # Create actors directory
        actors_dir = base_dir / 'actors'
        actors_dir.mkdir()

        # Create actor files
        actor1_config = {
            'name': 'Actor One',
            'short_name': 'Actor1',
            'llm_model': 'openai/gpt-4o'
        }
        with open(actors_dir / 'actor1.yaml', 'w') as f:
            yaml.safe_dump(actor1_config, f)

        actor2_config = {
            'name': 'Actor Two',
            'short_name': 'Actor2',
            'llm_model': 'anthropic/claude-3-haiku'
        }
        with open(actors_dir / 'actor2.yaml', 'w') as f:
            yaml.safe_dump(actor2_config, f)

        print(f"  ✓ Created base scenario at {base_dir}")

        # Create variation
        variations_config = [
            {
                'type': 'actor_model',
                'actor': 'Actor1',
                'values': ['openai/gpt-4o-mini']
            }
        ]

        variator = ParameterVariator(str(base_dir), variations_config)
        variations = variator.generate_variations()

        # Apply variation
        temp_scenario_dir = Path(tmpdir) / 'temp_scenario'
        result_path = variator.apply_variation_to_scenario(
            variations[0],
            str(temp_scenario_dir)
        )

        assert Path(result_path).exists()
        print(f"  ✓ Applied variation to {result_path}")

        # Verify modified scenario.yaml exists
        assert (Path(result_path) / 'scenario.yaml').exists()
        print(f"  ✓ scenario.yaml created")

        # Verify modified actor files
        modified_actor1 = Path(result_path) / 'actors' / 'actor1.yaml'
        assert modified_actor1.exists()

        with open(modified_actor1, 'r') as f:
            modified_config = yaml.safe_load(f)

        assert modified_config['llm_model'] == 'openai/gpt-4o-mini'
        print(f"  ✓ Actor1 model modified to {modified_config['llm_model']}")

        # Verify Actor2 unchanged
        modified_actor2 = Path(result_path) / 'actors' / 'actor2.yaml'
        with open(modified_actor2, 'r') as f:
            modified_config = yaml.safe_load(f)

        assert modified_config['llm_model'] == 'anthropic/claude-3-haiku'
        print(f"  ✓ Actor2 model unchanged: {modified_config['llm_model']}")

    print()
    print("✅ Test 7 passed: Apply variation works correctly")
    print()
    return True


def test_description_generation():
    """Test human-readable description generation"""
    print("=" * 70)
    print("TEST 8: Description generation")
    print("=" * 70)
    print()

    variations_config = [
        {
            'type': 'actor_model',
            'actor': 'Actor1',
            'values': ['openai/gpt-4o', 'openai/gpt-4o-mini']
        },
        {
            'type': 'actor_model',
            'actor': 'Actor2',
            'values': ['anthropic/claude-3-haiku']
        }
    ]

    variator = ParameterVariator('dummy_path', variations_config)
    variations = variator.generate_variations()

    # Check descriptions are human-readable
    for var in variations:
        desc = var['description']
        assert 'Actor1=' in desc
        assert 'Actor2=' in desc
        # Should use short model name (not full path)
        assert 'gpt-4o' in desc or 'gpt-4o-mini' in desc
        assert 'claude-3-haiku' in desc
        print(f"  ✓ Variation {var['variation_id']}: {desc}")

    print()
    print("✅ Test 8 passed: Description generation works correctly")
    print()
    return True


def run_all_tests():
    """Run all parameter variator tests"""
    print()
    print("=" * 70)
    print("V2 PARAMETER VARIATOR TESTS")
    print("=" * 70)
    print()

    tests = [
        test_simple_actor_model_variation,
        test_cartesian_product_variations,
        test_three_dimension_variations,
        test_no_variations,
        test_scenario_parameter_variation,
        test_mixed_variations,
        test_apply_variation_to_scenario,
        test_description_generation,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("=" * 70)
    print("PARAMETER VARIATOR TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL PARAMETER VARIATOR TESTS PASSED")
        print()
        print("Phase 4.1 Complete: Parameter Variation")
        print("  ✓ Simple actor model variations")
        print("  ✓ Cartesian product generation (2D, 3D)")
        print("  ✓ Scenario parameter variations")
        print("  ✓ Mixed actor and scenario variations")
        print("  ✓ Variation application to scenario files")
        print("  ✓ Human-readable descriptions")
        print("  ✓ Variation count estimation")
        print("  ✓ Total runs estimation")
        print()
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
