# Phase 5 & 6: Build, Deploy, and Testing

## 5.1 Python Bundling for Android

### Option A: Nuitka (Recommended)

```bash
# Install Nuitka
pip install nuitka

# Build standalone executable (Linux host with cross-compile)
python -m nuitka \
    --standalone \
    --onefile \
    --include-module=backend \
    --include-module=backend.sidecar_main \
    --include-module=backend.ipc_database \
    --include-module=backend.supabase_database \
    --output-filename=python-sync-processor \
    backend/sidecar_main.py

# Move to Tauri binaries folder
mv python-sync-processor frontend/src-tauri/binaries/python-sync-processor-aarch64-linux-android
```

### Option B: PyInstaller (Windows/Desktop)

```bash
# For desktop builds
pyinstaller --onefile \
    --name python-sync-processor \
    --hidden-import=backend.ipc_database \
    --hidden-import=backend.supabase_database \
    backend/sidecar_main.py
```

### Option C: Docker Cross-Compile Environment

```dockerfile
# Dockerfile.android-python
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    patchelf \
    && rm -rf /var/lib/apt/lists/*

RUN pip install nuitka

WORKDIR /app
COPY backend/ ./backend/
COPY requirements.txt .

RUN pip install -r requirements.txt

RUN python -m nuitka \
    --standalone \
    --onefile \
    --output-filename=python-sync-processor \
    backend/sidecar_main.py

# Output in /app/python-sync-processor
```

```bash
# Build using Docker
docker build -f Dockerfile.android-python -t python-android-build .
docker cp $(docker create python-android-build):/app/python-sync-processor ./frontend/src-tauri/binaries/
```

## 5.2 Development Commands

### Desktop Development (Test IPC First)

**Important:** Test IPC bridge on desktop before attempting Android build.

```bash
cd frontend

# Start development server
cargo tauri dev

# Test IPC communication with Python sidecar
# Verify database operations work through IPC
# Test sync functionality

# Build desktop release
cargo tauri build
```

### Android Development

**Note:** Tauri v1.5 Android support may be limited. Test desktop IPC first.

```bash
cd frontend

# Initialize Android (first time only)
# May not work in Tauri v1.5 - test first
cargo tauri android init

# If init fails, you may need to:
# 1. Upgrade to Tauri v2.0, OR
# 2. Manually configure Android project

# Start Android development (with connected device/emulator)
cargo tauri android dev

# Build Android debug APK
cargo tauri android build --debug

# Build Android release APK
cargo tauri android build --target aarch64
```

## 5.3 Device Deployment

### Connect Android Device

```bash
# Enable USB debugging on tablet
# Settings > Developer Options > USB Debugging

# Verify connection
adb devices

# Should show:
# List of devices attached
# XXXXXXXX    device
```

### Install APK

```bash
# Install release APK
adb install -r frontend/src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release.apk

# Or install debug APK
adb install -r frontend/src-tauri/gen/android/app/build/outputs/apk/universal/debug/app-universal-debug.apk
```

### Launch App

```bash
# Start the app
adb shell am start -n com.lessonplanner.bilingual/.MainActivity

# View logs
adb logcat -s RustStdoutStderr:V BilingualLessonPlanner:V
```

### Uninstall (Clean Test)

```bash
adb uninstall com.lessonplanner.bilingual
```

## 5.4 Testing Checklist

### Unit Tests

| Test | Command | Status |
|------|---------|--------|
| Rust bridge | `cargo test -p bilingual-lesson-planner` | [ ] |
| Python IPC adapter | `pytest tests/test_ipc_database.py` | [ ] |
| Sidecar main | `pytest tests/test_sidecar_main.py` | [ ] |

### Integration Tests

| Test | Description | Status |
|------|-------------|--------|
| Desktop IPC | Verify Rust↔Python communication on desktop | [ ] |
| Android launch | App starts without crash | [ ] |
| SQLite creation | Database file created in app data | [ ] |
| Basic query | SELECT from local database works | [ ] |
| Basic insert | INSERT to local database works | [ ] |

### Sync Tests

| Test | Description | Status |
|------|-------------|--------|
| Pull sync | Data pulled from Supabase to local | [ ] |
| Push sync | Pending data pushed to Supabase | [ ] |
| Offline mode | App works without network | [ ] |
| Conflict handling | Merge conflicts resolved correctly | [ ] |

### End-to-End Tests

| Scenario | Steps | Expected | Status |
|----------|-------|----------|--------|
| Fresh install | Install app, open | Shows empty state | [ ] |
| Initial sync | Tap sync button | Users/slots pulled | [ ] |
| Create plan | Generate lesson plan | Saved locally | [ ] |
| Sync plan | Tap sync | Plan pushed to cloud | [ ] |
| Kill + reopen | Force close, reopen | Data persisted | [ ] |
| Offline use | Disable network, use app | All local features work | [ ] |

## 5.5 Debugging Commands

### View App Logs

```bash
# All app logs
adb logcat | grep -E "(bilingual|python|sidecar|sqlite)"

# Rust-specific logs
adb logcat -s RustStdoutStderr:V

# Filter by priority (V=verbose, D=debug, I=info, W=warn, E=error)
adb logcat *:E
```

### Inspect Database

```bash
# Pull database from device
adb exec-out run-as com.lessonplanner.bilingual cat databases/lesson_planner.db > local_db.sqlite

# Open with sqlite3
sqlite3 local_db.sqlite
.tables
SELECT * FROM users;
```

### Check Sidecar Process

```bash
# List running processes
adb shell ps | grep python

# Check if sidecar binary exists
adb shell run-as com.lessonplanner.bilingual ls -la
```

## 5.6 Release Build

### Generate Signed APK

```bash
# Create keystore (first time only)
keytool -genkey -v -keystore release-key.jks \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -alias bilingual-lesson-planner

# Build signed release
cd frontend
cargo tauri android build --target aarch64 -- \
    --keystore /path/to/release-key.jks \
    --keystore-password YOUR_PASSWORD \
    --key-alias bilingual-lesson-planner
```

### APK Location

```
frontend/src-tauri/gen/android/app/build/outputs/apk/
├── universal/
│   ├── debug/
│   │   └── app-universal-debug.apk
│   └── release/
│       └── app-universal-release.apk
└── arm64-v8a/
    └── release/
        └── app-arm64-v8a-release.apk
```

## 5.7 Quick Reference Commands

```bash
# === SETUP ===
rustup target add aarch64-linux-android
cargo install tauri-cli --version "^2.0"
cargo tauri android init

# === DEVELOPMENT ===
cargo tauri dev                    # Desktop
cargo tauri android dev            # Android emulator/device

# === BUILD ===
cargo tauri build                  # Desktop release
cargo tauri android build          # Android APK

# === DEPLOY ===
adb install -r path/to/app.apk    # Install
adb shell am start -n com.lessonplanner.bilingual/.MainActivity  # Launch

# === DEBUG ===
adb logcat -s RustStdoutStderr:V  # View logs
adb uninstall com.lessonplanner.bilingual  # Clean uninstall
```
