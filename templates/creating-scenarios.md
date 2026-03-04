# Creating Scenarios for Scenario Lab V4

This guide helps you create scenarios for Scenario Lab V4 from background material and descriptions. It includes design principles, file structure, formatting specifications, and instructions for customizing system prompts.

## Design Principles

Scenario Lab V4 follows a **pure LLM architecture**:

1. **LLMs handle complexity** - Trust the LLM for narrative, metrics interpretation, and rule application
2. **Python is orchestration** - Minimal code that loads data, calls APIs, saves files
3. **No communication phases** - Simple turn loop: Events → Actors → Metric Rules → Metrics
4. **One simple turn loop** - Each turn represents a time period (e.g., 6 months)
5. **Start small, scale up** - Begin with 2 actors, 3-4 metrics, 3 turns. Add complexity when it works.

## File Structure

A complete scenario consists of these files:

```
scenario-name/
├── scenario.yaml              # Configuration
├── metrics.md                 # Metric definitions
├── events.md                  # External events
├── metric-rules.md            # Initial quantitative rules
├── background/
│   ├── context.md             # World background and initial state
│   └── actors/
│       ├── actor1.md          # Actor descriptions
│       └── actor2.md
└── system-prompts/            # Optional: scenario-specific prompts
    ├── events.md
    ├── actor.md
    ├── metric-rules.md
    └── metrics-update.md
```

## Configuration File (scenario.yaml)

The main configuration file defines the scenario parameters.

**Required fields:**
```yaml
name: "Scenario Name"
description: "Brief description of what the scenario explores"
start_date: "2026-01"           # Format: YYYY-MM
time_scale: "6 months per turn"
max_turns: 10
actors:
  - actor1_id
  - actor2_id

output_language: "English" # Optional: The desired language for LLM-generated text responses (e.g., "Swedish", "Spanish").
                          # If not specified, LLM will respond in the language of the prompt.

llm:
  # Option 1: Single model for all tasks
  model: "google/gemini-3-flash-preview"
  temperature: 0.7
  max_tokens: 2000

  # Option 2: Per-task models (more control)
  events: "x-ai/grok-4.1-fast"
  actors: "google/gemini-3-flash-preview"
  rules: "google/gemini-3-flash-preview"
  metrics: "google/gemini-3-flash-preview"
  temperature: 0.7
  max_tokens: 2000
```

**Actor IDs** should be:
- Lowercase with underscores (e.g., `government`, `labor_unions`)
- Descriptive and concise
- Match the filenames in `background/actors/` (without .md extension)

## Metrics (metrics.md)

Metrics are quantitative values that track the world state. Keep them simple and measurable.

**Format:**
```markdown
## metric_id

**Description:** What this metric represents
**ID:** metric_id
**Min:** 0
**Max:** 100
**Unit:** percent
**Start value:** 50
**Reference points:** (optional)
- 0: Description of this value
- 50: Description of this value
- 100: Description of this value
```

**Guidelines:**
- Use 3-6 metrics (more makes the simulation harder to manage)
- Choose clear, measurable metrics (avoid vague concepts)
- Include reference points to help LLMs interpret values
- Metrics can represent capabilities, adoption rates, sentiment, economic indicators, etc.

**Example:**
```markdown
## ai_capability

**Description:** Hours of work AI can autonomously handle (out of typical 40-hour workweek)
**ID:** ai_capability
**Min:** 0
**Max:** 40
**Unit:** hours per week
**Start value:** 8
**Reference points:**
- 0: AI cannot perform any work autonomously
- 8: AI handles basic administrative tasks
- 20: AI handles half of typical knowledge work
- 40: AI can handle all work in typical office job
```

## Events (events.md)

External events that can occur based on conditions and probabilities.

**Format:**
```markdown
## Event Name

**ID:** event_id
**Condition:** Natural language description of when this can occur
**Probability:** Fixed value (e.g., "10 percent per turn") or formula (e.g., "unemployment / 100")
**Can repeat:** Yes/No
**Description:** What happens when this event occurs
```

**Guidelines:**
- Events represent exogenous shocks or developments
- Conditions should reference specific metrics (e.g., "unemployment > 15")
- Probabilities can be fixed or dynamic formulas
- Use "Can repeat: No" for one-time events
- Include 5-10 events (fewer for simple scenarios)

**Example:**
```markdown
## Major AI Breakthrough

**ID:** major_breakthrough
**Condition:** ai_capability > 20 and turn > 3
**Probability:** 15 percent per turn
**Can repeat:** No
**Description:** A research team achieves a major breakthrough in AI capabilities, accelerating development significantly.
```

