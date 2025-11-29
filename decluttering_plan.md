<!-- 0b5f0f02-a1e3-4ffe-8716-0f3046613921 71e23662-04fb-40c1-9761-98335f753b19 -->
# Codebase Decluttering Plan

## Overview

The codebase has accumulated significant clutter over time:

- 46+ diagnostic scripts (`check_*.py`) at root level
- 100+ test files scattered between root and `tests/` folder
- 50+ completed documentation files (`*_COMPLETE.md`)
- 53+ session summary files (`SESSION_*.md`)
- 30+ fix/analysis documents (`*_FIX*.md`, `*_ANALYSIS*.md`)
- Backup files and temporary artifacts

This plan establishes a systematic decluttering process organized by priority and risk level.

## Phase 1: Analysis & Documentation (Low Risk)

### 1.1 Pilot Inventory & Scope Automation

**Action:** Run a manual pilot inventory across a representative slice of the root (e.g., diagnostics scripts, legacy docs, tests). Document the judgment calls, open questions, and decision criteria in `docs/maintenance/DECLUTTERING_INVENTORY_NOTES.md`.

**Follow-up Automation:** After the pilot, create a lightweight `tools/maintenance/generate_inventory.py` script that emits **only** raw counts and file paths for each category (e.g., `check_*.py`, `test_*.py`, `*_COMPLETE.md`). Humans remain responsible for interpreting the output and updating `docs/maintenance/DECLUTTERING_INVENTORY.md` with keep/archive/delete decisions.

**Why:** Preserves YAGNI by building automation around verified needs, keeps human context in the loop, and still allows the inventory to be regenerated after each phase.

### 1.2 Establish Organizational Structure

**Action:** Extend the existing `tools/` hierarchy instead of creating a competing top-level tree. Create subdirectories:

```
tools/
  ├── diagnostics/        # One-time diagnostic scripts migrated from root
  │   └── archive/        # Obsolete diagnostic scripts (retained for history)
  ├── maintenance/        # Ongoing maintenance utilities (inventory, audits)
  └── utilities/          # Reusable helper modules leveraged across tools

docs/
  ├── archive/            # Completed/obsolete documentation
  │   ├── sessions/       # Session summaries
  │   ├── fixes/          # Fix documentation
  │   ├── implementations/ # Completed implementation docs
  │   └── analysis/       # Analysis documents
  └── maintenance/        # Maintenance documentation
```

**Action:** Seed `docs/maintenance/DECLUTTERING_LOG.md` with a defined schema (Date, Author, Item, Action, Verification) and assign provisional phase owners so updates remain actionable rather than aspirational.

## Phase 2: Move Diagnostic Scripts (Low Risk, but requires audit)

### 2.0 Prerequisite: Audit All Consumers

**CRITICAL:** Before moving any scripts, audit all consumers using thin wrappers around proven tools (no bespoke scanners unless a gap is found):

**Action:** Document the exact commands in `docs/maintenance/SCRIPT_CONSUMERS_AUDIT.md`, for example:

- `rg "check_.*\.py" -n --hidden --glob "*.bat"`
- `rg "(check|analyze|fix|debug)_.*\.py" -n --glob "*.py"`
- `rg "(check|analyze|fix|debug)_.*\.py" -n --glob "*.md"`
- `rg "(check|analyze|fix|debug)_.*\.py" -n .github workflows`

Capture results (file, line, reference type, required action) directly in the audit doc. If repeatability is desired, add a lightweight wrapper script (e.g., `tools/maintenance/run_script_audits.ps1`) that executes the same commands.

**Action:** Manually review `.pre-commit-config.yaml` and any CI/CD workflows for script references.

**Action:** Create rollback procedure documented in `docs/maintenance/ROLLBACK_PROCEDURE.md` for emergency restoration.

### 2.1 Organize Check Scripts

**Action:** Move root-level `check_*.py` scripts to `tools/diagnostics/`

**Decision criteria:**

- If script is used regularly → move to `tools/diagnostics/` (create a lightweight wrapper `.bat` or helper in the root if legacy workflows expect the original path)
  - **Wrapper example:** Create `check_config.bat` in root that calls `python tools/diagnostics/check_config.py %*`
