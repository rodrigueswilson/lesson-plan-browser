# Future Session Planning Document

## Overview

This document outlines the planned work for future sessions to address codebase organization, create a streamlined Android version, and improve the installation experience.

**Note:** You mentioned planning four steps, but only three were provided. The fourth step can be added when you're ready.

---

## Step 1: Declutter the Codebase ✅ COMPLETED

**Status:** This step has already been implemented according to the existing `decluttering_plan.md`.

### Objective
Adapt and execute the existing decluttering system using industry best practices to organize the codebase and reduce root-level clutter.

### Current State
- Existing decluttering plan documented in `decluttering_plan.md`
- ~200+ files scattered at root level (diagnostic scripts, test files, documentation)
- Organized structure partially defined but not yet implemented

### Approach
1. **Review and Enhance Existing Plan**
   - Review `decluttering_plan.md` for completeness
   - Identify any gaps or improvements needed
   - Ensure alignment with DRY, KISS, and SOLID principles
   - Validate that the plan follows Single Source of Truth (SSOT) for file organization

2. **Phase 1: Foundation (Low Risk)**
   - Create organizational structure:
     - `tools/diagnostics/` - Diagnostic scripts
     - `tools/maintenance/` - Maintenance utilities
     - `tools/utilities/` - Reusable helpers
     - `docs/archive/` - Historical documentation
     - `docs/maintenance/` - Maintenance documentation
   - Create inventory automation script
   - Document decision criteria and audit procedures

3. **Phase 2: Move Diagnostic Scripts (Low Risk)**
   - Audit all consumers of `check_*.py`, `analyze_*.py`, `fix_*.py`, `debug_*.py` scripts
   - Move scripts to appropriate `tools/` subdirectories
   - Update all references (`.bat` files, imports, documentation, CI/CD)
   - Create wrapper scripts if needed for backward compatibility
   - Verify all batch files still work

4. **Phase 3: Consolidate Test Files (Medium Risk)**
   - Validate pytest configuration
   - Move root-level `test_*.py` files to `tests/`
   - Organize tests by category (unit, integration, e2e)
   - Fix imports and paths
   - Verify test suite runs successfully

5. **Phase 4: Archive Documentation (Low Risk)**
   - Distinguish feature docs (keep active) vs planning/implementation docs (archive)
   - Audit all inbound links to documentation
   - Move completed docs to `docs/archive/` subdirectories
   - Fix broken links
   - Create archive index

6. **Subsequent Phases**
   - Clean up backup files
   - Consolidate duplicate files
   - Create maintenance documentation
   - Remove obsolete files (high risk, careful review)

### Success Criteria
- Root directory reduced from ~200+ files to <50 essential files
- All scripts organized in `tools/` hierarchy
- All tests in `tests/` with proper organization
- Historical documentation archived but accessible
- All references updated and verified
- Test suite passes after reorganization

### Estimated Effort
- Phase 1: 2-3 hours
- Phase 2: 4-6 hours
- Phase 3: 3-4 hours
- Phase 4: 3-4 hours
- Subsequent phases: 4-6 hours
- **Total: 16-23 hours**

### Dependencies
- Git commits before major moves
- Test suite validation
- Reference audit completion

---

## Step 2: Plan Smaller Android Version (Lesson Plan Browser with Lesson Mode)

### Objective
Create a streamlined Android version that includes the full lesson plan browser functionality AND fully functional Lesson Mode for teaching. The browser must be identical to the main app's browser, capable of browsing lesson plans from both the database and JSON files, and allow teachers to review, navigate, and use Lesson Mode while teaching or accessing lessons before/after delivery.

### Current State
- Full desktop app with multiple features (batch processing, schedule management, lesson generation, etc.)
- Lesson Plan Browser component exists (`frontend/src/components/LessonPlanBrowser.tsx`)
- Lesson Mode component exists (`frontend/src/components/LessonMode.tsx`)
- Browser already supports both database and JSON file access
- Android build infrastructure already in place (`frontend/android/`, `frontend/src-tauri/`)
- Tauri v2 with Android support configured

