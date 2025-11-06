# Scenario Creation Guide

This guide explains how to create new scenarios for Scenario Lab using the interactive scenario creation wizard.

## Overview

The scenario creation wizard (`create_scenario.py`) is an interactive CLI tool that guides you through creating a complete scenario configuration, including:

- Scenario definition (name, description, parameters)
- Actor definitions (multiple actors with goals, constraints, expertise)
- Metrics configuration (optional)
- Validation rules (optional)

## Quick Start

```bash
python src/create_scenario.py
```

The wizard will guide you through 9 steps to create a complete scenario.

## Step-by-Step Guide

### Step 1: Basic Information

Provide fundamental information about your scenario:

- **Scenario name**: Full descriptive name (e.g., "AI Regulatory Negotiation 2025")
- **Description**: Brief description of what the scenario explores

**Example:**
```
Scenario name: Climate Policy Summit
Brief description: International negotiation on climate policy commitments
```

### Step 2: System Prompt

The system prompt sets the overall context for all actors in the scenario. It should describe:

- The overall simulation context
- General behavioral expectations
- Decision-making principles

**Default template:**
```
You are participating in a multi-turn scenario simulation focused on AI policy and governance.
Your goal is to act realistically as your assigned role, making strategic decisions that align
with your character's goals, constraints, and decision-making style.

Be specific and concrete in your actions. Consider both short-term tactics and long-term strategy.
Your decisions should reflect realistic policy negotiation dynamics, including compromise,
strategic positioning, and consideration of stakeholder interests.
```

You can use the default or customize it for your specific scenario type.

### Step 3: Initial World State

Describe the starting situation for the scenario:

- Current year/timeframe
- Key context and background
- Issues on the table
- Relevant constraints or conditions

**Example:**
```
The year is 2025. An international climate summit is convening to negotiate
binding emissions commitments. Three major economies must agree on:

- Emission reduction targets for 2030
- Financial support for developing nations
- Technology transfer mechanisms
- Verification and enforcement procedures

Current positions are far apart, with each nation prioritizing different concerns.
```

**Tips:**
- Be specific about the situation
- Define clear issues to be resolved
- Set realistic constraints
- Include relevant background information

### Step 4: Scenario Parameters

Configure basic scenario mechanics:

- **Number of turns**: How many rounds of interaction (typical: 3-10)
- **Turn duration**: Timeframe of each turn (e.g., "1 week", "1 month", "1 quarter")

**Recommendations:**
- **Quick scenarios**: 3-5 turns, 1 week per turn
- **Medium scenarios**: 5-10 turns, 1 month per turn
- **Long scenarios**: 10-20 turns, 1 quarter per turn

### Step 5: World State Model

Select the LLM model that will synthesize world state updates from actor actions.

**Recommended models:**

1. **openai/gpt-4o-mini** - Fast, cheap ($0.15/M in, $0.60/M out)
   - Best for: Testing, frequent iterations, cost-sensitive batch runs
   - Quality: Good for most scenarios

2. **openai/gpt-4o** - Balanced ($2.50/M in, $10/M out)
   - Best for: Production scenarios requiring good quality
   - Quality: Excellent synthesis and coherence

3. **anthropic/claude-3.5-sonnet** - High quality ($3/M in, $15/M out)
   - Best for: Complex scenarios requiring nuanced synthesis
   - Quality: Superior narrative coherence

**Cost consideration:** World state synthesis is called once per turn, so even expensive models remain affordable.

### Step 6: Create Actors

Create at least 2 actors for your scenario. For each actor, you'll define:

#### 6.1 Basic Information

- **Name**: Full actor name (e.g., "National AI Safety Regulator")
- **Short name**: Filename-friendly identifier (e.g., "regulator", "tech-company")

#### 6.2 LLM Model

Select the model for this actor's decision-making.

**Model selection tips:**
- **Testing**: Use cheaper models (gpt-4o-mini, claude-3-haiku)
- **Production**: Use higher-quality models for critical actors
- **Mixed strategies**: Use premium models for key actors, cheaper models for supporting roles

#### 6.3 System Prompt

Define the actor's identity, mandate, and behavioral parameters.

**Template structure:**
```
You are [ACTOR NAME]. Your mandate is to [DESCRIBE MANDATE].

Your goals are to:
- [GOAL 1]
- [GOAL 2]
- [GOAL 3]

Your constraints:
- [CONSTRAINT 1]
- [CONSTRAINT 2]
- [CONSTRAINT 3]

Your expertise levels:
- [DOMAIN]: [expert/intermediate/novice]
- [DOMAIN]: [expert/intermediate/novice]

Your decision-making style:
[DESCRIBE HOW THIS ACTOR MAKES DECISIONS]
```

**Tips:**
- Be specific about the actor's role and mandate
- Define clear, measurable goals
- Include realistic constraints (political, resource, technical)
- Specify expertise domains relevant to the scenario
- Describe decision-making approach (cautious/bold, pragmatic/idealistic, etc.)

