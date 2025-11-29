# UI/Processing Specification - Grade-Aware Lesson Plan Generation

## Overview

The system needs to:
1. **Select** the correct lesson block from primary teacher's file
2. **Extract** content based on teacher name, subject, and grade
3. **Transform** with LLM using grade-appropriate language and strategies
4. **Generate** bilingual lesson plan matched to developmental stage

---

## Selection Criteria (3-Part Match)

### 1. Teacher Name Match
**Purpose:** Find the correct file
**How:** File manager searches by teacher name pattern

```python
# User configures slot
slot = {
    'teacher_name': 'Davies',      # ← Matches filename
    'subject': 'Math',             # ← Matches subject in header table
    'grade': '3'                   # ← Determines LLM adaptation
}

# System finds file
file = find_file(teacher_name='Davies')
# Result: "10_6-10_10 Davies Lesson Plans.docx"
```

### 2. Subject Match
**Purpose:** Extract the correct lesson block from file
**How:** Parser finds header table with matching subject

```python
# Davies file has 4 subjects:
# - Table 0-1: ELA
# - Table 2-3: Math      ← Match!
# - Table 4-5: Social Studies
# - Table 6-7: Science/Health

parser.extract_subject_content('Math')
# Returns: Content from Table 3 (Math lesson table)
```

### 3. Grade Level Match
**Purpose:** Adapt LLM transformation to developmental stage
**How:** Pass grade to LLM for age-appropriate language

```python
# LLM receives:
{
    'content': '[Math lesson content]',
    'grade': '3',              # ← 3rd grade = 8-9 years old
    'subject': 'Math'
}

# LLM adapts:
# - Vocabulary complexity
# - Sentence structure
# - Cognitive expectations
# - WIDA standards for grade band
```

---

## Grade-Level Adaptations

### Grade Bands & Developmental Stages

**K-2 (Ages 5-8) - Early Elementary**
- Simple vocabulary (1-2 syllable words)
- Short sentences (5-8 words)
- Concrete, hands-on activities
- Visual supports essential
- WIDA: K-2 standards
- Portuguese: Basic cognates only

**3-5 (Ages 8-11) - Upper Elementary**
- Moderate vocabulary (2-3 syllable words)
- Medium sentences (8-12 words)
- Mix of concrete and abstract concepts
- Visual + textual supports
- WIDA: 3-5 standards
- Portuguese: Common cognates + phrases

**6-8 (Ages 11-14) - Middle School**
- Advanced vocabulary (3+ syllable words)
- Complex sentences (12-15 words)
- Abstract thinking expected
- Textual supports primary
- WIDA: 6-8 standards
- Portuguese: Academic cognates + complex phrases

**9-12 (Ages 14-18) - High School**
- Academic vocabulary
- Sophisticated sentences
- Critical thinking required
- Independent work expected
- WIDA: 9-12 standards
- Portuguese: Academic language + discipline-specific terms

---

## UI Workflow

### Step 1: User Configuration (One-Time Setup)

**Variable Slot Count:** Each user can have 1-10 slots (not fixed at 6)

**Daniela's Configuration (5 slots):**
```
┌─────────────────────────────────────────────────┐
│  Configure Class Slots - Daniela Silva           │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ Slot 1: Social Studies                  │    │
│  │ Teacher: [Coleman      ▼]               │    │
│  │ Subject: [Social Studies ▼]             │    │
│  │ Grade:   [7            ▼]               │    │
│  │ Homeroom: [7A           ]               │    │
│  │ [Remove Slot]                           │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ Slot 2: Math                            │    │
│  │ Teacher: [Laverty      ▼]               │    │
│  │ Subject: [Math         ▼]               │    │
│  │ Grade:   [5            ▼]               │    │
│  │ Homeroom: [5A           ]               │    │
│  │ [Remove Slot]                           │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ Slot 3: ELA                             │    │
│  │ Teacher: [Piret        ▼]               │    │
│  │ Subject: [ELA          ▼]               │    │
│  │ Grade:   [5            ▼]               │    │
│  │ Homeroom: [315          ]               │    │
│  │ [Remove Slot]                           │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ Slot 4: Social Studies                  │    │
│  │ Teacher: [Lonesky      ▼]               │    │
│  │ Subject: [Social Studies ▼]             │    │
│  │ Grade:   [5            ▼]               │    │
│  │ Homeroom: [5B           ]               │    │
│  │ [Remove Slot]                           │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ Slot 5: Science                         │    │
│  │ Teacher: [Lonesky      ▼]               │    │
│  │ Subject: [Science      ▼]               │    │
│  │ Grade:   [5            ▼]               │    │
│  │ Homeroom: [5B           ]               │    │
│  │ [Remove Slot]                           │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  [+ Add Another Slot]                            │
│  [Save Configuration]                            │
│                                                  │
│  ⚙️ Slot Order:                                  │
│  Output order: 1→2→3→4→5                         │
│  [Reorder Slots] (drag & drop)                   │
└─────────────────────────────────────────────────┘
```

