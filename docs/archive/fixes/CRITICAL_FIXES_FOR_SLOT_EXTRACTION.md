# Critical Fixes for Slot-Aware Extraction

## Issues Identified by Other AI

### ✅ 1. Paragraph Hyperlinks (FIXED)
**Problem:** Paragraph links were extracted regardless of table filtering.
**Fix:** Skip paragraph extraction when `table_start_idx` or `table_end_idx` is specified.
**Status:** FIXED in docx_parser.py lines 664-696

### ⚠️ 2. Signature Table Logic (NEEDS FIX)
**Problem:** Reducing `total_tables` count breaks index validation.
- File has 12 tables (0-11)
- Slot 6 needs tables 10-11
- Code detects signature at index 11, sets `total_tables = 11`
- Validation: `table_end (11) >= total_tables (11)` → Returns empty!

**Current Code:**
```python
if "signature" in last_table.first_cell.lower():
    total_tables -= 1  # WRONG! This breaks index validation
```

**Correct Fix:**
```python
# Don't adjust total_tables, just check if we're trying to access signature table
if table_end == len(self.doc.tables) - 1:
    # Check if last table is signature
    last_table = self.doc.tables[-1]
    if is_signature_table(last_table):
        # Reduce table_end to exclude signature
        table_end -= 1
        logger.debug("excluding_signature_table")
```

### ⚠️ 3. Image Extraction (BROKEN)
**Problem:** `extract_images_for_slot()` filters by `table_idx`, but `_find_image_context()` doesn't set it!

**Current Code:**
```python
slot_images = [
    img for img in all_images
    if img.get('table_idx') is not None and  # Always None!
    table_start <= img['table_idx'] <= table_end
]
```

**Fix Needed:**
Must add `table_idx` to image dictionaries in `_find_image_context()` or `extract_images()`.

### ⚠️ 4. Batch Processor Always Uses Slot Methods
**Problem:** `_process_slot()` now always calls `extract_images_for_slot()`, which currently returns empty list.

**Impact:** ALL image placement will fail until image extraction is fixed.

### ⚠️ 5. No Validation of Table Structure
**Problem:** Hardcoded `(slot-1)*2` assumes perfect 2-table-per-slot structure.

**Needed:** Log table structure and warn if it doesn't match expectations.

---

## Implementation Plan

### Priority 1: Fix Signature Table Logic

```python
def extract_hyperlinks_for_slot(self, slot_number: int, tables_per_slot: int = 2):
    table_start = (slot_number - 1) * tables_per_slot
    table_end = table_start + tables_per_slot - 1
    
    total_tables = len(self.doc.tables)
    
    # Check if we're trying to access the last table
    if table_end == total_tables - 1:
        # Check if last table is signature
        last_table = self.doc.tables[-1]
        if last_table.rows and last_table.rows[0].cells:
            first_cell = last_table.rows[0].cells[0].text.strip().lower()
            if "signature" in first_cell or "required signatures" in first_cell:
                # This slot would include signature table - that's wrong!
                logger.warning(
                    "slot_includes_signature_table",
                    extra={
                        "slot_number": slot_number,
                        "table_end": table_end,
                        "total_tables": total_tables
                    }
                )
                # Reduce table_end to exclude signature
                table_end -= 1
    
    # Now validate range (without adjusting total_tables)
    if table_start >= total_tables or table_end >= total_tables:
        logger.warning("slot_exceeds_table_count", ...)
        return []
    
    return self.extract_hyperlinks(table_start_idx=table_start, table_end_idx=table_end)
```

### Priority 2: Fix Image Extraction

**Option A: Add table_idx during extraction**
```python
def extract_images(self):
    images = []
    for rel_id, rel in self.doc.part.rels.items():
        if "image" in rel.target_ref:
            # Find which table this image belongs to
            table_idx = self._find_image_table_index(rel_id)
            
            image_dict = {
                'filename': ...,
                'table_idx': table_idx,  # ADD THIS
                ...
            }
            images.append(image_dict)
```

**Option B: Simpler - Extract images from specific tables only**
```python
def extract_images_for_slot(self, slot_number: int, tables_per_slot: int = 2):
    table_start = (slot_number - 1) * tables_per_slot
    table_end = table_start + tables_per_slot - 1
    
    # Extract images only from these specific tables
    images = []
    for table_idx in range(table_start, table_end + 1):
        if table_idx < len(self.doc.tables):
            table = self.doc.tables[table_idx]
            # Extract images from this table
            table_images = self._extract_images_from_table(table, table_idx)
            images.extend(table_images)
    
    return images
```

### Priority 3: Add Table Structure Validation

```python
def validate_slot_structure(self, expected_slots: int):
    """Validate document has expected slot structure."""
    total_tables = len(self.doc.tables)
    
    # Check for signature table
    has_signature = False
    if total_tables > 0:
        last_table = self.doc.tables[-1]
        if self._is_signature_table(last_table):
            has_signature = True
            total_tables -= 1
    
    expected_tables = expected_slots * 2
    
    if total_tables != expected_tables:
        logger.warning(
            "unexpected_table_structure",
            extra={
                "expected_tables": expected_tables,
                "actual_tables": total_tables,
                "has_signature": has_signature,
                "expected_slots": expected_slots
            }
        )
        return False
    
    return True
```

---

## Testing Requirements

### Test Cases Needed:

1. **Paragraph-only hyperlinks**
   - Document with links in intro text
   - Verify they're excluded when extracting for specific slot

2. **Signature table at end**
   - 9 tables (4 slots + signature)
   - Verify slot 4 extracts from tables 6-7, not 6-8

3. **Missing metadata table**
   - Slot with only daily plans table
   - Verify graceful handling

4. **Extra tables**
   - Summary table at beginning
   - Verify slot indices adjust correctly

5. **Images in slots**
   - Verify images extracted only from slot's tables
   - Verify `table_idx` is populated

---

## Immediate Actions

1. ✅ Fix paragraph extraction (DONE)
2. ⚠️ Fix signature table logic (IN PROGRESS)
3. ⚠️ Fix image extraction (TODO)
4. ⚠️ Add structure validation (TODO)
5. ⚠️ Add comprehensive tests (TODO)

---

**Without these fixes, the current implementation will:**
- ✅ Prevent paragraph link contamination (fixed)
- ❌ Drop slot 4+ in 9-table files (signature bug)
- ❌ Drop ALL images (image extraction broken)
- ❌ Silently fail on non-standard layouts (no validation)

**Priority: Fix signature table logic and image extraction before testing!**
