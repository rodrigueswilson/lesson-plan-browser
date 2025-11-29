# Diagnostic Scripts

**Location:** `tools/diagnostics/`  
**Migration Date:** 2025-01-27 (Phase 2 and Phase 6)  
**Purpose:** Diagnostic, analysis, and debugging scripts for troubleshooting and verification

## Original Locations

All scripts in this directory were originally located at the project root. They have been moved here as part of the codebase decluttering process (Phases 2 and 6).

## How to Run Scripts

**IMPORTANT:** These scripts must be run from the project root directory (`D:\LP`) because they import from `backend`, `tools`, etc.

### From Project Root (Recommended)

```bash
# Windows (PowerShell)
cd D:\LP
python tools\diagnostics\check_config.py
python tools\diagnostics\analyze_input_hyperlinks.py
python tools\diagnostics\debug_extraction.py

# Linux/Mac
cd /path/to/project
python tools/diagnostics/check_config.py
python tools/diagnostics/analyze_input_hyperlinks.py
python tools/diagnostics/debug_extraction.py
```

### Note on PYTHONPATH

Scripts assume they're run from the project root where:
- `backend/` module is accessible
- `tools/` module is accessible
- Project imports work correctly

If you get `ModuleNotFoundError`, ensure you're in the project root directory.

## Available Scripts

### Check Scripts (Phase 2)
- Database diagnostics: `check_db_*.py`, `check_env_db.py`
- Configuration: `check_config.py`, `check_wilson_config.py`
- Data validation: `check_json_structure.py`, `check_schema.py`
- User & plan diagnostics: `check_users.py`, `check_weekly_plan.py`, etc.
- Slot diagnostics: `check_slots.py`, `check_daniela_slots.py`, etc.
- File & link diagnostics: `check_hyperlinks_now.py`, `check_missing_links.py`, etc.

### Analyze Scripts (Phase 6)
- `analyze_input_hyperlinks.py` - Analyze input hyperlinks
- `analyze_output_hyperlinks.py` - Analyze output hyperlinks
- `analyze_teacher_files.py` - Analyze teacher files
- `comprehensive_analysis_both_folders.py` - Comprehensive folder analysis
- `comprehensive_diagnostic.py` - Comprehensive diagnostics
- `diagnostic_hyperlink_analysis.py` - Hyperlink analysis
- `diagnostic_scripts.py` - Diagnostic script utilities

### Debug Scripts (Phase 6)
- `debug_extraction.py` - Debug extraction process
- `debug_file_resolution.py` - Debug file resolution
- `debug_lesson_json.py` - Debug lesson JSON
- `debug_slot5.py` - Debug slot 5

### Diagnostic Scripts (Phase 6)
- `diagnose_crash.py` - Diagnose crashes
- `diagnose_cross_contamination.py` - Diagnose cross-contamination issues

## Notes

- These scripts are diagnostic tools and may not be used regularly
- Some scripts may have dependencies on project structure
- If a script fails, check that you're running from the project root
- For issues, refer to `docs/maintenance/DECLUTTERING_LOG.md`

## Migration Log

See `docs/maintenance/DECLUTTERING_LOG.md` for full migration history.

