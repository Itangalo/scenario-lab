#!/usr/bin/env python3
"""
Metrics Configuration Migration Tool: V1 to V2

Automatically converts V1 metrics.yaml files (dictionary-based) to V2 format
(list-based with Pydantic validation).

Usage:
    python -m scenario_lab.tools.migrate_metrics <metrics_file>
    python -m scenario_lab.tools.migrate_metrics <metrics_file> --dry-run
    python -m scenario_lab.tools.migrate_metrics <metrics_file> --output metrics-v2.yaml
"""

import argparse
import sys
import shutil
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

import yaml

from scenario_lab.schemas.metrics import MetricsConfig


def detect_v1_format(data: dict) -> bool:
    """
    Detect if metrics data is in V1 format.

    V1 indicators:
    - Top-level 'extraction_model' field
    - 'metrics' is a dict (not a list)
    - Metrics have 'extraction_type' instead of nested 'extraction'
    - Separate 'thresholds' section
    - 'data_type' field instead of 'type'
    """
    if not isinstance(data, dict):
        return False

    # V1 has top-level extraction_model
    if "extraction_model" in data:
        return True

    # V1 has separate thresholds section
    if "thresholds" in data:
        return True

    # Check metrics structure
    metrics = data.get("metrics")
    if metrics is None:
        return False

    # V1: metrics is a dict with metric names as keys
    if isinstance(metrics, dict):
        return True

    # V1: metrics is a list but with V1 fields
    if isinstance(metrics, list) and len(metrics) > 0:
        first_metric = metrics[0]
        if isinstance(first_metric, dict):
            # V1 indicators in metric definition
            if "extraction_type" in first_metric:
                return True
            if "extraction_prompt" in first_metric:
                return True
            if "data_type" in first_metric:
                return True
            if "aggregation" in first_metric:
                return True

    return False


def convert_data_type_to_v2_type(data_type: str) -> str:
    """Convert V1 data_type to V2 type"""
    mapping = {
        "float": "continuous",
        "integer": "continuous",
        "int": "continuous",
        "number": "continuous",
        "string": "categorical",
        "str": "categorical",
        "bool": "boolean",
        "boolean": "boolean",
    }
    return mapping.get(data_type.lower(), "continuous")


