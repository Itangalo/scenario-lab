"""
QA Validator V2 for Scenario Lab

Pure V2 implementation using Pydantic ValidationConfig.
Simplified version focusing on V2 patterns.
"""
import logging
from typing import Optional

from scenario_lab.schemas.validation import ValidationConfig
from scenario_lab.core.qa_validator import QAValidator, ValidationResult

logger = logging.getLogger(__name__)


class QAValidatorV2:
    """
    QA Validator V2 using Pydantic schemas

    This is a V2 wrapper that takes ValidationConfig instead of raw YAML paths.
    Currently wraps the existing QAValidator for validation logic.
    """

    def __init__(self, validation_config: ValidationConfig, api_key: Optional[str] = None):
        """
        Initialize QA Validator V2

        Args:
            validation_config: Pydantic ValidationConfig from scenario_lab.schemas.validation
            api_key: API key for LLM calls (optional, will use env var if not provided)
        """
        self.config = validation_config
        self.api_key = api_key
        self.validation_model = validation_config.validation_model

        # For now, convert ValidationConfig back to dict format for QAValidator
        # TODO: Refactor QAValidator to use ValidationConfig directly
        validation_rules = self._config_to_dict(validation_config)

        # Create wrapped QAValidator with converted rules
        self._wrapped_validator = QAValidator(api_key=api_key)
        self._wrapped_validator.validation_rules = validation_rules
        self._wrapped_validator.validation_model = validation_config.validation_model

        logger.info(
            f"Initialized QAValidatorV2: {len(validation_config.checks)} checks, "
            f"model={self.validation_model}"
        )

    def _config_to_dict(self, config: ValidationConfig) -> dict:
        """
        Convert ValidationConfig to dict format for wrapped validator

        Args:
            config: ValidationConfig object

        Returns:
            Dict representation for QAValidator
        """
        # Convert Pydantic checks to dict format
        checks_dict = {}
        for check_name, check_config in config.checks.items():
            checks_dict[check_name] = {
                "enabled": check_config.enabled,
                "severity": check_config.severity,
                "description": check_config.description or "",
                # Note: prompt_template not in Pydantic schema yet, would need to be added
                # For now, validation methods will work without prompt_template
            }

        return {
            "validation_model": config.validation_model,
            "checks": checks_dict,
            "run_after_each_turn": config.run_after_each_turn,
            "generate_turn_reports": config.generate_turn_reports,
            "halt_on_critical": config.halt_on_critical,
        }

    def is_enabled(self) -> bool:
        """Check if validation is enabled"""
        return len(self.config.checks) > 0

    def should_run_after_turn(self) -> bool:
        """Check if validation should run after each turn"""
        return self.config.run_after_each_turn

    # Delegate all validation methods to wrapped validator
    async def validate_actor_decision(self, *args, **kwargs):
        """Delegate to wrapped validator"""
        return await self._wrapped_validator.validate_actor_decision(*args, **kwargs)

    async def validate_world_state_update(self, *args, **kwargs):
        """Delegate to wrapped validator"""
        return await self._wrapped_validator.validate_world_state_update(*args, **kwargs)

    async def validate_information_access(self, *args, **kwargs):
        """Delegate to wrapped validator"""
        return await self._wrapped_validator.validate_information_access(*args, **kwargs)

    def create_cost_record(self, *args, **kwargs):
        """Delegate to wrapped validator"""
        return self._wrapped_validator.create_cost_record(*args, **kwargs)
