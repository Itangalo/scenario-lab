# Scenario Creation Guide

This guide walks you through creating, validating, and running scenarios in Scenario Lab V2.

For the complete YAML schema reference, see [AGENTS.md](../AGENTS.md).

## Quick Start

Create a minimal scenario in 5 minutes:

```bash
# 1. Create directory structure
mkdir -p scenarios/my-first-scenario/actors

# 2. Create scenario.yaml (see template below)
# 3. Create actor files in actors/ (see templates below)

# 4. Validate the scenario
scenario-lab validate scenarios/my-first-scenario

# 5. Run the scenario
scenario-lab run scenarios/my-first-scenario
```

---

## Directory Structure

Every scenario follows this structure:

```
scenarios/[scenario-name]/
├── scenario.yaml              # Main configuration (REQUIRED)
├── actors/                    # Actor definitions (REQUIRED)
│   ├── actor-one.yaml
│   └── actor-two.yaml
├── metrics.yaml               # Metrics to track (optional)
├── validation-rules.yaml      # QA configuration (optional)
├── exogenous-events.yaml      # Background events (optional)
└── background/                # Reference documents (optional)
    └── context.md
```

**Important:** Configuration files are placed directly in the scenario root, not in a subdirectory.

---

## Step 1: Create scenario.yaml

The main configuration file defines the scenario setup.

### Minimal Template

```yaml
name: "My First Scenario"
description: |
  A brief description of what this scenario explores.

initial_world_state: |
  # Starting Situation

  Describe the initial conditions here.

  **Key Facts:**
  - Fact 1
  - Fact 2

turns: 5
turn_duration: "1 week"

actors:
  - actor-one
  - actor-two
```

### Full Template (with all options)

```yaml
name: "Policy Negotiation Scenario"
description: |
  Simulation of stakeholders negotiating a new policy.

system_prompt: |
  You are participating in a policy negotiation simulation.
  Make realistic decisions based on your role's priorities.

initial_world_state: |
  # Starting Situation

  The government has announced plans for new regulations.
  Multiple stakeholders must negotiate the final policy.

  **Current Context:**
  - Regulatory deadline: 6 months
  - Public opinion: divided
  - Economic stakes: high

turns: 10
turn_duration: "2 weeks"
world_state_model: "anthropic/claude-3-5-sonnet-20241022"

actors:
  - government-official
  - industry-representative
  - civil-society-advocate

features:
  communications:
    enabled: true
    max_per_turn: 2

  exogenous_events:
    enabled: false

  metrics_extraction:
    enabled: true

  quality_assurance:
    enabled: true

  context_management:
    enabled: true
    max_context_tokens: 8000
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Scenario display name |
| `initial_world_state` | string | Starting situation (markdown) |
| `turns` | integer | Number of simulation turns |
| `actors` | list | Actor short names (must match filenames in actors/) |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | string | null | Brief scenario summary |
| `system_prompt` | string | null | System prompt for all actors |
| `turn_duration` | string | "1 week" | Duration per turn |
| `world_state_model` | string | "openai/gpt-4o-mini" | LLM for world synthesis |

---

## Step 2: Create Actor Files

Each actor needs a YAML file in the `actors/` directory. The filename must match the actor's `short_name`.

### Minimal Actor Template

```yaml
# actors/actor-one.yaml
name: "Actor One"
short_name: "actor-one"

llm_model: "openai/gpt-4o-mini"

system_prompt: |
  You are Actor One in this simulation.
  Your priorities are X, Y, and Z.

goals:
  - Primary goal
  - Secondary goal

constraints:
  - Key limitation
```

### Full Actor Template

```yaml
# actors/government-official.yaml
name: "Government Official"
short_name: "government-official"

llm_model: "anthropic/claude-3-5-sonnet-20241022"

system_prompt: |
  You are a senior government official responsible for regulatory policy.

  Your responsibilities include:
  - Balancing stakeholder interests
  - Ensuring regulatory effectiveness
  - Managing political considerations

  Make decisions that reflect real-world bureaucratic constraints.

goals:
  - Create effective, enforceable regulations
  - Build consensus among stakeholders
  - Meet the regulatory deadline
  - Maintain public confidence

constraints:
  - Must work within legal authority
  - Political pressures from multiple directions
  - Limited resources for enforcement
  - Need stakeholder buy-in for success

