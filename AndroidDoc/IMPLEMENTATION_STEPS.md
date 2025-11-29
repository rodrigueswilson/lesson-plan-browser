# Complete Implementation Steps: Android Sidecar

**Goal:** Complete Phases 5-6 to enable standalone Android app with Python sidecar

**Prerequisites:** Phases 0-4 complete ✅ (IPC, Rust, Python adapter, config)

**Current Status:**
- Desktop IPC: ✅ Working (spawns Python process)
- Android IPC: ❌ Stub only (returns error)
- Python sidecar: ✅ Implemented (not bundled)
- Binary bundling: ⚠️ Partial (desktop binaries exist, Android missing)

---

## Phase 5: Python Bundling & Desktop Testing

### Step 5.1: Verify Desktop Sidecar Works (Source Mode)

**Goal:** Ensure the sidecar works when spawned from source before bundling

**Actions:**
1. **Test current desktop IPC:**
   ```bash
   cd d:\LP\frontend
   cargo tauri dev
   ```

2. **Trigger sync from UI:**
   - Open app
   - Navigate to sync functionality
   - Trigger sync and verify it works
   - Check console for any errors

3. **Verify IPC communication:**
   - Check that Python sidecar receives commands
   - Verify SQL queries flow through IPC
   - Confirm Supabase sync works

**Success Criteria:**
- ✅ App launches without errors
- ✅ `trigger_sync()` command executes
- ✅ Python sidecar spawns and responds
- ✅ Database operations work via IPC

**If Issues:**
- Check Python path in `lib.rs` (line 104-106)
- Verify `backend` module is importable
- Check project root detection logic (lines 110-132)

---

### Step 5.2: Bundle Python Sidecar for Desktop

**Goal:** Create standalone binary that works without Python installation

**Option A: PyInstaller (Windows/Desktop - Recommended for Testing)**

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Create spec file (optional, for customization):**
   ```bash
   cd d:\LP\backend
   pyinstaller --name python-sync-processor sidecar_main.py --onefile --noconsole
   ```

3. **Build with all dependencies:**
   ```bash
   pyinstaller --onefile \
       --name python-sync-processor \
       --hidden-import=backend.ipc_database \
       --hidden-import=backend.supabase_database \
       --hidden-import=backend.schema \
       --hidden-import=backend.database \
       --hidden-import=supabase \
       --hidden-import=sqlalchemy \
       --collect-all=backend \
       sidecar_main.py
   ```

4. **Copy binary to Tauri binaries folder:**
   ```powershell
   # Windows
   Copy-Item "dist\python-sync-processor.exe" "frontend\src-tauri\binaries\python-sync-processor-x86_64-pc-windows-msvc.exe" -Force
   
   # Linux
   Copy-Item "dist/python-sync-processor" "frontend/src-tauri/binaries/python-sync-processor-linux" -Force
   ```

**Option B: Nuitka (Cross-platform, Better for Android)**

1. **Install Nuitka:**
   ```bash
   pip install nuitka
   ```

2. **Build for desktop:**
   ```bash
   cd d:\LP\backend
   python -m nuitka \
       --standalone \
       --onefile \
       --include-module=backend \
       --include-module=backend.sidecar_main \
       --include-module=backend.ipc_database \
       --include-module=backend.supabase_database \
       --output-filename=python-sync-processor \
       sidecar_main.py
   ```

3. **Copy to binaries folder** (same as PyInstaller)

**Files to Update:**
- Binary location: `frontend/src-tauri/binaries/`
- Naming convention: `python-sync-processor-{target-triple}`

---

### Step 5.3: Update Rust Bridge to Use Bundled Binary (Desktop)

**Goal:** Modify `bridge.rs` to use bundled binary instead of Python source

**File:** `frontend/src-tauri/src/bridge.rs`

**Changes:**

