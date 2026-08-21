# Scenario Lab Roadmap

This document captures a prioritized roadmap for improving Scenario Lab while preserving the core design in [ARCHITECTURE.md](ARCHITECTURE.md).

The guiding principle is simple:

- Prioritize improvements that strengthen `run -> inspect -> compare -> iterate`.
- Treat Mirofish-inspired ideas mainly as improvements to ingest, analysis, visualization, and UX.
- Avoid changes that weaken the pure LLM architecture by moving scenario logic into Python.

## Pre-release Checklist

These items must be completed before any public or semi-public release.

### Must-do

- [ ] Clean up the scenarios directory so only polished, tested scenarios remain.
- [ ] Review and tighten all documentation so it reads coherently to a new user.
- [x] Revisit batch analysis features and make sure they work in a meaningful way (2026-08: the `synthesize` command). Still needs validating at volume – see "Now" item 1.
- [ ] Run a proper test batch: ~50 simulations of the same scenario, including at least one run with non-budget LLMs.

### Nice to Have

- [ ] Videos showing how to use the tool and what you get out of it.
- [x] Better workflow for creating new scenarios (2026-07: `create-scenario` skill + `describe` command; 2026-08: `frame-scenario` skill for question framing and research).
- [ ] Graphical user interface.
- [ ] Support for running local LLMs.

---

## Prioritization Lens

Each candidate improvement should be judged against four questions:

1. Does it improve simulation quality or reliability?
2. Does it make runs easier to inspect, compare, and learn from?
3. Does it reduce scenario-authoring friction without obscuring the scenario spec?
4. Does it preserve the architecture described in [ARCHITECTURE.md](ARCHITECTURE.md)?

In practice, this implied the following order of importance:

1. Core robustness and evals
2. Run analysis and comparison
3. Scenario authoring and ingest
4. Provider and operational ergonomics
5. Richer product/workbench layers

As of 2026-08 all five are substantially built (see "Shipped"). The pipeline
now runs end to end: frame a question, draft a scenario, run it fifty times,
and get a synthesized answer. The binding constraint has moved from missing
capability to unverified capability – almost none of this has been exercised
at volume. Judge current candidates primarily by whether they tell us where
the pipeline actually breaks.

## Shipped

These items were on earlier versions of this roadmap and are now implemented. They are kept here, condensed, so the sequence of the project stays legible.

- **First-class regression and eval loop** ✅ (2026-06) – `check-run-integrity` for strict structural validation of saved runs, `check-regressions` for manifest-driven pairwise comparison, `compare-distributions` for distribution-level comparison across sets of runs, and `quality-check` as the combined entry point. Backed by `scenario_lab/regression.py` and fixtures under `tests/fixtures/regression/`.
- **Run comparison and branch analysis** ✅ – `compare-runs` diffs final metrics, per-turn metrics, occurred events, rules versions, and cost between any two saved runs; `--fail-on-diff` makes it scriptable. `branch` plus seed control makes matched-pair comparison possible, and `causal-impact` builds on it.
- **Stronger scenario linting and smoke tests** ✅ – `validate` covers structure, metric ranges, event probability formulas, and actor content warnings; `describe` gives the one-page overview; the `create-scenario` skill adds a cheap smoke run with an explicit behavioral checklist.
- **Better provider abstraction and operational ergonomics** ✅ (2026-04) – `ModelRoute(provider, model)`, an `LLMProvider` ABC with OpenRouter and Anthropic implementations, lazy `ProviderRegistry`, `FallbackRouter` with per-route retries, per-provider pricing caches, and Anthropic prompt caching with correct 1.25x/0.1x cost multipliers (2026-07).
- **Ingest pipeline from source material to scenario draft** ✅ (2026-07) – the `create-scenario` skill: ingest, framing checkpoint, ordered drafting, validation, smoke test, assumption logging in `design-notes.md`. Deliberately built agent-side rather than as engine code, so the engine stays thin.
- **Cross-run synthesis** ✅ (2026-08) – the `synthesize` command (`scenario_lab/synthesis.py`) joins the two halves of batch analysis: it ensures every completed run has a structured `analysis.json` (generating missing ones in parallel, reusing the rest), then makes one LLM call over those readings grounded in `ensemble`'s statistics. Reports outcome patterns with run counts and exemplar runs, recurring turning points, actor dynamics, one-off surprises, and which apparent findings may be simulation artifacts. `--dry-run` shows the cost shape before any call. Closes the "revisit batch analysis features" pre-release item.
- **Declarable research questions** ✅ (2026-08) – a `research_questions:` block in `scenario.yaml` records what the scenario exists to answer. `validate` errors on questions naming metrics or events that do not exist, which catches an unanswerable question before runs are spent on it; `describe` shows them; `synthesize` answers each explicitly with a frequency, the conditions the answer depends on, and evidencing runs, before reporting anything undeclared.
- **Question framing and research front-end** ✅ (2026-08) – the `frame-scenario` skill covers the two stages before drafting: refining a rough topic into a research question that passes seven explicit criteria (simulable, bounded, paced, populated, measurable, genuinely uncertain, open), then building a provenance-tagged information bank in `source-material/` with an `INDEX.md` and a known-gaps list. Hands off to `create-scenario`, which now skips its own framing checkpoint when `research-question.md` is present.

