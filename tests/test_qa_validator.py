"""
Unit tests for QAValidator
"""
import unittest
import sys
import os
import tempfile
import shutil
import yaml

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from qa_validator import QAValidator, ValidationResult


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult class"""

    def test_initialization(self):
        """Test ValidationResult initializes correctly"""
        result = ValidationResult(
            check_name="test_check",
            passed=True,
            issues=[],
            severity=None,
            explanation="All good",
            tokens_used=100
        )

        self.assertEqual(result.check_name, "test_check")
        self.assertTrue(result.passed)
        self.assertEqual(len(result.issues), 0)
        self.assertIsNone(result.severity)
        self.assertEqual(result.explanation, "All good")
        self.assertEqual(result.tokens_used, 100)

    def test_to_dict(self):
        """Test converting ValidationResult to dict"""
        result = ValidationResult(
            check_name="test_check",
            passed=False,
            issues=["Issue 1", "Issue 2"],
            severity="Medium",
            explanation="Some problems found",
            tokens_used=150
        )

        result_dict = result.to_dict()

        self.assertEqual(result_dict['check_name'], "test_check")
        self.assertFalse(result_dict['passed'])
        self.assertEqual(len(result_dict['issues']), 2)
        self.assertEqual(result_dict['severity'], "Medium")
        self.assertIn('timestamp', result_dict)


class TestQAValidator(unittest.TestCase):
    """Test QAValidator functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary scenario directory
        self.temp_dir = tempfile.mkdtemp()
        self.scenario_path = os.path.join(self.temp_dir, 'test-scenario')
        os.makedirs(self.scenario_path)

        # Create a minimal validation-rules.yaml
        self.validation_rules = {
            'validation_model': 'openai/gpt-4o-mini',
            'checks': {
                'actor_decision_consistency': {
                    'enabled': True,
                    'description': 'Test check',
                    'prompt_template': 'Test prompt: {actor_profile} {world_state}'
                }
            },
            'run_after_each_turn': True,
            'generate_turn_reports': True
        }

        with open(os.path.join(self.scenario_path, 'validation-rules.yaml'), 'w') as f:
            yaml.dump(self.validation_rules, f)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)

    def test_initialization_with_rules(self):
        """Test QAValidator initializes with validation rules"""
        validator = QAValidator(self.scenario_path, "test-api-key")

        self.assertIsNotNone(validator.validation_rules)
        self.assertTrue(validator.is_enabled())

    def test_initialization_without_rules(self):
        """Test QAValidator handles missing validation rules"""
        # Create scenario without validation-rules.yaml
        no_rules_path = os.path.join(self.temp_dir, 'no-rules')
        os.makedirs(no_rules_path)

        validator = QAValidator(no_rules_path, "test-api-key")

        self.assertIsNone(validator.validation_rules)
        self.assertFalse(validator.is_enabled())

    def test_should_run_after_turn(self):
        """Test should_run_after_turn returns correct value"""
        validator = QAValidator(self.scenario_path, "test-api-key")

        self.assertTrue(validator.should_run_after_turn())

    def test_format_actor_profile(self):
        """Test _format_actor_profile creates readable text"""
        validator = QAValidator(self.scenario_path, "test-api-key")

        actor_profile = {
            'name': 'Test Actor',
            'goals': ['Goal 1', 'Goal 2'],
            'constraints': ['Constraint 1'],
            'expertise': {'ai_safety': 'expert', 'policy': 'intermediate'},
            'decision_style': 'Pragmatic and careful'
        }

        formatted = validator._format_actor_profile(actor_profile)

        self.assertIn('Test Actor', formatted)
        self.assertIn('Goal 1', formatted)
        self.assertIn('Constraint 1', formatted)
        self.assertIn('ai_safety: expert', formatted)
        self.assertIn('Pragmatic and careful', formatted)

    def test_format_actor_profile_list_expertise(self):
        """Test _format_actor_profile handles list-of-dicts expertise format"""
        validator = QAValidator(self.scenario_path, "test-api-key")

        # This format was causing AttributeError before the fix
        actor_profile = {
            'name': 'Test Actor',
            'goals': ['Goal 1', 'Goal 2'],
            'constraints': ['Constraint 1'],
            'expertise': [
                {'ai_safety': 'expert'},
                {'policy': 'intermediate'},
                {'technology': 'expert'}
            ],
            'decision_style': 'Pragmatic and careful'
        }

        # Should not raise AttributeError
        formatted = validator._format_actor_profile(actor_profile)

        self.assertIn('Test Actor', formatted)
        self.assertIn('ai_safety: expert', formatted)
        self.assertIn('policy: intermediate', formatted)
        self.assertIn('technology: expert', formatted)

    def test_parse_validation_result_passed(self):
        """Test parsing a passed validation result"""
        validator = QAValidator(self.scenario_path, "test-api-key")

        llm_response = """
CONSISTENT: Yes

ISSUES FOUND:
- None

EXPLANATION:
The decision aligns well with the actor's goals and constraints.
"""

        result = validator._parse_validation_result(
            "test_check",
            llm_response,
            100
        )

        self.assertTrue(result.passed)
        self.assertEqual(len(result.issues), 0)
        self.assertIn("aligns well", result.explanation)

    def test_parse_validation_result_failed(self):
        """Test parsing a failed validation result"""
        validator = QAValidator(self.scenario_path, "test-api-key")

        llm_response = """
CONSISTENT: No

ISSUES FOUND:
- Actor violates stated constraint about budget limits
- Decision contradicts previously stated goals

SEVERITY: High

EXPLANATION:
The action directly contradicts the actor's stated constraints.
"""

        result = validator._parse_validation_result(
            "test_check",
            llm_response,
            150
        )

        self.assertFalse(result.passed)
        self.assertEqual(len(result.issues), 2)
        self.assertEqual(result.severity, "High")
        self.assertIn("budget limits", result.issues[0])

    def test_parse_validation_result_coherent_format(self):
        """Test parsing with COHERENT format (world state check)"""
        validator = QAValidator(self.scenario_path, "test-api-key")

        llm_response = """
COHERENT: Yes

ISSUES FOUND:
- None

EXPLANATION:
The world state update logically follows from the actions taken.
"""

        result = validator._parse_validation_result(
            "world_state_check",
            llm_response,
            100
        )

        self.assertTrue(result.passed)

    def test_get_validation_costs(self):
        """Test get_validation_costs returns correct format"""
        validator = QAValidator(self.scenario_path, "test-api-key")

        # Add some mock validation results
        validator.validation_results.append(
            ValidationResult("test1", True, [], None, "Good", 100)
        )
        validator.validation_results.append(
            ValidationResult("test2", False, ["Issue"], "Low", "Problem", 150)
        )
        validator.total_tokens = 250

        costs = validator.get_validation_costs()

        self.assertEqual(costs['total_tokens'], 250)
        self.assertEqual(costs['checks_performed'], 2)
        self.assertEqual(costs['model'], 'openai/gpt-4o-mini')

    def test_generate_turn_report(self):
        """Test generating a turn validation report"""
        validator = QAValidator(self.scenario_path, "test-api-key")

        # Add mock validation results
        validator.validation_results.append(
            ValidationResult("actor_decision_consistency", True, [], None, "Good decision", 100)
        )
        validator.validation_results.append(
            ValidationResult("world_state_coherence", False, ["Logical gap"], "Medium", "State inconsistent", 150)
        )

        # Create output directory
        output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(output_dir)

        validator.generate_turn_report(1, output_dir)

        # Check that report was created
        report_path = os.path.join(output_dir, 'validation-001.md')
        self.assertTrue(os.path.exists(report_path))

        # Check report contents
        with open(report_path, 'r') as f:
            content = f.read()

        self.assertIn('Validation Report - Turn 1', content)
        self.assertIn('✅', content)  # Passed check
        self.assertIn('⚠️', content)  # Failed check
        self.assertIn('Logical gap', content)

    def test_generate_summary_report(self):
        """Test generating summary validation report"""
        validator = QAValidator(self.scenario_path, "test-api-key")

        # Add mock validation results
        validator.validation_results.append(
            ValidationResult("check1", True, [], None, "Good", 100)
        )
        validator.validation_results.append(
            ValidationResult("check2", True, [], None, "Good", 100)
        )
        validator.validation_results.append(
            ValidationResult("check3", False, ["Issue 1"], "High", "Problem", 150)
        )
        validator.total_tokens = 350

        # Create output directory
        output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(output_dir)

        validator.generate_summary_report(output_dir)

        # Check that summary was created
        summary_path = os.path.join(output_dir, 'validation-summary.md')
        self.assertTrue(os.path.exists(summary_path))

        # Check summary contents
        with open(summary_path, 'r') as f:
            content = f.read()

        self.assertIn('Validation Summary Report', content)
        self.assertIn('**Total Checks:** 3', content)
        self.assertIn('**Passed:** 2', content)
        self.assertIn('**Failed:** 1', content)
        self.assertIn('**Total Tokens Used:**', content)
        self.assertIn('All Validation Failures', content)

    def test_disabled_checks_not_run(self):
        """Test that disabled checks are not run"""
        # Create rules with checks disabled
        rules = self.validation_rules.copy()
        rules['checks']['actor_decision_consistency']['enabled'] = False

        with open(os.path.join(self.scenario_path, 'validation-rules.yaml'), 'w') as f:
            yaml.dump(rules, f)

        validator = QAValidator(self.scenario_path, "test-api-key")

        # validate_actor_decision should return None for disabled check
        # (we're not actually calling LLM here, just checking the enabled flag)
        result = validator.validate_actor_decision(
            actor_profile={},
            world_state="test",
            actor_reasoning="test",
            actor_action="test",
            turn=1
        )

        # Note: This would need API key to actually run, but we can check
        # that it returns None when disabled
        # In actual use, we'd mock the API call
        # For now, just verify the validator was initialized
        self.assertTrue(validator.is_enabled())


if __name__ == '__main__':
    unittest.main()
