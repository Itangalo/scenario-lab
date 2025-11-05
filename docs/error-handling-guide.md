# Error Handling Guide

This guide explains the enhanced error handling system in Scenario Lab, which provides user-friendly error messages, automatic recovery suggestions, and progressive fallback strategies.

## Overview

The error handling system consists of three main components:

1. **Error Handler** (`src/error_handler.py`) - Classifies errors and provides detailed, actionable error messages
2. **Progressive Fallback** (`src/progressive_fallback.py`) - Automatically tries alternative models when errors occur
3. **Integration** - Error handling is integrated into `batch_runner.py` and `run_scenario.py`

## Key Features

### 1. Detailed Error Messages

When errors occur, you'll see:

- **Clear description** of what went wrong
- **Contextual information** (scenario, turn, actor, model, cost so far)
- **Explanation** of why the error matters
- **Suggested actions** with exact commands to fix the issue

**Example:**

```
❌ ERROR: API

What happened: 401 unauthorized - invalid API key
While: Making API call to openai/gpt-4o-mini
Scenario: ai-regulation-2027
Turn: 3
Model: openai/gpt-4o-mini
Cost so far: $1.2500

Why this matters:
Authentication failed. Your API key may be invalid, expired, or not set.
The API requires valid credentials to process requests.

======================================================================
💡 SUGGESTED ACTIONS:
======================================================================

1. Set or update your API key
   Command: export OPENROUTER_API_KEY=your_api_key_here

2. Verify your API key is valid at https://openrouter.ai/keys

======================================================================
```

### 2. Error Classification

Errors are automatically classified into categories with appropriate severity levels:

**Categories:**
- `API` - API-related errors (rate limits, auth, timeouts)
- `FILE` - File system errors (missing files, permissions)
- `YAML` - YAML parsing/validation errors
- `BUDGET` - Budget/cost limit exceeded
- `STATE` - State file corruption/incompatibility
- `MODEL` - Model-related errors (not found, unsupported)
- `VALIDATION` - Data validation errors
- `NETWORK` - Network connectivity errors
- `CONFIGURATION` - Configuration errors
- `UNKNOWN` - Uncategorized errors

**Severity Levels:**
- `LOW` - Minor issue, execution can continue
- `MEDIUM` - Issue but recoverable with retry
- `HIGH` - Critical, requires user intervention
- `FATAL` - Unrecoverable, must halt immediately

### 3. Progressive Fallback

When a model fails, the system can automatically try cheaper alternatives:

**Fallback chains:**
- `gpt-4` → `gpt-4o` → `gpt-4o-mini`
- `claude-3-opus` → `claude-3-sonnet` → `claude-3-haiku`
- `llama-3.1-405b` → `llama-3.1-70b` → `llama-3.1-8b`

**When fallback is enabled:**
- Model not found (404)
- Model access denied (403)
- Model timeout (faster model might work)
- Service unavailable (503)

**When fallback is disabled:**
- Authentication errors (need to fix API key)
- Budget errors (need to increase budget)
- Rate limits (need to wait)

## Common Error Scenarios

### API Rate Limits (429)

**What you see:**
```
❌ ERROR: API
What happened: 429 rate limit exceeded
```

**Suggested actions:**
1. Wait and retry (automatic retry already attempted)
2. Reduce `--max-parallel` to fewer concurrent runs
3. Use a different API key with higher rate limits

**How to fix:**
```bash
# Edit batch config to reduce parallelism
vim experiments/your-batch-config.yaml
# Change: max_parallel: 1

# Or use different API key
export OPENROUTER_API_KEY=your_key_with_higher_limits
```

### Authentication Errors (401)

**What you see:**
```
❌ ERROR: API
What happened: 401 unauthorized
```

**Suggested actions:**
1. Set or update your API key
2. Verify your API key is valid

**How to fix:**
```bash
# Set API key
export OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Verify it's set
echo $OPENROUTER_API_KEY

# Check validity at https://openrouter.ai/keys
```

### Missing Files

**What you see:**
```
❌ ERROR: FILE
What happened: File not found: /path/to/scenario.yaml
While: Loading scenario definition
File: /path/to/scenario.yaml
```

**Suggested actions:**
1. Create the missing file
2. Verify the path in your configuration is correct
3. Check you're running from the correct directory

**How to fix:**
```bash
# Check current directory
pwd  # Should be in scenario-lab root

# Check if file exists
ls -la /path/to/scenario.yaml

# Create if missing (or fix path in config)
```

