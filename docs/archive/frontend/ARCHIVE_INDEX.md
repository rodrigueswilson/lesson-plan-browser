# Frontend Archive Index

This document tracks all archived frontend files, their original locations, archive locations, and reasons for archiving.

**Last Updated**: 2025-01-27  
**Status**: Implementation Complete - Archive Index

## Archive Schema

Each archived file is documented with:
- **Original Path**: Where the file was originally located
- **Archive Location**: Where it's archived now
- **Date Archived**: When it was moved to archive (YYYY-MM-DD)
- **Reason**: Why it was archived (superseded, deprecated, etc.)
- **Replacement**: Link to replacement file or feature (if applicable)
- **Component**: Category (pc-version, tablet-version, build-scripts, documentation)

## Archived Files

### PC Version Files

| Original Path | Archive Location | Date | Reason | Replacement | Component |
|---------------|------------------|------|--------|-------------|-----------|
| `frontend/src/App.tsx` | `docs/archive/frontend/pc-version/App.tsx.backup` | 2025-01-27 | Superseded | `lesson-plan-browser/frontend/src/App.tsx` (unified) | pc-version |
| `frontend/src/components/mobile/MobileNav.tsx` | `docs/archive/frontend/pc-version/components/MobileNav.tsx` | 2025-01-27 | Not needed | Tablet has no navigation (unified frontend) | pc-version |
| `frontend/src/components/mobile/MobileNav.test.tsx` | `docs/archive/frontend/pc-version/components/MobileNav.test.tsx` | 2025-01-27 | Not needed | Tablet has no navigation (unified frontend) | pc-version |

### Tablet Version Files

| Original Path | Archive Location | Date | Reason | Replacement | Component |
|---------------|------------------|------|--------|-------------|-----------|
| `lesson-plan-browser/frontend/src/App.tsx` | `docs/archive/frontend/tablet-version/App.tsx.backup` | 2025-01-27 | Becomes unified | `lesson-plan-browser/frontend/src/App.tsx` (unified) | tablet-version |

### Documentation Files

| Original Path | Archive Location | Date | Reason | Replacement | Component |
|---------------|------------------|------|--------|-------------|-----------|
| `FRONTEND_VERSIONS_DOCUMENTATION.md` | `docs/archive/frontend/documentation/FRONTEND_VERSIONS_DOCUMENTATION.md` | 2025-01-27 | Superseded | `docs/implementation/UNIFIED_FRONTEND_IMPLEMENTATION_GUIDE.md` | documentation |

### Build Scripts

| Original Path | Archive Location | Date | Reason | Replacement | Component |
|---------------|------------------|------|--------|-------------|-----------|
| (Reference only) | `lesson-plan-browser/scripts/archive/deprecated-build-scripts/` | N/A | Already archived | See `docs/archive/frontend/build-scripts/README.md` | build-scripts |

**Note**: Deprecated build scripts are already archived in `lesson-plan-browser/scripts/archive/`. This index references them but does not duplicate them.

## Archive Organization

### Directory Structure

```
docs/archive/frontend/
├── pc-version/              # PC-specific archived files
│   ├── App.tsx.backup
│   └── components/
│       ├── MobileNav.tsx
│       └── MobileNav.test.tsx
├── tablet-version/          # Tablet-specific archived files
│   └── App.tsx.backup
├── build-scripts/           # Build script references
│   └── README.md            # Links to lesson-plan-browser/scripts/archive/
├── documentation/           # Superseded documentation
│   └── FRONTEND_VERSIONS_DOCUMENTATION.md
└── ARCHIVE_INDEX.md         # This file
```

## Archive Maintenance

### Adding New Files to Archive

When archiving a new file:

1. **Create Backup**: Copy file to archive location with `.backup` extension if original
2. **Update Index**: Add entry to this document with all required fields
3. **Update Original**: If file is replaced, update original location with redirect or new content
4. **Document Reason**: Clearly state why file was archived
5. **Link Replacement**: Provide link to replacement file or feature

### Archive Cleanup

**Review Periodically:**
- Files older than 1 year: Review for deletion
- Superseded files: Keep for reference, but mark as historical
- Duplicate files: Remove if truly duplicate

**Deletion Criteria:**
- File has been archived for > 1 year
- Replacement is stable and tested
- No references to archived file in codebase
- Git history preserves file if needed

## Archive Statistics

**Total Archived Files**: 5  
**PC Version Files**: 3  
**Tablet Version Files**: 1  
**Documentation Files**: 1  
**Build Scripts**: 0 (referenced only)

## Related Documents

- `docs/implementation/UNIFIED_FRONTEND_IMPLEMENTATION_GUIDE.md` - Main implementation guide
- `docs/implementation/UNIFIED_FRONTEND_MIGRATION_LOG.md` - Migration tracking
- `lesson-plan-browser/scripts/archive/deprecated-build-scripts/` - Deprecated build scripts

---

**Document Status**: Complete - Archive Index Updated  
**Last Updated**: 2025-01-27  
**Maintainer**: Development Team

