# Simplified Schema Guide for Training

**Version:** 1.0.0  
**Audience:** Training Session 1 Participants  
**Purpose:** Simplified explanation of the lesson plan JSON structure

---

## Important Note

The full production schema is comprehensive and includes many required fields for WIDA compliance, co-teaching models, and bilingual support. **For training purposes, we'll start with understanding the structure**, then build up to the full requirements.

---

## Minimum Required Structure

### Level 1: Metadata (Required)

```json
{
  "metadata": {
    "week_of": "10/6-10/10",        // Format: MM/DD-MM/DD
    "grade": "7",                    // Any grade level
    "subject": "Social Studies"      // Subject name
  }
}
```

**Optional metadata fields:**
- `homeroom`: Room number or identifier
- `teacher_name`: Teacher's name

---

### Level 2: Days (Required)

All five weekdays must be present:

```json
{
  "metadata": { ... },
  "days": {
    "monday": { ... },
    "tuesday": { ... },
    "wednesday": { ... },
    "thursday": { ... },
    "friday": { ... }
  }
}
```

---

### Level 3: Daily Plan Structure (Required for each day)

Each day requires these sections:

```json
"monday": {
  "unit_lesson": "Unit One Lesson Seven",
  "objective": { ... },
  "anticipatory_set": { ... },
  "tailored_instruction": { ... },
  "misconceptions": { ... },
  "assessment": { ... },
  "homework": { ... }
}
```

---

## Section Details

### 1. Objective (Tri-Objective Structure)

**Required fields:**
```json
"objective": {
  "content_objective": "Students will be able to explain...",
  "student_goal": "I will explain...",
  "wida_objective": "Students will use language to... (ELD-SS.6-8.Explain.Reading/Writing)..."
}
```

**Requirements:**
- `content_objective`: Min 10 characters
- `student_goal`: 5-80 characters, starts with "I will"
- `wida_objective`: Min 50 characters, must include ELD standard format

**ELD Standard Format:**
```
ELD-[Subject].[Grade].[Function].[Modality]

Examples:
- ELD-SS.6-8.Explain.Reading/Writing
- ELD-MA.7.Describe.Speaking/Listening
- ELD-LA.K-2.Narrate.Writing
```

---

### 2. Anticipatory Set

**Required fields:**
```json
"anticipatory_set": {
  "original_content": "Students will respond to...",
  "bilingual_bridge": "Preview key cognates: lei/law, banco/bank..."
}
```

**Requirements:**
- `original_content`: Any length
- `bilingual_bridge`: Min 20 characters, concrete L1 connection

---

### 3. Tailored Instruction (Most Complex)

**Required fields:**
```json
"tailored_instruction": {
  "original_content": "Engage / Introduction...",
  "co_teaching_model": { ... },
  "ell_support": [ ... ],           // 3-5 strategies
  "special_needs_support": [ ... ], // 1-2 accommodations
  "materials": [ ... ]
}
```

#### Co-Teaching Model Structure

```json
"co_teaching_model": {
  "model_name": "Station Teaching",
  "rationale": "Mixed range (4+ levels) needs differentiated stations",
  "wida_context": "Mixed range with typical 7th grade distribution...",
  "phase_plan": [
    {
      "phase_name": "Warmup",
      "minutes": 5,
      "bilingual_teacher_role": "Introduce stations...",
      "primary_teacher_role": "Explain content objective..."
    }
  ],
  "implementation_notes": [
    "Prepare 3 station signs, rotation chart, visual timer"
  ]
}
```

**Co-Teaching Models:**
- Station Teaching
- Parallel Teaching
- Team Teaching
- Alternative Teaching
- One Teach One Assist

#### ELL Support Strategies (3-5 required)

```json
"ell_support": [
  {
    "strategy_id": "cognate_awareness",
    "strategy_name": "Cognate Awareness",
    "implementation": "Create bilingual vocabulary anchor chart...",
    "proficiency_levels": "Levels 2-5"
  }
]
```

**Common Strategy IDs:**
- `cognate_awareness`
- `graphic_organizers`
- `sentence_frames`
- `visual_aids`
- `bilingual_glossary`

**Proficiency Level Format:**
- "Levels 2-5"
- "Levels 1-3"
- "Level 4"

---

### 4. Misconceptions

**Required fields:**
```json
"misconceptions": {
  "original_content": "Students may believe...",
  "linguistic_note": {
    "pattern_id": "subject_pronoun_omission",
    "note": "Portuguese speakers often drop subject pronouns...",
    "prevention_tip": "Use sentence frames that explicitly include..."
  }
}
```

---

### 5. Assessment

**Required fields:**
```json
"assessment": {
  "primary_assessment": "Exit Ticket",
  "bilingual_overlay": {
    "instrument": "Written exit ticket (1-2 sentences)",
    "wida_mapping": "Explain + ELD-SS.6-8.Writing + Levels 2-5",
    "supports_by_level": {
      "levels_1_2": "Sentence frame provided...",
      "levels_3_4": "Sentence starter provided...",
      "levels_5_6": "Open response..."
    },
    "scoring_lens": "Accept responses showing understanding...",
    "constraints_honored": "No new materials; uses existing format"
  }
}
```

---

### 6. Homework

**Required fields:**
```json
"homework": {
  "original_content": "Complete worksheet...",
  "family_connection": "Ask family members to help identify..."
}
```

---

## Training Progression

### Session 1 (Today)
- Understand basic structure
- Create simple examples with guidance
- Use provided templates

### Session 2 (Future)
- Master co-teaching models
- Create comprehensive ELL support
- Build complete WIDA-aligned plans

---

## Quick Reference: Complete Minimal Example

See `tests/fixtures/valid_lesson_minimal.json` for a complete working example that passes all validation.

**Key takeaways:**
1. All five weekdays required
2. Each day needs all 7 sections
3. WIDA objective must include ELD standard
4. Anticipatory set needs bilingual bridge
5. Tailored instruction needs co-teaching model + 3-5 ELL strategies
6. Assessment needs bilingual overlay with level-specific supports

---

## Common Validation Errors

### Error: "Field required"
**Cause:** Missing a required field  
**Fix:** Add the missing field

### Error: "String too short"
**Cause:** Field doesn't meet minimum length  
**Fix:** Add more detail (e.g., WIDA objective needs 50+ characters)

### Error: "Pattern mismatch"
**Cause:** Format doesn't match expected pattern  
**Fix:** Check format (e.g., ELD standard, proficiency levels)

### Error: "Too few items"
**Cause:** Array doesn't have enough elements  
**Fix:** Add more items (e.g., need 3-5 ELL strategies)

---

## Tips for Success

1. **Start with a working example** - Copy `valid_lesson_minimal.json` and modify it
2. **Validate frequently** - Check after each major change
3. **Use the schema** - Reference `schemas/lesson_output_schema.json` for details
4. **Ask questions** - Don't hesitate to ask for clarification
5. **Build incrementally** - Add one section at a time

---

## Resources

- **Full Schema:** `schemas/lesson_output_schema.json`
- **Working Example:** `tests/fixtures/valid_lesson_minimal.json`
- **Validation Endpoint:** http://localhost:8000/api/validate
- **API Docs:** http://localhost:8000/api/docs

---

**Remember:** The schema ensures WIDA compliance and bilingual support quality. While it may seem complex at first, it guarantees professional, consistent lesson plans that truly support English learners!
