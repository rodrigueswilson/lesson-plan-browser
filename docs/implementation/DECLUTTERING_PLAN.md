# Codebase Decluttering and Archiving Plan

**Date**: 2025-01-27  
**Status**: Ready for Execution  
**Related**: Unified Frontend Implementation - Phase 10

## Overview

This plan systematically identifies, archives, and removes deprecated, superseded, or unused files from the codebase following the successful unified frontend implementation.

## Objectives

1. **Archive deprecated frontend files** that have been replaced by the unified frontend
2. **Organize deprecated/ directory** into proper archive structure
3. **Remove duplicate or temporary files** that are no longer needed
4. **Update documentation** to reflect archived files
5. **Maintain git history** for all archived files

## Archive Categories

### Category 1: Frontend Files (Unified Frontend Related)

#### Files Already Backed Up (Need to Remove Originals)

| Original Path | Archive Location | Status | Action |
|---------------|------------------|--------|--------|
| `frontend/src/components/mobile/MobileNav.tsx` | `docs/archive/frontend/pc-version/components/MobileNav.tsx` | ✅ Backed up | Remove original |
| `frontend/src/components/mobile/MobileNav.test.tsx` | `docs/archive/frontend/pc-version/components/MobileNav.test.tsx` | ✅ Backed up | Remove original |
| `FRONTEND_VERSIONS_DOCUMENTATION.md` | `docs/archive/frontend/documentation/FRONTEND_VERSIONS_DOCUMENTATION.md` | ✅ Backed up | Remove original |

**Note**: `frontend/src/App.tsx` and `lesson-plan-browser/frontend/src/App.tsx` are NOT archived because:
- PC version now re-exports unified version (still needed)
- Unified version is the active implementation (still needed)

### Category 2: Deprecated Directory Files

The `deprecated/` directory contains 27 files that should be organized into archive:

#### Documentation Files (Move to `docs/archive/deprecated/documentation/`)
- `deprecated/README.md`
- `deprecated/enhanced_prompt_v4.md`
- `deprecated/Prompt_Lesson_Plan_V3_WIDA_Enhanced.md`
- `deprecated/Prompt Lesson Plan V2.md`

#### JSON Strategy Files (Move to `docs/archive/deprecated/strategies/`)
- `deprecated/bilingual_strategies_v1_3_full.json`
- `deprecated/bilingual_strategies_v1_3_full_with_refs_v2.json`
- `deprecated/bilingual_strategies_v1_3_chunk01.json`
- `deprecated/bilingual_strategies_v1_3_chunk02.json`
- `deprecated/bilingual_strategies_v1_3_chunk03.json`
- `deprecated/bilingual_strategies_v1_3_chunk04.json`
- `deprecated/bilingual_strategies_v1_3_chunk05.json`
- `deprecated/bilingual_strategies_v1_4_full.json`
- `deprecated/bilingual_strategies_v1_5_full.json`
- `deprecated/bilingual_strategies_v1_6_full.json`
- `deprecated/bilingual_strategies_v2_full.json`
- `deprecated/bilingual_strategies_merged.json`
- `deprecated/temp_merged.json`
- `deprecated/wida_strategy_enhancementsv2.json`
- `deprecated/wida_framework_reference v2.json`
- `deprecated/bilingual_strategies_references_annotated_ordered_by27.md`

#### Sample Files (Move to `docs/archive/deprecated/samples/`)
- `deprecated/Lesson Plan Template SY'25-26.docx`
- `deprecated/Sample lesson plan.txt`
- `deprecated/Sample_lesson_plan_WIDA_enhanced.docx`
- `deprecated/Sample_lesson_plan_WIDA_enhanced.doc`
- `deprecated/Sample_lesson_plan_WIDA_enhanced.txt`
- `deprecated/Lesson Plan Sample.pdf`
- `deprecated/Lesson Plan Sample.docx`

### Category 3: Temporary/Test Files (To Be Identified)

Search for:
- Files with `.tmp`, `.temp`, `.bak`, `.backup` extensions
- Test files that are no longer used
- Duplicate files

## Archive Structure

