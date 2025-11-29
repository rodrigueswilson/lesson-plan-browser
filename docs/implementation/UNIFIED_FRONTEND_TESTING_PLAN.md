# Unified Frontend Testing Plan

This document provides a comprehensive testing plan for the unified frontend implementation, covering platform detection, feature gating, navigation, builds, integration, and regression testing.

**Last Updated**: 2025-01-XX  
**Status**: Pre-Implementation Testing Plan

## Test Environment Setup

### PC Test Environment

**Requirements:**
- Windows 10/11 development machine
- Node.js 18+
- Rust (latest stable)
- Tauri CLI v2.0 installed
- Backend running on `http://localhost:8000`
- SQLite database with test data

**Setup Steps:**
1. Start backend: `cd backend && python -m uvicorn api:app --reload`
2. Verify backend health: `curl http://localhost:8000/api/health`
3. Navigate to frontend: `cd frontend`
4. Install dependencies: `npm install` (if needed)
5. Start dev server: `npm run tauri:dev`

### Tablet Test Environment

**Requirements:**
- Android emulator (Android 10+) or physical device
- ADB connected and working
- Backend accessible:
  - Emulator: `http://10.0.2.2:8000`
  - Physical device: Network IP (e.g., `http://192.168.1.100:8000`)
- Android build tools configured

**Setup Steps:**
1. Start backend (same as PC)
2. Connect device/start emulator
3. Verify ADB: `adb devices`
4. Navigate to tablet frontend: `cd lesson-plan-browser`
5. Build APK: `.\scripts\run-with-ndk.ps1 -Target arm64`
6. Install APK: `adb install -r .\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk`

### Test Data Requirements

**Database:**
- At least 2 test users
- At least 1 week of schedule entries
- At least 1 weekly plan with lesson JSON
- Test data for all PC features (analytics, history, etc.)

**Backend:**
- All API endpoints functional
- CORS configured correctly
- Health check endpoint working

## Test Categories

### 1. Platform Detection Tests

**Objective**: Verify platform detection works correctly on both platforms.

#### Test PD-1: Desktop Platform Detection

**Setup**: Run on PC (Windows desktop Tauri)

**Steps:**
1. Launch PC app: `npm run tauri:dev` in `frontend/`
2. Open browser DevTools (if available)
3. Check console for platform detection logs
4. Verify `isDesktop` is `true`
5. Verify `isMobile` is `false`

**Expected Results:**
- `getPlatform()` returns `'desktop'`
- `isDesktop` is `true`
- `isMobile` is `false`
- `isWeb` is `false`

**Pass Criteria**: All assertions pass

#### Test PD-2: Android Platform Detection

**Setup**: Run on Android tablet/emulator

**Steps:**
1. Build and install APK on Android device
2. Launch app
3. Check logs: `adb logcat | grep -i platform`
4. Verify `isMobile` is `true`
5. Verify `isDesktop` is `false`

**Expected Results:**
- `getPlatform()` returns `'mobile'` or detects Android Tauri
- `isMobile` is `true`
- `isDesktop` is `false`
- User agent contains "Android"

**Pass Criteria**: All assertions pass

#### Test PD-3: Platform Detection Edge Cases

**Setup**: Test various scenarios

**Test Cases:**
1. Web mode (no Tauri): Should detect as `'web'`
2. Tauri desktop with Android user agent: Should detect as `'desktop'` (Tauri takes precedence)
3. Missing window object: Should handle gracefully

**Expected Results:**
- Edge cases handled without errors
- Appropriate fallbacks used

**Pass Criteria**: No errors, appropriate detection

### 2. Feature Gating Tests

**Objective**: Verify PC-only features are accessible on PC but not on tablet.

#### Test FG-1: PC Shows All Features

**Setup**: Run on PC

**Steps:**
1. Launch PC app
2. Verify navigation shows all items:
   - Home
   - Lesson Plans
   - Schedule
   - Browser
   - History
   - Analytics
