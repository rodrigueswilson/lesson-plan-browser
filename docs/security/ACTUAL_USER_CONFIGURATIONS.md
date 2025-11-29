# Actual User Configurations - Variable Slot Counts

**Date:** October 5, 2025  
**Key Insight:** Users have different numbers of slots (not fixed at 6)

---

## User 1: Wilson Rodrigues (5 Slots)

**Base Path:** `F:\rodri\Documents\OneDrive\AS\Lesson Plan`

### Slot Configuration:

| Slot | Teacher | Subject | Grade | Homeroom | File Pattern |
|------|---------|---------|-------|----------|--------------|
| 1 | Lang | ELA | 3 | T5 | `Lang Lesson Plans 10_6_25-10_10_25.docx` |
| 2 | Savoca | ELA/SS | 2 | 209 | `Ms. Savoca-10_6_25-10_10_25 Lesson plans.docx` |
| 3 | Savoca | Math | 2 | 209 | `Ms. Savoca-10_6_25-10_10_25 Lesson plans.docx` |
| 4 | Savoca | Science | 2 | 209 | `Ms. Savoca-10_6_25-10_10_25 Lesson plans.docx` |
| 5 | Davies | Math | 3 | T2 | `10_6-10_10 Davies Lesson Plans.docx` |

**Key Observations:**
- **5 slots total** (not 6)
- **Savoca teaches 3 subjects** (slots 2, 3, 4) - same file, different subjects
- **Mixed grades:** 2nd and 3rd grade
- **Lang** appears only once (ELA)
- **Davies** appears only once (Math)

### Grade Distribution:
- **Grade 2:** 3 slots (Savoca: ELA/SS, Math, Science)
- **Grade 3:** 2 slots (Lang: ELA, Davies: Math)

---

## User 2: Daniela Silva (5 Slots)

**Base Path:** `F:\rodri\Documents\OneDrive\AS\Daniela LP`

### Slot Configuration:

| Slot | Teacher | Subject | Grade | Homeroom | File Pattern |
|------|---------|---------|-------|----------|--------------|
| 1 | Coleman | Social Studies | 7 | 7A | `Name_ Ariel Coleman 9-29.docx` |
| 2 | Laverty | Math | 5 | 5A | `_Brooke Laverty - SY'25-26_ week of 9_29.docx` |
| 3 | Piret | ELA | 5 | 315 | `Piret Lesson Plans 9_29_25-10_3_25.docx` |
| 4 | Lonesky | Social Studies | 5 | 5B | `Lonesky Week 5 Lesson Plans SY 25_26.docx` |
| 5 | Lonesky | Science | 5 | 5B | `Lonesky Week 5 Lesson Plans SY 25_26.docx` |

**Key Observations:**
- **5 slots total** (not 6)
- **Lonesky teaches 2 subjects** (slots 4, 5) - same file, different subjects
- **Mixed grades:** 5th and 7th grade
- **Coleman** teaches 7th grade (only 7th grade slot)
- **Laverty, Piret** appear once each

### Grade Distribution:
- **Grade 5:** 4 slots (Laverty: Math, Piret: ELA, Lonesky: SS & Science)
- **Grade 7:** 1 slot (Coleman: Social Studies)

---

## System Requirements for Variable Slots

### 1. Database Flexibility ✅

**Current Schema:**
```sql
CREATE TABLE class_slots (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    slot_number INTEGER NOT NULL,  -- Can be 1-10, not fixed
    subject TEXT NOT NULL,
    grade TEXT NOT NULL,
    homeroom TEXT,
    primary_teacher_name TEXT,
    display_order INTEGER DEFAULT NULL,
    UNIQUE(user_id, slot_number)
);
```

**No changes needed** - already supports variable slot counts!

### 2. UI Flexibility

**Add/Remove Slots:**
```
┌─────────────────────────────────────────────────┐
│  Configure Class Slots - Wilson Rodrigues        │
├─────────────────────────────────────────────────┤
│                                                  │
│  Current slots: 5                                │
│                                                  │
│  [Slot 1] [Slot 2] [Slot 3] [Slot 4] [Slot 5]   │
│                                                  │
│  [+ Add Another Slot] (max 10)                   │
│                                                  │
│  Each slot can be removed individually           │
└─────────────────────────────────────────────────┘
```

### 3. Processing Logic

```python
def process_user_week(user_id, week_of):
    """Process all slots for user (variable count)."""
    
    # Get all slots for user (could be 1-10)
    slots = db.get_user_slots(user_id)
    
    print(f"Processing {len(slots)} slots for user")
    
    # Process each slot
    for slot in slots:
        process_slot(slot, week_of)
    
    # Combine in display order
    sorted_slots = sorted(slots, key=lambda s: s.get('display_order') or s['slot_number'])
    
    return combine_lessons(sorted_slots)
```

### 4. Validation

```python
def validate_slot_configuration(user_id):
    """Validate user's slot configuration."""
    
    slots = db.get_user_slots(user_id)
    
    warnings = []
    
    # Check slot count
    if len(slots) == 0:
        warnings.append("No slots configured")
    elif len(slots) > 10:
        warnings.append(f"Too many slots ({len(slots)}). Maximum is 10.")
    
    # Check for duplicate slot numbers
    slot_numbers = [s['slot_number'] for s in slots]
    if len(slot_numbers) != len(set(slot_numbers)):
        warnings.append("Duplicate slot numbers detected")
    
    # Check for same teacher/subject in multiple slots
    teacher_subject_pairs = [(s['teacher_name'], s['subject']) for s in slots]
    duplicates = [pair for pair in teacher_subject_pairs if teacher_subject_pairs.count(pair) > 1]
    if duplicates:
        warnings.append(f"Same teacher/subject in multiple slots: {duplicates}")
    
    return warnings
```

