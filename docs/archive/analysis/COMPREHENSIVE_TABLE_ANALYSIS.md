# Comprehensive Table Structure Analysis

## Dataset

- **Total files analyzed:** 141
- **Successfully analyzed:** 140 (99.3%)
- **Errors:** 1 (0.7%)
- **Sources:**
  - Daniela LP: 46 files
  - Lesson Plan: 95 files

---

## Key Findings

### 1. Table Count Distribution

| Tables | Files | Percentage | Likely Structure |
|--------|-------|------------|------------------|
| 0 | 5 | 3.6% | Empty/corrupted |
| 1 | 4 | 2.9% | Single table only |
| 2 | 2 | 1.4% | 1 slot (no signature) |
| 3 | 28 | 20.0% | 1 slot + signature |
| 4 | 15 | 10.7% | 2 slots (no signature) |
| 5 | 4 | 2.9% | 2 slots + signature |
| 6 | 7 | 5.0% | 3 slots (no signature) |
| **9** | **37** | **26.4%** | **4 slots + signature** ⭐ |
| **11** | **31** | **22.1%** | **5 slots + signature** ⭐ |
| 12 | 1 | 0.7% | 6 slots (no signature) |
| 13 | 4 | 2.9% | 6 slots + signature |
| 14 | 1 | 0.7% | 7 slots (no signature) |
| 159 | 1 | 0.7% | Anomaly |

### 2. Most Common Structures

**Top 3:**
1. **9 tables (4 slots)** - 37 files (26.4%) ← W44 files
2. **11 tables (5 slots)** - 31 files (22.1%)
3. **3 tables (1 slot)** - 28 files (20.0%)

### 3. Slot Distribution

| Slots | Files | Percentage |
|-------|-------|------------|
| 0 | 10 | 7.1% |
| 1 | 43 | 30.7% |
| 2 | 12 | 8.6% |
| **4** | **37** | **26.4%** ⭐ |
| **5** | **31** | **22.1%** ⭐ |
| 6 | 6 | 4.3% |

### 4. Signature Table

- **With signature:** 125 files (89.3%)
- **Without signature:** 15 files (10.7%)

**Most files have a signature table at the end!**

---

## Critical Insights

### ❌ The "2 tables per slot" assumption is WRONG for many files!

**Reality:**
- **48.5%** of files have 4-5 slots (multi-teacher files)
- **30.7%** of files have 1 slot (single-teacher files)
- **Structure varies widely**

### ✅ What's Consistent:

1. **Signature table detection works** (89.3% have it)
2. **Pattern: Even number of tables + 1 signature** (for multi-slot files)
3. **Single-slot files:** 3 tables (metadata + daily + signature)
4. **Multi-slot files:** 2N + 1 tables (N slots × 2 tables + 1 signature)

---

## Revised Implementation Strategy

### Problem with Original Plan:

The original plan assumed:
```python
slot_N_tables = [(N-1)*2, (N-1)*2+1]
```

**This only works for 4-5 slot files!**

For 1-slot files (30.7% of dataset):
- Table 0: Metadata
- Table 1: Daily plans
- Table 2: Signature

Using `(1-1)*2 = 0, 1` would work, but we'd need to know it's a 1-slot file first.

### Better Approach: Content-Based Detection

Instead of assuming table positions, **detect slot boundaries by content**:

1. **Scan all tables** and identify metadata tables (contain "Name:", "Subject:", etc.)
2. **Build a slot map:** `{slot_1: [table_0, table_1], slot_2: [table_2, table_3], ...}`
3. **Extract hyperlinks** only from tables in the slot's map
4. **Exclude signature table** (last table with "Signature" in first cell)

### Algorithm:

```python
def build_slot_map(doc):
    """Build map of which tables belong to which slot."""
    slot_map = {}
    current_slot = None
    
    for idx, table in enumerate(doc.tables):
        # Check if this is a metadata table
        if is_metadata_table(table):
            # Start new slot
            current_slot = len(slot_map) + 1
            slot_map[current_slot] = [idx]
        elif current_slot is not None:
            # Add to current slot (daily plans table)
            slot_map[current_slot].append(idx)
            current_slot = None  # Reset for next slot
    
    # Remove signature table if present
    if doc.tables:
        last_table = doc.tables[-1]
        if is_signature_table(last_table):
            # Remove last table from any slot
            for slot_tables in slot_map.values():
                if len(doc.tables) - 1 in slot_tables:
                    slot_tables.remove(len(doc.tables) - 1)
    
    return slot_map

def extract_hyperlinks_for_slot(self, slot_number: int):
    """Extract hyperlinks for specific slot using content detection."""
    slot_map = self.build_slot_map(self.doc)
    
    if slot_number not in slot_map:
        logger.warning(f"Slot {slot_number} not found in document")
        return []
    
    table_indices = slot_map[slot_number]
    
    # Extract only from these tables
    hyperlinks = []
    for table_idx in table_indices:
        hyperlinks.extend(self._extract_hyperlinks_from_table(table_idx))
    
    return hyperlinks
```

---

## Implementation Plan (Revised)

### Phase 1: Add Content Detection

1. **Add `is_metadata_table(table)`** - Detect by "Name:", "Subject:", etc.
2. **Add `is_signature_table(table)`** - Detect by "Signature" in first cell
3. **Add `build_slot_map(doc)`** - Map slot numbers to table indices

### Phase 2: Update Extraction

1. **Modify `extract_hyperlinks()`** to accept list of table indices
2. **Add `extract_hyperlinks_for_slot(slot_number)`** using slot map
3. **Same for images**

### Phase 3: Update Batch Processor

1. **Pass slot number to extraction methods**
2. **Log slot map for debugging**

### Phase 4: Testing

1. **Test with 1-slot files** (30.7% of dataset)
2. **Test with 4-slot files** (26.4% of dataset)
3. **Test with 5-slot files** (22.1% of dataset)
4. **Verify signature table excluded**

---

## Advantages of Content-Based Approach

✅ **Works for all file structures** (1-slot, 4-slot, 5-slot, etc.)
✅ **Robust to variations** (extra tables, missing tables)
✅ **Self-documenting** (slot map shows structure)
✅ **Easy to debug** (can log slot map)
✅ **Handles edge cases** (files without signature, etc.)

---

## Next Steps

1. Implement content-based slot detection
2. Test on sample files from each category
3. Verify cross-contamination is eliminated
4. Deploy and test with real processing

---

**The data shows we need a more flexible approach than fixed table indices!** 📊
