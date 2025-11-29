# Phase 0: Pre-Implementation Audit Summary

**Completed:** Phase 0.1 - 0.3  
**Status:** Ready for Phase 0.4 (Bug Fixes) and 0.5 (Prototyping)

---

## ✅ Phase 0.1: Schema Versioning Analysis - COMPLETE

### **Current Schema (v1.1):**
```python
{
    'text': str,
    'url': str,
    'context_snippet': str,
    'context_type': str,
    'section_hint': Optional[str],
    'day_hint': Optional[str]
}
```

### **Proposed Schema (v2.0):**
```python
{
    'schema_version': '2.0',          # NEW
    # ... all v1.1 fields ...
    'table_idx': Optional[int],       # NEW
    'row_idx': Optional[int],         # NEW
    'cell_idx': Optional[int],        # NEW
    'row_label': Optional[str],       # NEW
    'col_header': Optional[str]       # NEW
}
```

### **Migration Strategy:**
- ✅ **Additive migration** (no breaking changes)
- ✅ Keep all v1.1 fields for backward compatibility
- ✅ Add new v2.0 fields alongside existing ones
- ✅ Version check in renderer to use appropriate strategy

### **Breaking Change Analysis:**
- ✅ **batch_processor.py:** No changes needed (only reads 'text' field)
- ✅ **docx_renderer.py:** Needs version check, but backward compatible
- ⚠️ **Test files:** May need fixture updates

**Document Created:** `SCHEMA_VERSIONING_PLAN.md`

---

## ✅ Phase 0.2: Code Audit - COMPLETE

### **Hyperlink Consumers Identified:**

#### **1. Parser (Producer):**
- **File:** `tools/docx_parser.py`
- **Method:** `extract_hyperlinks()` (line 645)
- **Current behavior:**
  - Extracts from paragraphs and tables
  - Infers section_hint and day_hint
  - Does NOT capture coordinates
- **Changes needed:**
  - Add table_idx, row_idx, cell_idx capture
  - Add row_label, col_header capture
  - Add schema_version field

#### **2. Batch Processor (Pass-through):**
- **File:** `tools/batch_processor.py`
- **Lines:** 344, 444, 548
- **Current behavior:**
  - Calls `parser.extract_hyperlinks()`
  - Extracts link text for LLM preservation
  - Stores in JSON as `_hyperlinks`
- **Changes needed:**
  - ✅ None (just passes through)

#### **3. Renderer (Consumer):**
- **File:** `tools/docx_renderer.py`
- **Lines:** 117, 155, 322-414
- **Current behavior:**
  - Reads `_hyperlinks` from JSON
  - Uses `_calculate_match_confidence()` for placement
  - Injects via `_inject_hyperlink_inline()`
- **Changes needed:**
  - Add schema version check
  - Add coordinate-based placement
  - Keep fuzzy matching as fallback

#### **4. Test Files:**
- `test_media_preservation.py`
- `test_media_e2e.py`
- `validate_threshold_change_v2.py`
- **Changes needed:**
  - Update fixtures to include v2.0 fields
  - Add tests for coordinate placement

---

## ✅ Phase 0.3: Reusable Code Identification - COMPLETE

### **Existing Fuzzy Matching Logic:**

**Location:** `tools/docx_renderer.py`, line 872

**Method:** `_calculate_match_confidence(cell_text, media, day_name, section_name)`

**Strategies (in order):**
1. **Exact text match:** `if media['text'] in cell_text` → 1.0 confidence
2. **Fuzzy context match:** `fuzz.partial_ratio(context, cell_text)` → 0.0-1.0
3. **Hint boosting:** +0.1 per matching hint (day/section)
4. **Hints only:** Both hints match → 0.5 confidence

**Current threshold:** `FUZZY_MATCH_THRESHOLD = 0.65`

**Dependencies:**
- `rapidfuzz.fuzz` for fuzzy matching
- Falls back to exact match if rapidfuzz not available

### **Reusable Components:**

✅ **Can reuse directly:**
- `_calculate_match_confidence()` - Complete fuzzy matching logic
- `_inject_hyperlink_inline()` - Hyperlink injection into cells
- `FUZZY_MATCH_THRESHOLD` - Threshold constant

✅ **Can extract and reuse:**
- Section hint inference logic
- Day hint extraction logic
- Context snippet extraction