**Wilson's Configuration (5 slots):**
```
┌─────────────────────────────────────────────────┐
│  Configure Class Slots - Wilson Rodrigues        │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ Slot 1: ELA                             │    │
│  │ Teacher: [Lang         ▼]               │    │
│  │ Subject: [ELA          ▼]               │    │
│  │ Grade:   [3            ▼]               │    │
│  │ Homeroom: [T5           ]               │    │
│  │ [Remove Slot]                           │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ Slot 2: ELA/SS                          │    │
│  │ Teacher: [Savoca       ▼]               │    │
│  │ Subject: [ELA/SS       ▼]               │    │
│  │ Grade:   [2            ▼]               │    │
│  │ Homeroom: [209          ]               │    │
│  │ [Remove Slot]                           │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ Slot 3: Math                            │    │
│  │ Teacher: [Savoca       ▼]               │    │
│  │ Subject: [Math         ▼]               │    │
│  │ Grade:   [2            ▼]               │    │
│  │ Homeroom: [209          ]               │    │
│  │ [Remove Slot]                           │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ Slot 4: Science                         │    │
│  │ Teacher: [Savoca       ▼]               │    │
│  │ Subject: [Science      ▼]               │    │
│  │ Grade:   [2            ▼]               │    │
│  │ Homeroom: [209          ]               │    │
│  │ [Remove Slot]                           │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ Slot 5: Math                            │    │
│  │ Teacher: [Davies       ▼]               │    │
│  │ Subject: [Math         ▼]               │    │
│  │ Grade:   [3            ▼]               │    │
│  │ Homeroom: [T2           ]               │    │
│  │ [Remove Slot]                           │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  [+ Add Another Slot]                            │
│  [Save Configuration]                            │
│                                                  │
│  ⚙️ Slot Order:                                  │
│  Output order: 1→2→3→4→5                         │
│  [Reorder Slots] (drag & drop)                   │
└─────────────────────────────────────────────────┘
```

**What happens:**
1. System stores: `teacher_name='Davies', subject='Math', grade='3'`
2. No file selection needed - system will find it automatically

### Step 2: Week Selection & Preview

```
┌─────────────────────────────────────────────────┐
│  Generate Lesson Plan - Week 41                  │
├─────────────────────────────────────────────────┤
│                                                  │
│  Week: [10/06-10/10 ▼]                          │
│                                                  │
│  📁 Week Folder: F:\...\25 W41                  │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ Slot 1: Math (Grade 3)                  │    │
│  │ ✅ Davies → 10_6-10_10 Davies...docx    │    │
│  │    Subject: Math (Table 3)              │    │
│  │    Grade: 3 (Upper Elementary)          │    │
│  │    Preview: Unit 1, Lesson 5...         │    │
│  │                                          │    │
│  │ Slot 2: ELA (Grade 3)                   │    │
│  │ ✅ Lang → Lang Lesson Plans...docx      │    │
│  │    Subject: ELA (Table 1)               │    │
│  │    Grade: 3 (Upper Elementary)          │    │
│  │    Preview: Unit 1, Forces and...       │    │
│  │                                          │    │
│  │ Slot 3: Science (Grade 2)               │    │
│  │ ✅ Savoca → Ms. Savoca-...docx          │    │
│  │    Subject: Science (Table 5)           │    │
│  │    Grade: 2 (Early Elementary)          │    │
│  │    Preview: Unit 1 Properties...        │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  [Generate Bilingual Plan]                       │
└─────────────────────────────────────────────────┘
```