## Metric Rules (metric-rules.md)

Initial quantitative rules for how metrics change over time or based on other metrics.

**Format:**
```markdown
1. Description of first rule (e.g., "ai_capability increases by 2 per turn")
2. Description of second rule (e.g., "When unemployment > 15, public_sentiment decreases by 1 per turn")
3. ...
```

**Guidelines:**
- Start with 5-10 rules
- Rules describe quantitative relationships between metrics
- Can reference time ("per turn") or other metrics ("when X > Y")
- LLM will update these during simulation based on what happens
- Keep rules clear and specific

**Example:**
```markdown
1. ai_capability increases by 1-2 hours per turn due to ongoing research
2. When ai_capability > 15, unemployment starts increasing by 0.5-1 percentage points per turn
3. When unemployment > 12, public_sentiment_to_ai decreases by 1-2 points per turn
4. When public_sentiment_to_ai < 40, political_support_innovation decreases by 1 point per turn
5. Strong government support (political_support_innovation > 70) increases ai_adoption_sweden by 2-3 percentage points per turn
```

## Background Context (background/context.md)

Describes the world at the start of the simulation.

**Structure:**
```markdown
# Scenario Name

## Overview
Brief description of the scenario and what it explores.

## Initial Situation
Detailed description of the world state at the start.

## Key Factors
Important contextual factors that will influence the simulation.
```

**Guidelines:**
- Provide enough context for LLMs to make informed decisions
- Include relevant historical background
- Describe current state of technology, politics, economy, etc.
- Typically 200-400 words

## Actors (background/actors/*.md)

Each actor represents an entity that takes actions in the simulation.

**Format:**
```markdown
# Actor Name

## Short Description
One sentence description of the actor.

## Long Description
Detailed description including:
- Role and responsibilities
- Resources and capabilities
- Constraints and limitations
- Initial strategic position
```

**Guidelines:**
- Start with 2-4 actors (more makes coordination harder)
- Choose actors with different goals and capabilities
- Include actors that can create interesting conflicts or synergies
- Typical actors: governments, companies, organizations, media, public
- Long description: 100-200 words

**Example:**
```markdown
# Government

## Short Description
The Swedish government balancing innovation, employment, and public welfare.

## Long Description
The government faces competing pressures: fostering AI innovation for economic competitiveness while protecting workers from job displacement and maintaining public support. It has tools including regulation, funding for research and retraining, and public communication. The government must balance short-term political concerns with long-term strategic goals. Its actions significantly influence both AI development pace and public sentiment toward AI adoption.
```

## System Prompts (Optional)

You can create scenario-specific system prompts to customize how LLMs interpret the scenario. These override the default templates.

Starting from the prompts in `templates/system-prompts/` is recommended.

**Location:** `system-prompts/` folder in scenario directory

**Files:**
- `events.md` - Customizes event evaluation
- `actor_{actor_id}.md` - Customizes behavior for specific actor (one file per actor)
- `metric-rules.md` - Customizes metric rules updates
- `metrics-update.md` - Customizes metrics and narrative generation

**Actor-specific prompts:**
Each actor should have their own system prompt file named `actor_{actor_id}.md` where `{actor_id}` matches the ID in scenario.yaml. For example, if your scenario has actors `government` and `media`, you would create:
- `system-prompts/actor_government.md`
- `system-prompts/actor_media.md`

This allows each actor to have customized instructions, emphasis, or behavioral guidelines.

**When to use:**
- Scenario has unusual mechanics or rules
- Need to emphasize specific aspects for certain actors
- Want different tone or style for different actors
- Actors require special behavioral constraints

**Creating scenario-specific prompts:**

When creating scenario-specific system prompts, you should **replace all placeholders** with actual scenario data. The templates in `templates/system-prompts/` contain placeholders, but your scenario-specific prompts should have these filled in:

- `{{scenario_description}}` → Your actual scenario description from scenario.yaml
- `{{actors_list}}` → Formatted list with actual actor names and descriptions
- `{{metrics_list}}` → Formatted list with actual metric definitions and reference points
- `{{actor_name}}` → The specific actor's name (for actor prompts)
- `{{actor_description}}` → The specific actor's full description (for actor prompts)

