# Scenario Lab Architecture

This document serves as the "ground truth" for the Scenario Lab architecture. It describes how the system is intended to work and should be updated before adding new functionality.

## 1. Design Philosophy: Pure LLM Architecture

V4 represents a radical simplification from previous versions. Instead of complex Python game logic, **we lean into the LLM**.

- **LLMs handle ALL complexity:** Narrative generation, metric updates, rule interpretation, and event evaluation are all performed by the LLM.
- **Python is minimal orchestration:** The Python code is strictly for loading data, constructing prompts, calling APIs, and persisting results to files. It does *not* contain game rules or simulation logic.
- **No communication phases:** There are no complex multi-step communication protocols between actors.
- **No hybrid architecture:** We do not mix Python-based rules with LLM-based reasoning. The simulation is purely LLM-driven.
- **One simple turn loop:** The simulation proceeds in a linear sequence of steps for each turn.

## 2. Core Concepts

### Metrics
- **Definition:** Pure quantitative values representing the state of the world (e.g., `ai_capability`, `unemployment`, `public_sentiment`).
- **Structure:** Each metric has a unique ID, a value, min/max bounds, a unit, and optional reference points for interpretation.
- **Handling:** Metrics are passed to the LLM as JSON and updated by the LLM as JSON. The Python code only validates that values are within bounds (clamping if necessary).

### Metric Rules
- **Definition:** Quantitative rules describing how metrics change over time or in relation to each other.
- **Examples:** "ai_capability doubles every 6 months", "high unemployment decreases public_sentiment".
- **Evolution:** The LLM reviews and updates these rules *every turn* based on world events. This allows the "physics" of the simulation to evolve.
- **Versioning:** Each rules update increments a version number (v1, v2, v3...) to track rule evolution over time.
- **Changelog:** All rule modifications require a structured changelog documenting:
  * **What changed** (Added/Modified/Removed rules)
  * **Motivation** (why the change is needed based on simulation state)
  * **Expected impact** (how this will affect future metrics)
- **Transparency:** Versioning and changelogs make rule evolution visible and debuggable across turns.

### World State
- **Definition:** A narrative description of what happened during the turn, plus a persistent summary of history.
- **Components:**
  * `narrative`: Detailed description of the *current* turn.
  * `historical_summary`: Concise summary of all *previous* turns.
- **Purpose:** It serves as the shared context for all actors in the next turn. There is no information asymmetry; all actors see the same world state.

### Actors
- **Definition:** Simulation participants (governments, organizations, companies) with defined goals and behaviors.
- **Actions:** Actors decide on goals and actions each turn. These are descriptive text, not structured data.

### Events
- **Definition:** Exogenous happenings with probabilities and conditions.
- **Evaluation:** The LLM evaluates whether conditions are met and calculates probabilities. The Python orchestrator then "rolls the dice" to see if the event actually triggers.

### Constitutional Constraints
- **Definition:** Invariant "must-hold" rules that the LLM must respect throughout the simulation.
- **Purpose:** Prevent unrealistic outcomes by enforcing fundamental constraints on how the world works.
- **Examples:**
  * Economic: "Budget cannot exceed revenue without explicit borrowing"
  * Regulatory: "New legislation requires minimum 1 turn from proposal to effect"
  * Organizational: "Agency capacity grows max 30% per turn organically"
  * Physical: "Compute/hardware has supply constraints"
- **Format:** Optional `constitution.md` file per scenario with 5-15 short, clear constraints.
- **Enforcement:** Lightweight LLM-based "referee" step that validates metrics updates against the constitution.
- **Philosophy:** Maintains pure LLM architecture while preventing common failure modes (instant budgets, magical scaling, etc.).

## 3. System Architecture

### File Structure & Loading (`loader.py`)
- **`scenario.yaml`**: Configuration (time scale, actors, LLM settings, output language).
  * **LLM Settings:** Includes per-task model configuration (`events`, `actors`, `rules`, `metrics`, `summary`, `referee`).
  * **Token Budgets:** Supports global `llm.max_tokens` plus optional per-task overrides via `llm.max_tokens_by_task` (for example, higher cap for `rules` to reduce truncation).
