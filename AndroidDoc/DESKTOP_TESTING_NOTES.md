# Desktop Testing Notes

## Critical Finding: Backend Required

**Yes, the backend needs to be running for the frontend to work correctly.**

### Why Backend is Required

1. **App Startup:** The app loads users from the API on startup (`UserSelector` component)
2. **API Dependencies:** Many features depend on backend API calls
3. **No Offline Mode Yet:** The sidecar/offline mode is not yet implemented (Phase 5-6)

### How to Start Backend

**Important:** Run from the project root (`d:\LP`), NOT from the `backend` directory:

```powershell
cd d:\LP
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

**Why:** The `backend.api:app` module path requires Python to find `backend` as a package, which only works when running from the parent directory.

**Important:** Use `--host 0.0.0.0` (not `127.0.0.1`) so it's accessible from:
- Desktop Tauri app: `http://localhost:8000`
- Android emulator: `http://10.0.2.2:8000`
- Real device: `http://<PC_IP>:8000`

### API URL Configuration

**Issue Found:** The API was using `/api` (relative path) which relies on Vite's proxy. In Tauri, the proxy doesn't work correctly, causing API calls to return HTML instead of JSON.

**Fix Applied:** Updated `frontend/src/lib/api.ts` to:
- Detect Tauri environment
- Use `http://localhost:8000/api` directly (bypasses proxy)
- Keep `/api` for web browser (where Vite proxy works)

### Testing Checklist

**Before Testing Frontend:**
- [ ] FastAPI backend is running on port 8000
- [ ] Backend is accessible (test: `curl http://localhost:8000/api/health`)

**During Testing:**
- [ ] App window opens
- [ ] No blank screen
- [ ] Users load successfully
- [ ] No API errors in console

### Current Status

- ✅ **Compilation:** Working
- ✅ **App Launch:** Working
- ⚠️ **API Configuration:** Fixed (needs backend running)
- ⏳ **Backend Connection:** Needs testing

---

**Last Updated:** Desktop testing phase

