# Scenario Lab V3 – Implementation Phases

## How to Use This Document

Work through the phases in order. Each phase has:
1. **Goal:** What you're building
2. **Prompt:** Copy-paste this to Claude Code
3. **Validation:** How to verify it works before moving on

Give Claude Code the design document as context at the start of the conversation. Then give one phase prompt at a time.

---

## Phase 1: Project Skeleton

**Goal:** Basic file structure, data models, empty turn loop.

**Prompt:**
````
I'm building Scenario Lab V3. The design document is attached.

Create the initial project structure:

1. Directory layout:
  scenario_lab/
  ├── engine.py          # Main simulation loop
  ├── models.py          # Pydantic data classes
  ├── llm_provider.py    # LLM abstraction (stub for now)
  ├── methods_base.py    # Base class for scenario methods
  └── utils.py           # File loading, logging helpers

2. In models.py, create Pydantic models for:
  - WorldState (metrics, relationships, fact_ledger, narrative, outcome_flags)
  - Actor (name, goals, action_points)
  - Message (sender, recipient, content, intent, visibility)
  - Metrics structure matching the design doc (world + actors with private/public)

3. In engine.py, create a Simulation class with:
  - __init__(self, scenario_path: str) that loads YAML files
  - run_turn(self) with placeholder logging for each phase:
    "Pre-turn", "Phase 1", "Phase 2", "Phase 3", "Post-turn"
  - run(self, num_turns: int) that loops through turns

4. Create a minimal test scenario in examples/test-scenario/ with:
  - scenario.yaml
  - metrics.yaml
  - events.yaml (can be empty list)
  - background/context.md (one paragraph)
  - background/actors/USA.md and China.md (minimal)

Technical requirements:
- Python 3.11+
- Use pydantic for all data classes
- Type hints everywhere
- No external dependencies yet except pydantic and pyyaml
````

**Validation:**
````bash
cd scenario_lab
python -c "from engine import Simulation; s = Simulation('examples/test-scenario'); s.run(2)"
```
Should print phase names for 2 turns without errors.

---

## Phase 2: Metrics Visibility

**Goal:** Actors see only what they're allowed to see.

**Prompt:**
```
Now implement the metrics visibility system.

In models.py or a new file visibility.py:

1. Add method get_visible_metrics(state: WorldState, actor_name: str) -> dict that returns:
  - All world metrics
  - The requesting actor's private AND public metrics
  - Other actors' public metrics only

2. Add method generate_actor_view(state: WorldState, actor_name: str) -> dict that returns
  a complete "view" for the actor including:
  - Visible metrics
  - Relationship state (all relationships are visible)
  - Fact ledger (all facts are visible)
  - Narrative state
  - The actor's current goals

Write tests in tests/test_visibility.py:
- USA sees USA.private.military_capacity
- USA does NOT see China.private.military_capacity
- USA sees China.public.budget
- Both see world.global_temperature

Use pytest. Make the tests runnable.
````

**Validation:**
````bash
pytest tests/test_visibility.py -v
```
All tests pass.

---

## Phase 3: Mock LLM

**Goal:** Fake LLM responses so we can test the full loop.

**Prompt:**
```
Create a mock LLM system for testing.

In llm_provider.py:

1. Define a Protocol class LLMProvider with method:
  complete(messages: list[dict], model: str, response_format: dict | None = None) -> str

2. Implement MockProvider that returns deterministic responses:
  - For Phase 1 (communication): Returns a message to a random other actor
  - For Phase 2 (response): Returns a reply or empty
  - For Phase 3 (action): Returns JSON with:
    - reasoning: str
    - actions: list[dict] with name and args
    - next_turn_goals: list[str]
  
  The mock should detect which phase based on the system prompt content
  (look for "Phase 1", "Phase 2", "Phase 3" in the messages).

3. Add a get_provider(config: dict) -> LLMProvider factory function.

Example Phase 3 mock response:
{
 "reasoning": "Given the current situation, investing in research is prudent.",
 "actions": [
   {"name": "invest_research", "args": {"amount": 50}}
 ],
 "next_turn_goals": [
   "Continue AI development",
   "Monitor China's activities"
 ]
}

Make the mock responses valid but simple. We'll replace this with real LLMs later.
````

**Validation:**
````python
from llm_provider import MockProvider
p = MockProvider()
response = p.complete([{"role": "system", "content": "Phase 3..."}], "mock")
import json
data = json.loads(response)
assert "actions" in data
```

---

## Phase 4: Action Execution

**Goal:** methods.py processes actions and updates state.

**Prompt:**
```
Implement the action execution system.

1. In methods_base.py, create:
  
  class ScenarioMethods:
      """Base class. Scenarios subclass this."""
      
      def execute_action(self, actor: str, action: dict, state: WorldState) -> list[str]:
          """Dispatch to action_<name> method. Return interpretations."""
          
      def validate_action(self, actor: str, action: dict, state: WorldState) -> bool:
          """Check if action is allowed. Default: max 2 actions per actor per turn."""

