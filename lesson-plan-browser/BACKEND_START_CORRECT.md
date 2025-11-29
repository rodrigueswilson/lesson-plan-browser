# ✅ Correct Backend Start Command

## The Issue

The backend uses `backend.api:app`, not `backend.main:app`.

## Correct Command

### Option 1: Direct Command
```powershell
cd D:\LP
python -m uvicorn backend.api:app --reload --port 8000
```

### Option 2: Use Batch File (Easiest)
```powershell
cd D:\LP
.\start-backend.bat
```

---

## Complete Testing Steps

### Terminal 1: Backend
```powershell
cd D:\LP
python -m uvicorn backend.api:app --reload --port 8000
```

Wait for: `Uvicorn running on http://127.0.0.1:8000`

### Terminal 2: App
```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run tauri:dev
```

---

## Verify Backend Started Correctly

After starting, you should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using WatchFiles
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**No errors!** ✅

---

**Now try the corrected command!**

