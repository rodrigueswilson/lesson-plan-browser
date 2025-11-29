# Phase 1: Environment Setup

## 1.1 Prerequisites

### Required Software

```bash
# Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Android targets for Rust
rustup target add aarch64-linux-android
rustup target add armv7-linux-androideabi
rustup target add i686-linux-android
rustup target add x86_64-linux-android

# Tauri CLI (current version - v1.5)
# Note: Android support in Tauri v1.5 may be limited
# If android init doesn't work, may need to upgrade to v2.0
cargo install tauri-cli
# Or for v2.0: cargo install tauri-cli --version "^2.0"
```

### Android SDK/NDK Setup

```bash
# Required components (via Android Studio or sdkmanager):
# - Android SDK Platform 33+
# - Android SDK Build-Tools
# - NDK 26.1.10909125
# - Android SDK Command-line Tools

# Environment variables (add to shell profile)
export ANDROID_HOME=$HOME/Android/Sdk
export ANDROID_SDK_ROOT=$ANDROID_HOME
export ANDROID_NDK_HOME=$ANDROID_HOME/ndk/26.1.10909125
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

### Windows-Specific Setup

```powershell
# Set environment variables
[Environment]::SetEnvironmentVariable("ANDROID_HOME", "$env:LOCALAPPDATA\Android\Sdk", "User")
[Environment]::SetEnvironmentVariable("ANDROID_NDK_HOME", "$env:LOCALAPPDATA\Android\Sdk\ndk\26.1.10909125", "User")
```

## 1.2 Verify Installation

```bash
# Check Rust targets
rustup target list --installed | grep android

# Check Tauri CLI
cargo tauri --version

# Check Android SDK
sdkmanager --version
adb --version
```

## 1.3 Initialize Tauri Android Project

**Note:** Tauri v1.5 Android support may be limited. Test `cargo tauri android init` first.

```bash
cd d:\LP\frontend

# Try to initialize Android support (may not work in v1.5)
cargo tauri android init

# If this fails, you may need to:
# 1. Upgrade to Tauri v2.0, OR
# 2. Manually set up Android project structure

# This should create:
# - src-tauri/gen/android/  (Android project files)
# - Updates Cargo.toml with mobile support
```

**Alternative:** If Android init fails, start with desktop IPC testing first, then tackle Android setup.

## 1.4 NDK Linker Configuration

Create `frontend/src-tauri/.cargo/config.toml`:

```toml
[target.aarch64-linux-android]
linker = "aarch64-linux-android21-clang"

[target.armv7-linux-androideabi]
linker = "armv7a-linux-androideabi21-clang"

[target.i686-linux-android]
linker = "i686-linux-android21-clang"

[target.x86_64-linux-android]
linker = "x86_64-linux-android21-clang"
```

## 1.5 Project Structure After Setup

```
d:\LP\frontend\
├── src/                          # React frontend (unchanged)
├── src-tauri/
│   ├── Cargo.toml                # Updated with rusqlite, keep Tauri v1.5
│   ├── tauri.conf.json           # Updated for v1.5 + sidecar config
│   ├── .cargo/
│   │   └── config.toml           # NDK linker config
│   ├── src/
│   │   ├── main.rs               # Updated with IPC bridge
│   │   ├── lib.rs                # Mobile entry point (new)
│   │   ├── bridge.rs             # Sidecar IPC bridge (new)
│   │   └── db_commands.rs        # SQL commands (new)
│   ├── binaries/                 # Python sidecar binaries (new)
│   └── gen/
│       └── android/              # Generated Android project
```