## Now

The engine, the quality loop, the authoring path, and the synthesis layer are all now in place. What remains is finding out how well they hold up in use.

### 1. Field-Test the Full Pipeline

**Priority:** Highest  
**Type:** Process  
**Why it matters:** Everything from question to answer now exists on paper, and almost none of it has been exercised end to end. Skills fail in ways code does not – checkpoints that feel bureaucratic, questions that miss what actually mattered, criteria that pass a bad question. Synthesis has its own failure modes that only show up at volume: reports that read plausibly but launder one run's analysis into a claim about the ensemble, or that miss the interesting minority entirely.

**What this means:**

- Build two or three scenarios end to end from a bare question, through `frame-scenario`, `create-scenario`, `batch-run`, and `synthesize`.
- At volume, check the synthesis against the runs by hand: are the counts right, do the exemplar runs actually show what is claimed, does it notice the outliers?
- Record where the pipeline asked the wrong thing, defaulted badly, or produced confident nonsense, and tighten against what actually went wrong.

**Note:** This also covers the pre-release checklist's "~50 simulations of the same scenario" item, which is the natural test bed for synthesis at volume.

### 2. Synthesis Quality Evals

**Priority:** High  
**Type:** Core Scenario Lab  
**Why it matters:** Synthesis is the one part of the pipeline whose output cannot be checked structurally. A per-run analysis can be compared against the run's artifacts; a synthesis claim about "14 of 20 runs" can only be checked by counting, which nothing currently does.

**What this means:**

- Verify mechanically what can be verified: do frequencies cited in a synthesis match the ensemble statistics, do named runs exist, do claimed events appear in those runs?
- Treat unverifiable-but-checkable claims as the eval target, not the prose quality.

**Likely scope:**

- A checker that cross-references a `synthesis.json` against `ensemble` output and the per-run analyses it drew on
- Fixture ensembles with known properties, where the right answer is established in advance
- Extension of `quality-check` to cover synthesis output where present

## Next

### 3. Better Visualization for Runs and Branches

**Priority:** Medium-High  
**Type:** Mirofish-inspired  
**Why it matters:** Visualization is one of the most practical ways to make Scenario Lab more usable without changing its core model. It improves both research workflows and communication with others.

**What this means:**

- Make it easier to see trajectories, divergence points, and causal stories.
- Support both single-run analysis and side-by-side run comparison.
- Expose information already present in artifacts rather than inventing a new abstraction layer.

**Likely scope:**

- Metric trajectory charts, including ensemble percentile bands
- Event timelines
- Rule evolution views
- Branch divergence views
- Cost and token usage charts

**Why this is after synthesis:** Good visualization should sit on top of stable structured aggregation, not compensate for its absence.

### 4. Thin Scenario Workbench

**Priority:** Medium  
**Type:** Mixed  
**Why it matters:** Once synthesis, analysis, and ingest are stronger, a thin workbench can unify the workflow into something much easier to use. The important constraint is that this should remain a thin layer over existing primitives, not a heavyweight platform rewrite.

**What this means:**

- Provide a clearer end-to-end workflow for creating, validating, running, comparing, and branching scenarios.
- Package the current power-user flow into a more guided experience.
- Preserve CLI-first correctness and transparency.

