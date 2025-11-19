# Resuming AI 2027 Calibration - Instructions

**Status:** Paused during Turn 1, Phase 1 (Bilateral Communications)
**Date Paused:** 2025-01-07 ~19:24
**Reason:** Need more API credits

## What Was Created

The run started and created partial Turn 1 outputs:
- `world-state-000.md` - Initial world state ✅
- 6 bilateral communication files ✅
- `scenario.log` - Execution log ✅
- Turn 1 incomplete (no actor decisions yet)

**Estimated cost so far:** ~$0.20-0.40 (bilateral communications only)

## When Ready to Resume

### Option 1: Resume from Checkpoint (RECOMMENDED)

If scenario saved state before interruption:

```bash
cd "/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/projekt/Scenario Lab"

# Check if state was saved
ls scenarios/ai-2027/calibration-runs/baseline-2025-01/scenario-state.json

# If exists, resume:
python src/run_scenario.py \
  --resume scenarios/ai-2027/calibration-runs/baseline-2025-01 \
  --credit-limit 6.00
```

**Benefits:**
- Continues exactly where it left off
- Preserves bilateral communications already done
- No wasted cost

### Option 2: Start Fresh (if resume fails)

If no state file or resume doesn't work:

```bash
cd "/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/projekt/Scenario Lab"

# Remove partial run
rm -rf scenarios/ai-2027/calibration-runs/baseline-2025-01

# Start new run with fresh directory name
python src/run_scenario.py \
  scenarios/ai-2027/definition \
  --max-turns 12 \
  --credit-limit 6.00 \
  --output scenarios/ai-2027/calibration-runs/baseline-2025-01-take2
```

**Note:** Will redo Turn 1 from scratch

## Before Running

### 1. Check API Credits

Ensure you have sufficient OpenRouter credits:
- Estimated cost for 12 turns: ~$2-3
- Buffer recommended: $5-6

Check at: https://openrouter.ai/credits

### 2. Verify API Key

```bash
# Check .env file has key
grep OPENROUTER_API_KEY .env
```

### 3. Consider Using Budget Version

If cost is a concern, use the budget version instead:

```bash
python src/run_scenario.py \
  scenarios/ai-2027/definition-budget \
  --max-turns 12 \
  --credit-limit 6.00 \
  --output scenarios/ai-2027/calibration-runs/baseline-budget-2025-01
```

**Budget version savings:**
- Uses `gpt-4o-mini` for 4 of 7 actors (57%)
- Cost: ~$1.20-1.80 (40% cheaper)
- Still produces useful calibration data

## Running the Full Calibration

Once you're ready:

### Quick Run (Just Get It Done)

```bash
cd "/Users/johanfalk/Desktop/Dropbox/Johans/Echo/Falk AI/projekt/Scenario Lab"

# Try resume first
python src/run_scenario.py \
  --resume scenarios/ai-2027/calibration-runs/baseline-2025-01 \
  --credit-limit 6.00

# If that fails, start fresh with budget version
python src/run_scenario.py \
  scenarios/ai-2027/definition-budget \
  --max-turns 12 \
  --credit-limit 6.00 \
  --output scenarios/ai-2027/calibration-runs/baseline-budget-2025-01
```

**Time:** 15-30 minutes
**Cost:** $1.20-3.00 depending on version

### Monitor Progress

In another terminal:
```bash
# Watch turn completion
watch -n 5 'ls scenarios/ai-2027/calibration-runs/baseline-*/world-state-*.md | wc -l'

# Check costs in real-time
tail -f scenarios/ai-2027/calibration-runs/baseline-*/scenario.log | grep -i cost
```

## After Completion

Follow instructions in:
- `QUICK-START-ANALYSIS.md` - Fast 30-minute analysis
- `CALIBRATION-SESSION-2025-01.md` - Detailed analysis

### Quick Check

```bash
cd scenarios/ai-2027/calibration-runs/baseline-2025-01  # or baseline-budget-2025-01

# Verify completion
ls world-state-*.md | wc -l  # Should show: 12

# Check costs
cat costs.json

# Quick read of first turn
head -50 openbrain-ceo-001.md
head -50 us-president-001.md
```

## Troubleshooting

### "Rate limit exceeded"

Scenario will auto-save state. Wait a few minutes, then resume:
```bash
python src/run_scenario.py --resume [path-to-run]
```

### "Credit limit exceeded"

If you set credit limit too low:
```bash
# Resume with higher limit
python src/run_scenario.py \
  --resume [path-to-run] \
  --credit-limit 10.00
```

### Process killed/crashed

Check if state was saved:
```bash
ls [run-directory]/scenario-state.json

# If exists, resume
python src/run_scenario.py --resume [path-to-run]
```

## Alternative: Shorter Test Run

If you want to test without full 12 turns:

```bash
# Run just 3 turns (~$0.50-0.75)
python src/run_scenario.py \
  scenarios/ai-2027/definition-budget \
  --max-turns 3 \
  --credit-limit 2.00 \
  --output scenarios/ai-2027/calibration-runs/short-test-2025-01
```

**Benefits:**
- Fast (~5-10 minutes)
- Cheap (~$0.50-0.75)
- Still validates framework basics
- Can extend later if useful

## What To Do With Results

Once you have completed run:

1. **Quick assessment** (30 min) - Use QUICK-START-ANALYSIS.md
2. **Full analysis** (2-3 hours) - Use calibration-results-template.md
3. **Implement fixes** - Based on findings
4. **Run validation** - Test improvements

## Files Reference

**Session documentation:**
- `CALIBRATION-SESSION-2025-01.md` - Detailed session log with observations
- `QUICK-START-ANALYSIS.md` - Fast 30-minute analysis guide
- `RESUME-INSTRUCTIONS.md` - This file

**Templates for analysis:**
- `../calibration-results-template.md` - Full calibration report template

**Guides:**
- `../../docs/calibration-guide.md` - Complete calibration guide
- `../CALIBRATION.md` - Methodology details

## Summary

**To resume calibration:**

1. **Check credits** - Ensure you have $3-6 available
2. **Try resume first:**
   ```bash
   python src/run_scenario.py --resume scenarios/ai-2027/calibration-runs/baseline-2025-01 --credit-limit 6.00
   ```
3. **Or start fresh with budget version:**
   ```bash
   python src/run_scenario.py scenarios/ai-2027/definition-budget --max-turns 12 --credit-limit 6.00 --output scenarios/ai-2027/calibration-runs/baseline-budget-2025-01
   ```
4. **Wait 15-30 minutes**
5. **Follow QUICK-START-ANALYSIS.md**

Good luck! The framework is ready and waiting for you. 🚀