3. Navigate to each section
4. Verify all sections load correctly

**Expected Results:**
- All navigation items visible
- All sections accessible
- No errors when navigating

**Pass Criteria**: All features accessible

#### Test FG-2: Tablet Shows Only Browser and Lesson Mode

**Setup**: Run on Android tablet

**Steps:**
1. Launch tablet app
2. Verify no navigation UI visible
3. Verify app starts in browser view
4. Enter lesson mode from browser
5. Exit lesson mode back to browser
6. Verify no way to access PC-only features

**Expected Results:**
- No navigation sidebar or bottom nav
- Only browser and lesson mode accessible
- No Schedule, Analytics, History, etc. visible
- Cannot access PC-only features via any means

**Pass Criteria**: Tablet restricted to browser and lesson mode only

#### Test FG-3: PC-Only Components Lazy Loaded

**Setup**: Run on tablet, check bundle

**Steps:**
1. Build tablet APK
2. Analyze bundle size
3. Check bundle contents (if possible)
4. Verify PC-only components not in bundle

**Expected Results:**
- Bundle size smaller than if all components included
- PC-only components not in tablet bundle
- Tree-shaking working correctly

**Pass Criteria**: Bundle size acceptable, PC components excluded

#### Test FG-4: Feature Gating Hook

**Setup**: Test `usePlatformFeatures` hook

**Steps:**
1. Use hook in test component
2. Verify `isTablet` and `isPC` flags correct
3. Verify feature flags (`showNavigation`, `showScheduleEditor`, etc.) correct
4. Test on both platforms

**Expected Results:**
- Hook returns correct platform flags
- Feature flags match platform capabilities
- No errors in hook usage

**Pass Criteria**: Hook works correctly on both platforms

### 3. Navigation Tests

**Objective**: Verify navigation works correctly on PC and is hidden on tablet.

#### Test NAV-1: PC Full Navigation

**Setup**: Run on PC

**Steps:**
1. Launch app
2. Verify sidebar navigation visible
3. Click each navigation item
4. Verify content changes correctly
5. Verify active item highlighted
6. Test navigation state persistence

**Expected Results:**
- All navigation items visible and clickable
- Content updates on navigation
- Active state correct
- Navigation state persists

**Pass Criteria**: Full navigation works correctly

#### Test NAV-2: Tablet No Navigation

**Setup**: Run on Android tablet

**Steps:**
1. Launch app
2. Verify no navigation UI (sidebar, bottom nav, etc.)
3. Verify full-screen browser view
4. Enter lesson mode
5. Verify still no navigation
6. Exit lesson mode
7. Verify back to browser, still no navigation

**Expected Results:**
- No navigation UI visible at any time
- Full-screen experience
- Browser and lesson mode only

**Pass Criteria**: No navigation UI on tablet

#### Test NAV-3: Navigation Item Filtering

**Setup**: Run on PC, test filtering

**Steps:**
1. Modify `availableNavItems` prop
2. Verify only specified items show
3. Test with empty array (should show none)
4. Test with all items (should show all)
5. Test with subset (should show subset)

**Expected Results:**
- Navigation respects `availableNavItems` prop
- Filtering works correctly
- No errors with various configurations

**Pass Criteria**: Filtering works as expected

#### Test NAV-4: Navigation State Management

**Setup**: Test navigation state

**Steps:**
1. Navigate to different sections
2. Refresh app (if possible)
3. Verify state persists or resets appropriately
4. Test deep linking (if applicable)

**Expected Results:**
- Navigation state managed correctly
- Appropriate persistence/reset behavior

**Pass Criteria**: State management works correctly

### 4. Build Tests

**Objective**: Verify both PC and Android builds work correctly.

#### Test BUILD-1: PC Development Build

**Setup**: PC development environment

**Steps:**
1. Navigate to `frontend/`
2. Run `npm run tauri:dev`
3. Verify app launches
4. Verify no build errors
5. Verify hot reload works (if applicable)

