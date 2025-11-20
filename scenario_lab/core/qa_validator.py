"""
Quality Assurance Validator for Scenario Lab V2

Automated consistency checking for scenarios using lightweight LLM models.

V2 Design:
- Pure functions (no mutable state)
- Works with ScenarioState
- Returns ValidationResult objects
- Uses V2 API client
- No V1 dependencies

Validation Checks:
- Actor decision consistency (goals, constraints, expertise alignment)
- World state coherence (logical consequences of actions)
- Information access consistency (actors only use available information)
"""
import yaml
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

from scenario_lab.utils.api_client import make_llm_call_async, LLMResponse
from scenario_lab.core.prompt_builder import build_messages_for_llm
from scenario_lab.models.state import ScenarioState, CostRecord
from scenario_lab.utils.model_pricing import calculate_cost

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a single validation check"""
    check_name: str
    passed: bool
    issues: List[str] = field(default_factory=list)
    severity: Optional[str] = None  # Low/Medium/High
    explanation: str = ""
    tokens_used: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

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
    Quality Assurance Validator for scenario consistency checking (V2)

    Unlike V1, this doesn't maintain validation history internally.
    Results are stored in ScenarioState and output files.
    """

    def __init__(self, validation_rules_path: Optional[Path] = None, api_key: Optional[str] = None):
        """
        Initialize QA Validator

        Args:
            validation_rules_path: Path to validation-rules.yaml file
            api_key: API key for LLM calls (optional, will use env var if not provided)
        """
        self.validation_rules: Optional[Dict[str, Any]] = None
        self.api_key = api_key
        self.validation_model = "openai/gpt-4o-mini"  # Default lightweight model

        if validation_rules_path and validation_rules_path.exists():
            self.load_validation_rules(validation_rules_path)

    def load_validation_rules(self, rules_path: Path):
        """
        Load validation rules from YAML file

        Args:
            rules_path: Path to validation-rules.yaml
        """
        try:
            with open(rules_path, 'r') as f:
                self.validation_rules = yaml.safe_load(f)

            self.validation_model = self.validation_rules.get('validation_model', 'openai/gpt-4o-mini')

            logger.info(f"Loaded QA validation rules from {rules_path}")
            logger.info(f"Validation model: {self.validation_model}")

        except Exception as e:
            logger.error(f"Failed to load validation rules from {rules_path}: {e}")
            raise

    def is_enabled(self) -> bool:
        """Check if validation is enabled"""
        return self.validation_rules is not None

    def should_run_after_turn(self) -> bool:
        """Check if validation should run after each turn"""
        if not self.validation_rules:
            return False
        return self.validation_rules.get('run_after_each_turn', True)

    async def validate_actor_decision(
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
            actor_profile: Actor's profile data (dict with name, goals, constraints, etc.)
            world_state: Current world state text
            actor_reasoning: Actor's reasoning for this turn
            actor_action: Actor's action for this turn
            turn: Current turn number

        Returns:
            ValidationResult or None if check is disabled
        """
        if not self.validation_rules:
            return None

        checks = self.validation_rules.get('checks', {})
        check_config = checks.get('actor_decision_consistency', {})

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
        llm_response = await self._make_validation_call(prompt)

        # Parse result
        validation_result = self._parse_validation_result(
            "actor_decision_consistency",
            llm_response.content,
            llm_response.tokens_used
        )

        return validation_result

    async def validate_world_state_update(
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

        checks = self.validation_rules.get('checks', {})
        check_config = checks.get('world_state_coherence', {})

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
        llm_response = await self._make_validation_call(prompt)

        # Parse result
        validation_result = self._parse_validation_result(
            "world_state_coherence",
            llm_response.content,
            llm_response.tokens_used
        )

        return validation_result

    async def validate_information_access(
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

        checks = self.validation_rules.get('checks', {})
        check_config = checks.get('information_access_consistency', {})

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
        llm_response = await self._make_validation_call(prompt)

        # Parse result
        validation_result = self._parse_validation_result(
            "information_access_consistency",
            llm_response.content,
            llm_response.tokens_used
        )

        return validation_result

    async def _make_validation_call(self, prompt: str) -> LLMResponse:
        """
        Make an LLM API call for validation

        Args:
            prompt: Validation prompt

        Returns:
            LLMResponse object
        """
        messages = build_messages_for_llm("", prompt)  # No system prompt for validation

        llm_response = await make_llm_call_async(
            model=self.validation_model,
            messages=messages,
            api_key=self.api_key,
            max_retries=3,
            context={'phase': 'qa_validation'}
        )

        return llm_response

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
        # Expected format:
        # PASSED: Yes/No
        # ISSUES: (list of issues if any)
        # SEVERITY: Low/Medium/High
        # EXPLANATION: (detailed explanation)

        passed = True
        issues = []
        severity = None
        explanation = ""

        lines = result_text.strip().split('\n')

        for line in lines:
            line = line.strip()

            if line.startswith('PASSED:'):
                value = line.split(':', 1)[1].strip().lower()
                passed = 'yes' in value or 'true' in value

            elif line.startswith('ISSUES:'):
                issues_text = line.split(':', 1)[1].strip()
                if issues_text and issues_text.lower() not in ['none', 'n/a', '-']:
                    # Split by newlines or bullet points
                    issue_lines = [i.strip() for i in issues_text.split('\n') if i.strip()]
                    issues.extend(issue_lines)

            elif line.startswith('SEVERITY:'):
                severity_text = line.split(':', 1)[1].strip()
                if severity_text and severity_text.lower() not in ['none', 'n/a', '-']:
                    severity = severity_text

            elif line.startswith('EXPLANATION:'):
                explanation = line.split(':', 1)[1].strip()

        # If no explicit format, treat the whole response as explanation
        if not any([passed is not None, issues, severity, explanation]):
            explanation = result_text.strip()
            # Try to determine if it passed based on keywords
            if any(word in result_text.lower() for word in ['inconsistent', 'violation', 'error', 'problem']):
                passed = False
                issues = [result_text[:200]]  # First 200 chars as issue

        return ValidationResult(
            check_name=check_name,
            passed=passed,
            issues=issues,
            severity=severity,
            explanation=explanation,
            tokens_used=tokens_used
        )

    def _format_actor_profile(self, actor_profile: Dict[str, Any]) -> str:
        """
        Format actor profile as text for validation prompts

        Args:
            actor_profile: Actor profile dict

        Returns:
            Formatted profile text
        """
        profile_parts = []

        if 'name' in actor_profile:
            profile_parts.append(f"**Name:** {actor_profile['name']}")

        if 'description' in actor_profile and actor_profile['description']:
            profile_parts.append(f"**Description:** {actor_profile['description']}")

        if 'goals' in actor_profile and actor_profile['goals']:
            goals_text = "\n".join(f"- {g}" for g in actor_profile['goals'])
            profile_parts.append(f"**Goals:**\n{goals_text}")

        if 'constraints' in actor_profile and actor_profile['constraints']:
            constraints_text = "\n".join(f"- {c}" for c in actor_profile['constraints'])
            profile_parts.append(f"**Constraints:**\n{constraints_text}")

        if 'expertise' in actor_profile and actor_profile['expertise']:
            if isinstance(actor_profile['expertise'], dict):
                expertise_text = "\n".join(
                    f"- {k}: {v}" for k, v in actor_profile['expertise'].items()
                )
            else:
                expertise_text = str(actor_profile['expertise'])
            profile_parts.append(f"**Expertise:**\n{expertise_text}")

        if 'decision_style' in actor_profile and actor_profile['decision_style']:
            profile_parts.append(f"**Decision Style:** {actor_profile['decision_style']}")

        return "\n\n".join(profile_parts)

    def create_cost_record(
        self,
        validation_result: ValidationResult,
        turn: int
    ) -> CostRecord:
        """
        Create a CostRecord from validation result

        Args:
            validation_result: Validation result
            turn: Current turn number

        Returns:
            CostRecord object
        """
        # Calculate cost based on tokens
        cost = calculate_cost(
            model=self.validation_model,
            input_tokens=int(validation_result.tokens_used * 0.7),  # Estimate
            output_tokens=int(validation_result.tokens_used * 0.3)
        )

        return CostRecord(
            timestamp=validation_result.timestamp,
            actor=None,  # Validation is not actor-specific
            phase="qa_validation",
            model=self.validation_model,
            input_tokens=int(validation_result.tokens_used * 0.7),
            output_tokens=int(validation_result.tokens_used * 0.3),
            cost=cost,
            metadata={'check_name': validation_result.check_name}
        )


def load_qa_validator(scenario_path: Path, api_key: Optional[str] = None) -> Optional[QAValidator]:
    """
    Load QA validator from scenario directory

    Args:
        scenario_path: Path to scenario directory
        api_key: Optional API key for LLM calls

    Returns:
        QAValidator if validation-rules.yaml exists, None otherwise
    """
    rules_file = scenario_path / "validation-rules.yaml"

    if not rules_file.exists():
        logger.debug(f"No validation-rules.yaml found in {scenario_path}")
        return None

    try:
        validator = QAValidator(rules_file, api_key)
        return validator

    except Exception as e:
        logger.warning(f"Failed to load QA validator: {e}")
        return None


async def save_validation_report(
    validation_results: List[ValidationResult],
    output_path: Path,
    turn: int
):
    """
    Save validation report to markdown file

    Args:
        validation_results: List of validation results
        output_path: Path to output file
        turn: Turn number
    """
    try:
        markdown = _format_validation_report(validation_results, turn)

        with open(output_path, 'w') as f:
            f.write(markdown)

        logger.info(f"Saved validation report to {output_path}")

    except Exception as e:
        logger.error(f"Failed to save validation report to {output_path}: {e}")
        raise


def _format_validation_report(
    validation_results: List[ValidationResult],
    turn: int
) -> str:
    """
    Format validation results as markdown

    Args:
        validation_results: List of validation results
        turn: Turn number

    Returns:
        Markdown formatted report
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Count results
    total = len(validation_results)
    passed = sum(1 for r in validation_results if r.passed)
    failed = total - passed

    # Summary
    markdown = f"""# QA Validation Report - Turn {turn}

*Generated at {timestamp}*

## Summary

- **Total Checks:** {total}
- **Passed:** {passed}
- **Failed:** {failed}
- **Pass Rate:** {(passed/total*100) if total > 0 else 0:.1f}%

## Validation Results

"""

    # Details for each check
    for result in validation_results:
        status_icon = "✅" if result.passed else "❌"
        markdown += f"### {status_icon} {result.check_name}\n\n"

        if result.passed:
            markdown += "**Status:** PASSED\n\n"
        else:
            markdown += "**Status:** FAILED\n\n"

            if result.severity:
                markdown += f"**Severity:** {result.severity}\n\n"

            if result.issues:
                markdown += "**Issues:**\n\n"
                for issue in result.issues:
                    markdown += f"- {issue}\n"
                markdown += "\n"

        if result.explanation:
            markdown += f"**Explanation:**\n\n{result.explanation}\n\n"

        markdown += f"*Tokens used: {result.tokens_used}*\n\n"
        markdown += "---\n\n"

    return markdown
