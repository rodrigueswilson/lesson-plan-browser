# Table Width Normalization - Validated Solution

**Date**: 2025-10-18  
**Status**: VALIDATED  
**API**: python-docx 1.2.0

---

## Summary

The python-docx API **DOES support** setting equal column widths through the `table.columns[i].width` property.

---

## Working Approach

### Method: Use `column.width` property

```python
from docx import Document
from docx.shared import Inches

doc = Document('input.docx')
table = doc.tables[0]

# Calculate equal width
total_width = Inches(6.5)  # Page width minus margins
col_width = int(total_width / len(table.columns))  # MUST be int!

# Set width on each column
for column in table.columns:
    column.width = col_width

doc.save('output.docx')
```

---

## Key Findings

### ✅ What Works

1. **`table.columns[i].width` property** - Read/write access to column width
2. **`cell.width` property** - Alternative approach, set on first row cells
3. **EMU units** - Width values are in English Metric Units (EMU)
4. **`Inches()` helper** - Converts inches to EMU automatically

### ⚠️ Critical Requirements

1. **Width MUST be integer** - Float values cause `TypeError`
   ```python
   # WRONG
   column.width = Inches(6.5) / 5  # Returns float
   
   # CORRECT
   column.width = int(Inches(6.5) / 5)  # Convert to int
   ```

2. **EMU values** - 1 inch = 914,400 EMU
   - `Inches(1.0)` returns `914400` (int)
   - `Inches(2.0)` returns `1828800` (int)

### 📊 Test Results

| Test | Result | Output File |
|------|--------|-------------|
| Simple 3-column table | ✅ PASS | `test_table_width_approach1.docx` |
| Cell-based approach | ✅ PASS | `test_table_width_approach2.docx` |
| Actual lesson template (5 cols) | ✅ PASS | `test_template_equal_widths.docx` |

**Template Test Details**:
- Template has 5 columns with unequal widths
- Original widths: `[2105025, 1143000, 1390650, 2047875, 2409825]` EMU
- After normalization: `[1188720, 1188720, 1188720, 1188720, 1188720]` EMU
- All columns now equal width

---

## Recommended Implementation

### Function Signature

```python
def normalize_table_column_widths(
    table: Table,
    total_width_inches: float = 6.5
) -> None:
    """
    Set all columns in table to equal width.
    
    Args:
        table: python-docx Table object
        total_width_inches: Total width to distribute (default 6.5")
    """
    from docx.shared import Inches
    
    if not table.columns:
        return
    
    col_width = int(Inches(total_width_inches) / len(table.columns))
    
    for column in table.columns:
        column.width = col_width
```

### Usage in Renderer

```python
# In tools/docx_renderer.py or tools/docx_utils.py

def render_to_docx(data: Dict[str, Any], template_path: str) -> Document:
    """Render lesson data to DOCX."""
    doc = Document(template_path)
    
    # ... existing rendering logic ...
    
    # Normalize table widths
    for table in doc.tables:
        normalize_table_column_widths(table)
    
    return doc
```

---

## Edge Cases Handled

### Merged Cells
- ✅ Works correctly - width applies to entire column
- Merged cells span multiple columns, width still applies

### Empty Tables
- ✅ Guard with `if not table.columns: return`

### Variable Column Count
- ✅ Divides width by actual column count
- Works for any number of columns

---

## Alternative Approaches Considered

### Approach 2: Set width on cells
```python
# Set width on first row cells
for cell in table.rows[0].cells:
    cell.width = col_width
```
- ✅ Also works
- ⚠️ Less intuitive (why first row only?)
- ❌ Doesn't handle merged cells as cleanly
- **Verdict**: Use column approach instead

### Approach 3: XML manipulation
```python
from docx.oxml.shared import OxmlElement
from docx.oxml.ns import qn

for cell in table.columns[0].cells:
    tc = cell._element
    tcPr = tc.get_or_add_tcPr()
    tcW = OxmlElement('w:tcW')
    tcW.set(qn('w:w'), str(col_width))
    tcW.set(qn('w:type'), 'dxa')
    tcPr.append(tcW)
```
- ✅ Works
- ❌ Too complex, uses private APIs
- ❌ Harder to maintain
- **Verdict**: Unnecessary, use column.width instead

---

## Decision: Include in Session 1

**Recommendation**: ✅ **INCLUDE** table width normalization in Session 1

**Rationale**:
- API is simple and well-documented
- Validation tests pass on actual template
- Low risk of breaking existing functionality
- High value for consistent output formatting

**Estimated Time**: 30 minutes
- 15 min: Add function to `tools/docx_utils.py`
- 10 min: Integrate into renderer
- 5 min: Add unit test

---

## References

- **API Docs**: https://python-docx.readthedocs.io/en/latest/api/table.html
- **Test Script**: `tests/test_table_width_validation.py`
- **Output Samples**: `output/test_table_width_*.docx`

---

**Validation Status**: ✅ COMPLETE  
**Ready for Implementation**: YES
