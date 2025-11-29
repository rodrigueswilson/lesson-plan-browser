# JSON Storage Implementation Tests

## Overview

This test suite validates the implementation of Option 3: saving JSON files to disk AND storing `lesson_json` in the database.

## Test Coverage

### 1. Database Schema Tests (`TestDatabaseSchema`)
- ✅ `lesson_json` column exists in `weekly_plans` table
- ✅ `consolidated` column exists
- ✅ `total_slots` column exists

### 2. Database Storage Tests (`TestDatabaseStorage`)
- ✅ Create weekly plan with `lesson_json`
- ✅ Update weekly plan with `lesson_json`
- ✅ Automatic JSON parsing when retrieving plans
- ✅ Multiple plans with JSON parsing
- ✅ `lesson_json` can be None (backward compatibility)
- ✅ Large `lesson_json` storage (5 days, 3 slots each)

### 3. JSON File Saving Tests (`TestJSONFileSaving`)
- ✅ JSON file created alongside DOCX file
- ✅ JSON file has correct format (indented, UTF-8)

### 4. Objectives Printer Integration Tests (`TestObjectivesPrinterIntegration`)
- ✅ Extract objectives from database-stored JSON
- ✅ Generate objectives DOCX from database JSON

### 5. Backward Compatibility Tests (`TestBackwardCompatibility`)
- ✅ Existing plans without `lesson_json` still work
- ✅ Can update existing plans to include `lesson_json`

### 6. Edge Cases Tests (`TestEdgeCases`)
- ✅ Invalid JSON handling (graceful degradation)
- ✅ Empty `lesson_json` handling
- ✅ Unicode characters in `lesson_json`

## Running the Tests

```bash
# Run all tests
python -m pytest tests/test_json_storage_implementation.py -v

# Run specific test class
python -m pytest tests/test_json_storage_implementation.py::TestDatabaseStorage -v

# Run specific test
python -m pytest tests/test_json_storage_implementation.py::TestDatabaseStorage::test_create_weekly_plan_with_lesson_json -v
```

## Test Results

**All 18 tests pass** ✅

```
======================== 18 passed, 1 warning in 0.98s =======================
```

## What Gets Tested

### Database Operations
1. **Schema Migration**: Verifies that `lesson_json` column is added to existing databases
2. **Storage**: Tests saving `lesson_json` as JSON string in database
3. **Retrieval**: Tests automatic parsing of JSON string back to Python dict
4. **Updates**: Tests updating existing plans with `lesson_json`

### File Operations
1. **JSON File Creation**: Verifies JSON files are created alongside DOCX files
2. **File Format**: Ensures proper indentation and UTF-8 encoding

### Integration
1. **Objectives Printer**: Tests that stored JSON can be used to generate objectives DOCX
2. **End-to-End**: Full workflow from database storage to DOCX generation

### Compatibility
1. **Backward Compatibility**: Existing plans without `lesson_json` continue to work
2. **Migration Path**: Can add `lesson_json` to existing plans

## Key Test Scenarios

### Scenario 1: New Plan with JSON
```python
# Create plan with lesson_json
plan_id = db.create_weekly_plan(..., lesson_json=sample_json)

# Retrieve and verify
plan = db.get_weekly_plan(plan_id)
assert plan['lesson_json'] == sample_json  # Automatically parsed
```

### Scenario 2: Update Existing Plan
```python
# Create plan without JSON
plan_id = db.create_weekly_plan(...)

# Update with JSON
db.update_weekly_plan(plan_id, lesson_json=sample_json)

# Verify
plan = db.get_weekly_plan(plan_id)
assert plan['lesson_json'] == sample_json
```

### Scenario 3: Generate Objectives from Database
```python
# Get plan from database
plan = db.get_weekly_plan(plan_id)
lesson_json = plan['lesson_json']

# Generate objectives DOCX
printer = ObjectivesPrinter()
printer.generate_docx(lesson_json, output_path, ...)
```

## Edge Cases Covered

1. **Empty JSON**: Empty dict `{}` handling
2. **None JSON**: Plans without `lesson_json` (backward compatibility)
3. **Invalid JSON**: Corrupted JSON strings (graceful error handling)
4. **Unicode**: Non-ASCII characters (UTF-8 encoding)
5. **Large JSON**: Multiple days and slots (performance)

## Notes

- Tests use temporary databases (cleaned up after each test)
- Tests use temporary file paths (no real files created)
- All tests are isolated (no dependencies between tests)
- Tests cover both single-slot and multi-slot scenarios

## Future Test Additions

When implementing the sync architecture, consider adding:
- P2P sync tests (JSON transfer between devices)
- Supabase sync tests (cloud backup/restore)
- Conflict resolution tests (concurrent edits)
- Performance tests (large JSON files, many plans)

