# Proposal: keeping variants apart (and putting them together) in analysis

Handoff brief. Everything stated as verified below was checked against the code
or against the 60-run `forking-futures` ensemble on 2026-08-25; file and line
references were accurate then. Verify before relying on any of them.

## The problem

`synthesize` and `ensemble` treat every completed run under a scenario as one
undifferentiated population. Two things follow, and both bite today.

A scenario run under several conditions cannot be reported per condition.
`forking-futures` runs three trajectory arms — 20 runs each — and the ensemble
report can only speak about all 60 at once. Its own analysis had to *infer* the
arms from narrative content, which is exactly the kind of thing that should be
read off metadata.

A variant of a scenario silently contaminates the base scenario's ensemble.
This is the sharper problem. `resolve_output_base()` (`scenario_lab/cli.py:121`)
walks up from a variant YAML to the directory containing `metrics.md`, so a
variant's runs are written to the *base* scenario's `runs/`. And
`_discover_completed_runs()` (`scenario_lab/ensemble.py`) returns every `run-*`
directory there whose `summary.json` says `completed`, with no filter. So the
moment a variant is run, every later synthesis of the base scenario silently
includes it. `synthesize` offers only `--max-runs`, which selects by recency.

The current workaround is `scenarios/forking-futures-urgent/`: a sibling
scenario directory whose physics files are symlinks into the base scenario, so
it gets its own `runs/` while the two arms cannot drift apart. It works, but it
is a workaround for a missing feature.

## What already exists

- `compare-distributions` compares two explicitly listed sets of run paths
  (see `scenarios/ai-safety-race/regressions/distribution-example.yaml`).
  Statistical only, no LLM synthesis, no faceting, run lists maintained by hand.
- `model_sensitivity.py` already groups runs by LLM configuration and reports
  per-group. Its grouping code is the closest existing model for this work and
  worth reading first.

## The key fact that makes this cheap

**The grouping key is already on disk in every run.** `config.json` records:

```json
"initial_state": {
  "source": "scenarios/forking-futures/draws/fast/draw-018.json",
  "notes": "arm=fast; draw=018; regime fixed for the whole run"
}
```

All 60 existing runs carry it. Nothing needs re-running. `config.json` also
records the scenario name and the actor list, which is what distinguishes a
variant's runs from the base scenario's.

## Suggested shape

A run's cohort is derived from metadata already persisted, along at least two
axes:

- scenario identity — `config.json`'s `scenario` name and `actors`, which
  separates a variant from its base
- initial-state group — the draw's directory name, or a `key=value` parsed out
  of `initial_state.notes`

Then two CLI surfaces on `synthesize` (and `ensemble`):

- `--filter <key>=<value>` restricts the population
- `--group-by <key>` facets the report: per-group statistics plus a
  between-group comparison

Default behaviour with neither flag stays exactly as it is today — pooled — so
nothing existing changes.

## The hard part is the prompt, not the statistics

The 60-run synthesis logged `Prompt context density: minimal`; it was already
shedding detail to fit. Faceting three groups makes that worse. Decide early
whether a grouped synthesis means *one* call carrying per-group statistics plus
a comparison instruction, or *N* per-group syntheses plus a stitching pass.
That decision shapes the whole design and should be settled before code.

## Constraints

- `AGENTS.md`: this changes system behaviour, so `docs/ARCHITECTURE.md` is
  ground truth and gets updated as part of the work.
- Keep Python on orchestration and bookkeeping. Which runs form a cohort is
  bookkeeping; what the difference between cohorts *means* is an LLM judgment
  and belongs in the prompt.
- `scenarios/forking-futures/` has 60 completed runs and
  `scenarios/forking-futures-urgent/` has 9. Between them they are a ready-made
  test case for both axes: three arms within one scenario, and two scenarios
  differing by one actor file.

## Related work already done

- The occurred-events record now includes repeatable events, and the events
  prompt receives a turn-stamped `event_history`. See `docs/ARCHITECTURE.md`
  and `tests/test_occurred_events_record.py`.
- Runs completed before that change hold an incomplete `occurred_events` in
  `summary.json`. Per-run analysis reads the turn artifacts instead and is
  unaffected; anything new that reads the ledger directly should do the same.
