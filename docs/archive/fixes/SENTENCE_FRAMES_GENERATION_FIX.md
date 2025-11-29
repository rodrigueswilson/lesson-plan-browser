# Sentence Frames Generation Fix - W48 Issue

## Root Cause Analysis

The diagnostic script revealed that sentence frames HTML and PDF files were not being generated for W48 lesson plans. The investigation identified several issues:

### Issues Found:

1. **Sentence Frames Check Was Too Restrictive**: The code was only checking the sanitized `lesson_json_for_pdf` version, which might have lost sentence frames data during sanitization. The check needed to also examine the original `lesson_json`.

2. **Missing Multi-Slot Support**: Sentence frames generation was only implemented for single-slot plans (`len(lessons) == 1`). Multi-slot plans (which create "Weekly" files) were not generating sentence frames at all.

3. **Path Resolution**: The sentence frames PDF path was being derived from `output_path`, but the path construction could be improved to ensure files are always saved in the correct directory.

4. **Insufficient Error Handling**: The code didn't verify that files were actually created after generation, making it difficult to diagnose failures.

## Fixes Applied

### 1. Enhanced Sentence Frames Detection (Single-Slot Path)

**File**: `tools/batch_processor.py` (lines ~2379-2508)

- Now checks both the original `lesson_json` and the sanitized `lesson_json_for_pdf` for sentence frames
- Counts total frames found for better logging
- Improved error messages with more context

### 2. Added Multi-Slot Sentence Frames Generation

**File**: `tools/batch_processor.py` (lines ~2767-2860)

- Added complete sentence frames generation for multi-slot plans
- Uses the same logic as single-slot plans but works with `merged_json`
- Ensures files are saved in the correct output directory

### 3. Improved Path Handling

- Uses `Path(output_path).parent` to ensure files are saved in the same directory as the lesson plan DOCX
- Explicitly creates output directory before generation
- Better path logging for debugging

### 4. Enhanced Verification and Logging

- Verifies that both HTML and PDF files are created after generation
- Logs file existence status
- Includes frame counts in logs for better diagnostics

## Testing

The diagnostic script (`diagnose_sentence_frames_w48.py`) confirmed:
- ✅ Sentence frames exist in W48 lesson plan JSON files (72 and 120 frames found)
- ✅ Sentence frames generation works when tested directly
- ✅ Files can be generated in the correct folder (`F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W48`)

## Expected Behavior After Fix

When generating lesson plans:

1. **Single-Slot Plans**: Sentence frames HTML and PDF will be generated alongside the lesson plan DOCX
2. **Multi-Slot Plans**: Sentence frames HTML and PDF will be generated for the consolidated weekly plan
3. **File Location**: Files will be saved in the same folder as the lesson plan DOCX file
4. **File Naming**: Files follow the pattern: `{lesson_plan_name}_sentence_frames.{html|pdf}`

## Next Steps

1. Test the fix by generating a new lesson plan for W48
2. Verify that sentence frames HTML and PDF files are created in the expected folder
3. Check backend logs for any generation errors (look for `batch_sentence_frames_*` log entries)

## Diagnostic Script

The diagnostic script `tools/diagnostics/diagnose_sentence_frames_w48.py` can be used to:
- Check if sentence frames exist in lesson plan JSON files
- Test sentence frames generation
- Verify file paths and folder resolution

Run it with:
```bash
python tools/diagnostics/diagnose_sentence_frames_w48.py
```

