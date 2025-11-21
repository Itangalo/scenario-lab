# AGENTS.md - Instructions for AI Assistants

This file provides instructions for AI coding assistants (Claude Code, Codex, Cursor, etc.) to help users create and configure Scenario Lab simulations.

## What is Scenario Lab?

Scenario Lab is a framework for AI-automated scenario exercises exploring complex policy and strategic questions, particularly around AI governance. The system enables multi-actor simulations where AI agents interact in dynamic environments.

**Primary use case**: Exploring AI policy questions through simulation—regulatory effectiveness, governance structures, international coordination, corporate AI strategy, safety interventions.

## Your Role as an AI Assistant

When a user wants to create a scenario, you should:

1. **Understand their research question** - What are they trying to explore?
2. **Identify relevant actors** - Who are the key decision-makers?
3. **Design the scenario structure** - Timeline, turns, world state
4. **Configure metrics** - What outcomes should be tracked?
5. **Set up validation** - Ensure simulation quality
6. **Generate all configuration files** - Valid YAML that works immediately

## Scenario Directory Structure

Every scenario follows this structure:

```
scenarios/[scenario-name]/
├── scenario.yaml              # Main configuration (REQUIRED)
├── actors/                    # Actor definitions (REQUIRED)
│   ├── actor-one.yaml
│   ├── actor-two.yaml
│   └── ...
├── metrics.yaml               # Metrics to track (optional)
├── validation-rules.yaml      # QA configuration (optional)
├── exogenous-events.yaml      # Background events (optional)
└── background/                # Reference documents (optional)
    ├── context.md
    └── data.md
```

---

## File Schemas and Examples

### 1. scenario.yaml (REQUIRED)

The main scenario configuration file.

**Required fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Scenario display name |
| `initial_world_state` | string | Starting situation (markdown) |
| `turn_duration` | string | Duration per turn (e.g., "1 week", "1 month") |
| `turns` | integer | Number of simulation turns |
| `actors` | list | Actor short names (must match filenames in actors/) |

**Optional fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | string | null | Brief scenario summary |
| `system_prompt` | string | null | System prompt for all actors |
| `world_state_model` | string | "openai/gpt-4o-mini" | LLM for world synthesis |
| `context_window_size` | integer | 3 | Previous turns in context |

**Example:**

```yaml
name: "US-China AI Investment Crisis"
description: |
  Simulation of US-China dynamics following a major AI investment collapse,
  exploring regulatory responses, diplomatic negotiations, and market effects.

system_prompt: |
  You are participating in a geopolitical simulation about AI investment dynamics.
  Act realistically as your assigned role, considering political constraints,
  economic pressures, and strategic interests.

  Make decisions that reflect real-world decision-making patterns:
  - Consider domestic political pressures
  - Account for information asymmetry
  - Balance short-term reactions with long-term strategy

initial_world_state: |
  # Starting Situation (January 2026)

  A major US AI company has announced significant financial difficulties,
  triggering concerns about the broader AI investment landscape.

  **Economic Context:**
  - US AI sector has received $200B+ in investment over past 3 years
  - Several high-profile AI startups have missed revenue targets
  - Stock market showing signs of AI sector correction

  **Political Climate:**
  - US election in 11 months
  - Growing bipartisan concern about AI competition with China
  - China accelerating domestic AI development programs

  **Key Uncertainties:**
  - Extent of contagion to other AI companies
  - Policy responses from both governments
  - Impact on AI development timelines

turns: 12
turn_duration: "1 month"
world_state_model: "anthropic/claude-3-5-sonnet-20241022"

actors:
  - us-president
  - us-treasury-secretary
  - china-state-council
  - fed-chairman
  - ai-company-ceo
```

**Validation rules:**
- `turn_duration` must match pattern: `^\d+\s+(second|minute|hour|day|week|month|year)s?$`
- Actor names must be lowercase with hyphens (e.g., "us-president", not "US President")
- At least one actor required

---

### 2. Actor YAML Files (REQUIRED)

Each actor needs a separate file in the `actors/` directory. Filename must match the actor's `short_name`.

**Required fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Actor display name |
| `short_name` | string | Identifier (lowercase-with-hyphens) |

**Recommended fields:**

| Field | Type | Description |
|-------|------|-------------|
| `llm_model` | string | LLM model (default: "openai/gpt-4o-mini") |
| `system_prompt` | string | Actor identity and behavioral parameters |
| `goals` | list | Actor's objectives |
| `constraints` | list | Limitations on actions |
| `expertise` | string/dict | Domain knowledge levels |
| `decision_making_style` | string | How actor approaches decisions |