### Key Requirements
1. **Browser must be identical to main app** - Same functionality, same data sources
2. **Dual data source support** - Read from both:
   - Database (via API: `planApi.list()`, `lessonApi.getPlanDetail()`)
   - JSON files (via `userApi.getRecentWeeks()` which detects folders with lesson plan files)
3. **Full Lesson Mode functionality** - Complete teaching interface with:
   - Lesson steps with timers
   - Instructions and resources display
   - Session state saving
   - Step navigation
   - Timer adjustments
   - Live mode (synced with schedule) and preview mode

### Approach

#### 2.1 Create Standalone PC Version (Browser + Lesson Mode)

**Architecture Decision:**
- Extract `LessonPlanBrowser` and `LessonMode` into a standalone application
- Keep all browser functionality identical to main app
- Keep all Lesson Mode functionality for teaching
- Create minimal backend API endpoints (read-only for lesson plans, read-write for lesson mode sessions)
- Remove dependencies on:
  - Batch processing
  - Schedule input/editing
  - Lesson generation
  - Analytics (optional - can be kept if needed)
  - User management (keep minimal - just user selection)

**Implementation Steps:**

1. **Create New Project Structure**
   ```
   lesson-plan-browser/
   ├── frontend/              # React + Tauri app
   │   ├── src/
   │   │   ├── components/
   │   │   │   ├── LessonPlanBrowser.tsx  # Core browser component (same as main app)
   │   │   │   ├── LessonMode.tsx         # Full lesson mode component
   │   │   │   ├── WeekView.tsx
   │   │   │   ├── DayView.tsx
   │   │   │   ├── LessonDetailView.tsx
   │   │   │   ├── TimelineSidebar.tsx    # For lesson mode
   │   │   │   ├── CurrentStepInstructions.tsx
   │   │   │   ├── ResourceDisplayArea.tsx
   │   │   │   ├── TimerAdjustmentDialog.tsx
   │   │   │   └── ui/                    # UI components
   │   │   ├── lib/
   │   │   │   └── api.ts                  # API client (read-only + lesson mode endpoints)
   │   │   ├── hooks/
   │   │   │   └── useLessonTimer.ts       # Timer hook for lesson mode
   │   │   ├── utils/                      # Utilities
   │   │   │   ├── scheduleEntries.ts
   │   │   │   ├── planMatching.ts
   │   │   │   ├── planIdResolver.ts
   │   │   │   └── lessonStepRecalculation.ts
   │   │   └── store/
   │   │       └── useStore.ts             # State management
   │   └── src-tauri/                      # Tauri configuration
   ├── backend/                            # Minimal FastAPI backend
   │   ├── api.py                          # API endpoints
   │   ├── database.py                     # Database access
   │   └── models.py                       # Data models
   └── README.md
   ```

2. **Identify Required Components (Full List)**

   **Browser Components:**
   - `LessonPlanBrowser.tsx` - Main browser (copy unchanged from main app)
   - `WeekView.tsx` - Week view
   - `DayView.tsx` - Day view  
   - `LessonDetailView.tsx` - Lesson detail view
   - All UI components (`Button`, `Select`, `Card`, etc.)

   **Lesson Mode Components:**
   - `LessonMode.tsx` - Main lesson mode (copy unchanged from main app)
   - `TimelineSidebar.tsx` - Step timeline sidebar
   - `CurrentStepInstructions.tsx` - Step instructions panel
   - `ResourceDisplayArea.tsx` - Resources display
   - `TimerAdjustmentDialog.tsx` - Timer adjustment dialog

   **Required Dependencies:**
   - API calls: 
     - Browser: `planApi.list()`, `lessonApi.getPlanDetail()`, `scheduleApi.getSchedule()`, `userApi.getRecentWeeks()`
     - Lesson Mode: `lessonApi.getLessonSteps()`, `lessonApi.generateLessonSteps()`, `lessonModeSessionApi.getActive()`, `lessonModeSessionApi.create()`, `lessonModeSessionApi.end()`
   - Store: `currentUser`, `slots`
   - Utilities: `dedupeScheduleEntries`, `normalizeSubject`, `findPlanSlotForEntry`, `resolvePlanIdFromScheduleEntry`, `recalculateStepDurations`
   - Hooks: `useLessonTimer`