1. **Add binary detection function:**
   ```rust
   #[cfg(not(target_os = "android"))]
   fn find_sidecar_binary() -> Option<std::path::PathBuf> {
       // Try to find binary relative to executable
       let exe_path = std::env::current_exe().ok()?;
       let exe_dir = exe_path.parent()?;
       
       // Check common locations
       let candidates = [
           exe_dir.join("python-sync-processor"),
           exe_dir.join("python-sync-processor.exe"),
           exe_dir.parent()?.join("binaries").join("python-sync-processor"),
           exe_dir.parent()?.join("binaries").join("python-sync-processor.exe"),
       ];
       
       candidates.iter().find(|p| p.exists()).cloned()
   }
   ```

2. **Update `spawn()` method:**
   ```rust
   #[cfg(not(target_os = "android"))]
   pub fn spawn(&self, _python_exe: &str, _args: &[&str], _working_dir: Option<&std::path::Path>) -> Result<(), String> {
       let mut is_running = self.is_running.lock().map_err(|e| e.to_string())?;
       if *is_running { return Ok(()); }

       // Try bundled binary first
       let binary_path = find_sidecar_binary()
           .ok_or_else(|| "Sidecar binary not found. Please build it first.".to_string())?;

       let mut cmd = Command::new(&binary_path);
       cmd.stdin(Stdio::piped())
          .stdout(Stdio::piped())
          .stderr(Stdio::inherit());
       
       // No working_dir needed for bundled binary
       
       let mut child = cmd.spawn()
           .map_err(|e| format!("Spawn failed: {}", e))?;

       *self.stdin.lock().unwrap() = child.stdin.take();
       *self.stdout.lock().unwrap() = child.stdout.take().map(BufReader::new);
       *self.process.lock().unwrap() = Some(child);
       *is_running = true;
       Ok(())
   }
   ```

3. **Update `lib.rs` to remove Python path logic:**
   ```rust
   // In trigger_sync(), remove lines 101-132 (Python exe detection)
   // Just call bridge.spawn() without arguments
   if let Err(e) = bridge.spawn("", &[], None) {
       // ...
   }
   ```

**Test:**
```bash
cd d:\LP\frontend
cargo tauri dev
```

**Success Criteria:**
- ✅ App uses bundled binary (not Python source)
- ✅ IPC works with bundled binary
- ✅ No Python installation required

---

### Step 5.4: Configure Tauri for Sidecar (Desktop)

**Goal:** Add sidecar configuration to `tauri.conf.json`

**File:** `frontend/src-tauri/tauri.conf.json`

**Add to configuration:**
```json
{
  "plugins": {
    "shell": {
      "sidecars": [
        {
          "name": "python-sync-processor",
          "targets": ["windows", "linux", "macos"]
        }
      ]
    }
  }
}
```

**Note:** For Tauri v2.0, sidecar configuration may be different. Check Tauri v2.0 documentation for exact format.

---

## Phase 6: Android Implementation

### Step 6.1: Build Python Sidecar for Android

**Goal:** Create Android-compatible binary (aarch64-linux-android)

**Option A: Docker Cross-Compile (Recommended)**

1. **Create Dockerfile:**
   ```dockerfile
   # Dockerfile.android-python
   FROM python:3.11-slim
   
   RUN apt-get update && apt-get install -y \
       build-essential \
       patchelf \
       gcc-aarch64-linux-gnu \
       && rm -rf /var/lib/apt/lists/*
   
   RUN pip install nuitka
   
   WORKDIR /app
   COPY backend/ ./backend/
   COPY requirements.txt .
   
   RUN pip install -r requirements.txt
   
   # Build for Android aarch64
   RUN python -m nuitka \
       --standalone \
       --onefile \
       --target-arch=aarch64 \
       --output-filename=python-sync-processor \
       backend/sidecar_main.py
   
   # Output in /app/python-sync-processor
   ```

2. **Build Docker image:**
   ```bash
   docker build -f Dockerfile.android-python -t python-android-build .
   ```

3. **Extract binary:**
   ```bash
   docker create --name temp-container python-android-build
   docker cp temp-container:/app/python-sync-processor ./frontend/src-tauri/binaries/python-sync-processor-aarch64-linux-android
   docker rm temp-container
   ```

**Option B: Linux Host with Cross-Compile**

