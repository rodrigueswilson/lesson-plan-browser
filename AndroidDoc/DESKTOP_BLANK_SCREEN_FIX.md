# Desktop Blank Screen Fix

**Date:** Based on `07_ANDROID_DEBUGGING_AND_FIXES.md` fixes  
**Issue:** App window opens but shows blank/white screen

## Root Cause

The `devUrl` configuration in `tauri.conf.json` causes Tauri to try connecting to the Vite dev server. If the connection fails or has issues, you get a blank screen.

## Solution (From Yesterday's Fixes)

**Remove `devUrl` and use bundled assets instead:**

1. **Remove `devUrl` from `tauri.conf.json`:**
   ```json
   "build": {
     "beforeDevCommand": "npm run dev",
     "beforeBuildCommand": "npm run build:skip-check",
     "frontendDist": "../dist"
     // "devUrl": "http://localhost:1420"  <-- REMOVE THIS
   }
   ```

2. **Build frontend first:**
   ```powershell
   cd d:\LP\frontend
   npm run build:skip-check
   ```

3. **Run Tauri dev:**
   ```powershell
   npm run tauri:dev
   ```

4. **App will use bundled assets from `dist/` folder**

## Why This Works

- **Bundled assets are reliable:** No dependency on dev server connection
- **No proxy issues:** Direct file serving, no network dependency
- **Consistent behavior:** Same approach works for both desktop and Android

## Trade-offs

**Pros:**
- ✅ Reliable, no blank screens
- ✅ Works consistently
- ✅ Same approach as Android

**Cons:**
- ❌ No hot reload (need to rebuild after changes)
- ❌ Slower development cycle

## Alternative: Use Dev Server (If Needed)

If you want hot reload for faster development:

1. **Keep `devUrl` in config**
2. **Ensure Vite dev server is running** (`npm run dev` in separate terminal)
3. **Verify connection:** Check `http://localhost:1420` is accessible
4. **Watch for connection errors** in console

**Recommendation:** Use bundled assets for testing, switch to dev server only when actively developing UI.

---

**Last Updated:** Desktop testing phase  
**Status:** Fix applied

