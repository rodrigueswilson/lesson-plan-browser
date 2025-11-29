# Tools Directory

**Purpose:** Organized collection of diagnostic, maintenance, and utility scripts  
**Last Updated:** 2025-01-27  
**Status:** Active

---

## Directory Structure

```
tools/
├── diagnostics/        # Diagnostic, analysis, and debugging scripts
├── maintenance/        # Maintenance, fix, and verification scripts
├── utilities/          # General utility scripts
└── archive/            # Obsolete scripts (retained for history)
```

---

## Quick Reference

### Diagnostic Scripts (`tools/diagnostics/`)

**Purpose:** Troubleshooting, analysis, and debugging

**Common Scripts:**
- `check_config.py` - Check application configuration
- `analyze_input_hyperlinks.py` - Analyze input hyperlinks
- `debug_extraction.py` - Debug extraction process
- `diagnose_crash.py` - Diagnose crashes

**See:** [`tools/diagnostics/README.md`](diagnostics/README.md) for complete list

---

### Maintenance Scripts (`tools/maintenance/`)

**Purpose:** Ongoing maintenance, fixes, and verification

**Common Scripts:**
- `verify_config.py` - Verify configuration
- `fix_daniela_file_patterns.py` - Fix file patterns
- `cleanup_users.py` - Clean up users
- `metadata_audit.py` - Audit metadata

**See:** [`tools/maintenance/README.md`](maintenance/README.md) for complete list

---

### Utility Scripts (`tools/utilities/`)

**Purpose:** General-purpose utilities

**Common Scripts:**
- `generate_demo_data.py` - Generate demo data
- `list_daniela_files.py` - List files
- `query_metrics.py` - Query metrics

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

## Core Application Tools

### Document Processing (`tools/` root)

**Core Application Scripts** (not tools, part of application):

- `docx_parser.py` - DOCX parsing engine
- `docx_renderer.py` - DOCX rendering engine
- `batch_processor.py` - Batch processing pipeline
- `json_merger.py` - JSON merging logic
- `table_structure.py` - Table structure detection

These are core application components, not standalone tools.

---

## Organization Guidelines

### Where to Put New Scripts

**Diagnostic Scripts** → `tools/diagnostics/`
- Analysis (`analyze_*.py`)
- Debugging (`debug_*.py`)
- Diagnostics (`diagnose_*.py`, `check_*.py`)

**Maintenance Scripts** → `tools/maintenance/`
- Fixes (`fix_*.py`)
- Cleanup (`cleanup_*.py`, `clear_*.py`)
- Configuration (`configure_*.py`)
- Audits (`*_audit.py`)
- Verification (`verify_*.py`, `validate_*.py`)

**Utility Scripts** → `tools/utilities/`
- Generation (`generate_*.py`)
- Lists (`list_*.py`)
- Queries (`query_*.py`)
- Test utilities (`test_*.py` - non-test files)

**Obsolete Scripts** → `tools/diagnostics/archive/`
- Scripts no longer used but retained for reference

### See Also

- [`docs/maintenance/SCRIPT_ORGANIZATION.md`](../docs/maintenance/SCRIPT_ORGANIZATION.md) - Detailed organization guide
- [`tools/diagnostics/README.md`](diagnostics/README.md) - Diagnostic scripts
- [`tools/maintenance/README.md`](maintenance/README.md) - Maintenance scripts

---

## Adding New Tools

### Checklist

When adding a new script:

1. **Choose the right directory** based on purpose (see above)
2. **Use appropriate naming** following conventions
3. **Ensure it runs from project root** (don't hardcode paths)
4. **Update README** in the appropriate directory
5. **Document usage** in script comments

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

See [`docs/maintenance/DECLUTTERING_LOG.md`](../docs/maintenance/DECLUTTERING_LOG.md) for full migration history.

---

## Dependencies

Tools may require:
- Python 3.8+
- python-docx
- docxcompose
- Other packages as specified in tool docstrings

Install dependencies:
```bash
pip install python-docx docxcompose
```

Or use the project virtual environment:
```bash
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
```

---

## Related Documentation

- **[Script Organization Guide](../docs/maintenance/SCRIPT_ORGANIZATION.md)** - Detailed organization guidelines
- **[Architecture](../docs/architecture_001.md)** - System design
- **[App Overview](../docs/app_overview.md)** - Document processing pipeline
- **[Tech Stack ADR](../docs/decisions/ADR-001-tech-stack.md)** - Technology decisions

---

**Last Updated:** 2025-01-27  
**Maintained By:** Development Team

