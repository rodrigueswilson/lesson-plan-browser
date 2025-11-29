# Final Updates: Coleman Teacher & Slot Ordering

**Date:** October 5, 2025  
**Updates:** Coleman teacher added, Slot ordering system designed

---

## Update 1: Coleman Teacher Added ✅

### Daniela's Complete Teacher List:

| Slot | Teacher | Subject | Grade | File Pattern |
|------|---------|---------|-------|--------------|
| 1 | Lonesky | Science | 6 | `Lonesky Week 5 Lesson Plans SY 25_26.docx` |
| 2 | Laverty | Math | 6 | `_Brooke Laverty - SY'25-26_ week of 9_29.docx` |
| 3 | Piret | ELA | 5 | `Piret Lesson Plans 9_29_25-10_3_25.docx` |
| 4 | **Coleman** | **Social Studies** | **6** | `Name_ Ariel Coleman 9-29.docx` |
| 5 | Lonesky | Science (2nd) | 6 | Same file as slot 1 |
| 6 | Morais | ELA/SS | 6 | `Morais 9_15_25 - 9_19_25.docx` |

**File Matching Test:**
```
✅ Coleman + Social Studies → Name_ Ariel Coleman 9-29.docx
```

---

## Update 2: Slot Ordering System ✅

### Purpose
Allow users to control the order of lessons in the final combined DOCX output.

### Problem Solved
**Before:** Lessons always appear in slot number order (1→2→3→4→5→6)
**After:** User can reorder to any sequence (e.g., Math→Science→ELA→SS)

### UI Feature: Drag & Drop Reordering

```
┌─────────────────────────────────────────────────┐
│  Reorder Lesson Plan Output                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  Drag to reorder how lessons appear in output:  │
│                                                  │
│  ☰ 1. Math (Laverty, Grade 6)           ↕       │
│  ☰ 2. Science (Lonesky, Grade 6)        ↕       │
│  ☰ 3. ELA (Piret, Grade 5)              ↕       │
│  ☰ 4. Social Studies (Coleman, Grade 6) ↕       │
│  ☰ 5. Science Period 2 (Lonesky, G6)    ↕       │
│  ☰ 6. ELA/SS (Morais, Grade 6)          ↕       │
│                                                  │
│  [Reset to Default] [Save Order]                │
└─────────────────────────────────────────────────┘
```

### Database Schema

**Added `display_order` field:**
```sql
ALTER TABLE class_slots 
ADD COLUMN display_order INTEGER DEFAULT NULL;

-- NULL = use slot_number (default order)
-- Integer = custom position in output
```

**Example Data:**
```sql
-- Default order (display_order = NULL)
Slot 1: Science    → Appears 1st
Slot 2: Math       → Appears 2nd
Slot 3: ELA        → Appears 3rd

-- Custom order (display_order set)
Slot 1: Science    → display_order = 2 → Appears 2nd
Slot 2: Math       → display_order = 1 → Appears 1st
Slot 3: ELA        → display_order = 3 → Appears 3rd

Output: Math → Science → ELA
```

### Processing Logic

```python
def get_slots_in_display_order(user_id):
    """Get slots sorted by display order."""
    
    slots = db.get_user_slots(user_id)
    
    # Sort by display_order if set, otherwise slot_number
    sorted_slots = sorted(
        slots, 
        key=lambda s: s.get('display_order') or s['slot_number']
    )
    
    return sorted_slots

def combine_lessons(user_id, lessons, week_of):
    """Combine lessons in user's preferred order."""
    
    # Get slots in display order
    sorted_slots = get_slots_in_display_order(user_id)
    
    combined_doc = Document(template)
    
    # Add lessons in order
    for i, slot in enumerate(sorted_slots):
        lesson = lessons[slot['slot_number']]
        
        # Add lesson content
        add_lesson_to_doc(combined_doc, lesson)
        
        # Add page break (except after last lesson)
        if i < len(sorted_slots) - 1:
            combined_doc.add_page_break()
    
    return combined_doc
```

### UI Behavior

**Initial State:**
- Slots appear in slot number order (1-6)
- `display_order = NULL` for all slots
- No visual indicator

**After Reordering:**
- Slots appear in custom order
- `display_order` saved to database
- Visual indicator: "⚙️ Custom order active"

**Reset Button:**
- Sets `display_order = NULL` for all slots
- Returns to slot number order
- Removes visual indicator

### Preview Screen

