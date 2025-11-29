# Subject-Based Slot Detection - CRITICAL FIX

## Status: ✅ IMPLEMENTED

**Problem:** Slot numbers don't align between source files and weekly plan configuration, causing wrong content extraction.

---

## The Issue

### Misaligned Slot Numbers

**Savoca Source File:**
```
Slot 1: ELA/SS (tables 0-1) - "Unit 2 Lesson 17 SIPPS"
Slot 2: Math (tables 2-3) - "Unit 2 lesson 8 Subtract Your Way"
Slot 3: Science (tables 4-5)
Slot 4: Social Studies (tables 6-7)
```

**Wilson Weekly Plan Config:**
```
Slot 1: Social Studies (Lang file)
Slot 2: ELA/SS (Savoca file) ← Wants ELA/SS content
Slot 3: Science (Savoca file)
Slot 4: Math (Savoca file)
Slot 5: Math (Davies file)
```

### What Was Happening

When processing Slot 2 (ELA/SS) from Savoca file:
1. Code requested: `extract_subject_content_for_slot(slot_number=2, subject="ELA/SS")`
2. Code extracted from: **Tables 2-3** (Slot 2 in file)
3. But tables 2-3 contain: **Math content** ("Subtract Your Way")
4. Result: **Math content in ELA/SS slot!**

---

## The Solution

### Subject-Based Slot Detection

Instead of assuming slot numbers align, **scan metadata tables to find which slot contains the requested subject**.

### New Method: `find_slot_by_subject()`

```python
def find_slot_by_subject(self, subject: str) -> int:
    """
    Find which slot contains the given subject by scanning metadata tables.
    
    Handles misaligned slot numbers between source file and weekly plan config.
    """
    # Normalize subject and get aliases
    subject_lower = subject.lower().strip()
    possible_names = get_subject_aliases(subject_lower)
    
    # Scan each slot's metadata table
    for slot_num in range(1, available_slots + 1):
        meta_table = self.doc.tables[slot_start]
        
        # Look for "Subject:" field in metadata
        for row in meta_table.rows:
            for cell in row.cells:
                if 'subject:' in cell.text.lower():
                    subject_value = cell.text.split('subject:')[-1].strip()
                    
                    # Check if it matches requested subject
                    if any(name in subject_value.lower() for name in possible_names):
                        return slot_num  # Found it!
    
    raise ValueError(f"Subject '{subject}' not found in any slot")
```

### Updated Extraction Flow

**Before:**
```python
# Assumed slot numbers align
slot_num = slot['slot_number']  # 2
extract_from_tables(slot_num)  # Extracts from tables 2-3 (wrong!)
```

**After:**
```python
# Find actual slot by subject
actual_slot_num = parser.find_slot_by_subject(slot['subject'])  # Returns 1 (ELA/SS is in Slot 1)
if actual_slot_num != slot['slot_number']:
    logger.warning("Slot mismatch detected!")
slot_num = actual_slot_num  # Use 1
extract_from_tables(slot_num)  # Extracts from tables 0-1 (correct!)
```

---

## Implementation Details

### Subject Aliases

Flexible matching handles variations:
```python
subject_mappings = {
    'ela': ['ela', 'english', 'language arts', 'reading', 'literacy', 'ela/ss'],
    'math': ['math', 'mathematics'],
    'science': ['science', 'sci', 'science/health'],
    'social studies': ['ss', 'social studies', 'history', 'ela/ss'],
    'ela/ss': ['ela/ss', 'language arts/social studies', 'ela', 'ss']
}
```

### Metadata Scanning

Looks for "Subject:" field in metadata tables:
```
| Name: Donna Savoca | Grade: 2 | Homeroom: 209 | Subject: ELA/SS | Week of: 10/27-10/31 |
                                                   ^^^^^^^^^^^^^^^^
                                                   Matches here!
```

### Fallback Behavior

