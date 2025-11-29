# Android Build and Installation - Files and Scripts Reference

## Overview
This document identifies all files and scripts involved in building and installing the Android APK using the commands:
- `.\scripts\run-with-ndk.ps1 -Target arm64 -DbPath ..\data\lesson_planner.db -JsonSourcePath "F:\rodri\Documents\OneDrive\AS"`
- `adb install -r .\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk`

---

## Main Build Scripts

### 1. `scripts/run-with-ndk.ps1`
**Purpose:** Entry point script that configures Android NDK environment and calls the main build script.

**Key Functions:**
- Locates Android NDK installation
- Sets up NDK environment variables (CC, AR, CARGO_TARGET_LINKER)
- Resolves database and JSON source paths
- Configures API URL and standalone DB mode
- Calls `build-android-offline.ps1`

**Parameters:**
- `-Target`: Architecture (arm64, armv7, x86_64, x86)
- `-Release`: Build release variant (default: debug)
- `-DbPath`: Path to SQLite database file
- `-JsonSourcePath`: Path to lesson JSON source files
- `-CacheSourcePath`: Path to pre-generated cache files
- `-ApiUrl`: API base URL (optional)

---

### 2. `scripts/build-android-offline.ps1`
**Purpose:** Main build script that orchestrates the entire Android APK build process.

**Key Functions:**
- **Step 1:** Builds frontend bundle (`npm run build:skip-check`)
- **Step 2:** Builds Rust shared library for Android target
- **Step 3:** Copies `.so` library to `jniLibs/`
- **Step 4:** Copies dist assets and bundles offline data (database + lesson JSON files)
- **Step 5:** Creates `.tauri` offline metadata
- **Step 6:** Mirrors configs at assets root
- **Step 7:** Runs Gradle to assemble APK

**Helper Functions:**
- `Get-WeekLabelFromFile`: Extracts week label from JSON metadata
- `Get-PlanIdFromFile`: Extracts plan ID from JSON content
- `Get-LessonFileNames`: Generates expected filenames (`<week_token>__<plan_id>.json`)
- `Copy-LessonPlanJson`: Copies and renames lesson JSON files
- `Sync-LessonPlanPayload`: Syncs lesson plans for multiple users

**Parameters:**
- `-Target`: Architecture target
- `-Release`: Release build flag
- `-DbPath`: Database file path
- `-LessonJsonSource`: Source path for lesson JSON files
- `-CacheSourcePath`: Pre-generated cache path

---

## Frontend Build Files

### 3. `frontend/package.json`
**Purpose:** Defines npm scripts and dependencies.

**Key Scripts:**
- `build:skip-check`: Builds frontend without TypeScript checks (used by build script)
- `build:tauri`: Builds frontend with Tauri environment

**Dependencies:**
- React, TypeScript, Vite
- Tauri plugins
- Shared packages (`@lesson-mode`, `@lesson-browser`, `@lesson-api`)

---

### 4. `frontend/vite.config.ts` (or `.js`)
**Purpose:** Vite build configuration.

**Key Settings:**
- Build output directory: `dist/`
- Path aliases for shared packages
- Tauri-specific configurations

---

### 5. `frontend/src-tauri/tauri.conf.json`
**Purpose:** Tauri application configuration.

**Key Settings:**
- `fullscreen: true` (for Android immersive mode)
- Window dimensions
- Security CSP settings
- Plugin configurations

---

### 6. `frontend/src-tauri/tauri.android.conf.json`
**Purpose:** Android-specific Tauri configuration.

**Key Settings:**
- `devUrl`: Set to `tauri://localhost` for offline mode
- Android build settings

---

## Rust Build Files

### 7. `frontend/src-tauri/Cargo.toml`
**Purpose:** Rust project configuration and dependencies.

**Key Dependencies:**
- `tauri` framework
- `tauri-plugin-*` plugins (http, shell, etc.)
- SQLite libraries
- Serde for JSON serialization

---

