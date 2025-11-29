# Script Organization Guide

**Purpose:** Guidelines for organizing scripts and tools in the codebase  
**Last Updated:** 2025-01-27  
**Status:** Active

---

## Folder Structure

```
tools/
├── diagnostics/        # Diagnostic, analysis, and debugging scripts
├── maintenance/        # Maintenance, fix, and verification scripts
├── utilities/          # General utility scripts
└── archive/            # Obsolete scripts (retained for history)
```

---

## Where to Put New Tools

### Diagnostic Scripts → `tools/diagnostics/`

**Use for:**
- Analysis scripts (`analyze_*.py`)
- Debugging scripts (`debug_*.py`)
- Diagnostic scripts (`diagnose_*.py`)
- Check scripts (`check_*.py`)
- One-time diagnostic tools

**Examples:**
- `analyze_input_hyperlinks.py`
- `debug_extraction.py`
- `check_config.py`

### Maintenance Scripts → `tools/maintenance/`

**Use for:**
- Fix scripts (`fix_*.py`)
- Cleanup scripts (`cleanup_*.py`, `clear_*.py`)
- Configuration scripts (`configure_*.py`)
- Audit scripts (`*_audit.py`)
- Verification scripts (`verify_*.py`)
- Validation scripts (`validate_*.py`)

**Examples:**
- `fix_daniela_file_patterns.py`
- `cleanup_users.py`
- `verify_config.py`
- `metadata_audit.py`

### Utility Scripts → `tools/utilities/`

**Use for:**
- Test utilities (`test_*.py` - non-test files)
- Generation scripts (`generate_*.py`)
- List utilities (`list_*.py`)
- Query utilities (`query_*.py`)
- Other general-purpose utilities

**Examples:**
- `generate_demo_data.py`
- `list_daniela_files.py`
- `query_metrics.py`

### Obsolete Scripts → `tools/diagnostics/archive/`

**Use for:**
- Scripts that are no longer used
- Scripts superseded by newer versions
- Historical scripts retained for reference

**Decision:** Archive rather than delete if:
- Script contains historical logic that might be referenced
- Script might be needed for rollback
- Script documents a specific approach or solution

---

## Decision Criteria

### When to Archive vs Delete

**Archive (move to `tools/diagnostics/archive/`):**
- Script contains historical logic or approaches
- Script documents a specific solution or fix
- Script might be needed for reference or rollback
- Script is obsolete but could inform future decisions

**Delete:**
- Script is completely superseded and not needed
- Script contains no historical value
- Script duplicates functionality available elsewhere
- Script is temporary and no longer needed

**Note:** When in doubt, **archive** rather than delete. Files can be deleted later if needed, but recovery is harder.

### When to Keep in Root

**Keep in root if:**
- Script is part of the core application (not a tool)
- Script is a primary entry point (e.g., `main.py`)
- Script is used by CI/CD or deployment
- Script is referenced in README as primary tool

**Examples of root-level scripts:**
- `main.py` - Application entry point
- Core application scripts (not tools)

---

## Script Naming Conventions

### Prefix Patterns

- `check_*.py` - Diagnostic/verification scripts → `tools/diagnostics/`
- `analyze_*.py` - Analysis scripts → `tools/diagnostics/`
- `debug_*.py` - Debugging scripts → `tools/diagnostics/`
- `diagnose_*.py` - Diagnostic scripts → `tools/diagnostics/`
- `fix_*.py` - Fix scripts → `tools/maintenance/`
- `cleanup_*.py` - Cleanup scripts → `tools/maintenance/`
- `clear_*.py` - Clear/cache scripts → `tools/maintenance/`
- `configure_*.py` - Configuration scripts → `tools/maintenance/`
- `*_audit.py` - Audit scripts → `tools/maintenance/`
- `verify_*.py` - Verification scripts → `tools/maintenance/`
- `validate_*.py` - Validation scripts → `tools/maintenance/`
- `generate_*.py` - Generation scripts → `tools/utilities/`
- `list_*.py` - List utilities → `tools/utilities/`
- `query_*.py` - Query utilities → `tools/utilities/`

### Naming Best Practices

- Use descriptive names that indicate purpose
- Use lowercase with underscores
- Include verb in name (check, analyze, fix, etc.)
- Be specific (e.g., `check_daniela_config.py` vs `check_config.py`)

---

## Running Scripts

### Important: Run from Project Root

**All scripts must be run from the project root directory** because they import from `backend`, `tools`, etc.

```bash
# Windows (PowerShell)
cd D:\LP
python tools\diagnostics\check_config.py
python tools\maintenance\verify_config.py

# Linux/Mac
cd /path/to/project
python tools/diagnostics/check_config.py
python tools/maintenance/verify_config.py
```

### PYTHONPATH

Scripts assume they're run from the project root where:
- `backend/` module is accessible
- `tools/` module is accessible
- Project imports work correctly

If you get `ModuleNotFoundError`, ensure you're in the project root directory.

---

## Adding New Scripts

### Checklist

When adding a new script:

1. **Choose the right directory** based on purpose (see above)
2. **Use appropriate naming** following conventions
3. **Ensure it runs from project root** (don't hardcode paths)
4. **Update README** in the appropriate directory if needed
5. **Document usage** in script comments or README

### Example

```python
#!/usr/bin/env python3
"""
Script to analyze hyperlink patterns.
Run from project root: python tools/diagnostics/analyze_hyperlinks.py
"""

import sys
from pathlib import Path

# Ensure running from project root
if not Path("backend").exists():
    print("Error: Must run from project root directory")
    sys.exit(1)

# Your script code here
```

---

## Migration History

Scripts were migrated from root directory in phases:
- **Phase 2:** `check_*.py` scripts → `tools/diagnostics/`
- **Phase 6:** `analyze_*.py`, `fix_*.py`, `debug_*.py` and other tool scripts → organized by purpose

See `docs/maintenance/DECLUTTERING_LOG.md` for full migration history.

---

## Maintenance

### Keeping Scripts Organized

- **Review periodically:** Check for scripts that should be moved or archived
- **Update READMEs:** Keep directory READMEs current as scripts are added
- **Archive obsolete:** Move unused scripts to archive rather than deleting
- **Document decisions:** Note in decluttering log when scripts are moved

### Questions?

- See `docs/maintenance/DECLUTTERING_LOG.md` for migration history
- See `tools/diagnostics/README.md` for diagnostic scripts
- See `tools/maintenance/README.md` for maintenance scripts
- See `tools/utilities/README.md` for utility scripts (if created)

---

**Last Updated:** 2025-01-27  
**Maintained By:** Development Team

