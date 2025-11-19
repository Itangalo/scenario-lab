# AI 2027 Calibration Session - January 2025

**Date Started:** 2025-01-07
**Status:** In Progress
**Run Directory:** `scenarios/ai-2027/calibration-runs/baseline-2025-01`

## Session Information

**Configuration:**
- Scenario: AI 2027 (scenarios/ai-2027/definition)
- Turns: 12 (covering mid-2025 to mid-2026)
- Credit limit: $6.00
- Models used:
  - 5 actors with `openai/gpt-4o`
  - 2 actors with `openai/gpt-4o-mini`
  - World state: `openai/gpt-4o-mini`

**Cost Estimate:** $2.14 for 12 turns
**Actual tokens (est):** 561,000

## Initial Observations (Turn 1)

### Response Parsing Issues Detected

Multiple parsing warnings observed during Turn 1:

```
No goals sections found in actor decision (3×)
No reasoning section found in actor decision (1×)
Failed to extract action - using entire content as fallback (1×)
```

**Analysis:**
- Actors are not consistently following expected response format
- System is using fallback extraction successfully
- This indicates actor prompts may need formatting guidance

**Impact:**
- Structured data extraction affected
- Fallback mechanisms working as designed
- Quality of extracted reasoning/goals data compromised

**Recommended Fix:**
Add explicit formatting instructions to actor system prompts:

```yaml
# Add to each actor's system_prompt:
IMPORTANT: Structure your response as follows:
**GOALS:**
[Your current goals and priorities]

**REASONING:**
[Your analysis and reasoning process]

**ACTION:**
[Your specific actions for this turn]
```

### Bilateral Communications

**Status:** ✅ Working
- First bilateral (OpenBrain CEO ↔ Alignment Lead) completed successfully
- Second bilateral (Alignment Lead ↔ US Advisor) initiated

**Observation:** Bilateral system functioning as designed despite parsing issues

## Next Steps

### 1. Monitor Completion

Check if scenario finished:
```bash
# Check if process is still running
ps aux | grep run_scenario

# Or check output directory for completion
ls -la scenarios/ai-2027/calibration-runs/baseline-2025-01/
```

**Expected outputs:**
- `world-state-001.md` through `world-state-012.md`
- `[actor-name]-001.md` through `[actor-name]-012.md` for each actor
- `costs.json`
- `metrics.json`
- `scenario-state.json`
- `validation-*.md` (if validation ran)

### 2. Quick Validation Check

Once complete, verify run succeeded:
```bash
cd scenarios/ai-2027/calibration-runs/baseline-2025-01/

# Check how many turns completed
ls world-state-*.md | wc -l

# Check final costs
cat costs.json | grep '"total"'

# Check if scenario completed or halted
grep -i "complete\|halt" scenario-state.json
```

### 3. Review Actor Decisions

Pick 2-3 key actors and review their Turn 1 decisions:
```bash
# OpenBrain CEO
cat openbrain-ceo-001.md

# US President
cat us-president-001.md

# Independent Alignment Researcher
cat independent-alignment-researcher-001.md
```

**Questions to ask:**
- Do decisions seem realistic for mid-2025?
- Are they considering appropriate factors?
- Do they reflect real CEO/President/Researcher behavior?

### 4. Compare Against Real Timeline

**Real events to compare (Q2-Q3 2024 → mid-2025 in simulation):**

**Model Releases:**
- GPT-4o (May 2024)
- Claude 3.5 Sonnet (June 2024)
- OpenAI o1 (September 2024)
- Gemini 2.0 (December 2024)
- DeepSeek R1 (January 2025)

**Key questions:**
- Did simulated OpenBrain CEO announce similar capability jump?
- Timing: How many turns until major release?
- Response: Did alignment lead raise concerns?
- Government: Did US President respond?

**Regulatory:**
- EU AI Act implementation (2024)
- US AI Safety Institute (2024)

**Questions:**
- Did simulated US President consider AI governance?
- Timing of policy responses?

### 5. Initial Scoring (Rough)

Use calibration-results-template.md and score 0-10 for each dimension:

**Decision Realism:**
- OpenBrain CEO: [X/10]
- US President: [X/10]
- Other actors: [X/10]

**Timeline Plausibility:**
- Did capability progression happen at realistic pace?
- Score: [X/10]

