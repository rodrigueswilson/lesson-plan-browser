# Diagnosing "Cannot load users!" Error

## Important: The Issue

The error "Cannot load users!" means the database query is **failing**, not just that the database is empty. If the database was empty, we should see "No users found" instead.

## Possible Causes

### 1. **Database Path Issue** (Most Likely)
The database path might be wrong on Android. Current path:
```
/data/data/com.lessonplanner.bilingual/databases/lesson_planner.db
```

This requires the app to create the `databases/` directory first. The database initialization should do this, but let's verify.

### 2. **Database Not Initialized**
The database file might not exist or tables might not be created.

### 3. **Tauri Command Not Working**
The `sql_query` Tauri command might be failing for some reason.

### 4. **Standalone Mode Not Detected**
The app might not be detecting standalone mode correctly, so it's still trying HTTP instead of local database.

## Diagnostic Steps

### Step 1: Check if Rebuild Happened
```powershell
Get-Item "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk" | Select-Object LastWriteTime
```
If more than 10 minutes ago, rebuild: `.\rebuild-android.ps1`

### Step 2: Check Logcat for Actual Error
```powershell
adb logcat -d | Select-String -Pattern "API|Error|sql_query|database|standalone" | Select-Object -Last 50
```

Look for:
- `[API] Using standalone mode` - confirms standalone detection
- `[API] Querying local database` - confirms database query attempt
- `Database query failed` or `sql_query` errors - shows actual error

### Step 3: Verify Database File Exists
```powershell
adb shell "run-as com.lessonplanner.bilingual ls -la databases/ 2>&1"
```

### Step 4: Test Database Query Directly
Try to query the database using ADB (if possible):
```powershell
adb shell "run-as com.lessonplanner.bilingual sqlite3 databases/lesson_planner.db 'SELECT COUNT(*) FROM users;'"
```

## Quick Fix: Verify Standalone Mode is Working

If standalone mode is working but database is empty, you should see:
- "No users found" message (not an error)
- Empty user list
- "Add User" button available

If you see "Cannot load users!" error, something is failing. Check logcat for the actual error message.

## Next Steps

1. **Run rebuild** to ensure latest code is in APK
2. **Check logcat** for detailed error messages
3. **Verify database file** exists and is accessible
4. **Test Tauri command** directly from browser console

