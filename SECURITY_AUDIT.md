# Security Audit Report - Scenario Lab V4
**Date:** 2025-12-07
**Audited By:** Claude (Anthropic AI Assistant)
**Scope:** Comprehensive security audit of all Python modules

## Executive Summary

This security audit identified **6 security vulnerabilities** ranging from **High to Low severity**. The most critical issues are:

1. ✅ **Path Traversal in Scenario Loading** (High Severity) - **FIXED 2025-12-07**
2. 🟠 **Jinja2 Template Injection** (High Severity - Conditional)
3. 🟡 **Path Traversal in Actor ID** (Medium Severity)
4. 🟡 **Arbitrary Attribute Setting via CLI** (Medium Severity)
5. 🟢 **YAML Bomb/Billion Laughs** (Low Severity)
6. 🟢 **Missing Input Validation on Override Values** (Low Severity)

---

## 🔴 Critical Vulnerabilities

### 1. Path Traversal in Base Scenario Loading ✅ FIXED

**Status:** ✅ **FIXED on 2025-12-07**
**File:** `scenario_lab/loader.py:212`
**Severity:** High
**CVSS Score:** 7.5 (High)

**Fix Applied:**
- Added security validation to prevent base scenario paths from escaping allowed directory structure
- Base scenarios are now validated using `Path.relative_to()` to ensure they remain within the scenarios directory
- Clear error messages inform users when a malicious path is rejected
- Comprehensive security tests added in `tests/test_security.py` with 3 test cases covering malicious and legitimate scenarios
- All 103 existing tests continue to pass

**Vulnerability:**
```python
base_path = (path.parent / base_path_str).resolve()
```

The `base` field in `scenario.yaml` is user-controlled and not validated. An attacker could craft a malicious scenario file with:

```yaml
base: "../../../etc/passwd"
```

Or:

```yaml
base: "../../../../../../home/user/.ssh/id_rsa"
```

**Attack Vector:**
1. User downloads or creates a malicious scenario
2. Runs: `python -m scenario_lab.cli run malicious-scenario`
3. The loader attempts to read files outside the scenario directory

**Impact:**
- Read arbitrary files on the system
- Information disclosure
- Potential data exfiltration via error messages

**Proof of Concept:**
```yaml
# malicious-scenario/scenario.yaml
name: "Malicious Scenario"
description: "PoC for path traversal"
base: "../../../etc/passwd"  # Tries to load /etc/passwd
# ... rest of config
```

**Recommended Fix:**
```python
def load_config(path: Path, _loading_stack: Optional[List[str]] = None) -> ScenarioConfig:
    # ... existing code ...

    if "base" in data:
        base_path_str = data.pop("base")

        # SECURITY: Validate base path doesn't escape scenario directory
        base_path = (path.parent / base_path_str).resolve()

        # Get the absolute path of the scenario root
        scenario_root = path.parent.resolve()

        # Ensure base_path is within scenario root or its parent directories
        # But NOT allowing arbitrary paths on the system
        try:
            base_path.relative_to(scenario_root.parent)
        except ValueError:
            raise ValueError(
                f"Security: Base scenario path '{base_path_str}' attempts to escape "
                f"allowed directory structure. Base scenarios must be relative paths "
                f"within the scenarios directory."
            )

        if not base_path.exists():
            raise FileNotFoundError(f"Base scenario not found: {base_path}")

        # Continue with existing logic...
```

**Alternative Fix (More Restrictive):**
```python
# Only allow base scenarios from a whitelist of known safe locations
ALLOWED_BASE_DIRS = [
    Path("scenarios"),  # Local scenarios
    Path("/usr/share/scenario-lab/scenarios"),  # System scenarios
]

def validate_base_path(base_path_str: str, current_path: Path) -> Path:
    """Validate base scenario path is in an allowed location."""
    candidate = (current_path.parent / base_path_str).resolve()

    for allowed_dir in ALLOWED_BASE_DIRS:
        try:
            candidate.relative_to(allowed_dir.resolve())
            return candidate
        except ValueError:
            continue

    raise ValueError(
        f"Security: Base scenario '{base_path_str}' is not in an allowed directory. "
        f"Allowed directories: {[str(d) for d in ALLOWED_BASE_DIRS]}"
    )
```

---

## 🟠 High Severity (Conditional)

### 2. Server-Side Template Injection (SSTI) in Custom Templates

**File:** `scenario_lab/prompts.py:92`
**Severity:** High (Conditional - requires malicious scenario author)
**CVSS Score:** 8.8 (High) if exploited

**Vulnerability:**
```python
def _get_user_template(self, prompt_type: str) -> Template:
    if key in self.scenario.custom_user_prompts:
        return Template(self.scenario.custom_user_prompts[key])  # UNSAFE!
```

