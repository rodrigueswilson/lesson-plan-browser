# Maintenance Scripts

**Location:** `tools/maintenance/`  
**Migration Date:** 2025-01-27 (Phase 6)  
**Purpose:** Ongoing maintenance utilities including fixes, cleanup, configuration, auditing, and verification

## Original Locations

All scripts in this directory were originally located at the project root. They have been moved here as part of the codebase decluttering process (Phase 6).

## How to Run Scripts

**IMPORTANT:** These scripts must be run from the project root directory (`D:\LP`) because they import from `backend`, `tools`, etc.

### From Project Root (Recommended)

```bash
# Windows (PowerShell)
cd D:\LP
python tools\maintenance\verify_config.py
python tools\maintenance\fix_daniela_file_patterns.py
python tools\maintenance\cleanup_users.py

# Linux/Mac
cd /path/to/project
python tools/maintenance/verify_config.py
python tools/maintenance/fix_daniela_file_patterns.py
python tools/maintenance/cleanup_users.py
```

### Note on PYTHONPATH

Scripts assume they're run from the project root where:
- `backend/` module is accessible
- `tools/` module is accessible
- Project imports work correctly

If you get `ModuleNotFoundError`, ensure you're in the project root directory.

## Available Scripts

### Fix Scripts
- `fix_daniela_file_patterns.py` - Fix Daniela file patterns
- `fix_daniela_parent_folder.py` - Fix Daniela parent folder
- `fix_daniela_path.py` - Fix Daniela paths
- `fix_daniela_slots_paths.py` - Fix Daniela slot paths
- `fix_daniela_teachers.py` - Fix Daniela teachers
- `fix_wilson_patterns.py` - Fix Wilson patterns

### Cleanup Scripts
- `cleanup_demo_data.py` - Clean up demo data
- `cleanup_semantic.py` - Clean up semantic data
- `cleanup_stuck_plans.py` - Clean up stuck plans
- `cleanup_users.py` - Clean up users
- `clear_cache.py` - Clear cache
- `clear_daniela_slot_files.py` - Clear Daniela slot files

### Configuration Scripts
- `configure_test_slot.py` - Configure test slot
- `configure_wilson_slots.py` - Configure Wilson slots

### Audit Scripts
- `metadata_audit.py` - Audit metadata
- `pre_implementation_audit.py` - Pre-implementation audit

### Verification Scripts
- `verify_backend_code.py` - Verify backend code
- `verify_both_outputs.py` - Verify both outputs
- `verify_config.py` - Verify configuration
- `verify_daniela_config.py` - Verify Daniela configuration
- `verify_hyperlink_placement_auto.py` - Auto-verify hyperlink placement
- `verify_hyperlink_placement.py` - Verify hyperlink placement
- `verify_migration.py` - Verify migration

### Validation Scripts
- `validate_assumptions.py` - Validate assumptions

### Maintenance Utilities
- `generate_inventory.py` - Generate decluttering inventory
- `consolidate_tool_scripts.py` - Consolidate tool scripts
- `archive_documentation.py` - Archive documentation

## Notes

- These scripts are maintenance utilities and may be used regularly
- Some scripts may have dependencies on project structure
- If a script fails, check that you're running from the project root
- For issues, refer to `docs/maintenance/DECLUTTERING_LOG.md`

## Migration Log

See `docs/maintenance/DECLUTTERING_LOG.md` for full migration history.

