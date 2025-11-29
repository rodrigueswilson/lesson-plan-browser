# Android Bundle Creation - Approach

## Challenge

Android requires ARM64 (aarch64) binaries, but:
- Docker builds on Linux x86_64 by default
- Cross-compiling Python to ARM64 is complex
- PyInstaller/Nuitka don't easily cross-compile to Android

## Solutions

### Option 1: Use PyInstaller on Linux (Simplest)

Build on a Linux system (WSL2, VM, or CI):

```bash
# In Linux environment
cd /path/to/project
pip install pyinstaller supabase postgrest pydantic python-dotenv

pyinstaller --onefile \
    --name python-sync-processor \
    --hidden-import=backend.ipc_database \
    --hidden-import=backend.supabase_database \
    --hidden-import=backend.schema \
    --hidden-import=backend.config \
    --hidden-import=backend.database_interface \
    --hidden-import=supabase \
    --hidden-import=postgrest \
    --hidden-import=pydantic \
    backend/sidecar_main.py

# The binary will be Linux x86_64, but Tauri might handle it
# OR we need to build on ARM64 hardware/emulator
```

### Option 2: Use Python for Android (Chaquopy/BeeWare)

Use a Python runtime designed for Android:
- **Chaquopy** - Python runtime for Android
- **BeeWare** - Python apps for mobile
- **Kivy** - Python framework with Android support

This requires significant changes to the architecture.

### Option 3: Build on Android Emulator/Device

Run PyInstaller directly on Android:
1. Set up Android emulator with Linux environment
2. Install Python and dependencies
3. Build binary on the emulator
4. Extract the binary

### Option 4: Use Pre-built Python Runtime

Bundle Python runtime with the app and run Python scripts directly:
- Include Python interpreter in APK
- Run `python -m backend.sidecar_main` instead of bundled executable
- Tauri can spawn Python interpreter

### Option 5: Simplified Approach (Recommended for Now)

For initial testing, we can:
1. Keep using `python -m backend.sidecar_main` in development
2. For production, bundle Python runtime with the app
3. Or use a Python runtime like Chaquopy

## Recommended Next Steps

Since cross-compilation is complex, let's:

1. **For Development**: Continue using `python -m backend.sidecar_main`
2. **For Production**: Consider bundling Python runtime or using Chaquopy
3. **Alternative**: Build on actual Android device/emulator

## Current Status

- ✅ Windows bundle created (for desktop testing)
- ⏸️ Android bundle: Requires different approach
- ✅ All bundling scripts ready
- ✅ Dockerfile created (but needs ARM64 setup)

## Decision Needed

Choose one:
1. Proceed with Phase 6 using `python -m backend.sidecar_main` (simpler, requires Python on device)
2. Set up proper Android ARM64 cross-compilation (complex, but standalone)
3. Use Python runtime bundling (middle ground)

