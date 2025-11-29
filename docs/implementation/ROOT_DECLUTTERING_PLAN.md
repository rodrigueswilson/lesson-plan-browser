# Root Directory Decluttering Plan

**Date**: 2025-01-27  
**Status**: Ready for Execution  
**Related**: Codebase Decluttering - Phase 2

## Overview

This plan systematically organizes and archives files in the root directory that are cluttering the project root. Files will be organized into appropriate locations or archived.

## Objectives

1. **Archive documentation files** that are superseded or historical
2. **Remove temporary files** that are no longer needed
3. **Organize log files** into logs directory
4. **Archive test files** that are no longer used
5. **Organize utility scripts** into appropriate directories
6. **Clean up batch/PowerShell scripts** that are duplicates or obsolete

## File Categories

### Category 1: Documentation Files (Markdown)

#### Analysis/Status Documents (Archive)
- `ANALYSIS_DETAILED_AND_LESSON_MODE.md`
- `ANALYSIS_SECOND_VERSION.md`
- `ANALYSIS_TABLE_WIDTH_ISSUE.md`
- `ANALYTICS_TEST_REPORT.md`
- `ANALYTICS_WORKFLOW_IMPROVEMENTS.md`
- `ANSWERS_TO_CRITICAL_QUESTIONS.md`
- `ARCHITECTURE_HYBRID_APPROACH.md`
- `BACKEND_NOT_RUNNING.md`
- `BROWSER_FULLSCREEN_IMPLEMENTATION.md`
- `BUILD_BLOCKER_REPORT.md`
- `BUILD_BLOCKER_SOLUTION.md`
- `BUILD_FIX_SUMMARY.md`
- `CACHE_CLEARING_IMPLEMENTATION.md`
- `CODE_REVIEW_RESPONSE.md`
- `CODEBASE_INTEGRATION_GUIDE.md`
- `CONSENSUS_SUMMARY.md`
- `COORDINATE_PLACEMENT_FOR_MULTISLOT.md`
- `DESKTOP_TESTING_RESULTS.md`
- `DESKTOP_TESTING_START.md`
- `DESKTOP_TESTING_TROUBLESHOOTING.md`
- `DIAGNOSE_ISSUE.md`
- `DIAGNOSIS_CHECKLIST.md`
- `END_TO_END_TESTING_GUIDE.md`
- `FINAL_RECOMMENDATION.md`
- `FIX_BACKEND_ISSUES.md`
- `FIX_STEPS.md`
- `FOLDER_DETERMINATION_LOGIC.md`
- `FOR_OTHER_AI_DEBUGGING_REQUEST.md`
- `FOR_OTHER_AI_HYPERLINK_BUG.md`
- `FRESH_START_SUMMARY.md`
- `FRESH_START_BROWSER_TESTING.md`
- `FUTURE_SESSION_PLAN.md`
- `GEMINI.md`
- `GITHUB_ACTIONS_SETUP.md`
- `IMPLEMENTATION_PRIORITY.md`
- `IMPLEMENTATION_READINESS.md`
- `IMPLEMENTATION_SUMMARY.md`
- `INSTRUMENTATION_ADDED.md`
- `IPC_BRIDGE_SUCCESS.md`
- `IPC_BRIDGE_TEST_RESULTS.md`
- `LESSON_MODE_IMPLEMENTATION_SUMMARY.md`
- `LESSON_MODE_V2_IMPLEMENTATION_SUMMARY.md`
- `LESSON_PLAN_BROWSER_ARCHITECTURE.md`
- `LLM_PROMPT_IMPROVEMENTS.md`
- `MANUAL_INSTALL_STEPS.md`
- `METADATA_MATCHING_ISSUE.md`
- `MIGRATION_INSTRUCTIONS.md`
- `NEXT_STEPS_ANDROID.md`
- `NEXT_STEPS_FRONTEND.md`
- `NEXT_STEPS_SUMMARY.md`
- `PDF_CONVERSION_STATUS.md`
- `PHASE1_TEST_GUIDE.md`
- `PHASE5_ANDROID_STATUS.md`
- `PHASE5_BUNDLING_GUIDE.md`
- `PHASE5_FINAL_SUMMARY.md`
- `PHASE5_PYTHON_BUNDLING.md`
- `PHASE6_QUICK_START.md`
- `PHASE6_READY.md`
- `PHASE6_SETUP_GUIDE.md`
- `PIPELINE_VERIFICATION_STATUS.md`
- `QUICK_FIX_ANDROID_BUILD.md`
- `QUICK_START_DIAGNOSTICS.md`
- `QUICK_START_TESTING.md`
- `READY_FOR_VALIDATION.md`
- `REAL_WORLD_TEST_RESULTS.md`
- `REBUILD_REQUIRED.md`
- `REBUILD_STEPS.md`
- `ROOT_CAUSE_FOUND.md`
- `SCHEDULE_MIGRATION_INSTRUCTIONS.md`
- `SIGNATURE_POSITION_REVIEW.md`
- `SOLUTION_SUMMARY.md`
- `SOLUTION_WEBVIEW_CACHE.md`
- `STANDALONE_TROUBLESHOOTING.md`
- `STEP2_EXECUTION_PLAN_UPDATED.md`
- `STRUCTURED_OUTPUTS_SOLUTION.md`
- `SUBJECT_BASED_SLOT_DETECTION.md`
- `SUBJECT_DETECTION_IMPROVEMENTS.md`
- `SUPABASE_TEST_SETUP.md`
- `TABLE_STRUCTURE_DATA.md`
- `TAURI_V1_ANDROID_OPTIONS.md`
- `TAURI_V2_UPGRADE_STATUS.md`
- `TAURI_V2_UPGRADE.md`
- `TEST_RESULTS_SUMMARY.md`
- `TESTING_GUIDE.md`
- `THRESHOLD_CHANGE_IMPLEMENTATION.md`
- `TOMORROW_START_HERE.md`
- `TROUBLESHOOT_INSTALL.md`
- `VOCAB_PIPELINE_FIX_SUMMARY.md`
- `WHERE_TO_FIND_GENERATED_FILES.md`
- `WHY_COORDINATES_DONT_WORK_MULTISLOT.md`
- `WINDOWS_SYMLINK_SOLUTION.md`

