# Phase 1: Diagnostic Logging - COMPLETE

**Date:** October 26, 2025  
**Status:** ✅ Implementation Complete  
**Next:** Run diagnostics on test files

---

## What Was Implemented

### 1. Enhanced Placement Tracking

**File:** `tools/docx_renderer.py`  
**Method:** `_place_hyperlink_hybrid()` (lines 1037-1107)

**Added:**
- Comprehensive diagnostic record for each hyperlink
- Tracks all strategies attempted (coordinate, label_day, fuzzy, fallback)
- Logs input coordinates vs. detected structure
- Logs label/day lookup results
- Logs specific failure reasons for each strategy

**Diagnostic Data Captured:**
```python
{
    'link_text': str,           # First 50 chars of link text
    'url': str,                 # First 50 chars of URL
    'input_coords': str,        # table_idx, row_idx, cell_idx from input
    'row_label': str,           # Row label from input
    'col_header': str,          # Column header from input
    'day_hint': str,            # Extracted day name
    'section_hint': str,        # Inferred section
    'structure_type': str,      # Detected output structure
    'strategy_attempted': [],   # List of strategies tried
    'result': str,              # Final result (success_* or fallback)
    'label_lookup': int/None,   # Row index from label lookup
    'day_lookup': int/None,     # Column index from day lookup
    'coordinate_failure': str,  # Why coordinate placement failed
    'label_day_failure': str,   # Why label/day placement failed
    'fuzzy_failure': str        # Why fuzzy placement failed
}
```

### 2. Enhanced Fuzzy Match Scoring

**File:** `tools/docx_renderer.py`  
**Method:** `_try_fuzzy_placement()` (lines 1180-1252)

**Added:**
- Tracks best match even if below threshold
- Logs confidence scores for all cells tested
- Shows which cell came closest to matching
- Helps identify if threshold is too high

**Best Match Data:**
```python
{
    'link_text': str,
    'best_confidence': float,   # Highest confidence score found
    'best_location': str,       # Cell coordinates of best match
    'threshold': float,         # Current threshold (0.65)
    'cell_preview': str,        # First 80 chars of best match cell
    'match_type': str           # Type of match attempted
}
```

### 3. Diagnostic Analysis Script

**File:** `tools/analyze_hyperlink_diagnostics.py` (NEW)

**Features:**
- Parses structured log files
- Generates comprehensive report
- Shows success rate by strategy
- Identifies most common failure patterns
- Lists row labels that fail lookup
- Lists day hints that fail lookup
- Shows sample fallback cases with full context
- Provides actionable recommendations

**Usage:**
```bash
python tools/analyze_hyperlink_diagnostics.py backend/logs/app.log
```

**Report Sections:**
1. Placement Results (success rate by strategy)
2. Structure Types (distribution of table formats)
3. Strategy Analysis (detailed breakdown)
4. Fallback Cases (sample failures with context)
5. Recommendations (actionable fixes)

### 4. Quick Test Script

**File:** `test_hyperlink_diagnostics.py` (NEW)

**Purpose:** Validate diagnostic logging is working

**Features:**
- Processes one lesson plan
- Uses first available user/slot
- Validates configuration
- Provides clear error messages
- Shows where to find diagnostic output

**Usage:**
```bash
python test_hyperlink_diagnostics.py
```

---

## How to Use

### Step 1: Process Test Files

**Option A: Use test script**
```bash
python test_hyperlink_diagnostics.py
```

**Option B: Process via frontend**
1. Open the application
2. Select a user with configured slots
3. Process a week's lesson plans
4. Check logs in `backend/logs/app.log`

### Step 2: Analyze Diagnostics

```bash
python tools/analyze_hyperlink_diagnostics.py backend/logs/app.log
```

### Step 3: Review Report

The analysis will show:
- **Overall success rate** - Target: 90%+
- **Strategy breakdown** - Which strategies work/fail
- **Common failures** - Row labels not found, day hints not found
- **Sample cases** - Specific examples of fallback links
- **Recommendations** - What to fix first

### Step 4: Identify Patterns