**What system does:**
1. For each slot:
   - Find file by teacher name
   - Extract subject block from file
   - Show preview of content
   - Display grade level for confirmation

### Step 3: Processing with Grade Awareness

```
┌─────────────────────────────────────────────────┐
│  Processing Lesson Plan...                       │
├─────────────────────────────────────────────────┤
│                                                  │
│  ✅ Slot 1: Math (Grade 3)                      │
│     📄 Extracted from Davies (Table 3)          │
│     🤖 LLM: Adapting for 3rd grade (8-9 yrs)    │
│     ✨ Generated bilingual plan                 │
│                                                  │
│  ⏳ Slot 2: ELA (Grade 3)                       │
│     📄 Extracting from Lang (Table 1)...        │
│                                                  │
│  ⏸  Slot 3: Science (Grade 2)                   │
│     Pending...                                   │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## Processing Flow (Backend)

### Step 1: File Finding & Extraction

```python
def process_slot(slot, week_of):
    # 1. Find file by teacher name
    file_mgr = get_file_manager()
    week_folder = file_mgr.get_week_folder(week_of)
    
    primary_file = file_mgr.find_primary_teacher_file(
        week_folder,
        teacher_pattern=slot['teacher_name'],  # "Davies"
        subject=slot['subject']                 # "Math"
    )
    
    # 2. Parse file and extract subject block
    parser = DOCXParser(primary_file)
    content = parser.extract_subject_content(slot['subject'])
    
    # 3. Validate extraction
    if not content['found']:
        raise ValueError(f"Subject {slot['subject']} not found in {primary_file}")
    
    # 4. Extract grade from content metadata (if available)
    extracted_grade = content['metadata'].get('grade')
    
    # 5. Verify grade matches configuration
    if extracted_grade and extracted_grade != slot['grade']:
        warnings.append(
            f"Grade mismatch: Slot configured for grade {slot['grade']}, "
            f"but file shows grade {extracted_grade}"
        )
    
    return content
```

### Step 2: Grade-Aware LLM Transformation

```python
def transform_with_llm(content, slot, week_of):
    # Prepare LLM request with grade context
    llm_request = {
        'primary_content': content['full_text'],
        'subject': slot['subject'],
        'grade': slot['grade'],              # ← Key: Grade level
        'week_of': week_of,
        'proficiency_levels': slot['proficiency_levels'],
        'homeroom': slot['homeroom']
    }
    
    # LLM receives grade-specific instructions
    llm_service = get_llm_service()
    
    success, lesson_json, error = llm_service.transform_lesson(
        primary_content=llm_request['primary_content'],
        grade=llm_request['grade'],          # ← Determines adaptation
        subject=llm_request['subject'],
        week_of=llm_request['week_of']
    )
    
    return lesson_json
```

### Step 3: Grade-Specific LLM Prompt

```python
def build_llm_prompt(content, grade, subject):
    # Get grade band
    grade_num = int(grade)
    if grade_num <= 2:
        grade_band = "K-2"
        age_range = "5-8 years"
        complexity = "simple"
        wida_band = "K-2"
    elif grade_num <= 5:
        grade_band = "3-5"
        age_range = "8-11 years"
        complexity = "moderate"
        wida_band = "3-5"
    elif grade_num <= 8:
        grade_band = "6-8"
        age_range = "11-14 years"
        complexity = "advanced"
        wida_band = "6-8"
    else:
        grade_band = "9-12"
        age_range = "14-18 years"
        complexity = "academic"
        wida_band = "9-12"
    
    prompt = f"""
Transform this {subject} lesson for Grade {grade} ESL students.

GRADE CONTEXT:
- Grade Band: {grade_band}
- Age Range: {age_range}
- Language Complexity: {complexity}
- WIDA Standards: Use {wida_band} band

ADAPTATION REQUIREMENTS:
1. Vocabulary: Use {complexity}-level words appropriate for {age_range} old students
2. Sentence Structure: Match cognitive development of grade {grade}
3. WIDA Standards: Select from {wida_band} ELD standards
4. Portuguese Support: Provide cognates suitable for {grade_band} learners
5. Activities: Design for {age_range} developmental stage

PRIMARY TEACHER CONTENT:
{content}

Generate bilingual lesson plan with grade-appropriate language and strategies.
"""
    
    return prompt
