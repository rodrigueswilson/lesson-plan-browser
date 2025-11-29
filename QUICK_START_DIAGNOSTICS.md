# Quick Start: Backend Crash Diagnostics

## The Problem
Backend crashes during lesson plan processing. Need error logs to fix it.

## The Solution
Run diagnostics to capture the exact error.

---

## 🚀 Quick Start (Choose One)

### Option 1: Safe Startup with Diagnostics (Recommended)
```bash
cd D:\LP
start-with-diagnostics.bat
```

**What it does**:
1. ✅ Checks configuration
2. ✅ Tests all components
3. ✅ Starts backend with visible logs
4. ✅ Shows errors immediately

### Option 2: Manual Diagnostics
```bash
cd D:\LP

# Step 1: Check config
python verify_config.py

# Step 2: Test components
python diagnose_crash.py

# Step 3: Start backend
python -m uvicorn backend.api:app --reload --port 8000
```

### Option 3: Use Existing Script
```bash
cd D:\LP
start-app.bat
```

**Then watch the "Backend API" terminal window for errors.**

---

## 📋 What to Do Next

### If Diagnostics Pass ✅
1. Backend starts successfully
2. Open frontend (Tauri window)
3. Process a lesson plan
4. **Watch the Backend API terminal**
5. Share any error messages

### If Diagnostics Fail ❌
You'll see exactly what's broken:
- **Import error** → Run `pip install -r requirements.txt`
- **Database error** → Check `.env` has `DATABASE_URL=sqlite:///./data/lesson_planner.db`
- **Template error** → Verify `input/Lesson Plan Template SY'25-26.docx` exists
- **Config error** → Copy `.env.example` to `.env` and configure

---

## 🔍 What We're Looking For

### Error Format
```
Traceback (most recent call last):
  File "backend/api.py", line 123, in process_lesson
    result = processor.process(data)
  File "tools/batch_processor.py", line 456, in process
    raise ValueError("Something went wrong")
ValueError: Something went wrong
```

### Share This Info
1. **Full error message** (all lines from "Traceback" to the end)
2. **What you were doing** (e.g., "clicked Process Week")
3. **Output from diagnostics** (if they failed)

---

## 🛠️ Common Quick Fixes

### Fix 1: Database Path Issue
```bash
# Check your .env file has this:
DATABASE_URL=sqlite:///./data/lesson_planner.db

# Create data folder if missing
mkdir data
```

### Fix 2: Missing Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Fix 3: Template File
```bash
# Verify it exists
dir "input\Lesson Plan Template SY'25-26.docx"
```

### Fix 4: Clear Python Cache
```bash
# Delete cache folders
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"
```

---

## 📊 Diagnostic Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `verify_config.py` | Quick config check | Before starting backend |
| `diagnose_crash.py` | Full component test | If backend won't start |
| `start-with-diagnostics.bat` | Safe startup | Every time (recommended) |
| `start-app.bat` | Normal startup | When diagnostics pass |

---

## ✅ Success Checklist

- [ ] `verify_config.py` passes
- [ ] `diagnose_crash.py` passes
- [ ] Backend starts without errors
- [ ] Frontend connects to backend
- [ ] Can process a lesson plan without crash

---

## 🎯 Bottom Line

**Run this now**:
```bash
start-with-diagnostics.bat
```

**Then share**:
- Any error messages from the terminal
- What step failed (config check, diagnostics, or processing)

**We'll fix it in < 30 minutes once we see the error!**