- **Markdown Resources**: `metrics.md`, `events.md`, `metric-rules.md`, `background/*.md`.
- **Optional Resources**:
  * `constitution.md`: Constitutional constraints (invariant rules) for the scenario.
- **Inheritance:** Scenarios can inherit from others via the `base` field in `scenario.yaml`.

### The Turn Loop (`orchestrator.py`)
Each turn executes the following steps in order:

1. **Events Step**:
  * **Input:** World state (history + current), current metrics, list of potential events.
  * **LLM Task:** Determine which events meet their conditions and calculate their probabilities.
  * **Python Action:** Parse JSON response, roll dice for probabilities, determine triggered events. If parsing fails, the orchestrator retries once with a dedicated “format-fix” prompt to coerce valid JSON before giving up for the turn.

2. **Actors Step**:
  * **Input:** World state (history + current), metrics, triggered events.
  * **LLM Task:** For *each* actor, review goals and describe actions for the turn.
  * **Parallelization:** Actor prompts are independent and are executed in parallel with bounded concurrency.

3. **Rules Step**:
  * **Input:** World state, triggered events, all actor actions, current rules (with version number).
  * **LLM Task:** Review and update the list of Metric Rules with:
    - Incremented version number (v1 → v2 → v3...)
    - Complete changelog documenting all Added/Modified/Removed rules
    - Motivation for each change (grounded in simulation state)
    - Expected impact on future metrics
  * **Sanity Check:** Optional validation step to check for:
    - Complete and accurate changelog
    - Internal consistency (no contradictory rules)
    - Grounding in narrative/metrics/events
  * **Parser Tolerance:** The Python parser remains formatting-oriented, but tolerates common LLM presentation noise such as an outer fenced Markdown code block and parenthetical annotations after changelog rule names (for example, "`rule_name` (rule 2)").
  * **Length Handling:** If rules output is truncated (`finish_reason=length`) or missing complete rules content, the orchestrator retries once with a concise-output instruction set to recover a complete `## Rules` section.

4. **Metrics Step**:
  * **Input:** World state, triggered events, actor actions, updated rules.
  * **LLM Task:**
    * Determine success of actor actions.
    * Calculate new metric values.
    * Write a narrative summary of the turn.
    * Update the "Notepad" (persistent and secret game master notes).
  * **Output Parsing:** Requires verbatim headers (`## Metrics`, `## Narrative`, `## Notepad`) for reliable parsing.
  * **Failure Handling:** If the metrics response cannot be parsed, the orchestrator retries once with a "format-fix" prompt to enforce the required headers/JSON. If it still fails, previous metric values are kept for that turn.

5. **Constitutional Referee Step (Optional)**:
  * **Condition:** Only runs if scenario has a `constitution.md` file.
  * **Input:** Constitution constraints, proposed metrics updates, narrative explaining the changes.
  * **LLM Task:** Review the metrics update against constitutional constraints and validate that:
    - Economic constraints are respected (budgets, resources)
    - Regulatory timelines are realistic (legislation, agreements)
    - Organizational changes are feasible (capacity growth, hiring)
    - Physical constraints are honored (compute, infrastructure)
  * **Output:** Either "APPROVED" or "VIOLATIONS: [list of issues]"
  * **Parser Tolerance:** The parser accepts those responses even when the whole referee output is wrapped in a single outer fenced Markdown code block.
  * **Retry Logic:** If violations are found, the orchestrator makes one additional LLM correction pass:
    - The referee first returns structured violations
    - A dedicated correction prompt asks the LLM to minimally revise the metrics and narrative so they comply
    - The referee then validates the revised output once more
    - If the revised output still violates the constitution or cannot be parsed, the run continues with the latest proposal and records that it was accepted with violations
  * **Model:** Uses dedicated `referee` model (default: x-ai/grok-4.1-fast) for cost-effective validation.
  * **Metadata:** Saves detailed validation results to `5-constitutional-check.json` including:
    - Status (approved, violations_found, max_attempts_reached, parse_error)
    - Number of iterations
    - List of violations found per iteration
    - Final action taken
  * **Cost:** Minimal - uses fast, cheap model with short max_tokens (1000).

6. **Summarization Step**:
  * **Input:** Current `historical_summary` and the new `narrative` from Metrics Step.
  * **LLM Task:** Condense the new narrative and append it to the historical summary, keeping the total length manageable.
  * **Purpose:** Prevent context window explosion over long simulations.

