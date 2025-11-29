# Phase 2: Remaining Root-Level Scripts Audit

**Date:** 2025-01-27  
**Purpose:** Audit remaining root-level diagnostic scripts before final migration  
**Status:** In Progress

## Root-Level Scripts Found

### check_*.py Scripts (25 files)

1. `check_backend_logs.py` - Check backend logs for debug output
2. `check_db_step.py` - Check database step
3. `check_duplicates.py` - Check for duplicates
4. `check_duplicate_users.py` - Check for duplicate users
5. `check_image_xml_structure.py` - Check image XML structure
6. `check_lesson_json_in_db.py` - Check lesson JSON in database
7. `check_old_databases.py` - Check old databases
8. `check_page_and_table_widths.py` - Check page and table widths
9. `check_page_margins.py` - Check page margins
10. `check_plan_data.py` - Check plan data
11. `check_plan_detail.py` - Check plan detail
12. `check_raw_db.py` - Check raw database
13. `check_recent_output_widths.py` - Check recent output widths
14. `check_specific_files_widths.py` - Check specific files widths
15. `check_step_generation.py` - Check step generation
16. `check_supabase_config.py` - Check Supabase configuration
17. `check_supabase_schedule_data.py` - Check Supabase schedule data
18. `check_supabase_schema.py` - Check Supabase schema
19. `check_table_alignment.py` - Check table alignment
20. `check_thursday.py` - Check Thursday data
21. `check_users_in_supabase.py` - Check users in Supabase
22. `check_vocab_sentences.py` - Check vocab sentences
23. `check_w45_no_school.py` - Check W45 no school
24. `check_w47_plans.py` - Check W47 plans
25. `check_wilson_both_projects.py` - Check Wilson both projects

**Target:** `tools/diagnostics/`

### analyze_*.py Scripts (3 files)

1. `analyze_6_vs_5_pattern.py` - Analyze 6 vs 5 pattern
2. `analyze_objectives_layout.py` - Analyze objectives layout
3. `analyze_signature_spacing.py` - Analyze signature spacing

**Target:** `tools/diagnostics/`

### fix_*.py Scripts (10 files)

1. `fix_all_plans.py` - Fix all plans
2. `fix_am_routine_data.py` - Fix AM routine data
3. `fix_missing_user.py` - Fix missing user
4. `fix_objectives_display.py` - Fix objectives display
5. `fix_objectives_metadata.py` - Fix objectives metadata
6. `fix_plan_status.py` - Fix plan status
7. `fix_plan_via_api.py` - Fix plan via API
8. `fix_table_alignment.py` - Fix table alignment
9. `fix_table_width_correct.py` - Fix table width correct
10. `fix_table_width_xml.py` - Fix table width XML

**Target:** `tools/maintenance/`

### debug_*.py Scripts (4 files)

1. `debug_ela_209_matching.py` - Debug ELA 209 matching
2. `debug_lesson_cards.py` - Debug lesson cards
3. `debug_slot_mismatch.py` - Debug slot mismatch
4. `debug_thursday.py` - Debug Thursday

**Target:** `tools/diagnostics/`

### diagnose_*.py Scripts (2 files)

1. `diagnose_am_routine_issue.py` - Diagnose AM routine issue
2. `diagnose_sentence_frames_w48.py` - Diagnose sentence frames W48

**Target:** `tools/diagnostics/`

## References Found

### Files Referencing These Scripts

1. `check_plan_data.py` - Self-reference (usage example)
2. `check_w47_plans.py` - Self-reference (usage example)
3. `analyze_objectives_layout.py` - Referenced by `generate_and_verify_objectives.py`
4. `fix_plan_status.py` - Referenced in documentation
5. `fix_missing_user.py` - Referenced in documentation
6. `debug_thursday.py` - Self-reference
7. `fix_am_routine_data.py` - Referenced in `SENTENCE_FRAMES_GENERATION_FIX.md`

## Action Plan

1. Move all `check_*.py` scripts to `tools/diagnostics/`
2. Move all `analyze_*.py` scripts to `tools/diagnostics/`
3. Move all `fix_*.py` scripts to `tools/maintenance/`
4. Move all `debug_*.py` scripts to `tools/diagnostics/`
5. Move all `diagnose_*.py` scripts to `tools/diagnostics/`
6. Update references in:
   - `generate_and_verify_objectives.py`
   - Documentation files
   - Any other references found
7. Test that scripts still work from new locations

## Verification

After moving:
- ✅ All scripts accessible from new locations
- ✅ All references updated
- ✅ Scripts run correctly
- ✅ No broken imports

