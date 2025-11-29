# Quick Start Guide

## Ready to Test! 🚀

The lesson-plan-browser app is ready for testing. Follow these steps:

## Prerequisites Check

### 1. Backend Server
```bash
# Make sure your FastAPI backend is running
# Should be accessible at: http://localhost:8000/api
```

### 2. Install Dependencies
```bash
cd lesson-plan-browser/frontend
npm install
```

**Note:** First install may take a few minutes to download all dependencies.

### 3. Start Development Server
```bash
npm run tauri:dev
```

**First run:**
- Will compile Rust dependencies (5-10 minutes)
- Will launch the desktop app window
- Subsequent runs will be faster

## What to Expect

1. **App Window Opens** - Tauri desktop window (1200x800)
2. **User Selection** - If no users in database, you'll see empty UserSelector
3. **Console Logs** - Check browser console for API connection status

## Common First-Run Issues

### Backend Connection Failed
**Symptom:** Console shows "Failed to load users" errors

**Fix:** 
- Ensure backend is running: `http://localhost:8000`
- Test: `curl http://localhost:8000/api/health`

### Rust Compilation Errors
**Symptom:** Build fails with Rust errors

**Fix:**
```bash
cd lesson-plan-browser/frontend/src-tauri
rustup update
cargo clean
cd ..
npm run tauri:dev
```

### Missing Dependencies
**Symptom:** Import errors or "module not found"

**Fix:**
```bash
npm install
```

## Testing Flow

1. **Select User** - Choose a user from UserSelector (or create one)
2. **Browse Plans** - Navigate to browser view
3. **Select Week** - Choose a week with lesson plans
4. **View Lessons** - Click on lessons to see details
5. **Enter Lesson Mode** - Click "Enter Lesson Mode" button
6. **Test Lesson Mode** - Navigate steps, test timer, etc.

## Files to Review

- `TESTING_CHECKLIST.md` - Detailed test cases
- `SETUP_INSTRUCTIONS.md` - Full setup guide
- `PROJECT_STATUS.md` - Current project status

## Need Help?

Check the console for detailed error messages. The app logs all API calls and errors with `[API]` prefix.

---

**Ready to start?** Run `npm install` then `npm run tauri:dev`!