If you have a Linux machine:
```bash
# Install cross-compilation tools
sudo apt-get install gcc-aarch64-linux-gnu

# Build with Nuitka
python -m nuitka \
    --standalone \
    --onefile \
    --target-arch=aarch64 \
    --output-filename=python-sync-processor \
    backend/sidecar_main.py
```

**Option C: Use Existing Build Script**

Check if `backend/bundle_sidecar.py` exists and supports Android:
```bash
cd d:\LP\backend
python bundle_sidecar.py --target android
```

**Success Criteria:**
- ✅ Binary exists: `frontend/src-tauri/binaries/python-sync-processor-aarch64-linux-android`
- ✅ Binary is executable (chmod +x on Linux)
- ✅ Binary is statically linked or includes all dependencies

---

### Step 6.2: Configure Tauri for Android Sidecar

**Goal:** Add sidecar binary to Android APK

**File:** `frontend/src-tauri/tauri.conf.json`

**Update configuration:**
```json
{
  "plugins": {
    "shell": {
      "sidecars": [
        {
          "name": "python-sync-processor",
          "targets": ["android"]
        }
      ]
    }
  },
  "bundle": {
    "resources": [
      "../binaries"
    ]
  }
}
```

**Alternative:** Manually copy binary to Android assets

If Tauri sidecar config doesn't work, manually copy:
```powershell
# Copy binary to Android assets
Copy-Item "frontend\src-tauri\binaries\python-sync-processor-aarch64-linux-android" `
    "frontend\src-tauri\gen\android\app\src\main\assets\python-sync-processor" -Force