2. Create examples/test-scenario/methods.py that inherits from ScenarioMethods:
  
  Implement these actions:
  - invest_research(actor, args, state): Spend budget, increase ai_capability
  - form_alliance(actor, args, state): Add to relationships
  - declare_war(actor, args, state): Set outcome_flags["war_declared"] = True
  
  Each returns list of interpretation strings.

3. In engine.py, add execute_actions(self, actions_by_actor: dict) that:
  - Loads the scenario's methods.py dynamically
  - Validates each action
  - Executes valid actions
  - Collects interpretations
  - Rejects invalid actions with logging

4. Update WorldState with helper methods:
  - get_metric(actor: str | None, key: str) -> float
  - set_metric(actor: str | None, key: str, value: float)
  - add_fact(fact: str)
  - set_outcome_flag(key: str, value: any)
````

**Validation:**
````python
from models import WorldState
from examples.test_scenario.methods import TestScenarioMethods

state = WorldState.from_yaml("examples/test-scenario")
methods = TestScenarioMethods()
interpretations = methods.execute_action("USA", {"name": "invest_research", "args": {"amount": 50}}, state)
assert state.get_metric("USA", "budget") == 450  # Started at 500
```

---

## Phase 5: Full Turn Loop

**Goal:** Complete turn cycle with all phases connected.

**Prompt:**
```
Connect everything into a working turn loop.

Update engine.py Simulation class:

1. pre_turn(self):
  - Check scheduled events (by turn number)
  - Check conditional events (evaluate conditions against metrics)
  - Apply event effects
  - Reset action points
  - Check world_altering_triggers, set flag if any true
  - Generate actor views and save to runs/run-XXX/turn-XX/views/

2. phase_1_communication(self):
  - For each actor: call LLM with their view, ask for messages
  - Deduct AP for messages sent
  - Save to comms_phase_1.json

3. phase_2_response(self):
  - Distribute Phase 1 messages to recipients
  - For each actor with messages: call LLM for responses
  - Free replies (0 AP), new messages cost AP
  - Save to comms_phase_2.json

4. phase_3_action(self):
  - Compile communication results
  - For each actor: call LLM for actions
  - Collect all action requests
  - Save to actions.json

5. post_turn(self):
  - Execute all actions via methods.py
  - Update metrics
  - Update relationships based on actions
  - Update fact ledger
  - Call Director (mock for now: just concatenate interpretations)
  - Save world_state.md, metrics.json, relationships.json, fact_ledger.json

6. Create run directory structure automatically:
  runs/run-001/turn-01/...

Run with MockProvider. Everything should execute and produce output files.
````

**Validation:**
````bash
python -m scenario_lab.engine examples/test-scenario --turns 3
ls examples/test-scenario/runs/run-001/turn-01/
# Should see: views/, comms_phase_1.json, comms_phase_2.json, actions.json, world_state.md, metrics.json
```

---

## Phase 6: Real LLM Integration

**Goal:** Connect to OpenRouter and local models.

**Prompt:**
```
Implement real LLM providers.

In llm_provider.py:

1. OpenRouterProvider:
  - __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1")
  - complete() sends POST to /chat/completions
  - Handle rate limits with exponential backoff (3 retries)
  - Handle malformed JSON responses (retry once with "Please respond with valid JSON only")
  - Timeout: 60 seconds
  - Use httpx for requests