**Expected Results:**
- Build succeeds
- App launches correctly
- No console errors
- Development features work

**Pass Criteria**: Development build works

#### Test BUILD-2: PC Production Build

**Setup**: PC build environment

**Steps:**
1. Navigate to `frontend/`
2. Run `npm run tauri:build`
3. Verify build completes
4. Verify output files created
5. Launch built app
6. Verify app works correctly

**Expected Results:**
- Build succeeds without errors
- Output files created in expected location
- Built app launches and works

**Pass Criteria**: Production build works

#### Test BUILD-3: Android APK Build

**Setup**: Android build environment

**Steps:**
1. Navigate to `lesson-plan-browser/`
2. Run `.\scripts\run-with-ndk.ps1 -Target arm64`
3. Verify build completes
4. Verify APK created
5. Install APK on device
6. Verify app launches

**Expected Results:**
- Build script runs without errors
- APK created in expected location
- APK installs successfully
- App launches on device

**Pass Criteria**: Android build works

#### Test BUILD-4: Build Script Path Verification

**Setup**: Verify build script paths

**Steps:**
1. Check `build-android-offline.ps1` line 35
2. Verify path: `$frontendDir = Join-Path $repoRoot "frontend"`
3. Verify this resolves to `lesson-plan-browser/frontend/`
4. Test build with this path

**Expected Results:**
- Path resolves correctly
- Build script finds frontend directory
- No path-related errors

**Pass Criteria**: Build script paths correct

#### Test BUILD-5: Bundle Size Verification

**Setup**: Compare bundle sizes

**Steps:**
1. Build PC version, note bundle size
2. Build tablet version, note bundle size
3. Compare sizes
4. Verify tablet bundle smaller (PC components excluded)

**Expected Results:**
- Both builds succeed
- Tablet bundle smaller than PC bundle
- Size difference reasonable (PC-only components excluded)

**Pass Criteria**: Bundle sizes acceptable

### 5. Integration Tests

**Objective**: Verify end-to-end functionality on both platforms.

#### Test INT-1: PC Full Workflow

**Setup**: Run on PC

**Steps:**
1. Launch app
2. Select or create user
3. Navigate to Schedule
4. Create/edit schedule entry
5. Navigate to Browser
6. View week/day/lesson
7. Enter Lesson Mode
8. Use timer, navigate steps
9. Exit lesson mode
10. Navigate to Analytics
11. View analytics data
12. Navigate to History
13. View plan history

**Expected Results:**
- All navigation works
- All features functional
- No errors throughout workflow
- Data persists correctly

**Pass Criteria**: Full PC workflow works

#### Test INT-2: Tablet Full Workflow

**Setup**: Run on Android tablet

**Steps:**
1. Launch app
2. Select or create user
3. View browser (week view)
4. Navigate to day view
5. View lesson detail
6. Enter Lesson Mode
7. Use timer, navigate steps
8. Exit lesson mode
9. Return to browser
10. Verify can only access browser and lesson mode

**Expected Results:**
- Browser navigation works
- Lesson mode works
- No access to PC-only features
- No errors throughout workflow

**Pass Criteria**: Full tablet workflow works

#### Test INT-3: User Selection

**Setup**: Test on both platforms

**Steps:**
1. Launch app
2. Verify user selector shown if no user
3. Select existing user
4. Verify user selection persists
5. Switch users
6. Verify data updates for new user

**Expected Results:**
- User selection works on both platforms
- Selection persists
- Data updates correctly

**Pass Criteria**: User selection works on both

#### Test INT-4: Lesson Mode Integration

**Setup**: Test on both platforms

**Steps:**
1. Navigate to browser
2. Select lesson
3. Enter lesson mode
4. Verify lesson data loads
5. Use timer
6. Navigate steps
7. Exit lesson mode
8. Verify returns to browser correctly

**Expected Results:**
- Lesson mode works on both platforms
- Timer functions correctly
- Step navigation works
- Exit behavior correct

