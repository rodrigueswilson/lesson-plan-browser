# Deprecated Build and Install Scripts Archive

This directory contains archived build and installation scripts that have been replaced by the current build system.

## Current Active Scripts

The following scripts are **currently in use** and should **NOT** be modified or removed:

- `scripts/run-with-ndk.ps1` - Main entry point for Android builds
- `scripts/build-android-offline.ps1` - Main build orchestrator

## Archived Scripts

The following scripts have been archived because they are:
- Duplicates of current functionality
- Older versions replaced by newer scripts
- Experimental or one-off fixes
- No longer needed with the current build system

### Archived Files (as of 2025-01-XX)

#### Build Scripts

1. **`scripts_tablet_build.py`** - Python-based build script (replaced by PowerShell scripts)
2. **`frontend_build-tablet.ps1`** - Old tablet build script from frontend directory
3. **`build-android.ps1`** - Old Android build script
4. **`root_rebuild-android.ps1`** - Duplicate rebuild script from root
5. **`build-pc.ps1`** - PC build script (may be deprecated)
6. **`root_build-android-offline.ps1`** - Duplicate build script from root (current version is in `scripts/`)

#### Install Scripts

7. **`install-android-app.ps1`** - Old installer script from lesson-plan-browser directory
8. **`root_install-android-app.ps1`** - Duplicate installer script from root
9. **`root_rebuild-and-fresh-install.ps1`** - Old rebuild and install script
10. **`root_fresh-install.ps1`** - Old fresh install script
11. **`root_check-install-status.ps1`** - Old status check utility

### Note on File Naming

Files are archived with prefixes to indicate their original location:
- `root_*` - Files from the root directory (`D:\LP\`)
- `frontend_*` - Files from `frontend/` directory
- `scripts_*` - Files from `scripts/` directory
- `backend_*` - Files from `backend/` directory (if any were found)

### Files Not Found (may have been deleted already)

The following files were searched for but not found (may have been removed previously):
- `frontend/src-tauri/build-tablet.ps1`
- `frontend/src-tauri/build-and-install-tablet.ps1`
- `frontend/fix_build_watch.ps1`
- `frontend/fix_build_watch_v2.ps1`
- `frontend/src-tauri/post-build-copy.ps1`
- `frontend/src-tauri/fix-android-abi.ps1`
- `frontend/src-tauri/apply-android-network-fix.ps1`
- `frontend/src-tauri/android-dev-workaround.ps1`
- `frontend/android-dev-workaround.ps1`
- `frontend/android-dev.ps1`
- `backend/docker-build-android.ps1`
- `backend/build_sidecar.ps1`

## Restoration

If you need to restore any of these scripts:

1. Copy the file from this archive back to its original location
2. Review the script to ensure it's compatible with the current codebase
3. Test thoroughly before using in production
4. Consider updating it to match current build patterns

## Notes

- All scripts were archived on: 2025-01-XX
- Current build system uses: `run-with-ndk.ps1` → `build-android-offline.ps1`
- Installation is now done via: `adb install -r <apk-path>`

