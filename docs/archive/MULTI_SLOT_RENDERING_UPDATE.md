# Multi-Slot Rendering Update

**Date**: 2025-10-05  
**Issue**: Multi-slot output was combining all slots into one table set  
**Solution**: Created separate table sets for each slot

---

## Problem

The previous multi-slot renderer was combining all 5 slots into a single table, making it hard to read:

```
MONDAY column:
Slot 1: ELA - content
---
Slot 2: Science - content  
---
Slot 3: Math - content
(all in one cell)
```

## User Requirement

Each slot must have **its own complete table set**:
- Metadata table (teacher, grade, subject, homeroom)
- Daily plans table (Monday-Friday with all rows)
- Signature section

Just like the original template, but repeated for each slot.

---

## Solution Implemented

### New File: `tools/docx_renderer_multi_slot.py`

**Key Features**:
1. Extracts individual slot data from merged JSON
2. Creates separate table sets for each slot
3. Adds page breaks between slots
4. Maintains template formatting for each slot

### Updated: `tools/batch_processor.py`

**Logic**:
```python
if len(lessons) > 1:
    # Use multi-slot renderer - separate table sets
    renderer = MultiSlotDOCXRenderer(template_path)
else:
    # Use single-slot renderer - one table set
    renderer = DOCXRenderer(template_path)
```

---

## Output Structure

### For 5 Slots:

**Slot 1: ELA (Lang)**
- Metadata: Teacher=Lang, Grade=3, Subject=ELA
- Daily Plans: Monday-Friday
- Signature box

*[Page Break]*

**Slot 2: Science (Savoca)**
- Metadata: Teacher=Savoca, Grade=3, Subject=Science
- Daily Plans: Monday-Friday
- Signature box

*[Page Break]*

**Slot 3: Math (Davies)**
- Metadata: Teacher=Davies, Grade=3, Subject=Math
- Daily Plans: Monday-Friday
- Signature box

*(etc. for all 5 slots)*

---

## How It Works

### 1. Extract Slots from Merged JSON

Converts multi-slot structure:
```json
{
  "days": {
    "monday": {
      "slots": [
        {"slot_number": 1, "subject": "ELA", ...},
        {"slot_number": 2, "subject": "Science", ...}
      ]
    }
  }
}
```

To individual slot structures:
```json
[
  {
    "metadata": {"subject": "ELA", "teacher_name": "Lang", ...},
    "days": {"monday": {...}, "tuesday": {...}}
  },
  {
    "metadata": {"subject": "Science", "teacher_name": "Savoca", ...},
    "days": {"monday": {...}, "tuesday": {...}}
  }
]
```

### 2. Render Each Slot

For each slot:
1. Add heading: "Slot X: Subject"
2. Copy template tables
3. Fill metadata table
4. Fill daily plans table
5. Add page break (except last slot)

---

## Testing

### To Test the New Renderer:

1. **Restart Backend** (to load new code):
   ```bash
   # Stop current backend (Ctrl+C)
   # Restart
   python -m uvicorn backend.api:app --reload --port 8000
   ```

2. **Generate New Plan**:
   - Use the UI or API to generate a weekly plan
   - Should now see separate table sets for each slot

3. **Verify Output**:
   - Open generated DOCX
   - Check that each slot has its own:
     - Header with slot number and subject
     - Metadata table
     - Daily plans table
     - Page break between slots

---

## Benefits

✅ **Clear Separation**: Each slot is visually distinct  
✅ **Complete Information**: Each slot shows its own teacher, grade, subject  
✅ **Easy to Print**: Can print individual slots if needed  
✅ **Template Compliant**: Each slot follows the original template structure  
✅ **Backward Compatible**: Single-slot plans still work as before  

---

## Next Steps

1. ✅ Restart backend to load new renderer
2. ⏳ Test with UI - generate new plan
3. ⏳ Verify output DOCX has separate table sets
4. ⏳ Adjust formatting if needed (spacing, page breaks, etc.)

---

**Status**: Implementation Complete - Ready for Testing