**Pass Criteria**: Lesson mode works on both platforms

### 6. Regression Tests

**Objective**: Verify existing features still work after unification.

#### Test REG-1: PC Existing Features

**Setup**: Run on PC

**Test Each Feature:**
- [ ] Schedule editing
- [ ] Schedule grid display
- [ ] Slot configuration
- [ ] Batch processing
- [ ] Analytics dashboard
- [ ] Plan history
- [ ] Browser navigation
- [ ] Lesson mode
- [ ] User selection
- [ ] Sync functionality

**Expected Results:**
- All features work as before
- No functionality lost
- No new bugs introduced

**Pass Criteria**: All features work

#### Test REG-2: Tablet Existing Features

**Setup**: Run on Android tablet

**Test Each Feature:**
- [ ] Browser week view
- [ ] Browser day view
- [ ] Browser lesson detail
- [ ] Lesson mode
- [ ] Timer functionality
- [ ] Step navigation
- [ ] User selection
- [ ] Offline mode (if applicable)

**Expected Results:**
- All features work as before
- No functionality lost
- No new bugs introduced

**Pass Criteria**: All features work

#### Test REG-3: Shared Components

**Setup**: Test shared components on both platforms

**Test Components:**
- [ ] LessonPlanBrowser
- [ ] WeekView
- [ ] DayView
- [ ] LessonDetailView
- [ ] UserSelector
- [ ] LessonMode
- [ ] TimerDisplay
- [ ] All resource displays

**Expected Results:**
- Components work on both platforms
- No platform-specific issues
- Consistent behavior

**Pass Criteria**: Shared components work on both

#### Test REG-4: API Client

**Setup**: Test API calls on both platforms

**Test API Functions:**
- [ ] User API (list, get, create)
- [ ] Schedule API (get, create, update)
- [ ] Plan API (list, get)
- [ ] Lesson API (get plan detail, get steps)
- [ ] Lesson mode session API

**Expected Results:**
- All API calls work
- Platform-specific URL resolution works
- Local DB mode works on tablet (if enabled)
- Network mode works on both

**Pass Criteria**: API client works on both platforms

## Test Execution Checklist

### Pre-Testing

- [ ] Test environments set up
- [ ] Test data prepared
- [ ] Backend running
- [ ] Dependencies installed
- [ ] Build tools configured

### During Testing

- [ ] Run all platform detection tests
- [ ] Run all feature gating tests
- [ ] Run all navigation tests
- [ ] Run all build tests
- [ ] Run all integration tests
- [ ] Run all regression tests

### Post-Testing

- [ ] Document all test results
- [ ] Record any failures
- [ ] Document resolutions
- [ ] Update test results document
- [ ] Verify all tests pass before proceeding

## Test Results Documentation

**File**: `docs/implementation/UNIFIED_FRONTEND_TEST_RESULTS.md`

**Template for Each Test:**
- Test ID
- Test Name
- Platform
- Date
- Result (Pass/Fail)
- Notes
- Screenshots (if applicable)
- Logs (if applicable)

## Known Issues & Limitations

**Document any known issues discovered during testing:**

| Issue | Platform | Severity | Status | Notes |
|-------|----------|----------|--------|-------|
| (To be filled during testing) | | | | |

## Test Automation Opportunities

**Future Enhancements:**
- Unit tests for platform detection
- Integration test suite
- E2E tests with Playwright/Cypress
- Automated build verification
- Bundle size monitoring

## Success Criteria

**Testing Complete When:**
- [ ] All platform detection tests pass
- [ ] All feature gating tests pass
- [ ] All navigation tests pass
- [ ] All build tests pass
- [ ] All integration tests pass
- [ ] All regression tests pass
- [ ] No critical bugs found
- [ ] Performance acceptable
- [ ] Bundle sizes acceptable

---

**Document Status**: Complete - Pre-Implementation  
**Last Updated**: 2025-01-XX  
**Maintainer**: Development Team

