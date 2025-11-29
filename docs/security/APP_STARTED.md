# Application Started

## ✅ Both Services Started

I've started both the backend and frontend in separate PowerShell windows.

---

## What's Running

### Backend (FastAPI)
- **Window:** New PowerShell window titled "Starting FastAPI Backend..."
- **URL:** http://localhost:8000
- **Status:** Check the window for startup messages
- **Endpoints:**
  - API: http://localhost:8000
  - API Docs: http://localhost:8000/docs
  - Health: http://localhost:8000/api/health
  - Metrics: http://localhost:8000/metrics

### Frontend (Vite/React)
- **Window:** New PowerShell window titled "Starting Frontend..."
- **URL:** http://localhost:5173
- **Status:** Check the window for startup messages
- **Opens:** Automatically in your browser (or open manually)

---

## Check the Windows

**Look for two new PowerShell windows:**

1. **Backend Window** - Should show:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
   INFO:     Started reloader process
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   ```

2. **Frontend Window** - Should show:
   ```
   VITE v5.x.x  ready in xxx ms

   ➜  Local:   http://localhost:5173/
   ➜  Network: use --host to expose
   ```

---

## Access the Application

**Open in browser:**
- Frontend: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs

---

## If Services Don't Start

### Backend Issues

**Check the backend window for errors:**
- Import errors → Install dependencies: `pip install -r requirements.txt`
- Port in use → Stop existing process: `.\scripts\stop_fastapi.ps1`
- Module not found → Install missing package

**Common fixes:**
```powershell
# Install dependencies
pip install -r requirements.txt

# Restart backend
cd D:\LP
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Issues

**Check the frontend window for errors:**
- Missing dependencies → Run: `npm install` in `frontend` directory
- Port in use → Change port or stop existing process

**Common fixes:**
```powershell
# Install dependencies
cd D:\LP\frontend
npm install

# Start frontend
npm run dev
```

---

## Stopping the Services

**To stop:**
1. Go to each PowerShell window
2. Press `Ctrl+C` to stop the service
3. Or close the window

**Or use scripts:**
```powershell
# Stop backend
.\scripts\stop_fastapi.ps1
```

---

## Verifying Everything Works

### 1. Backend Health
```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/health -UseBasicParsing
```

### 2. Backend Metrics
```powershell
Invoke-WebRequest -Uri http://localhost:8000/metrics -UseBasicParsing
```

### 3. Frontend
Open http://localhost:5173 in your browser

### 4. Prometheus (if running)
- Prometheus: http://localhost:9090
- Check targets: http://localhost:9090/targets
- Should show `lesson-planner-api` as UP (green)

---

## Quick Reference

**Backend:**
- Port: 8000
- Command: `uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000`
- Run from: `D:\LP` (root directory)

**Frontend:**
- Port: 5173
- Command: `npm run dev`
- Run from: `D:\LP\frontend` directory

**Both should be running for the full application to work!**