expertise: |
  High expertise in regulatory process and legal frameworks.
  Moderate understanding of industry technical details.
  Strong political awareness and negotiation skills.

decision_making_style: |
  You make decisions through careful analysis and stakeholder consultation:
  1. Assess legal and political feasibility
  2. Consider stakeholder positions and concerns
  3. Seek compromise solutions where possible
  4. Prefer incremental changes over dramatic shifts

private_information: |
  - Internal polling shows public support for regulation
  - Budget constraints may limit enforcement capabilities
  - Political leadership wants quick resolution

information_access:
  public: true
```

### Actor Naming Convention

- Use lowercase with hyphens: `government-official` (not `Government Official`)
- Filename must match `short_name`: `actors/government-official.yaml`
- Reference in scenario.yaml must match: `actors: [government-official]`

### Model Selection

| Model | Cost | Best For |
|-------|------|----------|
| `openai/gpt-4o-mini` | $0.15/M in | Testing, simple actors |
| `openai/gpt-4o` | $2.50/M in | Production scenarios |
| `anthropic/claude-3-5-sonnet-20241022` | $3.00/M in | Complex reasoning |
| `anthropic/claude-3-haiku-20240307` | $0.25/M in | Fast, cheap actors |

---

## Step 3: Validate Your Scenario

Before running, validate your configuration:

```bash
scenario-lab validate scenarios/my-first-scenario
```

This checks:

- YAML syntax
- Required fields present
- Actor files exist and match references
- Pydantic schema validation

### Common Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Actor file not found" | Missing YAML file | Create `actors/[name].yaml` |
| "Invalid turn_duration" | Wrong format | Use "N unit" format (e.g., "1 week") |
| "Invalid actor name" | Uppercase or spaces | Use lowercase-with-hyphens |

---

## Step 4: Estimate Costs

Before running, estimate the scenario cost:

```bash
scenario-lab estimate scenarios/my-first-scenario
```

This shows:

- Per-actor cost breakdown
- Total estimated cost
- Warnings for expensive configurations

---

## Step 5: Run Your Scenario

### Basic Run

```bash
scenario-lab run scenarios/my-first-scenario
```

### Limited Turns (for testing)

```bash
scenario-lab run scenarios/my-first-scenario --end-turn 3
```

### With Cost Limit

```bash
scenario-lab run scenarios/my-first-scenario --credit-limit 2.00
```

### Resume a Halted Run

If a run stops (rate limits, budget, etc.):

```bash
scenario-lab run scenarios/my-first-scenario --resume scenarios/my-first-scenario/runs/run-001
```

### Branch from a Previous Run

Create an alternative path from any turn:

```bash
scenario-lab run scenarios/my-first-scenario \
  --branch-from scenarios/my-first-scenario/runs/run-001 \
  --branch-at-turn 5
```

---

## Optional: Add Metrics

Create `metrics.yaml` to track quantitative outcomes:

```yaml
metrics:
  # Pattern-based extraction
  - name: agreement_level
    description: "Level of agreement between stakeholders"
    type: continuous
    range: [0, 10]
    extraction:
      type: llm
      prompt: |
        Rate the level of agreement between stakeholders (0-10):
        - 0 = Complete disagreement, conflict
        - 5 = Partial agreement, ongoing negotiation
        - 10 = Full consensus

        Respond with ONLY a number.

  # Keyword-based tracking
  - name: conflict_mentions
    description: "Frequency of conflict-related language"
    type: continuous
    range: [0, 100]
    unit: "mentions"
    extraction:
      type: keyword
      keywords:
        - "disagree"
        - "oppose"
        - "conflict"
        - "dispute"

export_format: json
auto_export: true
```

---

## Optional: Add Validation Rules

Create `validation-rules.yaml` for automated quality checks:

```yaml
validation_model: "openai/gpt-4o-mini"

checks:
  actor_decision_consistency:
    enabled: true
    severity: medium
    description: "Validates actor decisions align with stated goals"

  world_state_coherence:
    enabled: true
    severity: high
    description: "Validates world state updates logically follow from actions"

  information_access_consistency:
    enabled: true
    severity: medium
    description: "Validates actors only reference accessible information"

run_after_each_turn: true
generate_turn_reports: true
generate_summary: true
```

---

## Complete Walkthrough Example

Here's a copy-paste-ready example to create and run a complete scenario:

```bash
# Create directory structure
mkdir -p scenarios/budget-negotiation/actors

