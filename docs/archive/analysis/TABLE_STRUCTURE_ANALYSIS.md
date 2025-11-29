# Table Structure Analysis - W44 Files

## Key Findings

### 1. Actual Table Structure

**Each file has 9 tables total:**
- Tables 0-1: Slot 1 (Metadata + Daily Plans)
- Tables 2-3: Slot 2 (Metadata + Daily Plans)
- Tables 4-5: Slot 3 (Metadata + Daily Plans)
- Tables 6-7: Slot 4 (Metadata + Daily Plans)
- **Table 8: Signature table (NOT a slot!)**

### 2. Pattern Discovered

✅ **4 slots per file** (not 5 as assumed!)
✅ **2 tables per slot** (metadata + daily plans)
✅ **1 signature table at the end** (table 8)

**Formula:**
- Slot N tables: `[(N-1)*2, (N-1)*2+1]`
- Slot 1: Tables [0, 1]
- Slot 2: Tables [2, 3]
- Slot 3: Tables [4, 5]
- Slot 4: Tables [6, 7]
- Signature: Table 8 (skip this!)

### 3. Hyperlink Location

✅ **All hyperlinks are in tables** (not paragraphs)
✅ **No paragraph-level hyperlinks found**

This simplifies our implementation - we only need to filter by table index!

---

## Implementation Strategy (Revised)

### Approach: Simple Table Index Filtering

Since:
1. All hyperlinks are in tables
2. Structure is consistent (2 tables per slot + 1 signature)
3. No paragraph hyperlinks to worry about

We can use **simple table index filtering**:

```python
def extract_hyperlinks_for_slot(self, slot_number: int, tables_per_slot: int = 2):
    """
    Extract hyperlinks for specific slot.
    
    Args:
        slot_number: Slot number (1-indexed)
        tables_per_slot: Number of tables per slot (default: 2)
    """
    table_start = (slot_number - 1) * tables_per_slot
    table_end = table_start + tables_per_slot - 1
    
    # Validate
    if table_end >= len(self.doc.tables):
        # Check if we're hitting the signature table
        if table_end == len(self.doc.tables) - 1:
            # Last table might be signature, exclude it
            table_end = table_end - 1
        else:
            logger.warning(f"Slot {slot_number} exceeds table count")
            return []
    
    return self.extract_hyperlinks(table_start_idx=table_start, table_end_idx=table_end)
```

### Edge Case: Signature Table

The signature table (table 8) should be **excluded** from all slot extractions.

**Detection:**
- Last table in document
- First cell contains "Required Signatures" or "Signature"
- Only 1 column

---

## Updated Implementation Plan

### 1. Modify `extract_hyperlinks()` in `docx_parser.py`

Add table range filtering:

```python
def extract_hyperlinks(self, table_start_idx: int = None, table_end_idx: int = None):
    """Extract hyperlinks with optional table filtering."""
    
    # Existing code...
    
    for table_idx, table in enumerate(self.doc.tables):
        # NEW: Skip tables outside range
        if table_start_idx is not None and table_idx < table_start_idx:
            continue
        if table_end_idx is not None and table_idx > table_end_idx:
            continue
        
        # Existing extraction logic...
```

### 2. Add `extract_hyperlinks_for_slot()`

```python
def extract_hyperlinks_for_slot(self, slot_number: int):
    """Extract hyperlinks for specific slot."""
    tables_per_slot = 2
    table_start = (slot_number - 1) * tables_per_slot
    table_end = table_start + tables_per_slot - 1
    
    # Validate range
    total_tables = len(self.doc.tables)
    
    # Check if last table is signature table
    if total_tables > 0:
        last_table = self.doc.tables[-1]
        if last_table.rows and last_table.rows[0].cells:
            first_cell = last_table.rows[0].cells[0].text.strip().lower()
            if "signature" in first_cell:
                # Exclude signature table from slot calculations
                total_tables -= 1
    
    if table_end >= total_tables:
        logger.warning(
            "slot_exceeds_table_count",
            extra={
                "slot_number": slot_number,
                "table_start": table_start,
                "table_end": table_end,
                "total_tables": total_tables
            }
        )
        return []
    
    return self.extract_hyperlinks(table_start_idx=table_start, table_end_idx=table_end)
```

### 3. Same for `extract_images_for_slot()`

### 4. Update `batch_processor.py`

```python
# Line ~397
slot_num = slot['slot_number']
hyperlinks = await asyncio.to_thread(parser.extract_hyperlinks_for_slot, slot_num)
images = await asyncio.to_thread(parser.extract_images_for_slot, slot_num)
```

---

## Testing Plan

### Unit Tests

```python
def test_slot_1_extracts_tables_0_1():
    # Mock doc with 9 tables
    # Extract slot 1
    # Verify only tables 0-1 processed

def test_slot_4_extracts_tables_6_7():
    # Extract slot 4
    # Verify only tables 6-7 processed

def test_signature_table_excluded():
    # Verify table 8 (signature) is never extracted

def test_slot_exceeds_count_returns_empty():
    # Request slot 5 (doesn't exist)
    # Should return empty list, not crash
```

### Integration Test

Process W44 files and verify:
- Slot 1 (ELA) has only ELA hyperlinks
- Slot 2 (Math) has only Math hyperlinks
- No cross-contamination
- Signature table ignored

---

## Advantages of This Approach

✅ **Simple** - Just filter by table index
✅ **No paragraph handling needed** - All hyperlinks are in tables
✅ **Consistent structure** - 2 tables per slot across all files
✅ **Signature table detection** - Automatically excluded
✅ **Backward compatible** - Default behavior unchanged

---

## Potential Issues & Solutions

### Issue 1: What if a file has different structure?

**Solution:** Add validation and logging:
```python
expected_tables = (num_slots * 2) + 1  # +1 for signature
if len(doc.tables) != expected_tables:
    logger.warning("unexpected_table_count", extra={...})
```

### Issue 2: What if signature table is missing?

**Solution:** Detection is optional:
```python
if "signature" in first_cell:
    total_tables -= 1  # Only exclude if detected
```

### Issue 3: What if slots aren't sequential?

**Solution:** Current approach assumes sequential. If needed, we can add slot detection by scanning metadata tables for subject names.

---

## Next Steps

1. ✅ **Analyze table structure** (DONE)
2. **Implement table range filtering** in `docx_parser.py`
3. **Add `extract_hyperlinks_for_slot()`** method
4. **Update `batch_processor.py`** to use new method
5. **Add unit tests**
6. **Test with W44 files**
7. **Verify no cross-contamination**

---

**This is a much simpler solution than originally planned, thanks to the diagnostic data!** 🎯
