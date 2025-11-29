# Lesson Plan Browser

A streamlined Android tablet application for browsing lesson plans and using Lesson Mode for teaching.

## Features

- **Full Lesson Plan Browser** - Browse lesson plans by week, day, and lesson detail
- **Complete Lesson Mode** - Full teaching interface with timers, steps, and session management
- **Dual Data Sources** - Reads from both database and JSON files
- **Standalone Offline Architecture** - Works independently with local storage (Android)
- **Sync Capability** - WiFi and USB sync to receive updates from PC

## Architecture

### PC Version (Development)
- Connects to backend API (`http://localhost:8000`) for development/testing
- Uses HTTP backend for data access

### Android Version (Production)
- Uses local embedded SQLite database (Phase 9)
- Uses local JSON file storage (Phase 9)
- Works completely offline after sync
- Sync mechanism: WiFi (primary) or USB (fallback) to receive updates from PC

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
├── build-pc.ps1           # Build script for Windows
├── build-android.ps1      # Build script for Android
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
# From project root
.\build-pc.ps1

# Or manually
cd frontend
npm run tauri:build
```

## Android Build

### Quick Build
```bash
# From project root
.\build-android.ps1
```

### Manual Build
```bash
cd frontend
npm run android:build      # Release APK
npm run android:dev        # Debug APK (faster)
```

**Full Android build instructions:** See `ANDROID_BUILD_GUIDE.md`

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

- `TESTING_CHECKLIST.md` - Complete testing guide
- `SETUP_INSTRUCTIONS.md` - Detailed setup guide
- `ANDROID_BUILD_GUIDE.md` - Android build instructions
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
