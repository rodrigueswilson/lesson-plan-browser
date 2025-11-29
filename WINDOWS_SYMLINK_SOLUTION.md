# Windows Symlink Issue - Solutions

## Problem
Tauri Android build fails on Windows because it tries to create a symbolic link, which requires Developer Mode.

## Solutions

### Option 1: Enable Developer Mode (Recommended)
1. Open Windows Settings
2. Go to **Privacy & Security** → **For developers**
3. Enable **Developer Mode**
4. Restart your computer
5. Builds will work automatically

### Option 2: Manual Copy (Current Workaround)
After each Rust build, manually copy the library:
```powershell
cd frontend/src-tauri
.\copy_lib.ps1
```

Or use the npm script:
```powershell
cd frontend
npm run android:copy-lib
```

### Option 3: Automated Copy Script
I've created a script that runs automatically. Use:
```powershell
cd frontend
npm run android:dev
```

This will copy the library and then start the Android dev build.

## Why This Happens
- Windows requires special permissions to create symbolic links
- Tauri tries to symlink the `.so` file for faster builds
- Without Developer Mode, Windows blocks symlink creation
- Copying the file works but is slower

## Long-term Solution
Enable Developer Mode for the best development experience. It's safe and required for many development tools.

## Current Workaround
Since Tauri tries to create the symlink during the build process (after our pre-copy), you have two options:

1. **Enable Developer Mode** (recommended) - This is the cleanest solution
2. **Manual workaround**: After the build fails on symlink, run:
   ```powershell
   cd frontend
   npm run android:copy-lib
   cd src-tauri/gen/android
   .\gradlew assembleDebug
   ```

The symlink error happens because Tauri tries to create it AFTER the Rust build, even though we've already copied the file. The file is there, but Tauri's symlink attempt still fails.

