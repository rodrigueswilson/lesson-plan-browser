# Unified Frontend Rollback Plan

This document provides step-by-step procedures for reverting changes if the unified frontend implementation encounters critical issues.

**Last Updated**: 2025-01-XX  
**Status**: Pre-Implementation Rollback Plan

## Rollback Strategy

### Rollback Levels

1. **Quick Rollback**: Restore specific files from git or archive
2. **Phase Rollback**: Revert all changes from a specific phase
3. **Full Rollback**: Complete reversion to pre-unification state

### Rollback Triggers

**Immediate Rollback Required:**
- Critical bugs that break core functionality
- Build failures that cannot be resolved quickly
- Data loss or corruption
- Security vulnerabilities introduced

**Consider Rollback:**
- Multiple test failures
- Performance degradation
- User-reported critical issues
- Timeline pressure

## Pre-Rollback Checklist

Before rolling back:

- [ ] Identify the issue clearly
- [ ] Document the problem
- [ ] Determine rollback scope (quick, phase, or full)
- [ ] Verify backup/checkpoint exists
- [ ] Notify team members
- [ ] Plan rollback steps
- [ ] Test rollback procedure (if time permits)

## Quick Rollback Procedures

### Rollback Specific File

**Scenario**: Single file causing issues

**Steps:**

1. **Identify Problem File**
   ```bash
   # Check git status
   git status
   ```

2. **Restore from Git**
   ```bash
   # Find pre-unification commit
   git log --oneline | grep "Pre-unification checkpoint"
   # Note commit hash
   
   # Restore specific file
   git checkout <commit-hash> -- <file-path>
   ```

3. **Restore from Archive** (if git restore not possible)
   ```powershell
   # Copy from archive
   Copy-Item "docs/archive/frontend/pc-version/App.tsx.backup" -Destination "frontend/src/App.tsx"
   ```

4. **Verify Restoration**
   - Test the restored file
   - Verify functionality works
   - Commit the rollback

**Example: Rollback App.tsx**

```bash
# Restore PC App.tsx
git checkout <pre-unification-commit> -- frontend/src/App.tsx

# Or from archive
Copy-Item docs/archive/frontend/pc-version/App.tsx.backup -Destination frontend/src/App.tsx

# Test
cd frontend
npm run tauri:dev
```

### Rollback Phase Changes

**Scenario**: Entire phase needs to be reverted

**Steps:**

1. **Identify Phase Commit**
   ```bash
   # Find phase completion commit
   git log --oneline | grep "Phase X complete"
   ```

2. **Revert Phase Files**
   ```bash
   # Restore all files changed in phase
   git checkout <phase-start-commit> -- <file1> <file2> ...
   ```

3. **Verify Phase Rollback**
   - Test all phase-related functionality
   - Verify no broken dependencies
   - Document what was rolled back

## Full Rollback Procedures

### Complete Reversion to Pre-Unification State

**Scenario**: Complete rollback needed

**WARNING**: This discards ALL changes. Use only if absolutely necessary.

**Steps:**

1. **Create Current State Backup** (if not already committed)
   ```bash
   # Commit current state first
   git add .
   git commit -m "Pre-rollback checkpoint"
   ```

2. **Identify Pre-Unification Commit**
   ```bash
   # Find pre-unification checkpoint
   git log --oneline | grep "Pre-unification checkpoint"
   # Note commit hash (e.g., abc1234)
   ```

3. **Hard Reset to Pre-Unification**
   ```bash
   # WARNING: This discards all changes
   git reset --hard <pre-unification-commit>
   ```

4. **Restore Archived Files** (if needed)
   ```powershell
   # Restore PC App.tsx
   Copy-Item docs/archive/frontend/pc-version/App.tsx.backup -Destination frontend/src/App.tsx
   
   # Restore tablet App.tsx
   Copy-Item docs/archive/frontend/tablet-version/App.tsx.backup -Destination lesson-plan-browser/frontend/src/App.tsx
   ```

5. **Verify Both Platforms Work**
   ```bash
   # Test PC
   cd frontend
   npm run tauri:dev
   
   # Test tablet build
   cd ../lesson-plan-browser
   .\scripts\run-with-ndk.ps1 -Target arm64
   ```

