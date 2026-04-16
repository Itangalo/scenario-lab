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
- [ ] Revisit batch analysis features and make sure they work in a meaningful way — likely requires some development work.
- [ ] Run a proper test batch: ~50 simulations of the same scenario, including at least one run with non-budget LLMs.

### Nice to Have

- [ ] Videos showing how to use the tool and what you get out of it.
- [ ] Better workflow for creating new scenarios.
- [ ] Graphical user interface.
- [ ] Support for running local LLMs.

---

## Prioritization Lens

Each candidate improvement should be judged against four questions:

1. Does it improve simulation quality or reliability?
2. Does it make runs easier to inspect, compare, and learn from?
3. Does it reduce scenario-authoring friction without obscuring the scenario spec?
4. Does it preserve the architecture described in [ARCHITECTURE.md](ARCHITECTURE.md)?

In practice, this implies the following order of importance:

1. Core robustness and evals
2. Run analysis and comparison
3. Scenario authoring and ingest
4. Provider and operational ergonomics
5. Richer product/workbench layers

## Now

These items should be prioritized first because they directly improve confidence, iteration speed, and the practical usefulness of the existing engine.

### 1. First-Class Regression and Eval Loop

**Priority:** Highest  
**Type:** Core Scenario Lab  
**Why it matters:** Scenario Lab lives or dies on whether changes make runs better, not just different. The project already has tests and evals, but the next level of maturity is a clearer quality loop that catches behavioral regressions, prompt drift, parsing instability, and silent cost creep.

**What this means:**

- Define a set of reference scenarios and cheap reference runs.
- Track changes in key outputs across commits: metrics, events, rule updates, constitutional interventions, and total cost.
- Make it easy to detect when a prompt or parser change unexpectedly shifts behavior.
- Add scenario-quality evals, not just code correctness tests.

**Likely scope:**

- Golden-run fixtures or sampled baseline outputs
- Diff tooling for run artifacts
- Cost and token-budget regression checks
- Prompt/eval dashboards or summaries in CI or CLI

**Why this comes first:** It compounds with every later improvement. Without it, the roadmap increases complexity faster than confidence.

### 2. Run Comparison and Branch Analysis

**Priority:** Highest  
**Type:** Core Scenario Lab  
**Why it matters:** Scenario Lab already stores rich artifacts, but comparing two runs is still more manual than it should be. The project's strongest differentiator is not just generation, but inspectable divergence over time.

**What this means:**

- Add first-class support for comparing two runs, two variants, or a parent run against a branch.
- Surface where trajectories diverged and which events, actor actions, or rule changes appear to explain the difference.
- Make comparison output useful both for CLI users and later visualization/reporting layers.

**Likely scope:**

- `compare` CLI command for runs or branches
- Structured diffs for metric trajectories, occurred events, actor actions, and rule versions
- Outcome summaries such as "largest divergences by turn" or "branch point effects"

**Why this comes first:** This turns existing persistence into actual analytical leverage.

### 3. Stronger Scenario Linting and Smoke Tests

**Priority:** High  
**Type:** Core Scenario Lab  
**Why it matters:** A lot of simulation failures are not code bugs. They come from weak scenario definitions, ambiguous prompts, unbalanced metrics, or event logic that looks valid but behaves badly in practice. Better pre-run feedback saves both cost and iteration time.

**What this means:**

- Strengthen validation of metrics, events, constitutions, actor references, and prompt assumptions.
- Add a lightweight smoke-test path for new scenarios.
- Detect common scenario design problems before a full run.

**Likely scope:**

- Validation warnings for over-broad event conditions, impossible metric dynamics, or unstable prompt contracts
- A cheap `quick-check` or improved `validate` mode that runs one or two short low-cost turns
- Better actionable diagnostics when a scenario is technically valid but likely low quality

**Why this comes first:** The authoring loop is still a major bottleneck, and this improves it without major architectural risk.

## Next

These items should follow once the quality loop and run comparison story are stronger. They create leverage for users without destabilizing the engine.

### 4. Richer Analysis Layer on Top of Run Output

**Priority:** High  
**Type:** Core with some Mirofish inspiration  
**Why it matters:** Scenario Lab already produces good raw material, but the user still has to synthesize a lot manually. A stronger analysis layer would convert saved artifacts into insight more quickly.

**What this means:**

- Generate higher-level summaries of what drove outcomes.
- Highlight turning points, surprising events, actor bottlenecks, and rule shifts.
- Help users answer "what happened?" and "why did this outcome emerge?" without re-reading every file.

**Likely scope:**

- Auto-generated run reports
- Outcome-driver summaries
- Turn highlight extraction
- Branch comparison narratives

**Why this is not first:** It builds on the comparison and eval foundations. Without those, the analysis layer risks becoming polished but unreliable.

### 5. Ingest Pipeline from Source Material to Scenario Draft

**Priority:** High  
**Type:** Mirofish-inspired  
**Why it matters:** This is the strongest idea to borrow from Mirofish. Scenario Lab is powerful once a scenario exists, but the jump from raw source material to a good scenario spec is still expensive in human attention.

**What this means:**

- Accept raw material such as markdown, text, notes, or PDFs.
- Use that material to propose a first-pass scenario scaffold.
- Help a user move from research input to editable scenario files more quickly.

**Likely scope:**

- Draft generation for `scenario.yaml`, `metrics.md`, `events.md`, `metric-rules.md`, and actor/background files
- Confidence flags such as "missing actors," "weak metrics," or "events need human review"
- A workflow explicitly positioned as assisted authoring, not push-button truth generation