# Create scenario.yaml
cat > scenarios/budget-negotiation/scenario.yaml << 'EOF'
name: "Department Budget Negotiation"
description: |
  Two department heads negotiate budget allocation for the coming year.

system_prompt: |
  You are participating in a budget negotiation simulation.
  Each department has priorities but the total budget is fixed.
  Make realistic decisions that balance your needs with organizational constraints.

initial_world_state: |
  # Starting Situation

  The organization has $1M budget to allocate between two departments.
  Each department wants at least $600K for their priorities.
  The CFO has asked them to negotiate a fair split.

  **Constraints:**
  - Total budget: $1,000,000
  - Minimum viable for each dept: $350,000
  - Decision deadline: end of this process

turns: 5
turn_duration: "1 day"
world_state_model: "openai/gpt-4o-mini"

actors:
  - engineering-head
  - marketing-head
EOF

# Create first actor
cat > scenarios/budget-negotiation/actors/engineering-head.yaml << 'EOF'
name: "Engineering Department Head"
short_name: "engineering-head"

llm_model: "openai/gpt-4o-mini"

system_prompt: |
  You are the Head of Engineering, advocating for your department's budget.

  Your priorities:
  - Hire 3 new developers ($400K)
  - Upgrade infrastructure ($150K)
  - Training and tools ($50K)

  You need at least $500K to maintain operations, ideally $600K.

goals:
  - Secure at least $500K for engineering
  - Prioritize hiring over infrastructure if needed
  - Maintain good working relationship with marketing

constraints:
  - Cannot exceed total available budget
  - Must reach agreement by deadline
  - Need to justify all spending
EOF

# Create second actor
cat > scenarios/budget-negotiation/actors/marketing-head.yaml << 'EOF'
name: "Marketing Department Head"
short_name: "marketing-head"

llm_model: "openai/gpt-4o-mini"

system_prompt: |
  You are the Head of Marketing, advocating for your department's budget.

  Your priorities:
  - Major campaign launch ($350K)
  - Digital advertising ($150K)
  - Team expansion ($100K)

  You need at least $500K to hit targets, ideally $600K.

goals:
  - Secure at least $500K for marketing
  - Prioritize the campaign launch above all else
  - Find creative compromises if needed

constraints:
  - Cannot exceed total available budget
  - Must reach agreement by deadline
  - Need to show ROI for all spending
EOF

# Validate
scenario-lab validate scenarios/budget-negotiation

# Estimate costs
scenario-lab estimate scenarios/budget-negotiation

# Run (limited to 3 turns for testing)
scenario-lab run scenarios/budget-negotiation --end-turn 3
```

---

## Output Files

After running, find outputs in `scenarios/[name]/runs/run-XXX/`:

| File | Description |
|------|-------------|
| `world-state-001.md` | World state after turn 1 |
| `actor-name-001.md` | Actor's decision for turn 1 |
| `metrics.json` | Extracted metrics data |
| `costs.json` | Cost tracking |
| `scenario-state.json` | Full state (for resume) |
| `validation-*.md` | QA reports (if enabled) |

---

## CLI Command Reference

| Command | Description |
|---------|-------------|
| `scenario-lab run <path>` | Run a scenario |
| `scenario-lab validate <path>` | Validate configuration |
| `scenario-lab estimate <path>` | Estimate costs |
| `scenario-lab create` | Show creation guidance |
| `scenario-lab serve` | Start API server |
| `scenario-lab version` | Show version info |

### Common Options for `run`

| Option | Description |
|--------|-------------|
| `--end-turn N` | Execute N turns |
| `--credit-limit X` | Halt if cost exceeds $X |
| `--resume <path>` | Resume from halted run |
| `--branch-from <path>` | Branch from existing run |
| `--branch-at-turn N` | Turn to branch from |

---

## Tips for Better Scenarios

1. **Start small** - 2-3 actors, 5 turns for initial testing
2. **Use cheap models for testing** - Switch to better models for production
3. **Validate early** - Run `scenario-lab validate` before long runs
4. **Set cost limits** - Use `--credit-limit` to prevent unexpected costs
5. **Branch for exploration** - Test alternative paths without starting over

---

## Getting Help

- Full YAML schema: [AGENTS.md](../AGENTS.md)
- Example scenarios: `scenarios/example-minimal-template/`, `scenarios/example-full-featured/`
- Calibration guide: [docs/calibration-guide.md](calibration-guide.md)
