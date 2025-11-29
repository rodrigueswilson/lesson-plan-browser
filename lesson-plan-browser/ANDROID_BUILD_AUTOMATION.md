# Android Standalone Build & Automation Guide

This document records the current end-to-end process for producing tablet APKs, the relevant configuration points (Tauri, Vite, Cargo, env files), and a blueprint for scripting the workflow. It draws heavily on the official docs you already reviewed:

- [Tauri Prerequisites](https://tauri.app/start/prerequisites/)
- [Tauri Environment Variables](https://v2.tauri.app/reference/environment-variables/)
- [Vite: Env Variables & Modes](https://vite.dev/guide/env-and-mode.html)
- [Cargo Target Configuration](https://doc.rust-lang.org/cargo/reference/config.html#target)

---

## 1. Prerequisites & Global Setup

1. **Toolchain** (per the Tauri prereq guide):
   - Node.js 18+ (ships `npm`), Rust stable, MSVC build tools, Android SDK (platform tools + build-tools 33+), Android NDK (r29+), Java JDK 17.
   - Ensure `%LOCALAPPDATA%\Android\Sdk\platform-tools` and `...\build-tools\xx.x.x` are on `PATH` so `adb`, `aapt`, etc. are available.

2. **Cargo cross-linkers**  
   `frontend/src-tauri/.cargo/config.toml` pins the Android clang/ar binaries, so you do **not** need to export `CC_*` manually each time:
   ```toml
   [target.aarch64-linux-android]
   ar = "C:/Users/<user>/AppData/Local/Android/Sdk/ndk/29.0.14206865/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-ar.exe"
   linker = "C:/Users/<user>/AppData/Local/Android/Sdk/ndk/29.0.14206865/toolchains/llvm/prebuilt/windows-x86_64/bin/aarch64-linux-android30-clang.cmd"
   ```

3. **ADB device prep**
   - Enable Developer Options + USB debugging on the tablet.
   - `adb devices` should list the tablet (`R52Y90L71YP` in our case).

---

## 2. Environment Management

Vite only exposes variables prefixed with `VITE_`. Instead of editing `.env` in place, we store committed templates in `frontend/env/`:

| File | Purpose |
|------|---------|
| `env/desktop.env` | WiFi/PC-connected or emulator builds (`VITE_ENABLE_STANDALONE_DB=false`) |
| `env/android.env` | Tablet standalone mode (`VITE_ENABLE_STANDALONE_DB=true`, `TAURI_DEBUG=false`) |

`scripts/select-env.mjs` copies the appropriate template into `.env.local` before every dev/build command. `scripts/run-vite.mjs` then:

1. Runs `select-env`.
2. Detects `TAURI_ENV_PLATFORM` / `TAURI_ENV_TARGET_TRIPLE`.
3. Calls `npx vite` with `--mode android` whenever an Android build is detected (per the Vite mode rules).

The npm scripts wrap this behavior:

```jsonc
// package.json
"prepare:env": "node ./scripts/select-env.mjs",
"dev:tauri": "node ./scripts/run-vite.mjs dev",
"build:tauri": "node ./scripts/run-vite.mjs build"
```

`tauri.conf.json` now points `beforeDevCommand`/`beforeBuildCommand` at those scripts, so Android Studio/Gradle inherits the same env logic automatically.

---

## 3. Manual Build Flow (Current State)

### 3.1 Debug loop (fast iteration)

1. **Start the Tauri Android dev driver** (keep running):
   ```powershell
   cd D:\LP\lesson-plan-browser\frontend
   npx tauri android dev R52Y90L71YP
   ```
2. **Gradle build + install** in a second shell:
   ```powershell
   cd D:\LP\lesson-plan-browser\frontend\src-tauri\gen\android
   .\gradlew.bat assembleArm64Debug
   adb -s R52Y90L71YP install -r -d .\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk
   adb -s R52Y90L71YP shell am start -n com.lessonplanner.browser/.MainActivity
   ```

### 3.2 Tablet-ready bundle (standalone mode)

1. **Force android mode + production env**:
   ```powershell
   cd D:\LP\lesson-plan-browser\frontend
   $env:TAURI_ENV_PLATFORM = "android"
   $env:TAURI_ENV_TARGET_TRIPLE = "aarch64-linux-android"
   npm run build:tauri
   ```
2. **Gradle** (inherits the env above, linker config already set in `.cargo/config.toml`):
   ```powershell
   cd src-tauri/gen/android
   .\gradlew.bat assembleArm64Debug
   ```
3. **Install + restart** (same as debug flow).

4. **Seed / refresh the local SQLite DB** (optional but often required):
   ```powershell
   adb -s R52Y90L71YP push data\lesson_planner.db /data/local/tmp/lesson_planner.db
   adb -s R52Y90L71YP shell run-as com.lessonplanner.browser mkdir -p databases
   adb -s R52Y90L71YP shell run-as com.lessonplanner.browser cp /data/local/tmp/lesson_planner.db databases/lesson_planner.db
   adb -s R52Y90L71YP shell rm /data/local/tmp/lesson_planner.db
   adb -s R52Y90L71YP shell am force-stop com.lessonplanner.browser
   adb -s R52Y90L71YP shell am start -n com.lessonplanner.browser/.MainActivity
   ```

---

## 4. Automation Blueprint

To avoid typing the same commands repeatedly, we can wrap the workflow in a PowerShell script (Python would work too). Suggested entry point: `scripts/build-tablet.ps1`.

### Parameters

```powershell
param(
  [ValidateSet("debug","release")] [string]$Mode = "debug",
  [string]$Device = "R52Y90L71YP",
  [switch]$Install,
  [switch]$SeedDb,
  [string]$DbSource = "D:\LP\data\lesson_planner.db"
)
```

### Steps inside the script

1. **Sync env & Vite build**
   ```powershell
   cd $repo\frontend
   npm run prepare:env
   $env:TAURI_ENV_PLATFORM = "android"
   $env:TAURI_ENV_TARGET_TRIPLE = "aarch64-linux-android"
   npm run build:tauri   # `Mode` can control NODE_ENV / TAURI_DEBUG flags if needed
   ```
2. **Gradle**
   ```powershell
   cd $repo\frontend\src-tauri\gen\android
   .\gradlew.bat assembleArm64Debug
   ```
3. **Install (if `-Install` supplied)**
   ```powershell
   $apk = ".\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
   adb -s $Device install -r -d $apk
   ```
4. **Optional DB seed**
   ```powershell
   if ($SeedDb) {
     adb -s $Device push $DbSource /data/local/tmp/lesson_planner.db
     adb -s $Device shell run-as com.lessonplanner.browser mkdir -p databases
     adb -s $Device shell run-as com.lessonplanner.browser cp /data/local/tmp/lesson_planner.db databases/lesson_planner.db
     adb -s $Device shell rm /data/local/tmp/lesson_planner.db
   }
   adb -s $Device shell am force-stop com.lessonplanner.browser
   adb -s $Device shell am start -n com.lessonplanner.browser/.MainActivity
   ```

### Convenience `.bat` wrappers

Create thin wrappers in the repo root:

- `build-tablet-debug.bat`
  ```bat
  @echo off
  powershell -ExecutionPolicy Bypass -File scripts\build-tablet.ps1 -Mode debug -Install -SeedDb
  ```
- `build-tablet-release.bat`
  ```bat
  @echo off
  powershell -ExecutionPolicy Bypass -File scripts\build-tablet.ps1 -Mode release -Install
  ```

These wrappers allow a single double-click (or CI job) to run the entire sequence.

---

## 4.1 Python automation (`scripts/tablet_build.py`)

For a cross-platform option (and for richer logging/archiving), we now have `scripts/tablet_build.py`. Key features:

```bash
# Build + archive only
python scripts/tablet_build.py --mode release

# Build + install + seed DB
python scripts/tablet_build.py --mode release --install --seed-db \
  --db-path D:\LP\data\lesson_planner.db --device R52Y90L71YP \
  --log-file dist\logs\tablet-$(Get-Date -Format yyyyMMdd-HHmm).log

# Roll back to a prior archive without rebuilding
python scripts/tablet_build.py --rollback-apk dist/apk/tablet-20250115-1430-release.apk --install
```

What the script does:

1. Runs `npm run prepare:env` + `npm run build:tauri` with the Android env/mode.
2. Calls `gradlew.bat assembleArm64Debug`.
3. Copies the resulting APK to `dist/apk/tablet-<timestamp>-<mode>.apk`.
4. (Optional) Installs it on the tablet via `adb`, seeds `lesson_planner.db`, and restarts the app.
5. Logs to stdout and, optionally, to `--log-file`.

Use this script if you prefer Python-based orchestration or want timestamped APK archives for quick rollback.

---

## 5. Future Enhancements

1. **CI Integration** – Wire the PowerShell script into GitHub Actions to produce nightly debug APKs, archive them as artifacts, and optionally push to a device farm.
2. **Signed release flow** – Extend the script to run `assembleArm64Release`, call `apksigner`, and upload to an internal distribution channel.
3. **Log capture & validation** – Add optional flags to collect `adb logcat -d | Select-String "[API]"` output into `build-logs/`.
4. **`adb` device auto-detect** – Query `adb devices` if `-Device` is omitted.

---

## 6. Related Docs

- `TABLET_INSTALLATION_GUIDE.md` – high-level steps for installing on physical hardware.
- `PHYSICAL_TABLET_BUILD_PLAN.md` – historical build plan (prepend a link pointing to this new automation-focused guide).
- `PROJECT_STATUS.md` – architecture notes now mentioning the env-sync scripts and Cargo linker config.

Whenever we iterate on the automation script, update this guide and the related docs so the flow stays discoverable for future contributors.

