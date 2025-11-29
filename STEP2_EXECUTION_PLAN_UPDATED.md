# Step 2: Create Android Browser with Lesson Mode - Updated Execution Plan

## Overview

Create a streamlined Android tablet application that includes:
- Full lesson plan browser (identical to main app)
- Complete Lesson Mode functionality for teaching
- Dual data source support (database + JSON files)
- **Standalone offline architecture with local storage (REQUIRED)**

**Architecture Decision:** Separate project folder (`lesson-plan-browser/`) for cleaner separation.

**Implementation Order:** PC standalone version first → Android compilation with standalone architecture → Sync capabilities

**CRITICAL:** Android version MUST use local storage (embedded SQLite database + local JSON files). It does NOT connect to PC backend for daily use - only for sync operations.

---

## Phase 1: Project Structure & Setup

### 1.1 Create New Project Structure

Create `lesson-plan-browser/` directory structure:

```
lesson-plan-browser/
├── frontend/              # React + Tauri app (standalone)
│   ├── src/
│   │   ├── components/    # Copied from main app
│   │   ├── lib/           # API client (dual mode: HTTP for PC, local DB for Android)
│   │   ├── hooks/         # Timer hooks
│   │   ├── store/         # State management
│   │   └── utils/         # Utilities (plan matching, schedule entries, etc.)
│   └── src-tauri/         # Tauri configuration
├── backend/               # Minimal FastAPI backend (optional - can reuse main backend)
│   └── [minimal endpoints only]
└── README.md
```

**Files to create:**
- `lesson-plan-browser/frontend/package.json` - Copy from main frontend, remove unused deps
- `lesson-plan-browser/frontend/src-tauri/tauri.conf.json` - Configure for Android
- `lesson-plan-browser/frontend/tsconfig.json` - TypeScript config
- `lesson-plan-browser/frontend/vite.config.ts` - Vite config
- `lesson-plan-browser/README.md` - Project documentation

**Key decision:** Reuse main backend initially (no separate backend needed for PC version). Backend already supports all required endpoints.

---

## Phase 2: Copy & Adapt Components

### 2.1 Copy Core Browser Components

Copy from `frontend/src/components/` to `lesson-plan-browser/frontend/src/components/`:

**Browser Components (unchanged):**
- `LessonPlanBrowser.tsx` - Main browser component
- `WeekView.tsx` - Week view
- `DayView.tsx` - Day view
- `LessonDetailView.tsx` - Lesson detail view

**Dependencies to identify and copy:**
- All UI components from `frontend/src/components/ui/`
- Resource display components from `frontend/src/components/resources/`

### 2.2 Copy Lesson Mode Components

**Lesson Mode Components (unchanged):**
- `LessonMode.tsx` - Main lesson mode component
- `TimelineSidebar.tsx` - Step timeline sidebar
- `CurrentStepInstructions.tsx` - Step instructions panel
- `ResourceDisplayArea.tsx` - Resources display
- `TimerAdjustmentDialog.tsx` - Timer adjustment dialog
- `TimerDisplay.tsx` - Timer display component
- `StepNavigation.tsx` - Step navigation controls

### 2.3 Copy Required Utilities

Copy from `frontend/src/utils/`:
- `scheduleEntries.ts` - `dedupeScheduleEntries`, `normalizeSubject`
- `planMatching.ts` - `findPlanSlotForEntry`
- `planIdResolver.ts` - `resolvePlanIdFromScheduleEntry`
- `lessonStepRecalculation.ts` - `recalculateStepDurations`

### 2.4 Copy Required Hooks

Copy from `frontend/src/hooks/`:
- `useLessonTimer.ts` - Timer hook for lesson mode

### 2.5 Copy State Management

Copy from `frontend/src/store/`:
- `useStore.ts` - State management (may need simplification - remove batch processing, schedule editing state)

---

## Phase 3: Create Dual-Mode API Client

### 3.1 Create API Client with Mode Detection

