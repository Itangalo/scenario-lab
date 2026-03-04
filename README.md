# Scenario Lab V4

AI-powered scenario simulation framework with pure LLM-driven architecture.

## Design Philosophy

V4 is a radical simplification from V3. Instead of complex Python game logic, **we lean into the LLM**:

- LLMs handle **all** complexity: narrative, metrics, rules interpretation
- Python is minimal orchestration: load prompts, call APIs, save files
- No communication phases or action points
- No hybrid architecture - pure LLM reasoning
- One simple turn loop: Events → Actors → Metric Rules Update → Metrics Update

**Result:** Simpler code, more flexible scenarios, easier to iterate.

## Status

✅ **V4 core implementation is complete**

All 6 implementation phases finished:
- Phase 1: Foundation (models + loader)
- Phase 2: Prompt builder
- Phase 3: LLM client
- Phase 4: Orchestrator
- Phase 5: Output manager
- Phase 6: CLI

V3 is archived in the `v3-archive` tag.

## Documentation

The central ground truth for the system architecture and design is located in:
[**docs/ARCHITECTURE.md**](docs/ARCHITECTURE.md)

Please refer to this document before adding new functionality or modifying core components.

## Quick Start

### Installation

```bash
# Install dependencies
pip install -e .

# Set up API key
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### Usage

```bash
# Run a simulation
python -m scenario_lab.cli run scenarios/sweden-ai-2030

# Run with specific number of turns
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --turns 5

# Override the model
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --model google/gemini-3-flash-preview

# Preview prompts without running (dry run)
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --dry-run

# Override configuration settings at runtime
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --override output_language=Swedish --override llm.temperature=0.5

# Validate scenario before running
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --validate

# Validate without running
python -m scenario_lab.cli validate scenarios/sweden-ai-2030

# Audit configured models across all scenarios
python -m scenario_lab.cli audit-models

# Audit one scenario tree and output JSON
python -m scenario_lab.cli audit-models scenarios/sweden-ai-2030 --json

# Skip default model hygiene checks when starting a run
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --skip-model-checks

# Estimate costs before running
python -m scenario_lab.cli estimate scenarios/sweden-ai-2030 --turns 10

# View cost report for completed run
python -m scenario_lab.cli costs scenarios/sweden-ai-2030/runs/run-20251205-120000 --detailed

# Disable progress tracking for cleaner logs
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --no-progress

