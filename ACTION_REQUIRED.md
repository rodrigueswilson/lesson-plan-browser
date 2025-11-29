# ACTION REQUIRED: Rebuild App to Fix "Cannot load users!" Error

## The Issue

You're seeing **"Cannot load users!"** error because the app on your tablet still has the **old code** that tries to connect to a remote HTTP backend.

## What Changed in the Code

I've updated `frontend/src/lib/api.ts` to:
1. ✅ Detect standalone mode (Android + Tauri available)
2. ✅ Query local SQLite database via Tauri commands
3. ✅ Handle empty databases gracefully (show "No users found" instead of error)
4. ✅ Better error handling (return empty array on errors instead of throwing)

**BUT** these changes are **only in source files**, not in the installed APK.

## What You Must Do NOW

### Step 1: Rebuild the App

```powershell
cd d:\LP
.\rebuild-android.ps1
```

**This takes ~5-7 minutes:**
- Frontend build: ~1 minute
- APK rebuild (skip Rust): ~3-5 minutes
- Install on device: ~30 seconds

### Step 2: Test Again

After rebuild completes:
1. Launch the app on your tablet
2. It should now:
   - Detect standalone mode automatically
   - Query local database
   - Show "No users found" if database is empty (not an error)
   - Allow you to add users

## If Error Persists After Rebuild

Then we need to check the actual error from logcat:

```powershell
adb logcat -d | Select-String -Pattern "API|Error|sql_query|database|standalone" | Select-Object -Last 40
```

This will show us:
- Whether standalone mode is detected
- If database query is attempted
- The actual error message

## Summary

**You MUST rebuild the app** for the changes to take effect. The rebuild script is ready - just run it!

---

**Next Steps:**
1. Run `.\rebuild-android.ps1`
2. Wait for it to complete (~5-7 min)
3. Test the app
4. Share logcat output if error persists

