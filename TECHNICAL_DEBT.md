# Technical Debt

Items that need attention for improved robustness, quality, and maintainability.

## High Priority

### 1. Markdown Formatting Issues ✅ COMPLETED

**Status:** Implemented content-aware deduplication and validation

**Implementation:**
- ✅ Content similarity detection using SequenceMatcher
- ✅ Section content extraction for analysis
- ✅ Duplicate content detection (ACTION containing GOALS/REASONING)
- ✅ Embedded duplicate removal (extracting clean ACTION from full response)
- ✅ Duplicate section header removal
- ✅ Header normalization (CAPS → Proper Case)
- ✅ Excessive blank line removal
- ✅ 10 comprehensive tests for deduplication logic

**Files Modified:**
- `src/markdown_utils.py`: Added 5 new functions for content deduplication
  - `text_similarity()` - Calculate text similarity (0.0-1.0)
  - `extract_section_content()` - Extract content from specific sections
  - `detect_content_duplication()` - Detect if ACTION contains GOALS/REASONING
  - `remove_embedded_duplicates()` - Clean ACTION section of embedded content
  - `clean_markdown_formatting()` - Enhanced with content deduplication
- `tests/test_markdown_utils.py`: 10 new tests for deduplication features

**Result:** 150/150 tests passing. Markdown output now automatically cleaned of duplicates.

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

### 3. API Error Handling ✅ COMPLETED

**Status:** Implemented comprehensive error handling with retry logic

**Implementation:**
- ✅ Exponential backoff for 502, 503, 504, 429 errors (default max 3 retries)
- ✅ Retry-After header support for rate limiting
- ✅ Structured logging with contextual information (actor, turn, operation)
- ✅ Response body logging for debugging (first 500 chars)
- ✅ Distinction between transient and permanent failures
- ✅ Network error retry (connection failures, timeouts)
- ✅ Context parameter for tracking operation details
- ✅ 11 new integration tests verifying retry behavior

**Files Modified:**
- `src/api_utils.py`: Enhanced retry logic with logging and context
- `tests/test_api_error_handling.py`: 11 comprehensive tests

**Result:** 140/140 tests passing. Scenarios now gracefully handle transient API failures.

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

### 6. Integration Tests ✅ COMPLETED

**Status:** Comprehensive integration test coverage implemented

**Current Coverage:**
- Unit tests: WorldState, CommunicationManager, ContextManager, CostTracker, etc. (129 tests)
- Integration tests: Execution, resumption, branching, communications, credit limits (5 tests)
- API error handling tests: Retry logic, rate limiting, network errors (11 tests)
- Markdown deduplication tests: Content similarity, extraction, validation (10 tests)

**Completed:**
- ✅ Mock LLM provider for deterministic testing
- ✅ Full scenario execution test (multi-actor, multi-turn)
- ✅ Resumption workflow test (halt and resume)
- ✅ Branching workflow test
- ✅ API error recovery tests
- ✅ Bilateral communication integration test
- ✅ Credit limit enforcement test

**New Tests Added:**
- `TestBilateralCommunications` - Verifies bilateral negotiation workflow
- `TestCreditLimitEnforcement` - Verifies scenario halts when credit limit reached

**Remaining Gaps:**
- Performance tests for large scenarios (low priority)
- Coalition formation with actual coalition responses (medium priority)

**Impact:** All core workflows have end-to-end test coverage.

**Result:** 152/152 tests passing (2 new integration tests)

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

### 10. Logging and Debugging ✅ COMPLETED

**Status:** Comprehensive structured logging implemented

**Implementation:**
- ✅ Proper logging module with ColoredFormatter
- ✅ Log levels (DEBUG, INFO, WARNING, ERROR) with colors
- ✅ Structured logging throughout codebase
- ✅ API calls logged with context (actor, turn, operation)
- ✅ Optional verbose mode (--verbose flag)
- ✅ File logging (scenario.log in run directories)
- ✅ Specialized logging functions (log_section, log_actor_decision, etc.)

**Files Modified:**
- `src/logging_config.py`: Complete logging infrastructure
- `src/run_scenario.py`: Replaced 76 print statements with logging
- `src/api_utils.py`: API error logging with context

**Result:** Comprehensive logging for debugging and monitoring.

---

## Summary

**Completed Items:** ✅
1. ✅ API Error Handling - Comprehensive retry logic with exponential backoff
2. ✅ Logging and Debugging - Structured logging throughout codebase
3. ✅ Markdown Formatting Issues - Content-aware deduplication and validation
4. ✅ Integration Tests - Comprehensive end-to-end test coverage
5. ✅ Response Parsing Robustness (Partial) - Enhanced with 4 pattern formats and diagnostics

**Remaining High Priority:**
1. Enhanced Scenario Specification (Phase 1 completion)

**Remaining Medium Priority:**
2. Duplicate Content Detection (token efficiency) - Mostly addressed by markdown deduplication

**Remaining Low Priority:**
3. Metrics Extraction Improvements
4. Cost Estimation Accuracy
5. Performance tests for large scenarios
6. Coalition formation integration tests (with full coalition responses)

**Progress:** ~22-28 hours completed, ~15-20 hours remaining

**Next Recommended Steps:**
1. Enhanced Scenario Specification - JSON Schema validation for YAML files
2. Metrics Extraction Improvements - LLM-based extraction as fallback
