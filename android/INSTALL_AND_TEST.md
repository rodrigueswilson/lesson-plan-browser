# Install and Test Guide

## Prerequisites

1. **Android Device** (physical tablet/phone) OR **Android Emulator**
2. **USB Debugging** enabled (for physical devices)
3. **ADB** (Android Debug Bridge) - usually comes with Android Studio

## Step 1: Connect Device or Start Emulator

### Option A: Physical Device

1. **Enable Developer Options**:
   - Go to Settings > About Phone/Tablet
   - Tap "Build Number" 7 times
   - You'll see "You are now a developer!"

2. **Enable USB Debugging**:
   - Go to Settings > Developer Options
   - Enable "USB Debugging"
   - Enable "Install via USB" (if available)

3. **Connect Device**:
   - Connect your Android device to your computer via USB
   - On your device, when prompted, allow USB debugging
   - Check "Always allow from this computer" if you want

4. **Verify Connection**:
   ```powershell
   cd android
   adb devices
   ```
   You should see your device listed (e.g., `ABC123XYZ    device`)

### Option B: Android Emulator

1. **Start Android Studio**
2. **Open AVD Manager**:
   - Tools > Device Manager
   - Or click the device icon in the toolbar

3. **Create/Start Emulator**:
   - If you have an emulator, click the ▶️ play button
   - If not, click "Create Device" and follow the wizard
   - Recommended: Tablet (10"+) with API 26+ (Android 8.0+)

4. **Verify Connection**:
   ```powershell
   cd android
   adb devices
   ```
   You should see your emulator listed (e.g., `emulator-5554    device`)

## Step 2: Install the App

Once a device is connected, run:

```powershell
cd android
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
.\gradlew.bat installDebug
```

Or if ADB is in your PATH:

```powershell
cd android
.\gradlew.bat installDebug
```

**Expected Output**:
```
> Task :app:installDebug
Installing APK 'app-debug.apk' on 'device_name' for app:debug
Installed on 1 device.
BUILD SUCCESSFUL
```

## Step 3: Launch the App

### On Device/Emulator:
1. Find "Bilingual Lesson Planner" in your app drawer
2. Tap to launch

### Via ADB:
```powershell
adb shell am start -n com.bilingual.lessonplanner/.MainActivity
```

## Step 4: Testing Checklist

### Initial Setup
- [ ] App launches successfully
- [ ] User selection screen appears
- [ ] Supabase configuration is valid (no error message)

### User Selection
- [ ] List of users appears (Wilson, Daniela, etc.)
- [ ] Can select a user
- [ ] App navigates to Browser screen after selection

### Browser Screen
- [ ] Top bar shows "Lesson Plans"
- [ ] Refresh button is visible
- [ ] Week selector appears (if weeks are available)
- [ ] View mode buttons (Week/Day) are visible

### Week View
- [ ] Grid layout shows 5 columns (Monday-Friday)
- [ ] Lesson cards appear for each day
- [ ] Can click on a lesson card
- [ ] Navigation to lesson detail works

### Day View
- [ ] Can switch to Day view mode
- [ ] List of lessons for selected day appears
- [ ] Day navigation (previous/next) works
- [ ] Can click on a lesson to view details

### Lesson Detail View
- [ ] Full lesson content displays
- [ ] All sections visible:
  - [ ] Objectives
  - [ ] Vocabulary & Cognates
  - [ ] Sentence Frames
  - [ ] Materials Needed
  - [ ] Instruction Steps
- [ ] Back button works
- [ ] Navigation returns to previous screen

### Data Sync
- [ ] On first launch, data syncs from Supabase
- [ ] Loading indicators appear during sync
- [ ] Data appears after sync completes
- [ ] Refresh button triggers new sync

### Offline Mode
- [ ] Turn off WiFi/Mobile data
- [ ] App still shows cached data
- [ ] Can navigate between views
- [ ] Refresh shows appropriate message

### Week Selection
- [ ] Week selector shows available weeks
- [ ] Can select different weeks
- [ ] Week view updates with selected week's data

## Step 5: View Logs

To see app logs in real-time:

```powershell
adb logcat -s BilingualLessonPlanner
```

Or to see all logs:

```powershell
adb logcat | Select-String "BilingualLessonPlanner"
```

### Useful Log Tags:
- `BilingualLessonPlanner` - General app logs
- `SyncManager` - Sync operations
- `BackgroundSyncWorker` - Background sync
- `UserPreferences` - User selection
- `ConfigValidator` - Supabase configuration

## Troubleshooting

### "No connected devices!"
- Make sure device/emulator is connected
- Run `adb devices` to verify
- Try `adb kill-server` then `adb start-server`

### "Installation failed"
- Check if app is already installed (uninstall first)
- Enable "Install via USB" in Developer Options
- Check device storage space

### "App crashes on launch"
- Check logs: `adb logcat | Select-String "FATAL"`
- Verify Supabase credentials in `local.properties`
- Check if device meets min SDK (API 26+)

### "No data appears"
- Check network connection
- Verify Supabase credentials
- Check logs for sync errors
- Try manual refresh

### "Configuration Error" message
- Verify `local.properties` has Supabase credentials
- Check `SUPABASE_SETUP.md` for setup instructions
- Ensure credentials are correct for your Supabase projects

## Manual APK Installation

If automatic installation doesn't work, you can manually install:

1. **Locate APK**:
   ```
   android/app/build/outputs/apk/debug/app-debug.apk
   ```

2. **Transfer to Device**:
   - Copy APK to device via USB
   - Or use: `adb install app-debug.apk`

3. **Install on Device**:
   - Enable "Install from Unknown Sources" in Settings
   - Tap the APK file on your device
   - Follow installation prompts

## Next Steps After Testing

1. **Report Issues**: Note any bugs or unexpected behavior
2. **Performance**: Check if app feels responsive
3. **UI/UX**: Verify layout looks good on tablet
4. **Data Accuracy**: Verify lesson content is correct
5. **Edge Cases**: Test with no network, empty data, etc.

## Success Criteria

The app is working correctly if:
- ✅ App installs and launches
- ✅ User selection works
- ✅ All three views (Week/Day/Lesson) work
- ✅ Navigation flows correctly
- ✅ Data syncs from Supabase
- ✅ Offline mode works
- ✅ No crashes or major errors

Happy testing! 🎉