**Optional fields:**

| Field | Type | Description |
|-------|------|-------------|
| `private_information` | string | Information only this actor knows |
| `information_access` | object | What information actor can see |

**Example (actors/us-president.yaml):**

```yaml
name: "US President"
short_name: "us-president"

llm_model: "anthropic/claude-3-5-sonnet-20241022"

system_prompt: |
  You are the President of the United States, facing a potential AI investment crisis
  11 months before your re-election campaign.

  Your administration has championed American AI leadership. A major collapse would:
  - Undermine your economic narrative
  - Strengthen opponents' criticism
  - Potentially benefit Chinese AI ambitions

  You must balance:
  - Economic stability vs. market principles
  - Domestic politics vs. international competition
  - Short-term crisis response vs. long-term policy

goals:
  - Maintain economic stability and prevent broader market contagion
  - Preserve American AI leadership position
  - Manage political fallout ahead of election
  - Avoid actions that benefit Chinese AI development

constraints:
  - Must work through Congress for major fiscal interventions
  - Cannot appear to be "bailing out" wealthy tech investors
  - Must maintain alliance relationships
  - Limited direct control over Federal Reserve policy

expertise: |
  High expertise in political strategy and communication.
  Moderate understanding of economic policy (relies on advisors).
  Limited technical understanding of AI systems.
  Strong network of advisors and cabinet members.

decision_making_style: |
  You make decisions through political calculation combined with expert consultation:
  1. Assess political implications and public perception
  2. Consult cabinet members and key advisors
  3. Consider Congressional and international reactions
  4. Choose options that balance effectiveness with political viability

  You prefer measured responses over dramatic actions unless crisis demands it.
  You prioritize communication and framing alongside substantive policy.

private_information: |
  - Internal polling shows vulnerability on economic issues
  - Intelligence briefings on Chinese AI acceleration efforts
  - Back-channel communications with key Congressional leaders
```

**Model selection guidance:**

| Model | Cost | Best for |
|-------|------|----------|
| `openai/gpt-4o-mini` | Low ($0.15/M in) | Testing, supporting actors |
| `openai/gpt-4o` | Medium ($2.50/M in) | Production scenarios |
| `anthropic/claude-3-5-sonnet-20241022` | Medium ($3/M in) | Complex reasoning |
| `anthropic/claude-3-opus-20240229` | High ($15/M in) | Critical actors |

---

### 3. metrics.yaml (Optional but Recommended)

Define quantitative and qualitative metrics to track throughout the scenario.

**Three extraction methods:**

1. **pattern** - Regex extraction from text
2. **keyword** - Count keyword occurrences
3. **llm** - AI-powered extraction for complex concepts

**Metric types:**
- `continuous` - Numeric values with range
- `categorical` - Predefined categories
- `boolean` - True/false

**Example:**

```yaml
metrics:
  # Pattern-based: extract numbers from text
  - name: market_decline_percent
    description: "Reported market decline percentage"
    type: continuous
    range: [0, 100]
    unit: "percent"
    extraction:
      type: pattern
      pattern: '(\d+(?:\.\d+)?)\s*%\s*(?:decline|drop|fall)'
    actor_specific: false

  # Keyword-based: count mentions
  - name: crisis_severity_mentions
    description: "Frequency of crisis-related language"
    type: continuous
    range: [0, 100]
    unit: "mentions"
    extraction:
      type: keyword
      keywords:
        - "crisis"
        - "collapse"
        - "emergency"
        - "bailout"
        - "contagion"
    actor_specific: false

  # LLM-based: complex assessment
  - name: cooperation_level
    description: "Level of US-China cooperation (0-10 scale)"
    type: continuous
    range: [0, 10]
    unit: "cooperation"
    extraction:
      type: llm
      prompt: |
        Based on the world state, rate the level of US-China cooperation
        on economic/AI issues from 0-10:
        - 0 = Active confrontation, trade war escalation
        - 5 = Neutral, limited engagement
        - 10 = Active cooperation, joint initiatives

        Respond with ONLY a number between 0-10.
    actor_specific: false

  - name: domestic_political_stability
    description: "US domestic political stability regarding AI policy"
    type: continuous
    range: [0, 10]
    extraction:
      type: llm
      prompt: |
        Rate US domestic political stability regarding AI investment policy (0-10):
        - 0 = Major political crisis, bipartisan conflict
        - 5 = Normal political disagreements
        - 10 = Strong bipartisan consensus

        Respond with ONLY a number.
    actor_specific: false

export_format: json
auto_export: true
```