❌ **Cannot reuse (need new code):**
- Coordinate capture (doesn't exist yet)
- Structure detection (doesn't exist yet)
- Coordinate-based placement (doesn't exist yet)

### **Integration Plan:**

```python
def _try_fuzzy_placement(self, link, table, threshold=0.65) -> bool:
    """Use existing fuzzy matching logic."""
    
    # Iterate through table cells
    for row_idx, row in enumerate(table.rows):
        for cell_idx, cell in enumerate(row.cells):
            # Use existing _calculate_match_confidence
            confidence, match_type = self._calculate_match_confidence(
                cell.text,
                link,
                day_name=self._extract_day_from_row(row),
                section_name=self._extract_section_from_row(row)
            )
            
            if confidence >= threshold:
                # Use existing _inject_hyperlink_inline
                self._inject_hyperlink_inline(cell, link)
                return True
    
    return False
```

**No need to rewrite fuzzy matching - just call existing methods!**

---

## ⚠️ Phase 0.4: Bug Fixes in Implementation Plan - PENDING

### **Bugs Identified by Other AI:**

#### **Bug #1: Non-table guard logic**
**Location:** `COORDINATE_BASED_PLACEMENT_PLAN.md`, Phase 3

**Current (WRONG):**
```python
if not link.get('table_idx') is not None:  # Double negative!
```

**Fixed:**
```python
if link.get('table_idx') is None:
    logger.debug(f"Link '{link['text']}' not from table, using fallback")
    self._add_to_fallback(link)
    return 'fallback'
```

#### **Bug #2: Fuzzy placement stub**
**Location:** `COORDINATE_BASED_PLACEMENT_PLAN.md`, Phase 3

**Current (STUB):**
```python
def _try_fuzzy_placement(self, link, table, threshold):
    """Try to place link using fuzzy text matching (existing logic)."""
    # Use existing fuzzy matching code
    # ... (current implementation)
    pass  # ← This is a stub!
```

**Fixed:**
```python
def _try_fuzzy_placement(self, link, table, threshold=0.65) -> bool:
    """Use existing fuzzy matching logic."""
    
    for row_idx, row in enumerate(table.rows):
        for cell_idx, cell in enumerate(row.cells):
            confidence, match_type = self._calculate_match_confidence(
                cell.text, link,
                day_name=self._extract_day_from_row(row),
                section_name=self._extract_section_from_row(row)
            )
            
            if confidence >= threshold:
                self._inject_hyperlink_inline(cell, link)
                logger.debug(f"Placed '{link['text']}' via fuzzy ({confidence:.2f})")
                return True
    
    return False
```

### **Action Items:**
- [ ] Update `COORDINATE_BASED_PLACEMENT_PLAN.md` with fixes
- [ ] Review all code snippets for similar bugs
- [ ] Add proper logging statements
- [ ] Ensure all methods return correct types

---

## 📋 Phase 0.5: Prototype Strategy - PENDING

### **Prototype Plan:**

#### **Step 1: Select Test Files**
Pick 3-5 standard 8x6 files from analysis:
- `10_20-10_24 Davies Lesson Plans.docx` (standard 8x6)
- `10_20-10_24 Laverti Lesson Plans.docx` (standard 8x6)
- `10_20-10_24 Lonesky Lesson Plans.docx` (standard 8x6)

#### **Step 2: Implement Minimal Parser Changes**
```python
# Add ONLY coordinate capture, no other changes
def extract_hyperlinks(self):
    # ... existing code ...
    
    for table_idx, table in enumerate(self.doc.tables):
        for row_idx, row in enumerate(table.rows):
            row_label = row.cells[0].text.strip() if row.cells else ""
            
            for cell_idx, cell in enumerate(row.cells):
                # ... existing extraction ...
                
                hyperlink['table_idx'] = table_idx
                hyperlink['row_idx'] = row_idx
                hyperlink['cell_idx'] = cell_idx
                hyperlink['row_label'] = row_label
```

#### **Step 3: Validate Coordinates**
```python
# Create validation script
def validate_coordinates(input_file):
    parser = DOCXParser(input_file)
    hyperlinks = parser.extract_hyperlinks()
    
    for link in hyperlinks:
        print(f"Link: {link['text']}")
        print(f"  Coordinates: table={link['table_idx']}, "
              f"row={link['row_idx']}, cell={link['cell_idx']}")
        print(f"  Row label: {link['row_label']}")
        print(f"  Section: {link['section_hint']}, Day: {link['day_hint']}")
        print()
```

#### **Step 4: Manual Verification**
- Open input file in Word
- Locate each hyperlink manually
- Verify coordinates match actual position
- Check row labels are correct

#### **Success Criteria:**
- ✅ All hyperlinks have coordinates
- ✅ Coordinates match actual positions
- ✅ Row labels are correct
- ✅ No crashes or errors
- ✅ Non-table links have `table_idx=None`

---

## 📊 Summary Status

| Phase | Task | Status | Document |
|-------|------|--------|----------|
| 0.1 | Schema versioning | ✅ Complete | `SCHEMA_VERSIONING_PLAN.md` |
| 0.2 | Code audit | ✅ Complete | This document |
| 0.3 | Reusable code | ✅ Complete | This document |
| 0.4 | Bug fixes | ⏳ Pending | Need to update plan docs |
| 0.5 | Prototype | ⏳ Pending | Need to implement & test |

---

## 🎯 Next Steps

1. **Fix bugs in implementation plan** (Phase 0.4)
   - Update `COORDINATE_BASED_PLACEMENT_PLAN.md`
   - Fix non-table guard logic
   - Replace fuzzy placement stub with real code
   - Review all code snippets

2. **Create prototype** (Phase 0.5)
   - Implement minimal parser changes
   - Create validation script
   - Test on 3-5 standard files
   - Manual verification

3. **Proceed to Phase 1** (only after prototype validates)
   - Full parser implementation
   - Schema v2.0 rollout
   - Unit tests

---

**Estimated Time:**
- Phase 0.4: 2 hours
- Phase 0.5: 4 hours
- **Total remaining:** 6 hours

**Ready to proceed with Phase 0.4 (bug fixes)?**