3. **Create Backend API Endpoints**

   **Read-Only Endpoints (Browser):**
   - `GET /api/plans` - List lesson plans (from database)
   - `GET /api/plans/{plan_id}/detail` - Get plan detail (includes `lesson_json`)
   - `GET /api/schedule/{user_id}/{day}` - Get schedule entries
   - `GET /api/users/{user_id}/recent-weeks` - Get available weeks (detects JSON files in folders)
   - `GET /api/users/{user_id}/slots` - Get class slots (for enrichment)

   **Read-Write Endpoints (Lesson Mode):**
   - `GET /api/lesson-steps/{plan_id}/{day}/{slot}` - Get lesson steps
   - `POST /api/lesson-steps/{plan_id}/{day}/{slot}/generate` - Generate lesson steps
   - `GET /api/lesson-mode-sessions/active` - Get active session
   - `POST /api/lesson-mode-sessions` - Create/update session
   - `POST /api/lesson-mode-sessions/{session_id}/end` - End session

   **Data Source Support:**
   - Database: Plans stored with `lesson_json` field
   - JSON Files: Read from file system via folder detection (`getRecentWeeks` endpoint scans folders)
   - Both sources must be accessible and browsable
   - **Data Synchronization:** The app will read fresh data on each refresh/API call:
     - Database: New plans and updates appear when `planApi.list()` is called (no caching beyond 30 seconds)
     - JSON Files: New files detected when `getRecentWeeks()` scans folders (scans on each call)
     - Refresh button available in browser UI to manually reload data
     - Cache duration: 30 seconds (refresh button bypasses cache)

4. **Copy Components (No Simplification)**
   - Copy `LessonPlanBrowser.tsx` **unchanged** (keep all features including `onEnterLessonMode`)
   - Copy `LessonMode.tsx` **unchanged** (keep all teaching features)
   - Copy all dependent components unchanged
   - Copy all utilities and hooks unchanged
   - Ensure `LessonDetailView` properly calls `onEnterLessonMode` to launch Lesson Mode

5. **Data Source Integration**
   - Ensure browser can read from both:
     - **Database**: Plans via API endpoints (already supported)
     - **JSON Files**: Via `getRecentWeeks` API which detects folders containing lesson plan JSON files
   - Maintain same data access logic as main app
   - Both sources should appear in week selector dropdown
   - **Data Refresh Capability (PC → Tablet):**
     - Browser includes refresh button (already in `LessonPlanBrowser.tsx`)
     - **Workflow**: Teacher adds lesson plans on PC → Tablet connects to PC's backend via WiFi → Refresh on tablet → New plans appear
     - Tablet accesses same database as PC (via network connection)
     - Refresh reloads both database plans and scans for new JSON files from PC
     - Cache mechanism (30 seconds) prevents excessive API calls but refresh bypasses cache
     - New lesson plans added on PC database will appear on tablet after refresh
     - New JSON files added on PC will be detected on tablet after refresh
     - Plan updates on PC will be reflected on tablet after refresh

