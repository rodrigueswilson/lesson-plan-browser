# Lesson Plan Browser

A streamlined Android tablet application for browsing lesson plans and using Lesson Mode for teaching.

## Features

- **Full Lesson Plan Browser** - Browse lesson plans by week, day, and lesson detail
- **Complete Lesson Mode** - Full teaching interface with timers, steps, and session management
- **Dual Data Sources** - Reads from both database and JSON files
- **Standalone Offline Architecture** - Works independently with local storage (Android)
- **Sync Capability** - WiFi and USB sync to receive updates from PC

## Architecture

### Unified Frontend

The frontend is now **unified** - a single codebase that automatically detects platform (PC vs tablet) and adapts its UI and features accordingly.

- **PC Mode**: Full application with navigation (Home, Schedule, Browser, Lesson Mode, History, Analytics)
- **Tablet Mode**: Browser and Lesson Mode only (no navigation, full-screen experience)
- **Platform Detection**: Automatic detection of Android Tauri vs Desktop Tauri
- **Feature Gating**: PC-only features lazy loaded and excluded from tablet bundle

**See**: [Unified Frontend Implementation Guide](../../docs/implementation/UNIFIED_FRONTEND_IMPLEMENTATION_GUIDE.md) for complete architecture details.

### PC Version (Development)
- Connects to backend API (`http://localhost:8000`) for development/testing
- Uses HTTP backend for data access
- Uses unified frontend with platform detection

### Android Version (Production)
- Uses local embedded SQLite database (Phase 9)
- Uses local JSON file storage (Phase 9)
- Works completely offline after sync
- Sync mechanism: WiFi (primary) or USB (fallback) to receive updates from PC
- Uses unified frontend with platform detection (tablet mode)

## Project Structure

```
lesson-plan-browser/
├── frontend/              # React + Tauri app
│   ├── src/
│   │   ├── components/    # Browser and Lesson Mode components
│   │   ├── lib/           # API client (dual mode: HTTP for PC, local DB for Android)
│   │   ├── hooks/         # Timer hooks
│   │   ├── store/         # State management
│   │   └── utils/         # Utilities
│   └── src-tauri/         # Tauri configuration and Rust backend
├── scripts/               # Build and utility scripts
│   ├── run-with-ndk.ps1   # Canonical Android APK builder (entry point)
│   ├── build-android-offline.ps1  # Canonical Android APK builder (main orchestrator)
│   └── archive/           # Archived deprecated scripts
└── README.md              # This file
```

## Prerequisites

- **Node.js** 18+
- **Rust** (latest stable)
- **Tauri CLI** v2.0: `npm install -g @tauri-apps/cli@latest`
- **Backend Server** (for PC version): FastAPI running on `http://localhost:8000`

### Android Build Additional Requirements
- **Java JDK** 17+
- **Android SDK** (via Android Studio or command-line tools)
- **Rust Android targets** (see `ANDROID_BUILD_GUIDE.md`)

## Setup

```bash
cd frontend
npm install
```

## Development

### Run PC Version
```bash
cd frontend
npm run tauri:dev
```

Requires backend running on `http://localhost:8000`.

### Build PC Version
```bash
# Or manually
cd frontend
npm run tauri:build
```

## Android Build

### Canonical Build Scripts

The **canonical** and **only supported** scripts for building Android APKs are:

1. **`scripts/run-with-ndk.ps1`** - Main entry point that configures NDK environment
2. **`scripts/build-android-offline.ps1`** - Main build orchestrator (called by run-with-ndk.ps1)

> **Note:** These scripts became the canonical builders on **November 29, 2025**. All other build scripts have been archived (see `scripts/archive/deprecated-build-scripts/`).

### Building Android APK

#### Standard Build Command
```powershell
# From project root (lesson-plan-browser/)
.\scripts\run-with-ndk.ps1 -Target arm64 -DbPath ..\data\lesson_planner.db -JsonSourcePath "F:\rodri\Documents\OneDrive\AS"
```

#### Parameters
- `-Target`: Architecture (`arm64`, `armv7`, `x86_64`, `x86`) - Default: `arm64`
- `-DbPath`: Path to SQLite database file (required)
- `-JsonSourcePath`: Path to lesson JSON source files (optional)
- `-CacheSourcePath`: Path to pre-generated cache files (optional, alternative to JsonSourcePath)
- `-Release`: Build release variant (default: debug)
- `-ApiUrl`: API base URL (optional, defaults to `http://10.0.2.2:8000/api`)

#### Installing the APK
```powershell
# After build completes, install on connected device
adb install -r .\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk
```

#### Build Process
The build script performs these steps:
1. Configures Android NDK environment
2. Builds frontend bundle (`npm run build:skip-check`)
3. Compiles Rust library for Android target
4. Copies native library to `jniLibs/`
5. Bundles assets (dist, database, lesson JSON files)
6. Creates offline metadata configuration
7. Runs Gradle to assemble APK

**Full Android build instructions:** See `ANDROID_BUILD_GUIDE.md` or `docs/android-build-install-files.md`

## Testing

See `TESTING_CHECKLIST.md` for detailed test cases.

### Quick Test Checklist
- [ ] App launches
- [ ] User selection works
- [ ] Browser view loads
- [ ] Can navigate to Lesson Mode
- [ ] Timer works
- [ ] Session saves/restores

## Documentation

- **[Unified Frontend Implementation Guide](../../docs/implementation/UNIFIED_FRONTEND_IMPLEMENTATION_GUIDE.md)** - Complete guide for unified frontend architecture and implementation
- `TESTING_CHECKLIST.md` - Complete testing guide
- `SETUP_INSTRUCTIONS.md` - Detailed setup guide
- `ANDROID_BUILD_GUIDE.md` - Android build instructions
- `docs/android-build-install-files.md` - Complete reference for Android build files and scripts
- `QUICK_START.md` - Quick start guide
- `PROJECT_STATUS.md` - Current project status

## Project Status

**Completed Phases (1-7):**
- ✅ Project structure & setup
- ✅ All components copied
- ✅ Dual-mode API client
- ✅ Navigation & entry point
- ✅ Tauri configuration
- ✅ Testing documentation
- ✅ Android build scripts

**Remaining Phases:**
- ⏳ Phase 8: Bundle optimization
- ⏳ Phase 9: Standalone architecture (local DB + sync) - **REQUIRED for Android**

See `PROJECT_STATUS.md` for detailed status.

## License

Same as main project.
