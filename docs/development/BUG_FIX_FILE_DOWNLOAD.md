# Bug Fix: File Download Fails in Browser

## Problem

File download in Plan History failed with error:
```
Failed to save file: TypeError: window.__TAURI_IPC__ is not a function
```

**Root Cause:**
The `PlanHistory` component was using Tauri's `invoke` function directly, which only works in a Tauri desktop app environment. When running in a browser, Tauri APIs are not available, causing the error.

## Solution

Updated `PlanHistory.tsx` to:
1. **Detect platform** using `isDesktop` from platform utilities
2. **Use Tauri APIs** only when running in desktop app
3. **Use browser download** when running in browser:
   - Create temporary `<a>` element
   - Set `href` to backend API endpoint (`/api/render/{filename}`)
   - Trigger click to download
   - Remove element after download

## Changes Made

### Before (Tauri-only):
```typescript
const handleDownload = async (filepath: string) => {
  const destination = await invoke<string>('save_file_dialog', { sourcePath: filepath });
  // ...
};
```

### After (Platform-aware):
```typescript
const handleDownload = async (filepath: string) => {
  if (isDesktop) {
    // Use Tauri file dialog
    const { invoke } = await import('@tauri-apps/api/tauri');
    const destination = await invoke<string>('save_file_dialog', { sourcePath: filepath });
    // ...
  } else {
    // Browser: Download via API endpoint
    const filename = filepath.split('/').pop() || filepath.split('\\').pop() || 'plan.docx';
    const downloadUrl = `${config.apiBaseUrl}/api/render/${filename}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    link.click();
    // ...
  }
};
```

## Files Changed

- `frontend/src/components/PlanHistory.tsx`:
  - Added platform detection import
  - Updated `handleDownload` for browser compatibility
  - Updated `handleShowInFolder` to show message in browser
  - Updated `handleOpenFile` to open in new tab in browser

## Backend Endpoint Used

- `/api/render/{filename}` - Serves rendered DOCX files for download
- Returns `FileResponse` with proper content type

## Verification

**Before Fix:**
- Desktop app: ✅ Works
- Browser: ❌ Error: `window.__TAURI_IPC__ is not a function`

**After Fix:**
- Desktop app: ✅ Works (uses Tauri file dialog)
- Browser: ✅ Works (uses browser download)

## Status

✅ **FIXED** - File downloads now work in both desktop and browser environments

---

**Date Fixed:** 2025-11-07  
**Impact:** High (blocked file downloads in browser)

