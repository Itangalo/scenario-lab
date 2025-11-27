# Creating Scenarios for Scenario Lab V3

This document provides instructions for creating new scenarios, intended for both human authors and AI coding assistants (Claude Code, Gemini CLI, etc.).

## ⚠️ CRITICAL: Read Before Generating

**Before writing any code, you MUST:**
1. Read the reference scenario at `examples/us-china-ai/` completely
2. Follow the EXACT formats shown in this document
3. Use ONLY the WorldState API methods documented below
4. Run validation after generating files

**DO NOT:**
- Invent methods that don't exist (e.g., `increment_metric`, `add_outcome_flag` with wrong signature)
- Use undocumented YAML formats (e.g., `metric_and`, `metric_or`, `random` conditionals)
- Create actors as objects instead of strings
- Reference metrics that don't exist in metrics.yaml

---

## File Structure

A complete scenario has this structure:

```
scenarios/my-scenario/
├── background/                 # Human-authored input (read by AI)
│   ├── scenario-sketch.md      # Overall scenario description
│   ├── actors-sketch.md        # Actor descriptions
│   ├── world-state-sketch.md   # Initial world state
│   ├── events-sketch.md        # Events and triggers
│   └── actors/                 # Detailed actor files (required)
│       ├── actor-one.md
│       └── actor-two.md
├── scenario.yaml               # Generated: main config
├── metrics.yaml                # Generated: world and actor metrics
├── events.yaml                 # Generated: scheduled events ONLY
├── methods.py                  # Generated: action implementations
└── runs/                       # Created at runtime
```

---

## WorldState API Reference

**This is the ONLY API available in methods.py. Do not invent other methods.**

### Getting Metrics

```python
# Get world metric
value = state.get_metric(None, "metric_name")

# Get actor's public metric
value = state.get_metric(actor, "public.metric_name")

# Get actor's private metric  
value = state.get_metric(actor, "private.metric_name")

# Shorthand (defaults to public)
value = state.get_metric(actor, "metric_name")
```

### Setting Metrics

```python
# Set world metric
state.set_metric(None, "metric_name", new_value)

# Set actor's public metric
state.set_metric(actor, "public.metric_name", new_value)

# Set actor's private metric
state.set_metric(actor, "private.metric_name", new_value)
```

### ⚠️ There is NO `increment_metric` method!

To increment a metric, you must get then set:
```python
# CORRECT way to increment
current = state.get_metric(actor, "public.budget")
state.set_metric(actor, "public.budget", current + 10)

# WRONG - this method does not exist!
# state.increment_metric(actor, "public.budget", 10)  # ❌ ERROR
```

### Relationships

```python
# Get relationship between two actors
rel = state.get_relationship(actor1, actor2)

# Modify trust (float, typically -1.0 to 1.0)
rel.trust += 0.1
rel.trust -= 0.2
```

### Facts

```python
# Add a fact to the ledger
state.add_fact("Something happened", source="action:action_name")
```

### Outcome Flags

```python
# Set an outcome flag (for scenario analysis)
state.set_outcome_flag("crisis_occurred", True)
```

---

## Technical File Formats

### scenario.yaml

```yaml
name: "Scenario Name"
description: "Brief description of the scenario"
start_date: "2026-01-01"  # Optional but recommended - enables precise time periods
time_scale: "6 months per turn"
max_turns: 10

# ⚠️ CRITICAL: actors must be a list of STRINGS, not objects!
actors:
  - actor-one      # ✅ CORRECT
  - actor-two      # ✅ CORRECT
  # - name: "actor-one"  # ❌ WRONG - do not use objects!

llm:
  provider: "mock"  # Use "mock" for testing, "openrouter" for real runs
  model: "mock-model"
  api_key_env: "OPENROUTER_API_KEY"
  temperature: 0.7
  max_tokens: 2000

action_point_rules:
  initial_per_turn: 3
  message_to_new_recipient: 1
  message_reply: 0
  forward_message: 1

# World-altering triggers (optional)
world_altering_triggers:
  - name: "Crisis Threshold"
    description: "What happens when triggered"
    conditions:
      - type: "metric"
        path: "world.crisis_level"
        operator: "gt"
        value: 0.8
    effects:
      - type: "set_outcome_flag"
        key: "crisis_occurred"
        value: true
```

**About `start_date`:**

The `start_date` field (format: `YYYY-MM-DD`) is optional but highly recommended. When provided, the Director agent will generate narratives with specific time periods instead of generic phrases:

**Without `start_date`:**
- "Over the past six months, tensions increased..."
- "Recently, the government announced..."

**With `start_date: "2026-01-01"` and `time_scale: "6 months per turn"`:**
- "During the first half of 2026, tensions increased..." (Turn 1)
- "In the second half of 2026, the government announced..." (Turn 2)
- "Throughout the first half of 2027, AI adoption accelerated..." (Turn 3)

The system automatically calculates the correct time period based on:
- **6 months, Jan-Jun:** "the first half of YEAR"
- **6 months, Jul-Dec:** "the second half of YEAR"
- **Other periods:** "March-May YEAR" or "January YEAR-June YEAR"

**Supported time scales:**
- `"6 months per turn"`, `"3 months per turn"`, `"1 year per turn"`, etc.


### metrics.yaml

```yaml
world:
  # World-level metrics visible to all actors
  metric_one: 50
  metric_two: 0.5

actors:
  actor-one:
    public:
      # Visible to all actors
      budget: 100
      reputation: 70
    private:
      # Visible only to this actor
      secret_capability: 80
      internal_morale: 60

  actor-two:
    public:
      budget: 80
      reputation: 65
    private:
      secret_capability: 70
      internal_morale: 55
```

**Rules:**
- Actor names must match exactly between scenario.yaml and metrics.yaml
- Use lowercase with hyphens for actor names
- Every actor in scenario.yaml MUST have an entry in metrics.yaml

### events.yaml

**⚠️ CURRENT LIMITATION: Only scheduled events are implemented!**

The engine currently only processes events where `turn` matches the current turn number. Conditional events (`scheduled: false`) are defined in the schema but not yet processed by the engine.

```yaml
events:
  # Scheduled events - these work
  - turn: 2
    name: "Election"
    description: "A major election takes place"
    effects:
      world.political_uncertainty: 0.7
      actors.government.public.legitimacy: 50

  - turn: 5
    name: "Economic Summit"
    description: "International economic summit"
    effects:
      world.cooperation_index: 0.6
```

**Effect values are ABSOLUTE, not relative:**
```yaml
effects:
  world.metric: 0.5    # Sets metric TO 0.5, does not add 0.5
```

