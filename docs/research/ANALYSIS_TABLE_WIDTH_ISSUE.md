# Table Width Preservation Issue - Analysis

## Problem
The codebase hardcodes table width to **6.5 inches** but the actual template uses **landscape orientation (11" x 8.5")** with **0.5" margins**, requiring **10 inches** width.

## Current Hardcoded Values
1. **tools/docx_utils.py**:
   - `normalize_table_column_widths()`: default `total_width_inches=6.5`
   - `normalize_all_tables()`: default `total_width_inches=6.5`

2. **tools/docx_renderer.py** (line 276, 281):
   - `normalize_all_tables(doc, total_width_inches=6.5)`

3. **tests/test_table_width.py**: Multiple tests use 6.5 inches

## Root Cause
The comment in `docx_utils.py` line 23 states:
```
Standard US Letter: 8.5" wide - 2" margins = 6.5" available
```

This assumes **portrait orientation** with **1" margins**, but the actual template is:
- **Landscape**: 11" x 8.5"
- **Margins**: 0.5" left/right
- **Available width**: 10" (11" - 0.5" - 0.5")

## Impact
When rendering output documents, tables are set to 6.5" width instead of 10", causing:
- Large white space on right margin (2.5" excess)
- Misalignment with template
- Inconsistent appearance

## Solution
Make table width **dynamic** based on template page setup:
1. Read page width and margins from template document
2. Calculate available width: `page_width - left_margin - right_margin`
3. Pass calculated width to `normalize_all_tables()`

## Files to Fix
1. `tools/docx_utils.py` - Update defaults and documentation
2. `tools/docx_renderer.py` - Calculate width dynamically from template
3. `tests/test_table_width.py` - Update test expectations
4. `backend/config.py` - Consider adding TABLE_WIDTH_INCHES setting (optional)
