# Regression Fixtures

These fixtures provide small saved-run examples for:

- `check-run-integrity`
- `check-regressions`
- `compare-distributions`

Example commands from the repository root:

```bash
python -m scenario_lab.cli check-run-integrity tests/fixtures/regression/pairwise/run-baseline
python -m scenario_lab.cli check-regressions tests/fixtures/regression/pairwise-regressions.yaml
python -m scenario_lab.cli compare-distributions tests/fixtures/regression/distribution-comparison.yaml
```
