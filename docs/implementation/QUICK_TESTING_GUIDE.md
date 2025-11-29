# Quick Testing Guide - Unified Frontend

This guide provides quick steps to test the unified frontend implementation.

**Status**: Code Verification Complete ✅  
**Next**: Manual Testing Required

## Code Verification Results

✅ All implementation files verified and correct:
- Unified App.tsx exists and uses platform detection
- Feature gating hook implemented correctly
- Platform detection enhanced for Android Tauri
- Build script paths correct
- PC App.tsx correctly re-exports unified version

## Quick Test Steps

### Test 1: PC Development Build (BUILD-1)

**Objective**: Verify PC app builds and runs with unified frontend

**Steps**:
1. Start backend:
   ```powershell
   cd backend
   python -m uvicorn api:app --reload
   ```

2. In a new terminal, start PC app:
   ```powershell
   cd frontend
   npm run tauri:dev
   ```

3. **Verify**:
   - [ ] App launches without errors
   - [ ] Console shows no import errors
   - [ ] Full navigation visible (Home, Plans, Schedule, Browser, History, Analytics)
   - [ ] All navigation items work
   - [ ] Browser view works
   - [ ] Lesson Mode works

**Expected**: App should work exactly as before, but now using unified frontend

---

### Test 2: Platform Detection (PD-1)

**Objective**: Verify platform detection works on PC

**Steps**:
1. With PC app running, open DevTools (if available) or check console
2. Add temporary console log in `lesson-plan-browser/frontend/src/App.tsx`:
   ```typescript
   console.log('Platform:', { isDesktop, isMobile, platform });
   ```

3. **Verify**:
   - [ ] `isDesktop` is `true`
   - [ ] `isMobile` is `false`
   - [ ] `platform` is `'desktop'`

**Expected**: Platform correctly detected as desktop

---

### Test 3: Android APK Build (BUILD-3)

**Objective**: Verify Android build works with unified frontend

**Steps**:
1. Navigate to tablet directory:
   ```powershell
   cd lesson-plan-browser
   ```

2. Build APK:
   ```powershell
   .\scripts\run-with-ndk.ps1 -Target arm64
   ```

3. **Verify**:
   - [ ] Build completes without errors
   - [ ] APK created in expected location
   - [ ] No path-related errors

**Expected**: Build should work unchanged (no script modifications needed)

---

### Test 4: Android Platform Detection (PD-2)

**Objective**: Verify platform detection works on Android

**Steps**:
1. Install APK on device (from `lesson-plan-browser/` directory):
   ```powershell
   adb install -r frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk
   ```
   
   **Note**: Make sure you're in the `lesson-plan-browser/` directory when running this command.

2. Launch app on device

3. Check logs:
   ```powershell
   adb logcat | Select-String -Pattern "platform|Platform|isMobile|isDesktop"
   ```

4. **Verify**:
   - [ ] `isMobile` is `true`
   - [ ] `isDesktop` is `false`
   - [ ] User agent contains "Android"

**Expected**: Platform correctly detected as mobile/Android

---

### Test 5: Feature Gating (FG-1, FG-2)

**Objective**: Verify PC shows all features, tablet shows only browser/lesson mode

**PC Verification**:
- [ ] All navigation items visible (Home, Plans, Schedule, Browser, History, Analytics)
- [ ] Schedule editor accessible
- [ ] Analytics accessible
- [ ] Plan History accessible
- [ ] Batch Processor accessible

**Tablet Verification**:
- [ ] No navigation UI visible (no sidebar, no bottom nav)
- [ ] Only browser view visible on launch
- [ ] Can enter Lesson Mode from browser
- [ ] Cannot access Schedule, Analytics, History, etc.

**Expected**: 
- PC: Full feature set
- Tablet: Browser + Lesson Mode only

---

### Test 6: Lazy Loading (FG-3)

**Objective**: Verify PC-only components not in tablet bundle

**Steps**:
1. Build tablet APK (already done in Test 3)
2. Analyze bundle size (if tools available)
3. Check that ScheduleInput, Analytics, etc. are not loaded on tablet

**Expected**: Tablet bundle should be smaller (PC components excluded)

---

## Test Results Tracking

Update `docs/implementation/UNIFIED_FRONTEND_TEST_RESULTS.md` with results as you test.

## Troubleshooting

### PC App Won't Start
- Check backend is running on `http://localhost:8000`
- Check console for import errors
- Verify `frontend/src/App.tsx` correctly re-exports unified App

### Android Build Fails
- Verify you're in `lesson-plan-browser/` directory
- Check build script path (should be `lesson-plan-browser/frontend/`)
- Verify all dependencies installed

### Platform Detection Wrong
- Check `navigator.userAgent` contains "Android" on Android
- Verify `__TAURI_INTERNALS__` exists on both platforms
- Check platform.ts logic

## Next Steps After Testing

1. Document all test results in `UNIFIED_FRONTEND_TEST_RESULTS.md`
2. Fix any issues found
3. Re-test after fixes
4. Mark tests as passed when verified

---

**See Also**:
- `docs/implementation/UNIFIED_FRONTEND_TESTING_PLAN.md` - Complete test plan
- `docs/implementation/UNIFIED_FRONTEND_TEST_RESULTS.md` - Test results log

