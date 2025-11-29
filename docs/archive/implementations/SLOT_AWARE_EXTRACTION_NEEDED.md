# Slot-Aware Hyperlink Extraction Needed

## Status: 🔴 CRITICAL ISSUE IDENTIFIED

The diagnostic logs revealed the TRUE root cause of cross-contamination.

---

## The Real Problem

### Current Behavior:
1. Each teacher's DOCX file contains **MULTIPLE slots** (ELA, Math, Science, etc.)
2. Each slot has its own **2-table structure** (metadata + daily plans)
3. When we call `parser.extract_hyperlinks()`, it extracts **ALL hyperlinks from the entire file**
4. So Slot 1 (ELA) gets hyperlinks from Slots 2, 3, 4, 5 (Math, Science, etc.)

### Evidence from Diagnostic Logs:
```json
// 01_parser_slot1_001.json
{
  "source_file": "Lang Lesson Plans 10_27_25-10_31_25.docx",
  "hyperlink_count": 94,
  "hyperlinks": [
    {"text": "navigation by stars", ...},  // ELA link
    {"text": "LESSON 9: MEASURE TO FIND THE AREA", ...},  // MATH link!
    {"text": "LESSON 10: SOLVE AREA PROBLEMS", ...},  // MATH link!
    {"text": "LESSON 11: AREA AND THE MULTIPLICATION TABLE", ...}  // MATH link!
  ]
}
```

**The ELA slot extraction got Math hyperlinks because they're in the same file!**

---

## The Solution

### Add Slot-Aware Extraction to DOCXParser

The parser needs to:
1. **Identify which tables belong to which slot**
2. **Extract hyperlinks only from that slot's tables**
3. **Ignore hyperlinks from other slots' tables**

### Implementation Approach

#### Option 1: Table Index Range
```python
def extract_hyperlinks(self, table_start_idx: int = None, table_end_idx: int = None):
    """
    Extract hyperlinks from specific table range.
    
    Args:
        table_start_idx: First table to include (e.g., 0 for slot 1)
        table_end_idx: Last table to include (e.g., 1 for slot 1's 2 tables)
    """
    # Only extract from tables[table_start_idx:table_end_idx+1]
```

**Usage:**
```python
# Slot 1: Tables 0-1
hyperlinks = parser.extract_hyperlinks(table_start_idx=0, table_end_idx=1)

# Slot 2: Tables 2-3
hyperlinks = parser.extract_hyperlinks(table_start_idx=2, table_end_idx=3)

# Slot 3: Tables 4-5
hyperlinks = parser.extract_hyperlinks(table_start_idx=4, table_end_idx=5)
```

#### Option 2: Slot Number Parameter
```python
def extract_hyperlinks_for_slot(self, slot_number: int):
    """
    Extract hyperlinks for specific slot.
    
    Assumes each slot has 2 tables (metadata + daily plans).
    Slot 1 = tables 0-1
    Slot 2 = tables 2-3
    etc.
    """
    table_start = (slot_number - 1) * 2
    table_end = table_start + 1
    return self.extract_hyperlinks(table_start, table_end)
```

**Usage:**
```python
# Much cleaner!
hyperlinks = parser.extract_hyperlinks_for_slot(slot_number=1)
```

---

## Required Changes

### 1. Update DOCXParser (`tools/docx_parser.py`)

Add slot-aware extraction methods:
- `extract_hyperlinks_for_slot(slot_number)` 
- `extract_images_for_slot(slot_number)`
- Update `extract_hyperlinks()` to accept table range parameters

### 2. Update BatchProcessor (`tools/batch_processor.py`)

Change from:
```python
hyperlinks = await asyncio.to_thread(parser.extract_hyperlinks)
images = await asyncio.to_thread(parser.extract_images)
```

To:
```python
slot_num = slot['slot_number']
hyperlinks = await asyncio.to_thread(parser.extract_hyperlinks_for_slot, slot_num)
images = await asyncio.to_thread(parser.extract_images_for_slot, slot_num)
```

### 3. Handle Edge Cases

- **What if file doesn't have expected number of tables?**
  - Log warning and extract from all tables (fallback to current behavior)
  
- **What if slot structure is different?**
  - Add validation to check table count
  - Provide clear error messages

---

## Expected Result After Fix

### Before Fix:
```json
// Slot 1 (ELA) - WRONG
{
  "hyperlinks": [
    "navigation by stars",  // ELA ✓
    "LESSON 9: MEASURE TO FIND THE AREA",  // Math ✗
    "LESSON 10: SOLVE AREA PROBLEMS"  // Math ✗
  ]
}
```

### After Fix:
```json
// Slot 1 (ELA) - CORRECT
{
  "hyperlinks": [
    "navigation by stars",  // ELA ✓
    "Culminating Task: Reading New Jersey Maps"  // ELA ✓
  ]
}

// Slot 5 (Math) - CORRECT
{
  "hyperlinks": [
    "LESSON 9: MEASURE TO FIND THE AREA",  // Math ✓
    "LESSON 10: SOLVE AREA PROBLEMS"  // Math ✓
  ]
}
```

---

## Testing Plan

1. **Add unit tests** for slot-aware extraction
2. **Test with W44 files** (known to have 5 slots)
3. **Check diagnostic logs** to verify correct extraction
4. **Verify output DOCX** has no cross-contamination

---

## Priority

**🔴 CRITICAL** - This is the actual root cause of cross-contamination.

The metadata fix we implemented was correct, but it can't filter out hyperlinks that shouldn't have been extracted in the first place!

---

**This explains everything! The diagnostic logs did their job perfectly.** 🎯