6. **Data Synchronization and Updates (PC → Tablet Workflow)**

   **Architecture: Standalone Offline Tablet App with Dual Sync Options**
   
   - **Tablet app has its OWN database and JSON files** (local storage, NOT connecting to PC backend)
   - **Completely offline** after sync (works without network at school)
   - **Two Sync Methods Available:**
   
   **Option A: WiFi Sync (Primary)**
     - Tablet connects to PC's backend via WiFi network (same local network)
     - Sync process: Tablet app fetches data from PC backend → Saves to local database and JSON files
     - Real-time or on-demand sync via refresh button
     - **Works even with T-Mobile router** (connection appears possible)
     - **Advantages:** Convenient, no cable needed, can sync at school if PC is accessible
     - **Limitations:** Requires WiFi connection, PC backend must be running
   
   **Option B: USB Sync (Reliable Fallback)**
     - Database file copied from PC to tablet via USB connection
     - JSON files copied from PC to tablet via USB connection
     - Tablet uses local embedded SQLite database (Room/SQLite on Android)
     - Sync process: Copy database + JSON files from PC → Transfer via USB → Replace tablet's local files
     - Requires: ADB or file transfer mode via USB cable
     - **Advantages:** More reliable, doesn't depend on network/router, guaranteed to work
     - **Use when:** WiFi unavailable, router blocks connection, or network issues
   
   **Why Standalone Architecture:**
   - Tablet needs offline access to lesson plans (no network connection required at school after sync)
   - Reliable offline operation for teaching
   - Fast, no network latency during use
   - Works anywhere without network dependency (after sync)
   - Dual sync options provide flexibility and reliability

   **Workflow - How New Lesson Plans Reach Tablet:**

   **WiFi Sync Workflow (Primary):**
   1. **At Home/Office (PC):**
      - Teacher creates/adds lesson plans using main PC app
      - Plans saved to database on PC
      - Plans also saved as JSON files in folders
      - PC backend running and accessible on network
   
   2. **At School or Home (Tablet - WiFi Sync):**
      - Tablet connects to same WiFi network as PC (T-Mobile router)
      - Tablet app connects to PC's backend API (`http://PC_IP_ADDRESS:8000/api`)
      - Teacher opens tablet app and taps refresh/sync button
      - Tablet app fetches:
        - Database updates (new/updated lesson plans) → Saves to local Room database
        - JSON files updates → Saves to local JSON file storage
      - Sync completes, data stored locally on tablet
      - **If WiFi sync fails:** Use USB sync as fallback
   
   3. **At School (Tablet - Offline Mode after Sync):**
      - Tablet uses local embedded database (already synced via WiFi or USB)
      - Tablet uses local JSON files (already synced)
      - All lesson plans available offline
      - No network connection required at school (app works offline)
      - App works completely independently

   **USB Sync Workflow (Reliable Fallback):**
   1. **At Home/Office (PC):**
      - Teacher creates/adds lesson plans using main PC app
      - Plans saved to database on PC (SQLite file)
      - Plans also saved as JSON files in folders
      - Prepare files for transfer:
        - Database file: `data/lesson_planner.db` (or similar path)
        - JSON files: All lesson plan JSON files from folders
   
   2. **Sync Process (USB Transfer):**
      - Connect tablet to PC via USB cable
      - Enable USB debugging on tablet (for ADB) OR USB file transfer mode
      - **Option A - ADB (recommended):**
        - Use ADB to push database file: `adb push <db_file> /data/data/com.lessonplanner.bilingual/databases/`
        - Copy JSON files to tablet's accessible storage folder
      - **Option B - File Transfer Mode:**
        - Copy database file and JSON files to tablet's accessible storage
        - Use app's import function to load files
      - Verify files transferred successfully
      - Restart tablet app to load new database and JSON files
   
   3. **At School (Tablet - Offline Mode after Sync):**
      - Tablet uses local embedded database (already synced via USB)
      - Tablet uses local JSON files (already synced via USB)
      - All lesson plans available offline
      - No network connection required at school
      - App works completely independently

   **How Updates Reach Tablet:**
   
   **WiFi Sync Process (Primary):**
     - **Database updates**: New lesson plans added on PC:
       - Tablet connects to PC backend via WiFi
       - Tablet app fetches new/updated plans from PC backend API
       - Plans saved to tablet's local Room database
       - All new plans and updates available on tablet after sync
     - **JSON file updates**: New JSON files added on PC:
       - Tablet app fetches JSON files from PC backend (via `getRecentWeeks` endpoint)
       - Files saved to tablet's local JSON storage
       - New files detected and appear in tablet's week selector
     - **Plan updates**: Existing plans updated on PC:
       - Updated data fetched from PC backend via WiFi
       - All changes saved to tablet's local storage
     - **Sync Frequency**: Real-time or on-demand via refresh button in tablet app
     - **Sync Process**: Automatic or manual refresh in tablet app (no cable needed)
     - **Offline Access**: Tablet works completely offline after sync - no network required at school
     - **Fallback**: If WiFi fails, use USB sync instead
   
   **USB Sync Process (Reliable Fallback):**
     - **Database updates**: New lesson plans added on PC:
       - Database file updated on PC
       - Copy updated database file to tablet via USB
       - Replace tablet's local database with new file
       - All new plans and updates available on tablet
     - **JSON file updates**: New JSON files added on PC:
       - Copy new/updated JSON files to tablet via USB
       - Replace or merge JSON files on tablet
       - New files detected and appear in tablet's week selector
     - **Plan updates**: Existing plans updated on PC:
       - Updated database/JSON files copied to tablet
       - All changes reflected on tablet after sync
     - **Sync Frequency**: As needed (weekly, daily, or whenever plans are updated)
     - **Sync Process**: Manual USB transfer or automated sync script
     - **Offline Access**: Tablet works completely offline after sync - no network required
     - **Reliability**: Guaranteed to work regardless of network/router issues

   **Network Requirements (WiFi Sync):**
   - PC and tablet must be on same WiFi network
   - PC backend must be running and accessible (port 8000)
   - T-Mobile router must allow local device-to-device communication (appears possible)
   - Backend API accessible at `http://PC_IP:8000/api`
   - **Fallback:** Use USB sync if WiFi unavailable or connection fails

   **USB Requirements (USB Sync):**
   - USB cable connection between PC and tablet
   - USB debugging enabled on tablet (for ADB) OR USB file transfer mode
   - Access to tablet's app data directory (for ADB) OR accessible storage folder
   - Database file location on PC identified
   - JSON files location on PC identified
   - Sync script/tool to automate transfer process (optional but recommended)