```
┌─────────────────────────────────────────────────┐
│  Week 41 Preview - Daniela Silva                 │
├─────────────────────────────────────────────────┤
│                                                  │
│  Output will combine lessons in this order:      │
│  ⚙️ Custom order active                          │
│                                                  │
│  1️⃣ Math (Laverty, Grade 6)                     │
│     ✅ File: _Brooke Laverty - SY'25-26_...     │
│                                                  │
│  2️⃣ Science (Lonesky, Grade 6)                  │
│     ✅ File: Lonesky Week 5 Lesson Plans...     │
│                                                  │
│  3️⃣ ELA (Piret, Grade 5)                        │
│     ✅ File: Piret Lesson Plans 9_29_25...      │
│     ⚠️  Extended format (13 rows)               │
│                                                  │
│  4️⃣ Social Studies (Coleman, Grade 6)           │
│     ✅ File: Name_ Ariel Coleman 9-29.docx      │
│                                                  │
│  5️⃣ Science Period 2 (Lonesky, Grade 6)         │
│     ✅ File: Lonesky Week 5... (same as #2)     │
│                                                  │
│  6️⃣ ELA/SS (Morais, Grade 6)                    │
│     ✅ File: Morais 9_15_25 - 9_19_25.docx      │
│                                                  │
│  [Change Order] [Generate Plan]                  │
└─────────────────────────────────────────────────┘
```

---

## Benefits

### 1. Flexibility
- User controls lesson sequence
- Can group by subject type (all Math together)
- Can order by importance
- Can match school schedule

### 2. Consistency
- Same order every week (if desired)
- Saved per user
- Easy to modify

### 3. User Experience
- Visual drag & drop
- Clear preview of order
- Easy reset to default

---

## Implementation Checklist

### Database ✅
- [x] Add `display_order` column to `class_slots` table
- [x] Update schema documentation

### Backend
- [ ] Add `get_slots_in_display_order()` method
- [ ] Update `combine_lessons()` to use display order
- [ ] Add `update_slot_order()` API endpoint
- [ ] Add `reset_slot_order()` API endpoint

### Frontend (Tauri + React)
- [ ] Drag & drop slot reordering component
- [ ] Visual indicator for custom order
- [ ] Preview screen showing order
- [ ] Reset button
- [ ] Save order button

### Testing
- [ ] Test default order (display_order = NULL)
- [ ] Test custom order
- [ ] Test reset functionality
- [ ] Test with both users (Wilson & Daniela)

---

## API Endpoints Needed

### Update Slot Order
```
PUT /api/users/{user_id}/slots/reorder
Body: {
  "slot_orders": [
    {"slot_number": 1, "display_order": 2},
    {"slot_number": 2, "display_order": 1},
    {"slot_number": 3, "display_order": 3},
    ...
  ]
}
Response: {
  "success": true,
  "message": "Slot order updated"
}
```

### Reset Slot Order
```
POST /api/users/{user_id}/slots/reset-order
Response: {
  "success": true,
  "message": "Slot order reset to default"
}
```

### Get Slots in Display Order
```
GET /api/users/{user_id}/slots?ordered=true
Response: [
  {
    "slot_number": 2,
    "subject": "Math",
    "display_order": 1,  // Appears first
    ...
  },
  {
    "slot_number": 1,
    "subject": "Science",
    "display_order": 2,  // Appears second
    ...
  },
  ...
]
```

---

## Example Use Cases

### Use Case 1: Match School Schedule
**Scenario:** Daniela's school schedule is Math→Science→ELA→SS

**Configuration:**
```
Slot 2 (Math)     → display_order = 1
Slot 1 (Science)  → display_order = 2
Slot 3 (ELA)      → display_order = 3
Slot 4 (SS)       → display_order = 4
```

**Result:** Output matches school schedule order

### Use Case 2: Group by Subject Type
**Scenario:** Wilson wants all language arts together

**Configuration:**
```
Slot 2 (ELA)      → display_order = 1
Slot 4 (SS)       → display_order = 2  (reading-heavy)
Slot 1 (Math)     → display_order = 3
Slot 3 (Science)  → display_order = 4
```

**Result:** Language-focused subjects first, then STEM

### Use Case 3: Priority Order
**Scenario:** Daniela wants most important subjects first

**Configuration:**
```
Slot 2 (Math)     → display_order = 1  (priority)
Slot 3 (ELA)      → display_order = 2  (priority)
Slot 1 (Science)  → display_order = 3
Slot 4 (SS)       → display_order = 4
```

**Result:** Core subjects appear first in output

---

## Summary

### Updates Made:
1. ✅ **Coleman teacher** added to Daniela's configuration
2. ✅ **Slot ordering system** designed and specified
3. ✅ **Database schema** updated with `display_order` field
4. ✅ **UI mockups** created for drag & drop interface
5. ✅ **Processing logic** defined for custom ordering

### Ready For:
- API endpoint implementation
- Frontend UI development
- Testing with real data

**Status:** Specification complete, ready for implementation! 🎯