```

---

## Grade-Specific Adaptations in LLM Output

### Example: Same Math Concept, Different Grades

**Grade 2 (Age 7-8):**
```json
{
  "objective": "Students will add two numbers using pictures",
  "student_goal": "I can add numbers with pictures",
  "wida_objective": "Students will explain addition using visual models (ELD-MA.K-2.Explain)",
  "vocabulary": [
    {"term": "add", "portuguese": "somar", "definition": "put together"},
    {"term": "plus", "portuguese": "mais", "definition": "and"}
  ],
  "activities": "Use counting bears to show 3 + 2. Draw pictures."
}
```

**Grade 5 (Age 10-11):**
```json
{
  "objective": "Students will solve multi-digit addition problems using place value strategies",
  "student_goal": "I can add large numbers by understanding place value",
  "wida_objective": "Students will explain multi-step addition procedures (ELD-MA.3-5.Explain)",
  "vocabulary": [
    {"term": "place value", "portuguese": "valor posicional", "definition": "value based on position"},
    {"term": "regroup", "portuguese": "reagrupar", "definition": "carry to next place"}
  ],
  "activities": "Use base-10 blocks to model regrouping. Solve word problems."
}
```

**Grade 8 (Age 13-14):**
```json
{
  "objective": "Students will apply algebraic thinking to solve equations involving addition",
  "student_goal": "I can solve equations by isolating variables using inverse operations",
  "wida_objective": "Students will argue mathematical reasoning using academic language (ELD-MA.6-8.Argue)",
  "vocabulary": [
    {"term": "inverse operation", "portuguese": "operação inversa", "definition": "opposite mathematical operation"},
    {"term": "isolate", "portuguese": "isolar", "definition": "separate variable from constants"}
  ],
  "activities": "Solve algebraic equations. Justify solutions with mathematical reasoning."
}
```

---

## Slot Ordering System

### Purpose
The slot order determines the sequence of lessons in the final combined DOCX output.

### Default Order
Slots are numbered 1-6 and processed in that order by default:
```
Slot 1 → Slot 2 → Slot 3 → Slot 4 → Slot 5 → Slot 6
```

### Custom Ordering

**Use Case:** User wants Math first, then ELA, then Science (regardless of slot numbers)

**UI Feature: Drag & Drop Reordering**
```
┌─────────────────────────────────────────────────┐
│  Reorder Lesson Plan Output                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  Drag to reorder how lessons appear in output:  │
│                                                  │
│  ☰ 1. Math (Laverty, Grade 6)                   │
│  ☰ 2. Science (Lonesky, Grade 6)                │
│  ☰ 3. ELA (Piret, Grade 5)                      │
│  ☰ 4. Social Studies (Coleman, Grade 6)         │
│  ☰ 5. Science Period 2 (Lonesky, Grade 6)       │
│  ☰ 6. ELA/SS (Morais, Grade 6)                  │
│                                                  │
│  [Reset to Default] [Save Order]                │
└─────────────────────────────────────────────────┘
```

### Database Storage

**Add `display_order` field to slots:**
```sql
ALTER TABLE class_slots 
ADD COLUMN display_order INTEGER DEFAULT NULL;

-- If NULL, use slot_number
-- If set, use display_order for output sequence
```

**Example:**
```python
# User configures slots
Slot 1: Science (Lonesky)     → display_order = 2
Slot 2: Math (Laverty)        → display_order = 1
Slot 3: ELA (Piret)           → display_order = 3
Slot 4: SS (Coleman)          → display_order = 4
Slot 5: Science 2 (Lonesky)   → display_order = 5
Slot 6: ELA/SS (Morais)       → display_order = 6