7. **Create Tauri Config**
   - Keep file system read access (for JSON file detection)
   - Keep network access for backend API
   - Keep all permissions needed for Lesson Mode

8. **Testing on PC**
   - Test browser with database plans
   - Test browser with JSON file plans
   - Test refresh functionality:
     - Add new plan to database, verify refresh shows it
     - Add new JSON file to folder, verify refresh detects it
     - Update existing plan, verify refresh shows updates
   - Test Lesson Mode entry from LessonDetailView
   - Test all Lesson Mode features:
     - Step navigation
     - Timer functionality
     - Session saving
     - Resource display
     - Timer adjustments
   - Verify navigation between browser and Lesson Mode
   - Performance testing

#### 2.2 Compile for Android

**After PC version is working:**

1. **Android Configuration**
   - Use existing Tauri Android build setup
   - Configure `tauri.conf.json` for Android
   - Set up Android-specific permissions:
     - Network access (for API)
     - File system read access (for JSON files)
     - Storage access (if needed for session data)

2. **Build Process**
   - Test build process
   - Verify APK generation
   - Test on Android emulator first
   - Optimize bundle size (remove only unused dependencies, keep all browser/lesson mode code)

3. **Android-Specific Considerations**
   - Touch interactions (already handled by React components)
   - Screen size adaptation (responsive design for tablet)
   - Network connectivity handling
   - File system access for JSON files
   - Performance optimization for lesson mode timers
   - Battery impact considerations

### Success Criteria
- Standalone PC version works independently
- Browser identical to main app (week/day/lesson views, navigation)
- Browser reads from both database AND JSON files
- **Data synchronization works (both methods):**
  - **WiFi sync:** Tablet can connect to PC backend and fetch updates (even with T-Mobile router)
  - **USB sync:** Database and JSON files can be transferred via USB as reliable fallback
  - New lesson plans added to database are accessible after sync (WiFi or USB)
  - New JSON files added to folders are detected after sync
  - Updates to existing plans are reflected after sync
  - Both sync methods save data locally for offline access