### Prompt Engineering (`prompts.py` & Templates)
- **Jinja2 Templates:** All prompts are generated using Jinja2 templates located in `scenarios/{name}/system-prompts/` and `scenarios/{name}/user-prompts/`, defaulting to `templates/systemp-prompts/` and `templates/user-prompts/` if none are found.
- **Context:** Templates receive a rich context object including `turn`, `time_period`, `metrics_json`, `world_state`, `events_list`, and individual metric variables (`metric_X`).
- **Output Language:** The `output_language` setting injects instructions into templates to control the language of the LLM's response (e.g., "Please write your response in Swedish").

### LLM Integration (`llm.py`)
- **Client:** Uses `httpx` to call OpenRouter API.
- **Fallback:** Supports a list of models for fallback (e.g., try Claude 3.5 Sonnet, then Haiku).
- **Parsing:** Includes strict regex-based parsing for JSON and specific Markdown headers.

### Persistence (`output.py`)
- **Incremental Writing:** Results are saved to disk *immediately* after each step of the turn loop.
- **Structure:** Each run gets a timestamped directory. If a timestamp collides, the writer appends a numeric suffix (for example `run-20260304-102254-01`) instead of reusing the same directory. Each turn gets a subdirectory.
- **Crash Resilience:** If the simulation crashes, all progress up to the last successful step is preserved.
- **Resumption:** The directory structure and `summary.json` support resuming crashed runs or extending completed runs.

### Batch Execution (`cli.py`)
- **CLI Command:** `python -m scenario_lab.cli batch-run <target...> [options]`
- **Target Types:** Accepts scenario directories and variant YAML files. With `--variants`, a scenario directory expands to all YAML files in its `variants/` directory.
- **Repeat Runs:** `--repeat N` runs each resolved target N times, which supports Monte Carlo-style repeated runs of the same scenario without repeating the path manually.
- **Execution Model:** Batch jobs run as separate child processes that invoke the normal `run` command. This keeps each simulation isolated while preserving the same orchestration and persistence behavior as single runs.
- **Concurrency Control:** Uses bounded parallelism via `--max-concurrency` rather than launching every job at once.
- **Logging:** Each batch job writes its stdout/stderr to a per-job log file under the owning scenario's `runs/batch-logs/` directory.
- **Model Checks:** Batch jobs bypass interactive model preflight prompts so unattended runs do not block on TTY input.
- **Batch Resume:** `python -m scenario_lab.cli batch-resume <target...> [options]` resumes multiple runs with the same bounded-concurrency/process-isolation model. Scenario directories and `runs/` directories expand to incomplete `run-*` directories automatically; explicit run directories are resumed directly.

### Resume & Branching (`resume.py`)

**Module:** `scenario_lab/resume.py` provides core functionality for loading and manipulating run state.

**Key Functions:**
- `detect_last_turn(run_dir)`: Finds the highest completed turn by validating turn directory structure.
- `validate_run_directory(run_dir)`: Checks for required files (`config.json`, `summary.json`, turn directories).
- `get_scenario_path_from_run(run_dir)`: Navigates from run directory to scenario directory.
- `load_run_state(run_dir, from_turn, state_modifications)`: Loads complete scenario state from disk, with optional modifications.
- `create_branch(parent_run_dir, from_turn, output_base, state_modifications, config_overrides)`: Creates a new branched run.

**Resume Implementation:**
- **CLI Command:** `python -m scenario_lab.cli resume <run_dir> [options]`
- **Options:**
  * `--from-turn N`: Resume from specific turn (default: auto-detect last completed)
  * `--turns N`: Total turns to run (overrides config)
  * `--model X`: Override all LLM models
  * `--override key=value`: Override any config value
- **Behavior:**
  * Loads state from the specified turn (metrics, narrative, rules, notepad, historical summary, occurred events)
  * Continues execution in the *same* run directory (no duplication)
  * Updates `summary.json` with `resumed_at` and `resumed_from_turn` metadata
  * Useful for: crashed runs, extending completed scenarios, switching to better/cheaper models
