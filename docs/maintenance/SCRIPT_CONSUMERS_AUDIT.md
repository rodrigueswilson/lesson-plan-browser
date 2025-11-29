# Script Consumers Audit

**Date:** 2025-01-27  
**Phase:** 2.0 Prerequisite  
**Purpose:** Identify all references to diagnostic scripts (`check_*.py`, `analyze_*.py`, `fix_*.py`, `debug_*.py`) before moving them

## Audit Commands Executed

### 1. Search .bat files for script references
```powershell
rg "check_.*\.py" -n --glob "*.bat"
```
**Result:** No matches found (0 files)

### 2. Search Python files for script references
```powershell
rg "(check|analyze|fix|debug)_.*\.py" -n --glob "*.py"
```
**Results:**
- `tools/maintenance/generate_inventory.py` (lines 45-46): References to `check_*.py` pattern (inventory script - safe)
- `check_json_structure.py` (lines 85, 87, 97): Self-references in usage examples (safe)
- `test_hyperlink_simple.py` (line 109): References `tools/analyze_hyperlink_diagnostics.py` (already in tools/)
- `tools/analyze_hyperlink_diagnostics.py` (lines 6, 189, 191): Self-references in usage examples (safe)
- `test_hyperlink_diagnostics.py` (line 98): References `tools/analyze_hyperlink_diagnostics.py` (already in tools/)

### 3. Search Markdown files for script references
```powershell
rg "(check|analyze|fix|debug)_.*\.py" -n --glob "*.md"
```
**Results:**
- `docs/maintenance/DECLUTTERING_INVENTORY_NOTES.md`: Documentation about decluttering (safe)
- `decluttering_plan.md`: Plan documentation (safe)
- `docs/FIXES_NEEDED_IN_PLAN.md`: Plan documentation (safe)
- `DIAGNOSIS_CHECKLIST.md` (line 34, 130, 152): References `check_json_structure.py` as example command
- `MULTI_SLOT_NOT_DETECTED_DIAGNOSIS.md` (line 81): References `check_json_structure.py` as example command

### 4. Check .pre-commit-config.yaml
**File:** `.pre-commit-config.yaml`  
**Line 116:** References `tools/check_snapshot_updates.py`  
**Status:** ✅ Already in `tools/` directory - no action needed

### 5. Check for Python imports
```powershell
rg "import.*check_|from.*check_" --glob "*.py"
```
**Results:**
- `diagnostic_scripts.py` (line 250): Function name `check_merger_import()` - not a script reference (safe)

### 6. Check for subprocess/exec calls
```powershell
rg "subprocess.*check_|exec.*check_|run.*check_" --glob "*.py"
```
**Results:** No matches found

## Summary of Required Actions

### ✅ No Action Needed
- **.bat files:** No batch files reference `check_*.py` scripts
- **Python imports:** No Python files import `check_*.py` scripts as modules
- **Subprocess calls:** No scripts execute `check_*.py` scripts via subprocess
- **CI/CD:** No GitHub workflows found
- **Pre-commit:** References `tools/check_snapshot_updates.py` which is already in tools/

### ⚠️ Documentation Updates Required
- **`DIAGNOSIS_CHECKLIST.md`** (lines 34, 130, 152): Update examples to use `python tools/diagnostics/check_json_structure.py`
- **`MULTI_SLOT_NOT_DETECTED_DIAGNOSIS.md`** (line 81): Update example to use `python tools/diagnostics/check_json_structure.py`

### 📝 Notes
- All references found are either:
  1. Documentation examples (will update after move)
  2. Self-references in usage examples (safe)
  3. Already in `tools/` directory (no move needed)
  4. Inventory/documentation files (safe)

## Risk Assessment

**Overall Risk:** ✅ **LOW**

- No automated workflows depend on root-level `check_*.py` scripts
- No batch files need updating
- No Python code imports these scripts
- Only documentation examples need updating (non-critical)

## Next Steps

1. ✅ Audit complete - proceed with Phase 2.1 (move scripts)
2. After move: Update documentation examples in `DIAGNOSIS_CHECKLIST.md` and `MULTI_SLOT_NOT_DETECTED_DIAGNOSIS.md`
3. Verify scripts work from new location