**Example** (system-prompts/actor_government.md):
```markdown
# System Prompt: Government Actor

This is part of an AI-driven scenario simulation about exploring climate policy and renewable energy transition.

The simulation includes the following actors:
* Government: National decision-making body balancing innovation, security, and welfare
* Industry: Energy companies implementing renewable transition
* Environmental Groups: Advocacy organizations pushing for faster change

Key metrics:
* carbon_emissions: Annual CO2 emissions in millions of tons (0-100)
* renewable_percentage: Percentage of energy from renewables (0-100%)
* public_support: Public support for climate action (-10 to 10)

You are the Government.

The government must balance economic growth, climate goals, and political viability. You have tools including regulation, subsidies, and public communication.

Special rules for government actions in this scenario:
- Your actions should consider long-term consequences (10+ years)
- All major policy changes require 2-3 turns for implementation
- You must balance competing pressures from other actors
- Budget constraints limit simultaneous initiatives

[Rest of prompt follows template structure...]
```

**Important:**
- Only create custom system prompts when needed. The default templates work well for most scenarios.
- Always replace placeholders with actual scenario data - don't leave `{{...}}` in the files.

## Validation

Before running a scenario, validate the structure:

1. **File existence:** All required files present
2. **YAML syntax:** scenario.yaml parses correctly
3. **Actor IDs:** Match between config and actor files
4. **Metrics:** All referenced metrics are defined
5. **Start values:** All metrics have valid start values

**Automated Validation:**

You can use the built-in validator to check for common errors:

```bash
python -m scenario_lab.cli validate scenarios/your-scenario
```

Manual validation checklist:
- [ ] scenario.yaml has all required fields
- [ ] All actor IDs in scenario.yaml have corresponding .md files
- [ ] All metrics have ID, min, max, unit, start value
- [ ] All events have ID, condition, probability, can repeat, description
- [ ] Context.md provides sufficient background
- [ ] Each actor has short and long descriptions

## Running the Scenario

```bash
# Basic run
python -m scenario_lab.cli scenarios/scenario-name

# Specific number of turns
python -m scenario_lab.cli scenarios/scenario-name --turns 5

# Use different model
python -m scenario_lab.cli scenarios/scenario-name --model google/gemini-3-flash-preview

# Dry run (show prompts without executing)
python -m scenario_lab.cli scenarios/scenario-name --dry-run
```

## Tips for Creating Good Scenarios

1. **Start simple:** 2 actors, 3-4 metrics, 5 events. Add complexity after testing.

2. **Clear goals:** Give actors specific, potentially conflicting goals.

3. **Interesting dynamics:** Design metrics that interact (e.g., capability growth → unemployment → sentiment → political support).

4. **Realistic timescales:** Match time_scale to the scenario (months for fast-moving tech, years for policy).

5. **Test iteratively:**
   - Run 3 turns to see if basic mechanics work
   - Check if actors behave plausibly
   - Verify metrics change in reasonable ways
   - Adjust and re-run

6. **Reuse and adapt:** Start from existing scenarios (e.g., sweden-ai-2030) and modify.

7. **Document assumptions:** Include key assumptions in context.md.

## Example: Creating a Climate Policy Scenario

Here's how you might create a simple climate policy scenario:

**1. scenario.yaml**
```yaml
name: "Climate Policy 2025-2035"
description: "National climate policy and renewable energy transition"
start_date: "2025-01"
time_scale: "1 year per turn"
max_turns: 10
actors: [government, industry, environmental_groups]
llm:
  model: "google/gemini-3-flash-preview"
  temperature: 0.7
  max_tokens: 2000
```

**2. metrics.md**
```markdown
## carbon_emissions
**Description:** Annual CO2 emissions in millions of tons
**ID:** carbon_emissions
**Min:** 0
**Max:** 100
**Unit:** million tons CO2
**Start value:** 50

## renewable_percentage
**Description:** Percentage of energy from renewable sources
**ID:** renewable_percentage
**Min:** 0
**Max:** 100
**Unit:** percent
**Start value:** 30
```

**3. Continue with events.md, metric-rules.md, context.md, and actor files...**

## Troubleshooting

**LLMs produce inconsistent outputs:**
- Simplify metrics and rules
- Add more reference points to metrics
- Use more specific event conditions

**Actors behave unrealistically:**
- Add more constraints to actor descriptions
- Include specific examples of realistic actions
- Consider custom system prompt for actors

**Metrics don't change as expected:**
- Review metric rules for clarity
- Check if events are triggering correctly
- Verify probability calculations in dry-run mode

**Simulation ends too quickly:**
- Increase max_turns
- Adjust event probabilities
- Review terminal conditions in metric rules