```

**Note:** You may need to update the build process to include this copy step.

---

### Step 6.3: Implement Android Bridge Using Tauri Shell Plugin

**Goal:** Replace stub implementation with working Android bridge

**File:** `frontend/src-tauri/src/bridge.rs`

**Current State:** Lines 137-145, 157-160, 173-176 are stubs

**New Implementation:**

1. **Update SidecarBridge struct for Android:**
   ```rust
   #[cfg(target_os = "android")]
   pub struct SidecarBridge {
       app_handle: Mutex<Option<tauri::AppHandle>>,
       sidecar_handle: Mutex<Option<tauri_plugin_shell::process::CommandChild>>,
       is_running: Mutex<bool>,
   }
   ```

2. **Update `new()` method:**
   ```rust
   #[cfg(target_os = "android")]
   pub fn new() -> Self {
       Self {
           app_handle: Mutex::new(None),
           sidecar_handle: Mutex::new(None),
           is_running: Mutex::new(false),
       }
   }
   
   #[cfg(target_os = "android")]
   pub fn set_app_handle(&self, app: tauri::AppHandle) {
       *self.app_handle.lock().unwrap() = Some(app);
   }
   ```

3. **Implement `spawn()` for Android:**
   ```rust
   #[cfg(target_os = "android")]
   pub fn spawn(&self, _python_exe: &str, _args: &[&str], _working_dir: Option<&std::path::Path>) -> Result<(), String> {
       use tauri_plugin_shell::ShellExt;
       
       let mut is_running = self.is_running.lock().map_err(|e| e.to_string())?;
       if *is_running { return Ok(()); }
       
       let app_handle = self.app_handle.lock().unwrap()
           .as_ref()
           .ok_or("AppHandle not set. Call set_app_handle() first.")?
           .clone();
       
       // Spawn sidecar using Tauri shell plugin
       let sidecar = app_handle.shell()
           .sidecar("python-sync-processor")
           .map_err(|e| format!("Failed to create sidecar: {}", e))?;
       
       // Configure stdin/stdout
       let child = sidecar
           .stdin(std::process::Stdio::piped())
           .stdout(std::process::Stdio::piped())
           .stderr(std::process::Stdio::inherit())
           .spawn()
           .map_err(|e| format!("Failed to spawn sidecar: {}", e))?;
       
       *self.sidecar_handle.lock().unwrap() = Some(child);
       *is_running = true;
       Ok(())
   }
   ```

4. **Implement `send()` for Android:**
   ```rust
   #[cfg(target_os = "android")]
   pub fn send(&self, message: &RustMessage) -> Result<(), String> {
       use tauri_plugin_shell::process::CommandExt;
       
       let json = serde_json::to_string(message).map_err(|e| e.to_string())?;
       
       let mut handle_guard = self.sidecar_handle.lock().unwrap();
       let child = handle_guard.as_mut()
           .ok_or("Sidecar not running")?;
       
       // Write to stdin
       if let Some(stdin) = child.stdin.as_mut() {
           use std::io::Write;
           writeln!(stdin, "{}", json).map_err(|e| e.to_string())?;
           stdin.flush().map_err(|e| e.to_string())?;
       }
       
       Ok(())
   }
   ```

5. **Implement `receive()` for Android:**
   ```rust
   #[cfg(target_os = "android")]
   pub fn receive(&self) -> Result<PythonMessage, String> {
       use tauri_plugin_shell::process::CommandExt;
       use std::io::{BufRead, BufReader};
       
       let mut handle_guard = self.sidecar_handle.lock().unwrap();
       let child = handle_guard.as_mut()
           .ok_or("Sidecar not running")?;
       
       // Read from stdout
       if let Some(stdout) = child.stdout.as_mut() {
           let mut reader = BufReader::new(stdout);
           let mut line = String::new();
           reader.read_line(&mut line).map_err(|e| e.to_string())?;
           serde_json::from_str(line.trim()).map_err(|e| e.to_string())
       } else {
           Err("No stdout available".into())
       }
   }
   ```

**Note:** Tauri v2.0 shell plugin API may differ. Check [Tauri v2.0 documentation](https://v2.tauri.app/) for exact API.

**Update `lib.rs` to set app handle:**
```rust
// In run() function, after creating bridge:
let bridge = SidecarBridge::new();
#[cfg(target_os = "android")]
{
    // Store app handle for later use
    // This needs to be done after app is created
}
```

**Alternative Approach:** Pass AppHandle to spawn method

If the above doesn't work, modify `spawn()` signature:
```rust
#[cfg(target_os = "android")]
pub fn spawn(&self, app: &tauri::AppHandle) -> Result<(), String> {
    // Implementation using app.shell().sidecar()
}
```

And update `trigger_sync()`:
```rust
#[cfg(target_os = "android")]
if let Err(e) = bridge.spawn(&app) {
    // ...
}
```

---

### Step 6.4: Update lib.rs for Android

**Goal:** Ensure Android-specific initialization works

**File:** `frontend/src-tauri/src/lib.rs`

**Changes:**

1. **Update `trigger_sync()` to handle Android:**
   ```rust
   #[tauri::command]
   async fn trigger_sync(
       app: tauri::AppHandle,
       user_id: String,
   ) -> Result<serde_json::Value, String> {
       let bridge = app.state::<SidecarBridge>();
       
       #[cfg(target_os = "android")]
       {
           // Set app handle if not already set
           bridge.set_app_handle(app.clone());
       }
       
       let request_id = uuid::Uuid::new_v4().to_string();
       
       // Spawn sidecar
       #[cfg(target_os = "android")]
       if let Err(e) = bridge.spawn("", &[], None) {
           return Err(format!("Failed to start sidecar: {}", e));
       }
       
       #[cfg(not(target_os = "android"))]
       if let Err(e) = bridge.spawn("", &[], None) {
           return Err(format!("Failed to start sidecar: {}", e));
       }
       
       // Rest of implementation...
   }
   ```

2. **Ensure database path is correct for Android:**
   ```rust
   #[cfg(target_os = "android")]
   let db_path = std::path::PathBuf::from("/data/data/com.lessonplanner.bilingual/databases/lesson_planner.db");
   ```

---

### Step 6.5: Build and Test on Android Device

**Goal:** Verify complete implementation works on physical tablet

**Build Process:**

1. **Build frontend:**
   ```powershell
   cd d:\LP\frontend
   npm run build:skip-check
   ```

2. **Copy assets (including sidecar binary):**
   ```powershell
   Remove-Item "frontend\src-tauri\gen\android\app\src\main\assets" -Recurse -Force -ErrorAction SilentlyContinue
   New-Item -ItemType Directory -Path "frontend\src-tauri\gen\android\app\src\main\assets" -Force
   Copy-Item "frontend\dist\*" "frontend\src-tauri\gen\android\app\src\main\assets\" -Recurse -Force
   
   # Copy sidecar binary
   Copy-Item "frontend\src-tauri\binaries\python-sync-processor-aarch64-linux-android" `
       "frontend\src-tauri\gen\android\app\src\main\assets\python-sync-processor" -Force
   ```