def infer_range_from_prompt(prompt: str) -> tuple[float, float]:
    """Attempt to infer range from LLM prompt"""
    import re

    # Look for patterns like "0-10", "1-5", "0 to 100"
    patterns = [
        r"(\d+)\s*[-–to]\s*(\d+)\s*scale",
        r"scale\s*(?:of|from)?\s*(\d+)\s*[-–to]\s*(\d+)",
        r"(\d+)\s*[-–to]\s*(\d+)",
        r"between\s*(\d+)\s*and\s*(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            if min_val < max_val:
                return (min_val, max_val)

    # Default range
    return (0, 10)


def migrate_metric(
    name: str,
    v1_metric: dict,
    extraction_model: Optional[str] = None,
    thresholds: Optional[dict] = None,
) -> dict:
    """Convert a single V1 metric to V2 format"""
    v2_metric: dict[str, Any] = {
        "name": name,
        "description": v1_metric.get("description", f"Metric: {name}"),
    }

    # Convert data_type to type
    data_type = v1_metric.get("data_type", "float")
    v2_type = convert_data_type_to_v2_type(data_type)
    v2_metric["type"] = v2_type

    # Build extraction block
    extraction: dict[str, Any] = {}

    extraction_type = v1_metric.get("extraction_type", "manual")
    extraction["type"] = extraction_type

    if extraction_type == "llm":
        prompt = v1_metric.get("extraction_prompt", v1_metric.get("prompt", ""))
        extraction["prompt"] = prompt

        # Add model if specified
        model = v1_metric.get("model") or extraction_model
        if model:
            extraction["model"] = model

        # Infer range from prompt for continuous metrics
        if v2_type == "continuous":
            v2_metric["range"] = infer_range_from_prompt(prompt)

    elif extraction_type == "keyword":
        keywords = v1_metric.get("keywords", [])
        extraction["keywords"] = keywords

        # Add scoring if specified
        scoring = v1_metric.get("scoring", "count")
        extraction["scoring"] = scoring

        # Default range for keyword metrics
        if v2_type == "continuous":
            v2_metric["range"] = (0, 100)

    elif extraction_type == "pattern":
        pattern = v1_metric.get("pattern", "")
        extraction["pattern"] = pattern

        # Default range for pattern metrics
        if v2_type == "continuous":
            v2_metric["range"] = (0, 100)

    else:  # manual or unknown
        extraction["type"] = "manual"
        if v2_type == "continuous":
            v2_metric["range"] = (0, 100)

    v2_metric["extraction"] = extraction

    # Handle categorical type
    if v2_type == "categorical":
        # Try to get categories from keywords or create defaults
        keywords = v1_metric.get("keywords", [])
        if keywords:
            v2_metric["categories"] = keywords
        else:
            v2_metric["categories"] = ["unknown"]
        # Remove range if it was set
        v2_metric.pop("range", None)

    # Handle boolean type
    if v2_type == "boolean":
        v2_metric.pop("range", None)
        v2_metric.pop("categories", None)

    # Add unit if available
    unit = v1_metric.get("unit")
    if unit:
        v2_metric["unit"] = unit
    elif v2_type == "continuous":
        # Infer unit from metric name or description
        if "percent" in name.lower() or "percent" in v2_metric["description"].lower():
            v2_metric["unit"] = "percent"
        elif "count" in name.lower() or "mention" in name.lower():
            v2_metric["unit"] = "count"

    # Add thresholds if available
    if thresholds and name in thresholds:
        metric_thresholds = thresholds[name]
        if "warning" in metric_thresholds:
            v2_metric["warning_threshold"] = metric_thresholds["warning"]
        if "critical" in metric_thresholds:
            v2_metric["critical_threshold"] = metric_thresholds["critical"]

    # Add actor_specific
    v2_metric["actor_specific"] = v1_metric.get("actor_specific", False)

    return v2_metric


def migrate_v1_to_v2(v1_data: dict) -> dict:
    """Convert V1 metrics configuration to V2 format"""
    v2_data: dict[str, Any] = {"metrics": []}

    # Extract top-level V1 fields
    extraction_model = v1_data.get("extraction_model")
    thresholds = v1_data.get("thresholds", {})

    # Get metrics
    v1_metrics = v1_data.get("metrics", {})

    # Handle dict-based metrics (V1 style)
    if isinstance(v1_metrics, dict):
        for name, metric_def in v1_metrics.items():
            v2_metric = migrate_metric(name, metric_def, extraction_model, thresholds)
            v2_data["metrics"].append(v2_metric)

    # Handle list-based metrics that still have V1 fields
    elif isinstance(v1_metrics, list):
        for metric_def in v1_metrics:
            name = metric_def.get("name", f"metric_{len(v2_data['metrics'])}")
            v2_metric = migrate_metric(name, metric_def, extraction_model, thresholds)
            v2_data["metrics"].append(v2_metric)

    # Add export settings
    v2_data["export_format"] = v1_data.get("export_format", "json")
    v2_data["auto_export"] = v1_data.get("auto_export", True)

    return v2_data


def validate_v2_config(v2_data: dict) -> tuple[bool, Optional[str]]:
    """Validate V2 configuration against Pydantic schema"""
    try:
        MetricsConfig(**v2_data)
        return True, None
    except Exception as e:
        return False, str(e)


def format_yaml_output(data: dict) -> str:
    """Format data as YAML with nice formatting"""

    class CustomDumper(yaml.SafeDumper):
        # Disable aliases to avoid confusing &id001/*id001 references
        def ignore_aliases(self, data):
            return True

    def str_representer(dumper, data):
        if "\n" in data:
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    def list_representer(dumper, data):
        # Use flow style for simple lists (numbers, short strings)
        if all(isinstance(item, (int, float)) for item in data):
            return dumper.represent_sequence(
                "tag:yaml.org,2002:seq", data, flow_style=True
            )
        if all(
            isinstance(item, str) and len(item) < 30 and "\n" not in item
            for item in data
        ):
            if len(data) <= 5:
                return dumper.represent_sequence(
                    "tag:yaml.org,2002:seq", data, flow_style=True
                )
        return dumper.represent_sequence("tag:yaml.org,2002:seq", data)

    CustomDumper.add_representer(str, str_representer)
    CustomDumper.add_representer(list, list_representer)

    return yaml.dump(
        data,
        Dumper=CustomDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=100,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Migrate metrics.yaml from V1 to V2 format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s scenarios/my-scenario/metrics.yaml
  %(prog)s metrics.yaml --dry-run
  %(prog)s metrics.yaml --output metrics-v2.yaml

For more information, see docs/METRICS_MIGRATION.md
        """,
    )
    parser.add_argument("input_file", type=Path, help="Path to V1 metrics.yaml file")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path (default: overwrite input file)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Preview changes without writing",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't create backup of original file",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Convert even if file appears to be V2 format",
    )

    args = parser.parse_args()

    # Check input file exists
    if not args.input_file.exists():
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    # Read input file
    try:
        with open(args.input_file) as f:
            v1_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in {args.input_file}: {e}", file=sys.stderr)
        sys.exit(1)

    if not v1_data:
        print(f"Error: Empty file: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    # Check if already V2 format
    if not detect_v1_format(v1_data) and not args.force:
        print(f"File appears to already be in V2 format: {args.input_file}")
        print("Use --force to convert anyway.")
        sys.exit(0)

    # Perform migration
    print(f"Migrating: {args.input_file}")
    v2_data = migrate_v1_to_v2(v1_data)

    # Validate result
    valid, error = validate_v2_config(v2_data)
    if not valid:
        print(f"Warning: Migrated config has validation issues: {error}", file=sys.stderr)
        print("You may need to manually fix the output.", file=sys.stderr)

    # Format output
    output_yaml = format_yaml_output(v2_data)

    # Dry run: just print
    if args.dry_run:
        print("\n--- Migrated V2 Configuration ---\n")
        print(output_yaml)
        if valid:
            print("\n✓ Configuration validates successfully")
        else:
            print(f"\n⚠ Validation issues: {error}")
        return

    # Determine output path
    output_path = args.output or args.input_file

    # Create backup if overwriting
    if output_path == args.input_file and not args.no_backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = args.input_file.with_suffix(f".v1.{timestamp}.yaml")
        shutil.copy2(args.input_file, backup_path)
        print(f"Backup created: {backup_path}")

    # Write output
    with open(output_path, "w") as f:
        f.write(output_yaml)

    print(f"Migrated configuration written to: {output_path}")

    if valid:
        print("✓ Configuration validates successfully")
    else:
        print(f"⚠ Validation issues (manual fixes may be needed): {error}")


if __name__ == "__main__":
    main()
