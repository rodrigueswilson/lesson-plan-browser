# REBUILD REQUIRED

## The Problem

You're still seeing "Cannot load users!" because **the new code is not in the APK yet**.

## What Changed

The code in `frontend/src/lib/api.ts` has been updated to:
1. Detect standalone mode (Android + Tauri)
2. Query local SQLite database instead of HTTP
3. Handle empty databases gracefully

**BUT** these changes are only in the **source code files**, not in the installed APK on your tablet.

## What You Need to Do

**You MUST rebuild and reinstall the app:**

```powershell
cd d:\LP
.\rebuild-android.ps1
```

This will:
1. Build the frontend with the new standalone mode code (~1 min)
2. Copy assets to Android (~5 sec)
3. Rebuild APK without Rust compilation (~3-5 min)
4. Install on your device (~30 sec)

**Total time: ~5-7 minutes**

## After Rebuild

Once rebuilt, the app will:
- Detect standalone mode automatically
- Query local database instead of HTTP
- Show "No users found" if database is empty (not an error)
- Allow you to add users

## If Error Persists After Rebuild

Then we need to check logcat for the actual error:

```powershell
adb logcat -d | Select-String -Pattern "API|Error|sql_query|database" | Select-Object -Last 30
```

But **first, please rebuild the app!**

