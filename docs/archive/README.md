# Codebase Archive

This directory contains archived files from the codebase that are no longer actively used but are kept for reference, historical purposes, or potential future use.

## Archive Structure

```
docs/archive/
├── frontend/          # Frontend-related archived files
│   ├── pc-version/    # PC frontend archived files
│   ├── tablet-version/ # Tablet frontend archived files
│   ├── documentation/  # Superseded frontend documentation
│   └── ARCHIVE_INDEX.md
├── deprecated/        # Deprecated files archive
│   ├── documentation/ # Deprecated documentation
│   ├── strategies/    # Deprecated strategy JSON files
│   ├── samples/       # Deprecated sample files
│   └── ARCHIVE_INDEX.md
├── root-documentation/ # Root directory MD files
├── android-documentation/ # Android-specific docs
├── test-files/        # Test and debug files
├── temp-files/        # Temporary files
├── scripts/           # Archived scripts
│   ├── batch/         # Batch scripts
│   └── powershell/    # PowerShell scripts
├── ROOT_ARCHIVE_INDEX.md # Root archive index
└── README.md          # This file
```

## Archive Categories

### Frontend Archive (`frontend/`)

Contains archived files from the unified frontend implementation:
- PC version files (App.tsx backups, MobileNav components)
- Tablet version files (App.tsx backups)
- Superseded documentation (FRONTEND_VERSIONS_DOCUMENTATION.md)

**Index**: [frontend/ARCHIVE_INDEX.md](frontend/ARCHIVE_INDEX.md)

### Deprecated Files Archive (`deprecated/`)

Contains archived files from the `deprecated/` directory:
- Documentation files (old prompts, READMEs)
- Strategy JSON files (old bilingual strategy versions)
- Sample files (old lesson plan templates and samples)

**Index**: [deprecated/ARCHIVE_INDEX.md](deprecated/ARCHIVE_INDEX.md)

### Root Directory Archive

Contains files archived from the project root directory:
- **root-documentation/**: ~95 documentation MD files (analysis, status, guides)
- **android-documentation/**: 5 Android-specific documentation files
- **test-files/**: ~20 test files, debug files, and samples
- **temp-files/**: Temporary files kept for reference
- **scripts/**: Archived batch and PowerShell scripts
  - **batch/**: ~26 batch scripts
  - **powershell/**: ~15 PowerShell scripts

**Python Scripts**: Moved to `tools/archive/root-scripts/` (~56 files)  
**Log Files**: Moved to `logs/archive/` (~11 files)

**Index**: [ROOT_ARCHIVE_INDEX.md](ROOT_ARCHIVE_INDEX.md)

## Archive Maintenance

### Adding Files to Archive

1. **Create Backup**: Copy file to appropriate archive location
2. **Update Index**: Add entry to relevant ARCHIVE_INDEX.md
3. **Remove Original**: Remove file from active codebase (after verification)
4. **Document**: Clearly state reason for archiving and replacement

### Archive Cleanup Policy

- **Review Period**: Files older than 1 year should be reviewed
- **Deletion Criteria**: 
  - File archived for > 1 year
  - Replacement is stable and tested
  - No references in active codebase
  - Git history preserves file if needed

## Archive Statistics

**Frontend Archive**: 5 files  
**Deprecated Archive**: 27 files  
**Root Directory Archive**: ~230 files
  - Documentation: ~95 files
  - Python Scripts: ~56 files
  - Batch Scripts: ~26 files
  - Test Files: ~20 files
  - PowerShell Scripts: ~15 files
  - Log Files: ~11 files
  - Android Docs: 5 files
  - Other: ~2 files

**Total Archived**: ~260+ files

## Related Documents

- `docs/implementation/DECLUTTERING_PLAN.md` - Decluttering plan
- `docs/implementation/UNIFIED_FRONTEND_IMPLEMENTATION_GUIDE.md` - Unified frontend guide

---

**Last Updated**: 2025-01-27  
**Maintainer**: Development Team
