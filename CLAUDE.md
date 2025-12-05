# Scenario Lab V4 – Claude Code Instructions

## Project Overview

**Scenario Lab** is a framework for simulating complex strategic and political scenarios with AI agents. The system focuses on AI policy, geopolitics, and organizational strategy.

**Purpose:**

- Primary: Explore how LLMs can be used for scenario simulation
- Secondary: Identify patterns in outcomes through repeated simulations (both quantitative and qualitative)

**Status:** V4 core implementation is complete. V3 is archived in the `v3-archive` tag.

## Architecture – Pure LLM Design

V4 is a radical simplification from V3. Instead of complex Python logic, **we lean into the LLM**:

- **LLMs handle ALL complexity:** narrative, metrics, rule interpretation
- **Python is minimal orchestration:** load prompts, call APIs, save files
- **No communication phases** or action points
- **No hybrid architecture** - pure LLM reasoning
- **One simple turn loop:** Events → Actors → Metric Rules Update → Metrics Update

### Core Components

1. **Orchestrator (Python):** Minimal orchestration that runs the turn loop
2. **World State:** Narrative description of the world's state
3. **Metrics:** Quantitative values (e.g., `ai_capability`, `unemployment`, `public_sentiment`)
4. **Metric Rules:** LLM-managed rules for how metrics change
5. **Actors:** Simulation participants (countries, companies, organizations) with goals and actions
6. **Events:** Exogenous events with probabilities and conditions

## Turn Loop (V4)

Each turn represents a time period (e.g., 6 months):

1. **Events:** LLM determines which external events occur based on conditions and probabilities
2. **Actors:** Each actor decides goals and actions for the turn
3. **Metric Rules Update:** LLM reviews and updates quantitative rules
4. **Metrics Update:** LLM updates all metrics and generates narrative based on actions and rules

## File Structure (V4)

```
scenario-name/
├── scenario.yaml              # Configuration (time period, actors, LLM settings)
├── metrics.md                 # Metric definitions (markdown format)
├── events.md                  # Exogenous events (markdown format)
├── metric-rules.md            # Initial quantitative rules
├── background/
│   ├── context.md             # World background and initial state
│   └── actors/
│       ├── actor1.md          # Actor descriptions
│       └── actor2.md
└── runs/
    └── run-YYYYMMDD-HHMMSS/
        ├── config.json        # Run configuration
        ├── summary.json       # Final results
        └── turn-XX/
            ├── 1-events.json
            ├── 2-actors/
            │   └── actor.md
            ├── 3-metric-rules.md
            ├── 4-metrics.json
            └── 4-world-state.md
```

## Creating New Scenarios

A scenario consists of:

**1. Background (Markdown)**

- `context.md` - World background and initial situation
- `actors/*.md` - Actor descriptions with goals

**2. Configuration (YAML)**

```yaml
name: "Scenario Name"
description: "Brief description"
time_scale: "6 months per turn"
start_date: "2026-01"
max_turns: 10
actors:
  - actor1
  - actor2
llm:
  model: "anthropic/claude-sonnet-4"
  temperature: 0.7
  max_tokens: 2000
```

**3. Metrics (Markdown)**

```markdown
## metric_name
**Beskrivning:** What this metric represents
**ID:** metric_name
**Startvärde:** 50
**Min:** 0
**Max:** 100
**Enhet:** percent
```

**4. Events (Markdown)**

```markdown
## Event Name
**ID:** event_id
**Villkor:** When this can happen
**Sannolikhet:** 10 procent per runda
**Kan upprepas:** Ja/Nej
**Beskrivning:** What happens
```

## Technical Stack

- **Python:** 3.11+
- **Dependencies:** httpx, pyyaml, python-dotenv, pytest
- **Type hints:** Required throughout
- **LLM Provider:** OpenRouter API (supports Claude, GPT, Llama, etc.)

## LLM Evaluation Suite (Issue #120)

V4 includes a complete pytest-based evaluation system for testing LLM performance on event condition interpretation.

**Location:** `tests/evals/llm-event-conditions/`

**Purpose:** Test whether LLMs can correctly:

1. **Interpret conditions** - Understand when events can occur (e.g., "metric_a > 40")
2. **Calculate probabilities** - Evaluate formulas correctly (e.g., "2 * unemployment / 100")
3. **Avoid hallucinations** - Not reference metrics that don't exist
4. **Handle temporal conditions** - Understand turn- and date-based triggers

**Features:**

- 20 test events across 4 capabilities
- Ground truth YAML with expected results
- Minimal eval scenario (4 metrics, 1 actor)
- Weighted scoring with category-specific thresholds
- Complete documentation in README.md