### 8. `frontend/src-tauri/src/lib.rs`
**Purpose:** Main Rust library entry point.

**Key Functions:**
- Initializes database connection
- Registers Tauri commands
- Configures Android-specific paths

**Tauri Commands:**
- `sql_query`, `sql_execute`
- `get_app_data_dir`
- `read_json_file`, `write_json_file`, `list_json_files`

---

### 9. `frontend/src-tauri/src/db_commands.rs`
**Purpose:** Implements database and file I/O Tauri commands.

**Key Functions:**
- SQLite query/execute operations
- JSON file read/write operations
- App data directory resolution

---

## Android Project Files

### 10. `frontend/src-tauri/gen/android/app/build.gradle.kts`
**Purpose:** Gradle build configuration for Android app.

**Key Settings:**
- Android SDK version
- Build variants (debug/release)
- Dependencies
- Rust build tasks

---

### 11. `frontend/src-tauri/gen/android/app/src/main/AndroidManifest.xml`
**Purpose:** Android app manifest.

**Key Settings:**
- Package name: `com.lessonplanner.browser`
- Permissions
- Activity configurations
- Fullscreen settings

---

### 12. `frontend/src-tauri/gen/android/app/src/main/assets/`
**Purpose:** Directory containing bundled assets.

**Contents:**
- `assets/`: Frontend dist bundle (HTML, JS, CSS)
- `databases/lesson_planner.db`: SQLite database
- `lesson-plans/<userId>/`: Renamed lesson JSON files
- `.tauri/`: Tauri runtime configuration
- `tauri.conf.json`, `tauri.android.conf.json`: Config mirrors

---

### 13. `frontend/src-tauri/gen/android/app/src/main/jniLibs/arm64-v8a/`
**Purpose:** Native libraries directory.

**Contents:**
- `liblesson_plan_browser.so`: Rust shared library for ARM64

---

## Android Kotlin/Java Files

### 14. `android/app/src/main/java/com/bilingual/lessonplanner/App.kt`
**Purpose:** Android Application class.

**Key Functions:**
- `onCreate()`: Calls `OfflineAssetSeeder.seedLessonPlanCache()`
- Application initialization

---

### 15. `android/app/src/main/java/com/bilingual/lessonplanner/utils/OfflineAssetSeeder.kt`
**Purpose:** Seeds bundled assets to internal storage.

**Key Functions:**
- `seedLessonPlanCache()`: Copies lesson JSON files from APK assets to internal storage
- `copyAssetFile()`: Copies individual asset files

**Target Location:**
- `/data/data/com.lessonplanner.browser/files/lesson-plans/<userId>/`

---

### 16. `android/app/src/main/java/com/bilingual/lessonplanner/MainActivity.kt`
**Purpose:** Main Android activity (if exists).

**Key Functions:**
- Launches Tauri WebView
- Handles app lifecycle

---

## Data Files

### 17. `../data/lesson_planner.db`
**Purpose:** SQLite database bundled into APK.

**Location in APK:**
- `assets/databases/lesson_planner.db`

**Tables:**
- `weekly_plans`: Lesson plan metadata
- `users`: User information
- Other lesson-related tables

---

### 18. `F:\rodri\Documents\OneDrive\AS\` (or specified `JsonSourcePath`)
**Purpose:** Source directory for lesson JSON files.

**Structure:**
- User folders (e.g., "Lesson Plan", "Daniela LP")
- JSON files with week metadata

**Processing:**
- Files are scanned for week labels and plan IDs
- Renamed to `<week_token>__<plan_id>.json` format
- Copied to `assets/lesson-plans/<userId>/`

---

## Build Output Files

### 19. `frontend/dist/`
**Purpose:** Frontend build output directory.

**Contents:**
- `index.html`: Main HTML file
- `assets/`: Compiled JS, CSS bundles

**Generated by:**
- `npm run build:skip-check` or `npm run build:tauri`

---

### 20. `frontend/src-tauri/target/aarch64-linux-android/debug/liblesson_plan_browser.so`
**Purpose:** Compiled Rust shared library.