#### 6.4 Description

Brief description of the actor (can be derived from system prompt).

#### 6.5 Goals

List specific objectives this actor pursues. These should be:

- **Concrete**: Specific outcomes the actor wants
- **Measurable**: Possible to assess if achieved
- **Potentially conflicting**: Creating interesting dynamics

**Example:**
```
- Ensure robust safety standards for AI systems
- Maintain public trust in regulation
- Balance safety with innovation concerns
- Create enforceable and practical regulations
```

#### 6.6 Constraints

Define limitations on the actor's actions:

- **Political constraints**: Must maintain support from key stakeholders
- **Resource constraints**: Limited budget, staff, authority
- **Technical constraints**: Must be feasible with current technology
- **Legal constraints**: Must operate within existing law

**Example:**
```
- Must consider industry feedback (political pressure exists)
- Regulations must be technically feasible
- Need to maintain international competitiveness
- Limited enforcement resources
```

#### 6.7 Expertise

Define the actor's knowledge and capabilities in relevant domains.

**Format:** `domain=level` (levels: expert, intermediate, novice)

**Example:**
```
ai_safety=expert
policy=expert
technology=intermediate
economics=intermediate
```

#### 6.8 Decision Style

Describe how this actor approaches decision-making:

- **Risk orientation**: Cautious vs. bold
- **Value priorities**: Safety vs. innovation, cooperation vs. competition
- **Decision approach**: Data-driven vs. intuitive, principled vs. pragmatic
- **Interpersonal style**: Collaborative vs. adversarial

**Example:**
```
You are cautious but pragmatic. You prioritize safety but understand the need for
workable compromises. You seek evidence-based policy and are willing to adjust
proposals based on legitimate concerns.
```

### Step 7: Metrics (Optional)

Define quantitative and qualitative metrics to track throughout the scenario.

For each metric, specify:

- **Description**: What this metric measures
- **Type**: integer, float, string, or boolean
- **Unit**: (if numeric) e.g., "hours", "USD", "FLOPS"
- **Extraction method**:
  - **Regex**: Automatic pattern matching in generated text
  - **Manual**: Set by analyst after reviewing outputs
- **Pattern**: (if regex) Regular expression to extract value
- **Actor-specific**: Whether this applies to one specific actor

**Examples:**

1. **Numeric metric with regex extraction:**
```yaml
incident_reporting_hours:
  description: "Required timeline for incident reporting"
  type: "integer"
  unit: "hours"
  extraction_method: "regex"
  pattern: '(\d+)\s*[-]?hour'
  actor_specific: false
```

2. **Boolean metric with regex extraction:**
```yaml
working_group_proposed:
  description: "Whether a joint working group was proposed"
  type: "boolean"
  extraction_method: "regex"
  pattern: 'working\s+group'
  actor_specific: false
```

3. **Manual metric (analyst assessment):**
```yaml
compromise_level:
  description: "Degree of compromise reached (1-10 scale)"
  type: "integer"
  extraction_method: "manual"
  actor_specific: false
```

**Tips:**
- Start with 3-5 key metrics
- Use regex for objective, quantifiable values
- Use manual extraction for subjective assessments
- Balance automatic and manual metrics

### Step 8: Validation Rules (Optional)

Enable automated consistency checking with lightweight LLM models.

**Available checks:**

1. **Actor decision consistency**: Validates decisions align with goals, constraints, and expertise
2. **World state coherence**: Validates world state updates logically follow from actions
3. **Information access consistency**: Validates actors only use information they should have

**Recommended settings:**
- **Validation model**: `openai/gpt-4o-mini` (cheap, effective)
- **Enable all checks**: Yes (unless you have specific reasons to disable)
- **Run after each turn**: Yes

**Benefits:**
- Catch logical inconsistencies automatically
- Ensure simulation quality
- Low cost (lightweight model, ~$0.01 per scenario)

**Cost:**
With gpt-4o-mini, validation typically costs $0.005-0.02 per turn, making it very affordable even for large batch runs.

### Step 9: Save Scenario

Review and save your scenario:

- **Output directory**: Default `scenarios/[scenario-name]`
- **Preview**: Shows summary of configuration
- **Confirmation**: Final chance to review before saving

## Directory Structure

After creation, your scenario will have this structure:

```
scenarios/your-scenario-name/
├── scenario.yaml           # Main scenario configuration
├── actors/
│   ├── actor-one.yaml     # First actor configuration
│   └── actor-two.yaml     # Second actor configuration
├── metrics.yaml           # Metrics definitions (if created)
└── validation-rules.yaml  # Validation configuration (if enabled)
```

## Editing Scenarios

After creation, you can edit scenario files directly:

- **scenario.yaml**: Adjust turns, world state, system prompt
- **actors/*.yaml**: Refine actor goals, constraints, prompts
- **metrics.yaml**: Add/modify/remove metrics
- **validation-rules.yaml**: Adjust validation settings

All files are human-readable YAML format.

## Running Your Scenario

Once created, run your scenario with:

```bash
# Single run
python src/run_scenario.py scenarios/your-scenario-name

# With budget limit
python src/run_scenario.py scenarios/your-scenario-name --credit-limit 1.00

# Limited turns (useful for testing)
python src/run_scenario.py scenarios/your-scenario-name --max-turns 2

# Resume a halted run
python src/run_scenario.py --resume output/your-scenario-name/run-001
```

## Creating Batch Experiments

After creating a scenario, create batch experiments to test variations:

```bash
python src/create_batch_config.py
```

This lets you:
- Test different actor models systematically
- Run multiple repetitions for statistical significance
- Compare different parameter configurations

See [Batch Execution Guide](batch-execution-guide.md) for details.

## Example Scenarios

### Example 1: Policy Negotiation

**Scenario type:** Two-party negotiation
**Actors:** 2 (regulator + company)
**Turns:** 3-5
**Best for:** Testing regulatory dynamics, compliance strategies

**Key features:**
- Clear opposing interests
- Defined negotiation space
- Measurable outcomes (regulatory parameters)

### Example 2: Multi-Stakeholder Summit

**Scenario type:** Multi-party coordination
**Actors:** 3-5 (government agencies, companies, NGOs)
**Turns:** 5-10
**Best for:** Coalition dynamics, compromise patterns

**Key features:**
- Multiple competing priorities
- Coalition formation opportunities
- Complex outcome space

### Example 3: Crisis Response

**Scenario type:** Rapid decision-making under uncertainty
**Actors:** 3-4 (emergency managers, technical experts, officials)
**Turns:** 5-7 (short duration, e.g., "6 hours")
**Best for:** Testing decision-making under pressure

**Key features:**
- Time pressure (short turn duration)
- Information asymmetry
- Cascading consequences

## Best Practices

### Actor Design

1. **Distinct roles**: Ensure actors have different goals and constraints
2. **Realistic constraints**: Don't make actors too powerful or too limited
3. **Clear expertise**: Define what each actor knows and doesn't know
4. **Believable motivations**: Give actors realistic reasons for their positions

### Scenario Design

1. **Clear stakes**: Define what success/failure looks like
2. **Appropriate complexity**: Start simple, add complexity as needed
3. **Measurable outcomes**: Define metrics that capture key dynamics
4. **Realistic timeframes**: Match turn duration to decision type

### Model Selection

1. **Start cheap**: Test with inexpensive models (gpt-4o-mini)
2. **Upgrade strategically**: Use premium models for production runs
3. **Mixed strategies**: Premium for key actors, cheap for supporting roles
4. **Validate costs**: Use `--dry-run` in batch mode to estimate costs

### Iteration

1. **Test early**: Run 1-2 turns before committing to full scenario
2. **Review outputs**: Check if actors behave as intended
3. **Refine prompts**: Adjust based on actual behavior
4. **Use validation**: Enable QA checks to catch issues automatically

## Troubleshooting

### Actors not behaving as expected

**Solution:**
- Make goals more explicit in system prompt
- Add more specific constraints
- Clarify decision-making style
- Use examples in actor prompt (not yet implemented, but planned)

### World state updates too generic

**Solution:**
- Use a more capable world state model (gpt-4o or better)
- Provide more detailed initial world state
- Check that actor actions are specific enough

### Metrics not extracting correctly

**Solution:**
- Test regex patterns on sample text first
- Use simpler patterns for regex extraction
- Switch to manual extraction for complex metrics
- Add more examples in metrics documentation

### Validation finding false positives

**Solution:**
- Review validation prompts in validation-rules.yaml
- Adjust severity thresholds
- Disable specific checks if not relevant
- Use manual review for edge cases

## Advanced Topics

### Custom Validation Rules

You can customize validation by editing `validation-rules.yaml`:

- Modify prompt templates for checks
- Add custom validation checks
- Adjust severity thresholds
- Control reporting frequency

### Background Information

Add background context by creating:
```
scenarios/your-scenario/background/
├── historical-data.md
├── reference-docs.md
└── technical-specs.md
```

Reference these in actor system prompts: "See background/historical-data.md for context"

### Exogenous Events

Define black swan events in `black-swans.yaml` (see documentation for details).

## Getting Help

- **Documentation**: See `docs/` directory for detailed guides
- **Examples**: Review `scenarios/test-regulation-negotiation/` for a complete example
- **Issues**: Report problems at the project repository

## Next Steps

After creating your scenario:

1. **Test run**: Run 1-2 turns to verify behavior
2. **Refine**: Adjust based on initial outputs
3. **Full run**: Execute complete scenario
4. **Batch experiments**: Use batch runner for systematic exploration
5. **Analysis**: Review markdown outputs and metrics data

See [README.md](../README.md) for comprehensive framework documentation.
