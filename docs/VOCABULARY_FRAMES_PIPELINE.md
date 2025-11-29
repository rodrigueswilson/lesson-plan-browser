# Vocabulary and Sentence Frames Pipeline Documentation

## Overview

This document explains how `vocabulary_cognates` and `sentence_frames` flow through the system, from source JSON to frontend display, and how to prevent common issues.

## Expected Data Structure

### In Source JSON Files

```json
{
  "days": {
    "monday": {
      "slots": [
        {
          "slot_number": 1,
          "vocabulary_cognates": [
            {
              "english": "state",
              "portuguese": "estado",
              "is_cognate": false,
              "relevance_note": "Core label for New Jersey..."
            }
          ],
          "sentence_frames": [
            {
              "english": "This is a fact: ___",
              "portuguese": "Este é um fato: ___",
              "proficiency_level": "levels_1_2",
              "language_function": "identify",
              "frame_type": "frame"
            }
          ]
        }
      ]
    }
  }
}
```

### In Database (lesson_json)

The `lesson_json` column in `weekly_plans` table should have the same structure as the source JSON.

## Pipeline Flow

1. **Source JSON** → Contains vocabulary/frames in `days[day]["slots"][slot_number]`
2. **Plan Creation/Import** → `lesson_json` should be populated with vocabulary/frames
3. **Step Generation** (`/api/lesson-steps/generate`) → Reads from `lesson_json` and creates vocabulary/frames steps
4. **Database** → Steps stored in `lesson_steps` table with `vocabulary_cognates` and `sentence_frames` columns
5. **API Response** → Returns steps with vocabulary/frames data
6. **Frontend** → Displays vocabulary/frames in `VocabularyDisplay` and `SentenceFramesDisplay` components

## Common Issues and Prevention

### Issue 1: Empty vocabulary/frames in lesson_json

**Symptoms:**
- "No vocabulary found for this lesson." in UI
- "No sentence frames found for this lesson." in UI
- Only 4 steps generated instead of 6 (missing vocabulary/frames steps)

**Root Cause:**
Plan's `lesson_json` has empty arrays (`[]`) or missing keys for `vocabulary_cognates`/`sentence_frames`.

**Prevention:**
1. **Validation during plan creation**: Check source JSON has vocabulary/frames before creating plan
2. **Warning logs**: The system now logs warnings when vocabulary/frames are missing during step generation
3. **Validation utility**: Use `backend/utils/validate_lesson_json.py` to check lesson_json structure

**Fix:**
```python
# Use update_plan_supabase.py script to fix existing plans
python update_plan_supabase.py
```

### Issue 2: Vocabulary/frames not extracted from source JSON

**Symptoms:**
- Plan created but lesson_json doesn't contain vocabulary/frames from source JSON

**Prevention:**
- Ensure plan creation/import properly extracts vocabulary/frames from source JSON
- Add validation after plan creation to verify lesson_json structure

### Issue 3: Steps not created during generation

**Symptoms:**
- Vocabulary/frames exist in lesson_json but steps aren't created

**Root Cause:**
The step generation logic checks for non-empty arrays. If arrays are empty or None, steps won't be created.

**Prevention:**
- The code now includes comprehensive comments explaining when steps are/aren't created
- Warning logs are emitted when vocabulary/frames are missing

## Code Locations

### Key Files

1. **`backend/api.py`** (lines ~2644-2800):
   - Step generation logic
   - Extracts vocabulary/frames from lesson_json
   - Creates vocabulary/frames steps
   - **Contains extensive comments about expected structure**

2. **`backend/database.py`**:
   - `update_weekly_plan()`: Updates plan's lesson_json
   - **Now includes docstring warning about vocabulary/frames**

3. **`backend/utils/validate_lesson_json.py`** (new):
   - Validation utility functions
   - Can be used to check lesson_json structure

4. **`frontend/src/components/resources/VocabularyDisplay.tsx`**:
   - Displays vocabulary in UI
   - Reads from `step.vocabulary_cognates`

5. **`frontend/src/components/resources/SentenceFramesDisplay.tsx`**:
   - Displays sentence frames in UI
   - Reads from `step.sentence_frames`

## Validation Tools

### Validate lesson_json structure

```python
from backend.utils.validate_lesson_json import validate_vocabulary_frames_in_lesson_json

lesson_json = plan.lesson_json
is_valid, warnings = validate_vocabulary_frames_in_lesson_json(
    lesson_json, 
    day="monday", 
    slot_number=1
)

if not is_valid:
    for warning in warnings:
        print(f"WARNING: {warning}")
```

### Log validation warnings

```python
from backend.utils.validate_lesson_json import log_vocabulary_frames_warnings

log_vocabulary_frames_warnings(
    lesson_json, 
    plan_id="plan_123", 
    logger=logger,
    day="monday",
    slot_number=1
)
```

## Best Practices

1. **Always validate source JSON** before creating/importing plans
2. **Check lesson_json after plan creation** to ensure vocabulary/frames are present
3. **Monitor warning logs** for missing vocabulary/frames
4. **Use validation utilities** during development/testing
5. **Fix plans early** using `update_plan_supabase.py` if issues are detected

## Debugging

### Check if plan has vocabulary/frames

```python
# Via API
GET /api/plans/{plan_id}

# Check lesson_json structure
lesson_json = response["lesson_json"]
monday_slot_1 = lesson_json["days"]["monday"]["slots"][0]  # Assuming slot_number=1
vocab = monday_slot_1.get("vocabulary_cognates", [])
frames = monday_slot_1.get("sentence_frames", [])

print(f"Vocabulary count: {len(vocab)}")
print(f"Frames count: {len(frames)}")
```

### Check if steps were created

```python
# Via API
GET /api/lesson-steps/{plan_id}/{day}/{slot}

# Check for vocabulary/frames steps
steps = response
vocab_step = next((s for s in steps if "vocabulary" in s["step_name"].lower()), None)
frames_step = next((s for s in steps if s["content_type"] == "sentence_frames"), None)

print(f"Vocabulary step: {vocab_step is not None}")
print(f"Frames step: {frames_step is not None}")
```

## Fix Scripts

### Update existing plan

```python
# Use update_plan_supabase.py
python update_plan_supabase.py
```

### Fix all plans

```python
# Use fix_all_plans.py (if vocabulary/frames exist in lesson_json but not in steps)
python fix_all_plans.py
```

## Future Improvements

1. **Automatic validation** during plan creation
2. **Migration script** to backfill missing vocabulary/frames from source JSON
3. **UI warning** when plans are missing vocabulary/frames
4. **Health check endpoint** to detect plans with missing vocabulary/frames

