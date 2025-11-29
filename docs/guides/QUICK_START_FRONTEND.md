# Quick Start - Frontend Development

**Status**: Ready to run  
**Time to first run**: 10-15 minutes (first time)  
**Prerequisites**: Node.js 18+, Rust 1.70+, Python 3.11+

---

## 1. Install Prerequisites

### Node.js (if not installed)
```bash
# Download from https://nodejs.org/ (LTS version)
# Or use winget:
winget install OpenJS.NodeJS.LTS

# Verify:
node --version  # Should be 18+
npm --version
```

### Rust (if not installed)
```bash
# Download from https://rustup.rs/
# Or use winget:
winget install Rustlang.Rustup

# Verify:
rustc --version  # Should be 1.70+
cargo --version
```

---

## 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

**Time**: 2-3 minutes  
**What it does**: Installs React, Tauri, TailwindCSS, and all dependencies

---

## 3. Start Backend Server

**In a separate terminal:**

```bash
# From project root (d:\LP)
python -m uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
```

**Verify backend is running:**
```bash
curl http://localhost:8000/api/health
```

Should return: `{"status":"healthy",...}`

---

## 4. Start Frontend Development

### Option A: Use the convenience script

```bash
cd frontend
start-dev.bat
```

### Option B: Manual start

```bash
cd frontend
npm run tauri:dev
```

**First run**: 5-10 minutes (Rust compilation)  
**Subsequent runs**: 30-60 seconds

---

## 5. Test the Application

Once the Tauri window opens:

### Test User Management
1. Click user dropdown
2. Select "Wilson Rodrigues" or "Daniela Silva"
3. Verify slots load automatically

### Test Slot Configuration
1. Click "Add Slot" button
2. Fill in:
   - Teacher name: `Davies`
   - Subject: `Math`
   - Grade: `3`
   - Homeroom: `T2`
3. Try dragging the slot to reorder
4. Click delete button to remove

### Test Batch Processing
1. Enter week: `10-06-10-10`
2. Click "Generate" button
3. Watch progress bar update
4. Click "Download" when complete

### Test Plan History
1. Verify generated plan appears
2. Check status indicator (green check)
3. Click "Download" button

---

## 6. Build for Production

```bash
cd frontend
npm run tauri:build
```

**Output location:**
- Installer: `src-tauri/target/release/bundle/msi/`
- Executable: `src-tauri/target/release/bilingual-lesson-planner.exe`

**Build time**: 5-10 minutes

---

## Common Issues

### "Backend is not running"

**Solution:**
```bash
# Start backend in separate terminal
python -m uvicorn backend.api:app --reload
```

### "Rust not found"

**Solution:**
```bash
# Install Rust
winget install Rustlang.Rustup
# Or download from https://rustup.rs/
```

### "npm install fails"

**Solution:**
```bash
# Clear cache and retry
npm cache clean --force
rm -rf node_modules
npm install
```

### "Tauri build fails"

**Solution:**
```bash
# Clean Rust cache
cd src-tauri
cargo clean
cd ..
npm run tauri:build
```

### "Hot reload not working"

**Solution:**
- Save file again (Ctrl+S)
- Check Vite dev server is running (port 1420)
- Restart: `npm run tauri:dev`

---

## Development Workflow

### Daily Development

1. **Start backend** (once per session)
   ```bash
   python -m uvicorn backend.api:app --reload
   ```

2. **Start frontend** (once per session)
   ```bash
   cd frontend
   npm run tauri:dev
   ```

3. **Make changes** to React components
   - Changes hot-reload automatically
   - No restart needed for React changes
   - Restart needed for Rust changes

4. **Test changes** in Tauri window
   - Open DevTools: F12
   - Check console for errors
   - Test all affected features

### Making Changes

**React Components** (`src/components/`)
- Edit `.tsx` files
- Changes appear immediately (hot reload)
- Check browser console for errors

**Styles** (`src/index.css`)
- Edit TailwindCSS classes
- Changes appear immediately
- Use Tailwind IntelliSense in VS Code

**API Client** (`src/lib/api.ts`)
- Edit TypeScript files
- Changes hot-reload
- Verify API calls in Network tab

**State Management** (`src/store/useStore.ts`)
- Edit Zustand store
- Changes hot-reload
- Use React DevTools to inspect state

---

## Project Structure Reference

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Reusable UI components
│   │   ├── UserSelector.tsx
│   │   ├── SlotConfigurator.tsx
│   │   ├── BatchProcessor.tsx
│   │   └── PlanHistory.tsx
│   ├── lib/
│   │   ├── api.ts           # API client
│   │   └── utils.ts         # Utilities
│   ├── store/
│   │   └── useStore.ts      # State management
│   ├── App.tsx              # Main app
│   └── main.tsx             # Entry point
├── src-tauri/               # Rust/Tauri code
├── package.json
└── start-dev.bat            # Convenience script
```

---

## Key Commands

| Command | Purpose |
|---------|---------|
| `npm install` | Install dependencies |
| `npm run dev` | Start Vite dev server only |
| `npm run tauri:dev` | Start Tauri + Vite (full app) |
| `npm run tauri:build` | Build production executable |
| `npm run build` | Build web assets only |

---

## Performance Tips

- **First run is slow** (Rust compilation): 5-10 minutes
- **Subsequent runs are fast**: 30-60 seconds
- **Hot reload is instant**: React changes appear immediately
- **Build once, run many**: Production build is one-time

---

## Documentation

- **FRONTEND_SETUP_GUIDE.md** - Complete setup guide
- **frontend/README.md** - Frontend documentation
- **DAY5_COMPLETE.md** - Implementation summary
- **ACTUAL_USER_CONFIGURATIONS.md** - User profiles

---

## Support

If you encounter issues:

1. Check **TROUBLESHOOTING_QUICK_REFERENCE.md**
2. Review **FRONTEND_SETUP_GUIDE.md**
3. Check browser console (F12)
4. Check terminal output
5. Verify backend is running

---

**Ready to develop!** 🚀

Start with: `cd frontend && start-dev.bat`
