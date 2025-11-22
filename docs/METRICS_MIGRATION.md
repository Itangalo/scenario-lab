# Metrics Configuration Migration Guide: V1 to V2

This guide helps you migrate metrics.yaml files from the V1 format (dictionary-based) to the V2 format (list-based with Pydantic validation).

## Why Migrate?

The V2 metrics format provides:

- **Strict validation** using Pydantic schemas
- **Better type safety** with explicit `continuous`, `categorical`, and `boolean` types
- **Clearer structure** with nested `extraction` configuration
- **Per-metric thresholds** instead of a separate thresholds section
- **Actor-specific metrics** support

## Quick Reference: Format Differences

| Aspect | V1 Format | V2 Format |
|--------|-----------|-----------|
| **Root extraction model** | `extraction_model:` (top-level) | `extraction.model:` (per-metric) |
| **Extraction type** | `extraction_type:` | `extraction.type:` |
| **LLM prompt** | `extraction_prompt:` | `extraction.prompt:` |
| **Pattern/keywords** | Top-level on metric | Inside `extraction:` block |
| **Data typing** | `data_type: "float"\|"integer"` | `type: "continuous"\|"categorical"\|"boolean"` |
| **Value range** | Not required | `range: [min, max]` (required for continuous) |
| **Categories** | Not required | `categories: [...]` (required for categorical) |
| **Thresholds** | Separate `thresholds:` section | `warning_threshold:` / `critical_threshold:` on metric |
| **Aggregation** | `aggregation: "max"\|"sum"\|"last"` | Removed (calculated per-turn) |

## Migration Examples

### Example 1: Pattern-Based Metric

**V1 Format:**
```yaml
extraction_model: "openai/gpt-4o-mini"

metrics:
  budget_spent:
    description: "Total budget spent in millions"
    extraction_type: "pattern"
    pattern: '\$(\d+(?:\.\d+)?)\s*(?:M|million)'
    data_type: "float"
    aggregation: "max"

thresholds:
  budget_spent:
    warning: 8.0
    critical: 10.0
```

**V2 Format:**
```yaml
metrics:
  - name: budget_spent
    description: "Total budget spent in millions"
    type: continuous
    range: [0, 10]
    unit: "M$"
    extraction:
      type: pattern
      pattern: '\$(\d+(?:\.\d+)?)\s*(?:M|million)'
    warning_threshold: 8.0
    critical_threshold: 10.0
    actor_specific: false

export_format: json
```

### Example 2: Keyword-Based Metric

**V1 Format:**
```yaml
metrics:
  privacy_concerns:
    description: "Privacy concern mentions"
    extraction_type: "keyword"
    keywords:
      - "privacy"
      - "surveillance"
      - "data protection"
    data_type: "integer"
    aggregation: "sum"
```

**V2 Format:**
```yaml
metrics:
  - name: privacy_concerns
    description: "Privacy concern mentions"
    type: continuous
    range: [0, 100]
    unit: "mentions"
    extraction:
      type: keyword
      keywords:
        - "privacy"
        - "surveillance"
        - "data protection"
      scoring: count
    actor_specific: false
```

### Example 3: LLM-Based Metric

**V1 Format:**
```yaml
extraction_model: "openai/gpt-4o-mini"

metrics:
  support_level:
    description: "Public support level (0-10)"
    extraction_type: "llm"
    extraction_prompt: |
      Rate the public support level on a scale of 0-10.
      Respond with only a number.
    data_type: "integer"
    aggregation: "last"
```

**V2 Format:**
```yaml
metrics:
  - name: support_level
    description: "Public support level (0-10)"
    type: continuous
    range: [0, 10]
    unit: "support"
    extraction:
      type: llm
      prompt: |
        Rate the public support level on a scale of 0-10.
        Respond with only a number.
      model: "openai/gpt-4o-mini"  # Optional: per-metric model
    actor_specific: false

export_format: json
```

### Example 4: Categorical Metric

**V1 Format:**
```yaml
metrics:
  scenario_outcome:
    description: "Scenario trajectory"
    extraction_type: "keyword"
    keywords:
      - "cooperation"
      - "conflict"
      - "stalemate"
    data_type: "string"
    aggregation: "last"
```

**V2 Format:**
```yaml
metrics:
  - name: scenario_outcome
    description: "Scenario trajectory"
    type: categorical
    categories:
      - "cooperation"
      - "conflict"
      - "stalemate"
    extraction:
      type: keyword
      keywords:
        - "cooperation"
        - "conflict"
        - "stalemate"
      scoring: presence
    actor_specific: false
```

## Step-by-Step Migration Checklist

Use this checklist to convert your V1 metrics.yaml to V2:

### 1. Structure Changes

- [ ] **Convert metrics from dict to list**: Change `metrics: {name: {...}}` to `metrics: [{name: "...", ...}]`
- [ ] **Add `name` field**: Move the metric key to a `name` field inside each metric object