### YAML Syntax Errors

**What you see:**
```
❌ ERROR: YAML
What happened: mapping values are not allowed here
While: Parsing scenario YAML
File: /path/to/config.yaml
```

**Suggested actions:**
1. Check YAML syntax with a validator
2. Common issues: indentation (use spaces, not tabs), unquoted special characters, missing colons

**How to fix:**
```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('your_file.yaml'))"

# Common fixes:
# - Use 2 or 4 spaces for indentation (not tabs)
# - Quote strings with special characters: "value: with: colons"
# - Ensure consistent indentation levels
```

### Budget Exceeded

**What you see:**
```
❌ ERROR: BUDGET
What happened: Budget limit exceeded
While: Running batch
Cost so far: $12.5000
```

**Suggested actions:**
1. Resume with increased budget limit
2. Review the batch config and increase credit_limit
3. Use cheaper models to reduce costs
4. Reduce the number of runs or turns

**How to fix:**
```bash
# Resume with more budget (if scenario was halted)
python src/run_scenario.py --resume scenario/runs/run-005

# Or edit batch config
vim experiments/your-batch-config.yaml
# Change: credit_limit: 25.0  # Was 10.0

# Or use cheaper models
# Change: model: openai/gpt-4o-mini  # Was gpt-4
```

### Model Not Found (404)

**What you see:**
```
❌ ERROR: MODEL
What happened: 404 Model not found: gpt-5
While: LLM call
```

**Suggested actions:**
1. Verify model name format (e.g., 'openai/gpt-4o-mini')
2. Check available models at https://openrouter.ai/models
3. Try a common model (gpt-4o-mini, claude-3-haiku, llama-3.1-70b)

**How to fix:**
```bash
# Fix model name in scenario YAML
vim scenario/definition/scenario.yaml

# Common correct formats:
# - openai/gpt-4o-mini
# - anthropic/claude-3-haiku
# - meta-llama/llama-3.1-70b-instruct
```

## Using Error Handling in Code

### Basic Usage

The error handler is automatically integrated into batch_runner.py and run_scenario.py. You don't need to do anything special - just run your scenarios and batch experiments as normal.

### Manual Usage

If you're writing custom code, you can use the error handler directly:

```python
from error_handler import ErrorHandler, classify_error

# Create error handler
error_handler = ErrorHandler(verbose=False)

try:
    # Your code here
    risky_operation()

except Exception as e:
    # Classify the error
    error_context = classify_error(
        e,
        operation="Running my custom operation",
        scenario_name="test-scenario",
        turn_number=5,
        cost_so_far=1.50
    )

    # Handle with user-friendly message
    should_continue, recovery_actions = error_handler.handle_error(error_context)

    if not should_continue:
        # Critical error - halt execution
        raise
    else:
        # Can continue despite error
        pass
```

### Progressive Fallback

To use progressive fallback with model retries:

```python
from progressive_fallback import execute_with_auto_fallback

def make_llm_call_with_model(model):
    def call():
        # Your LLM call here
        return llm_api.call(model, prompt)
    return call

# Try primary model with automatic fallback
result = execute_with_auto_fallback(
    func=lambda: make_llm_call("openai/gpt-4"),
    operation_name="Actor decision",
    primary_model="openai/gpt-4",
    fallback_func_generator=lambda model: make_llm_call_with_model(model),
    context={'actor': 'RegulatorA', 'turn': 3},
    enable_fallback=True
)
```

## Configuration

### Disabling Error Handler

The error handler is always active, but you can control its verbosity:

```python
error_handler = ErrorHandler(verbose=False)  # Less detailed output
```

### Customizing Fallback Behavior

```python
from progressive_fallback import FallbackConfig, ProgressiveFallbackExecutor

# Custom fallback configuration
config = FallbackConfig(
    fallback_models=['model1', 'model2', 'model3'],
    enable_fallback=True,
    max_fallback_attempts=2,  # Only try first 2 fallbacks
    save_state_on_error=True
)

executor = ProgressiveFallbackExecutor(
    fallback_config=config,
    context={'scenario': 'test', 'turn': 5}
)
```

## Testing

The error handling system includes comprehensive tests:

```bash
# Run error handler tests (28 tests)
python -m pytest tests/test_error_handler.py -v

# Run progressive fallback tests (28 tests)
python -m pytest tests/test_progressive_fallback.py -v

# Run all error handling tests
python -m pytest tests/test_error_handler.py tests/test_progressive_fallback.py -v
```