---

### 4. validation-rules.yaml (Optional but Recommended)

Automated consistency checking using lightweight LLM models.

**Available checks:**
- `actor_decision_consistency` - Do decisions match actor goals/constraints?
- `world_state_coherence` - Are world updates logical?
- `information_access_consistency` - Do actors only use available information?
- `goal_progress_tracking` - Are actors making progress on goals?

**Example:**

```yaml
validation_model: "openai/gpt-4o-mini"

checks:
  actor_decision_consistency:
    enabled: true
    severity: medium
    description: "Validates actor decisions align with stated goals and constraints"

  world_state_coherence:
    enabled: true
    severity: high
    description: "Validates world state updates logically follow from actions"

  information_access_consistency:
    enabled: true
    severity: medium
    description: "Validates actors only reference information they have access to"

  goal_progress_tracking:
    enabled: true
    severity: low
    description: "Tracks whether actors are making progress toward goals"

run_after_each_turn: true
generate_turn_reports: true
generate_summary: true
halt_on_critical: false
report_format: markdown
```

---

### 5. exogenous-events.yaml (Optional)

Background events that occur independently of actor decisions.

**Event types:**

1. **trend** - Gradual changes over time
2. **random** - Probabilistic events
3. **conditional** - Triggered by conditions
4. **scheduled** - Events at specific turns

**Example:**

```yaml
events:
  # Trend: gradual background change
  - type: trend
    name: "AI Investment Sentiment"
    description: "Overall market sentiment toward AI investments"
    initial_value: 60
    trend_direction: -5  # Declining 5 points per turn initially
    volatility: 10

  # Random: probabilistic events
  - type: random
    name: "Major Tech Earnings Report"
    description: "Quarterly earnings from major AI companies"
    probability: 0.25
    turn_range: [1, 12]
    outcomes:
      - "Beats expectations, market rallies"
      - "Meets expectations, stability"
      - "Misses expectations, further decline"
    outcome_weights: [0.2, 0.3, 0.5]

  # Conditional: triggered by world state
  - type: conditional
    name: "Congressional Hearing"
    description: "Congress convenes emergency hearing on AI investment crisis"
    condition: "market decline exceeds 30% OR public pressure increases significantly"
    effect: |
      Congressional leaders announce emergency hearings on AI investment practices.
      Both parties seek political advantage from the crisis.

  # Scheduled: specific timing
  - type: scheduled
    name: "Federal Reserve Meeting"
    description: "Scheduled FOMC meeting"
    turn: 3
    effect: |
      Federal Reserve announces interest rate decision and economic outlook.
      Markets await signals about potential intervention.
```

---

## Workflow for Creating Scenarios

### Step 1: Understand the Research Question

Ask the user clarifying questions:
- What policy question are you exploring?
- What decisions or dynamics are you interested in?
- What actors are most relevant?
- What timeframe makes sense?
- What outcomes would you want to measure?

### Step 2: Research Actors

For each actor, research:
- **Real-world counterparts** - Who makes these decisions?
- **Goals and motivations** - What do they want?
- **Constraints** - What limits their actions?
- **Expertise** - What do they know/not know?
- **Decision patterns** - How do they typically decide?

**Sources for actor research:**
- Official statements and policies
- News coverage and analysis
- Academic research on decision-making
- Historical precedents

### Step 3: Design the Scenario

Consider:
- **Turn duration** - Match to decision-making pace (crisis = days/weeks, policy = months)
- **Number of turns** - Enough for dynamics to play out (typically 5-20)
- **Initial state** - Set up tensions and uncertainties
- **World state model** - Higher quality for complex scenarios

### Step 4: Configure Metrics

Choose metrics that capture:
- **Outcome variables** - What the user wants to measure
- **Process variables** - How decisions unfold
- **Risk indicators** - Warning signs to track

### Step 5: Generate Files

Create all YAML files with proper structure and validation-compliant format.

---

## Actor Design Guidelines

### Creating Realistic Actors

1. **Distinct perspectives** - Each actor should have different goals and constraints
2. **Information asymmetry** - Actors know different things
3. **Realistic expertise** - No actor knows everything
4. **Political/institutional constraints** - Real decisions have limits
5. **Decision-making patterns** - How does this type of actor typically decide?

