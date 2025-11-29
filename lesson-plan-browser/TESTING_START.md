# Quick Start for PC Testing

## Step 1: Verify Prerequisites

### Check Backend is Running
```powershell
# Test backend health endpoint
curl http://localhost:8000/api/health
```

If backend is not running, start it first in a separate terminal.

### Check Node.js Installation
```powershell
node --version  # Should be 18+
npm --version
```

---

## Step 2: Install Dependencies

```powershell
cd lesson-plan-browser\frontend
npm install
```

**First install takes 2-3 minutes** - downloads all dependencies.

---

## Step 3: Start Development Server

```powershell
# From lesson-plan-browser\frontend directory
npm run tauri:dev
```

**First run takes 5-10 minutes** - compiles Rust dependencies.

---

## Step 4: What to Expect

1. **Build Process:**
   - Vite dev server starts
   - Rust code compiles
   - Tauri app window opens (1200x800)

2. **App Window:**
   - Should show UserSelector component
   - Console logs will show API connection attempts

3. **Console Output:**
   - Look for `[API]` prefixed logs
   - Check for any error messages

---

## Step 5: Initial Testing

### Test User Loading
- [ ] App window opens
- [ ] UserSelector displays
- [ ] Users load from backend (or empty if no users)
- [ ] No errors in console

### Test User Selection
- [ ] Can select a user from dropdown
- [ ] Browser view appears after selection
- [ ] Week selector is visible

---

## Common Issues

### Backend Not Running
**Symptom:** Console shows "Failed to load users" or connection errors

**Fix:**
```powershell
# Start backend in main project directory
cd <main-project-root>
# Start your FastAPI backend
python -m uvicorn backend.main:app --reload
```

### Dependencies Not Installed
**Symptom:** Import errors or "module not found"

**Fix:**
```powershell
cd lesson-plan-browser\frontend
npm install
```

### Rust Compilation Errors
**Symptom:** Build fails with Rust errors

**Fix:**
```powershell
cd lesson-plan-browser\frontend\src-tauri
rustup update
cargo clean
cd ..\..
npm run tauri:dev
```

### Port Already in Use
**Symptom:** "Port 1420 already in use"

**Fix:** Close other instances or change port in `vite.config.ts`

---

## Next: Follow Full Testing Checklist

Once the app is running, proceed with `TESTING_CHECKLIST.md` for comprehensive testing.

---

**Ready?** Run `npm install` then `npm run tauri:dev`!