## Error Categories Reference

### API Errors

| Code | Category | Severity | Fallback? | Suggested Action |
|------|----------|----------|-----------|------------------|
| 401  | API | HIGH | No | Set/update API key |
| 403  | API | HIGH | Yes | Check model access permissions |
| 404  | API | HIGH | Yes | Verify model name |
| 429  | API | MEDIUM | No | Reduce parallelism, wait |
| 503  | API | MEDIUM | Yes | Wait and retry |
| Timeout | API | MEDIUM | Yes | Try faster model |

### File Errors

| Error | Category | Severity | Suggested Action |
|-------|----------|----------|------------------|
| FileNotFoundError | FILE | HIGH | Create file or fix path |
| PermissionError | FILE | HIGH | Fix file permissions |

### Configuration Errors

| Error | Category | Severity | Suggested Action |
|-------|----------|----------|------------------|
| YAML syntax | YAML | HIGH | Fix YAML syntax |
| Validation | VALIDATION | HIGH | Fix configuration values |
| Missing field | CONFIGURATION | HIGH | Add required field |

### Resource Errors

| Error | Category | Severity | Suggested Action |
|-------|----------|----------|------------------|
| Budget exceeded | BUDGET | HIGH | Increase budget or resume |
| State corrupted | STATE | HIGH | Start fresh run |

## Best Practices

1. **Always check error messages carefully** - They contain specific information about what went wrong and how to fix it

2. **Use dry-run mode** before expensive batch runs to catch configuration errors:
   ```bash
   python src/batch_runner.py config.yaml --dry-run
   ```

3. **Set budget limits** to prevent runaway costs:
   ```yaml
   budget_limit: 10.0  # Total budget
   cost_per_run_limit: 0.5  # Per-run limit
   ```

4. **Enable fallback for production** but test your primary model first

5. **Monitor error history** - Repeated errors indicate a systematic problem

6. **Save state frequently** - The system automatically saves state after each turn

## Troubleshooting

### "I keep getting 429 errors"

This means you're hitting rate limits. Solutions:
1. Reduce `max_parallel` in batch config
2. Use a different API key with higher limits
3. Wait between runs
4. Contact your API provider to increase limits

### "Fallback isn't working"

Fallback is disabled for:
- Authentication errors (401) - fix your API key first
- Rate limits (429) - need to wait, not try different model
- Budget errors - need to increase budget

For other errors, fallback should work automatically.

### "Error messages are too verbose"

Set `verbose=False` when creating ErrorHandler:
```python
error_handler = ErrorHandler(verbose=False)
```

### "I want to customize recovery actions"

You can modify the recovery action methods in `src/error_handler.py`:
- `_get_api_recovery_actions()`
- `_get_file_recovery_actions()`
- `_get_yaml_recovery_actions()`
- etc.

## Implementation Details

### Error Handler Architecture

```
┌─────────────────┐
│  Error Occurs   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ classify_error()│  ← Determines category & severity
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ErrorContext   │  ← Rich context object
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ErrorHandler    │  ← Formats message & suggests actions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Display to User │  ← User-friendly output
└─────────────────┘
```

### Progressive Fallback Flow

```
┌──────────────┐
│ Primary Call │
└──────┬───────┘
       │
       ▼
   [Success?] ──Yes──> Return result
       │
      No
       │
       ▼
   [Should Fallback?] ──No──> Raise error
       │
      Yes
       │
       ▼
┌──────────────┐
│ Try Fallback │
│   Model 1    │
└──────┬───────┘
       │
       ▼
   [Success?] ──Yes──> Return result
       │
      No
       │
       ▼
┌──────────────┐
│ Try Fallback │
│   Model 2    │
└──────┬───────┘
       │
       ▼
   [Success?] ──Yes──> Return result
       │
      No
       │
       ▼
   Raise error
```

## Future Enhancements

Potential improvements to the error handling system:

1. **Error metrics tracking** - Track error frequency and patterns
2. **Automatic retry with backoff** - More sophisticated retry logic
3. **Email/Slack notifications** - Alert on critical errors
4. **Error rate limiting** - Stop execution if error rate exceeds threshold
5. **Cost prediction** - Better estimation to prevent budget overruns
6. **Multi-language support** - Error messages in different languages

## Related Documentation

- [Batch Configuration Wizard Guide](batch-config-wizard-guide.md) - Creating batch configs
- [Integration Tests](../tests/INTEGRATION_TESTS.md) - Testing the system
- [README](../README.md) - Main project documentation