### Common Actor Archetypes

**Government actors:**
- Goals: Policy objectives, political survival, institutional interests
- Constraints: Legal authority, political capital, bureaucratic processes
- Style: Often cautious, precedent-following, coalition-building

**Corporate actors:**
- Goals: Profit, market position, regulatory environment
- Constraints: Shareholders, regulations, reputation
- Style: Strategic, competitive, sometimes short-term focused

**Civil society actors:**
- Goals: Values-based outcomes, constituency interests
- Constraints: Resources, access, coalition partners
- Style: Advocacy-focused, principled, public-facing

**International actors:**
- Goals: National interest, domestic politics, international standing
- Constraints: Sovereignty, treaties, domestic approval
- Style: Strategic, often slow-moving, face-saving important

### Avoiding Common Mistakes

- **Too powerful actors** - Give meaningful constraints
- **Too cooperative actors** - Build in conflicting interests
- **Too rational actors** - Include biases and limited information
- **Too uniform actors** - Vary expertise and decision styles
- **Too static actors** - Allow for learning and adaptation

---

## Running and Validating Scenarios

### Running a Scenario

```bash
# Basic run
scenario-lab run scenarios/your-scenario

# Limited turns (for testing)
scenario-lab run scenarios/your-scenario --end-turn 3

# With cost limit
scenario-lab run scenarios/your-scenario --credit-limit 2.00

# Dry run (cost estimation only)
scenario-lab run scenarios/your-scenario --dry-run
```

### Validating Configuration

Before running, verify:

1. **All actor files exist** - Each name in `actors:` list needs a matching `.yaml` file
2. **Actor names are lowercase-with-hyphens** - e.g., "us-president" not "US President"
3. **Turn duration format is correct** - e.g., "1 week" not "1 wk" or "weekly"
4. **Metrics reference valid extraction types** - "pattern", "keyword", "llm", or "manual"
5. **Model names are valid** - Use "provider/model" format

### Common Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Actor file not found" | Missing YAML file | Create actors/[name].yaml |
| "Invalid turn_duration" | Wrong format | Use "N unit" format |
| "Invalid actor name" | Uppercase or spaces | Use lowercase-with-hyphens |
| "'range' required" | Missing for continuous metric | Add range: [min, max] |
| "'prompt' required" | Missing for LLM extraction | Add prompt field |

---

## Example: Complete Scenario Generation

**User request:** "I want to simulate how the US and China would respond to a major AI investment collapse in the US."

**Your response should:**

1. Ask clarifying questions about scope, actors, timeframe
2. Propose a scenario structure
3. Generate all required files:
   - scenario.yaml
   - actors/us-president.yaml
   - actors/us-treasury-secretary.yaml
   - actors/china-state-council.yaml
   - actors/fed-chairman.yaml
   - actors/ai-company-ceo.yaml
   - metrics.yaml
   - validation-rules.yaml

4. Explain how to run and iterate on the scenario

---

## Reference: Available LLM Models

| Provider/Model | Cost (input/output per 1M tokens) | Notes |
|----------------|-----------------------------------|-------|
| openai/gpt-4o-mini | $0.15 / $0.60 | Best for testing, validation |
| openai/gpt-4o | $2.50 / $10.00 | Good balance |
| anthropic/claude-3-5-sonnet-20241022 | $3.00 / $15.00 | Strong reasoning |
| anthropic/claude-3-opus-20240229 | $15.00 / $75.00 | Highest quality |
| anthropic/claude-3-haiku-20240307 | $0.25 / $1.25 | Fast, cheap |

---

## Tips for AI Assistants

1. **Always generate valid YAML** - Test mentally against the schema rules
2. **Use realistic actor profiles** - Research real-world counterparts
3. **Include conflicting interests** - This creates interesting dynamics
4. **Start with fewer actors** - 2-4 actors for initial scenarios
5. **Match turn duration to decision pace** - Crises need short turns
6. **Include private information** - Information asymmetry is key
7. **Design measurable metrics** - Choose extraction methods that will work
8. **Enable validation** - It catches issues early

---

## Files to Reference

For complete examples, see:
- `scenarios/example-full-featured/` - Comprehensive 4-actor scenario
- `scenarios/example-minimal-template/` - Minimal starting point
- `scenarios/ai-2027/` - Complex 7-actor calibration scenario
- `docs/scenario-creation-guide.md` - Detailed human-readable guide
- `scenario_lab/schemas/` - Pydantic validation schemas