**Generated by:**
- `cargo build --target aarch64-linux-android`

**Copied to:**
- `gen/android/app/src/main/jniLibs/arm64-v8a/liblesson_plan_browser.so`

---

### 21. `frontend/src-tauri/gen/android/app/build/outputs/apk/arm64/debug/app-arm64-debug.apk`
**Purpose:** Final Android APK file.

**Generated by:**
- Gradle `assembleArm64Debug` task

**Installed via:**
- `adb install -r app-arm64-debug.apk`

---

## Installation Command

### 22. `adb` (Android Debug Bridge)
**Purpose:** Command-line tool for Android device communication.

**Command:**
```powershell
adb install -r .\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk
```

**Parameters:**
- `-r`: Replace existing application
- APK path: Full path to generated APK

---

## Build Process Flow

1. **NDK Configuration** (`run-with-ndk.ps1`)
   - Locates NDK
   - Sets environment variables
   - Resolves paths

2. **Frontend Build** (`build-android-offline.ps1` Step 1)
   - Runs `npm run build:skip-check`
   - Outputs to `frontend/dist/`

3. **Rust Build** (`build-android-offline.ps1` Step 2)
   - Runs `cargo build --target aarch64-linux-android`
   - Outputs `.so` library

4. **Library Copy** (`build-android-offline.ps1` Step 3)
   - Copies `.so` to `jniLibs/arm64-v8a/`

5. **Asset Bundling** (`build-android-offline.ps1` Step 4)
   - Copies `dist/` to `assets/`
   - Bundles database to `assets/databases/`
   - Processes and renames lesson JSON files to `assets/lesson-plans/`

6. **Config Creation** (`build-android-offline.ps1` Steps 5-6)
   - Creates `.tauri/android-config.json`
   - Mirrors configs at assets root

7. **Gradle Build** (`build-android-offline.ps1` Step 7)
   - Runs `gradlew.bat assembleArm64Debug`
   - Generates APK

8. **Installation** (`adb install`)
   - Installs APK to connected Android device

---

## Key Configuration Values

- **Package Name:** `com.lessonplanner.browser`
- **Target Architecture:** `aarch64-linux-android` (ARM64)
- **Build Profile:** `debug` (or `release` with `-Release` flag)
- **Offline Mode:** `VITE_ENABLE_STANDALONE_DB=true`
- **API URL:** `http://10.0.2.2:8000/api` (default, overridden by `-ApiUrl`)
- **Dev URL:** `tauri://localhost` (for offline mode)

---

## File Naming Conventions

### Lesson JSON Files
- **Source Format:** `Wilson_Lesson_plan_W48_11-24-11-28_20251129.json`
- **Bundled Format:** `<week_token>__<plan_id>.json`
  - Example: `11%2F24-11%2F28__auto.json`
  - Week token is URL-encoded
  - Plan ID defaults to "auto" if not found

### User Directories
- **Format:** `<sanitized_user_id>/`
- **Example:** `04fe8898-cb89-4a73-affb-64a97a98f820/`

---

## Dependencies

### External Tools
- **Android NDK:** Required for Rust compilation
- **Cargo:** Rust package manager
- **Gradle:** Android build system
- **ADB:** Android Debug Bridge (for installation)
- **Node.js/npm:** Frontend build tools

### Environment Variables
- `ANDROID_NDK_HOME`: NDK installation path
- `VITE_API_BASE_URL`: API base URL
- `VITE_ENABLE_STANDALONE_DB`: Standalone database mode flag

---

## Troubleshooting

### Common Issues
1. **NDK not found:** Check `ANDROID_NDK_HOME` or NDK installation path
2. **Database not found:** Verify `-DbPath` points to existing file
3. **JSON files not bundled:** Check `-JsonSourcePath` and file structure
4. **APK not generated:** Check Gradle build logs
5. **Installation fails:** Verify device is connected and authorized (`adb devices`)

