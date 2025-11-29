# Bundled Binary Detection Issue

## ✅ RESOLVED (2025-11-25)

**Problem:** The bundled binary exists but is not being detected by the Rust code.

**Solution:** Fixed `main.rs` to use the binary detection code from `lib.rs`. The issue was that `main.rs` had an old version of `trigger_sync` without binary detection.

**Evidence (Before Fix):**
- Binary exists at: `D:\LP\frontend\src-tauri\binaries\python-sync-processor-x86_64-pc-windows-msvc.exe` ✅
- App is using source mode: `python -m backend.sidecar_main` ❌

**Evidence (After Fix):**
- Binary detected: `[Sidecar] Found bundled binary at: D:\LP\frontend\src-tauri\binaries\python-sync-processor-x86_64-pc-windows-msvc.exe` ✅
- Binary executed: `[Sidecar] Using bundled binary: ...` ✅
- Sidecar started: `2025-11-25 21:08:27,348 - INFO - Sidecar started` ✅

## Path Detection Logic

The Rust code checks these paths in order:

1. **Path 1:** Relative to executable
   - From: `target/debug/bilingual-lesson-planner.exe`
   - To: `target/` → `src-tauri/` → `binaries/python-sync-processor-x86_64-pc-windows-msvc.exe`
   - **Expected:** `D:\LP\frontend\src-tauri\binaries\python-sync-processor-x86_64-pc-windows-msvc.exe`
   - **Status:** Binary exists at this path ✅

2. **Path 2:** From current working directory
   - Multiple variations based on CWD
   - **Status:** Should find it if CWD is `D:\LP` ✅

3. **Path 3:** Absolute path fallback (Windows)
   - `d:\LP\frontend\src-tauri\binaries\python-sync-processor-x86_64-pc-windows-msvc.exe`
   - **Status:** Binary exists at this path ✅

## Debugging Steps

### 1. Check Terminal Output
The `eprintln!` messages should appear in the terminal where `npm run tauri:dev` is running. Look for:
- `[Sidecar] Checking path1: ... (exists: true/false)`
- `[Sidecar] Found bundled binary at: ...`
- OR `[Sidecar] Bundled binary not found in any location`

### 2. Verify Path Calculation
The path calculation should work:
```rust
exe_dir = target/debug/
  .parent() = target/
  .parent() = src-tauri/
  .join("binaries") = src-tauri/binaries/
  .join(binary_name) = src-tauri/binaries/python-sync-processor-x86_64-pc-windows-msvc.exe
```

### 3. Check if Messages Are Being Printed
The `eprintln!` messages go to stderr. They should appear in the Tauri dev terminal, but might be:
- Hidden if terminal doesn't show stderr
- Buffered and not flushed immediately
- Lost if terminal output is redirected

## Next Steps

1. **Restart the app** to see the new debug logging
2. **Check the Tauri dev terminal** for `[Sidecar]` messages
3. **Verify the path** is being calculated correctly
4. **Check if `exists()` is working** - maybe there's a permission issue?

## Potential Issues

1. **Path separator:** Windows uses `\` but Rust paths should handle this automatically
2. **Permissions:** The binary might exist but not be readable/executable
3. **Timing:** The binary might be checked before it's fully written (unlikely)
4. **Case sensitivity:** Windows paths are case-insensitive, but Rust's `exists()` should handle this

## Solution

Added explicit debug logging to path1 calculation. After restarting the app and triggering sync, check the terminal for:
```
[Sidecar] Checking path1: D:\LP\frontend\src-tauri\binaries\python-sync-processor-x86_64-pc-windows-msvc.exe (exists: true)
```

If this shows `exists: false`, there's a path calculation issue.
If this shows `exists: true` but binary still not used, there's a logic issue after detection.

