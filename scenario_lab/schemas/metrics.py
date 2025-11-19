"""
Metrics configuration schema for Scenario Lab V2

Validates metrics.yaml files with clear error messages.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, model_validator, field_validator


class MetricExtraction(BaseModel):
    """
    How to extract a metric from scenario data

    Examples:
        # LLM extraction:
        extraction:
          type: llm
          prompt: "Rate the cooperation level from 0-10"

        # Keyword extraction:
        extraction:
          type: keyword
          keywords: ["cooperate", "collaborate", "together"]
          scoring: count

        # Pattern extraction:
        extraction:
          type: pattern
          pattern: "cooperation level: (\\d+)"
    """

    type: Literal["llm", "keyword", "pattern", "manual"] = Field(
        ...,
        description="Extraction method",
    )

    # LLM extraction
    prompt: Optional[str] = Field(
        default=None,
        description="Prompt for LLM to extract metric (if type='llm')",
    )

    model: Optional[str] = Field(
        default=None,
        description="Model to use for extraction (if type='llm')",
    )

    # Keyword extraction
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords to search for (if type='keyword')",
    )

    scoring: Optional[Literal["count", "presence", "density"]] = Field(
        default="count",
        description="How to score keyword matches",
    )

    # Pattern extraction
    pattern: Optional[str] = Field(
        default=None,
        description="Regex pattern to extract value (if type='pattern')",
    )

    @model_validator(mode='after')
    def validate_extraction_config(self):
        """Validate that required fields are present for each type"""
        if self.type == "llm" and self.prompt is None:
            raise ValueError("'prompt' field required when type is 'llm'")

        if self.type == "keyword" and (self.keywords is None or not self.keywords):
            raise ValueError("'keywords' field required when type is 'keyword'")

        if self.type == "pattern" and self.pattern is None:
            raise ValueError("'pattern' field required when type is 'pattern'")

        return self


class MetricConfig(BaseModel):
    """
    Configuration for a single metric

    Example:
        name: cooperation_level
        description: Degree of cooperation between actors
        type: continuous
        range: [0, 10]
        extraction:
          type: llm
          prompt: "On a scale of 0-10, rate the cooperation level..."
        warning_threshold: 3
        critical_threshold: 1
    """

    name: str = Field(
        ...,
        description="Metric identifier (lowercase with underscores)",
        pattern=r"^[a-z0-9_]+$",
    )

    description: str = Field(
        ...,
        description="What the metric measures",
        min_length=1,
    )

    type: Literal["continuous", "categorical", "boolean"] = Field(
        ...,
        description="Metric data type",
    )

    # Range/options
    range: Optional[tuple[float, float]] = Field(
        default=None,
        description="Min/max values for continuous metrics [min, max]",
    )

    categories: Optional[List[str]] = Field(
        default=None,
        description="Valid categories for categorical metrics",
    )

    # Extraction
    extraction: MetricExtraction = Field(
        ...,
        description="How to extract this metric from scenario data",
    )

    # Thresholds
    warning_threshold: Optional[float] = Field(
        default=None,
        description="Value that triggers a warning",
    )

    critical_threshold: Optional[float] = Field(
        default=None,
        description="Value that triggers a critical alert",
    )

    # Optional metadata
    unit: Optional[str] = Field(
        default=None,
        description="Unit of measurement (e.g., 'percentage', 'count')",
    )

    actor_specific: Optional[bool] = Field(
        default=False,
        description="Whether this metric is tracked per-actor",
    )

    @model_validator(mode='after')
    def validate_type_specific_fields(self):
        """Validate fields specific to metric type"""
        if self.type == "continuous":
            if self.range is None:
                raise ValueError("'range' field required for continuous metrics")

            min_val, max_val = self.range
            if min_val >= max_val:
                raise ValueError(f"Invalid range: min ({min_val}) must be less than max ({max_val})")

        if self.type == "categorical":
            if self.categories is None or not self.categories:
                raise ValueError("'categories' field required for categorical metrics")

        if self.type == "boolean":
            # No additional fields required
            pass

        return self


class MetricsConfig(BaseModel):
    """
    Configuration for all scenario metrics

    Example metrics.yaml:
        metrics:
          - name: cooperation_level
            description: Level of cooperation between actors
            type: continuous
            range: [0, 10]
            extraction:
              type: llm
              prompt: "Rate cooperation from 0-10"

          - name: negotiation_success
            description: Whether negotiation succeeded
            type: boolean
            extraction:
              type: keyword
              keywords: ["agreement", "deal", "success"]

        export_format: json
    """

    metrics: List[MetricConfig] = Field(
        ...,
        description="List of metrics to track",
        min_length=1,
    )

    export_format: Optional[Literal["json", "csv", "both"]] = Field(
        default="json",
        description="Format for exporting metrics data",
    )

    auto_export: Optional[bool] = Field(
        default=True,
        description="Automatically export metrics after each turn",
    )

    export_path: Optional[str] = Field(
        default=None,
        description="Path for metric exports (default: run directory)",
    )

    @field_validator('metrics')
    @classmethod
    def validate_unique_names(cls, v: List[MetricConfig]) -> List[MetricConfig]:
        """Ensure metric names are unique"""
        names = [m.name for m in v]
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            raise ValueError(f"Duplicate metric names found: {set(duplicates)}")

        return v
