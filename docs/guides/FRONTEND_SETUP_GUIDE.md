# Frontend Setup Guide - Day 5 Implementation

**Status**: Complete  
**Date**: October 5, 2025  
**Progress**: 100% (Day 5 Complete)

---

## What Was Built

A complete Tauri + React + TypeScript desktop application with:

### Core Features
- **Multi-user system** with Wilson Rodrigues and Daniela Silva profiles
- **Variable slot configuration** (1-10 slots, not fixed at 6)
- **Drag & drop slot reordering** for output sequence control
- **Real-time progress tracking** via Server-Sent Events (SSE)
- **Grade-aware processing** with K-12 support
- **Plan history** with download capability

### Technology Stack
- Frontend: React 18 + TypeScript
- Desktop: Tauri 1.5
- Styling: TailwindCSS + Custom Components
- State: Zustand
- DnD: @dnd-kit/core + @dnd-kit/sortable
- HTTP: Axios

---

## Quick Start

### 1. Install Node Dependencies

```bash
cd frontend
npm install
```

This installs:
- React and React DOM
- Tauri API bindings
- TailwindCSS and PostCSS
- TypeScript and Vite
- Zustand, Axios, @dnd-kit
- Lucide icons

### 2. Install Rust (if not already installed)

**Windows:**
```bash
# Download and run rustup-init.exe from:
# https://rustup.rs/

# Or use winget:
winget install Rustlang.Rustup
```

**Verify installation:**
```bash
rustc --version
cargo --version
```

### 3. Start Backend Server

The frontend requires the FastAPI backend running on port 8000.

```bash
# From project root (d:\LP)
python -m uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
```

**Verify backend is running:**
```bash
curl http://localhost:8000/api/health
```

Should return: `{"status":"healthy","version":"1.0.0",...}`

### 4. Run Development Mode

```bash
cd frontend
npm run tauri:dev
```

This will:
1. Start Vite dev server on port 1420
2. Compile Rust code
3. Launch Tauri desktop window
4. Enable hot-reload for React changes

**First run takes 5-10 minutes** (Rust compilation). Subsequent runs are faster.

---

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                    # Base UI components
│   │   │   ├── Button.tsx         # Button with variants
│   │   │   ├── Card.tsx           # Card container
│   │   │   ├── Input.tsx          # Text input
│   │   │   ├── Select.tsx         # Dropdown select
│   │   │   ├── Label.tsx          # Form label
│   │   │   ├── Alert.tsx          # Alert messages
│   │   │   └── Progress.tsx       # Progress bar
│   │   ├── UserSelector.tsx       # User management UI
│   │   ├── SlotConfigurator.tsx   # Slot config with DnD
│   │   ├── BatchProcessor.tsx     # Week processing
│   │   └── PlanHistory.tsx        # Generated plans list
│   ├── lib/
│   │   ├── api.ts                 # API client + types
│   │   └── utils.ts               # Utilities
│   ├── store/
│   │   └── useStore.ts            # Zustand state
│   ├── App.tsx                    # Main app
│   ├── main.tsx                   # React entry
│   └── index.css                  # TailwindCSS
├── src-tauri/
│   ├── src/
│   │   └── main.rs                # Rust entry point
│   ├── Cargo.toml                 # Rust dependencies
│   └── tauri.conf.json            # Tauri config
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

---

## Component Overview

### 1. UserSelector
**File**: `src/components/UserSelector.tsx`

**Features**:
- Dropdown to select user (Wilson or Daniela)
- "Add User" button to create new profiles
- Auto-loads user's slots and plans on selection
- Displays current user context

**API Calls**:
- `GET /api/users` - List all users
- `POST /api/users` - Create new user
- `GET /api/users/{id}` - Get user details
- `GET /api/users/{id}/slots` - Load user's slots
- `GET /api/users/{id}/plans` - Load user's plans

### 2. SlotConfigurator
**File**: `src/components/SlotConfigurator.tsx`

**Features**:
- Display 1-10 slots (variable count)
- Add/Remove slots dynamically
- Drag & drop to reorder (uses @dnd-kit)
- Configure per slot:
  - Teacher name (text input, not file picker)
  - Subject (dropdown)
  - Grade (K-12 dropdown)
  - Homeroom (text input)
- Real-time updates to backend
- Display order indicator

**API Calls**:
- `POST /api/users/{id}/slots` - Create slot
- `PUT /api/slots/{id}` - Update slot
- `DELETE /api/slots/{id}` - Delete slot