**Action**: Move to `docs/archive/root-documentation/`

#### Android-Specific Documentation (Keep in AndroidDoc or Archive)
- `ANDROID_BUNDLE_APPROACH.md`
- `ANDROID_DEBUG_NOTES.md`
- `ANDROID_PYTHON_RUNTIME_APPROACH.md`
- `ANDROID_PYTHON_SOLUTION.md`
- `ANDROID_STANDALONE_ISSUE.md`

**Action**: Move to `AndroidDoc/` or `docs/archive/android-documentation/`

### Category 2: Temporary Files (Delete or Archive)

- `temp_apk_path.txt`
- `temp_apk.apk`
- `temp_apk.zip`
- `temp_lesson.json`
- `temp.zip`
- `temp_apk/` (directory)
- `temp_apk_extract/` (directory)

**Action**: Delete if truly temporary, or move to `docs/archive/temp-files/` if needed for reference

### Category 3: Log Files (Move to logs/)

- `app-launch-logs.txt`
- `backend_debug.log`
- `backend_error.log`
- `backend_server.log`
- `full-tablet-logs.txt`
- `tablet-app-errors.txt`
- `tablet-crash-log.txt`
- `tablet-error-log.txt`
- `ipconfig.txt`
- `ipconfig_output.txt`
- `verify_output.txt`

**Action**: Move to `logs/archive/` or delete if old

### Category 4: Test Files (Archive)

