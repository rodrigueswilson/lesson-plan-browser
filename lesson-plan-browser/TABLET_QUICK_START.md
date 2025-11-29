# Quick Start: Physical Tablet Build

## 🚀 Quick Build & Install

### Prerequisites
- PC IP address (find with `ipconfig`)
- Backend running on PC (`http://PC_IP:8000`)
- Tablet and PC on same WiFi network

### Build APK

```powershell
cd lesson-plan-browser/frontend
.\build-tablet.ps1 -PC_IP "192.168.1.100"
```

**With standalone mode:**
```powershell
.\build-tablet.ps1 -PC_IP "192.168.1.100" -Standalone
```

### Install on Tablet

**Via ADB (USB connected):**
```powershell
adb install -r "src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release.apk"
```

**Via File Transfer:**
1. Copy APK to tablet
2. Open Files app → Tap APK → Install

---

## 📋 Pre-Build Checklist

- [ ] PC IP address identified (`ipconfig`)
- [ ] Backend running (`http://PC_IP:8000/api/health` accessible)
- [ ] Tablet and PC on same WiFi
- [ ] Dependencies installed (`npm install`)

---

## 🔧 Manual Build Steps

```powershell
cd lesson-plan-browser/frontend

# Set environment variables
$env:VITE_API_BASE_URL = "http://192.168.1.100:8000/api"
$env:VITE_ANDROID_API_BASE_URL = "http://192.168.1.100:8000/api"
$env:NODE_ENV = "production"
$env:TAURI_DEBUG = "false"

# Build
npm run build:skip-check
npm run tauri android build -- --release
```

---

## 📱 APK Locations

After build, find APK at:
- Universal: `src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release.apk`
- ARM64: `src-tauri/gen/android/app/build/outputs/apk/arm64-v8a/release/app-arm64-v8a-release.apk`

---

## 🐛 Troubleshooting

**Can't connect to backend?**
- Verify PC IP is correct
- Check backend: `curl http://PC_IP:8000/api/health`
- Ensure firewall allows port 8000
- Verify same WiFi network

**APK won't install?**
- Enable "Install from unknown sources"
- Uninstall old version: `adb uninstall com.lessonplanner.browser`
- Try ADB install instead

---

## 📚 Full Documentation

See `PHYSICAL_TABLET_BUILD_PLAN.md` for complete details.

