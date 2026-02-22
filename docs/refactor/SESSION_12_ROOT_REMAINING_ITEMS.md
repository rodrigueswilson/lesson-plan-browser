# Session 12: Root declutter – remaining items checklist

Generated from audit of root vs ROOT_DECLUTTERING_PLAN. Only tracked root files are listed.

## Keep in root (essential)

- `.env.example`, `.gitignore`, `.pre-commit-config.yaml`, `README.md`, `requirements.txt`, `pytest.ini`
- `package-lock.json`
- `start-backend.bat`, `start-app.bat`, `start-app-with-logs.ps1`, `CHECK_BACKEND_STATUS.ps1`, `test-unified-frontend.ps1`
- `Dockerfile.android-python`, `docker-compose.monitoring.yml`
- `icon.svg`, `icon2.svg`

## Phase 1 – Documentation to docs/archive/root-documentation

- DATE_FLOW_AUDIT.md, DEBUGGING_GUIDE.md, DEBUGGING_STEPS.md
- ERROR_ANALYSIS_OBJECTIVES_GENERATION.md, ERROR_AUDIT.md, FIXES_GUIDE.md, FIXES_SUMMARY.md
- METADATA_ANALYSIS.md, RUN_SUPABASE_MIGRATIONS.md, SCHEDULE_ORDERING_VERIFICATION_RESULTS.md
- TEACHER_NAME_FIX_SUMMARY.md, schedule_ordering_plan.md
- inspect_davies.md, inspect_out_len.md, inspect_out_len_utf8.md

## Phase 2–3 – Temp and logs

- Temp: temp_json.json, temp_log.txt, tmpclaude-* (dirs)
- Logs/outputs: all *.txt in root (all_friday_schedules*, analysis_results, audit_output, benchmark_output, crash_log*, db_debug_log*, debug_output, final_verify_*, full-log*, hyperlink_debug*, inspect_out, link_comparison_*, schedules_friday*, sci_debug, slot_list, test_output*, user_dump, week_output)

## Phase 4 – Test/debug files to docs/archive/test-files

- test.png, test_hyperlink_robustness.docx, test_output.txt, test_output_dedup.txt, test_results_verification.txt
- mock_output.docx, mock_output.html
- debug_document.xml, debug_styles.xml, debug_styles_v2.xml, debug_styles_v3.xml, debug_styles_v4.xml
- template_document.xml, template_styles.xml

## Phase 5 – Scripts

- Python: all *.py in root -> tools/archive/root-scripts/
- Batch: start-app-cursor.bat, start-frontend.bat -> docs/archive/scripts/batch/
- PowerShell (archive): build-apk.ps1, check_backend_port.ps1, clean_env.ps1, copy-db-to-tablet.ps1, install-apk.ps1, start-backend-safe.ps1, start-backend-with-logs.ps1, start-frontend-with-logs.ps1, sync-database-to-tablet.ps1, test-database-direct.ps1, update-tablet.ps1 -> docs/archive/scripts/powershell/

## Phase 6 – Other

- android16-edge.html, edge-to-edge.html, immersive.html -> docs/archive/test-files/
- formatted_plan.json, full_plan.json, latest_lesson.json, latest_plan.json, latest_raw.json, monday_slots.json, monday_slots_v2.json, plan_20_slots.json, plan_content.json, plan_dump.json, plan_full.json, suspect_plan.json -> docs/archive/test-files/ (or root-documentation as data)
- packages.txt, python-sync-processor.spec, sqlite_schema.sql -> docs/archive/root-documentation/ or test-files