- `test_desktop_ipc.md`
- `test_navigation.md`
- `test_objectives.docx`
- `test_objectives_verified.docx`
- `test_page_break.docx`
- `test_precise_layout.docx`
- `test_precise_objectives.docx`
- `test_reordered_page_break.docx`
- `test_rust_database.rs`
- `test_table_width_diagnosis.docx`
- `test_vocab_pipeline.db`
- `test_xml_page_break.docx`
- `debug_sentence_frames.html`
- `debug_sentence_frames.pdf`
- `debuginfo001.md`
- `Debuginfo002.md`

**Action**: Move to `docs/archive/test-files/`

### Category 5: Python Utility Scripts (Move to tools/)

- `add_vocab_column.py`
- `add_wilson_slots.py`
- `auto_pdf_generator.py`
- `backfill_lesson_json.py`
- `batch_processor_enhancement_same_folder.py`
- `batch_processor_enhancement.py`
- `calculate_table_width.py`
- `convert_plan_format.py`
- `create_test_users.py`
- `delete_duplicate_wilson.py`
- `display_fixed_html.py`
- `FINAL_AUTO_PDF_INTEGRATION.py`
- `final_test.py`
- `find_coteaching_pattern.py`
- `find_wilson_slots.py`
- `generate_and_verify_objectives.py`
- `generate_fixed_objectives_demo.py`
- `generate_objectives_from_db.py`
- `generate_pdf_demo.py`
- `generate_real_objectives.py`
- `generate_sentence_frames_week.py`
- `generate_wilson_objectives.py`
- `import_plan_from_json.py`
- `inspect_json_structure.py`
- `inspect_lesson_json.py`
- `inspect_real_data.py`
- `integrate_objectives_pdf.py`
- `list_lesson_plan_json_files.py`
- `list_weeks.py`
- `measure_admin_date_position.py`
- `migrate_db.py`
- `migrate_supabase_to_sqlite.py`
- `migrate_wilson_slots.py`
- `objectives_integration_code.py`
- `quick_test_w47.py`
- `regenerate_fixed_dates.py`
- `reliable_auto_pdf.py`
- `repro_modelprivateattr.py`
- `reproduce_frontend_logic.py`
- `reproduce_misalignment_v2.py`
- `reproduce_misalignment.py`
- `reproduce_mismatch_content.py`
- `review_signature_position.py`
- `set_tauri_env.py`
- `show_thursday_details.py`
- `show_w47_wednesday.py`
- `simple_objectives_fix.py`
- `update_plan_supabase.py`
- `verify_fix_comparison.py`
- `verify_lesson_json_column.py`
- `verify_phase1.py`
- `verify_phase2.py`
- `verify_refactor.py`
- `verify_tablet_database.py`
- `verify_week47_json.py`
- `working_objectives_fix.py`

**Action**: Move to `tools/archive/root-scripts/` or review and keep in `tools/` if still useful

### Category 6: Batch Scripts (Archive or Consolidate)

Many batch scripts for starting/restarting services. Keep only essential ones:

**Keep**:
- `start-backend.bat` (if still used)
- `start-app.bat` (if still used)

**Archive**:
- `apply_frontend_fixes.bat`
- `backup_registry_before_fix.bat`
- `CLEAN_AND_RESTART.bat`
- `fix_localhost_registry.bat`
- `fix_localhost_registry_undo.bat`
- `FRESH_START_ALL.bat`
- `fresh-start-complete.bat`
- `fresh-start-schedule.bat`
- `fresh-start.bat`
- `HARD_RESET_BACKEND.bat`
- `install-app.bat`
- `rebuild-frontend.bat`
- `RESTART_BACKEND_CLEAN.bat`
- `restart-backend-supabase.bat`
- `restart-backend.bat`
- `restart-frontend-clean.bat`
- `START_BACKEND_NOW.bat`
- `START_FRESH_BROWSER_TEST.bat`
- `start-app-with-devtools.bat`
- `start-backend-all-interfaces.bat`
- `start-backend-for-testing.bat`
- `start-backend-no-reload.bat`
- `start-backend-safe.bat`
- `start-with-diagnostics.bat`
- `test-schedule.bat`
- `test_fresh.bat`

