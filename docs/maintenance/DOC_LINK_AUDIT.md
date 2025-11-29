# Documentation Link Audit

This document tracks all inbound links to documentation files before archiving.

## Audit Commands

Run these commands to identify links:

### PowerShell Commands (Windows)

```powershell
# Find all markdown links in root and docs directories
Get-ChildItem -Path . -Include *.md -Recurse -Exclude node_modules | Select-String -Pattern '\[([^\]]+)\]\(([^)]+)\)' | Format-Table Path,LineNumber,Line

# Check for links to SESSION_*.md files
Get-ChildItem -Path . -Include *.md -Recurse -Exclude node_modules | Select-String -Pattern 'SESSION_[^)]+\.md' | Format-Table Path,LineNumber,Line

# Check for links to *_COMPLETE.md files
Get-ChildItem -Path . -Include *.md -Recurse -Exclude node_modules | Select-String -Pattern '[^/]_COMPLETE\.md' | Format-Table Path,LineNumber,Line

# Check for links to *_PLAN*.md files
Get-ChildItem -Path . -Include *.md -Recurse -Exclude node_modules | Select-String -Pattern '[^/]_PLAN[^)]*\.md' | Format-Table Path,LineNumber,Line

# Check for links to *_FIX*.md files
Get-ChildItem -Path . -Include *.md -Recurse -Exclude node_modules | Select-String -Pattern '[^/]_FIX[^)]*\.md' | Format-Table Path,LineNumber,Line
```

## Files to Archive

### Session Summaries (→ `docs/archive/sessions/`)
- Root-level `SESSION_*.md` files (53 files found)
- `NEXT_SESSION_*.md` files (20 files found)

### Implementation Plans (→ `docs/archive/implementations/`)
- `*_PLAN*.md` files (28 files found)
- `*_COMPLETE.md` files (50 files found - exclude active docs)

### Fix Documentation (→ `docs/archive/fixes/`)
- `*_FIX*.md` files (41 files found)
- `CRITICAL_*_FIX.md` files
- `*_BUG_FIXED.md` files

### Analysis Documents (→ `docs/archive/analysis/`)
- `*_ANALYSIS*.md` files (12 files found)
- `*_FINDINGS.md` files (1 file found)
- `*_DIAGNOSIS.md` files (4 files found)

## Link Audit Results

### Links Found (to be populated)

| Source File | Line Number | Link Target | Required Action |
|------------|-------------|-------------|----------------|
| | | | |

## Next Steps

1. Run audit commands above
2. Populate link audit results table
3. Update all links to point to new archive locations
4. Create redirect stubs for frequently-referenced files
5. Verify all links after updates

