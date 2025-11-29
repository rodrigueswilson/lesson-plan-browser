# Android Debug Notes

## Current Issue: "Hello Android!" Message

The app is showing "Hello Android!" instead of the frontend UI. This indicates:

1. ✅ Native Android code is running
2. ✅ Rust library is loaded
3. ❌ Webview is not loading the frontend

## Possible Causes

1. **Dev server not running**: The Vite dev server needs to be accessible from the emulator
2. **URL configuration**: The devUrl might not be correctly passed to the Rust webview code
3. **Network connectivity**: The emulator might not be able to reach the dev server at 192.168.12.153:1420

## Debugging Steps

1. Verify dev server is running:
   ```powershell
   Get-NetTCPConnection -LocalPort 1420
   ```

2. Test connectivity from emulator:
   ```powershell
   adb shell "curl http://192.168.12.153:1420"
   ```

3. Check Android logs for webview errors:
   ```powershell
   adb logcat | Select-String -Pattern "webview|RustWebView|error"
   ```

4. Verify the URL is being passed correctly in the Rust code (check `tauri::generate_context!()`)

## Solution

The dev server should start automatically with `npm run tauri android dev`. If it's not running, manually start it:
```powershell
cd frontend
npm run dev
```

Then rebuild the Android app.

