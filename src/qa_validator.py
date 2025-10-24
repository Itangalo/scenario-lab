"""
Quality Assurance Validator - Automated consistency checking for scenarios

Uses lightweight LLM models to validate:
- Actor decision consistency (goals, constraints, expertise alignment)
- World state coherence (logical consequences of actions)
- Information access consistency (actors only use available information)
"""
import os
import yaml
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from api_utils import make_openrouter_call


class ValidationResult:
    """Represents the result of a single validation check"""

    def __init__(
        self,
        check_name: str,
        passed: bool,
        issues: List[str],
        severity: Optional[str] = None,
        explanation: str = "",
        tokens_used: int = 0
    ):
        self.check_name = check_name
        self.passed = passed
        self.issues = issues
        self.severity = severity  # Low/Medium/High (only if issues found)
        self.explanation = explanation
        self.tokens_used = tokens_used
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "issues": self.issues,
            "severity": self.severity,
            "explanation": self.explanation,
            "tokens_used": self.tokens_used,
            "timestamp": self.timestamp.isoformat()
        }


class QAValidator:
    """
    Quality Assurance Validator for scenario consistency checking
    """

    def __init__(self, scenario_path: str, api_key: str):
        """
        Initialize QA Validator

        Args:
            scenario_path: Path to scenario directory
            api_key: OpenRouter API key
        """
        self.scenario_path = scenario_path
        self.api_key = api_key
        self.validation_rules = self._load_validation_rules()
        self.validation_results = []  # List of ValidationResult objects
        self.total_tokens = 0
        self.total_cost = 0.0

    def _load_validation_rules(self) -> Optional[Dict[str, Any]]:
        """Load validation rules from validation-rules.yaml"""
        rules_path = os.path.join(self.scenario_path, 'validation-rules.yaml')

        if not os.path.exists(rules_path):
            print(f"⚠️  No validation-rules.yaml found in {self.scenario_path}")
            return None

        with open(rules_path, 'r') as f:
            return yaml.safe_load(f)

    def is_enabled(self) -> bool:
        """Check if validation is enabled for this scenario"""
        return self.validation_rules is not None

    def should_run_after_turn(self) -> bool:
        """Check if validation should run after each turn"""
        if not self.validation_rules:
            return False
        return self.validation_rules.get('run_after_each_turn', True)

    def validate_actor_decision(
        self,
        actor_profile: Dict[str, Any],
        world_state: str,
        actor_reasoning: str,
        actor_action: str,
        turn: int
    ) -> Optional[ValidationResult]:
        """
        Validate an actor's decision for consistency with their profile

        Args:
            actor_profile: Actor's YAML profile data
            world_state: Current world state text
            actor_reasoning: Actor's reasoning for this turn
            actor_action: Actor's action for this turn
            turn: Current turn number

        Returns:
            ValidationResult or None if check is disabled
        """
        if not self.validation_rules:
            return None

        check_config = self.validation_rules.get('checks', {}).get('actor_decision_consistency', {})

        if not check_config.get('enabled', False):
            return None

        # Format actor profile as text
        profile_text = self._format_actor_profile(actor_profile)

        # Fill in the prompt template
        prompt = check_config['prompt_template'].format(
            actor_profile=profile_text,
            world_state=world_state,
            actor_reasoning=actor_reasoning,
            actor_action=actor_action
        )

        # Make LLM call
        result_text, tokens = self._make_validation_call(prompt)

        # Parse result
        validation_result = self._parse_validation_result(
            "actor_decision_consistency",
            result_text,
            tokens
        )

        self.validation_results.append(validation_result)
        self.total_tokens += tokens

        return validation_result

    def validate_world_state_update(
        self,
        previous_world_state: str,
        actor_actions: Dict[str, str],
        new_world_state: str,
        turn: int
    ) -> Optional[ValidationResult]:
        """
        Validate that world state update is coherent with actions

        Args:
            previous_world_state: World state from previous turn
            actor_actions: Dict of {actor_name: action_text}
            new_world_state: Newly generated world state
            turn: Current turn number

        Returns:
            ValidationResult or None if check is disabled
        """
        if not self.validation_rules:
            return None

        check_config = self.validation_rules.get('checks', {}).get('world_state_coherence', {})

        if not check_config.get('enabled', False):
            return None

        # Format actor actions as text
        actions_text = "\n\n".join([
            f"**{actor}:**\n{action}"
            for actor, action in actor_actions.items()
        ])

        # Fill in the prompt template
        prompt = check_config['prompt_template'].format(
            previous_world_state=previous_world_state,
            actor_actions=actions_text,
            new_world_state=new_world_state
        )

        # Make LLM call
        result_text, tokens = self._make_validation_call(prompt)

        # Parse result
        validation_result = self._parse_validation_result(
            "world_state_coherence",
            result_text,
            tokens
        )

        self.validation_results.append(validation_result)
        self.total_tokens += tokens

        return validation_result

    def validate_information_access(
        self,
        actor_name: str,
        actor_reasoning: str,
        public_world_state: str,
        private_communications: str,
        restricted_information: str,
        turn: int
    ) -> Optional[ValidationResult]:
        """
        Validate that actor only uses information they have access to

        Args:
            actor_name: Name of the actor
            actor_reasoning: Actor's reasoning text
            public_world_state: Public world state available to all
            private_communications: Communications this actor participated in
            restricted_information: Information this actor should NOT have
            turn: Current turn number

        Returns:
            ValidationResult or None if check is disabled
        """
        if not self.validation_rules:
            return None

        check_config = self.validation_rules.get('checks', {}).get('information_access_consistency', {})

        if not check_config.get('enabled', False):
            return None

        # Fill in the prompt template
        prompt = check_config['prompt_template'].format(
            actor_name=actor_name,
            public_world_state=public_world_state,
            private_communications=private_communications,
            restricted_information=restricted_information,
            actor_reasoning=actor_reasoning
        )

        # Make LLM call
        result_text, tokens = self._make_validation_call(prompt)

        # Parse result
        validation_result = self._parse_validation_result(
            "information_access_consistency",
            result_text,
            tokens
        )

        self.validation_results.append(validation_result)
        self.total_tokens += tokens

        return validation_result

    def _make_validation_call(self, prompt: str) -> tuple[str, int]:
        """
        Make an LLM API call for validation

        Args:
            prompt: Validation prompt

        Returns:
            Tuple of (response_text, tokens_used)
        """
        model = self.validation_rules.get('validation_model', 'openai/gpt-4o-mini')

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = make_openrouter_call(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            payload=payload
        )

        data = response.json()
        result_text = data['choices'][0]['message']['content']
        tokens_used = data.get('usage', {}).get('total_tokens', 0)

        return result_text, tokens_used

    def _parse_validation_result(
        self,
        check_name: str,
        result_text: str,
        tokens_used: int
    ) -> ValidationResult:
        """
        Parse validation result from LLM response

        Args:
            check_name: Name of the validation check
            result_text: LLM response text
            tokens_used: Tokens consumed

        Returns:
            ValidationResult object
        """
        # Parse the structured output from the LLM
        lines = result_text.strip().split('\n')

        passed = True
        issues = []
        severity = None
        explanation = ""

        current_section = None

        for line in lines:
            line = line.strip()

            # Detect section headers
            if line.startswith('CONSISTENT:') or line.startswith('COHERENT:') or line.startswith('VALID ACCESS:'):
                # Extract Yes/No
                value = line.split(':', 1)[1].strip().lower()
                passed = value == 'yes'

            elif line.startswith('ISSUES FOUND:') or line.startswith('VIOLATIONS FOUND:'):
                current_section = 'issues'

            elif line.startswith('SEVERITY:'):
                severity = line.split(':', 1)[1].strip()
                current_section = None

            elif line.startswith('EXPLANATION:'):
                current_section = 'explanation'

            elif line.startswith('-') and current_section == 'issues':
                issue_text = line[1:].strip()
                if issue_text.lower() != 'none':
                    issues.append(issue_text)

            elif current_section == 'explanation' and line:
                explanation += line + " "

        return ValidationResult(
            check_name=check_name,
            passed=passed,
            issues=issues,
            severity=severity,
            explanation=explanation.strip(),
            tokens_used=tokens_used
        )

    def _format_actor_profile(self, actor_profile: Dict[str, Any]) -> str:
        """Format actor profile as readable text"""
        parts = []

        parts.append(f"**Name:** {actor_profile.get('name', 'Unknown')}")

        if 'goals' in actor_profile:
            parts.append("\n**Goals:**")
            if isinstance(actor_profile['goals'], list):
                for goal in actor_profile['goals']:
                    parts.append(f"- {goal}")
            else:
                parts.append(str(actor_profile['goals']))

        if 'constraints' in actor_profile:
            parts.append("\n**Constraints:**")
            if isinstance(actor_profile['constraints'], list):
                for constraint in actor_profile['constraints']:
                    parts.append(f"- {constraint}")
            else:
                parts.append(str(actor_profile['constraints']))

        if 'expertise' in actor_profile:
            parts.append("\n**Expertise:**")
            for domain, level in actor_profile['expertise'].items():
                parts.append(f"- {domain}: {level}")

        if 'decision_style' in actor_profile:
            parts.append(f"\n**Decision Style:**\n{actor_profile['decision_style']}")

        return "\n".join(parts)

    def generate_turn_report(self, turn: int, output_dir: str):
        """
        Generate validation report for a specific turn

        Args:
            turn: Turn number
            output_dir: Directory to write report
        """
        if not self.validation_rules:
            return

        if not self.validation_rules.get('generate_turn_reports', True):
            return

        # Get results for this turn
        turn_results = [r for r in self.validation_results if r.timestamp]
        # Since we don't store turn in ValidationResult, we'll take the most recent results
        # This is a simplification - could be improved by adding turn to ValidationResult

        report_path = os.path.join(output_dir, f'validation-{turn:03d}.md')

        with open(report_path, 'w') as f:
            f.write(f"# Validation Report - Turn {turn}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            if not turn_results:
                f.write("*No validation checks performed this turn.*\n")
                return

            # Group by check type
            checks = {}
            for result in turn_results:
                if result.check_name not in checks:
                    checks[result.check_name] = []
                checks[result.check_name].append(result)

            # Write each check type
            for check_name, results in checks.items():
                f.write(f"## {check_name.replace('_', ' ').title()}\n\n")

                for result in results:
                    status_emoji = "✅" if result.passed else "⚠️"
                    f.write(f"{status_emoji} **{'PASSED' if result.passed else 'ISSUES FOUND'}**\n\n")

                    if not result.passed and result.issues:
                        f.write("**Issues:**\n\n")
                        for issue in result.issues:
                            f.write(f"- {issue}\n")
                        f.write("\n")

                        if result.severity:
                            f.write(f"**Severity:** {result.severity}\n\n")

                    if result.explanation:
                        f.write(f"**Explanation:** {result.explanation}\n\n")

                    f.write(f"*Tokens used: {result.tokens_used}*\n\n")
                    f.write("---\n\n")

    def generate_summary_report(self, output_dir: str):
        """
        Generate summary validation report for entire scenario

        Args:
            output_dir: Directory to write report
        """
        if not self.validation_rules:
            return

        if not self.validation_rules.get('generate_summary_report', True):
            return

        report_path = os.path.join(output_dir, 'validation-summary.md')

        with open(report_path, 'w') as f:
            f.write("# Validation Summary Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            if not self.validation_results:
                f.write("*No validation checks performed.*\n")
                return

            # Overall statistics
            total_checks = len(self.validation_results)
            passed_checks = sum(1 for r in self.validation_results if r.passed)
            failed_checks = total_checks - passed_checks

            f.write("## Summary Statistics\n\n")
            f.write(f"- **Total Checks:** {total_checks}\n")
            f.write(f"- **Passed:** {passed_checks} ({100*passed_checks/total_checks:.1f}%)\n")
            f.write(f"- **Failed:** {failed_checks} ({100*failed_checks/total_checks:.1f}%)\n")
            f.write(f"- **Total Tokens Used:** {self.total_tokens:,}\n")
            f.write(f"- **Estimated Cost:** ${self.total_cost:.4f}\n\n")

            # Breakdown by check type
            f.write("## Checks by Type\n\n")
            check_types = {}
            for result in self.validation_results:
                if result.check_name not in check_types:
                    check_types[result.check_name] = {"passed": 0, "failed": 0}

                if result.passed:
                    check_types[result.check_name]["passed"] += 1
                else:
                    check_types[result.check_name]["failed"] += 1

            for check_name, counts in check_types.items():
                total = counts["passed"] + counts["failed"]
                f.write(f"### {check_name.replace('_', ' ').title()}\n\n")
                f.write(f"- Passed: {counts['passed']}/{total}\n")
                f.write(f"- Failed: {counts['failed']}/{total}\n\n")

            # List all failures
            failures = [r for r in self.validation_results if not r.passed]

            if failures:
                f.write("## All Validation Failures\n\n")

                for result in failures:
                    f.write(f"### {result.check_name.replace('_', ' ').title()}\n\n")
                    f.write(f"**Time:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    if result.severity:
                        f.write(f"**Severity:** {result.severity}\n\n")

                    f.write("**Issues:**\n\n")
                    for issue in result.issues:
                        f.write(f"- {issue}\n")
                    f.write("\n")

                    if result.explanation:
                        f.write(f"**Explanation:** {result.explanation}\n\n")

                    f.write("---\n\n")

    def get_validation_costs(self) -> Dict[str, Any]:
        """
        Get validation cost breakdown for inclusion in costs.json

        Returns:
            Dict with validation cost data
        """
        return {
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 4),
            "checks_performed": len(self.validation_results),
            "model": self.validation_rules.get('validation_model', 'unknown') if self.validation_rules else 'unknown'
        }