**Key Events Comparison:**
1. Major model release:
   - Predicted: [Yes/No]
   - Timing: [Turns off]
   - Score: [X/10]

2. Regulatory response:
   - Predicted: [Yes/No]
   - Realistic: [Yes/No]
   - Score: [X/10]

## Issues to Document

### 1. Response Format Consistency

**Problem:** Actors not following structured format
**Evidence:** Multiple parsing fallback warnings
**Severity:** Medium (fallbacks work but data quality affected)
**Fix:** Add explicit format instructions to prompts

### 2. Pydantic Deprecation Warning

```
PydanticDeprecatedSince20: The `dict` method is deprecated; use `model_dump` instead.
```

**Location:** `src/run_scenario.py:90`
**Severity:** Low (works but should be updated)
**Fix:** Replace `scenario_config.dict()` with `scenario_config.model_dump()`

## Preliminary Findings

*To be filled after reviewing completed run*

### Strengths
- [What framework did well]

### Weaknesses
- Response parsing: Actors don't follow format consistently
- [Other issues found]

### Surprising Results
- [Unexpected but interesting outcomes]

## Recommended Prompt Changes

### High Priority

**1. Add Format Instructions to All Actors**
Location: `scenarios/ai-2027/definition/actors/*.yaml`

Add to system_prompt:
```
RESPONSE FORMAT:
Structure each turn's response as follows:

**GOALS:**
- List your current priorities and objectives

**REASONING:**
Explain your analysis and decision-making process

**ACTION:**
Describe your specific actions for this turn

This format helps ensure clear documentation of your decision-making.
```

### Medium Priority

**2. Emphasize Realism in Actor Prompts**
If actors are too aggressive/conservative, add:
```
Act realistically based on how actual [CEOs/Presidents/Researchers]
behave in similar situations. Consider market pressures, political
realities, and practical constraints.
```

## Files Generated

**Run outputs:** `scenarios/ai-2027/calibration-runs/baseline-2025-01/`
**This session log:** `scenarios/ai-2027/calibration-runs/CALIBRATION-SESSION-2025-01.md`
**Final results:** (To be created) `scenarios/ai-2027/calibration-results-2025-01.md`

## Timeline

- **2025-01-07 18:20:** Run started
- **2025-01-07 18:3X:** Expected completion (15-30 min)
- **Next:** Review outputs and create full calibration report

## Commands for Analysis

Once run is complete, use these commands:

```bash
# 1. Check completion
cd "/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/projekt/Scenario Lab"
ls -la scenarios/ai-2027/calibration-runs/baseline-2025-01/

# 2. Check costs
cat scenarios/ai-2027/calibration-runs/baseline-2025-01/costs.json | python -m json.tool

# 3. View metrics progression
cat scenarios/ai-2027/calibration-runs/baseline-2025-01/metrics.json | python -m json.tool

# 4. Read first few turns
cat scenarios/ai-2027/calibration-runs/baseline-2025-01/world-state-001.md
cat scenarios/ai-2027/calibration-runs/baseline-2025-01/openbrain-ceo-001.md

# 5. Check validation reports (if generated)
ls scenarios/ai-2027/calibration-runs/baseline-2025-01/validation-*.md

# 6. Create detailed calibration report
cp scenarios/ai-2027/calibration-results-template.md \
   scenarios/ai-2027/calibration-results-2025-01.md

# Then fill in the template with findings
```

## Calibration Report Creation

When ready to document findings:

1. **Copy template:**
   ```bash
   cp scenarios/ai-2027/calibration-results-template.md \
      scenarios/ai-2027/calibration-results-2025-01.md
   ```

2. **Fill in sections:**
   - Executive Summary (overall assessment)
   - Configuration (record settings used)
   - Overall Calibration Scores (0-10 for each metric)
   - Historical Event Comparison (event-by-event)
   - Actor-by-Actor Analysis
   - Recommendations

3. **Calculate Overall Score:**
   Average of 4 metrics = Overall calibration score
   - ≥7.5: Suitable for research
   - 6-7.4: Use with caution, expert review needed
   - <6: Significant improvements needed

## Next Session

After analyzing results:
- Implement prompt improvements
- Run validation calibration with refined prompts
- Compare improvement in scores
- Document lessons learned
