"""
Validation configuration schema for Scenario Lab V2

Validates validation-rules.yaml files with clear error messages.
"""
from typing import Optional, Dict, Literal
from pydantic import BaseModel, Field


class ValidationCheck(BaseModel):
    """
    Configuration for a single validation check

    Example:
        actor_decision_consistency:
          enabled: true
          severity: medium
          description: "Checks if actor decisions align with their goals"
    """

    enabled: bool = Field(
        default=True,
        description="Whether this check is active",
    )

    severity: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Severity level for issues found by this check",
    )

    description: Optional[str] = Field(
        default=None,
        description="What this check validates",
    )


class ValidationConfig(BaseModel):
    """
    Configuration for QA validation system

    Example validation-rules.yaml:
        validation_model: openai/gpt-4o-mini
        checks:
          actor_decision_consistency:
            enabled: true
            severity: medium
          world_state_coherence:
            enabled: true
            severity: high
          information_access_consistency:
            enabled: true
            severity: medium
        run_after_each_turn: true
        generate_turn_reports: true
        halt_on_critical: false
    """

    validation_model: str = Field(
        default="openai/gpt-4o-mini",
        description="LLM model to use for validation checks",
    )

    checks: Dict[str, ValidationCheck] = Field(
        default_factory=lambda: {
            "actor_decision_consistency": ValidationCheck(
                enabled=True,
                severity="medium",
                description="Validates actor decisions align with goals and constraints",
            ),
            "world_state_coherence": ValidationCheck(
                enabled=True,
                severity="high",
                description="Validates world state updates are logical and consistent",
            ),
            "information_access_consistency": ValidationCheck(
                enabled=True,
                severity="medium",
                description="Validates actors only use information they have access to",
            ),
        },
        description="Validation checks to run",
    )

    run_after_each_turn: bool = Field(
        default=True,
        description="Run validation after every turn",
    )

    generate_turn_reports: bool = Field(
        default=True,
        description="Generate detailed per-turn validation reports",
    )

    generate_summary: bool = Field(
        default=True,
        description="Generate summary report at end of scenario",
    )

    halt_on_critical: bool = Field(
        default=False,
        description="Stop scenario execution if critical issues are found",
    )

    max_issues_before_halt: Optional[int] = Field(
        default=None,
        description="Maximum number of issues before halting (if halt_on_critical=true)",
        gt=0,
    )

    report_format: Literal["markdown", "json", "both"] = Field(
        default="markdown",
        description="Format for validation reports",
    )

    model_config = {
        "extra": "allow",  # Allow extra fields for custom checks
    }
