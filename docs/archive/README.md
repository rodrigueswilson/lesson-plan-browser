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
**Total Archived**: 32 files

## Related Documents

- `docs/implementation/DECLUTTERING_PLAN.md` - Decluttering plan
- `docs/implementation/UNIFIED_FRONTEND_IMPLEMENTATION_GUIDE.md` - Unified frontend guide

---

**Last Updated**: 2025-01-27  
**Maintainer**: Development Team