2. LocalProvider:
  - __init__(self, base_url: str = "http://localhost:11434/v1")
  - Same interface, calls local OpenAI-compatible endpoint
  - No retry on rate limits (local doesn't have them)

3. Update get_provider(config: dict) to read from scenario.yaml llm section:
  - provider: "openrouter" | "local" | "mock"
  - model: model string
  - api_key_env: environment variable name for API key

4. Add --provider CLI flag to override scenario.yaml for testing.

5. Robust error handling:
  - Log full request/response on error
  - Raise clear exceptions: LLMConnectionError, LLMResponseError, LLMRateLimitError
````

**Validation:**
````bash
export OPENROUTER_API_KEY="your-key"
python -m scenario_lab.engine examples/test-scenario --turns 1 --provider openrouter --model anthropic/claude-haiku
# Should complete one turn with real LLM
```

---

## Phase 7: Prompts

**Goal:** Separate prompt files for each phase.

**Prompt:**
```
Create the prompt system.

1. Create prompts/ directory with:
  - actor_phase1.txt  (communication)
  - actor_phase2.txt  (response)
  - actor_phase3.txt  (action)
  - director.txt      (narrative synthesis)

2. Each prompt should be a Jinja2 template with placeholders:
  - {{ actor_name }}
  - {{ actor_description }}
  - {{ current_goals }}
  - {{ visible_metrics }}
  - {{ relationships }}
  - {{ fact_ledger }}
  - {{ narrative }}
  - {{ action_points }}
  - {{ incoming_messages }}  (for phase 2)
  - {{ communication_summary }}  (for phase 3)
  - {{ world_altering_event }}  (boolean flag)
  - {{ available_actions }}  (list from methods.py)

3. Create prompts/loader.py:
  - load_prompt(name: str, **kwargs) -> str
  - Loads template, renders with kwargs

4. Update engine.py to use prompt templates instead of hardcoded strings.

5. Write actor_phase3.txt with:
  - Clear instruction to output JSON
  - Schema for expected response
  - Instruction about goal stability (only change marginally unless world_altering_event)
  - List of available actions with their arguments
  - Constraint reminder: max 2 major initiatives

Include this in the phase 3 prompt:
"You must respond with valid JSON only. No markdown, no explanation outside the JSON."
```

**Validation:**
Review generated prompts manually. Run one turn and verify LLM receives properly formatted prompts (check logs).

---

## Phase 8: Director Agent

**Goal:** Coherent narrative synthesis.

**Prompt:**
```
Implement the Director agent.

1. Create director.py with class Director:
  
  synthesize_turn(
      turn_number: int,
      actions_by_actor: dict,
      interpretations: list[str],
      events_triggered: list[dict],
      previous_narrative: str
  ) -> str

2. The Director:
  - Receives all actions taken (with actor reasoning)
  - Receives interpretations from methods.py
  - Receives any events that triggered
  - Receives previous narrative for continuity
  - Calls LLM to generate world_state.md

3. Director prompt (director.txt) should instruct:
  - Write in third person, past tense
  - Focus on what happened, not what actors thought
  - Integrate metric interpretations naturally
  - Keep it concise: 2-4 paragraphs per turn
  - End with "current situation" summary

4. Update post_turn() to call Director instead of concatenating interpretations.

5. Add memory management:
  - If turn > 2, summarize turns 1 to (current-2) into "earlier epochs"
  - Pass only last 2 turns in detail + epoch summary to Director
```

**Validation:**
Run 3 turns. Read generated world_state.md files. They should be coherent narrative, not lists of actions.

---

## Phase 9: CLI and Logging

**Goal:** Usable command-line interface.

**Prompt:**
```
Create a proper CLI.

1. Update engine.py or create cli.py with argparse:
  
  scenario_lab run <scenario_path> [options]
  
  Options:
  --turns N          Number of turns (default: from scenario.yaml)
  --run-id ID        Custom run ID (default: auto-increment)
  --provider NAME    Override LLM provider
  --model NAME       Override model
  --verbose          Print detailed progress
  --dry-run          Run with MockProvider regardless of config

2. Progress display:
  - Print current turn and phase
  - Print actor names as they act
  - Print action summaries
  - Print event triggers

3. Logging:
  - Save all LLM requests/responses to runs/run-XXX/llm_log.jsonl
  - Each line: {"timestamp", "phase", "actor", "request", "response"}

4. Add command:
  
  scenario_lab analyze <scenario_path> [options]
  
  --runs N           Analyze last N runs
  
  Output: Summary statistics from outcome_flags across runs.

5. Error recovery:
  - If a turn fails, save partial state
  - Allow resuming with --resume flag
````

**Validation:**
````bash
scenario_lab run examples/test-scenario --turns 3 --verbose
scenario_lab analyze examples/test-scenario --runs 1
```

---

## Phase 10: Complete Test Scenario

**Goal:** A real, playable scenario.

**Prompt:**
```
Create a complete US-China AI Race scenario.

1. Expand examples/us-china-ai/ with:

  background/context.md:
  - 2-3 paragraphs setting the scene (2025, AI competition heating up)
  
  background/actors/USA.md:
  - Identity, initial goals, behavioral traits
  - 3-5 concrete goals
  
  background/actors/China.md:
  - Same structure
  
  background/actors/EU.md:
  - Third actor for more interesting dynamics

2. scenario.yaml with:
  - 10 turn max
  - 3 AP per actor
  - Meaningful world_altering_triggers

3. metrics.yaml with:
  - World: global_temperature, ai_catastrophe_risk, global_ai_regulation
  - Per actor: budget, ai_capability, military_capacity, public_trust, international_influence
  - Sensible starting values that create tension

4. events.yaml with:
  - 3 scheduled events (elections, summits, tech breakthroughs)
  - 3 conditional events (based on metric thresholds)

5. methods.py with actions:
  - invest_ai_research
  - invest_ai_safety
  - impose_sanctions
  - form_alliance
  - propose_treaty
  - military_posturing
  - public_announcement
  
  Each with appropriate metric effects and interpretations.

6. Make the scenario interesting:
  - Budget constraints force tradeoffs
  - ai_capability growth has diminishing returns
  - High ai_capability + low ai_safety increases ai_catastrophe_risk
  - Treaties can reduce tensions but cost political capital
````

**Validation:**
Run 5 turns with a capable model (Claude Sonnet). Read the output. Is it coherent? Do actors behave plausibly? Are there interesting dynamics?

---

## Debugging Tips

**If actors ignore their goals:**
Check the Phase 3 prompt. Goals might not be prominent enough.

**If actions are invalid JSON:**
Add more explicit JSON formatting instructions. Consider using `response_format: {"type": "json_object"}` if provider supports it.

**If narrative is repetitive:**
Director prompt may need more variation instructions. Or previous narrative context is too long.

**If metrics don't change:**
Check methods.py action implementations. Add logging to see which actions execute.

**If simulation feels random:**
Actors may lack enough context. Increase narrative detail or add more facts to fact_ledger.
