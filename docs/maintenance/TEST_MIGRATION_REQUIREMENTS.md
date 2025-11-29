# Test Migration Requirements

## Phase 3.0: Pytest Configuration Validation

### Current State

**Pytest Configuration:**
- pytest==7.4.3 installed in requirements.txt
- pytest-asyncio==0.21.1 for async tests
- No pytest.ini, pyproject.toml, or setup.cfg with pytest config
- Default pytest discovery will be used

**Test File Inventory:**
- Root level: 46 test_*.py files
- tests/ directory: 56 test_*.py files
- tools/ directory: 5 test_*.py files
- Total: 107 test files

**Import Patterns:**
- Tests use absolute imports: `from tools.*`, `from backend.*`
- No relative imports (`from ..`) found in root-level tests
- This means tests should work from any location

### Required Configuration

**Create pytest.ini:**
```ini
[pytest]
pythonpath = .
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

**Why:**
- `pythonpath = .` ensures imports from project root work
- `testpaths = tests` tells pytest where to discover tests
- Explicit patterns for clarity

### Pre-Migration Validation

**Commands to run:**

1. Test current discovery (from root):
```bash
pytest --collect-only --quiet
```

2. Check for relative imports in root tests:
```bash
rg "from \.\." test_*.py -l
```

3. Check for helper dependencies:
```bash
rg "import .*helpers" test_*.py
```

### Expected Results

- All tests should be discoverable
- No relative imports to fix
- Absolute imports should continue working after move

### Post-Migration Validation

After moving tests to tests/:

1. Verify all tests discovered:
```bash
pytest --collect-only --quiet
```

2. Run test suite:
```bash
pytest tests/ -v
```

3. Check for import errors and fix as needed

### Risk Assessment

**LOW RISK** because:
- Tests already use absolute imports
- No pytest.ini conflicts (none exists)
- tests/ directory already has working tests
- Can easily rollback by moving files back

### Rollback Procedure

If issues arise:
1. Move files back to root: `git checkout -- test_*.py`
2. Or manually move from tests/ back to root
3. Document issues in DECLUTTERING_LOG.md

## Validation Complete

Date: 2025-10-31
Status: READY TO PROCEED
Risk Level: LOW