Look for:
1. **High fallback rate** → Label normalization issues
2. **Label lookup failures** → Missing row patterns
3. **Day lookup failures** → Day extraction issues
4. **Low fuzzy scores** → Threshold too high for bilingual content
5. **Adaptive structures** → Unknown table formats

---

## Expected Output

### Good Result (90%+ success):
```
PLACEMENT RESULTS
✓ success_label_day        : 150 (75.0%)
✓ success_fuzzy            :  30 (15.0%)
✓ success_coordinate       :  10 ( 5.0%)
✗ fallback                 :  10 ( 5.0%)

Overall Success Rate: 190/200 (95.0%)
```

### Problem Result (<70% success):
```
PLACEMENT RESULTS
✓ success_label_day        :  50 (25.0%)
✓ success_fuzzy            :  20 (10.0%)
✗ fallback                 : 130 (65.0%)

Overall Success Rate: 70/200 (35.0%)

Top Row Labels Not Found:
  'Unit, Lesson #, Module:': 45 times
  'Anticipatory Set:': 30 times
  'Tailored Instruction:': 25 times
```

---

## Next Steps

### If Success Rate is Good (>90%):
- ✅ System is working well
- Consider Phase 3 (structural improvements) for edge cases
- Monitor production usage

### If Success Rate is Medium (70-90%):
- Proceed to **Phase 2: Quick Wins**
- Focus on label normalization
- Adjust fuzzy threshold

### If Success Rate is Low (<70%):
- **Urgent:** Proceed to Phase 2 immediately
- Review sample fallback cases carefully
- May need Phase 3 (structural) as well

---

## Files Modified

1. `tools/docx_renderer.py` (+70 lines)
   - Enhanced `_place_hyperlink_hybrid()` with diagnostics
   - Enhanced `_try_fuzzy_placement()` with best match tracking

2. `tools/analyze_hyperlink_diagnostics.py` (NEW, 250 lines)
   - Log parser
   - Analysis engine
   - Report generator

3. `test_hyperlink_diagnostics.py` (NEW, 120 lines)
   - Quick validation script
   - Configuration checker
   - Usage guide

---

## Logging Configuration

Ensure logging is configured correctly:

**File:** `backend/telemetry.py`

Logging level should be **INFO** or **DEBUG** to capture diagnostics:
```python
logger = structlog.get_logger()
logger.setLevel(logging.INFO)  # or logging.DEBUG
```

Log file location: `backend/logs/app.log`

---

## Troubleshooting

### No diagnostic data in logs?

**Check:**
1. Logging level is INFO or DEBUG
2. Log file path is correct
3. Lesson plans have been processed after code update
4. Hyperlinks exist in input files

### Analysis script shows 0 diagnostics?

**Check:**
1. Log file path is correct
2. Log file contains recent data
3. Structured logging format is correct
4. Run test script to generate fresh data

### Test script fails?

**Check:**
1. Database has at least one user
2. User has at least one slot configured
3. Slot has valid primary_teacher_file path
4. API keys are configured in .env
5. Input file exists and has hyperlinks

---

## Success Criteria

✅ **Phase 1 Complete When:**
- Diagnostic logging implemented
- Analysis script working
- Test script validates setup
- Report shows actionable data

✅ **Ready for Phase 2 When:**
- Processed 3-5 test files
- Generated diagnostic report
- Identified top 3 failure patterns
- Understand current success rate

---

## Example Workflow

```bash
# 1. Process a test file
python test_hyperlink_diagnostics.py

# 2. Analyze the results
python tools/analyze_hyperlink_diagnostics.py backend/logs/app.log

# 3. Review the report
# Look for:
#   - Overall success rate
#   - Most common label lookup failures
#   - Most common day lookup failures
#   - Sample fallback cases

# 4. Proceed to Phase 2 with specific fixes based on findings
```

---

## Notes

- All changes are **additive** - no existing functionality broken
- Logging is **structured** - easy to parse and analyze
- Diagnostics are **comprehensive** - capture all relevant data
- Analysis is **actionable** - provides specific recommendations
- Testing is **simple** - one command to validate

---

## Contact

If you encounter issues or need clarification:
1. Check this document first
2. Review the code comments
3. Run the test script for validation
4. Check log files for errors