Create `lesson-plan-browser/frontend/src/lib/api.ts` based on `frontend/src/lib/api.ts`:

**CRITICAL: Dual Mode Architecture**

**Mode Detection:**
- Reuse `isStandaloneMode()` logic from main app (detects Android + Tauri)
- **PC Version:** Use HTTP backend API (localhost:8000) - for development/testing
- **Android Version:** Use local database via Tauri commands (standalone mode)

**Required capabilities:**

**For PC version (HTTP API):**
- `planApi.list()` - List lesson plans from database
- `lessonApi.getPlanDetail()` - Get plan detail with `lesson_json`
- `scheduleApi.getSchedule()` - Get schedule entries
- `scheduleApi.getCurrentLesson()` - Get current lesson (for Lesson Mode)
- `userApi.getRecentWeeks()` - Get available weeks (detects JSON files)
- `userApi.getSlots()` - Get class slots (for enrichment)
- `lessonApi.getLessonSteps()` - Get lesson steps
- `lessonApi.generateLessonSteps()` - Generate lesson steps
- `lessonModeSessionApi.getActive()` - Get active session
- `lessonModeSessionApi.create()` - Create/update session
- `lessonModeSessionApi.end()` - End session

**For Android version (Local Database via Tauri):**
- Direct SQL queries via `sql_query` Tauri command
- Read from local embedded SQLite database (on tablet)
- Read JSON files from local file system
- Write lesson mode sessions to local database
- **Sync endpoints (WiFi only - for populating local data):**
  - Fetch from PC backend → Save to local database
  - Fetch JSON files → Save to local storage

**Implementation:**
- Copy API client structure from main app
- Implement dual mode: HTTP API (PC) vs Local Database (Android)
- Use `isStandaloneMode()` to switch between modes
- Reuse existing Tauri database commands (`sql_query`, `sql_execute` - already in main app)
- Remove unused endpoints (batch processing, analytics, etc.)

---

## Phase 4: Application Entry Point

### 4.1 Create Main App Component

Create `lesson-plan-browser/frontend/src/App.tsx`:

**Features:**
- User selector (minimal - just for user selection)
- Navigation between Browser and Lesson Mode
- No batch processing, schedule editing, or analytics views

**Navigation flow:**
- Default: Lesson Plan Browser view
- Click lesson → Lesson Detail View
- Enter Lesson Mode button → Switch to Lesson Mode
- Exit Lesson Mode → Return to Browser

**Structure:**
```typescript
function App() {
  const [view, setView] = useState<'browser' | 'lesson-mode'>();
  const [lessonModeProps, setLessonModeProps] = useState<LessonModeProps>();
  
  return (
    <div>
      {view === 'browser' && (
        <LessonPlanBrowser 
          onEnterLessonMode={(entry, day, slot, planId) => {
            setLessonModeProps({ scheduleEntry: entry, day, slot, planId });
            setView('lesson-mode');
          }}
        />
      )}
      {view === 'lesson-mode' && lessonModeProps && (
        <LessonMode 
          {...lessonModeProps}
          onExit={() => setView('browser')}
        />
      )}
    </div>
  );
}
```

### 4.2 Create Entry Point File

Create `lesson-plan-browser/frontend/src/main.tsx` - Standard React entry point

---

## Phase 5: Tauri Configuration

### 5.1 Configure Tauri for Desktop (PC Version)

Create `lesson-plan-browser/frontend/src-tauri/tauri.conf.json`:

**Required permissions:**
- File system read access (for JSON file detection)
- Network access (for backend API)
- All permissions needed for Lesson Mode

**Configuration:**
- Copy base structure from main app's `tauri.conf.json`
- Update app identifier: `com.lessonplanner.browser`
- Update app name: "Lesson Plan Browser"
- Remove unused plugins (keep only essentials)

### 5.2 Configure Tauri for Android

