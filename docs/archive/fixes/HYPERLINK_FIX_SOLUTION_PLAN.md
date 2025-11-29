# Hyperlink Placement Fix - Solution Plan

**Date:** October 26, 2025  
**Problem:** Hyperlinks appear in wrong table cells or fallback section  
**Root Causes:** Coordinate mismatch, LLM rephrasing, label detection failures  
**Goal:** Achieve 90%+ inline placement accuracy

---

## Executive Summary

This plan implements a 3-phase approach to fix hyperlink misplacement:

1. **Phase 1 (Diagnostics):** Add comprehensive logging to identify failure patterns (2-3 hours)
2. **Phase 2 (Quick Wins):** Fix label normalization and improve fuzzy matching (3-4 hours)
3. **Phase 3 (Structural):** Enhance structure detection and validation (3-5 hours)

**Total Estimated Time:** 8-12 hours  
**Risk Level:** Low (all changes are additive with fallbacks)  
**Expected Improvement:** 40-60% → 90%+ inline placement rate

---

## Phase 1: Diagnostic Logging (2-3 hours)

### Goal
Understand exactly where and why hyperlinks fail to place correctly.

### Tasks

#### 1.1 Add Placement Tracking to `_place_hyperlink_hybrid()`

**File:** `tools/docx_renderer.py` (lines 1037-1075)

**What to add:**
- Log each strategy attempted (coordinate, label_day, fuzzy, fallback)
- Log input coordinates vs. detected structure
- Log label/day lookup results
- Log why each strategy failed

**Key metrics to capture:**
- `link_text`, `url`, `input_coords`, `row_label`, `day_hint`, `section_hint`
- `structure_type`, `strategy_attempted[]`, `result`
- `label_lookup`, `day_lookup`, `coordinate_failure`, `fuzzy_failure`

#### 1.2 Add Fuzzy Match Scoring to `_try_fuzzy_placement()`

**File:** `tools/docx_renderer.py` (lines 1148-1196)

**What to add:**
- Track best match even if below threshold
- Log confidence scores for all cells tested
- Show which cell came closest to matching

#### 1.3 Create Diagnostic Analysis Script

**File:** `tools/analyze_hyperlink_diagnostics.py` (NEW)

**Purpose:** Parse logs and generate summary report showing:
- % success rate for each strategy
- Most common row labels that fail lookup
- Structure type distribution
- Sample fallback cases with full context

#### 1.4 Run Diagnostic Test

**Steps:**
1. Process 3-5 lesson plans with known issues
2. Collect diagnostic logs
3. Run analysis: `python tools/analyze_hyperlink_diagnostics.py backend/logs/app.log`
4. Identify top 3 failure patterns

---

## Phase 2: Quick Wins (3-4 hours)

### Goal
Fix the most common failure patterns identified in Phase 1.

### Tasks

#### 2.1 Improve Label Normalization

**File:** `tools/table_structure.py`

**Changes needed:**

1. **`_build_row_map()` (lines 196-212):** Add aggressive normalization
   - Remove all punctuation: `:`, `,`, `.`, `/`, `&`
   - Collapse whitespace
   - Store multiple variations of each label

2. **`get_row_index()` (lines 24-43):** Match with same normalization
   - Apply same cleaning to input label
   - Try exact match, then compact match, then pattern match
   - Add partial matching as last resort

**Expected fix:** Handle variations like "Unit/Lesson:" vs "Unit & Lesson" vs "Unit, Lesson #, Module:"

#### 2.2 Improve Day Extraction

**File:** `tools/docx_parser.py`

**Method:** `_extract_day_from_header()` (line 826+)

**Changes:**
- Handle dates in headers: "Monday 10/21" → "monday"
- Support abbreviations: "Mon", "Tue", "Wed", etc.
- Case-insensitive matching

#### 2.3 Lower Fuzzy Threshold for Bilingual Content

**File:** `tools/docx_renderer.py`

**Changes:**

1. **Line 30:** Lower `FUZZY_MATCH_THRESHOLD` from 0.65 to 0.50

2. **`_calculate_match_confidence()` (lines 954-1017):** Add hint-based boost
   - If both day_hint and section_hint match, accept lower text similarity (0.40)
   - If one hint matches, accept 0.45
   - This handles LLM rephrasing in bilingual content

#### 2.4 Add Input Validation

**File:** `tools/docx_parser.py`

**Method:** `extract_hyperlinks()` (lines 645-746)

**Changes:**
- Validate `day_hint` is a real day name
- Validate `section_hint` is a known section
- Clean `row_label` (strip whitespace)
- Log warnings for invalid data

---

## Phase 3: Structural Improvements (3-5 hours)

### Goal
Handle edge cases and improve structure detection.

### Tasks

#### 3.1 Disable Coordinate Placement for Non-Standard Structures

**File:** `tools/docx_renderer.py`

**Method:** `_place_hyperlink_hybrid()` (lines 1037-1075)

**Changes:**
- Only attempt coordinate placement if structure is verified "standard_8x6"
- Add bounds checking before attempting placement
- Log why coordinate placement was skipped or failed

**Rationale:** Coordinate placement only works if input exactly matches template

#### 3.2 Enhance Structure Detection

**File:** `tools/table_structure.py`

**Method:** `detect_structure()` (lines 80-123)

