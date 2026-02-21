# Android Native App Archive

## Archive Date
December 7, 2025

## What Was Archived
The entire `android/` directory containing the native Android app (package: `com.bilingual.lessonplanner`).

## Why It Was Archived
This native Android app was replaced by the Tauri/web-based app (package: `com.lessonplanner.browser`). The native app is no longer in use and was causing confusion during database sync operations.

## Archive Contents
- Native Android app source code (Kotlin)
- Build configuration files
- AndroidManifest.xml
- All related documentation and setup files

## Current Active App
The active app is now:
- **Package**: `com.lessonplanner.browser`
- **Type**: Tauri/web-based application
- **Location**: `frontend/` directory
- **Database Path**: `/data/data/com.lessonplanner.browser/databases/lesson_planner.db`

## Deletion Schedule
**This archive can be safely deleted after: December 21, 2025 (2 weeks from archive date)**

If no issues arise with the Tauri app by that date, this archive can be permanently removed.

## Restoration Instructions
If needed, restore the archive by:
1. Extract the zip file to the project root
2. The `android/` directory will be restored
3. Rebuild the app using the instructions in `android/BUILD_INSTRUCTIONS.md`

## Notes
- The sync scripts have been updated to use `com.lessonplanner.browser` instead of `com.bilingual.lessonplanner`
- The Tauri app database path has been fixed to match the correct package name
- All database sync operations now target the Tauri app

## Related Files
- `scripts/sync-to-tablet.ps1` - Updated to use correct package name
- `frontend/src-tauri/src/lib.rs` - Fixed database path for Android

