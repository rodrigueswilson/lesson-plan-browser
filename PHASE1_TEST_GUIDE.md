# Phase 1 Testing Guide

## What Was Fixed

### 1. Duration Fixes
- **Problem**: Steps could have `duration_minutes = 0`, causing timer to finish immediately
- **Fix**: Added check to ensure all steps have minimum 5-minute duration
- **Location**: `backend/api.py` line ~1968

### 2. Instruction Extraction
- **Problem**: Vocabulary and Sentence Frames steps showed only word lists, missing instructional text
- **Fix**: Extract `implementation` text from `ell_support` strategies and prepend to `display_content`
- **Location**: `backend/api.py` lines ~2036-2046 (vocab), ~2086-2096 (frames)

## How to Test

### Option 1: Using the Test Script

```bash
# Check lesson JSON structure (verify ell_support exists)
python test_phase1_fixes.py --plan-id <YOUR_PLAN_ID> --check-json

# Verify generated steps
python test_phase1_fixes.py --plan-id <YOUR_PLAN_ID> --day monday --slot 1
```

### Option 2: Manual Testing via API

#### Step 1: Find a Lesson Plan
1. Open your database or use the API to list plans
2. Note a `plan_id` that has lesson JSON with:
   - `phase_plan` in `tailored_instruction.co_teaching_model`
   - `vocabulary_cognates` (for vocabulary step)
   - `sentence_frames` (for frames step)
   - `ell_support` with `cognate_awareness` and `sentence_frames` strategies

#### Step 2: Regenerate Lesson Steps
```bash
# Using curl
curl -X POST "http://localhost:8000/api/lesson-steps/generate?plan_id=<PLAN_ID>&day=monday&slot=1" \
  -H "X-Current-User-Id: <USER_ID>"

# Or use the frontend to regenerate steps
```

#### Step 3: Verify Results
```bash
# Get the generated steps
curl "http://localhost:8000/api/lesson-steps/<PLAN_ID>/monday/1" \
  -H "X-Current-User-Id: <USER_ID>"
```

#### Step 4: Check the Response

**For Duration Fix:**
- ✅ All steps should have `duration_minutes > 0`
- ✅ No steps should have `duration_minutes = 0`

**For Instruction Extraction:**
- ✅ Vocabulary step (`step_name` contains "Vocabulary" or "Cognate") should have:
  - `display_content` that starts with instructional text (not just "- word -> word")
  - Instructional text should come from `ell_support` strategy with `strategy_id: "cognate_awareness"`
  
- ✅ Sentence Frames step (`content_type: "sentence_frames"`) should have:
  - `display_content` with instructional text (not empty or very short)
  - Instructional text should come from `ell_support` strategy with `strategy_id: "sentence_frames"`

### Option 3: Test in Frontend

1. **Open Lesson Mode** for a lesson
2. **Check the steps**:
   - All steps should show a duration (not 0:00)
   - Vocabulary step should show instructions before the word list
   - Sentence Frames step should show instructions

## Expected Results

### Before Fixes:
```json
{
  "step_name": "Vocabulary / Cognate Awareness",
  "duration_minutes": 0,  // ❌ Zero duration
  "display_content": "- law -> lei\n- system -> sistema\n..."  // ❌ Only word list
}
```

### After Fixes:
```json
{
  "step_name": "Vocabulary / Cognate Awareness",
  "duration_minutes": 5,  // ✅ Non-zero duration
  "display_content": "Teacher uses cognate cards to introduce vocabulary...\n\n- law -> lei\n- system -> sistema\n..."  // ✅ Instructions + word list
}
```

## Troubleshooting

### If durations are still 0:
1. Check that you regenerated steps after the fix
2. Verify the `phase_plan` in lesson JSON doesn't explicitly set `minutes: 0`
3. Check backend logs for warnings about zero duration fixes

### If instructions are missing:
1. Verify `ell_support` exists in `tailored_instruction`
2. Check that strategies have `strategy_id: "cognate_awareness"` or `"sentence_frames"`
3. Verify strategies have `implementation` or `implementation_steps` field
4. Check backend logs for any extraction errors

### If you see warnings in logs:
- Look for: `lesson_step_zero_duration_fixed` - this means the fix worked
- The warning indicates a step had zero duration and was fixed to 5 minutes

## Test Checklist

- [ ] All steps have `duration_minutes > 0`
- [ ] Vocabulary step has instructional text in `display_content`
- [ ] Sentence Frames step has instructional text in `display_content`
- [ ] Instructions appear before word lists/frames
- [ ] No errors in backend logs
- [ ] Timer works correctly in Lesson Mode UI

