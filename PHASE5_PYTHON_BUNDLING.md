# Phase 5: Python Bundling for Android

## Objective
Create a standalone Python executable that can run on Android devices as a Tauri sidecar.

## Current Status
- ✅ Binaries directory created: `frontend/src-tauri/binaries/`
- ✅ Bundling scripts created
- ⏳ Ready to build

## Approach

### Option 1: PyInstaller (Windows Development)
For initial testing on Windows, we can build a Windows executable:
```powershell
.\scripts\bundle_python.ps1
```

**Note**: This creates a Windows `.exe` file. For Android, we need a Linux ARM64 binary.

### Option 2: Docker Cross-Compilation (Recommended for Android)
For Android deployment, use Docker to build Linux ARM64 binary:
```bash
.\scripts\bundle_python_docker.sh
```

### Option 3: Manual Linux Build
If you have access to a Linux machine or WSL:
```bash
.\scripts\bundle_python.sh
```

## Dependencies to Include

The sidecar needs these modules:
- `backend` - Main backend package
- `backend.sidecar_main` - Entry point
- `backend.ipc_database` - IPC database adapter
- `backend.supabase_database` - Supabase client
- `backend.schema` - Data models
- `backend.database` - Database interface
- `backend.config` - Configuration
- `supabase` - Supabase Python client
- `postgrest` - PostgREST client
- `sqlmodel` - ORM
- `sqlalchemy` - Database toolkit
- `pydantic` - Data validation

## Binary Naming Convention

Tauri expects binaries named: `{name}-{target-triple}`

For Android ARM64: `python-sync-processor-aarch64-linux-android`

## Steps

### Step 1: Install PyInstaller
```powershell
pip install pyinstaller
```

### Step 2: Build Windows Binary (for testing)
```powershell
cd D:\LP
.\scripts\bundle_python.ps1
```

This will create:
- `frontend/src-tauri/binaries/python-sync-processor.exe` (Windows)

### Step 3: Build Android Binary (Linux ARM64)

**Option A: Using Docker (Recommended)**
```bash
.\scripts\bundle_python_docker.sh
```

**Option B: Using WSL/Linux**
```bash
wsl
cd /mnt/d/LP
bash scripts/bundle_python.sh
```

**Option C: Manual Build**
```bash
# On Linux or WSL
cd /path/to/project
pip install pyinstaller
pyinstaller --onefile \
    --name python-sync-processor \
    --hidden-import=backend \
    --hidden-import=backend.ipc_database \
    --hidden-import=backend.supabase_database \
    --hidden-import=backend.schema \
    --hidden-import=backend.database \
    --hidden-import=backend.config \
    --hidden-import=supabase \
    --hidden-import=postgrest \
    --hidden-import=sqlmodel \
    --hidden-import=sqlalchemy \
    --hidden-import=pydantic \
    --collect-all supabase \
    --collect-all postgrest \
    backend/sidecar_main.py

# Rename for Android
mv dist/python-sync-processor \
   frontend/src-tauri/binaries/python-sync-processor-aarch64-linux-android
```

## Testing the Binary

### Test Windows Binary (Desktop)
```powershell
# In Tauri app, the binary should be automatically detected
# Or test manually:
cd frontend/src-tauri/binaries
.\python-sync-processor.exe
# Should start and wait for stdin input
```

### Test Android Binary
```bash
# On Linux or Android device
chmod +x python-sync-processor-aarch64-linux-android
./python-sync-processor-aarch64-linux-android
# Should start and wait for stdin input
```

## Troubleshooting

### Issue: Missing Modules
If you get import errors, add to `--hidden-import`:
```bash
--hidden-import=missing.module.name
```

### Issue: Large Binary Size
PyInstaller bundles Python interpreter. Expected size: 50-100MB.
- This is normal for standalone executables
- Consider using Nuitka for smaller binaries (but more complex setup)

### Issue: Binary Not Found on Android
- Check binary name matches target triple
- Ensure binary is in `frontend/src-tauri/binaries/`
- Check file permissions (should be executable)

## Next Steps

After successful bundling:
1. ✅ Binary created in `frontend/src-tauri/binaries/`
2. ⏭️ Proceed to Phase 6: Android Build
3. ⏭️ Test on Android device/emulator

## Notes

- **Windows Build**: Good for testing IPC on desktop
- **Android Build**: Required for actual Android deployment
- **Size**: Expect 50-100MB for standalone Python executable
- **Performance**: First startup may be slower (extraction), then normal

