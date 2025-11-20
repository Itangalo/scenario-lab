# V2-Only Migration Plan

This document outlines the steps required to make Scenario Lab purely V2. The goal is to remove remaining V1 dependencies, ensure the tests rely only on the new architecture, and deliver a consistent developer experience.

## 1. Core principles
- V1 components (legacy `src/*` modules) should no longer be imported anywhere under `scenario_lab/` or tests.
- All execution flows (CLI, runners, tests) must use the same V2 pipeline. For now we can build a minimal pipeline that hits the essential phases (decision, world update, persistence) and stubs/defers others.
- Tests should rely on internal fixtures/helper classes in `scenario_lab` rather than patching into `src`. The new test fixtures should create scenario directories compatible with the V2 schemas.

## 2. Loader and schema alignment
- Use `scenario_lab/schemas/...` exclusively. The loader should:
  - Read `scenario.yaml` and `actors/*.yaml`.
  - Validate them using the Pydantic V2 schemas.
  - Build immutable `ScenarioState` instances with the scenario config attached for later phases.
- Any old helper (e.g. `load_scenario_config` in `src/schemas.py`) must be removed from import paths inside the V2 code.

## 3. Decision phase
- Implement a native V2 `DecisionPhase` that:
  - Builds prompts from the scenario configuration and current state.
  - Calls the shared `make_llm_call` helper (from `api_utils`) or any other V2-friendly LLM client.
  - Parses responses with `scenario_lab.utils.json_response_parser` and records costs via `scenario_lab.utils.model_pricing`.
- Tests for `DecisionPhase` should patch `make_llm_call` rather than using V1 Actor classes.

## 4. World update phase
- Provide a V2 `WorldUpdatePhase` that constructs the next world state via LLM calls similar to the decision phase.
- It should synthesize Markdown, update `ScenarioState`, and track costs.
- Tests patch `make_llm_call` and assert the prompts include actor decisions and context.

## 5. Persistence phase
- Keep `PersistencePhase` but ensure it uses only V2 types (no `.to_markdown()` from V1 world state). It should read from `ScenarioState` directly.
- Ensure `StatePersistence` serializes/deserializes `scenario_config` so resume/branch flows remain viable without accessing V1 modules.

## 6. Runner/orchestrator wiring
- Replace the V1-centric `SyncRunner` with a V2 runner that:
  - Loads the scenario via the new loader.
  - Creates `ScenarioOrchestrator` with phases from the new V2 services.
  - Supports resume/branch by consuming `StatePersistence` only.
- Remove references to `ContextManager`, `WorldStateUpdater`, `CommunicationManager`, etc., unless equivalent V2 versions exist.
- Decide whether a minimal `CommunicationPhase` will exist in V2. If not ready, defer it and adjust tests/orchestrator accordingly.

## 7. Test suite cleanup
- Update integration tests (`tests/test_v2_integration.py` etc.) so that they:
  - Always patch the new V2 phases’ LLM calls via fixtures.
  - Only create scenario directories via V2 schema-compatible YAML.
  - No longer insert legacy `src` paths.
- Update `tests/test_v2_phases.py` to use `ActorConfig` objects and the new phases.
- Drop or rewrite tests that rely on V1-specific behaviour.

## 8. Remove legacy imports
- Search for `sys.path.insert` of `src` and remove or replace with equivalent V2 functionality.
- Delete V1 modules/packages once no V2 code imports them.
- Ensure `pyproject.toml` and requirements align with the modern stack (remove old dependencies that were only for V1).

## 9. Documentation and CLI
- Update README/CLI instructions to describe the V2-only execution path.
- If CLI commands still reference V1 scripts (e.g., `run_scenario.py`), rewrite them to call the V2 runner.

## 10. Final validation
- Run `pytest` to ensure the V2 tests pass.
- Verify CLI scenarios run end-to-end using the new runner.
- Document any remaining TODOs for optional phases (communication, metrics extraction, etc.).