**Architectural constraint:** The output should still be explicit scenario files that humans can inspect and edit. The ingest layer should not become a hidden second source of truth.

### 6. Better Visualization for Runs and Branches

**Priority:** Medium-High  
**Type:** Mirofish-inspired  
**Why it matters:** Visualization is one of the most practical ways to make Scenario Lab more usable without changing its core model. It improves both research workflows and communication with others.

**What this means:**

- Make it easier to see trajectories, divergence points, and causal stories.
- Support both single-run analysis and side-by-side run comparison.
- Expose information already present in artifacts rather than inventing a new abstraction layer.

**Likely scope:**

- Metric trajectory charts
- Event timelines
- Rule evolution views
- Branch divergence views
- Cost and token usage charts

**Why this is later than comparison:** Good visualization should sit on top of stable structured comparison data, not compensate for its absence.

## Later

These items are valuable, but they should follow after the engine, comparison layer, and authoring workflow are clearly stronger.

### 7. Better Provider Abstraction and Operational Ergonomics ✅ Done

**Status:** Implemented (2026-04).

**What was built:**

- `ModelRoute(provider, model)` replaces bare model strings everywhere. YAML syntax: `"openrouter:x-ai/grok-4.1-fast"`, `"anthropic:claude-sonnet-4-6"`.
- `LLMProvider` ABC with `OpenRouterProvider` (httpx) and `AnthropicProvider` (official SDK).
- `ProviderRegistry` creates providers lazily, so only keys for providers actually used need to be set.
- `FallbackRouter` replaces the old in-class fallback loop: ordered routes, per-route retries with backoff, falls through on non-retryable errors.
- Provider-specific pricing caches: `OpenRouterPricingCache` (unchanged) and `AnthropicPricingCache` (LiteLLM catalog + bundled seed). `get_pricing_for(route)` dispatches to the right one.
- `TokenUsage` gains a `provider` field so cost calculation uses the correct pricing cache.
- `refresh-pricing` now refreshes both caches; `--provider` scopes to one.

**Follow-up items:**

- [ ] Prompt caching support for Anthropic (use `cache_creation_input_tokens` / `cache_read_input_tokens` already tracked in `TokenUsage`).
- [ ] Support for local model endpoints (Ollama, vLLM) as a third provider type.

### 8. Thin Scenario Workbench

**Priority:** Medium  
**Type:** Mixed  
**Why it matters:** Once comparison, analysis, and ingest are better, a thin workbench can unify the workflow into something much easier to use. The important constraint is that this should remain a thin layer over existing primitives, not a heavyweight platform rewrite.

**What this means:**

- Provide a clearer end-to-end workflow for creating, validating, running, comparing, and branching scenarios.
- Package the current power-user flow into a more guided experience.
- Preserve CLI-first correctness and transparency.

**Likely scope:**

- Wizard or guided workflow for new scenarios
- Faster quick-run and compare loops
- Unified entry point for common tasks

**Why this is later:** The workbench becomes much more valuable after the underlying authoring and analysis capabilities are mature enough to deserve a front door.

### 9. Analyst Assistant over Saved Runs

**Priority:** Medium-Low  
**Type:** Mirofish-inspired  
**Why it matters:** Scenario Lab already stores the evidence required for a helpful analyst layer. A question-answering assistant over run artifacts could reduce the cognitive load of interpreting long simulations.

**What this means:**

- Let a user ask questions about one or more saved runs.
- Ground answers in persisted artifacts rather than vague memory.
- Focus on explanation and analysis, not on creating new simulation state.

**Likely scope:**

- Queries like "why did unemployment rise in run B but not run A?"
- Artifact-grounded summaries with links to relevant turns or files
- Report mode for key findings across repeated runs

**Architectural constraint:** This should be a reader and analyst, not a second orchestrator or a hidden rule engine.

### 10. Optional Public-Sphere or Social-Dynamics Modules

**Priority:** Low / Experimental  
**Type:** Mirofish-inspired  
**Why it matters:** For some scenarios, social diffusion and public-reaction dynamics could add real value. But this is domain-specific and should not become the assumed core model for Scenario Lab.

**What this means:**

- Add richer public-opinion or media-dynamics patterns only where they materially improve a scenario.
- Treat these as optional scenario-level modules or templates.
- Avoid reshaping the whole framework around a Twitter/Reddit-style simulation model.

**Likely scope:**

- Reusable scenario templates for public sentiment dynamics
- Better handling of information cascades, media amplification, or backlash loops
- Scenario-specific prompt/tooling support

**Why this is last:** It is the easiest category to overbuild. It can be valuable, but it does not improve the baseline framework for most scenarios as much as comparison, evals, or ingest do.

## Recommended Sequence

If implemented in phases, the recommended order is:

### Phase 1: Strengthen the Core

1. First-class regression and eval loop
2. Run comparison and branch analysis
3. Stronger scenario linting and smoke tests

### Phase 2: Increase Analytical Leverage

4. Richer analysis layer on top of run output
5. Better visualization for runs and branches

### Phase 3: Lower Creation and Usage Friction

6. Ingest pipeline from source material to scenario draft
7. ~~Better provider abstraction and operational ergonomics~~ ✅
8. Thin scenario workbench

### Phase 4: Add Optional Product Layers

9. Analyst assistant over saved runs
10. Optional public-sphere or social-dynamics modules

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