# Minimal output mode
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --quiet
```

### Output

Results are saved in timestamped directories:

```
scenarios/*/runs/run-YYYYMMDD-HHMMSS/
├── config.json              # Scenario configuration
├── summary.json             # Final results
├── costs.json               # Token usage and cost tracking
└── turn-XX/
    ├── 1-events.json        # Triggered events
    ├── 2-actors/            # Actor outputs (markdown)
    ├── 3-metric-rules.md    # Updated rules
    ├── 4-metrics.json       # Updated metrics
    └── 4-world-state.md     # Turn narrative
```

## Key Features

### Scenario Validation

Comprehensive validation catches errors before expensive LLM calls:

**What it validates:**
- Metric references in actors, events, and rules
- Event probability formulas (static values and mathematical expressions)
- LLM configuration (model strings, temperature, max_tokens)
- Model hygiene warnings (clearly legacy families, dated snapshots older than ~6 months, and optional repo policy mismatches)
- Actor references (ensuring all configured actors have files)
- Time configuration (start_date format, max_turns limits)

**Run-time model preflight (default on `run`):**
- Warns before execution if the configured models look stale or risky
- Tries to suggest replacements from OpenRouter's models catalog
- Prefers replacements that are both newer and cheaper than the current model when available
- Lets you accept replacements interactively before the simulation starts
- Can be disabled with `--skip-model-checks`
- Uses the repository-local `model-policy.yaml` file so teams can tune the rules without changing Python code

**Smart probability handling:**
- Static probabilities: "10%", "5 percent per round"
- Mathematical formulas: `unemployment / 100`, `2 * ai_capability / 100`
- Natural language: "Double the value of unemployment" (LLM will interpret)

**Usage:**
```bash
# Validate before running (blocks execution on errors)
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --validate

# Validate without running
python -m scenario_lab.cli validate scenarios/sweden-ai-2030

# Example output:
# ✅ Scenario is valid!
# ⚠️  Warnings:
#   - Actor 'government' has no short description
```

### Cost Tracking and Estimation

Track token usage and estimate costs to budget and optimize LLM spending:

**Features:**
- Real-time token counting for all LLM API calls
- Cost estimation using pricing table for common models
- Breakdown by turn, task (events/actors/rules/metrics), and model
- Pre-run cost estimation to plan experiments

**Usage:**
```bash
# Estimate costs before running
python -m scenario_lab.cli estimate scenarios/sweden-ai-2030 --turns 10

# Example output:
# Estimated token usage per turn: ~13,000 tokens
# Total simulation: ~130,000 tokens
# Estimated cost: $0.45 - $0.65 USD

# View cost report after run
python -m scenario_lab.cli costs scenarios/sweden-ai-2030/runs/run-20251205-120000

# Example output:
# Total cost: $0.52 USD
# Total tokens: 145,234
# Average per turn: $0.052 USD (14,523 tokens)
#
# By Task:
#   Actors: $0.23 (65,321 tokens, 40 calls)
#   Metrics: $0.10 (28,234 tokens, 10 calls)
#   Events: $0.07 (20,145 tokens, 10 calls)

# Detailed breakdown by turn
python -m scenario_lab.cli costs run-20251205-120000 --detailed
```

**Cost data saved to `costs.json`:**
- Total tokens and cost
- Breakdown by turn, task, and model
- Individual call history

### Progress Tracking

Real-time feedback during long-running simulations:

**Features:**
- Turn-by-turn progress with numbered headers
- Step status updates (Events, Actors, Rules, Metrics)
- Estimated time remaining based on average turn duration
- Cost tracking during execution
- Configurable verbosity levels

**Display example:**
```
============================================================
TURN 3/10
Estimated time remaining: 14.5 minutes
Cost so far: $0.15 | Projected total: $0.50
============================================================
  [Events] ✓ Complete
  [Actors] Processing actor 2/4...
  [Rules] ✓ Complete
  [Metrics] Processing...
```

**Options:**
```bash
# Default: progress tracking enabled
python -m scenario_lab.cli run scenarios/sweden-ai-2030

# Disable for cleaner logs
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --no-progress

# Minimal output
python -m scenario_lab.cli run scenarios/sweden-ai-2030 --quiet
```

## LLM Output Parsing Requirements

For certain steps, the system expects specific Markdown headers in the LLM's response to correctly parse and extract information. It is crucial that these headers are used verbatim, even if the content of the response is in a different language.

**Metrics Update Step:**
The `metrics-update` prompt expects the following exact headers for parsing:
*   `## Metrics` (followed by a JSON object)
*   `## Narrative` (followed by the narrative text)
*   `## Notepad` (optional, for persistent notes)

These headers should not be translated by the LLM, regardless of the `output_language` setting.

## V4 Architecture

### Turn Loop

Each turn represents a time period (e.g., 6 months) and follows this sequence:

1. **Exogenous Events** - LLM determines which external events occur based on probabilities and conditions
2. **Actor Actions** - Each actor decides their goals and actions for the turn
3. **Metric Rules Update** - LLM reviews and updates the quantitative rules governing metrics
4. **Metrics Update** - LLM updates all metrics and generates narrative based on actions and rules

### Key Concepts

**Metrics**
- Pure numbers with metadata (min/max/unit)
- Represent quantitative state: `ai_capability`, `unemployment`, `public_sentiment`, etc.

**Metric Rules**
- Quantitative rules describing how metrics change
- Examples: "ai_capability doubles every 6 months", "high unemployment decreases public_sentiment"
- LLM can modify rules based on world changes

**World State**
- The narrative describing what happened during the turn
- Generated by LLM based on actor actions and metric changes
- Serves as input for actors in the next turn

**Actors**
- Represent stakeholders: governments, organizations, interest groups
- Each actor has goals and takes actions each turn
- Actors receive the same world state (no information asymmetry in V4)

**External Events**
- Exogenous happenings with probabilities and conditions
- Examples: "AI breakthrough (5% per turn)", "Election (100% when November 2026 in turn period)"

### Information Flow

```
Turn N starts with:
├── Previous World State (narrative)
├── Current Metrics (numbers)
└── Metric Rules (quantitative relationships)

LLM processes:
1. Events: What external events occur?
2. Actors: What do actors do?
3. Rules: Should any metric rules change?
4. Metrics: Update numbers and write narrative

Turn N+1 starts with:
├── New World State (from step 4)
├── New Metrics (from step 4)
└── Updated Metric Rules (from step 3)
```

## Project Structure

```
scenario-lab/
├── README.md
├── CLAUDE.md                    # Development notes for Claude Code
├── .gitignore
├── pyproject.toml               # Python package configuration
├── scenario_lab/                # Core Python package
│   ├── models.py                # Data models
│   ├── loader.py                # Scenario file parsers
│   ├── orchestrator.py          # Turn execution engine
│   ├── prompts.py               # Prompt builder
│   ├── llm.py                   # LLM client with fallback support
│   ├── output.py                # Output persistence
│   └── cli.py                   # Command-line interface
├── prompts/                     # System prompt templates
│   └── system/
│       ├── events.md
│       ├── actor.md
│       ├── metric-rules.md
│       └── metrics-update.md
├── docs/
│   └── V4/
│       ├── design-spec.md       # V4 architecture documentation
│       └── early-testing/       # Test runs and frozen prompts
├── tests/
│   └── evals/
│       └── llm-event-conditions/  # LLM evaluation suite (Issue #120)
│           ├── README.md
│           ├── test_event_conditions.py
│           ├── ground_truth.yaml
│           └── scenario/        # Minimal eval scenario
└── scenarios/
    └── sweden-ai-2030/          # Example scenario
        ├── background/          # Context and actor descriptions
        ├── metrics.md           # Metric definitions (markdown)
        ├── events.md            # External events (markdown)
        ├── metric-rules.md      # Quantitative rules
        ├── constitution.md      # Constitutional constraints (optional)
        ├── scenario.yaml        # Scenario configuration
        └── variants/            # Scenario variants
```

## Creating a Scenario

A scenario consists of:

### 1. Background Files (Markdown)

**context.md** - World background and initial state
**actors/*.md** - Actor descriptions with goals and context

### 2. Scenario Configuration (YAML)

```yaml
name: "My Scenario"
description: "Brief description"
time_scale: "6 months per turn"
start_date: "2026-01"
max_turns: 10
actors:
  - ActorName1
  - ActorName2
output_language: "English" # Optional: Set the language for LLM-generated text
```

### 3. Metrics (YAML)

```yaml
metrics:
  - id: metric_name
    description: "What this metric represents"
    min: 0
    max: 100
    unit: "percent"
    start_value: 50
```

### 4. Events (YAML)

```yaml
events:
  - id: election_2026
    description: "National election"
    probability: 1.0  # 100%
    condition: "November 2026 in turn period"
    can_repeat: false
```

### 5. Constitutional Constraints (Markdown - Optional)

**constitution.md** - Invariant "must-hold" rules that prevent unrealistic outcomes.

```markdown
# Constitutional Constraints

These invariant rules must always hold in this scenario:

## Economic Constraints
- Budget cannot exceed revenue without explicit borrowing/deficit
- Capital expenditures require funding source
- Economic effects have minimum 1-turn lag

## Regulatory Constraints
- New legislation requires minimum 1 turn from proposal to effect
- International agreements require minimum 2 turns
- Regulatory capacity grows max 20% per turn without major investment

## Organizational Constraints
- Agency/organization capacity grows max 30% per turn organically
- Hiring/training has 1-turn lag before productivity
- Expertise cannot be created instantly

## Physical Constraints
- Compute/hardware has supply constraints
- Infrastructure projects have realistic timelines
- Resource scarcity is real
```

**When to use:** Add constitutional constraints when your scenario risks unrealistic outcomes like:
- Instant budgets appearing when needed
- Legislation taking effect immediately
- Organizations scaling infinitely fast
- Physical resources appearing magically

The LLM will validate metrics updates against these constraints after each turn.

## Example: Sweden AI 2030

Located in `scenarios/sweden-ai-2030/`, this scenario explores AI development in Sweden from 2026-2030.

**Actors:**
- Government (innovation vs. regulation)
- Labor Unions (worker protection)
- Business Sector (AI adoption)
- Media (public discourse)

**Metrics:**
- `ai_capability` - Hours of work AI can handle
- `ai_adoption_sweden` - Percent regularly using AI
- `unemployment` - Unemployment rate
- `public_sentiment_to_ai` - Public opinion scale

**Events:**
- AI breakthrough, AI stall, bubble collapse
- Sweden election, Taiwan blockade
- AI incidents and labor strikes

## LLM Evaluation Suite

V4 includes an automated pytest-based evaluation system for testing LLM performance on event condition interpretation.

**Location:** `tests/evals/llm-event-conditions/`

**Purpose:** Test whether LLMs can correctly:
1. Interpret conditions (e.g., "metric_a > 40")
2. Calculate probabilities from formulas (e.g., "2 * unemployment / 100")
3. Avoid hallucinations (not reference non-existent metrics)
4. Handle temporal conditions (turn-based and date-based triggers)

**Features:**
- 20 test events across 4 capability categories
- Ground truth YAML with expected outputs
- Minimal eval scenario (4 metrics, 1 actor)
- Weighted scoring with category-specific thresholds
- Comprehensive documentation

**Usage:**
```bash
# Set API key
export OPENROUTER_API_KEY="your_key_here"

# Run all evaluation tests
pytest tests/evals/llm-event-conditions/ -v

# Test specific model
export TEST_LLM_MODEL="x-ai/grok-4.1-fast"
pytest tests/evals/llm-event-conditions/ -v

# Test specific category
pytest tests/evals/llm-event-conditions/ -k "hallucination" -v
```

**Expected Output:**
```
============================================================
EVALUATION RESULTS
============================================================
condition_interpretation      : 87.5% (7/8) [weight: 1.0]
probability_calculation       : 100.0% (4/4) [weight: 1.0]
hallucination_prevention      : 100.0% (3/3) [weight: 2.0]
temporal_conditions           : 83.3% (10/12) [weight: 1.0]
------------------------------------------------------------
OVERALL SCORE                 : 91.7%
============================================================
```

**See:** `tests/evals/llm-event-conditions/README.md` for detailed documentation.

## Development Status

### Completed
✅ V4 design specification
✅ System prompt templates
✅ Example scenario (Sweden AI 2030)
✅ Test data and frozen prompts
✅ Python orchestrator
✅ Scenario file parsers (loader.py)
✅ Turn execution engine (orchestrator.py)
✅ CLI interface (cli.py)
✅ Output persistence (output.py)
✅ LLM evaluation suite for event conditions (Issue #120)
✅ Flat prompt evaluation suite for event conditions
✅ Progress tracking and real-time feedback (Issue #133)
✅ Cost tracking and estimation (Issue #137)
✅ Comprehensive scenario validation (Issue #134)
✅ Resume and branch functionality (Issue #129)

### Next Steps
⬜ End-to-end testing with real LLM
⬜ Additional example scenarios
⬜ Multi-run analysis tools
⬜ Visualization tools

## Security

Scenario Lab V4 implements security best practices to protect against common vulnerabilities:

**Fixed Vulnerabilities:**
- ✅ **Path Traversal in Base Scenario Loading** - Base scenarios are validated to prevent directory escaping
- ✅ **Jinja2 Template Injection (SSTI)** - All templates use sandboxed environment to prevent code execution

**Security Features:**
- Sandboxed Jinja2 template rendering for custom prompts
- Path validation for scenario inheritance
- Safe YAML loading
- API keys from environment variables only
- AST-based safe expression evaluator (no eval())

**Security Testing:**
- Comprehensive security test suite in `tests/test_security.py`
- 15+ tests covering path traversal, template injection, and code execution attempts
- All security tests passing ✅

For detailed security information, see [SECURITY_AUDIT.md](SECURITY_AUDIT.md).

## Why V4?

V3 was powerful but complex:
- Communication phases with action points
- Hybrid LLM + Python validation
- Relationship tracking
- Fact ledgers
- Information asymmetry

V3 taught us: **LLMs are better at complexity than we thought.**

V4 simplifies radically:
- No phases, no action points
- LLM handles all logic
- Simple linear turn flow
- Easier to build, easier to iterate

Trade-offs:
- Less deterministic (LLM interprets rules)
- No built-in actor communication
- Single world view (no information asymmetry)

But gains:
- 10x simpler code
- Faster iteration on scenarios
- LLM handles edge cases naturally
- Focus on prompt engineering, not Python

## V3 Archive

V3 code is preserved in the `v3-archive` tag:

```bash
git checkout v3-archive  # View V3 code
git checkout v4          # Return to V4 development
```

## License

MIT