**⚠️ DO NOT USE these conditional formats (not implemented):**
```yaml
# ❌ These do NOT work in the current engine:
conditional:
  type: "metric_and"    # ❌ Not implemented
  type: "metric_or"     # ❌ Not implemented  
  type: "random"        # ❌ Not implemented
  probability: 0.1      # ❌ Not implemented
```

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
        # You MUST register every action you implement
        self.register_action("invest", self.invest)
        self.register_action("negotiate", self.negotiate)
        self.register_action("public_statement", self.public_statement)

    def invest(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """
        Actor invests resources in something.
        
        Args expected:
            amount: int - How much to invest (default: 10)
        """
        amount = args.get("amount", 10)
        
        # Get current value, then set new value
        # ⚠️ There is no increment_metric method!
        current_budget = state.get_metric(actor, "public.budget")
        if current_budget < amount:
            return [f"{actor} lacks budget to invest {amount}."]
        
        state.set_metric(actor, "public.budget", current_budget - amount)
        
        # Increase capability
        current_cap = state.get_metric(actor, "private.capability")
        state.set_metric(actor, "private.capability", current_cap + amount * 0.5)
        
        return [f"{actor} invested {amount} in capability development."]

    def negotiate(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Actor negotiates with another actor."""
        target = args.get("target_actor")
        if not target:
            return ["No target specified for negotiation."]
        
        # Modify relationship
        rel = state.get_relationship(actor, target)
        rel.trust += 0.1
        
        # Add fact
        state.add_fact(
            f"{actor} and {target} held negotiations",
            source="action:negotiate"
        )
        
        return [f"{actor} negotiated with {target}, improving relations."]

    def public_statement(self, actor: str, args: dict, state: WorldState) -> List[str]:
        """Actor makes a public statement."""
        message = args.get("message", "a general statement")
        
        # Affect world metric
        sentiment = state.get_metric(None, "public_sentiment")
        state.set_metric(None, "public_sentiment", sentiment + 2)
        
        state.add_fact(
            f"{actor} made public statement: {message}",
            source="action:public_statement"
        )
        
        return [f"{actor} announced: {message}"]
```

**Critical rules for methods.py:**
1. Class MUST inherit from `ScenarioMethods`
2. Every action MUST be registered in `_register_actions()`
3. Use ONLY the documented WorldState API methods
4. Always get-then-set to modify metrics (no `increment_metric`)
5. Return `List[str]` with narrative descriptions

### background/actors/{actor-name}.md

```markdown
[One paragraph describing the actor and their role in the scenario.]

**Initial Goals:**
1. Primary goal
2. Secondary goal
3. Tertiary goal

**Behavioral Traits:**
- **Trait One:** How this affects their decisions
- **Trait Two:** How this affects their decisions
```

### background/context.md

A prose description (1-3 paragraphs) of the scenario's starting situation.

---

## Common Errors to Avoid

### Error 1: Actors as objects instead of strings

```yaml
# ❌ WRONG
actors:
  - name: "government"
    display_name: "The Government"

# ✅ CORRECT
actors:
  - government
```

### Error 2: Using non-existent methods

```python
# ❌ WRONG - increment_metric does not exist
state.increment_metric(actor, "budget", 10)

# ✅ CORRECT
current = state.get_metric(actor, "public.budget")
state.set_metric(actor, "public.budget", current + 10)
```

### Error 3: Conditional event formats that don't work

```yaml
# ❌ WRONG - these conditional types are not implemented
conditional:
  type: "metric_and"
  type: "random"
  probability: 0.15

# ✅ CORRECT - use only scheduled events for now
- turn: 3
  name: "Event Name"
  description: "..."
  effects:
    world.metric: 0.5
```

### Error 4: Mismatched actor names

```yaml
# scenario.yaml
actors:
  - labor-unions    # hyphenated

# metrics.yaml - MUST match exactly
actors:
  labor-unions:     # ✅ matches
    public: ...
    
  # laborunions:    # ❌ WRONG - doesn't match
  # labor_unions:   # ❌ WRONG - doesn't match
```

### Error 5: Missing metric paths

```python
# If you reference a metric, it MUST exist in metrics.yaml
state.get_metric(actor, "private.secret_plan")  
# ❌ Error if metrics.yaml doesn't have "secret_plan" under private
```

---

## Validation Checklist

Before considering a scenario complete, verify:

- [ ] `actors` in scenario.yaml is a list of strings (not objects)
- [ ] Every actor has a matching entry in metrics.yaml
- [ ] Every actor has a matching .md file in background/actors/
- [ ] All metrics referenced in methods.py exist in metrics.yaml
- [ ] All metrics referenced in events.yaml exist in metrics.yaml
- [ ] methods.py only uses documented WorldState API
- [ ] All actions in methods.py are registered in `_register_actions()`
- [ ] events.yaml only uses scheduled events (turn > 0)
- [ ] No invented methods like `increment_metric`

---

## Testing

After generating, always test:

```bash
# Must run from scenario_lab_v15 directory
cd /path/to/scenario_lab_v15

# Test with mock LLM (catches most errors)
python -m scenario_lab.cli run scenarios/my-scenario --turns 2 --dry-run

# If that passes, test with real LLM
export OPENROUTER_API_KEY="your-key"
python -m scenario_lab.cli run scenarios/my-scenario --turns 2
```

**Expected output for successful run:**
```
INFO - Loading scenario from: scenarios/my-scenario
INFO - Loaded scenario methods: MyScenarioMethods
INFO - TURN 1
...
INFO - Simulation complete. 2 turns processed.
```

**If you see errors:**
- `ValidationError` → Check YAML formats match examples exactly
- `Action not registered` → Add missing action to `_register_actions()`
- `AttributeError: increment_metric` → Use get/set pattern instead
- `KeyError` → Check metric exists in metrics.yaml

---

## Quick Reference Card

```python
# WorldState API - the ONLY methods available:

# Metrics
state.get_metric(actor, "path")           # Get value
state.get_metric(None, "world_metric")    # Get world metric
state.set_metric(actor, "path", value)    # Set value
state.set_metric(None, "world_metric", v) # Set world metric

# Relationships
rel = state.get_relationship(actor1, actor2)
rel.trust += 0.1                          # Modify trust

# Facts
state.add_fact("text", source="action:name")

# Outcome flags
state.set_outcome_flag("flag_name", True)
```

```yaml
# YAML formats:

# scenario.yaml - key fields
name: "Scenario Name"
start_date: "2026-01-01"  # Optional - enables precise time periods
time_scale: "6 months per turn"
actors:
  - actor-name  # MUST be strings, not objects

# events.yaml - ONLY scheduled events work
events:
  - turn: 2
    name: "Event"
    description: "..."
    effects:
      world.metric: 0.5
```
