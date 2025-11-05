# AI 2027 - Budget Version

This is a cost-optimized version of the AI 2027 scenario, designed for exploratory runs, testing, and batch analysis where cost efficiency is important.

## Cost Optimization

**Model Distribution:**
- **gpt-4o (premium):** 3 actors (43%)
  - OpenBrain CEO - Critical decision-maker driving AI development
  - DeepCent CEO - Key competitor influencing race dynamics
  - US President - High-level government policy decisions

- **gpt-4o-mini (cost-efficient):** 4 actors (57%)
  - OpenBrain Alignment Lead - Technical safety expert
  - US AI Advisor - Technical policy advisor
  - CCP Secretary - Chinese government leadership
  - Independent Alignment Researcher - External safety advocate

**Cost Savings:**
- Approximately **40% reduction** in API costs compared to the premium version
- Still maintains high-quality decisions for the most influential actors
- Ideal for batch runs, sensitivity analysis, and exploratory experiments

## When to Use This Version

✅ **Good for:**
- Exploratory runs and testing
- Batch analysis with many variations
- Initial scenario exploration
- Budget-constrained research
- Comparing model performance (does gpt-4o-mini produce similar results?)

❌ **Consider premium version for:**
- Final research publications
- High-stakes analysis requiring maximum quality
- Detailed expert review of actor decisions
- Presentations or demonstrations requiring best output

## Running the Budget Version

```bash
# Single run
python src/run_scenario.py scenarios/ai-2027/definition-budget/scenario.yaml

# With limits (recommended for testing)
python src/run_scenario.py scenarios/ai-2027/definition-budget/scenario.yaml --max-turns 12 --credit-limit 5

# Resume
python src/run_scenario.py --resume scenarios/ai-2027/runs/run-001
```

## Estimated Costs

**Per full run (66 turns):**
- Premium version (all gpt-4o): ~$8-12
- Budget version (this): ~$5-7
- **Savings:** ~$3-5 per run (40%)

**For batch analysis (12 runs):**
- Premium: ~$96-144
- Budget: ~$60-84
- **Savings:** ~$36-60 per batch

**Note:** Actual costs vary based on context length, response length, and caching effectiveness. Use `--dry-run` for accurate estimates.

## Comparison with Premium Version

Research question: Do the cheaper models produce qualitatively similar outcomes?

You can test this by running both versions and comparing:
```bash
# Run premium version
python src/run_scenario.py scenarios/ai-2027/definition/scenario.yaml --max-turns 20

# Run budget version
python src/run_scenario.py scenarios/ai-2027/definition-budget/scenario.yaml --max-turns 20

# Compare metrics and decision quality
```

Early testing suggests that gpt-4o-mini performs well for most actors, with differences primarily in prose style rather than strategic decision-making.

## See Also

- Main README: `scenarios/ai-2027/README.md`
- Premium version: `scenarios/ai-2027/definition/`
- Example batch config: `scenarios/ai-2027/example-batch-config.yaml`
