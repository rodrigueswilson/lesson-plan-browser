# Setup Instructions for Testing

## Prerequisites

1. **Backend Server Running**
   - Ensure the FastAPI backend is running on `http://localhost:8000`
   - Database should have test data (users, lesson plans, schedules)

2. **Node.js and npm**
   - Node.js 18+ installed
   - npm installed

3. **Rust and Tauri**
   - Rust toolchain installed
   - Tauri CLI v2.0 installed (`npm install -g @tauri-apps/cli@latest`)

## Step-by-Step Setup

### 1. Install Dependencies

```bash
cd lesson-plan-browser/frontend
npm install
```

This will install:
- React and React DOM
- TypeScript
- Vite
- Tauri dependencies
- UI libraries (lucide-react, tailwindcss, etc.)

### 2. Verify Backend is Running

```bash
# In a separate terminal, start the backend
cd <main-project-root>
# Start your FastAPI backend server
# Should be accessible at http://localhost:8000
```

Test backend connectivity:
```bash
curl http://localhost:8000/api/health
```

### 3. Run Development Server

```bash
cd lesson-plan-browser/frontend
npm run tauri:dev
```

This will:
- Start the Vite dev server
- Compile the Rust backend
- Launch the Tauri desktop app

**First run may take several minutes** as it compiles Rust dependencies.

## Troubleshooting

### Issue: "Backend not found" or connection errors

**Solution:** Ensure backend is running on `http://localhost:8000`

### Issue: "Module not found" errors

**Solution:**
```bash
cd lesson-plan-browser/frontend
npm install
```

### Issue: Rust compilation errors

**Solution:**
```bash
# Update Rust toolchain
rustup update

# Ensure you're in the correct directory
cd lesson-plan-browser/frontend/src-tauri
cargo check
```

### Issue: Tauri CLI not found

**Solution:**
```bash
npm install -g @tauri-apps/cli@latest
```

### Issue: Port 8000 already in use

**Solution:** 
- Stop the existing backend process
- Or change backend port and update `frontend/src/lib/config.ts`

## Verification Checklist

Before testing, verify:

- [ ] Backend is running and accessible
- [ ] Database has test users
- [ ] Database has test lesson plans
- [ ] JSON lesson plan files exist (if testing JSON file detection)
- [ ] `npm install` completed successfully
- [ ] No TypeScript errors in IDE

## Expected Behavior on First Run

1. App window opens
2. UserSelector displays (may be empty if no users in database)
3. Console shows API connection attempts
4. If backend is running: Users load and can be selected
5. If backend is not running: Error messages in console

## Next Steps

Once the app launches successfully, proceed with testing according to `TESTING_CHECKLIST.md`.