### 2. Field Renames

- [ ] **`extraction_type`** → `extraction.type`
- [ ] **`extraction_prompt`** → `extraction.prompt`
- [ ] **`pattern`** → `extraction.pattern`
- [ ] **`keywords`** → `extraction.keywords`

### 3. Type System Changes

- [ ] **Replace `data_type`** with `type` using V2 values:
  - `"float"` → `continuous`
  - `"integer"` → `continuous`
  - `"string"` → `categorical`
  - `"bool"` → `boolean`

### 4. Required Fields for Each Type

- [ ] **Continuous metrics**: Add `range: [min, max]`
- [ ] **Categorical metrics**: Add `categories: ["option1", "option2", ...]`
- [ ] **Boolean metrics**: No additional fields required

### 5. Thresholds Migration

- [ ] **Remove `thresholds:` section**
- [ ] **Move thresholds to metrics**: Add `warning_threshold:` and `critical_threshold:` to each metric

### 6. Cleanup

- [ ] **Remove `extraction_model:`** from top level (move to `extraction.model:` per-metric if needed)
- [ ] **Remove `aggregation:`** field (no longer used)
- [ ] **Add `unit:`** label (optional but recommended)
- [ ] **Add `actor_specific: false`** (optional, defaults to false)
- [ ] **Add `export_format: json`** at root level (optional, defaults to json)

## Automated Migration Tool

A migration tool is available to automatically convert V1 metrics files to V2 format:

```bash
# Convert a single metrics file
python -m scenario_lab.tools.migrate_metrics scenarios/my-scenario/metrics.yaml

# Preview changes without writing
python -m scenario_lab.tools.migrate_metrics scenarios/my-scenario/metrics.yaml --dry-run

# Output to different file
python -m scenario_lab.tools.migrate_metrics scenarios/my-scenario/metrics.yaml --output metrics-v2.yaml
```

The tool will:

1. Detect if the file is V1 format
2. Convert all fields to V2 schema
3. Preserve comments where possible
4. Validate the output against V2 schema
5. Create a backup of the original file

## Common Validation Errors After Migration

If validation fails after migration, check for these common issues:

### Missing `type` field

```
ValueError: field required (type=value_error.missing)
```

**Fix:** Add `type: continuous`, `type: categorical`, or `type: boolean`

### Missing `range` for continuous metrics

```
ValueError: 'range' field required for continuous metrics
```

**Fix:** Add `range: [min_value, max_value]` (e.g., `range: [0, 10]`)

### Missing `categories` for categorical metrics

```
ValueError: 'categories' field required for categorical metrics
```

**Fix:** Add `categories: ["option1", "option2", ...]`

### Invalid metric name

```
ValueError: string does not match regex "^[a-z0-9_]+$"
```

**Fix:** Use lowercase with underscores only (e.g., `public_support` not `Public-Support`)

### Missing extraction prompt

```
ValueError: 'prompt' field required when type is 'llm'
```

**Fix:** Add `prompt:` inside the `extraction:` block

### Duplicate metric names

```
ValueError: Duplicate metric names found: {'metric_name'}
```

**Fix:** Ensure each metric has a unique `name`

## V2 Schema Reference

### MetricsConfig (Root)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `metrics` | list | Yes | - | List of metric configurations |
| `export_format` | string | No | "json" | "json", "csv", or "both" |
| `auto_export` | boolean | No | true | Auto-export after each turn |
| `export_path` | string | No | null | Custom export location |

### MetricConfig (Individual Metric)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Identifier (lowercase_with_underscores) |
| `description` | string | Yes | - | What the metric measures |
| `type` | string | Yes | - | "continuous", "categorical", or "boolean" |
| `extraction` | object | Yes | - | How to extract the metric |
| `range` | [float, float] | Yes* | - | *Required for continuous type |
| `categories` | list | Yes* | - | *Required for categorical type |
| `unit` | string | No | null | Unit label (e.g., "percent") |
| `actor_specific` | boolean | No | false | Per-actor tracking |
| `warning_threshold` | float | No | null | Warning trigger value |
| `critical_threshold` | float | No | null | Critical alert trigger |

### MetricExtraction

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | string | Yes | - | "llm", "keyword", "pattern", or "manual" |
| `prompt` | string | Yes* | - | *Required when type="llm" |
| `model` | string | No | null | LLM model for extraction |
| `keywords` | list | Yes* | - | *Required when type="keyword" |
| `scoring` | string | No | "count" | "count", "presence", or "density" |
| `pattern` | string | Yes* | - | *Required when type="pattern" |

## Getting Help

If you encounter issues during migration:

1. **Check the examples** in `scenarios/example-full-featured/metrics.yaml`
2. **Run validation** with `scenario-lab validate scenarios/your-scenario`
3. **Review the schema** in `scenario_lab/schemas/metrics.py`
4. **Report issues** at https://github.com/Itangalo/scenario-lab/issues
