# Phase 5: Python Bundling Guide

## Current Status

✅ **PyInstaller**: Installed and ready
❌ **Nuitka**: Not installed (optional)

## Strategy

Since we're on Windows and need to build for Android (Linux ARM64), we have two approaches:

### Approach 1: Windows Bundle First (Testing)
Create a Windows executable to verify bundling works, then cross-compile for Android.

### Approach 2: Docker Cross-Compilation (Production)
Use Docker to build Android binary directly.

## Step 1: Create Windows Bundle (Testing)

This verifies our bundling configuration works:

```powershell
cd D:\LP
.\bundle_sidecar.ps1 pyinstaller
```

This will create: `frontend/src-tauri/binaries/python-sync-processor-x86_64-pc-windows-msvc.exe`

### Test Windows Bundle

After creating the bundle, we can test it with the desktop Tauri app by:
1. Updating `main.rs` to use the bundled executable instead of `python -m backend.sidecar_main`
2. Testing that IPC still works

## Step 2: Android Cross-Compilation

For Android, we need a Linux ARM64 binary. Options:

### Option A: Docker (Recommended)

```powershell
# Build Docker image
docker build -f Dockerfile.android-python -t python-android-build .

# Extract binary
docker create --name temp-container python-android-build
docker cp temp-container:/app/python-sync-processor frontend/src-tauri/binaries/python-sync-processor-aarch64-linux-android
docker rm temp-container
```

### Option B: WSL2

If you have WSL2 installed:

```bash
# In WSL2
cd /mnt/d/LP
./bundle_sidecar.sh pyinstaller
# Or use nuitka for smaller binary
```

### Option C: Linux VM

Use a Linux VM with ARM64 emulation or cross-compilation toolchain.

## Step 3: Update Tauri Configuration

After creating the Android binary, Tauri will automatically detect it based on the naming convention:
- `python-sync-processor-aarch64-linux-android` for Android
- `python-sync-processor-x86_64-pc-windows-msvc.exe` for Windows

## Dependencies for Sidecar

The sidecar needs these minimal dependencies:
- `supabase>=2.0.0` - Supabase client
- `postgrest>=0.13.0` - PostgREST client (dependency)
- `pydantic>=2.9.0` - Data validation
- `python-dotenv==1.0.0` - Environment variables

Note: We don't need FastAPI, uvicorn, or other server dependencies for the sidecar.

## Next Steps

1. **Create Windows bundle** (for testing)
2. **Test bundled executable** with desktop Tauri app
3. **Create Android bundle** using Docker or WSL2
4. **Verify binary placement** in `frontend/src-tauri/binaries/`
5. **Proceed to Phase 6** (Android build)