Jinja2 templates are created from user-provided content without sandboxing. A malicious template could execute arbitrary Python code.

**Attack Vector:**
```markdown
<!-- scenarios/malicious/user-prompts/events.md -->
It is turn {{turn}}.

{{''.__class__.__mro__[1].__subclasses__()[104].__init__.__globals__['sys'].modules['os'].popen('cat /etc/passwd').read()}}
```

Or using the `config` object to access environment variables:
```jinja2
{{config.items()}}
{{lipsum.__globals__.os.popen('whoami').read()}}
```

**Impact:**
- Remote Code Execution (RCE) if attacker can provide custom templates
- File system access
- Environment variable exposure
- Complete system compromise

**Risk Assessment:**
- **Likelihood:** Medium (requires attacker to create malicious scenario)
- **Impact:** Critical (full RCE)
- **Risk Level:** High

**Recommended Fix:**

Use Jinja2's `SandboxedEnvironment`:

```python
from jinja2 import Template, Environment, select_autoescape
from jinja2.sandbox import SandboxedEnvironment

class PromptBuilder:
    def __init__(self, scenario: Scenario):
        self.scenario = scenario

        # Create sandboxed Jinja2 environment
        self.jinja_env = SandboxedEnvironment(
            autoescape=select_autoescape(enabled_extensions=()),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self._load_templates()

    def _get_user_template(self, prompt_type: str) -> Template:
        key = prompt_type.replace("-", "_")

        if key in self.scenario.custom_user_prompts:
            # Use sandboxed environment instead of Template()
            return self.jinja_env.from_string(self.scenario.custom_user_prompts[key])

        # For default templates, can use regular Template (trusted)
        return self.jinja_env.from_string(self.user_templates[key])
```

**Additional Protection:**

Restrict available variables in template context:
```python
def _get_common_context(self, turn: int) -> dict[str, Any]:
    """Get context variables common to all prompts."""
    # ... existing code ...

    # Only expose safe, read-only values
    # Do NOT expose: config objects, functions, builtins
    safe_context = {
        "turn": turn,
        "time_period": time_period,
        "metrics_json": metrics_json,
        "world_state": world_state,
        # Add individual metrics by value only (not objects)
        **{f"metric_{m_id.replace('-', '_')}": float(metric.value)
           for m_id, metric in self.scenario.metrics.metrics.items()},
    }

    return safe_context
```

---

## 🟡 Medium Severity

### 3. Path Traversal in Actor ID

**File:** `scenario_lab/output.py:78`
**Severity:** Medium
**CVSS Score:** 5.3 (Medium)

**Vulnerability:**
```python
def save_actor_output(self, turn: int, actor_id: str, output: str):
    turn_dir = self.get_turn_dir(turn)
    actors_dir = turn_dir / "2-actors"
    actors_dir.mkdir(exist_ok=True)
    (actors_dir / f"{actor_id}.md").write_text(output, encoding="utf-8")  # UNSAFE
```

If `actor_id` contains path traversal characters like `../`, files could be written outside the intended directory.

**Attack Vector:**
```yaml
# scenario.yaml
actors:
  - "../../malicious"  # Writes to parent directories
  - "../../../etc/passwd"  # Attempts to overwrite system files (likely fails due to permissions)
```

**Impact:**
- Write files to arbitrary locations (within user permissions)
- Overwrite important files
- Data corruption

**Likelihood:** Low (requires malicious scenario author + appropriate file permissions)

**Recommended Fix:**
```python
import os

def save_actor_output(self, turn: int, actor_id: str, output: str):
    # Validate actor_id doesn't contain path traversal
    if ".." in actor_id or os.sep in actor_id or actor_id.startswith("/"):
        raise ValueError(
            f"Security: Invalid actor_id '{actor_id}'. "
            f"Actor IDs cannot contain path separators or '..'."
        )

    # Additional validation: only allow alphanumeric, dash, underscore
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', actor_id):
        raise ValueError(
            f"Security: Invalid actor_id '{actor_id}'. "
            f"Actor IDs must only contain alphanumeric characters, dashes, and underscores."
        )

    turn_dir = self.get_turn_dir(turn)
    actors_dir = turn_dir / "2-actors"
    actors_dir.mkdir(exist_ok=True)

    output_path = actors_dir / f"{actor_id}.md"

    # Final safety check: ensure resolved path is within actors_dir
    if not output_path.resolve().is_relative_to(actors_dir.resolve()):
        raise ValueError(
            f"Security: Resolved actor output path escapes actors directory."
        )

    output_path.write_text(output, encoding="utf-8")
```

**Note:** Same issue exists in `loader.py:156` where actor files are loaded:
```python
# scenario_lab/loader.py:156
actor_prompt_path = prompts_dir / f"actor_{actor_id}.md"
```