**Likely scope:**

- A single entry point spanning frame → draft → validate → run → synthesize
- Faster quick-run and compare loops
- Graphical interface, if the pre-release checklist item is pursued

**Why this is later:** The workbench becomes much more valuable after the underlying authoring and analysis capabilities are mature enough to deserve a front door.

## Later

### 5. Analyst Assistant over Saved Runs

**Priority:** Medium-Low  
**Type:** Mirofish-inspired  
**Why it matters:** Scenario Lab already stores the evidence required for a helpful analyst layer. A question-answering assistant over run artifacts could reduce the cognitive load of interpreting long simulations.

**What this means:**

- Let a user ask ad-hoc questions about one or more saved runs, beyond the declared research questions.
- Ground answers in persisted artifacts rather than vague memory.

**Likely scope:**

- Queries like "why did unemployment rise in run B but not run A?"
- Artifact-grounded summaries with links to relevant turns or files

**Architectural constraint:** This should be a reader and analyst, not a second orchestrator or a hidden rule engine.

**Relationship to synthesis:** Largely the interactive form of the same capability. Now that `synthesize` exists, this is a much smaller job: the same artifacts, asked ad hoc rather than in one pass.

### 6. Local Model Endpoints

**Priority:** Low-Medium  
**Type:** Operational  

The provider abstraction was built to accommodate this: a third provider type for Ollama or vLLM slots into `LLMProvider` and `ProviderRegistry` without touching the router. Mainly useful for cheap high-volume batches and for running scenarios with sensitive material.

### 7. Optional Public-Sphere or Social-Dynamics Modules

**Priority:** Low / Experimental  
**Type:** Mirofish-inspired  
**Why it matters:** For some scenarios, social diffusion and public-reaction dynamics could add real value. But this is domain-specific and should not become the assumed core model for Scenario Lab.

**What this means:**

- Add richer public-opinion or media-dynamics patterns only where they materially improve a scenario.
- Treat these as optional scenario-level modules or templates.
- Avoid reshaping the whole framework around a Twitter/Reddit-style simulation model.

**Why this is last:** It is the easiest category to overbuild.

## Backlog from the 2026-07 Epistemics Review

A review of how well the engine models genuine uncertainty produced four shipped improvements (emergent events, multi-sample probability elicitation, the `causal-impact` command, GM friction guidance + narrative-diversity stats) and three ideas deliberately left for later:

- **Established-facts canon against summarization drift.** All long-term memory flows through the historical summary (re-condensed every turn) and the notepad (REPLACE semantics), so load-bearing facts can silently vanish over 10+ turns. Idea: an append-only "established facts" list that the summarization step may add to but not delete, injected into prompt context. Left undone because it changes the summarize output contract and can only be verified with real runs.
- **Probability calibration vignettes.** The evals test event-condition *logic*, but nothing tests whether elicited probabilities are *calibrated*. Idea: a small set of human-anchored reference vignettes with agreed probability ranges, run against candidate event models.
- **Human-in-the-loop mode.** Let a human play one actor or approve/steer between turns, on top of the existing pause/resume machinery. Connects the tool to live scenario exercises with clients rather than only Monte Carlo automation.

## Recommended Sequence

1. Field-testing the full pipeline end to end, at volume
2. Synthesis quality evals
3. Visualization on top of stable aggregation
4. Thin workbench over the whole flow
5. Optional product layers: analyst assistant, local models, social-dynamics modules

## What to Avoid

The following patterns are tempting, but should generally be avoided:

- Moving more scenario logic into Python in the name of product features
- Building a large frontend before comparison and analysis are strong
- Making social-media-style simulation the default model for all scenarios
- Introducing heavy platform complexity before the current artifact model is fully leveraged

## Summary

The best way for Scenario Lab to learn from Mirofish is not to copy its entire shape. The high-value lessons are:

- reduce authoring friction
- improve analytical usability
- visualize simulation results better
- make practical operation smoother

The parts that should remain distinctly Scenario Lab are:

- explicit scenario specs
- strong artifact persistence
- inspectable turn-by-turn evolution
- a pure LLM simulation architecture with lightweight Python orchestration