- If script provides reusable helpers for other scripts → move to `tools/utilities/`
- If script was one-time diagnostic → move to `tools/diagnostics/`
- If script is obsolete → move to `tools/diagnostics/archive/`

**Files to move:**

- `check_*.py` (46 files) → `tools/diagnostics/`

### 2.2 Update All References

**Action:** Based on audit results from Phase 2.0:

- Update all `.bat` files with new paths to `tools/diagnostics/check_*.py`
- Update any Python imports (if any found)
- Update documentation links
- Update CI/CD workflows if applicable
- Update `.pre-commit-config.yaml` if needed (e.g., `tools/check_snapshot_updates.py` is already in tools/)

**Action:** Add README in `tools/diagnostics/` explaining:

- Original locations
- Migration date
- How to run scripts from new location

**Action:** Verify all batch files still work after updates:

- Test each `.bat` file that references moved scripts
- Document any failures in `docs/maintenance/DECLUTTERING_LOG.md`

## Phase 3: Consolidate Test Files (Medium Risk, requires pytest validation)

### 3.0 Prerequisite: Validate Test Configuration

**CRITICAL:** Before moving tests, ensure pytest configuration supports new structure:

**Action:** Document repeatable checks (no bespoke tooling unless gaps emerge) in `docs/maintenance/TEST_MIGRATION_REQUIREMENTS.md`, including:

- Inspect existing config files (`pytest.ini`, `pyproject.toml`, `setup.cfg`) for discovery/path settings.
- Run command aliases, e.g.:
  - `rg "from \.\." test_*.py` (identify relative imports that need adjusting)
  - `rg "from tools" test_*.py` (flag absolute imports)
  - `rg "import .*helpers" test_*.py` (catch helper dependencies)
- Summarise required pytest configuration changes, import fixes, and PYTHONPATH adjustments.

**Action:** Create `pytest.ini` or update existing config to:

- Set `pythonpath = .` (if tests import from root)
- Configure test discovery for `tests/` directory
- Set any required markers or options

**Action:** Run test suite in dry-run mode from root:

```bash
pytest --collect-only --quiet
```

- Verify all tests are discovered
- Document any missing tests
- Verify coverage parity before moving

### 3.1 Move Root-Level Tests to `tests/`

**Action:** Move all `test_*.py` files from root to `tests/`

**Exception:** Keep root-level tests only if they:

- Are integration tests that need to run from root
- Have special path dependencies that can't be resolved

**Files to move:**

- All `test_*.py` files from root → `tests/`

**Action:** Review for duplicates:

- If `test_X.py` exists in both root and `tests/`, compare and consolidate
- Keep the more complete version

### 3.2 Fix Imports and Paths

**Action:** Based on Phase 3.0 analysis:

- Update all relative imports in moved test files
- Fix absolute imports to work from `tests/` directory
- Ensure helper modules are importable (may need `__init__.py` or PYTHONPATH)
- Update any batch files that call test scripts (e.g., `test_fresh.bat`)

**Action:** Verify test suite runs successfully:

```bash
pytest tests/ -v
```

- Document any failures
- Fix import/path issues before proceeding

**Checkpoint:** Confirm `pytest --collect-only --quiet` (from repository root) and the targeted test runs succeed before beginning Phase 4 archiving work.

### 3.3 Organize Tests by Category

**Action:** Within `tests/`, create subdirectories:

```
tests/
  ├── unit/              # Unit tests
  ├── integration/       # Integration tests
  ├── e2e/               # End-to-end tests
  └── fixtures/          # Already exists
```

**Action:** Move tests to appropriate subdirectories based on test type (manual review required).

## Phase 4: Archive Documentation (Low Risk)

### 4.1 Distinguish Feature Documentation vs Planning/Implementation Docs

**Critical Distinction:**

- **Feature Documentation** = Active references explaining HOW the system works, HOW to use features, WHAT features exist. These should STAY ACTIVE.
- **Planning/Implementation Docs** = Historical records of WHAT was planned, WHAT was done in sessions, HOW bugs were fixed. These can be ARCHIVED.

**Decision Criteria:**

- If doc answers "How do I use X?" → Feature doc (keep active)
- If doc answers "How does X work?" → Feature doc (keep active)
- If doc answers "What features exist?" → Feature doc (keep active)
- If doc answers "What was planned/done in session Y?" → Planning doc (archive)

