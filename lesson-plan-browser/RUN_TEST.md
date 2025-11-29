# Running PC Tests - Step by Step

## ✅ Step 1: Dependencies Installed

Dependencies have been installed successfully!

## Step 2: Check Backend Status

**Backend must be running on `http://localhost:8000`**

If backend is not running:
1. Open a **new terminal window**
2. Navigate to your main project directory
3. Start the backend:
   ```powershell
   python -m uvicorn backend.api:app --reload --port 8000

# Or use the batch file:
# .\start-backend.bat
   ```

Wait for: `Uvicorn running on http://127.0.0.1:8000`

## Step 3: Start the App

From the `lesson-plan-browser` directory, run:

```powershell
cd frontend
npm run tauri:dev
```

**First run will take 5-10 minutes** to compile Rust dependencies.

**What happens:**
1. Vite dev server starts (port 1420)
2. Rust code compiles
3. Tauri app window opens (1200x800)
4. App loads in the window

## Step 4: Initial Verification

When the app window opens, you should see:

### Expected Behavior
- ✅ UserSelector component displayed
- ✅ Console shows API connection logs
- ✅ If users exist: Dropdown with users
- ✅ If no users: Empty selector (still OK)

### Console Logs to Look For
- `[API] Determining API URL...`
- `[API] Using HTTP API (desktop/remote-control mode)`
- `[API] GET http://localhost:8000/api/users`

### Common First-Run Issues

**Issue: Backend Connection Failed**
- Check backend is running
- Check console for error messages
- Verify backend URL is `http://localhost:8000`

**Issue: Rust Compilation Errors**
- First run always takes time (5-10 minutes)
- Subsequent runs are faster
- Check for specific error messages

**Issue: App Window Doesn't Open**
- Check console for errors
- Verify Rust toolchain is installed: `rustup --version`

## Step 5: Basic Testing

Once the app window opens:

1. **Check User Loading**
   - [ ] UserSelector appears
   - [ ] Users load (or shows empty if no users in database)
   - [ ] No errors in console

2. **Select a User**
   - [ ] Select user from dropdown
   - [ ] Browser view appears
   - [ ] Week selector is visible

3. **Navigate Browser**
   - [ ] Week view displays
   - [ ] Can switch to day view
   - [ ] Can click on lessons

## Step 6: Full Testing Checklist

After basic verification works, follow the complete checklist:
- See `TESTING_CHECKLIST.md` for detailed test cases

---

## Quick Commands

```powershell
# Start app (from lesson-plan-browser/frontend)
npm run tauri:dev

# Stop app
Press Ctrl+C in the terminal

# Check backend
curl http://localhost:8000/api/health
```

---

**Ready?** Make sure backend is running, then run `npm run tauri:dev`!