- **State Loading:**
  * Reads `turn-XX/4-metrics.json` to restore metric values
  * Reads `turn-XX/4-world-state.md` to restore narrative
  * Reads `turn-XX/3-metric-rules.md` to restore rules
  * Reads `turn-XX/5-notepad.md` to restore game master notes
  * Reads `turn-XX/6-historical-summary.md` to restore turn history
  * Reads `summary.json` to restore occurred events list

**Branch Implementation:**
- **CLI Command:** `python -m scenario_lab.cli branch <run_dir> --from-turn N [options]`
- **Options:**
  * `--from-turn N`: **Required** - Turn number to branch from
  * `--modify-metric id=value`: Modify metric value(s) for "what-if" scenarios (repeatable)
  * `--modify-narrative "text"`: Replace narrative text
  * `--model X`: Override all LLM models
  * `--override key=value`: Override any config value
  * `--turns N`: Total turns to run from branch point
- **Behavior:**
  * Creates a *new* timestamped run directory
  * Copies turn directories 1 through N from parent run
  * Loads state from turn N and applies modifications
  * Continues execution from turn N+1 in new directory
  * Useful for: "what-if" experiments, sensitivity analysis, model comparison
- **Metadata Tracking:**
  * `config.json` includes: `parent_run`, `branch_turn`, `branch_created_at`, `state_modifications`, `config_overrides`
  * `summary.json` includes: `metadata` object with parent run reference, branch point, and all modifications
  * Preserves full lineage for analysis and reproducibility
- **State Modifications:**
  * Metrics: Modified values are clamped to min/max bounds with warnings
  * Narrative: Completely replaces the world state narrative
  * Notepad: Replaces game master notes
  * Rules: Replaces metric rules markdown
  * Persistence: Modified branch-point state is written back to copied turn files and reflected in `summary.json` immediately

**Orchestrator Integration:**
- `run_simulation()` now accepts `start_turn` parameter (default: 1)
- Turn loop iterates from `start_turn` to `max_turns` instead of 1 to `max_turns`
- No other orchestrator changes needed - pre-loaded scenario state works seamlessly

**File Structure for Resume/Branch:**
```
run-YYYYMMDD-HHMMSS/
├── config.json                   # Contains metadata for branched runs
├── summary.json                  # Contains resume/branch metadata
└── turn-XX/                      # Validated for completeness before loading
    ├── 1-events.json
    ├── 2-actors/*.md
    ├── 3-metric-rules.md         # Versioned rules with changelog
    ├── 3-metric-rules-metadata.json  # Rules version and changelog metadata
    ├── 4-metrics.json            # Source of truth for metric values
    ├── 4-world-state.md          # Source of truth for narrative
    ├── 5-constitutional-check.json   # Constitutional validation results (if constitution exists)
    ├── 5-notepad.md              # Source of truth for GM notes
    └── 6-historical-summary.md   # Source of truth for history
```

**Metric Rules Format:**
Each `3-metric-rules.md` file includes:
- Version number in header (e.g., "# Metric Rules v3 (Turn 4)")
- Changelog section documenting all changes from previous version
- Full set of current rules

**Constitutional Validation Metadata:**
The `5-constitutional-check.json` file (when present) includes:
- Status: approved, violations_found, max_attempts_reached, or parse_error
- Iterations: Number of validation attempts
- Violations found: List of violations per iteration with details
- Final action: Whether metrics were accepted or corrected

**Future Extensions:**
- Batch branch: Create multiple branches from a batch of runs
- Parallel execution for resume/branch operations

### Validation (`validator.py`)

**Purpose:** Catch errors before expensive LLM calls by validating scenario structure, references, and configuration.

**Key Validation Functions:**

1. **Metric Reference Validation** (`validate_metric_references`):
   - Checks that all metric references in actor descriptions, event conditions, event probabilities, and metric rules point to existing metrics
   - Prevents runtime failures from undefined metric references

