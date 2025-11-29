# Docker Android Build Environment

This Docker setup bypasses the persistent Tauri Android caching issues by providing a clean, isolated build environment.

## Quick Start

### 1. Build and Run
```bash
# From LP root directory
chmod +x docker/build-android.sh
./docker/build-android.sh
```

### 2. Extract APK
```bash
# After build completes
docker cp tauri-android-builder:/app/frontend/src-tauri/gen/android/app/build/outputs/apk/arm64/debug/app-arm64-debug.apk ./app-arm64-debug.apk
```

### 3. Install on Device
```bash
adb install app-arm64-debug.apk
```

## Manual Docker Commands

### Build Only
```bash
docker-compose build android-builder
```

### Interactive Development
```bash
docker-compose run --rm android-builder /bin/bash
# Inside container:
cd /app/frontend
npm run tauri android dev
```

### Clean Build
```bash
# Remove all caches and rebuild
docker-compose down -v
docker system prune -f
./docker/build-android.sh
```

## Docker Compose Services

### android-builder
- **Base Image**: `node:20-bullseye`
- **Rust**: Latest stable via rustup
- **Android SDK**: API 33 with NDK 25.1.8937393
- **Targets**: aarch64, armv7, x86_64, i686
- **Tauri CLI**: v2.x

### Volumes
- `android-build-cache`: Cargo registry and dependencies
- `android-sdk-cache`: Android SDK and NDK
- Source code mounted for live development

## Environment Variables

The container automatically configures:
- `ANDROID_SDK_ROOT=/opt/android-sdk`
- `ANDROID_NDK_ROOT=/opt/android-sdk/ndk/25.1.8937393`
- Rust target linkers for all Android architectures
- Tauri CLI in PATH

## Troubleshooting

### Build Fails with "Permission Denied"
```bash
chmod +x docker/build-android.sh
```

### Docker Not Running
Start Docker Desktop or Docker Engine before running the script.

### Port Already in Use
```bash
# Check what's using port 1420
netstat -tulpn | grep :1420
# Or use different port in docker-compose.yml
```

### Cache Issues
```bash
# Clean all Docker caches
docker-compose down -v
docker system prune -af
docker volume prune -f
```

### ADB Connection Issues
```bash
# Ensure ADB can see your device
adb devices
# If not found, check USB debugging and drivers
```

## Advantages of Docker Approach

1. **Clean Environment**: No local caching issues
2. **Reproducible**: Same environment every time
3. **Isolated**: Doesn't affect local development setup
4. **Portable**: Works on any system with Docker
5. **Version Control**: Environment defined in code

## Performance Notes

- First build: ~10-15 minutes (downloads all dependencies)
- Subsequent builds: ~2-5 minutes (uses cached volumes)
- APK size: ~25MB (same as local build)

## File Locations

Inside container:
- Source code: `/app/frontend`
- Build output: `/app/frontend/src-tauri/gen/android/`
- APK: `/app/frontend/src-tauri/gen/android/app/build/outputs/apk/arm64/debug/app-arm64-debug.apk`

## Development Workflow

1. Make code changes locally
2. Run `./docker/build-android.sh`
3. Extract and test APK
4. Repeat

This ensures every build uses a fresh environment while preserving your source code changes.
