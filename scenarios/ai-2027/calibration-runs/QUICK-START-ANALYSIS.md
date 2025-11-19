# Quick Start: Analyzing Your Calibration Run

The calibration baseline is running in the background. Here's what to do when it completes.

## 1. Check If Complete (1 minute)

```bash
cd "/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/projekt/Scenario Lab"

# Check if run finished
ls scenarios/ai-2027/calibration-runs/baseline-2025-01/world-state-*.md | wc -l
# Should show: 12 (if all turns completed)

# Check costs
cat scenarios/ai-2027/calibration-runs/baseline-2025-01/costs.json
```

## 2. Quick Reality Check (5 minutes)

Read Turn 1-2 decisions from key actors:

```bash
cd scenarios/ai-2027/calibration-runs/baseline-2025-01/

# OpenBrain CEO - did they announce capability jump?
head -50 openbrain-ceo-001.md

# US President - policy response?
head -50 us-president-001.md

# Alignment Lead - safety concerns?
head -50 openbrain-alignment-lead-001.md
```

**Ask yourself:**
- Does this sound like how a real CEO/President/Researcher would act?
- Are they considering realistic factors?
- Timing makes sense?

## 3. Compare Key Events (10 minutes)

**Real 2024 events to look for:**

- **GPT-4o release (May 2024)**: Did OpenBrain CEO announce similar?
- **o1 reasoning model (Sep 2024)**: Any breakthrough by turn 3-4?
- **DeepSeek R1 (Jan 2025)**: Did DeepCent CEO catch up?

Quick grep:
```bash
# Search for model releases
grep -i "agent\|model\|release" openbrain-ceo-*.md | head -20

# Search for regulatory mentions
grep -i "regulat\|policy\|govern" us-president-*.md | head -20
```

## 4. Score Realism (5 minutes)

Quick scoring guide:

**Decision Realism (0-10):**
- 8-10: Very realistic, matches real behavior
- 6-7: Broadly correct, some oddities
- 4-5: Partially realistic
- 0-3: Unrealistic

**Quick test for each actor:**
- OpenBrain CEO: [?/10]
- US President: [?/10]
- Alignment Lead: [?/10]

## 5. Note Key Findings (5 minutes)

Create quick notes:

```bash
# Edit the session file
nano scenarios/ai-2027/calibration-runs/CALIBRATION-SESSION-2025-01.md

# Add under "Preliminary Findings":
# - What worked well
# - What seemed unrealistic
# - Surprising results
```

## 6. Next Steps

**If results look good (≥7/10 realism):**
- Framework is working well!
- Document findings properly using calibration-results-template.md
- Minor prompt tweaks only

**If results are mixed (5-6/10):**
- Identify specific actors with issues
- Review their prompts
- Add explicit format instructions
- Run again with improvements

**If results are poor (<5/10):**
- Review CALIBRATION-SESSION-2025-01.md for known issues
- Focus on response format problems first
- Consider using better models for key actors

## Common Quick Fixes

**Problem: Actors too cautious**
→ Add competitive pressure language to prompts

**Problem: Actors too aggressive**
→ Emphasize safety culture and reputational risk

**Problem: Timeline too slow**
→ Increase competitive pressure in scenario

**Problem: Timeline too fast**
→ Add realistic bottlenecks (talent, hardware delays)

## Full Analysis Later

When you have more time, create complete calibration report:

```bash
cp scenarios/ai-2027/calibration-results-template.md \
   scenarios/ai-2027/calibration-results-2025-01.md

# Then fill in all sections systematically
```

See `CALIBRATION-SESSION-2025-01.md` for detailed instructions.

## Questions?

See:
- `docs/calibration-guide.md` - Complete guide
- `scenarios/ai-2027/CALIBRATION.md` - Methodology
- `CALIBRATION-SESSION-2025-01.md` - This session's details
