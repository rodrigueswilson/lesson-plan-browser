# Fixes Needed in Decluttering Plan

## Phase 4 Fixes

**After line 291** (after "Latest plan versions: Keep latest version active..."), add:

```markdown
### 4.5 Fix Broken Links

**Action:** Based on Phase 4.2 audit results:
- Update all links in active documentation to point to new archive locations
- For frequently-referenced archived docs, create redirect stubs in original locations:
  ```markdown
  # [Document Title]
  
  This document has been archived. See: [docs/archive/category/filename.md](docs/archive/category/filename.md)
  ```
- Remove dead links if archived content is no longer relevant
- Update any README files that reference archived docs

**Action:** Verify all links after updates:
```bash
markdown-link-check docs/**/*.md
```
- Document any remaining broken links that require manual review

### 4.6 Create Archive Index
```

**Then change line 293** from `### 4.2 Create Archive Index` to `### 4.6 Create Archive Index`

## Phase 6 Fixes

**Before line 327** (`### 6.1 Identify Duplicates`), add:

```markdown
### 6.0 Prerequisite: Audit All Consumers of Tool Scripts

**CRITICAL:** Before moving any scripts, audit all consumers (mirror Phase 2.0):

**Action:** Create `tools/maintenance/audit_tool_script_consumers.py` that:
- Searches all `.bat` files for references to `analyze_*.py`, `fix_*.py`, `debug_*.py` scripts
- Searches all `.py` files for imports of these modules
- Searches all `.md` files for references to these scripts
- Searches CI/CD configs (`.yml`, `.yaml`, `.github/workflows/`) for references
- Generates `docs/maintenance/TOOL_SCRIPT_CONSUMERS_AUDIT.md` listing:
  - File path
  - Line number
  - Type of reference (batch call, import, documentation link)
  - Required update action

**Action:** Update rollback procedure in `docs/maintenance/ROLLBACK_PROCEDURE.md` (add tool script section if already exists).

```

**After line 346** (after `- `debug_*.py` scripts → move to `scripts/diagnostics/``), add:

```markdown
**Decision criteria:**
- Scripts already in `tools/` → keep there
- Diagnostic/analysis scripts → `scripts/diagnostics/`
- Maintenance/fix scripts → `scripts/maintenance/`
- Utility scripts → `scripts/utilities/` or keep in `tools/`

### 6.3 Update All References to Tool Scripts

**Action:** Based on audit results from Phase 6.0:
- Update all `.bat` files with new paths to moved scripts
- Update any Python imports (if any found)
- Update documentation links
- Update CI/CD workflows if applicable

**Action:** Verify all batch files still work after updates:
- Test each `.bat` file that references moved scripts
- Document any failures in `docs/maintenance/DECLUTTERING_LOG.md`

**Action:** Add README in `scripts/diagnostics/` and `scripts/maintenance/` explaining:
- Original locations
- Migration date
- How to run scripts from new location
```

## Implementation Order Fix

**Replace lines 392-401** with:

```markdown
## Implementation Order

1. **Phase 1** - Create inventory and structure (foundation)
2. **Phase 2** - Move diagnostic scripts (low risk, high impact) - includes audit prerequisite
3. **Phase 4** - Archive documentation (low risk, high impact) - includes link audit prerequisite
4. **Phase 3** - Consolidate tests (medium risk, review needed) - includes pytest validation
5. **Phase 5** - Clean backups (low risk, quick win)
6. **Phase 6** - Consolidate duplicates (medium risk, review needed) - includes audit prerequisite
7. **Phase 7** - Create maintenance docs (guidelines) - **AFTER structure is finalized**
8. **Phase 8** - Remove obsolete files (high risk, careful review)
```

