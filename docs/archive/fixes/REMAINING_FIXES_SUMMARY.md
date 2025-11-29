# Remaining Fixes Summary

## ✅ Fixed
1. **Week number in filename** - Fixed `_calculate_week_number()` to handle "MM-DD-MM-DD" format
2. **No School day labels** - Fixed to clear all cells except Unit/Lesson

## 🔧 To Fix

### 3. Markdown formatting (** not rendering as bold)
**Issue:** Text like `**Assessment:**` appears with asterisks instead of bold
**Location:** `tools/markdown_to_docx.py` - The `add_multiline_text()` method
**Fix needed:** Ensure markdown parsing is working correctly

### 4. Font formatting (Times New Roman 8pt)
**Issue:** Need to format table cells (except row 1 and column A) to Times New Roman 8pt
**Location:** `tools/docx_renderer.py` - After filling cells
**Fix needed:** Add font formatting to `_fill_cell()` method

### 5. Duplicate "Required Signatures" table
**Issue:** Two signature tables appear in output
**Possible causes:**
- Template has one, we're adding another
- Multi-slot merge is duplicating it
**Location:** Check `batch_processor.py` `_add_signature_box()` and `_remove_signature_boxes()`

### 6. Table width consistency
**Issue:** All tables must have the same width
**Location:** `tools/docx_utils.py` - `normalize_all_tables()` function
**Current:** Already normalizes to 6.5 inches
**Check:** Verify it's being applied to ALL tables including signatures

## Priority Order
1. Markdown formatting (affects readability)
2. Font formatting (affects appearance)
3. Duplicate signatures (affects professionalism)
4. Table width (minor visual issue)
