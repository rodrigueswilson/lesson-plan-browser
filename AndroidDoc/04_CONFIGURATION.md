# Phase 4: Configuration Updates

## 4.1 Tauri Configuration (v2.0)

**File:** `frontend/src-tauri/tauri.conf.json`

**Note:** Using Tauri v2.0 format. Plugin configuration is in `Cargo.toml`, not `tauri.conf.json`.

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "Bilingual Lesson Planner",
  "version": "1.0.0",
  "identifier": "com.lessonplanner.bilingual",
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build:skip-check",
    "frontendDist": "../dist"
  },
  "app": {
    "windows": [
      {
        "fullscreen": false,
        "resizable": true,
        "title": "Bilingual Lesson Planner",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": false,
    "targets": "all"
  }
}
```

**Key Changes:**
- **No `devUrl`**: Uses bundled assets (`frontendDist`) for both dev and production
- **v2.0 format**: Simplified structure, plugins configured in `Cargo.toml`
- **Bundled assets**: Frontend must be built before running (`npm run build:skip-check`)
- **No SQL plugin config**: Using `rusqlite` directly

**Important:** Do NOT add `devUrl` - it causes blank screen issues. Always use bundled assets.

## 4.2 Cargo.toml Dependencies (v2.0)

**File:** `frontend/src-tauri/Cargo.toml`

```toml
[build-dependencies]
tauri-build = { version = "2.0", features = [] }

[dependencies]
tauri = { version = "2.0", features = ["devtools"] }
tauri-plugin-dialog = "2.0"
tauri-plugin-fs = "2.0"
tauri-plugin-http = "2.0"
tauri-plugin-shell = "2.0"
rusqlite = { version = "0.30", features = ["bundled", "serde_json"] }
base64 = "0.21"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1.0", features = ["full"] }
uuid = { version = "1.0", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
thiserror = "1.0"
log = "0.4"
```

**Key Plugins:**
- `tauri-plugin-shell`: For spawning Python sidecar (desktop and Android)
- `tauri-plugin-http`: For Supabase API calls
- `tauri-plugin-fs`: For file operations
- `tauri-plugin-dialog`: For file dialogs

## 4.3 Android Manifest Permissions

**File:** `frontend/src-tauri/gen/android/app/src/main/AndroidManifest.xml`

Add these permissions:

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    
    <!-- Network access for Supabase sync -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    
    <!-- Storage for documents -->
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    
    <!-- Keep app running during sync -->
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    
    <application
        android:allowBackup="true"
        android:label="@string/app_name"
        android:usesCleartextTraffic="true"
        android:networkSecurityConfig="@xml/network_security_config">
        
        <!-- ... existing activity config ... -->
        
    </application>
</manifest>
```

## 4.4 Network Security Config

**File:** `frontend/src-tauri/gen/android/app/src/main/res/xml/network_security_config.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">localhost</domain>
        <domain includeSubdomains="true">10.0.2.2</domain>
    </domain-config>
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">supabase.co</domain>
    </domain-config>
</network-security-config>
```

## 4.5 Sidecar Binary Configuration

**Directory Structure:**
```
frontend/src-tauri/binaries/
├── python-sync-processor-x86_64-pc-windows-msvc.exe    # Windows
├── python-sync-processor-x86_64-apple-darwin           # macOS Intel
├── python-sync-processor-aarch64-apple-darwin          # macOS ARM
├── python-sync-processor-x86_64-unknown-linux-gnu      # Linux
└── python-sync-processor-aarch64-linux-android         # Android
```

**Naming Convention:**
- Format: `{name}-{target-triple}[.exe]`
- Tauri auto-selects correct binary based on target platform

## 4.6 Environment Variables

**File:** `.env.android` (for Android builds)

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Python Sidecar Path (auto-resolved on Android)
PYTHON_SIDECAR_PATH=python-sync-processor

# Database Path (Android app data directory)
SQLITE_DB_PATH=/data/data/com.lessonplanner.bilingual/databases/lesson_planner.db

# Logging
LOG_LEVEL=INFO
```

## 4.7 Frontend API Updates

**File:** `frontend/src/lib/api.ts`

**Critical:** API URL detection for Tauri v2.0

```typescript
// Force API URL to bypass proxy issues in Tauri
const getApiUrl = (): string => {
  const userAgent = navigator.userAgent || '';
  
  // Check if running in Tauri v2.0 (correct detection method)
  const isTauri = typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
  
  if (userAgent.includes('Android')) {
    // Android emulator: use special host IP
    return 'http://10.0.2.2:8000/api';
  }
  
  // For Tauri desktop, use localhost (proxy doesn't work in Tauri)
  if (isTauri) {
    return 'http://localhost:8000/api';
  }
  
  // Fallback to config (for web browser with Vite proxy)
  return config.apiBaseUrl;
};

// Make API_BASE_URL a function to check at runtime
let _cachedApiUrl: string | null = null;
const getApiBaseUrl = (): string => {
  if (_cachedApiUrl === null) {
    _cachedApiUrl = getApiUrl();
  }
  return _cachedApiUrl;
};

// Sync function
export async function triggerSync(userId: string): Promise<SyncResult> {
  if (isDesktop) {
    // Use Tauri command for desktop/mobile
    const { invoke } = await import('@tauri-apps/api/core');
    return invoke<SyncResult>('trigger_sync', { userId });
  } else {
    // Browser fallback - direct HTTP to backend
    return apiRequest('/api/sync', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  }
}

export interface SyncResult {
  pulled: number;
  pushed: number;
  conflicts?: Array<{ id: string; error: string }>;
}
```

**Key Points:**
- **Tauri v2.0 detection**: Use `__TAURI_INTERNALS__` in window (not `window.__TAURI__`)
- **No proxy in Tauri**: Direct connection to `http://localhost:8000/api`
- **Android emulator**: Use `http://10.0.2.2:8000/api` (special emulator host IP)
- **Runtime evaluation**: API URL must be determined at runtime, not module load time

## 4.8 GitHub Actions CI

**File:** `.github/workflows/android-build.yml`

```yaml
name: Android Build

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build-android:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Java
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'
      
      - name: Setup Android SDK
        uses: android-actions/setup-android@v3
      
      - name: Setup NDK
        run: sdkmanager --install "ndk;26.1.10909125"
      
      - name: Setup Rust
        uses: dtolnay/rust-action@stable
        with:
          targets: aarch64-linux-android
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install Tauri CLI
        run: cargo install tauri-cli --version "^2.0"
      
      - name: Install dependencies
        working-directory: frontend
        run: npm ci
      
      - name: Build Android APK
        working-directory: frontend
        run: cargo tauri android build --target aarch64
        env:
          ANDROID_NDK_HOME: ${{ env.ANDROID_HOME }}/ndk/26.1.10909125
      
      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: android-apk
          path: frontend/src-tauri/gen/android/app/build/outputs/apk/
```