**Drag & Drop**:
- Uses `@dnd-kit/core` for DnD context
- Uses `@dnd-kit/sortable` for sortable items
- Updates `display_order` field on backend

### 3. BatchProcessor
**File**: `src/components/BatchProcessor.tsx`

**Features**:
- Week input (MM-DD-MM-DD format)
- "Generate" button to start processing
- Real-time progress via SSE
- Progress bar with slot count
- Success/error alerts
- Download button for completed plans
- Displays configured slots preview

**API Calls**:
- `POST /api/process-week` - Start batch processing
- `GET /api/progress/{task_id}` - SSE progress stream
- `GET /api/render/{filename}` - Download DOCX

**SSE Progress**:
```typescript
const eventSource = new EventSource(`/api/progress/${taskId}`);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Update progress: data.current, data.total, data.message
};
```

### 4. PlanHistory
**File**: `src/components/PlanHistory.tsx`

**Features**:
- List of generated plans (newest first)
- Status indicators:
  - Completed (green check)
  - Failed (red X)
  - Processing (spinner)
  - Pending (clock)
- Download button for completed plans
- Formatted dates and week ranges

**API Calls**:
- `GET /api/users/{id}/plans` - List plans
- `GET /api/render/{filename}` - Download plan

---

## State Management

### Zustand Store
**File**: `src/store/useStore.ts`

**State**:
```typescript
{
  currentUser: User | null,
  users: User[],
  slots: ClassSlot[],
  plans: WeeklyPlan[],
  isProcessing: boolean,
  progress: { current, total, message },
  selectedWeek: string | null
}
```

**Actions**:
- `setCurrentUser(user)` - Set active user
- `setUsers(users)` - Update users list
- `setSlots(slots)` - Update slots
- `addSlot(slot)` - Add new slot
- `updateSlot(id, data)` - Update slot
- `removeSlot(id)` - Remove slot
- `setPlans(plans)` - Update plans
- `setIsProcessing(bool)` - Set processing state
- `setProgress(progress)` - Update progress
- `setSelectedWeek(week)` - Set selected week

**Usage**:
```typescript
import { useStore } from '../store/useStore';

function MyComponent() {
  const { currentUser, slots, setSlots } = useStore();
  // ...
}
```

---

## API Client

### File: `src/lib/api.ts`

**Base URL**: `http://localhost:8000/api`

**Exports**:
- `userApi` - User CRUD operations
- `slotApi` - Slot CRUD operations
- `planApi` - Plan operations
- `healthCheck()` - Health check
- `createProgressStream(taskId, onProgress)` - SSE stream

**Types**:
- `User` - User profile
- `ClassSlot` - Class slot configuration
- `WeeklyPlan` - Generated plan record
- `BatchProcessResult` - Processing result

**Example**:
```typescript
import { userApi, slotApi } from '../lib/api';

// List users
const response = await userApi.list();
const users = response.data;

// Create slot
const slot = await slotApi.create(userId, {
  slot_number: 1,
  subject: 'Math',
  grade: '3',
  homeroom: 'T5',
});
```

---

## Building for Production

### Development Build
```bash
npm run tauri:dev
```

### Production Build
```bash
npm run tauri:build
```

**Output**:
- Windows: `src-tauri/target/release/bundle/msi/Bilingual Lesson Planner_1.0.0_x64_en-US.msi`
- Executable: `src-tauri/target/release/bilingual-lesson-planner.exe`

**Build includes**:
- Compiled React app (optimized)
- Rust binary (optimized)
- All dependencies bundled
- Windows installer (MSI)

### Build Configuration

**Tauri Config**: `src-tauri/tauri.conf.json`
- Window size: 1200x800 (min 800x600)
- Allowed HTTP: `localhost:8000`
- File system access: User documents
- Dialog permissions: Open/Save

**Vite Config**: `vite.config.ts`
- Dev server: Port 1420
- Build target: Chrome 105 / Safari 13
- Path alias: `@/` → `./src/`

---

## Testing the UI

### 1. User Management
- [ ] Select Wilson Rodrigues from dropdown
- [ ] Verify slots load (should show 5 slots)
- [ ] Switch to Daniela Silva
- [ ] Verify slots load (should show 5 slots)
- [ ] Click "Add User" and create test user
- [ ] Verify new user appears in dropdown

