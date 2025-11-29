# Rollback Procedure

**Purpose:** Emergency restoration procedure if decluttering changes break critical functionality

## Quick Rollback Commands

### Rollback Phase 2 (Diagnostic Scripts)

If scripts fail after moving to `tools/diagnostics/`, restore to root:

```powershell
# From project root
Get-ChildItem tools\diagnostics\check_*.py | ForEach-Object {
    Move-Item $_.FullName -Destination $_.Name -Force
}
```

Or manually:
```powershell
Move-Item tools\diagnostics\check_*.py -Destination . -Force
```

### Rollback Phase 3 (Test Files)

If tests fail after moving to `tests/`:

```powershell
# Identify moved test files from log
# Move back to original locations
# Example:
Move-Item tests\test_file_matching.py -Destination . -Force
```

### Rollback Phase 4 (Documentation)

If documentation links break:

```powershell
# Move archived docs back to original locations
# Example:
Move-Item docs\archive\sessions\SESSION_1_COMPLETE.md -Destination . -Force
```

## Full Restoration from Git

If rollback is needed, restore from git history:

```bash
# View recent commits
git log --oneline -10

# Restore specific file
git checkout <commit-hash> -- <file-path>

# Restore entire directory
git checkout <commit-hash> -- <directory-path>

# Restore entire repository state (NUCLEAR OPTION)
git reset --hard <commit-hash>
```

## Verification After Rollback

1. **Test scripts:** Run moved scripts to verify functionality
2. **Test suite:** Run `pytest` to verify tests still work
3. **Documentation:** Check markdown links with `markdown-link-check`
4. **Application:** Run application smoke tests

## Prevention

- ✅ All changes logged in `docs/maintenance/DECLUTTERING_LOG.md`
- ✅ Git commits after each phase
- ✅ Test scripts before and after moves
- ✅ Document all file locations in `DECLUTTERING_INVENTORY.md`

## Emergency Contacts

- Review `docs/maintenance/DECLUTTERING_LOG.md` for recent changes
- Check git history for file locations before moves
- Refer to `docs/maintenance/DECLUTTERING_INVENTORY_NOTES.md` for original locations

