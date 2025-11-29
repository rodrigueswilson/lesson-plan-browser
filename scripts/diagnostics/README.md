# Vocabulary/Frames Pipeline Diagnostic Scripts

This folder contains diagnostic and utility scripts for the vocabulary/frames pipeline.

## Main Fix Scripts (in root directory)

- **`fix_all_plans.py`** - Fixes all plans that have vocabulary/frames in lesson_json but not in steps
- **`update_plan_supabase.py`** - Updates a specific plan's lesson_json with vocabulary/frames from source JSON

## Diagnostic Scripts (in this folder)

- **`check_plan_steps.py`** - Check what steps are generated for a specific plan and why vocabulary/frames steps are missing
- **`diagnose_vocab_pipeline.py`** - Comprehensive diagnostic to trace vocabulary and sentence frames pipeline
- **`find_plan_with_vocab.py`** - Find plans that have vocabulary_cognates and sentence_frames in their lesson_json
- **`fix_vocab_cognates_save.py`** - Fix vocabulary_cognates not being saved by ensuring it's explicitly set
- **`regenerate_steps_for_plan.py`** - Regenerate lesson steps for a specific plan and check if vocabulary/frames steps are created

## Usage

These scripts are primarily for debugging and diagnosis. For fixing plans, use the main fix scripts in the root directory.