### 2. Slot Configuration
- [ ] Click "Add Slot" button
- [ ] Fill in teacher name, subject, grade, homeroom
- [ ] Drag slot to reorder
- [ ] Verify order updates
- [ ] Click delete button
- [ ] Confirm deletion works

### 3. Batch Processing
- [ ] Enter week: `10-06-10-10`
- [ ] Click "Generate" button
- [ ] Verify progress bar updates
- [ ] Wait for completion
- [ ] Click "Download" button
- [ ] Verify DOCX file downloads

### 4. Plan History
- [ ] Verify generated plan appears in history
- [ ] Check status indicator (green check)
- [ ] Click "Download" button
- [ ] Verify file downloads again

---

## Troubleshooting

### Backend Connection Failed

**Symptom**: API calls fail, console shows network errors

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Restart backend
python -m uvicorn backend.api:app --reload
```

### Rust Compilation Errors

**Symptom**: `cargo build` fails during `npm run tauri:dev`

**Solution**:
```bash
# Update Rust
rustup update

# Clean and rebuild
cd src-tauri
cargo clean
cd ..
npm run tauri:dev
```

### Hot Reload Not Working

**Symptom**: React changes don't appear

**Solution**:
- Save file again (Ctrl+S)
- Check Vite dev server is running (port 1420)
- Restart: `npm run tauri:dev`

### Drag & Drop Not Working

**Symptom**: Slots don't reorder

**Solution**:
- Check console for errors
- Verify @dnd-kit packages installed: `npm list @dnd-kit`
- Ensure slot IDs are unique

### SSE Progress Not Updating

**Symptom**: Progress bar stuck at 0%

**Solution**:
- Check backend logs for SSE errors
- Verify `/api/progress/{task_id}` endpoint works
- Check browser console for EventSource errors

---

## Next Steps

### Production Deployment
1. Build production executable: `npm run tauri:build`
2. Test on clean Windows machine
3. Create installer (MSI already generated)
4. Distribute to users

### Optional Enhancements
- [ ] Dark mode toggle
- [ ] Keyboard shortcuts
- [ ] Undo/redo for slot changes
- [ ] Bulk slot import (CSV)
- [ ] Custom themes
- [ ] Offline mode

---

## Performance Targets

- **Initial Load**: < 2 seconds
- **User Switch**: < 500ms
- **Slot Add/Remove**: Instant (optimistic updates)
- **Drag & Drop**: 60 FPS
- **Batch Processing**: Depends on slot count + LLM speed
- **Memory Usage**: < 200MB typical

---

## Success Criteria (Day 5)

- [x] User can select/switch between users
- [x] User can configure 1-10 slots (variable count)
- [x] User can drag & drop to reorder slots
- [x] User can trigger batch processing
- [x] User sees real-time progress via SSE
- [x] User can download generated plans
- [x] User can access plan history
- [x] Error handling works (partial failures)
- [x] UI is responsive and modern
- [x] All API endpoints integrated

---

## Files Created

**Configuration** (10 files):
- `package.json` - Node dependencies
- `tsconfig.json` - TypeScript config
- `vite.config.ts` - Vite config
- `tailwind.config.js` - TailwindCSS config
- `postcss.config.js` - PostCSS config
- `src-tauri/tauri.conf.json` - Tauri config
- `src-tauri/Cargo.toml` - Rust dependencies
- `src-tauri/src/main.rs` - Rust entry
- `src-tauri/build.rs` - Rust build script
- `index.html` - HTML entry

**Source Code** (18 files):
- `src/main.tsx` - React entry
- `src/App.tsx` - Main app
- `src/index.css` - Global styles
- `src/lib/api.ts` - API client
- `src/lib/utils.ts` - Utilities
- `src/store/useStore.ts` - State management
- `src/components/ui/Button.tsx`
- `src/components/ui/Card.tsx`
- `src/components/ui/Input.tsx`
- `src/components/ui/Select.tsx`
- `src/components/ui/Label.tsx`
- `src/components/ui/Alert.tsx`
- `src/components/ui/Progress.tsx`
- `src/components/UserSelector.tsx`
- `src/components/SlotConfigurator.tsx`
- `src/components/BatchProcessor.tsx`
- `src/components/PlanHistory.tsx`
- `frontend/README.md` - Documentation

---

**Status**: Day 5 Complete - 100% ✅  
**Ready for**: Production deployment and user testing
