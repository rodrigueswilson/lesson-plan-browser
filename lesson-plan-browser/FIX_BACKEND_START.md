# Fix Backend Start Command

## Issue

The backend import error occurred because the wrong module was specified.

**Wrong command:**
```powershell
python -m uvicorn backend.main:app --reload
```

**Correct command:**
```powershell
python -m uvicorn backend.api:app --reload --port 8000
```

The FastAPI app is in `backend/api.py`, not `backend/main.py`.

---

## Corrected Steps

### Step 1: Start Backend (Terminal 1)

```powershell
cd D:\LP
python -m uvicorn backend.api:app --reload --port 8000
```

Or use the batch file:
```powershell
cd D:\LP
.\start-backend.bat
```

**Wait for:** `Uvicorn running on http://127.0.0.1:8000`

---

### Step 2: Start App (Terminal 2)

```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run tauri:dev
```

---

## Alternative: Use Existing Batch File

You can also use the existing backend start script:

```powershell
cd D:\LP
.\start-backend.bat
```

This script:
- Checks Python installation
- Installs uvicorn if needed
- Starts backend on port 8000
- Uses correct module: `backend.api:app`

---

## Verify Backend is Running

Test the backend:
```powershell
curl http://localhost:8000/api/health
```

Should return JSON with status information.

---

**Try again with:** `python -m uvicorn backend.api:app --reload --port 8000`