Update Android configuration:
- Set up Android permissions in `tauri.conf.json`
- Network access for WiFi sync (temporary connection only)
- File system access for local JSON files
- Storage access for local database
- Database access via Tauri commands

---

## Phase 6: Testing & Validation (PC Version)

### 6.1 Test Browser Functionality

**Test cases:**
1. Week selection displays correctly
2. Week view loads and shows lessons
3. Day view works correctly
4. Lesson detail view displays correctly
5. Navigation between views works
6. Can read lesson plans from database (via HTTP API)
7. Can read lesson plans from JSON files (via `getRecentWeeks`)
8. Both data sources appear in week selector
9. Refresh button works (clears cache, reloads data)
10. Plan detail loads with `lesson_json`

### 6.2 Test Lesson Mode Functionality

**Test cases:**
1. Enter Lesson Mode from Lesson Detail View
2. Step navigation works (previous/next)
3. Timer functions correctly
4. Session state saves and restores
5. Resources display correctly
6. Timer adjustments work
7. Exit Lesson Mode returns to browser
8. Auto-advance works (if enabled)
9. Live mode detection works (within 30 mins of slot time)

### 6.3 Integration Testing

**Test cases:**
1. Navigate: Browser → Lesson Detail → Lesson Mode → Browser
2. Session persists when switching views
3. Plan data loads correctly from both sources
4. Performance is acceptable (no lag, fast navigation)

---

## Phase 7: Android Build Configuration

### 7.1 Update Tauri Config for Android

Update `lesson-plan-browser/frontend/src-tauri/tauri.conf.json`:

**Android-specific settings:**
- Bundle identifier: `com.lessonplanner.browser`
- Minimum SDK version
- Target SDK version
- Permissions: Internet (for WiFi sync only), Storage, etc.
- Database access permissions

### 7.2 Build Scripts

Create build scripts:
- `lesson-plan-browser/build-android.ps1` - Build Android APK
- `lesson-plan-browser/build-pc.ps1` - Build PC executable

### 7.3 Test Android Build (Skeleton)

**Build process:**
1. Test build on emulator first
2. Verify APK generation succeeds
3. Test APK installation
4. Verify app launches without errors

**Note:** Full functionality requires Phase 9 (Standalone Architecture)

---

## Phase 8: Optimize Bundle Size

### 8.1 Remove Unused Dependencies

**Check package.json:**
- Remove batch processing dependencies
- Remove schedule editing dependencies
- Keep only browser and Lesson Mode dependencies

### 8.2 Code Splitting

**Optimizations:**
- Lazy load Lesson Mode components (only when needed)
- Optimize bundle size for Android

---

## Phase 9: Android Standalone Architecture (REQUIRED)

**CRITICAL:** This phase is REQUIRED for Android version. The tablet MUST work independently with local storage.

### 9.1 Local Database Implementation (Android)

**Requirements:**
- Embedded SQLite database on tablet (via Tauri)
- Same schema as main app's database
- Read lesson plans from local database
- Store lesson mode sessions locally

**Implementation Steps:**

1. **Create Database Schema:**
   - Copy migrations from main app (`frontend/src-tauri/migrations/`)
   - Create local database initialization logic
   - **Core tables (Phase 1):** `users`, `class_slots`, `weekly_plans`, `schedule_entries`
   - **Lesson Mode tables (Phase 9):** `lesson_steps`, `lesson_mode_sessions`
   - **Note:** Core tables are created in Phase 1. Lesson Mode tables (`lesson_steps`, `lesson_mode_sessions`) will be added in Phase 9 when implementing standalone architecture

2. **Add Lesson Mode Migration Files:**
   - Create `005_lesson_steps.sql` - Migration for lesson steps table
   - Create `006_lesson_mode_sessions.sql` - Migration for lesson mode sessions table
   - Update `db_commands.rs` to run these migrations in `run_migrations()` function
   - Tables needed for Lesson Mode:
     - `lesson_steps` - Stores lesson step data (step_number, duration, content, etc.)
     - `lesson_mode_sessions` - Stores lesson mode session state (current step, timer, etc.)