2. **Event Probability Validation** (`validate_event_probabilities`):
   - Validates that probability formulas are valid mathematical expressions
   - Uses a **secure AST-based evaluator** that prevents code injection attacks
   - Only allows safe operations: arithmetic (+, -, *, /, //, %, **), comparisons (<, >, ==, etc.), min/max functions, and metric variable references
   - Rejects dangerous operations: imports, attribute access, arbitrary function calls, assignments, control flow
   - Verifies formulas evaluate to valid range [0, 1] with sample data
   - Handles both static probabilities (e.g., "10 procent per runda") and dynamic formulas (e.g., "unemployment / 100")
   - **Security:** Uses `SafeExpressionEvaluator` class that parses expressions into Abstract Syntax Trees (AST) and validates each operation before execution, eliminating the security risks of Python's `eval()` function

3. **Model Hygiene Checks** (`model_audit.py` + `validate_scenario` warnings):
   - Applies local heuristic warnings to configured LLM model names before expensive runs
   - Flags clearly legacy model families (for example GPT-3.5 / Claude 2 style names)
   - Flags dated snapshot models older than a configured age threshold (currently 180 days)
   - Reads optional repository policy from `model-policy.yaml` to make hygiene rules editable without code changes
   - Policy supports:
     - `max_snapshot_age_days`: override the snapshot age threshold
     - `allowed_patterns`: optional regex allowlist; if non-empty, models outside it are warned
     - `blocked_patterns`: regex denylist; matching models are warned
   - Static validation remains local and deterministic; optional run-time replacement suggestions may query OpenRouter's model catalog for current pricing and capability metadata
   - Replacement selection prefers models that are both newer and cheaper than the current one when such candidates exist, while preserving modality compatibility

3. **LLM Configuration Validation** (`validate_llm_config`):
   - Validates model strings follow OpenRouter format
   - Ensures temperature is in valid range [0, 2]
   - Checks max_tokens is reasonable (> 100, < 100000)
   - Validates all task-specific model configurations (events, actors, rules, metrics, summary)

4. **Actor Reference Validation** (`validate_actor_references`):
   - Ensures all actors in scenario.yaml have corresponding files
   - Detects orphaned actor files

5. **Date and Time Scale Validation** (`validate_time_config`):
   - Validates start_date is in correct format (YYYY-MM)
   - Checks time_scale is parseable
   - Ensures max_turns doesn't exceed reasonable limits

**Integration:**
- `validate_scenario(scenario_path)`: Runs all validation checks and returns `ValidationResult` with errors and warnings
- CLI command: `python -m scenario_lab.cli validate scenarios/sweden-ai-2030`
- Auto-validation: `--validate` flag on run command to validate before executing

**Value:**
- **Cost Savings:** Catch errors before LLM API calls
- **Developer Experience:** Fast feedback on scenario design
- **Reliability:** Fewer runtime failures
- **Documentation:** Validation errors help users understand requirements

### Cost Tracking (`llm.py`, `output.py`)

**Purpose:** Track token usage and estimate costs to help users budget and optimize LLM API spending.

**Token Usage Tracking:**
- `TokenUsage` dataclass stores prompt_tokens, completion_tokens, total_tokens, model, and estimated_cost_usd
- `LLMClient` tracks usage for every API call in `call_history` and maintains `total_usage`
- Token counts extracted from OpenRouter API responses
- Cost estimation based on pricing table for common models (per 1M tokens)

**Pricing Table:**
- Maintains pricing for common models (Claude, GPT, Grok, etc.)
- Pricing in USD per 1M tokens (separate for prompt and completion)
- Returns $0.00 for unknown models with warning
- Can be updated as model pricing changes

**Cost Reporting:**
- Saved to `costs.json` in run directory with detailed breakdown
- Tracks costs by turn, by task (events, actors, rules, metrics, summary), and by model
- Includes total tokens, total cost, and averages

**CLI Commands:**
- `estimate`: Pre-run cost estimation based on scenario configuration
- `costs`: Display cost report for completed runs with optional `--detailed` breakdown

**Value:**
- Budget control and planning
- Model selection guidance (cost vs. quality trade-offs)
- Optimization of expensive steps
- Transparency in API spending

### Progress Tracking (`progress.py`)

**Purpose:** Provide real-time feedback during long-running simulations to improve user experience.

**ProgressTracker Class:**
- Tracks current turn, step, and timing information
- Displays turn headers with ETA estimates
- Updates step status (in_progress, completed)
- Records turn completion times for ETA calculation

**Features:**
- Turn-level progress with numbered headers
- Step-by-step status updates (Events, Actors, Rules, Metrics)
- Estimated time remaining based on average turn duration
- Cost information during execution (if tracking enabled)

**CLI Options:**
- Default: Progress tracking enabled
- `--no-progress`: Disable for cleaner logs
- `--quiet`: Minimal output mode

**Display Format:**
```
============================================================
TURN 3/10
Estimated time remaining: 14.5 minutes
Cost so far: $0.15 | Projected total: $0.50
============================================================
  [Events] ✓ Complete
  [Actors] Processing...
```

**Value:**
- User feedback for long operations (2-5 minutes per turn)
- Debugging aid to identify slow steps
- Progress monitoring for batch runs

### CLI (`cli.py`)
- **Entry Point:** `python -m scenario_lab.cli`.
- **Commands:** `run`, `batch-run`, `batch-resume`, `resume`, `branch`, `validate`, `audit-models`, `visualize`, `costs`, `estimate`
- **Overrides:** Supports `--override key=value` to modify configuration at runtime (e.g., `--override output_language=Spanish`).
- **Validation:** Supports `--validate` flag to validate scenarios before running
- **Model Preflight:** `run` performs model hygiene checks by default and can be bypassed with `--skip-model-checks`
- **Progress:** Supports `--no-progress` and `--quiet` flags for output control

## 4. Evaluation & Testing
- **Unit Tests:** Standard pytest suite for Python logic.
- **LLM Evals:** Specialized suite in `tests/evals/llm-event-conditions/` to benchmark LLM performance on logic, math, and hallucination prevention.
- **Security Tests:** Comprehensive security test suite in `tests/test_security.py` covering path traversal, template injection, and code execution prevention.

## 5. Security Architecture

Scenario Lab implements defense-in-depth security measures to protect against common vulnerabilities:

### Template Security
- **Sandboxed Jinja2 Environment:** All user-provided templates (custom system/user prompts) are rendered using Jinja2's `SandboxedEnvironment`.
- **Protection Against SSTI:** The sandbox prevents Server-Side Template Injection attacks by blocking access to dangerous attributes (`__class__`, `__mro__`, `__bases__`) and preventing code execution.
- **Implementation:** `prompts.py` creates a sandboxed environment in `__init__` and uses `jinja_env.from_string()` for all template rendering.

### Path Security
- **Base Scenario Validation:** The `base` field in `scenario.yaml` is validated to prevent path traversal attacks. Base scenarios must be within the scenarios directory structure.
- **Actor ID Validation:** (Pending - Issue #3) Actor IDs should be validated to prevent path traversal in output file creation.
- **Implementation:** `loader.py` uses `Path.relative_to()` to ensure base paths don't escape allowed directories.

### Input Security
- **Safe YAML Loading:** Uses `yaml.safe_load()` instead of `yaml.load()` to prevent arbitrary object deserialization.
- **AST-Based Expression Evaluation:** Event probability formulas are evaluated using a safe AST-based evaluator, not `eval()`. Only allows basic arithmetic operations and metric variable references.
- **API Key Handling:** API keys are only loaded from environment variables, never hardcoded or logged.

### Security Testing
- **15+ Security Tests:** Comprehensive test coverage in `tests/test_security.py`:
  - Path traversal prevention (3 tests)
  - Template injection prevention (6 tests)
  - Code execution prevention
  - File access prevention
- **Continuous Validation:** All security tests run as part of the standard test suite.

### Fixed Vulnerabilities
See [SECURITY_AUDIT.md](../SECURITY_AUDIT.md) for detailed audit results and fixes:
- ✅ Path Traversal in Base Scenario Loading (Fixed 2025-12-07)
- ✅ Jinja2 Template Injection (Fixed 2025-12-08)

## 6. Extension Guidelines
- **Update This Document first:** This document must be the ground truth and reflect how the project should work. Before adding or changing substantial functionality, it should be described here.
- **New Features:** Must not break the "Pure LLM" philosophy. Avoid adding game logic to Python.
- **Prompts:** Modify templates, not Python code, whenever possible.
- **No backwards Compatibility:** As the project is still in an early phase, there is no need for backwards compatibility. Old scenarios (e.g., `sweden-ai-2030`) and other files are either updated or deleted when changing data models.
- **Language:** Both code and scenarios should be written in English. Code comments, documentation, scenario files (YAML, Markdown), and all technical content should use English for consistency and broader accessibility.