---

## Same Teacher, Multiple Subjects

### Wilson's Case: Savoca (3 subjects)

**Configuration:**
```
Slot 2: Savoca → ELA/SS (Grade 2)
Slot 3: Savoca → Math (Grade 2)
Slot 4: Savoca → Science (Grade 2)
```

**File Finding:**
```python
# All three slots find the same file
file = "Ms. Savoca-10_6_25-10_10_25 Lesson plans.docx"

# But extract different subjects
Slot 2 extracts: Table 0-1 (ELA/SS)
Slot 3 extracts: Table 2-3 (Math)
Slot 4 extracts: Table 4-5 (Science)
```

### Daniela's Case: Lonesky (2 subjects)

**Configuration:**
```
Slot 4: Lonesky → Social Studies (Grade 5)
Slot 5: Lonesky → Science (Grade 5)
```

**File Finding:**
```python
# Both slots find the same file
file = "Lonesky Week 5 Lesson Plans SY 25_26.docx"

# But extract different subjects
Slot 4 extracts: Social Studies section
Slot 5 extracts: Science section
```

---

## Grade-Level Adaptations

### Wilson's Mixed Grades (2nd & 3rd)

**Grade 2 (Slots 2, 3, 4 - Savoca):**
- Age: 7-8 years
- WIDA: K-2 standards
- Vocabulary: Simple (1-2 syllables)
- Activities: Concrete, hands-on
- Portuguese: Basic cognates

**Grade 3 (Slots 1, 5 - Lang, Davies):**
- Age: 8-9 years
- WIDA: 3-5 standards
- Vocabulary: Moderate (2-3 syllables)
- Activities: Mix of concrete and abstract
- Portuguese: Common cognates + phrases

### Daniela's Mixed Grades (5th & 7th)

**Grade 5 (Slots 2, 3, 4, 5):**
- Age: 10-11 years
- WIDA: 3-5 standards
- Vocabulary: Moderate to advanced
- Activities: Abstract thinking emerging
- Portuguese: Academic cognates

**Grade 7 (Slot 1 - Coleman):**
- Age: 12-13 years
- WIDA: 6-8 standards
- Vocabulary: Advanced (3+ syllables)
- Activities: Abstract thinking expected
- Portuguese: Academic language

---

## Output File Structure

### Wilson's Output (5 lessons):

```
Wilson_Rodrigues_Lesson_plan_W41_10-06-10-10.docx

Page 1-2:   Slot 1 - ELA (Lang, Grade 3)
Page 3-4:   Slot 2 - ELA/SS (Savoca, Grade 2)
Page 5-6:   Slot 3 - Math (Savoca, Grade 2)
Page 7-8:   Slot 4 - Science (Savoca, Grade 2)
Page 9-10:  Slot 5 - Math (Davies, Grade 3)
Page 11:    Signature
```

### Daniela's Output (5 lessons):

```
Daniela_Silva_Lesson_plan_W40_09-29-10-03.docx

Page 1-2:   Slot 1 - SS (Coleman, Grade 7)
Page 3-4:   Slot 2 - Math (Laverty, Grade 5)
Page 5-6:   Slot 3 - ELA (Piret, Grade 5)
Page 7-8:   Slot 4 - SS (Lonesky, Grade 5)
Page 9-10:  Slot 5 - Science (Lonesky, Grade 5)
Page 11:    Signature
```

---

## UI Mockup: Variable Slot Management

```
┌─────────────────────────────────────────────────┐
│  Manage Slots - Wilson Rodrigues                 │
├─────────────────────────────────────────────────┤
│                                                  │
│  Total Slots: 5 / 10                             │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ ☰ Slot 1: ELA (Lang, Grade 3)      [×] │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │ ☰ Slot 2: ELA/SS (Savoca, Grade 2) [×] │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │ ☰ Slot 3: Math (Savoca, Grade 2)   [×] │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │ ☰ Slot 4: Science (Savoca, Grade 2)[×] │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │ ☰ Slot 5: Math (Davies, Grade 3)   [×] │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  [+ Add Slot 6]                                  │
│                                                  │
│  ☰ = Drag to reorder                             │
│  [×] = Remove slot                               │
└─────────────────────────────────────────────────┘
```

---

## Key Takeaways

### 1. Variable Slot Count ✅
- **Not fixed at 6**
- Each user can have 1-10 slots
- UI must support add/remove

### 2. Same Teacher, Multiple Subjects ✅
- Savoca: 3 subjects (Wilson)
- Lonesky: 2 subjects (Daniela)
- System finds same file, extracts different subjects

### 3. Mixed Grade Levels ✅
- Wilson: Grades 2 & 3
- Daniela: Grades 5 & 7
- LLM adapts per slot's grade

### 4. Flexible Processing ✅
- Process N slots (not fixed 6)
- Combine in display order
- Handle any slot configuration

---

## Implementation Checklist

### Backend ✅
- [x] Database supports variable slots
- [x] No hardcoded slot count
- [x] Processes any number of slots

### UI (To Do)
- [ ] Add/remove slot buttons
- [ ] Slot counter (X / 10)
- [ ] Drag & drop reordering
- [ ] Remove confirmation dialog

### Testing
- [ ] Test with 1 slot
- [ ] Test with 5 slots (Wilson & Daniela)
- [ ] Test with 10 slots (max)
- [ ] Test same teacher, multiple subjects
- [ ] Test mixed grades

---

**Status:** System is flexible and ready for variable slot counts! 🎯