- Lesson Mode fully functional (all features working)
- Enter Lesson Mode from browser works correctly
- Navigation between browser and Lesson Mode works
- Android build successful
- APK installs and runs on tablet
- Performance acceptable on Android device
- Teachers can use it for teaching (review plans, enter lesson mode, deliver lessons)
- Teachers can access newly added/updated lesson plans on tablet

### Estimated Effort
- PC version creation: 12-16 hours (more complex due to Lesson Mode integration)
- Android compilation and testing: 6-8 hours
- **Total: 18-24 hours**

### Dependencies
- Step 1 completion (cleaner codebase will make extraction easier)
- Existing database/API structure
- Existing JSON file structure and folder detection logic
- Android development environment
- **Network Setup:**
  - PC backend must be running and accessible
  - PC and tablet must be on same WiFi network
  - PC's IP address configured in tablet app (or auto-detected)
  - Backend API accessible at `http://PC_IP:8000/api`

### Technical Decisions Needed
1. **Database Access:** 
   - Option A: Browser connects to same backend API (requires backend running)
   - Option B: Browser has embedded SQLite (simpler deployment, but data sync needed)
   - **Recommendation:** Option A initially (maintains consistency with main app), Option B for future offline support

2. **JSON File Access:**
   - Option A: Continue using `getRecentWeeks` API endpoint that scans folders
   - Option B: Direct file system access via Tauri commands
   - **Recommendation:** Option A (maintains consistency, already working)

3. **User Management:**
   - Option A: Keep user selection (if multiple users)
   - Option B: Single user mode (simpler)
   - **Recommendation:** Option A (maintains compatibility with existing data structure)

4. **Lesson Mode Session Storage:**
   - Option A: Store in backend database (requires backend)
   - Option B: Store locally in SQLite (offline support)
   - **Recommendation:** Option A initially (same as main app), Option B for future offline support

5. **Backend Deployment & Synchronization:** ✅ **DECIDED**
   - **Architecture: Standalone Offline Tablet App** (Dual Sync: WiFi Primary + USB Fallback)
     - Tablet app has its OWN database and JSON files (local storage, NOT connecting to PC backend for daily use)
     - Tablet uses local embedded SQLite database (Room/SQLite on Android)
     - Completely offline after sync - no network connection required at school
     
     - **WiFi Sync Process (Primary):**
       - Tablet connects to PC backend via WiFi network
       - Fetches data from PC backend API → Saves to local Room database and JSON storage
       - Real-time or on-demand sync via refresh button
       - Works even with T-Mobile router (connection appears possible)
       - Convenient, no cable needed
     
     - **USB Sync Process (Reliable Fallback):**
       - Copy database file from PC to tablet via USB
       - Copy JSON files from PC to tablet via USB
       - Sync process: Export DB + JSON files from PC → Transfer via USB (ADB or file transfer) → Import to tablet
       - More reliable, doesn't depend on network/router
       - Guaranteed to work regardless of network issues
   
   - **Why Standalone Architecture:**
     - App needs offline access to lesson plans (no network required at school after sync)
     - Reliable offline operation for teaching
     - Fast, no network latency during use
     - Works anywhere without network dependency (after sync)
     - Dual sync options provide flexibility and reliability
   
   - **Decision:** Dual Sync Mode (WiFi Primary + USB Fallback)
     - Implement local database (Room) on tablet
     - Implement local JSON file storage on tablet
     - **WiFi sync capability:** Connect to PC backend, fetch data, save locally
     - **USB sync capability:** Transfer database and JSON files via USB
     - Multiple users supported in local database
     - Both methods store data locally for offline access

---

## Step 3: Install and Test on Tablet

### Objective
Install the new Android app (browser with Lesson Mode) on the tablet and verify it works correctly in the classroom environment, including both browsing lesson plans and using Lesson Mode for teaching.

### Current State
- **Previous Issues (to address in new implementation):**
  - Compilation took 4+ hours because it included entire app (lesson plan generation, schedule, etc.)
  - Frontend didn't have access to users and lesson plans - app was unusable for its purpose