---

### 4. Arbitrary Attribute Setting via CLI Overrides

**File:** `scenario_lab/cli.py:302-313`, `cli.py:580-591`
**Severity:** Medium
**CVSS Score:** 4.3 (Medium)

**Vulnerability:**
```python
# Lines 302-313, 580-591
if hasattr(target, last_key):
    setattr(target, last_key, value)  # UNSAFE - no validation
```

The `--override` flag allows setting arbitrary attributes on the scenario config using `setattr()` without validation.

**Attack Vector:**
```bash
# Attempt to override internal Python attributes
python -m scenario_lab.cli run scenario --override "__class__=malicious"
python -m scenario_lab.cli run scenario --override "__dict__=evil"

# Or attempt to modify object internals
python -m scenario_lab.cli run scenario --override "actors.__class__.__init__=hack"
```

**Impact:**
- Potential for modifying internal object state
- Could cause crashes or unexpected behavior
- In worst case, could enable code execution if combined with other vulnerabilities

**Likelihood:** Low (Python's attribute protection + error handling limits impact)

**Recommended Fix:**
```python
# Whitelist of allowed override paths
ALLOWED_OVERRIDE_PATHS = {
    "output_language",
    "llm.temperature",
    "llm.max_tokens",
    "llm.events",
    "llm.actors",
    "llm.rules",
    "llm.metrics",
    "llm.summary",
}

def apply_override(scenario: Scenario, override: str):
    """Safely apply configuration override."""
    if "=" not in override:
        print(f"Warning: Invalid override format '{override}', skipping.")
        return

    key_path, value = override.split("=", 1)

    # SECURITY: Check against whitelist
    if key_path not in ALLOWED_OVERRIDE_PATHS:
        print(f"Error: Override path '{key_path}' is not allowed.")
        print(f"Allowed paths: {', '.join(sorted(ALLOWED_OVERRIDE_PATHS))}")
        return

    # SECURITY: Reject paths starting with underscore (private attributes)
    if any(part.startswith("_") for part in key_path.split(".")):
        print(f"Error: Cannot override private attributes: '{key_path}'")
        return

    # Continue with existing type conversion and attribute setting...
    # ... rest of existing logic ...
```

---

## 🟢 Low Severity

### 5. YAML Bomb / Billion Laughs Attack

**File:** `scenario_lab/loader.py:207`
**Severity:** Low
**CVSS Score:** 3.3 (Low)

**Vulnerability:**
```python
data = yaml.safe_load(path.read_text(encoding="utf-8"))
```

While `yaml.safe_load()` is used (good!), it doesn't protect against YAML bombs that cause excessive memory consumption.

**Attack Vector:**
```yaml
# malicious-scenario/scenario.yaml
a: &a ["lol","lol","lol","lol","lol","lol","lol","lol","lol"]
b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]
c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]
d: &d [*c,*c,*c,*c,*c,*c,*c,*c,*c]
e: &e [*d,*d,*d,*d,*d,*d,*d,*d,*d]
f: &f [*e,*e,*e,*e,*e,*e,*e,*e,*e]
g: &g [*f,*f,*f,*f,*f,*f,*f,*f,*f]
h: &h [*g,*g,*g,*g,*g,*g,*g,*g,*g]
i: &i [*h,*h,*h,*h,*h,*h,*h,*h,*h]
```

**Impact:**
- Denial of Service (DoS)
- Memory exhaustion
- System crash

**Likelihood:** Very Low (requires malicious scenario, only affects local user)

**Recommended Fix:**
```python
import yaml
import io

def safe_yaml_load(file_path: Path, max_size_mb: int = 10) -> dict:
    """Safely load YAML with size limits."""
    file_size = file_path.stat().st_size
    max_bytes = max_size_mb * 1024 * 1024

    if file_size > max_bytes:
        raise ValueError(
            f"YAML file too large: {file_size / 1024 / 1024:.2f} MB "
            f"(maximum: {max_size_mb} MB)"
        )

    content = file_path.read_text(encoding="utf-8")

    # Additional protection: limit the loaded object size
    try:
        # Use a custom loader with recursion limits
        class LimitedLoader(yaml.SafeLoader):
            pass

        def construct_sequence(self, node):
            if len(node.value) > 1000:  # Limit sequence size
                raise yaml.constructor.ConstructorError(
                    None, None,
                    "sequence too large (max 1000 items)",
                    node.start_mark
                )
            return super().construct_sequence(node)

        LimitedLoader.construct_sequence = construct_sequence

        return yaml.load(content, Loader=LimitedLoader)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}")
```

---

### 6. Missing Input Validation on Override Values

**File:** `scenario_lab/cli.py:274-286`
**Severity:** Low
**CVSS Score:** 2.4 (Low)

**Vulnerability:**
Type conversion of override values is done with simple try-except, allowing potentially dangerous values:

```python
# Try to convert value to int/float/bool
if value.lower() == "true":
    value = True
elif value.lower() == "false":
    value = False
else:
    try:
        if "." in value:
            value = float(value)  # No validation of range
        else:
            value = int(value)  # No validation of range
    except ValueError:
        pass  # Keep as string
```

**Attack Vector:**
```bash
# Set temperature to invalid value
python -m scenario_lab.cli run scenario --override "llm.temperature=999999"

# Set max_tokens to negative or huge value
python -m scenario_lab.cli run scenario --override "llm.max_tokens=-1"
python -m scenario_lab.cli run scenario --override "llm.max_tokens=999999999"
```

**Impact:**
- Invalid configuration values
- Potential API errors
- Unexpected behavior
- Excessive API costs (if max_tokens is set very high)

**Recommended Fix:**
```python
def convert_override_value(key_path: str, value_str: str) -> any:
    """Convert override value with validation."""
    # Boolean conversion
    if value_str.lower() in ("true", "false"):
        return value_str.lower() == "true"

    # Numeric conversion with validation
    try:
        if "." in value_str:
            value = float(value_str)
        else:
            value = int(value_str)

        # Validate based on key
        if "temperature" in key_path.lower():
            if not 0 <= value <= 2:
                raise ValueError(f"Temperature must be between 0 and 2, got {value}")
        elif "max_tokens" in key_path.lower():
            if not 1 <= value <= 100000:
                raise ValueError(f"max_tokens must be between 1 and 100000, got {value}")

        return value
    except ValueError:
        # Keep as string
        return value_str
```

---

## ✅ Security Best Practices Found

The audit also identified several **good security practices**:

### 1. ✅ Safe YAML Loading
```python
data = yaml.safe_load(path.read_text(encoding="utf-8"))  # Using safe_load, not load!
```

**Good:** Uses `yaml.safe_load()` instead of `yaml.load()`, preventing arbitrary Python object deserialization.

### 2. ✅ API Key from Environment
```python
self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
```

**Good:** API key is never hardcoded, retrieved from environment variables.

### 3. ✅ No API Key in Logs
API key is never logged or printed in error messages (verified with grep).

### 4. ✅ HTTPS for API Calls
```python
API_URL = "https://openrouter.ai/api/v1/chat/completions"
```

**Good:** Uses HTTPS, not HTTP.

### 5. ✅ Safe Expression Evaluator (Fixed)
The unsafe `eval()` was recently replaced with an AST-based safe evaluator ✅

### 6. ✅ JSON Parsing
All JSON parsing uses `json.loads()` which is safe.

### 7. ✅ Path Object Usage
Using `pathlib.Path` throughout, which provides some protection against common path issues.

---

## Priority Recommendations

### Immediate (Critical)

1. **Fix path traversal in base scenario loading** - Add validation to `loader.py:212`
2. **Sandbox Jinja2 templates** - Use `SandboxedEnvironment` in `prompts.py`

### Short-term (High Priority)

3. **Validate actor IDs** - Add path traversal protection to `output.py:78`
4. **Whitelist CLI overrides** - Restrict what can be overridden via `--override`

### Long-term (Improvements)

5. **Add YAML size limits** - Protect against YAML bombs
6. **Validate override value ranges** - Ensure temperature, max_tokens are reasonable

---

## Testing Recommendations

Create security test cases:

```python
# tests/test_security.py

def test_path_traversal_in_base_scenario():
    """Test that base scenario can't escape directory."""
    malicious_yaml = """
    name: "Malicious"
    base: "../../../etc/passwd"
    """
    with pytest.raises(ValueError, match="Security.*escape"):
        load_config(malicious_yaml)

def test_template_injection_blocked():
    """Test that template injection is prevented."""
    malicious_template = "{{''.__class__}}"
    # Should raise or sanitize the template

def test_actor_id_path_traversal():
    """Test that actor_id can't contain path traversal."""
    with pytest.raises(ValueError, match="Security.*path"):
        output_manager.save_actor_output(1, "../../../evil", "content")
```

---

## Conclusion

While the codebase demonstrates some good security practices (safe YAML loading, API key handling), there are **several critical vulnerabilities** that should be addressed immediately, particularly:

1. Path traversal in scenario inheritance
2. Potential template injection in custom prompts

The conditional nature of most vulnerabilities (requiring malicious scenario authors) reduces the immediate risk, but **defense in depth** is important. All recommendations should be implemented to harden the application against both malicious scenarios and accidental misuse.

**Overall Security Grade: C+ (Needs Improvement)**

With the recommended fixes implemented: **Security Grade: A-**
