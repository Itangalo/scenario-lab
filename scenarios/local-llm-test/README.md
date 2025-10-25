# Local LLM Test Scenario

This is a simple 2-actor, 3-turn test scenario to verify local LLM functionality with Ollama.

## Purpose

Test that Scenario Lab works correctly with local models before running expensive batch runs on cloud APIs.

## Models Used

- **World State:** `ollama/deepseek-r1:8b` (excellent reasoning for synthesis)
- **United States:** `ollama/deepseek-r1:8b` (strategic decision-making)
- **European Union:** `ollama/qwen2.5:14b` (complex policy reasoning)

## Running the Test

```bash
python src/run_scenario.py scenarios/local-llm-test
```

**Expected runtime:** ~2-5 minutes (depending on your Mac's performance)

**Cost:** $0 (completely free!)

## What You're Testing

- ✅ Local LLM routing works correctly
- ✅ DeepSeek R1:8b handles actor decisions
- ✅ Qwen 2.5:14b handles complex reasoning
- ✅ World state synthesis with local models
- ✅ All scenario features work without cloud API

## Expected Output

```
output/local-llm-test/run-001/
├── world-state-001.md
├── world-state-002.md
├── world-state-003.md
├── world-state-004.md  (final state)
├── united-states-001.md
├── united-states-002.md
├── united-states-003.md
├── european-union-001.md
├── european-union-002.md
├── european-union-003.md
├── metrics.json
└── cost-summary.json  (should show $0 cost)
```

## Performance Notes

On M1 MacBook Air with 16GB RAM:
- **DeepSeek R1:8b:** ~20-30 tokens/sec
- **Qwen 2.5:14b:** ~10-15 tokens/sec (larger model, slower but better quality)

First turn will be slower as models load into memory.

## After Testing

If this works correctly, you can:

1. **Use for development:** Test scenario changes without API costs
2. **Run batch experiments:** 100 local runs = $0 vs ~$40 with cloud
3. **Mix configurations:** Local for actors, cloud for world state
4. **Scale up:** Try larger scenarios with more actors

See `docs/LOCAL_LLMS.md` for full documentation.
