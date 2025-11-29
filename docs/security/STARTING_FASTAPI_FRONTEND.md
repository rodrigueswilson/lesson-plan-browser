# Starting FastAPI and Frontend

## Starting FastAPI (Backend)

**From the project root (`D:\LP`):**

```powershell
cd D:\LP
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

**Or use the script:**
```powershell
.\scripts\start_fastapi.ps1
```

**What to expect:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Endpoints:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health
- Metrics: http://localhost:8000/metrics

---

## Starting Frontend

**The frontend is in the `frontend` directory. You need to change to that directory first:**

```powershell
cd D:\LP\frontend
npm run dev
```

**Or from root:**
```powershell
cd D:\LP
cd frontend
npm run dev
```

**What to expect:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Frontend will be available at:** http://localhost:5173

---

## Quick Start (Both Services)

**Terminal 1 - Backend:**
```powershell
cd D:\LP
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd D:\LP\frontend
npm run dev
```

---

## Troubleshooting

### Frontend: "Could not read package.json"

**Problem:** Running `npm run dev` from root directory

**Solution:** Change to frontend directory first:
```powershell
cd frontend
npm run dev
```

### Backend: "ModuleNotFoundError"

**Problem:** Missing Python dependencies

**Solution:** Install dependencies:
```powershell
pip install -r requirements.txt
```

### Port Already in Use

**Backend (port 8000):**
```powershell
# Find and stop process
.\scripts\stop_fastapi.ps1
```

**Frontend (port 5173):**
```powershell
# Find process using port 5173
netstat -ano | findstr :5173
# Stop the process (replace PID)
taskkill /PID <PID> /F
```

---

## Verifying Everything Works

### 1. Backend Health Check
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
- Alertmanager: http://localhost:9093
- Check targets: http://localhost:9090/targets

---

## Summary

**Backend:** Run from `D:\LP` (root directory)
```powershell
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:** Run from `D:\LP\frontend` directory
```powershell
cd frontend
npm run dev
```

Both need to be running for the full application to work!