### 4.2 Prerequisite: Audit All Links to Documentation

**CRITICAL:** Before archiving any docs, audit all inbound links:

**Action:** Use standard tooling to map inbound links before any move. Capture the exact commands and their output in `docs/maintenance/DOC_LINK_AUDIT.md`, for example:

- `rg "\[[^\]]+\]\(([^)]+)\)" docs -n --glob "*.md"`
- `rg "\[[^\]]+\]\(([^)]+)\)" README.md -n`

Summarize results in a table listing source file, line number, link target, and the required action (update path, create redirect stub, remove link). If repeatability is desired, add a thin wrapper script (PowerShell or Python) that simply runs the documented commands.

**Action:** Use `markdown-link-check` (or wrapper) to validate all links:
```bash
# Install: npm install -g markdown-link-check
# Windows (PowerShell): Get-ChildItem -Path docs -Recurse -Filter *.md | ForEach-Object { markdown-link-check $_.FullName }
# Unix/Linux: find docs -name "*.md" -exec markdown-link-check {} \;
# Optional wrapper: python tools/maintenance/run_markdown_link_check.py
```

### 4.3 Preserve Active Feature Documentation

**Action:** Keep these files active (do NOT archive):

**User Guides** (in `docs/guides/` or root):

- `QUICK_START_GUIDE.md` - How to use the system
- `USER_PROFILE_GUIDE.md` - How to configure users
- `USER_TRAINING_GUIDE.md` - Training materials
- `TESTING_GUIDE.md` - General testing procedures
- `TROUBLESHOOTING_QUICK_REFERENCE.md` - Troubleshooting guide

**Architecture & Reference Docs**:

- `ARCHITECTURE_MULTI_USER.md` - System architecture
- `DOCX_PARSER_GUIDE.md` - How parsing works
- `IMPLEMENTATION_STATUS.md` - Current feature status (ACTIVE, should be updated)
- `CONTRIBUTING.md` - Developer guidelines

### 4.4 Archive Planning/Implementation Documentation

**Action:** Move completed planning/implementation docs to `docs/archive/`

**Session summaries** → `docs/archive/sessions/`:

- `SESSION_*_COMPLETE.md` files - Historical records of sessions
- `SESSION_*_SUMMARY.md` files - Session summaries
- `SESSION_*_FINAL.md` files - Final session status
- `SESSION_*_TESTING_GUIDE.md` - Session-specific testing guides (e.g., `SESSION_7_TESTING_GUIDE.md`)
- `NEXT_SESSION_*.md` files - Planning for next sessions (if no longer active)

**Implementation plans** → `docs/archive/implementations/`:

- `*_PLAN*.md` files - Planning documents (e.g., `MULTISLOT_INLINE_HYPERLINKS_PLAN_V2.md`, `MULTISLOT_INLINE_HYPERLINKS_PLAN_V3.md`)
- `IMPLEMENTATION_PLAN_*.md` - Implementation planning docs
- `*_COMPLETE.md` - Implementation completion records (e.g., `HYPERLINK_FIX_COMPLETE.md`)
- `PHASE_*_COMPLETE.md` - Phase completion records
- `IMPLEMENTATION_COMPLETE.md` - Overall implementation completion

**Fix documentation** → `docs/archive/fixes/`:

- `*_FIX_COMPLETE.md` - Bug fix completion records
- `*_FIX_*.md` files - Fix documentation (e.g., `HYPERLINK_FIX_SOLUTION_PLAN.md`)
- `CRITICAL_*_FIX.md` files - Critical fix documentation
- `*_BUG_FIXED.md` files - Bug fix records
- `*_CRITICAL_FIXES*.md` - Critical fixes documentation

**Analysis documents** → `docs/archive/analysis/`:

- `*_ANALYSIS*.md` - Analysis documents (e.g., `HYPERLINK_ANALYSIS_FINDINGS.md`)
- `*_FINDINGS.md` - Research findings
- `*_DIAGNOSIS.md` - Diagnostic reports

**Exception Handling:**