If subject not found in metadata:
1. Log warning
2. Fall back to requested slot number
3. Continue processing (don't crash)

---

## Files Modified

### 1. tools/docx_parser.py (+79 lines)

**Added `find_slot_by_subject()` method:**
- Scans metadata tables for subject field
- Returns actual slot number containing subject
- Handles subject aliases and variations

**Updated `extract_subject_content_for_slot()`:**
- Calls `find_slot_by_subject()` first
- Logs warning if mismatch detected
- Uses actual slot number for extraction

### 2. tools/batch_processor.py (+18 lines)

**Added subject detection before extraction:**
```python
# Find actual slot by subject
actual_slot_num = await asyncio.to_thread(parser.find_slot_by_subject, slot['subject'])
if actual_slot_num != slot['slot_number']:
    logger.warning("slot_subject_mismatch", ...)
slot_num = actual_slot_num

# Use actual slot for all extractions
images = await asyncio.to_thread(parser.extract_images_for_slot, slot_num)
hyperlinks = await asyncio.to_thread(parser.extract_hyperlinks_for_slot, slot_num)
content = await asyncio.to_thread(parser.extract_subject_content_for_slot, slot_num, subject)
```

---

## Expected Behavior After Fix

### Savoca File Processing

**Slot 2 (ELA/SS) - Wilson Config:**
```
DEBUG: Finding actual slot for subject 'ELA/SS'
DEBUG: Slot mismatch! Requested slot 2, found subject in slot 1
INFO: subject_slot_found - ELA/SS found in slot 1
DEBUG: Extracting from slot 1 (tables 0-1)
Result: ✅ ELA/SS content ("Unit 2 Lesson 17 SIPPS")
```

**Slot 4 (Math) - Wilson Config:**
```
DEBUG: Finding actual slot for subject 'Math'
DEBUG: Slot mismatch! Requested slot 4, found subject in slot 2
INFO: subject_slot_found - Math found in slot 2
DEBUG: Extracting from slot 2 (tables 2-3)
Result: ✅ Math content ("Unit 2 lesson 8 Subtract Your Way")
```

---

## Logging & Diagnostics

### New Log Events

1. **`subject_slot_found`** - Subject successfully located
   ```json
   {
     "requested_subject": "ELA/SS",
     "found_in_slot": 1,
     "metadata_subject": "ela/ss"
   }
   ```

2. **`slot_number_mismatch`** - Mismatch detected
   ```json
   {
     "requested_slot": 2,
     "actual_slot": 1,
     "subject": "ELA/SS",
     "message": "Slot 2 requested but subject 'ELA/SS' found in slot 1"
   }
   ```

3. **`subject_slot_detection_failed`** - Fallback to requested slot
   ```json
   {
     "slot_number": 2,
     "subject": "Unknown Subject",
     "error": "Subject 'Unknown Subject' not found in any slot",
     "fallback": "using requested slot number"
   }
   ```

4. **`slot_subject_mismatch`** - Batch processor warning
   ```json
   {
     "requested_slot": 2,
     "actual_slot": 1,
     "subject": "ELA/SS",
     "file": "Ms. Savoca-10_27_25-10_31_25 Lesson plans.docx"
   }
   ```

---

## Why This Wasn't Caught Earlier

1. **Test files had aligned slot numbers** - No mismatches
2. **Single-subject files** - No ambiguity
3. **Assumed consistent structure** - Didn't account for variations

---

## Edge Cases Handled

### 1. Subject Not in Metadata
- Falls back to requested slot number
- Logs warning
- Continues processing

### 2. Multiple Matches
- Returns first match found
- Scans slots in order (1, 2, 3, ...)

### 3. Subject Aliases
- "ELA" matches "ELA/SS"
- "Math" matches "Mathematics"
- "SS" matches "Social Studies"

### 4. Case Insensitivity
- "ELA/SS" matches "ela/ss"
- "MATH" matches "math"

---

## Testing

### Test Case 1: Savoca File
```
Source: Slot 1 = ELA/SS, Slot 2 = Math
Config: Slot 2 = ELA/SS, Slot 4 = Math

Expected:
- Slot 2 extracts from source Slot 1 (ELA/SS content)
- Slot 4 extracts from source Slot 2 (Math content)

Result: ✅ Correct content extracted
```

### Test Case 2: Aligned Slots
```
Source: Slot 1 = ELA, Slot 2 = Math
Config: Slot 1 = ELA, Slot 2 = Math

Expected:
- No mismatch warnings
- Direct extraction

Result: ✅ Works as before
```

### Test Case 3: Subject Not Found
```
Config: Slot 5 = "Unknown Subject"

Expected:
- Warning logged
- Falls back to slot 5
- Continues processing

Result: ✅ Graceful fallback
```

---

## Impact

**Severity:** CRITICAL - Prevented correct content extraction

**Scope:** Any multi-slot file with non-aligned slot numbers

**Fix Complexity:** Medium - New detection method + integration

**Risk:** Low - Fallback ensures backward compatibility

---

## Related Fixes

This completes the slot-aware extraction trilogy:
1. ✅ **Hyperlink/Image extraction** - Slot-aware by table index
2. ✅ **Content extraction** - Slot-aware by table index
3. ✅ **Subject detection** - Finds correct slot by metadata

---

**Status:** Ready for production! Subject-based slot detection implemented. 🎯