**Usage:**

```bash
# Run all eval tests
export OPENROUTER_API_KEY="your_key"
pytest tests/evals/llm-event-conditions/ -v

# Test specific model
export TEST_LLM_MODEL="anthropic/claude-haiku-4"
pytest tests/evals/llm-event-conditions/ -v

# Test specific category
pytest tests/evals/llm-event-conditions/ -k "hallucination" -v
```

**Output:**

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

## Example: Sweden AI 2030

Scenario exploring AI development in Sweden 2026-2030.

**Location:** `scenarios/sweden-ai-2030/`

**Actors:**

- Government (innovation vs. regulation)
- Labor Unions (worker protection)
- Business Sector (AI adoption)
- Media (public discourse)

**Metrics:**

- `ai_capability` - Hours of work AI can handle
- `ai_adoption_sweden` - Percent regularly using AI
- `unemployment` - Unemployment rate
- `public_sentiment` - Public opinion

**Variants:**

- `cheap-with-fallback.yaml` - Cost-effective execution with fallback models

## CLI Usage

### Running Simulations

```bash
# Run simulation
python -m scenario_lab.cli scenarios/sweden-ai-2030

# Specific number of turns
python -m scenario_lab.cli scenarios/sweden-ai-2030 --turns 5

# Use specific model
python -m scenario_lab.cli scenarios/sweden-ai-2030 --model anthropic/claude-opus-4

# Dry run (show prompts without running)
python -m scenario_lab.cli scenarios/sweden-ai-2030 --dry-run

# Use variant
python -m scenario_lab.cli scenarios/sweden-ai-2030/variants/cheap-with-fallback.yaml
```

### Resume and Branch (Issue #129)

**Resume:** Continue interrupted or completed runs from the same directory

```bash
# Resume from last completed turn
python -m scenario_lab.cli resume scenarios/sweden-ai-2030/runs/run-20251205-120000

# Resume from specific turn
python -m scenario_lab.cli resume scenarios/sweden-ai-2030/runs/run-20251205-120000 --from-turn 3

# Resume with different model
python -m scenario_lab.cli resume scenarios/sweden-ai-2030/runs/run-20251205-120000 --model anthropic/claude-opus-4

# Resume and run to turn 10
python -m scenario_lab.cli resume scenarios/sweden-ai-2030/runs/run-20251205-120000 --turns 10

# Resume with config overrides
python -m scenario_lab.cli resume scenarios/sweden-ai-2030/runs/run-20251205-120000 --override llm.temperature=0.3
```

**Branch:** Create "what-if" scenarios by branching from a specific turn

```bash
# Branch from turn 3
python -m scenario_lab.cli branch scenarios/sweden-ai-2030/runs/run-20251205-120000 --from-turn 3

# Branch with modified metrics (what-if scenarios)
python -m scenario_lab.cli branch scenarios/sweden-ai-2030/runs/run-20251205-120000 \
  --from-turn 3 \
  --modify-metric ai_capability=150 \
  --modify-metric unemployment=10.0

# Branch with different model
python -m scenario_lab.cli branch scenarios/sweden-ai-2030/runs/run-20251205-120000 \
  --from-turn 3 \
  --model anthropic/claude-opus-4

# Branch with modified narrative
python -m scenario_lab.cli branch scenarios/sweden-ai-2030/runs/run-20251205-120000 \
  --from-turn 3 \
  --modify-narrative "A major AI breakthrough has occurred..."

# Branch with config overrides
python -m scenario_lab.cli branch scenarios/sweden-ai-2030/runs/run-20251205-120000 \
  --from-turn 3 \
  --override llm.temperature=0.9 \
  --turns 5
```

**Use Cases:**

- **Resume:** Interrupted simulations, extend completed runs, continue with different/better models
- **Branch:** Explore alternate scenarios, test sensitivity to initial conditions, compare outcomes with different LLM models

**Metadata Tracking:**

- Resume updates `summary.json` with `resumed_at` and `resumed_from_turn`
- Branch creates new run directory with `parent_run`, `branch_turn`, and `state_modifications` in metadata
- Both preserve full lineage for analysis and reproducibility

## Development Guidelines

1. **LLMs handle complexity** - Trust the LLM instead of writing Python logic
2. **Prompts are code** - Version and test system prompts carefully
3. **Log everything** - Save raw LLM input/output for debugging
4. **Start small** - 2 actors, 3 turns. Scale up when it works
5. **Use cheap models for iteration** - Haiku/Grok for dev, Sonnet/Opus for production
6. **Type hints required** - Throughout all code
