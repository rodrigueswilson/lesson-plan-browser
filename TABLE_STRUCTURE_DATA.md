# Table Structure Data - W44 Files

## Status: ✅ DATA COLLECTED

Analyzed 3 W44 input files without LLM processing.

---

## Key Findings

### 100% Consistent Structure Across All Files:

**Pattern:**
```
Table 0: Slot 1 Metadata (Name: [Teacher])
Table 1: Slot 1 Daily Plans (MONDAY | TUESDAY | ...)
Table 2: Slot 2 Metadata (Name: [Teacher])
Table 3: Slot 2 Daily Plans (MONDAY | TUESDAY | ...)
Table 4: Slot 3 Metadata (Name: [Teacher])
Table 5: Slot 3 Daily Plans (MONDAY | TUESDAY | ...)
Table 6: Slot 4 Metadata (Name: [Teacher])
Table 7: Slot 4 Daily Plans (MONDAY | TUESDAY | ...)
Table 8: Signature (Required Signatures)
```

### Detection Rules That Work:

1. **Metadata Table:**
   - First cell contains "Name:"
   - Has 5 columns
   - Has 1 row
   - Contains: Name | Grade | Homeroom | Subject | Week of

2. **Daily Plans Table:**
   - First cell is empty
   - First row contains weekday names (MONDAY, TUESDAY, etc.)
   - Has 6 columns (empty + 5 days)
   - Has 8-9 rows

3. **Signature Table:**
   - First cell contains "Required Signatures"
   - Has 1 column
   - Has 4 rows
   - Always last table (index 8)

---

## Slot Mapping Formula

**For all W44 files:**
```python
slot_number = 1, 2, 3, 4
table_start = (slot_number - 1) * 2  # 0, 2, 4, 6
table_end = table_start + 1           # 1, 3, 5, 7
```

**Signature table:** Always index 8 (excluded from slots)

---

## Validation

### All 3 Files Match:
- ✅ Davies: 4 slots + signature = 9 tables
- ✅ Lang: 4 slots + signature = 9 tables
- ✅ Savoca: 4 slots + signature = 9 tables

### Subjects Vary by Teacher:
- **Davies:** ELA, Math, Science/Health, Social Studies
- **Lang:** ELA, Math, Science/Health, Social Studies
- **Savoca:** ELA/SS, Math, Science, Health

---

## Implementation Plan

### Step 1: Simple Slot Detection

```python
def detect_slot_tables(doc):
    """Detect which tables belong to which slots."""
    slot_map = {}
    
    for idx, table in enumerate(doc.tables):
        # Skip if no rows
        if not table.rows or not table.rows[0].cells:
            continue
        
        first_cell = table.rows[0].cells[0].text.strip()
        
        # Check if metadata table
        if first_cell.startswith("Name:"):
            # This is a metadata table - start new slot
            slot_num = len(slot_map) + 1
            slot_map[slot_num] = [idx, idx + 1]  # Metadata + Daily Plans
    
    return slot_map
```

### Step 2: Extract with Slot Filtering

```python
def extract_hyperlinks_for_slot(parser, slot_number):
    """Extract hyperlinks only from slot's tables."""
    slot_map = detect_slot_tables(parser.doc)
    
    if slot_number not in slot_map:
        return []
    
    table_indices = slot_map[slot_number]
    hyperlinks = []
    
    # Extract only from this slot's tables
    for table_idx in table_indices:
        if table_idx < len(parser.doc.tables):
            table = parser.doc.tables[table_idx]
            # Extract hyperlinks from this table only
            table_hyperlinks = extract_from_table(table, table_idx)
            hyperlinks.extend(table_hyperlinks)
    
    return hyperlinks
```

### Step 3: Skip Paragraph Links

```python
# Don't extract from paragraphs during slot-specific extraction
# Only extract from the slot's tables
```

---

## Next Steps

### Option A: Implement Now (Recommended)
The structure is 100% consistent. We can safely implement:
1. Slot detection by "Name:" in first cell
2. Extract from tables [slot*2-2, slot*2-1]
3. Exclude table 8 (signature)
4. Skip paragraph extraction

**Time:** 1-2 hours
**Risk:** Low (data is consistent)

### Option B: Add More Validation
Add checks for:
- Table count == 9
- Each metadata table followed by daily plans
- Signature table at end
- Warn if structure doesn't match

**Time:** +30 minutes
**Risk:** Very low

---

## Recommendation

**Implement Option A + B:**

The data shows perfect consistency. We can confidently implement slot-aware extraction with:

1. ✅ Content-based detection ("Name:" in first cell)
2. ✅ Paired table assumption (metadata + daily)
3. ✅ Signature table exclusion (table 8)
4. ✅ Validation (warn if structure unexpected)
5. ✅ Skip paragraph links

**This will eliminate cross-contamination with high confidence!**

---

**Ready to implement?** 🚀
