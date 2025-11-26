# Creating Scenarios for Scenario Lab V3

This document provides instructions for creating new scenarios, intended for both human authors and AI coding assistants (Claude Code, Gemini CLI, etc.).

## Overview

A scenario consists of background material (human-authored) and technical files (can be AI-generated). The workflow is:

1. Human writes background sketches describing the scenario
2. AI generates technical files based on the sketches and reference examples
3. Human reviews and iterates

## File Structure

A complete scenario has this structure:

```
scenarios/my-scenario/
├── background/                 # Human-authored input (read by AI)
│   ├── scenario-sketch.md      # Overall scenario description
│   ├── actors-sketch.md        # Actor descriptions
│   ├── world-state-sketch.md   # Initial world state
│   ├── events-sketch.md        # Events and triggers
│   └── actors/                 # Optional: detailed actor files
│       ├── actor-one.md
│       └── actor-two.md
├── scenario.yaml               # Generated: main config
├── metrics.yaml                # Generated: world and actor metrics
├── events.yaml                 # Generated: scheduled and conditional events
├── methods.py                  # Generated: action implementations
└── runs/                       # Created at runtime
```

## Background Files (Human Input)

These are the files humans should write. They can be in any language and format, but should be clear and detailed enough for an AI to generate the technical files.

### scenario-sketch.md

Describe:
- **Purpose**: What is this scenario exploring?
- **Time frame**: Start date, end date, turn duration
- **Actors**: Who are the main actors? (Just list them here)
- **Themes**: What dynamics are you interested in?
- **Metrics**: What should be tracked?

Example excerpt:
```markdown
## Time Frame
- Start: January 2026
- End: December 2030
- Turn duration: 6 months (10 turns total)

## Actors
- Government
- Labor Unions
- Media
- Business Sector
```

### actors-sketch.md

For each actor, describe:
- **Role**: What is this actor in the scenario?
- **Goals**: What do they want to achieve?
- **Constraints**: What limits their actions?
- **Decision style**: How do they typically behave?
- **Information access**: What do they know/not know?
- **Relationships**: How do they relate to other actors?

### world-state-sketch.md

Describe the initial state of the world:
- Global context
- Local/regional context
- Key metrics and their starting values
- Recent events that set the stage

### events-sketch.md

Describe events that should occur:
- **Scheduled events**: Things that happen at specific turns
- **Conditional events**: Things that trigger based on metrics
- **Random events**: Low-probability events (optional)
- **World-altering triggers**: Conditions that end or transform the scenario

---

## Technical Files (AI-Generated)

These files must follow exact formats. Use `examples/us-china-ai/` as a reference.

### scenario.yaml

```yaml
name: "Scenario Name"
time_scale: "6 months per turn"
max_turns: 10

actors:
  - actor-one
  - actor-two

llm:
  provider: "openrouter"
  model: "anthropic/claude-sonnet-4-20250514"
  api_key_env: "OPENROUTER_API_KEY"
  temperature: 0.7
  max_tokens: 2000

action_point_rules:
  initial_per_turn: 3
  message_to_new_recipient: 1
  message_reply: 0
  forward_message: 1

world_altering_triggers:
  - name: "Trigger Name"
    description: "What happens when triggered"
    conditions:
      - type: "metric"
        path: "world.some_metric"
        operator: "gt"
        value: 0.8
    effects:
      - type: "set_outcome_flag"
        key: "scenario_ended"
        value: true
```

**Key rules:**
- Actor names in `actors:` must match filenames in `background/actors/` (without extension)
- Actor names should use lowercase with hyphens (e.g., `labor-unions`)
- `llm.provider` can be "openrouter", "local", or "mock"

### metrics.yaml

```yaml
world:
  metric_one: 0.5
  metric_two: 100

actors:
  actor-one:
    public:
      visible_metric: 50
      another_public: 0.7
    private:
      hidden_metric: 80
      secret_capability: 100
      
  actor-two:
    public:
      visible_metric: 45
    private:
      hidden_metric: 60
```

**Key rules:**
- `world:` metrics are visible to all actors
- `public:` metrics for each actor are visible to all actors
- `private:` metrics are only visible to the actor itself
- Metrics can be numbers (int or float)
- Choose metric names that are clear and consistent

### events.yaml

```yaml
events:
  # Scheduled events (happen at specific turns)
  - turn: 2
    name: "Event Name"
    description: "What happens"
    effects:
      world.some_metric: 0.3
      actors.actor-one.public.trust: -0.1

  # Conditional events (check every turn)
  - turn: 0
    scheduled: false
    name: "Conditional Event"
    description: "Triggers when condition is met"
    conditional:
      type: "metric"
      path: "actors.*.public.some_metric"
      operator: "lt"
      value: 0.3
    effects:
      world.instability: 0.1
```

**Key rules:**
- Scheduled events: set `turn:` to the turn number
- Conditional events: set `turn: 0` and `scheduled: false`
- Effect values are absolute (set to), not relative (add to)
- Paths use dot notation: `world.metric`, `actors.name.public.metric`

### methods.py

