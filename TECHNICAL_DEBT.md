# Technical Debt

Items that need attention for improved robustness, quality, and maintainability.

## High Priority

### 1. Markdown Formatting Issues

**Problem:** LLM responses sometimes result in duplicated content in markdown files.

**Example:** In `tech-company-002.md`, goals/reasoning/action sections appeared twice.

**Root Cause:** LLM doesn't always follow the exact format we request. Our parsing extracts sections, but if the LLM structures the response differently (e.g., puts everything in ACTION section), we get duplication.

**Impact:** Confusing output files, harder to read for experts.

**Solution Options:**
- Improve prompt to be more explicit about format
- Add post-processing to detect and remove duplicates
- Use structured output (JSON) instead of markdown parsing
- Add format validation before saving markdown

**Estimated Effort:** Medium (2-4 hours)

---

### 2. Response Parsing Robustness

**Problem:** Parsing relies on exact string matching like `"**REASONING:**"`. Minor variations break parsing.

**Current State:** We added try-except blocks, but still fragile.

**Examples:**
- `**REASONING**` (missing colon) breaks parsing
- Extra whitespace or formatting differences cause failures
- Fallback to "No structured reasoning provided" loses information

**Impact:** Lost data, less reliable extraction, debugging difficulty.

**Solution Options:**
- Use regex with flexible matching (whitespace, punctuation variations)
- Try multiple parsing strategies in sequence
- Switch to JSON mode for LLM responses (if available)
- Add fuzzy section detection

**Estimated Effort:** Medium (3-5 hours)

---

### 3. API Error Handling

**Problem:** Transient API errors (502, 429) cause scenario failures mid-run.

**Current State:** 
- 429 (rate limit) is handled with state persistence
- 502 (server error) causes immediate failure
- No retry logic for transient failures

**Impact:** Scenarios fail unnecessarily, requiring manual resumption.

**Solution Options:**
- Add exponential backoff retry for 502, 503, 504 errors
- Distinguish transient vs. permanent failures
- Log all API errors with full context
- Add max retry limit to prevent infinite loops

**Estimated Effort:** Low (1-2 hours)

---

## Medium Priority

### 4. Quality Assurance Validator (Phase 1 Incomplete)

**Problem:** No automated consistency checking for actor decisions and world states.

**Planned Features:**
- Validate actor decisions align with stated goals
- Check actions are within actor capabilities
- Verify world state updates are logically consistent
- Detect contradictions or impossible actions

**Impact:** Quality issues may go unnoticed until expert review.

**Solution:**
- Create QA validator using lightweight LLM (gpt-4o-mini)
- Run after each turn with configurable validation rules
- Generate warnings (not failures) for inconsistencies
- Export validation reports to markdown

**Estimated Effort:** High (6-8 hours)

---

### 5. Enhanced Scenario Specification

**Problem:** Limited validation of scenario YAML files. No support for validation rules or background data.

**Current Gaps:**
- No schema validation for scenario.yaml
- No validation rules support (from Phase 1 plan)
- Background data folder exists but isn't used
- Actor YAML validation is minimal

**Impact:** Invalid scenarios discovered at runtime, not during setup.

**Solution:**
- Add JSON Schema validation for all YAML files
- Implement validation rules in `validation-rules.yaml`
- Integrate background data into actor context
- Validate actor/scenario compatibility

**Estimated Effort:** High (8-10 hours)

---

### 6. Integration Tests

**Problem:** Only unit tests exist. No end-to-end scenario execution tests.

**Current Coverage:**
- Unit tests: WorldState, CommunicationManager, ContextManager, CostTracker (29 tests)
- Integration tests: None

**Gaps:**
- No tests for full scenario execution
- No tests for resumption workflow
- No tests for branching workflow
- No tests for error recovery

**Impact:** Regressions in workflow may not be caught.

**Solution:**
- Create mock LLM responses for deterministic testing
- Add tests for: basic scenario, resumption, branching, coalitions
- Test error conditions (rate limits, API failures)
- Add performance tests for large scenarios

**Estimated Effort:** High (6-8 hours)

---

### 7. Duplicate Content Detection

**Problem:** Related to #1, but broader. Actors sometimes repeat information unnecessarily.

**Examples:**
- Repeating recent world state in their reasoning
- Re-stating goals that haven't changed
- Verbose responses that could be more concise

**Impact:** Token waste, harder to read outputs.

**Solution:**
- Prompt engineering to encourage conciseness
- Post-processing to detect and flag repetition
- Context optimization to avoid redundancy

**Estimated Effort:** Medium (3-4 hours)

---

## Low Priority

### 8. Metrics Extraction Improvements

**Problem:** Regex-based metric extraction is limited and error-prone.

**Current State:** Works for simple patterns, but fragile.

**Improvements:**
- LLM-based extraction as fallback
- More sophisticated regex patterns
- Validation of extracted values
- Support for more complex metric types

**Estimated Effort:** Medium (4-5 hours)

---

### 9. Cost Estimation Accuracy

**Problem:** Pre-execution cost estimates are very rough.

**Current Issues:**
- Doesn't account for communication rounds
- Assumes fixed token counts
- No historical data used for estimation

**Impact:** Budget planning is difficult.

**Solution:**
- Track actual costs per scenario type
- Use historical averages for estimation
- Account for communication phases
- Add confidence intervals to estimates

**Estimated Effort:** Low (2-3 hours)

---

### 10. Logging and Debugging

**Problem:** Limited logging makes debugging difficult.

**Current State:** Print statements only, no structured logging.

**Improvements:**
- Add proper logging module
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Log all API calls with request/response
- Structured log format for analysis
- Optional verbose mode

**Estimated Effort:** Low (2-3 hours)

---

## Summary

**Recommended Priority Order:**
1. API Error Handling (quick win, high impact)
2. Markdown Formatting Issues (visible quality issue)
3. Response Parsing Robustness (reliability)
4. Quality Assurance Validator (Phase 1 completion)
5. Integration Tests (prevent regressions)
6. Enhanced Scenario Specification (Phase 1 completion)

**Total Estimated Effort:** ~40-50 hours for all items

**Next Steps:** Choose 2-3 high-priority items to tackle first.