3. **Build APK:**
   ```powershell
   cd d:\LP\frontend\src-tauri\gen\android
   .\gradlew.bat assembleArm64Debug -x rustBuildArm64Debug
   ```

4. **Install on device:**
   ```powershell
   adb uninstall com.lessonplanner.bilingual
   adb install "app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
   ```

**Testing:**

1. **Check sidecar starts:**
   ```powershell
   adb logcat | grep -E "(python|sidecar|bilingual)"
   ```

2. **Test sync functionality:**
   - Open app
   - Trigger sync
   - Verify no "not yet implemented" error
   - Check logs for IPC communication

3. **Test offline mode:**
   - Enable airplane mode
   - Create a plan
   - Verify it saves locally
   - Disable airplane mode
   - Trigger sync
   - Verify plan syncs to Supabase

**Success Criteria:**
- ✅ App launches without errors
- ✅ Sidecar binary is found and executed
- ✅ IPC communication works
- ✅ Database operations work
- ✅ Supabase sync works
- ✅ Offline mode works

---

## Troubleshooting

### Issue: Binary not found

**Symptoms:** "Sidecar binary not found" error

**Solutions:**
1. Verify binary exists in `binaries/` folder
2. Check binary naming matches target triple
3. Ensure binary is included in APK (check assets folder)
4. Verify file permissions (chmod +x on Linux)

### Issue: IPC communication fails

**Symptoms:** No response from sidecar, timeouts

**Solutions:**
1. Check sidecar binary is executable
2. Verify stdin/stdout pipes are configured correctly
3. Check logs: `adb logcat | grep python`
4. Test sidecar binary manually (if possible)

### Issue: Tauri shell plugin API errors

**Symptoms:** Compilation errors, API not found

**Solutions:**
1. Verify `tauri-plugin-shell = "2.0"` in Cargo.toml
2. Check Tauri v2.0 documentation for correct API
3. Ensure plugin is initialized in `lib.rs`
4. Check `tauri.conf.json` plugin configuration

### Issue: Database path errors on Android

**Symptoms:** Database not found, permission errors

**Solutions:**
1. Verify path: `/data/data/com.lessonplanner.bilingual/databases/`
2. Check Android manifest permissions
3. Ensure directory is created before opening database
4. Check app data directory permissions

---

## Checklist

### Phase 5: Python Bundling
- [ ] Step 5.1: Verify desktop sidecar works (source mode)
- [ ] Step 5.2: Bundle Python sidecar for desktop
- [ ] Step 5.3: Update Rust bridge to use bundled binary
- [ ] Step 5.4: Configure Tauri for sidecar (desktop)
- [ ] Test: Desktop app works with bundled binary

### Phase 6: Android Implementation
- [ ] Step 6.1: Build Python sidecar for Android
- [ ] Step 6.2: Configure Tauri for Android sidecar
- [ ] Step 6.3: Implement Android bridge using Tauri shell plugin
- [ ] Step 6.4: Update lib.rs for Android
- [ ] Step 6.5: Build and test on Android device
- [ ] Test: Offline mode works
- [ ] Test: Supabase sync works
- [ ] Test: Data persists after app restart

---

## Next Steps After Completion

1. **Performance Optimization:**
   - Optimize binary size
   - Reduce startup time
   - Cache database connections

2. **Error Handling:**
   - Add retry logic for IPC
   - Improve error messages
   - Add fallback mechanisms

3. **Testing:**
   - Add unit tests for bridge
   - Add integration tests for IPC
   - Test on multiple Android versions

4. **Documentation:**
   - Update user guide
   - Document troubleshooting steps
   - Create deployment guide

---

**Last Updated:** Based on current codebase state  
**Status:** Ready for implementation