3. **Implement Local Database Queries:**
   - Use existing Tauri commands (`sql_query`, `sql_execute` - already in main app)
   - Implement local database queries for:
     - `listPlans()` - Query local database for lesson plans
     - `getPlanDetail()` - Get plan detail from local database
     - `getSchedule()` - Get schedule entries from local database
     - `getSlots()` - Get class slots from local database
     - `getLessonSteps()` - Get lesson steps from local database (requires lesson_steps table)
     - `getActiveSession()` - Get active lesson mode session (requires lesson_mode_sessions table)
     - `createSession()` - Create/update lesson mode session (requires lesson_mode_sessions table)
     - `endSession()` - End lesson mode session (requires lesson_mode_sessions table)

3. **Update API Client for Standalone Mode:**
   - When `isStandaloneMode()` returns true, use local database queries
   - Route all data access through local database instead of HTTP API
   - Maintain same API interface for components (transparent switch)

### 9.2 Local JSON File Storage (Android)

**Requirements:**
- Store JSON lesson plan files locally on tablet
- Read from local file system (not PC's file system)
- Detect weeks from local JSON files

**Implementation Steps:**

1. **Local File Storage Setup:**
   - Determine local storage directory for JSON files (app's data directory)
   - Create directory structure for storing lesson plan JSON files
   - Implement file system access via Tauri commands

2. **JSON File Management:**
   - `storeJsonFile()` - Save JSON file to local storage
   - `readJsonFile()` - Read JSON file from local storage
   - `listJsonFiles()` - List available JSON files (for week detection)
   - `getRecentWeeks()` - Scan local JSON files and return available weeks

3. **Week Detection:**
   - Parse JSON file names or contents to detect weeks
   - Return week list similar to backend `getRecentWeeks()` endpoint

### 9.3 Sync Mechanism Implementation

**WiFi Sync (Primary):**

**Implementation Steps:**

1. **Sync UI:**
   - Add sync button in browser UI
   - Add sync status indicator
   - Add sync settings (PC IP address configuration)

2. **Sync Process:**
   - Connect to PC backend via WiFi (temporary connection)
   - Fetch plans from PC backend API:
     - `GET /api/plans` → Save to local database
     - `GET /api/plans/{id}/detail` → Save lesson_json to local database
   - Fetch JSON files from PC backend:
     - `GET /api/users/{id}/recent-weeks` → Get JSON file paths
     - Download JSON files → Save to local storage
   - Fetch schedules:
     - `GET /api/schedule/{user_id}/{day}` → Save to local database
   - Fetch slots:
     - `GET /api/users/{id}/slots` → Save to local database
   - After sync completes: Disconnect, app uses local data

3. **Error Handling:**
   - Handle network errors gracefully
   - Allow partial sync (continue even if some requests fail)
   - Show sync progress and status

**USB Sync (Fallback):**

**Implementation Steps:**

1. **Import UI:**
   - Add import button in app settings
   - Allow user to select database file and JSON files for import

2. **Import Process:**
   - Read database file from accessible storage location
   - Import database schema and data into local database
   - Copy JSON files to local storage directory
   - Verify import succeeded
   - Refresh app to show imported data

3. **Export Script (PC-side):**
   - Create script to export database and JSON files from PC
   - Prepare files for USB transfer
   - Document transfer process

### 9.4 Testing Standalone Architecture

**Test cases:**

1. **Local Database:**
   - Verify database created on tablet
   - Verify plans read from local database (not backend)
   - Verify lesson mode sessions stored locally
   - Verify data persists across app restarts

2. **Local JSON Files:**
   - Verify JSON files stored locally
   - Verify weeks detected from local JSON files
   - Verify plan detail loads from local JSON

3. **WiFi Sync:**
   - Connect to PC backend via WiFi
   - Sync new lesson plans from PC
   - Verify plans appear in tablet app after sync
   - Disconnect from network, verify app still works offline

4. **USB Sync:**
   - Export database and JSON files from PC
   - Transfer via USB
   - Import to tablet
   - Verify plans appear in tablet app

5. **Offline Operation:**
   - Disconnect from network
   - Verify browser works (reads from local database)
   - Verify Lesson Mode works (saves sessions locally)
   - Verify all features work without network

---

## Implementation Dependencies

### Components & Files to Copy

**From `frontend/src/components/`:**
- `LessonPlanBrowser.tsx`
- `WeekView.tsx`
- `DayView.tsx`
- `LessonDetailView.tsx`
- `LessonMode.tsx`
- `TimelineSidebar.tsx`
- `CurrentStepInstructions.tsx`
- `ResourceDisplayArea.tsx`
- `TimerAdjustmentDialog.tsx`
- `TimerDisplay.tsx`
- `StepNavigation.tsx`
- All UI components from `ui/`
- Resource display components from `resources/`

**From `frontend/src/lib/`:**
- `api.ts` (modified - dual mode implementation)
- `config.ts`

**From `frontend/src/utils/`:**
- `scheduleEntries.ts`
- `planMatching.ts`
- `planIdResolver.ts`
- `lessonStepRecalculation.ts`

**From `frontend/src/hooks/`:**
- `useLessonTimer.ts`

**From `frontend/src/store/`:**
- `useStore.ts` (may need simplification)

**From `frontend/src-tauri/src/`:**
- Database commands (`sql_query`, `sql_execute`) - already exist in main app
- File system commands for local JSON storage

**From `frontend/src-tauri/migrations/`:**
- Database migration files (for local database schema)

---

## Key Implementation Notes

### Data Source Architecture

**CRITICAL: Standalone Offline Architecture for Android**

The Android tablet version MUST work independently with local storage:
- **Tablet has its OWN database** (local SQLite/Room database, NOT connecting to PC backend for daily use)
- **Tablet has its OWN JSON files** (local file storage, NOT accessing PC's file system)
- **Completely offline after sync** (works without network at school)
- **Sync happens separately** (WiFi or USB) to populate local storage

**PC Version (Development/Testing):**
- Can connect to backend API (localhost:8000) for development/testing
- Uses HTTP backend for data access
- This is for development convenience only

**Android Version (Production):**
- **MUST use local database** - Embedded SQLite via Tauri on tablet
- **MUST use local JSON files** - Files stored on tablet's file system
- **MUST work offline** - No network connection required after initial sync
- Sync mechanism (WiFi/USB) copies data FROM PC TO tablet's local storage

**Sync Architecture (Android Only):**

**WiFi Sync (Primary):**
- Tablet connects to PC backend via WiFi (for sync only, not for daily use)
- Sync button in app: Fetches plans from PC backend → Saves to local database
- After sync: Disconnect from network, app uses local data

**USB Sync (Fallback):**
- Copy database file from PC → Transfer via USB → Import to tablet's local database
- Copy JSON files from PC → Transfer via USB → Save to tablet's local storage
- After sync: App uses local data, no network needed

**Refresh mechanism (Android):**
- Refresh button triggers sync (WiFi) or file import (USB)
- After sync, data stored locally
- App then reads from local database/files (offline)

### Navigation Flow

1. **Browser → Lesson Detail:**
   - User clicks lesson in Week/Day view
   - `handleLessonClick()` loads plan detail from local database
   - Shows `LessonDetailView`

2. **Lesson Detail → Lesson Mode:**
   - User clicks "Enter Lesson Mode" button
   - `onEnterLessonMode()` callback triggered
   - Switches to Lesson Mode view

3. **Lesson Mode → Browser:**
   - User clicks exit/back button
   - `onExit()` callback triggered
   - Returns to Browser view

### Component Integration

**LessonPlanBrowser integration:**
- Already supports `onEnterLessonMode` prop
- No changes needed to component itself
- API client handles mode detection transparently

**LessonMode integration:**
- Already supports props: `scheduleEntry`, `planId`, `day`, `slot`
- Supports `onExit` callback
- No changes needed to component itself
- API client handles local database access transparently

---

## Success Criteria

### PC Version
- [x] Standalone app builds and runs
- [x] Browser works identically to main app
- [x] Can browse plans from database (via HTTP API)
- [x] Can browse plans from JSON files (via `getRecentWeeks`)
- [x] Refresh button works correctly
- [x] Lesson Mode fully functional
- [x] Navigation between browser and Lesson Mode works
- [x] All teaching features work (timers, sessions, steps)

### Android Version
- [x] APK builds successfully
- [x] App installs on tablet
- [x] App launches without errors
- [x] **Uses local embedded SQLite database** (not connecting to PC backend for daily use)
- [x] **Uses local JSON file storage** (not accessing PC files)
- [x] **Works completely offline** (after sync, no network required)
- [x] All browser features work (reading from local database/files)
- [x] All Lesson Mode features work (storing sessions locally)
- [x] **WiFi sync works** (fetch from PC backend → save to local storage)
- [x] **USB sync works** (import database/JSON files → local storage)
- [x] **New lesson plans appear after sync** (PC → Tablet)
- [x] **Updated plans appear after sync**
- [x] Performance acceptable on tablet
- [x] Touch interactions work smoothly

---

## Estimated Effort

- **Phase 1 (Project Structure):** 2-3 hours
- **Phase 2 (Copy Components):** 3-4 hours
- **Phase 3 (API Client - Dual Mode):** 3-4 hours
- **Phase 4 (App Entry Point):** 2-3 hours
- **Phase 5 (Tauri Config):** 1-2 hours
- **Phase 6 (PC Testing):** 4-6 hours
- **Phase 7 (Android Build):** 3-4 hours
- **Phase 8 (Optimization):** 2-3 hours
- **Phase 9 (Standalone Architecture):** 8-12 hours
  - Local database implementation: 3-4 hours
  - Local JSON file storage: 2-3 hours
  - Sync mechanism (WiFi + USB): 3-5 hours

**Total: 28-43 hours**

**Note:** Phase 9 (Standalone Architecture) is essential for Android version. The tablet MUST work independently with local storage, not connecting to PC backend for daily use.

---

## Risk Mitigation

### Missing Dependencies
- **Risk:** Component dependencies not copied
- **Mitigation:** Systematic audit of all imports, copy all referenced components

### API Compatibility
- **Risk:** Backend endpoints may change
- **Mitigation:** Reuse existing backend, maintain endpoint compatibility

### Performance on Tablet
- **Risk:** Timer performance issues on Android
- **Mitigation:** Test thoroughly, optimize if needed, use efficient timer implementation

### Build Time
- **Risk:** Android build takes too long
- **Mitigation:** Exclude unused code, optimize dependencies, test incrementally

### Standalone Architecture Complexity
- **Risk:** Local database implementation may have issues
- **Mitigation:** Reuse existing Tauri database commands from main app, test thoroughly, implement proper error handling

### Sync Reliability
- **Risk:** WiFi sync may fail in some network environments
- **Mitigation:** Implement USB sync as reliable fallback, handle errors gracefully, allow partial syncs

---

## Implementation Order Summary

1. **Phase 1-5:** Setup project and copy components (PC version)
2. **Phase 6:** Test PC version with HTTP backend
3. **Phase 7:** Configure Android build
4. **Phase 8:** Optimize bundle size
5. **Phase 9:** Implement standalone architecture (REQUIRED for Android)
   - Local database
   - Local JSON storage
   - Sync mechanism
6. **Final Testing:** Verify Android version works offline and sync works

**Critical Path:** Phases 9 must be completed for Android version to meet requirements. PC version can work with HTTP backend, but Android version MUST use standalone architecture.