```
docs/archive/
├── frontend/                    # Already exists
│   ├── pc-version/
│   ├── tablet-version/
│   ├── documentation/
│   └── ARCHIVE_INDEX.md
├── deprecated/                  # New directory
│   ├── documentation/
│   ├── strategies/
│   ├── samples/
│   └── ARCHIVE_INDEX.md
└── README.md                    # Archive overview
```

## Execution Plan

### Phase 1: Frontend Files Archiving

**Steps**:
1. Verify backup files exist in archive
2. Remove original files from active codebase:
   - `frontend/src/components/mobile/MobileNav.tsx`
   - `frontend/src/components/mobile/MobileNav.test.tsx`
   - `FRONTEND_VERSIONS_DOCUMENTATION.md`
3. Remove empty `frontend/src/components/mobile/` directory if empty
4. Update `docs/archive/frontend/ARCHIVE_INDEX.md`

**Verification**:
- [ ] Originals removed
- [ ] Backups exist in archive
- [ ] No broken imports (verify builds still work)
- [ ] Archive index updated

### Phase 2: Deprecated Directory Organization

**Steps**:
1. Create archive structure: `docs/archive/deprecated/{documentation,strategies,samples}/`
2. Move files to appropriate subdirectories
3. Create `docs/archive/deprecated/ARCHIVE_INDEX.md`
4. Create `docs/archive/deprecated/README.md` explaining organization
5. Update root `deprecated/README.md` to point to archive (or remove if empty)

**Verification**:
- [ ] All files moved to archive
- [ ] Archive index created
- [ ] README created
- [ ] Original deprecated/ directory can be removed (or kept with README only)

### Phase 3: Temporary Files Cleanup

**Steps**:
1. Search for temporary files (`.tmp`, `.temp`, `.bak`, `.backup`)
2. Search for duplicate files
3. Review and archive or delete as appropriate
4. Document decisions in archive index

**Verification**:
- [ ] No temporary files in active codebase
- [ ] Duplicates identified and resolved
- [ ] Decisions documented

### Phase 4: Documentation Updates

**Steps**:
1. Update `docs/archive/frontend/ARCHIVE_INDEX.md` with all frontend archives
2. Create `docs/archive/deprecated/ARCHIVE_INDEX.md`
3. Create `docs/archive/README.md` (overview of all archives)
4. Update any references to archived files in active documentation

**Verification**:
- [ ] All archive indexes updated
- [ ] Archive overview created
- [ ] No broken links in documentation

### Phase 5: Final Verification

**Steps**:
1. Run build tests (PC and Android)
2. Verify no broken imports
3. Check git status (ensure only intended files removed)
4. Create summary report

**Verification**:
- [ ] PC build works
- [ ] Android build works
- [ ] No broken imports
- [ ] Git status clean (except intended changes)

## Safety Measures

1. **Git Checkpoint**: Create commit before starting: `git commit -m "Pre-archiving checkpoint"`
2. **Backup Verification**: Verify all backups exist before removing originals
3. **Build Verification**: Test builds after each phase
4. **Incremental Commits**: Commit after each phase
5. **Rollback Plan**: Keep git history for easy rollback

## Archive Index Template

Each archive index should include:
- Original path
- Archive location
- Date archived
- Reason for archiving
- Replacement/reference link
- Component category

## Success Criteria

- [ ] All deprecated frontend files archived and removed
- [ ] Deprecated directory organized and archived
- [ ] Temporary files identified and cleaned up
- [ ] All archive indexes updated
- [ ] Archive overview documentation created
- [ ] No broken builds or imports
- [ ] Git history preserved
- [ ] Documentation updated

## Estimated Impact

**Files to Archive**: ~30 files
**Files to Remove**: ~3 frontend files + deprecated directory contents
**Disk Space**: Minimal (files moved, not duplicated)
**Build Impact**: None (archived files not used in builds)
**Documentation Impact**: Archive indexes updated

## Next Steps After Archiving

1. Update main README.md to reference archive structure
2. Document archive maintenance procedures
3. Set up periodic archive review schedule
4. Consider archive cleanup policy (e.g., files older than 1 year)

---

**Document Status**: Ready for Execution  
**Last Updated**: 2025-01-27  
**Maintainer**: Development Team