6. **Document Rollback**
   - Update migration log
   - Document reason for rollback
   - Note what was reverted

### Alternative: Create Rollback Branch

**Safer Approach**: Create rollback branch instead of hard reset

**Steps:**

1. **Create Rollback Branch**
   ```bash
   # Create branch from pre-unification commit
   git checkout -b rollback/unified-frontend <pre-unification-commit>
   ```

2. **Switch to Rollback Branch**
   ```bash
   git checkout rollback/unified-frontend
   ```

3. **Verify Rollback Branch**
   - Test both platforms
   - Verify functionality

4. **Merge or Replace Main** (if rollback branch works)
   ```bash
   # Option A: Merge rollback into main
   git checkout main
   git merge rollback/unified-frontend
   
   # Option B: Replace main with rollback
   git checkout main
   git reset --hard rollback/unified-frontend
   ```

## Platform-Specific Rollbacks

### Rollback PC Version Only

**Steps:**

1. **Restore PC App.tsx**
   ```bash
   git checkout <pre-unification-commit> -- frontend/src/App.tsx
   ```

2. **Restore PC Components** (if needed)
   ```bash
   git checkout <pre-unification-commit> -- frontend/src/components/
   ```

3. **Test PC Build**
   ```bash
   cd frontend
   npm run tauri:dev
   ```

### Rollback Tablet Version Only

**Steps:**

1. **Restore Tablet App.tsx**
   ```bash
   git checkout <pre-unification-commit> -- lesson-plan-browser/frontend/src/App.tsx
   ```

2. **Test Tablet Build**
   ```bash
   cd lesson-plan-browser
   .\scripts\run-with-ndk.ps1 -Target arm64
   ```

## Rollback Verification

### After Any Rollback

**Verification Steps:**

1. **Build Verification**
   - [ ] PC build succeeds: `npm run tauri:build` in `frontend/`
   - [ ] Tablet build succeeds: `.\scripts\run-with-ndk.ps1` in `lesson-plan-browser/`

2. **Functionality Verification**
   - [ ] PC app launches and works
   - [ ] Tablet app launches and works
   - [ ] Core features functional
   - [ ] No console errors

3. **Integration Verification**
   - [ ] Backend connectivity works
   - [ ] API calls succeed
   - [ ] Data loads correctly

4. **Regression Check**
   - [ ] No new bugs introduced
   - [ ] Existing features still work
   - [ ] Performance acceptable

## Rollback Documentation

### Document Rollback

**Update These Files:**

1. **Migration Log**
   - Add rollback entry
   - Document reason
   - Note files reverted

2. **Test Results**
   - Document rollback tests
   - Note any issues found

3. **Archive Index**
   - Update if files restored from archive

### Rollback Entry Template

```markdown
| Date | Phase | File | Action | Description | Author | Verification | Status |
|------|-------|------|--------|-------------|--------|--------------|--------|
| YYYY-MM-DD | Rollback | file.tsx | Rolled back | Reason: [issue]. Restored from commit [hash] | Name | Tests pass | Complete |
```

## Prevention Strategies

### To Avoid Needing Rollback

1. **Incremental Implementation**: One phase at a time
2. **Comprehensive Testing**: Test after each phase
3. **Git Commits**: Commit after each successful phase
4. **Backup Strategy**: Archive files before replacing
5. **Code Review**: Review changes before proceeding
6. **Documentation**: Document all changes

## Emergency Contacts

**If Rollback Needed:**
- Development Team Lead
- Backend Team (if API issues)
- Build System Admin (if build issues)

## Related Documents

- `docs/implementation/UNIFIED_FRONTEND_IMPLEMENTATION_GUIDE.md` - Main guide
- `docs/implementation/UNIFIED_FRONTEND_MIGRATION_LOG.md` - Change tracking
- `docs/archive/frontend/ARCHIVE_INDEX.md` - Archive index

---

**Document Status**: Complete - Ready for Use  
**Last Updated**: 2025-01-XX  
**Maintainer**: Development Team

