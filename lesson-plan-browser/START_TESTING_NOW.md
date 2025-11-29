# Start PC Testing Now

## Current Status ✅

- ✅ Dependencies installed
- ⚠️ Backend needs to be started
- ✅ App ready to launch

---

## Step-by-Step Instructions

### Step 1: Start Backend (Terminal 1)

Open a **new terminal window** and run:

```powershell
# Navigate to main project directory
cd D:\LP

# Start FastAPI backend
python -m uvicorn backend.api:app --reload --port 8000

# Or use the batch file:
# .\start-backend.bat
```

**Wait for:** `Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`

**Keep this terminal open** - backend must stay running.

---

### Step 2: Start App (Terminal 2)

Open a **second terminal window** and run:

```powershell
# Navigate to browser app
cd D:\LP\lesson-plan-browser\frontend

# Start development server
npm run tauri:dev
```

**First run:** Will take 5-10 minutes to compile Rust code.

**Subsequent runs:** Much faster (~30 seconds).

---

### Step 3: What to Expect

1. **Build Process:**
   ```
   > tauri dev
   [vite] VITE ready in XXX ms
   [tauri] Compiling Rust code...
   (This takes 5-10 minutes on first run)
   ```

2. **App Window Opens:**
   - Window size: 1200x800
   - Title: "Lesson Plan Browser"
   - Shows UserSelector component

3. **Console Output:**
   ```
   [API] Determining API URL. UserAgent: ...
   [API] Using HTTP API (desktop/remote-control mode)
   [API] GET http://localhost:8000/api/users
   ```

---

## Step 4: Initial Verification

### ✅ Success Indicators

- [ ] App window opens
- [ ] UserSelector component visible
- [ ] Console shows API connection logs
- [ ] No red error messages in console

### ⚠️ If Backend Not Running

**Symptoms:**
- Console shows connection errors
- "Failed to load users" messages
- App shows empty user selector with errors

**Fix:** Go back to Step 1 - start backend first

---

## Step 5: Basic Test

Once app is running:

1. **Check User Loading:**
   - If users exist in database: Dropdown shows users
   - If no users: Empty selector (still OK, app is working)

2. **Select a User:**
   - Select from dropdown (if available)
   - Browser view should appear
   - Week selector should be visible

---

## Quick Reference

### Terminal 1 (Backend)
```powershell
cd D:\LP
python -m uvicorn backend.main:app --reload
```

### Terminal 2 (App)
```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run tauri:dev
```

### Stop App
- Press `Ctrl+C` in Terminal 2
- Close app window

### Stop Backend
- Press `Ctrl+C` in Terminal 1

---

## Troubleshooting

### Issue: "Backend not found"
**Solution:** Start backend in Terminal 1 first

### Issue: "Port 1420 already in use"
**Solution:** 
- Close other instances
- Or change port in `vite.config.ts`

### Issue: Rust compilation fails
**Solution:**
```powershell
cd D:\LP\lesson-plan-browser\frontend\src-tauri
rustup update
cargo clean
cd ..\..
npm run tauri:dev
```

### Issue: App window doesn't open
**Solution:** 
- Check console for errors
- Verify Rust is installed: `rustup --version`

---

## Next: Full Testing

After basic verification, follow `TESTING_CHECKLIST.md` for comprehensive testing.

---

**Ready?** Start Terminal 1 for backend, then Terminal 2 for app!

