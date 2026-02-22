# Root Directory Archive Index

This document tracks all files archived from the root directory during the decluttering process.

**Last Updated**: 2026-02-22  
**Status**: Archive Complete (Session 12)

**Session 12 (2026-02-22):** Additional root files archived per ROOT_DECLUTTERING_PLAN: root-documentation (16 MD files), logs/archive (30+ .txt and .log), docs/archive/test-files (test/debug/JSON/HTML/XML), tools/archive/root-scripts (56 Python scripts), docs/archive/scripts/batch (2 .bat), docs/archive/scripts/powershell (11 .ps1), docs/archive/temp-files (temp_json.json). Root now keeps only essential config, README, requirements.txt, pytest.ini, start-backend.bat, start-app.bat, start-app-with-logs.ps1, CHECK_BACKEND_STATUS.ps1, test-unified-frontend.ps1, and project assets. tmpclaude-* removed from tracking; .gitignore updated.

## Archive Schema

Each archived file is documented with:
- **Original Path**: Where the file was originally located (root directory)
- **Archive Location**: Where it's archived now
- **Date Archived**: When it was moved to archive (YYYY-MM-DD)
- **Reason**: Why it was archived (superseded, deprecated, temporary, etc.)
- **Category**: Type of file (documentation, script, test, log, etc.)

## Archive Categories

### Documentation Files

**Location**: `docs/archive/root-documentation/`

All root-level markdown documentation files that are superseded, historical, or no longer actively used.

**Count**: ~90 files

**Examples**:
- Analysis documents (ANALYSIS_*.md)
- Status reports (BUILD_*.md, PHASE*.md)
- Implementation summaries
- Testing guides
- Troubleshooting documents

**See**: `docs/archive/root-documentation/` for complete list

### Android Documentation

**Location**: `docs/archive/android-documentation/`

Android-specific documentation files from root directory.

**Count**: 5 files

**Files**:
- ANDROID_BUNDLE_APPROACH.md
- ANDROID_DEBUG_NOTES.md
- ANDROID_PYTHON_RUNTIME_APPROACH.md
- ANDROID_PYTHON_SOLUTION.md
- ANDROID_STANDALONE_ISSUE.md

### Test Files

**Location**: `docs/archive/test-files/`

Test files, debug files, and sample files from root directory.

**Count**: ~15 files

**Files Include**:
- test_*.docx, test_*.md, test_*.rs, test_*.db
- debug_*.html, debug_*.pdf
- debuginfo*.md
- Error JSON files (w47_*.json)

### Log Files

**Location**: `logs/archive/`

Log files and output files from root directory.

**Count**: ~10 files

**Files Include**:
- *.log files (backend_debug.log, backend_error.log, etc.)
- *.txt log files (app-launch-logs.txt, tablet-*.txt)
- ipconfig*.txt
- verify_output.txt

### Python Scripts

**Location**: `tools/archive/root-scripts/`

Python utility scripts that were in root directory, moved to tools archive.

**Count**: ~50 files

**Scripts Include**:
- Utility scripts (add_*, generate_*, verify_*, etc.)
- Migration scripts (migrate_*.py)
- Test/repro scripts (repro_*.py, test_*.py)
- One-off processing scripts

### Batch Scripts

**Location**: `docs/archive/scripts/batch/`

Batch (.bat) scripts for starting/restarting services, mostly superseded.

**Count**: ~25 files

**Scripts Include**:
- start-*.bat
- restart-*.bat
- fresh-start-*.bat
- fix-*.bat
- Various utility batch scripts

### PowerShell Scripts

**Location**: `docs/archive/scripts/powershell/`

PowerShell (.ps1) scripts from root directory, mostly utility scripts.

**Count**: ~15 files

**Scripts Include**:
- bundle_*.ps1
- clear-*.ps1
- diagnose-*.ps1
- Utility PowerShell scripts

### Temporary Files

**Location**: `docs/archive/temp-files/`

Temporary files that were kept for reference.

**Files**:
- temp_apk.apk
- temp_apk.zip
- temp.zip

**Note**: Most temporary files were deleted. Only a few were kept for reference.

## Archive Statistics

**Total Files Archived**: ~200+ files

**Breakdown**:
- Documentation: ~90 files
- Python Scripts: ~50 files
- Batch Scripts: ~25 files
- Test Files: ~15 files
- PowerShell Scripts: ~15 files
- Log Files: ~10 files
- Android Docs: 5 files
- Temporary Files: 3 files

## Archive Organization

### Directory Structure

```
docs/archive/
├── root-documentation/     # Root MD files
├── android-documentation/  # Android-specific docs
├── test-files/             # Test and debug files
├── temp-files/             # Temporary files
└── scripts/
    ├── batch/              # Batch scripts
    └── powershell/         # PowerShell scripts

tools/archive/
└── root-scripts/           # Python scripts from root

logs/archive/               # Log files from root
```

## Archive Maintenance

### Adding New Files to Archive

When archiving a new root file:

1. **Move File**: Move file to appropriate archive subdirectory
2. **Update Index**: Add entry to this document if significant
3. **Document Reason**: Clearly state why file was archived
4. **Link Replacement**: Provide link to replacement if applicable

### Archive Cleanup

**Review Periodically:**
- Files older than 1 year: Review for deletion
- Superseded files: Keep for reference, but mark as historical
- Temporary files: Can be deleted after verification

**Deletion Criteria:**
- File has been archived for > 1 year
- Replacement is stable and tested
- No references to archived file in codebase
- Git history preserves file if needed

## Related Documents

- `docs/archive/README.md` - Main archive overview
- `docs/implementation/ROOT_DECLUTTERING_PLAN.md` - Decluttering plan
- `docs/implementation/DECLUTTERING_PLAN.md` - Original decluttering plan

---

**Document Status**: Complete - Archive Index Created  
**Last Updated**: 2025-01-27  
**Maintainer**: Development Team