**Add support for:**
- **7x6 format** (compact, missing one row)
- **10x6 format** (extra subject header row)
- Better detection of merged cells
- Better handling of non-standard headers

**Add new methods:**
- `_create_compact_7x6()`
- `_create_with_subject_header()`

#### 3.3 Create Structure Validation Tool

**File:** `tools/validate_table_structure.py` (NEW)

**Purpose:** Scan teacher files and report structure types

**Usage:** `python tools/validate_table_structure.py <week_folder>`

**Output:**
- Structure type for each file
- Row/column mappings
- Warnings for unknown structures
- Summary of structure type distribution

---

## Phase 4: Testing & Validation (2 hours)

### Tasks

#### 4.1 Unit Tests

**File:** `tests/test_hyperlink_placement.py` (NEW)

**Test cases:**
- Label+day matching on standard format
- Label normalization with variations
- Day extraction from headers with dates
- Fuzzy matching with bilingual content
- Structure detection for each format

#### 4.2 Integration Test

**Process 10 real lesson plans:**
- 5 with known hyperlink issues
- 5 with different teacher formats

**Measure:**
- Inline placement rate (target: 90%+)
- Strategy distribution (coordinate, label_day, fuzzy, fallback)
- Processing time impact

#### 4.3 Regression Test

**Ensure no degradation:**
- Test on previously working files
- Verify images still place correctly
- Check multi-slot plans still work

---

## Implementation Order

### Week 1: Diagnostics & Quick Wins
1. **Day 1-2:** Implement Phase 1 (diagnostic logging)
2. **Day 2:** Run diagnostics on 5 test files
3. **Day 3-4:** Implement Phase 2 (quick wins)
4. **Day 4:** Test quick wins, measure improvement

### Week 2: Structural & Validation
5. **Day 5-6:** Implement Phase 3 (structural improvements)
6. **Day 7:** Create validation tools
7. **Day 8:** Run full test suite
8. **Day 8:** Document results and create handoff

---

## Success Criteria

### Minimum Viable Fix (MVP)
- ✅ Inline placement rate ≥ 70% (up from 40-60%)
- ✅ Label+day strategy works for standard formats
- ✅ No regressions on existing functionality

### Target Success
- ✅ Inline placement rate ≥ 90%
- ✅ Support for 5+ teacher table formats
- ✅ Clear diagnostic reports for remaining failures
- ✅ Processing time increase < 10%

### Stretch Goals
- ✅ Inline placement rate ≥ 95%
- ✅ Automatic format detection for all teacher styles
- ✅ Post-LLM text restoration for exact hyperlink matching

---

## Risk Mitigation

### Risk 1: Changes break existing functionality
**Mitigation:** All changes are additive with fallbacks. Run regression tests.

### Risk 2: Performance degradation
**Mitigation:** Profile diagnostic logging. Make it optional via config flag.

### Risk 3: New bugs in label matching
**Mitigation:** Extensive unit tests. Gradual rollout with monitoring.

### Risk 4: Unknown table formats
**Mitigation:** Adaptive structure detection as fallback. Validation tool to identify edge cases.

---

## Rollout Plan

### Stage 1: Diagnostic Mode (1 week)
- Deploy with diagnostic logging enabled
- Collect data from production usage
- Analyze failure patterns
- No changes to placement logic yet

### Stage 2: Quick Wins (1 week)
- Deploy label normalization fixes
- Deploy fuzzy threshold adjustments
- Monitor improvement
- Collect feedback

### Stage 3: Structural (2 weeks)
- Deploy enhanced structure detection
- Deploy coordinate placement guards
- Full validation on all teacher formats
- Production release

---

## Files to Modify

### Core Changes
1. `tools/docx_renderer.py` - Placement logic, diagnostics, thresholds
2. `tools/table_structure.py` - Label normalization, structure detection
3. `tools/docx_parser.py` - Day extraction, input validation

### New Files
4. `tools/analyze_hyperlink_diagnostics.py` - Diagnostic analysis
5. `tools/validate_table_structure.py` - Structure validation
6. `tests/test_hyperlink_placement.py` - Integration tests

### Documentation
7. `HYPERLINK_FIX_SOLUTION_PLAN.md` - This document
8. `HYPERLINK_PLACEMENT_GUIDE.md` - User-facing documentation

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Set up test environment** with sample files
3. **Begin Phase 1** (diagnostic logging)
4. **Schedule check-in** after diagnostics complete
5. **Iterate** based on diagnostic findings

---

## Appendix: Key Code Locations

### Hyperlink Extraction
- `tools/docx_parser.py:645-746` - `extract_hyperlinks()`
- `tools/docx_parser.py:826+` - `_extract_day_from_header()`

### Hyperlink Placement
- `tools/docx_renderer.py:1037-1075` - `_place_hyperlink_hybrid()`
- `tools/docx_renderer.py:1077-1111` - `_try_coordinate_placement()`
- `tools/docx_renderer.py:1113-1146` - `_try_label_day_placement()`
- `tools/docx_renderer.py:1148-1196` - `_try_fuzzy_placement()`

### Structure Detection
- `tools/table_structure.py:80-123` - `detect_structure()`
- `tools/table_structure.py:24-43` - `get_row_index()`
- `tools/table_structure.py:196-212` - `_build_row_map()`

### Configuration
- `tools/docx_renderer.py:30` - `FUZZY_MATCH_THRESHOLD`
- `backend/config.py` - Media matching settings