- Existing `install-app.bat` script available
- Tablet connection via ADB
- **Requirements:**
  - App must access lesson plans and navigate exactly as PC app
  - App must have access to users and lesson plans (must work for its intended purpose)
  - Build time must be reasonable (not 4+ hours)

### Approach

#### 3.1 Pre-Installation Preparation

1. **Verify Development Environment**
   - ADB installed and working
   - Tablet connected and recognized (`adb devices`)
   - Tablet architecture confirmed (arm64)
   - USB debugging enabled on tablet

2. **Build Clean APK (Optimized for Speed)**
   - Ensure clean build (no cached artifacts)
   - Verify APK architecture matches tablet (arm64)
   - **Optimize build:** Only include browser + Lesson Mode (exclude lesson plan generation, schedule editing, etc.)
   - **Goal:** Reduce build time from 4+ hours to reasonable duration
   - Check APK size (should be smaller than full app since it excludes generation features)
   - Verify APK signing
   - **Critical:** Ensure users and lesson plans are accessible (fix previous issue where frontend couldn't access data)

3. **Create Installation Script**
   - Update or create new installation script for browser with Lesson Mode app
   - Include diagnostic steps:
     - Device connection check
     - Architecture verification
     - Previous installation cleanup
     - APK file verification
     - Installation attempt
     - Verification
     - Launch test

#### 3.2 Installation Process

1. **Uninstall Previous Versions**
   - Remove any existing installations
   - Clear app data if needed
   - Verify removal

2. **Install New APK**
   - Use `adb install -r -d` for reinstall with downgrade allowed
   - Monitor installation output for errors
   - Verify installation success

3. **Verify Installation**
   - Check package installed: `adb shell pm list packages | grep lesson`
   - Verify app appears in app drawer
   - Check app permissions

#### 3.3 Testing on Tablet

1. **Basic Functionality Tests**
   - App launches successfully
   - User selection works (if applicable)
   - Week selection displays
   - Week view loads and displays lessons
   - Day view works
   - Lesson detail view displays correctly
   - Navigation between views works
   - Can read lesson plans from database
   - Can read lesson plans from JSON files
   - Both data sources appear in week selector

2. **Data Connectivity Tests**
   - Backend connection (required for API access)
   - Data loads correctly from database
   - Data loads correctly from JSON files
   - Week/plan data displays from both sources
   - Schedule entries load
   - Lesson details load
   - Lesson Mode session API connectivity
   - Lesson steps API connectivity
   - **Data Update Tests:**
     - Add new lesson plan to database, refresh app, verify it appears
     - Add new JSON file to folder, refresh app, verify it's detected
     - Update existing plan in database, refresh, verify changes appear
     - Verify refresh button works correctly
     - Test cache expiration (wait 30+ seconds, verify fresh data loads)

3. **Performance Tests**
   - App startup time
   - View switching speed
   - Data loading performance
   - Memory usage
   - Battery impact (if significant)

4. **User Experience Tests**
   - Touch interactions work smoothly
   - Text is readable on tablet screen
   - Navigation is intuitive
   - No crashes or freezes
   - Error handling (network issues, etc.)

5. **Lesson Mode Tests**
   - Enter Lesson Mode from lesson detail view
   - Step navigation works
   - Timer functions correctly
   - Session state saves and restores
   - Resources display correctly
   - Timer adjustments work
   - Exit Lesson Mode returns to browser

6. **Real-World Usage Test**
   - Use in actual classroom scenario
   - Test with real lesson plans
   - Verify all needed information is accessible
   - Check usability during teaching
   - Test Lesson Mode during actual lesson delivery
   - Verify smooth transition between browsing and teaching

#### 3.4 Troubleshooting

**Common Issues and Solutions:**

1. **Installation Failures**
   - Check ADB connection
   - Verify APK architecture matches device
   - Check for conflicting package names
   - Clear previous installations completely

2. **App Crashes**
   - Check logcat: `adb logcat | grep -i error`
   - Verify backend connectivity
   - Check database access
   - Verify API endpoints

3. **Performance Issues**
   - Check memory usage (especially during Lesson Mode with timers)
   - Optimize data loading
   - Reduce bundle size if needed (while keeping all browser/lesson mode features)
   - Profile app performance
   - Check timer performance in Lesson Mode

4. **Data Issues**
   - Verify backend is running
   - Check database connectivity
   - Verify JSON file access and folder detection
   - Verify API responses (both browser and lesson mode endpoints)
   - Check data format compatibility
   - Verify lesson steps can be generated/loaded

5. **Lesson Mode Specific Issues**
   - Check timer accuracy and performance
   - Verify session state saves correctly
   - Test step navigation smoothness
   - Check resource loading in Lesson Mode
   - Verify timer adjustments work correctly

### Success Criteria
- APK installs successfully on tablet
- App launches without errors
- All browser features work correctly (database and JSON file browsing)
- Lesson Mode fully functional on tablet
- Performance is acceptable (especially timer updates)
- App is usable in classroom environment for both reviewing and teaching
- No critical bugs or crashes
- Smooth navigation between browser and Lesson Mode

### Estimated Effort
- Preparation: 1-2 hours
- Installation: 1 hour
- Testing: 3-4 hours
- Troubleshooting (if needed): 2-4 hours
- **Total: 7-11 hours**

### Dependencies
- Step 2 completion (Android build ready)
- Tablet access
- Backend API running (if using API approach)
- Test data available

---

---

## Implementation Order

1. **Step 1: Declutter Codebase** ✅ **COMPLETED** (Already implemented)
2. **Step 2: Create Browser with Lesson Mode Version** (Build the new module with full functionality - standalone offline architecture)
3. **Step 3: Install and Test on Tablet** (Deploy and validate in classroom environment - optimize build time, ensure data access works)

---

## Risk Assessment

### Step 1 Risks
- **Low:** Breaking references when moving files
  - *Mitigation:* Comprehensive audit before moves, git commits, rollback procedure
- **Medium:** Test suite issues after reorganization
  - *Mitigation:* Validate pytest config, test after each phase

### Step 2 Risks
- **Medium:** Missing dependencies when extracting components (browser + Lesson Mode)
  - *Mitigation:* Careful dependency analysis of all components, thorough testing
- **Medium:** Lesson Mode complexity (timers, sessions, state management)
  - *Mitigation:* Copy components unchanged, test thoroughly on PC before Android build
- **Low:** Android build issues
  - *Mitigation:* Use existing Android setup, test incrementally
- **Low:** Bundle size increase due to Lesson Mode inclusion
  - *Mitigation:* Monitor APK size, optimize only non-essential dependencies

### Step 3 Risks
- **Low:** Installation issues (already experienced)
  - *Mitigation:* Improved installation script, better diagnostics
- **Medium:** Performance on tablet (especially Lesson Mode timers)
  - *Mitigation:* Performance testing, optimization if needed, test timer updates
- **Low:** Lesson Mode timer accuracy on Android
  - *Mitigation:* Test timer functionality thoroughly, verify background/foreground behavior

---

## Notes

- Each step should be completed and verified before moving to the next
- Git commits should be made after each major phase
- Documentation should be updated as work progresses
- User feedback should be incorporated during Step 3 testing

---

## Questions for Clarification

1. **Step 1:** ✅ **COMPLETED** - Already implemented according to the existing `decluttering_plan.md`.

2. **Step 2:** ✅ ANSWERED
   - **Connect to backend?** ❌ NO - Tablet app will have its own database and JSON files (standalone offline)
   - **Offline capability?** ✅ YES - App needs to store lesson plans for offline use
   - **Multiple users?** ✅ YES - App should support multiple users
   - **Lesson Mode session storage?** ✅ Local storage (Room/SQLite) - Best practice, easier to update, supports offline navigation

3. **Step 3:** ✅ ANSWERED
   - **Previous installation issues:**
     - Compilation took 4+ hours because it included entire app (lesson plan generation, schedule, etc.)
     - Frontend didn't have access to users and lesson plans - app was unusable
   - **Features required:** App must access lesson plans and navigate exactly as PC app