- `END_TO_END_TESTING_GUIDE.md` - Review: If it's general testing guide → keep active in `docs/guides/`. If session-specific → archive.
- Latest plan versions: Keep latest version active if still being implemented (e.g., keep `MULTISLOT_INLINE_HYPERLINKS_PLAN_V3.md` if still in progress)

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

**Action:** Verify all links after updates (Windows-compatible):

```bash
# Windows (PowerShell):
Get-ChildItem -Path docs -Recurse -Filter *.md | ForEach-Object { markdown-link-check $_.FullName }

# Unix/Linux:
find docs -name "*.md" -exec markdown-link-check {} \;

# Python wrapper (cross-platform):
python tools/maintenance/check_markdown_links.py
```

- Document any remaining broken links that require manual review

### 4.6 Create Archive Index

**Action:** Create `docs/archive/README.md` with:

- Index of archived files by category
- Dates archived
- Brief descriptions
- Links to active documentation if relevant

## Phase 5: Clean Up Backup Files (Low Risk)

### 5.1 Review Backup Files

**Files found:**

- `frontend/src/components/UserSelector.tsx.backup`
- `frontend/src/lib/api.ts.backup`
- `data/lesson_planner.db.backup`

**Action:** Apply triage criteria before making any move. Record the outcome in `docs/maintenance/BACKUP_FILES.md` with: Purpose, Last Verified Restore, Age, Recommended Action. Only archive or delete once a newer, verified restore point exists and ownership for the replacement backup is documented.

### 5.2 Remove Backup Files (After Review)

**Action:** After confirming not needed:

- Delete `.backup` files or move to `deprecated/backups/`
- Document removal in `docs/maintenance/DECLUTTERING_LOG.md`

## Phase 6: Consolidate Duplicate Files (Medium Risk)

### 6.0 Prerequisite: Reuse Phase 2.0 Audit Results

**CRITICAL:** Phase 2.0 audit already covers all script patterns (`check_*.py`, `analyze_*.py`, `fix_*.py`, `debug_*.py`).

**Action:** Review `docs/maintenance/SCRIPT_CONSUMERS_AUDIT.md` from Phase 2.0:

- Filter for references to `analyze_*.py`, `fix_*.py`, `debug_*.py` scripts
- Create `docs/maintenance/TOOL_SCRIPT_CONSUMERS_AUDIT.md` subset if needed for tracking Phase 6 updates
- If Phase 2.0 audit was not run, run it now with all script patterns before proceeding

**Action:** Update rollback procedure in `docs/maintenance/ROLLBACK_PROCEDURE.md` (add tool script section if already exists).

### 6.1 Identify Duplicates

**Action:** Search for duplicate patterns:

- Same file in multiple locations
- Multiple versions of same concept (`*_PLAN_V2.md`, `*_PLAN_V3.md`)
- Superseded files (already have `deprecated/` folder)

**Known duplicates:**

- Plan files: `MULTISLOT_INLINE_HYPERLINKS_PLAN_V2.md`, `MULTISLOT_INLINE_HYPERLINKS_PLAN_V3.md`
  - Keep only latest version (V3), move others to `docs/archive/implementations/`

### 6.2 Consolidate Tool Scripts

**Action:** Review root-level Python scripts that should be in `tools/`:

- `analyze_*.py` scripts → move to `tools/diagnostics/`
- `fix_*.py` scripts → move to `tools/maintenance/`
- `debug_*.py` scripts → move to `tools/diagnostics/`

**Decision criteria:**

- Scripts already in `tools/` → keep there
- Diagnostic/analysis scripts → `tools/diagnostics/`
- Maintenance/fix scripts → `tools/maintenance/`
- Utility scripts → `tools/utilities/` or keep in `tools/`

### 6.3 Update All References to Tool Scripts

**Action:** Based on audit results from Phase 2.0 (filtered for tool scripts) or Phase 6.0:

- Update all `.bat` files with new paths to moved scripts
- Update any Python imports (if any found)
- Update documentation links
- Update CI/CD workflows if applicable

**Action:** Verify all batch files still work after updates:

- Test each `.bat` file that references moved scripts
- Document any failures in `docs/maintenance/DECLUTTERING_LOG.md`

**Action:** Add README files in `tools/diagnostics/` and `tools/maintenance/` explaining:

- Original locations
- Migration date
- How to run scripts from new location

## Phase 7: Create Maintenance Documentation (Low Risk)

### 7.1 Create Maintenance Guides

**Files to create:**

**`docs/maintenance/DECLUTTERING_LOG.md`**

- Track all moves/deletions
- Columns: Date, Author, Item, Action, Verification/Link
- Assign an explicit owner for each phase (e.g., Phase 2 lead updates after script moves) and add the cadence to the relevant phase checklist so entries stay current.

**`docs/maintenance/SCRIPT_ORGANIZATION.md`**

- Explain folder structure
- Where to put new tools
- When to archive vs delete

**`tools/README.md`**

- Overview of tool organization
- Quick reference for common utilities and diagnostics

**`docs/archive/README.md`**

- Index of archived documentation
- How to find archived files

## Phase 8: Clean Up Obsolete Files (High Risk - Requires Review)

### 8.1 Identify Obsolete Files

**Action:** Review files that appear obsolete:

- Temporary files (`.tmp`, `.temp`)
- Old log files (if not in `.gitignore`)
- Generated files that shouldn't be committed

### 8.2 Remove Obsolete Files

**Action:** Only after careful review:

- Delete truly obsolete files
- Document deletions in `docs/maintenance/DECLUTTERING_LOG.md`

## Implementation Order

1. **Phase 1** - Create inventory and structure (foundation)
2. **Phase 2** - Move diagnostic scripts (low risk, high impact)
3. **Phase 3** - Consolidate tests (medium risk, review needed)
4. **Phase 4** - Archive documentation (low risk, high impact)
5. **Phase 5** - Clean backups (low risk, quick win)
6. **Phase 6** - Consolidate duplicates (medium risk, review needed)
7. **Phase 7** - Create maintenance docs (guidelines) – after structure is finalized
8. **Phase 8** - Remove obsolete files (high risk, careful review)

**Checkpoint:** Do not begin Phase 4 until the Phase 3 prerequisites are complete and `pytest --collect-only --quiet` passes from the repository root after the test moves.

## Safety Measures

1. **Backup before moving:** Create git commit before major moves
2. **Verify imports:** Check for broken imports after moves
3. **Test suite:** Run tests after test file consolidation
4. **Incremental:** Process one phase at a time, verify before proceeding
5. **Documentation:** Keep detailed log of all changes

## Expected Outcomes

- **Reduced root clutter:** ~200 files moved from root
- **Clear organization:** Scripts and docs in logical folders
- **Better discoverability:** Easier to find active vs archived files
- **Maintained history:** Archive preserves context without cluttering active workspace
- **Easier maintenance:** Clear patterns for future additions

## Files to Modify/Create

**New directories:**

- `tools/diagnostics/`
- `tools/maintenance/`
- `tools/utilities/`
- `docs/archive/sessions/`
- `docs/archive/fixes/`
- `docs/archive/implementations/`
- `docs/archive/analysis/`
- `docs/maintenance/`

**New files:**

- `docs/maintenance/DECLUTTERING_INVENTORY.md`
- `docs/maintenance/DECLUTTERING_INVENTORY_NOTES.md`
- `docs/maintenance/DECLUTTERING_LOG.md`
- `docs/maintenance/SCRIPT_ORGANIZATION.md`
- `tools/README.md`
- `docs/archive/README.md`

**Files to move:** ~200+ files total across all phases

### To-dos

- [ ] Run manual pilot inventory and capture findings in `docs/maintenance/DECLUTTERING_INVENTORY_NOTES.md`
- [ ] Create decluttering inventory document cataloging all files to organize
- [ ] Create folder structure for tools and archived documentation
- [ ] Create maintenance documentation (decluttering log, script organization guide, archive index)
- [ ] Move diagnostic `check_*.py` scripts from root to `tools/diagnostics/`
- [ ] Archive completed documentation (sessions, fixes, implementations) to `docs/archive/`
- [ ] Move root-level `test_*.py` files to `tests/` folder and organize by category
- [ ] Review and organize backup files (`.backup` extensions)
- [ ] Identify and consolidate duplicate files (plan versions, etc.)
- [ ] Review and remove obsolete files (temporary files, old logs)