**Action**: Move to `docs/archive/scripts/batch/`

### Category 7: PowerShell Scripts (Archive or Consolidate)

**Keep** (if still used):
- `test-unified-frontend.ps1` (recent, useful)
- `CHECK_BACKEND_STATUS.ps1` (if still used)

**Archive**:
- `bundle_sidecar.ps1`
- `bundle_sidecar.sh`
- `capture-error-logs.ps1`
- `check-standalone-errors.ps1`
- `clear-webview-cache-aggressive.ps1`
- `clear-webview-cache.ps1`
- `create-test-user.ps1`
- `diagnose-app.ps1`
- `fresh-start-complete.ps1`
- `fresh-start.ps1`
- `PUSH_TO_GITHUB.ps1`
- `start-prometheus.ps1`
- `start-tablet-usb.ps1`
- `stop-port-8000.ps1`
- `verify-apk-assets.ps1`

**Action**: Move to `docs/archive/scripts/powershell/`

### Category 8: Other Files

- `api_tauri_fixed.ts` - Move to appropriate location or archive
- `console-messages.md` - Archive
- `decluttering_plan.md` - Already superseded, archive
- `emulator_screenshot.png` - Archive or delete
- `prompt_v4.md` - Move to appropriate docs location
- `python-sync-processor.spec` - Keep if used, otherwise archive
- `UserSelector_improved.tsx` - Move to frontend or archive
- `w47_generation_errors.json` - Archive
- `w47_test_errors.json` - Archive
- `wilson_lesson_sample.json` - Move to test fixtures or archive

## Archive Structure

```
docs/archive/
├── root-documentation/     # Root MD files
├── android-documentation/   # Android-specific docs
├── test-files/             # Test files
├── temp-files/             # Temporary files (if keeping)
├── scripts/
│   ├── batch/              # Batch scripts
│   └── powershell/         # PowerShell scripts
└── ARCHIVE_INDEX.md         # Root archive index
```

## Execution Plan

### Phase 1: Documentation Files
1. Create `docs/archive/root-documentation/`
2. Move all analysis/status MD files
3. Move Android docs to `AndroidDoc/` or archive
4. Create archive index

### Phase 2: Temporary Files
1. Review temporary files
2. Delete truly temporary files
3. Archive any needed for reference

### Phase 3: Log Files
1. Move log files to `logs/archive/`
2. Clean up old logs

### Phase 4: Test Files
1. Create `docs/archive/test-files/`
2. Move all test files
3. Update archive index

### Phase 5: Scripts
1. Review Python scripts - move to `tools/` or archive
2. Archive batch scripts
3. Archive PowerShell scripts
4. Keep only essential scripts in root

### Phase 6: Other Files
1. Organize remaining files
2. Update archive index

## Safety Measures

1. **Git Checkpoint**: Create commit before starting
2. **Backup Verification**: Verify important files before moving
3. **Incremental Commits**: Commit after each phase
4. **Preserve Git History**: All files preserved in git

## Success Criteria

- [ ] Root directory contains only essential files
- [ ] All documentation archived with index
- [ ] Temporary files removed or archived
- [ ] Log files organized
- [ ] Test files archived
- [ ] Scripts organized or archived
- [ ] Archive indexes created
- [ ] No broken references

## Estimated Impact

**Files to Archive**: ~150+ files  
**Files to Delete**: ~10-15 temporary files  
**Files to Move**: ~50 Python scripts to tools/  
**Root Directory**: Reduced from ~200+ files to ~20-30 essential files

---

**Document Status**: Ready for Execution  
**Last Updated**: 2025-01-27  
**Maintainer**: Development Team

