# Session 7: Backend Crash Diagnosis

## Current Status
**Backend crashes during lesson plan processing** - Need error logs to identify root cause.

## Diagnostic Tools Created

### 1. `verify_config.py` - Quick Configuration Check
**Purpose**: Verify basic configuration before starting backend
**Checks**:
- `.env` file exists
- Settings load correctly
- Database path is valid
- Template file exists
- API key is configured
- Critical directories exist

**Usage**:
```bash
python verify_config.py
```

### 2. `diagnose_crash.py` - Comprehensive Diagnostics
**Purpose**: Test all backend components for initialization errors
**Tests**:
1. Python environment
2. Critical imports (FastAPI, Uvicorn, python-docx)
3. Backend module imports (config, database, llm_service)
4. Database initialization and connection
5. Template file validation
6. API module loading
7. Batch processor import
8. DOCX tools import

**Usage**:
```bash
python diagnose_crash.py
```

### 3. `start-with-diagnostics.bat` - Safe Startup
**Purpose**: Run diagnostics before starting backend
**Steps**:
1. Verify configuration
2. Run full diagnostics
3. Start backend with visible logs

**Usage**:
```bash
start-with-diagnostics.bat
```

## Known Configuration Issue

**Database Filename Mismatch**:
- `.env.example` uses: `lesson_plans.db` (plural)
- `config.py` default uses: `lesson_planner.db` (singular)

**Fix**: Ensure your `.env` file uses:
```env
DATABASE_URL=sqlite:///./data/lesson_planner.db
```

## Next Steps

### Option A: Run Diagnostics First (Recommended)
```bash
# Run this to catch errors before starting
start-with-diagnostics.bat
```

This will:
1. Verify configuration
2. Test all imports
3. Start backend with visible logs
4. Show exact error if crash occurs

### Option B: Use Existing start-app.bat
```bash
# Your existing startup script
start-app.bat
```

Then **watch the "Backend API" terminal window** for error messages.

### After Backend Starts
1. Open frontend (Tauri window)
2. Select a user
3. Configure a class slot
4. Click "Process Week"
5. **Watch the Backend API terminal** for errors

## What to Look For

### Python Stack Trace
```
Traceback (most recent call last):
  File "...", line X, in <function>
    <code>
ErrorType: Error message here
```

### Common Error Types
- `ModuleNotFoundError` - Missing dependency
- `FileNotFoundError` - Missing file (template, schema, etc.)
- `sqlite3.OperationalError` - Database issue
- `ValidationError` - JSON schema issue
- `AuthenticationError` - API key issue
- `KeyError` / `AttributeError` - Code bug

## Files Created

1. **`verify_config.py`** (150 lines)
   - Quick configuration validation
   - Creates missing directories
   - Shows configuration summary

2. **`diagnose_crash.py`** (200 lines)
   - Comprehensive component testing
   - Detailed error reporting
   - Exit codes for automation

3. **`start-with-diagnostics.bat`** (40 lines)
   - Safe startup with pre-flight checks
   - Visible error messages
   - Keeps terminal open

4. **`BACKEND_CRASH_DIAGNOSIS.md`** (Documentation)
   - Diagnostic steps
   - Common crash causes
   - Quick fixes
   - What to share for debugging

## Expected Outcomes

### If Diagnostics Pass
Backend should start successfully. If it still crashes during processing, we'll see the exact error in the terminal.

### If Diagnostics Fail
You'll see exactly which component is broken:
- Import error → Missing dependency
- Database error → Path or permission issue
- Template error → Missing file
- Config error → Invalid `.env` settings

## Debugging Workflow

```
1. Run verify_config.py
   └─ PASS → Continue
   └─ FAIL → Fix configuration issues

2. Run diagnose_crash.py
   └─ PASS → Continue
   └─ FAIL → Fix import/initialization issues

3. Start backend (start-with-diagnostics.bat)
   └─ Starts OK → Continue
   └─ Crashes → Check terminal for error

4. Process lesson plan from frontend
   └─ Works → Success!
   └─ Crashes → Share stack trace
```

## Why Backend Might Crash

### During Startup
- Missing dependencies
- Invalid configuration
- Database initialization failure
- Import errors

### During Processing
- LLM API errors
- JSON validation errors
- DOCX rendering errors
- Memory issues
- File I/O errors

## Quick Fixes Reference

### Fix 1: Missing Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Fix 2: Database Path
```bash
# Ensure data folder exists
mkdir data

# Check database
python check_db_url.py
```

### Fix 3: Clear Cache
```bash
# Delete Python cache
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"
```

### Fix 4: Template File
```bash
# Verify template exists
dir "input\Lesson Plan Template SY'25-26.docx"
```

## Success Criteria

✅ `verify_config.py` passes all checks
✅ `diagnose_crash.py` completes without errors
✅ Backend starts and shows "Application startup complete"
✅ Frontend connects to backend
✅ Lesson plan processing completes without crash

## Current Blocker

**Need visible error logs** to identify crash cause. The diagnostic tools will provide this.

---

**Status**: Diagnostic tools ready
**Next Action**: Run `start-with-diagnostics.bat` and share any error messages
**Estimated Time**: 5-10 minutes to identify issue, 10-30 minutes to fix (depends on root cause)