```python
"""
Scenario-specific methods for [Scenario Name].
"""
from typing import List
from scenario_lab.methods_base import ScenarioMethods
from scenario_lab.models import WorldState


class MyScenarioMethods(ScenarioMethods):
    """Methods and actions for this scenario."""

    def _register_actions(self) -> None:
        """Register all available actions for this scenario."""
        self.register_action("action_name", self.action_name)
        self.register_action("another_action", self.another_action)

    def action_name(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """
        Description of what this action does.
        
        Args:
            amount: How much to invest (default: 10)
        """
        amount = args.get("amount", 10)
        
        # Modify metrics
        current = state.get_metric(actor, "public.budget")
        state.set_metric(actor, "public.budget", current - amount)
        
        # Return narrative description
        return [f"{actor} did something with {amount}."]

    def another_action(self, actor: str, args: dict, state: WorldState) -> List[str]:
        target = args.get("target_actor")
        if not target:
            return ["No target specified."]
        
        # Modify relationships
        state.get_relationship(actor, target).trust += 0.1
        
        # Add facts to world state
        state.add_fact(f"{actor} interacted with {target}", source="action")
        
        return [f"{actor} did something with {target}."]
```

**Key rules:**
- Class must inherit from `ScenarioMethods`
- All actions must be registered in `_register_actions()`
- Action methods take `actor`, `args`, `state` and return `List[str]`
- Use `state.get_metric()` and `state.set_metric()` for metrics
- Use `state.get_relationship()` for relationships
- Use `state.add_fact()` to add facts to world state
- Return a list of narrative strings describing what happened

### background/actors/{actor-name}.md

One file per actor with:
- Description of the actor
- Initial goals (numbered list)
- Behavioral traits

```markdown
[One paragraph describing the actor and their role.]

**Initial Goals:**
1. First goal
2. Second goal
3. Third goal

**Behavioral Traits:**
- **Trait One:** Description
- **Trait Two:** Description
```

### background/context.md

A single prose description (1-3 paragraphs) of the scenario's starting situation. This is included in prompts to the LLM.

---

## Generating a Scenario

When asked to generate a scenario from background sketches, follow this process:

### Step 1: Read all background files
Read and understand:
- The scenario purpose and themes
- All actors and their relationships
- The world state and metrics
- Events and triggers

### Step 2: Determine metrics
From the sketches, identify:
- World-level metrics (global state)
- Per-actor public metrics (visible to all)
- Per-actor private metrics (information asymmetry)

Choose clear, quantifiable metrics. Common patterns:
- Capabilities: 0-100 scale
- Trust/opinion: -1.0 to 1.0 or 0.0 to 1.0
- Resources: absolute numbers (budget, population)
- Rates: percentages (unemployment, adoption rate)

### Step 3: Design actions
Create actions that:
- Match what actors would realistically do
- Modify relevant metrics
- Have clear costs and benefits
- Enable interesting trade-offs

Common action patterns:
- **Invest**: Spend resources to gain capability
- **Negotiate**: Attempt to change relationships
- **Announce**: Make public statements (narrative)
- **Regulate**: Change rules that affect other actors
- **Sanction**: Impose costs on other actors

### Step 4: Design events
Create:
- 2-4 scheduled events per scenario (key milestones)
- 2-4 conditional events (emergent dynamics)
- 1-2 world-altering triggers (end conditions)

### Step 5: Generate files
Create all technical files with consistent:
- Actor names (matching across all files)
- Metric names (matching across all files)
- Action names (registered and implemented)

### Step 6: Validate
Check that:
- All actors in `scenario.yaml` have matching `.md` files
- All actors in `scenario.yaml` have entries in `metrics.yaml`
- All metrics referenced in `events.yaml` exist in `metrics.yaml`
- All actions in `methods.py` are registered
- Class name in `methods.py` matches scenario theme

---

## Example: Converting Sweden AI 2030

Given background sketches about Sweden and AI 2026-2030, you would:

1. **Actors**: government, labor-unions, media, business-sector
2. **World metrics**: 
   - `ai_capability_metr` (hours of tasks AI can handle)
   - `global_ai_regulation` (0-1 scale)
   - `eu_regulatory_pressure` (0-1 scale)
3. **Actor public metrics**:
   - `public_trust`, `international_influence`, `budget`
4. **Actor private metrics**:
   - `ai_adoption_rate`, `internal_capability`, `lobbying_power`
5. **Actions**:
   - `invest_ai_adoption`, `propose_regulation`, `lobby_government`
   - `public_campaign`, `negotiate_with_unions`, `publish_report`
6. **Events**:
   - Turn 1: "Riksdagsval 2026"
   - Turn 5: "US Presidential Election 2028"
   - Conditional: "AI Unemployment Crisis" if unemployment > 12%

---

## Testing Your Scenario

After generating, test with:

```bash
# Dry run with mock LLM
python -m scenario_lab.cli run scenarios/my-scenario --turns 3 --dry-run

# Real run with actual LLM
export OPENROUTER_API_KEY="your-key"
python -m scenario_lab.cli run scenarios/my-scenario --turns 3
```

Check that:
- All turns complete without errors
- Metrics change as expected
- Events trigger at correct times
- Actions produce sensible narratives
