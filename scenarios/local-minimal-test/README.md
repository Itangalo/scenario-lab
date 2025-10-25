# Minimal Local LLM Test

Ultra-lightweight 1-turn scenario for testing local LLM integration without overheating your Mac.

## Specifications

- **Actors:** 2 (Actor A, Actor B)
- **Turns:** 1 (minimum possible)
- **Model:** Only DeepSeek R1:8b (the smaller, faster model)
- **Topic:** Simple compute threshold negotiation
- **Expected runtime:** 1-2 minutes
- **Cost:** $0

## Hardware Requirements

- **Minimum:** M1 MacBook Air with 16GB RAM
- **Temperature:** Wait for Mac to cool down before running
- **Cooling:** Ensure good ventilation

## Running the Test

```bash
# 1. Make sure your Mac has cooled down
# 2. Start Ollama
brew services start ollama

# 3. Wait a few seconds for Ollama to start
sleep 5

# 4. Run minimal test
python src/run_scenario.py scenarios/local-minimal-test
```

## Expected Output

```
output/local-minimal-test/run-001/
├── world-state-001.md  (initial)
├── world-state-002.md  (final)
├── actor-a-001.md
├── actor-b-001.md
├── metrics.json
└── cost-summary.json  ($0.00)
```

## What This Tests

✅ Local model routing works
✅ DeepSeek R1:8b handles decisions
✅ World state synthesis with local model
✅ Complete scenario runs without errors
✅ Cost tracking shows $0

## If It Still Overheats

Your MacBook Air may not have adequate cooling for sustained LLM inference. Options:

1. **Use cloud models** - stick with `openai/gpt-4o-mini`
2. **Better hardware** - Mac Studio, or desktop with GPU
3. **Short bursts** - run 1 turn at a time, let Mac cool between runs

The framework fully supports both - no limitations!