# Output order: Math → Science → ELA → SS → Science 2 → ELA/SS
```

### Processing Logic

```python
def combine_lessons(user_id, lessons, week_of):
    """Combine lessons in display order."""
    
    # Get slots with display order
    slots = db.get_user_slots(user_id)
    
    # Sort by display_order (or slot_number if NULL)
    sorted_slots = sorted(slots, key=lambda s: s.get('display_order') or s['slot_number'])
    
    # Process in order
    for slot in sorted_slots:
        lesson = lessons[slot['slot_number']]
        add_to_output(lesson)
    
    return combined_output
```

### UI Behavior

**Initial State:**
- Slots shown in slot number order (1-6)
- display_order = NULL (uses slot_number)

**After Reordering:**
- Slots shown in custom order
- display_order saved to database
- Visual indicator: "Custom order active ⚙️"

**Reset:**
- Sets display_order = NULL for all slots
- Returns to slot number order

### Visual Feedback

**In Preview Screen:**
```
┌─────────────────────────────────────────────────┐
│  Week 41 Preview                                 │
├─────────────────────────────────────────────────┤
│                                                  │
│  Output will combine lessons in this order:      │
│  ⚙️ Custom order active                          │
│                                                  │
│  1️⃣ Math (Laverty, Grade 6)                     │
│  2️⃣ Science (Lonesky, Grade 6)                  │
│  3️⃣ ELA (Piret, Grade 5)                        │
│  4️⃣ Social Studies (Coleman, Grade 6)           │
│  5️⃣ Science Period 2 (Lonesky, Grade 6)         │
│  6️⃣ ELA/SS (Morais, Grade 6)                    │
│                                                  │
│  [Change Order]                                  │
└─────────────────────────────────────────────────┘
```

**In Output File:**
The DOCX will have lessons in the specified order, with page breaks between each.

---

## Database Schema Update

### Add Grade to Slots Table

```sql
ALTER TABLE class_slots 
ADD COLUMN grade TEXT NOT NULL;

-- Now stores:
-- teacher_name: "Davies"
-- subject: "Math"
-- grade: "3"          ← NEW: For LLM adaptation
```

### Slot Configuration Example

```python
db.create_class_slot(
    user_id=user_id,
    slot_number=1,
    subject="Math",
    grade="3",                    # ← Determines LLM adaptation
    homeroom="T2",
    primary_teacher_name="Davies"  # ← Finds file
)
```

---

## Validation & Error Handling

### Grade Mismatch Detection

```python
# Scenario: Slot configured for Grade 3, but file shows Grade 2

slot = {'grade': '3', 'teacher_name': 'Davies', 'subject': 'Math'}
content = parser.extract_subject_content('Math')

if content['metadata']['grade'] != slot['grade']:
    warning = {
        'type': 'grade_mismatch',
        'configured': slot['grade'],
        'found': content['metadata']['grade'],
        'message': f"Slot expects Grade {slot['grade']}, but file shows Grade {content['metadata']['grade']}"
    }
    
    # Show in UI:
    # ⚠️ Grade Mismatch: Configured for Grade 3, but Davies' file shows Grade 2
    # Continue anyway? [Yes] [No] [Update Slot]
```

### Subject Not Found

```python
# Scenario: Configured for "Math" but file only has "ELA"

content = parser.extract_subject_content('Math')

if not content['found']:
    available = parser.get_all_subjects()
    error = {
        'type': 'subject_not_found',
        'requested': 'Math',
        'available': available,
        'message': f"Math not found. Available: {', '.join(available)}"
    }
    
    # Show in UI:
    # ❌ Subject Not Found: Math not in Davies' file
    # Available subjects: ELA, Science, Social Studies
    # Update slot configuration? [Yes] [Cancel]
```

---

## Summary

### Selection Process:
1. **Teacher Name** → Finds file
2. **Subject** → Extracts correct table
3. **Grade** → Adapts LLM transformation

### Grade Impact:
- **Vocabulary complexity**
- **Sentence structure**
- **WIDA standard selection**
- **Portuguese cognate level**
- **Activity design**
- **Cognitive expectations**

### UI Shows:
- ✅ Teacher → File match
- ✅ Subject → Table match
- ✅ Grade → Developmental stage
- ⚠️ Warnings for mismatches

**Ready to implement grade-aware processing!** 🎯
