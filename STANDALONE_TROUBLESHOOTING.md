# Troubleshooting: "Cannot load users!" in Standalone Mode

## Problem
After implementing standalone mode, the app still shows "Cannot load users!" error.

## Possible Causes

### 1. **App Not Rebuilt Yet**
The new code changes aren't in the APK yet. You need to rebuild.

**Solution:** Run the rebuild script:
```powershell
cd d:\LP
.\rebuild-android.ps1
```

### 2. **Database Not Initialized**
The SQLite database file might not exist or the tables haven't been created.

**Check:** 
```powershell
adb shell "ls -la /data/data/com.lessonplanner.bilingual/databases/"
```

**Solution:** The database should auto-initialize on app start. Check logcat for database initialization errors.

### 3. **Database Empty (This is OK!)**
If the database exists but has no users, you'll see "No users found" (not an error).

**Solution:** Create a test user via the app or sync from Supabase.

### 4. **Tauri Command Not Available**
The `sql_query` command might not be registered or accessible.

**Check logcat for:**
- `[API] Using standalone mode`
- `[API] Invoking sql_query command`
- Any errors about command not found

### 5. **Permission Issues**
Android might not have permission to access the database directory.

**Solution:** The app should automatically create the directory, but check if there are permission errors in logcat.

## Diagnostic Steps

### Step 1: Verify Rebuild
Check if APK was recently rebuilt:
```powershell
Get-Item "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk" | Select-Object LastWriteTime
```

### Step 2: Check Logcat
Run diagnostic script:
```powershell
cd d:\LP
.\check-standalone-errors.ps1
```

Or manually:
```powershell
adb logcat -c
adb shell am start -n com.lessonplanner.bilingual/.MainActivity
adb logcat | Select-String -Pattern "API|Error|sql_query|database|standalone"
```

### Step 3: Verify Database Exists
```powershell
adb shell "run-as com.lessonplanner.bilingual ls -la databases/"
```

### Step 4: Check Standalone Mode Detection
Look for in logcat:
```
[API] Mode detection: { standalone: true }
[API] Using standalone mode: querying local database for users
```

If you don't see these, standalone mode isn't being detected.

## Quick Fix Checklist

- [ ] Rebuilt APK with latest code (`.\rebuild-android.ps1`)
- [ ] Reinstalled APK on device
- [ ] Checked logcat for actual error messages
- [ ] Verified standalone mode is being detected
- [ ] Verified database file exists
- [ ] Checked for permission errors

## Expected Behavior

**If database is empty (OK):**
- App loads successfully
- Shows "No users found" message
- "Add User" button is available

**If database query fails (ERROR):**
- Shows "Cannot load users!" alert
- Error message indicates the problem
- Check logcat for detailed error

