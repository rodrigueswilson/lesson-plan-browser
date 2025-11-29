# Backend Crash Diagnosis Guide

## Issue Summary
The backend crashes during lesson plan processing. We need to capture the actual error logs to identify the root cause.

## Database Configuration Issue Found

**CRITICAL**: There's a filename mismatch in database configuration:
- `.env.example` uses: `lesson_plans.db` (plural)
- `config.py` default uses: `lesson_planner.db` (singular)

This mismatch could cause database connection issues.

## Diagnostic Steps

### Step 1: Run Pre-Flight Diagnostic
```bash
cd D:\LP
python diagnose_crash.py
```

This will test:
1. Python environment
2. Critical imports (FastAPI, Uvicorn, python-docx)
3. Backend module imports
4. Database initialization
5. Template file existence
6. API module loading
7. Batch processor import
8. DOCX tools import

**If this fails**, the error will show exactly what's broken.

### Step 2: Check Your .env File
Open `D:\LP\.env` and verify:
```env
DATABASE_URL=sqlite:///./data/lesson_planner.db
```

**Note**: Use `lesson_planner.db` (singular) to match `config.py` default.

### Step 3: Start Backend with Visible Logs
Your `start-app.bat` already opens a visible terminal. Just run:
```bash
start-app.bat
```

**Watch the "Backend API" terminal window** for error messages.

### Step 4: Trigger the Crash
1. Open the frontend (Tauri window)
2. Select a user
3. Configure a class slot
4. Click "Process Week"
5. **Immediately check the Backend API terminal**

### Step 5: Capture the Error
Look for:
- Python stack traces (red text)
- `ERROR` or `CRITICAL` log messages
- Lines starting with `Traceback (most recent call last):`
- Module import failures
- Database connection errors

## Common Crash Causes

### 1. Database Path Issues
**Symptom**: `sqlite3.OperationalError` or `FileNotFoundError`
**Fix**: Ensure `.env` has correct path and `data/` folder exists

### 2. Missing Template File
**Symptom**: `FileNotFoundError: input/Lesson Plan Template SY'25-26.docx`
**Fix**: Verify template exists at exact path

### 3. Import Errors
**Symptom**: `ModuleNotFoundError` or `ImportError`
**Fix**: Reinstall dependencies: `pip install -r requirements.txt`

### 4. API Key Issues
**Symptom**: `AuthenticationError` or `Invalid API key`
**Fix**: Check `LLM_API_KEY` in `.env`

### 5. JSON Schema Errors
**Symptom**: `ValidationError` or `JSONDecodeError`
**Fix**: Check `schemas/lesson_output_schema.json` exists and is valid

### 6. Memory/Resource Issues
**Symptom**: `MemoryError` or process killed silently
**Fix**: Close other applications, check Task Manager

## Quick Fixes to Try

### Fix 1: Database Path Standardization
```bash
# Ensure data folder exists
mkdir data

# Check current database
python check_db_url.py
```

### Fix 2: Reinstall Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Fix 3: Clear Python Cache
```bash
# Delete all __pycache__ folders
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"

# Delete .pyc files
del /s /q *.pyc
```

### Fix 4: Test Backend Standalone
```bash
# Start backend manually with verbose logging
python -m uvicorn backend.api:app --reload --port 8000 --log-level debug
```

## What to Share

When you find the error, share:
1. **Full stack trace** (all lines from `Traceback` to the final error)
2. **Error message** (the last line of the error)
3. **What action triggered it** (e.g., "clicked Process Week")
4. **Output from `diagnose_crash.py`**

## Next Steps After Diagnosis

Once we have the error logs, we can:
1. Identify the failing module
2. Implement a targeted fix
3. Add error handling to prevent future crashes
4. Update tests to catch this scenario

---

**Status**: Waiting for error logs from visible terminal
**Blocker**: Need actual Python stack trace to proceed
