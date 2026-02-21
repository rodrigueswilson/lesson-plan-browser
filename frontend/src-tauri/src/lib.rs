// Library entry point for Android builds
// This is used when building for Android (shared library)

mod bridge;
mod db_commands;

use bridge::{PythonMessage, RustMessage, SidecarBridge};
use std::collections::HashMap;
use tauri::Manager;

#[tauri::command]
fn show_in_folder(path: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        use std::path::PathBuf;

        let mut p = PathBuf::from(path.replace('/', "\\"));

        if !p.exists() {
            if let Some(parent) = p.parent() {
                p = parent.to_path_buf();
            }
        }

        let resolved = p.canonicalize().unwrap_or(p);

        if resolved.is_dir() {
            std::process::Command::new("explorer")
                .arg(resolved.as_os_str())
                .spawn()
                .map_err(|e| format!("Failed to open Explorer: {}", e))?;
        } else {
            let arg = format!("/select,{}", resolved.to_string_lossy());
            std::process::Command::new("explorer")
                .arg(arg)
                .spawn()
                .map_err(|e| format!("Failed to open Explorer: {}", e))?;
        }
    }

    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .args(["-R", &path])
            .spawn()
            .map_err(|e| format!("Failed to open Finder: {}", e))?;
    }

    #[cfg(target_os = "linux")]
    {
        if let Some(parent) = std::path::Path::new(&path).parent() {
            std::process::Command::new("xdg-open")
                .arg(parent)
                .spawn()
                .map_err(|e| format!("Failed to open file manager: {}", e))?;
        }
    }

    Ok(())
}

fn run_command_capture(mut cmd: std::process::Command) -> Result<String, String> {
    let output = cmd.output().map_err(|e| e.to_string())?;
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    if output.status.success() {
        let combined = format!("{}{}", stdout, stderr);
        return Ok(combined.trim().to_string());
    }

    let combined = format!("{}{}", stdout, stderr);
    Err(combined.trim().to_string())
}

fn find_latest_apk() -> Result<std::path::PathBuf, String> {
    use std::path::{Path, PathBuf};
    use std::time::SystemTime;

    fn candidate_dirs() -> Vec<PathBuf> {
        // Anchor paths at the repo root. In dev, the CWD is often `frontend/` so relative paths
        // like `lesson-plan-browser/...` would not resolve.
        let root = find_project_root_with_script("build-apk.ps1")
            .or_else(|_| std::env::current_dir().map_err(|e| e.to_string()))
            .unwrap_or_else(|_| PathBuf::from("."));

        vec![
            root.join("lesson-plan-browser")
                .join("frontend")
                .join("src-tauri")
                .join("gen")
                .join("android"),
            root.join("frontend")
                .join("src-tauri")
                .join("gen")
                .join("android"),
        ]
    }

    fn walk_apks(dir: &Path) -> Vec<PathBuf> {
        let mut out: Vec<PathBuf> = Vec::new();
        let Ok(entries) = std::fs::read_dir(dir) else {
            return out;
        };
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                out.extend(walk_apks(&path));
            } else if path
                .extension()
                .and_then(|s| s.to_str())
                .map(|s| s.eq_ignore_ascii_case("apk"))
                .unwrap_or(false)
            {
                out.push(path);
            }
        }
        out
    }

    let dirs = candidate_dirs();
    let mut best: Option<(SystemTime, PathBuf)> = None;
    for dir in &dirs {
        for apk in walk_apks(dir) {
            if let Ok(meta) = std::fs::metadata(&apk) {
                if let Ok(mtime) = meta.modified() {
                    match &best {
                        None => best = Some((mtime, apk)),
                        Some((best_time, _)) if mtime > *best_time => best = Some((mtime, apk)),
                        _ => {}
                    }
                }
            }
        }
    }

    best.map(|(_, p)| p).ok_or_else(|| {
        format!(
            "No APK files found. Build an Android APK first (e.g. build-apk.ps1), then try again.\nSearched:\n- {}",
            dirs.iter()
                .map(|d| d.to_string_lossy().to_string())
                .collect::<Vec<_>>()
                .join("\n- ")
        )
    })
}

#[tauri::command]
fn install_tablet_apk_latest() -> Result<serde_json::Value, String> {
    let device = detect_single_adb_device()?;
    let apk_path = find_latest_apk()?;
    let apk_str = apk_path
        .to_str()
        .ok_or_else(|| "APK path is not valid UTF-8".to_string())?
        .to_string();

    let install_out = run_command_capture({
        let mut cmd = std::process::Command::new("adb");
        cmd.arg("-s")
            .arg(&device)
            .arg("install")
            .arg("-r")
            .arg(&apk_str);
        cmd
    })
    .map_err(|e| format!("adb install failed: {}", e))?;

    // Best-effort start.
    let activity = "com.lessonplanner.browser/.MainActivity";
    let start_out = run_command_capture({
        let mut cmd = std::process::Command::new("adb");
        cmd.arg("-s")
            .arg(&device)
            .args(["shell", "am", "start", "-n", activity]);
        cmd
    })
    .unwrap_or_else(|e| format!("(start failed) {}", e));

    Ok(serde_json::json!({
        "device_id": device,
        "apk_path": apk_str,
        "install_output": install_out,
        "start_output": start_out,
    }))
}

fn ensure_package_installed(device: &str, package_name: &str) -> Result<(), String> {
    let out = run_command_capture({
        let mut cmd = std::process::Command::new("adb");
        cmd.arg("-s")
            .arg(device)
            .args(["shell", "pm", "path", package_name]);
        cmd
    })
    .unwrap_or_default();
    if out.trim().is_empty() {
        return Err(format!(
            "Android package is not installed: {}. Install the APK first.",
            package_name
        ));
    }
    Ok(())
}

fn find_project_root_with_script(script_name: &str) -> Result<std::path::PathBuf, String> {
    if let Ok(cwd) = std::env::current_dir() {
        let mut p = Some(cwd.as_path());
        while let Some(cur) = p {
            let candidate = cur.join(script_name);
            if candidate.exists() {
                return Ok(cur.to_path_buf());
            }
            p = cur.parent();
        }
    }

    if let Ok(exe) = std::env::current_exe() {
        let mut p = exe.parent();
        while let Some(cur) = p {
            let candidate = cur.join(script_name);
            if candidate.exists() {
                return Ok(cur.to_path_buf());
            }
            p = cur.parent();
        }
    }

    Err(format!(
        "Could not locate project root containing {}",
        script_name
    ))
}

#[tauri::command]
async fn build_tablet_apk(
    db_path: String,
    target: Option<String>,
    release: Option<bool>,
) -> Result<serde_json::Value, String> {
    let root = find_project_root_with_script("build-apk.ps1")?;
    let script = root.join("build-apk.ps1");

    let target_value = target.unwrap_or_else(|| "arm64".to_string());
    let release_value = release.unwrap_or(false);

    let db_abs = std::path::PathBuf::from(db_path.clone());
    if !db_abs.exists() {
        return Err(format!("Database file does not exist: {}", db_path));
    }

    // Keep copies outside the closure (we return them in JSON below).
    let target_value_for_cmd = target_value.clone();
    let db_path_for_cmd = db_path.clone();

    let result = tauri::async_runtime::spawn_blocking(move || -> Result<(i32, String), String> {
        #[cfg(target_os = "windows")]
        {
            let mut cmd = std::process::Command::new("powershell");
            cmd.arg("-NoProfile")
                .arg("-ExecutionPolicy")
                .arg("Bypass")
                .arg("-File")
                .arg(script.to_string_lossy().to_string())
                .arg("-Target")
                .arg(target_value_for_cmd)
                .arg("-DbPath")
                .arg(db_path_for_cmd);

            if release_value {
                cmd.arg("-Release");
            }

            let output = cmd.output().map_err(|e| e.to_string())?;
            let stdout = String::from_utf8_lossy(&output.stdout).to_string();
            let stderr = String::from_utf8_lossy(&output.stderr).to_string();
            let code = output.status.code().unwrap_or(-1);
            Ok((code, format!("{}{}", stdout, stderr)))
        }
        #[cfg(not(target_os = "windows"))]
        {
            Err("build_tablet_apk is only implemented for Windows currently".to_string())
        }
    })
    .await
    .map_err(|e| e.to_string())??;

    let (exit_code, output) = result;
    if exit_code != 0 {
        let latest_apk_hint = find_latest_apk()
            .ok()
            .map(|p| format!("\n\nLatest APK found on disk:\n{}", p.to_string_lossy()))
            .unwrap_or_default();
        return Err(format!(
            "Build failed (exit code {}). Output:\n{}{}",
            exit_code, output, latest_apk_hint
        ));
    }

    Ok(serde_json::json!({
        "exit_code": exit_code,
        "output": output,
        "target": target_value,
        "release": release_value,
        "db_path": db_path,
    }))
}

fn detect_single_adb_device() -> Result<String, String> {
    let mut adb_devices_cmd = std::process::Command::new("adb");
    adb_devices_cmd.arg("devices");
    let out = run_command_capture(adb_devices_cmd).map_err(|e| {
        format!(
            "ADB not available or failed to run. Ensure Android platform-tools are installed and adb is in PATH. Details: {}",
            e
        )
    })?;
    let mut devices: Vec<String> = Vec::new();
    let mut unauthorized: Vec<String> = Vec::new();
    let mut offline: Vec<String> = Vec::new();

    for line in out.lines().skip(1) {
        let l = line.trim();
        if l.is_empty() {
            continue;
        }
        if let Some((serial, status)) = l.split_once('\t') {
            let serial = serial.trim().to_string();
            let status = status.trim();
            if status == "device" {
                devices.push(serial);
            } else if status == "unauthorized" {
                unauthorized.push(serial);
            } else if status == "offline" {
                offline.push(serial);
            }
        }
    }

    match devices.len() {
        0 => {
            if !unauthorized.is_empty() {
                return Err(format!(
                    "ADB device unauthorized. Approve the USB debugging prompt on the tablet. Devices: {}",
                    unauthorized.join(", ")
                ));
            }
            if !offline.is_empty() {
                return Err(format!(
                    "ADB device offline. Reconnect USB / restart adb. Devices: {}",
                    offline.join(", ")
                ));
            }
            Err(
                "No ADB devices detected. Connect the tablet via USB and enable USB debugging."
                    .to_string(),
            )
        }
        1 => Ok(devices[0].clone()),
        _ => Err(format!(
            "Multiple ADB devices detected. Disconnect extra devices or specify one. Devices: {}",
            devices.join(", ")
        )),
    }
}

#[tauri::command]
fn push_tablet_db(db_path: String) -> Result<serde_json::Value, String> {
    use std::path::PathBuf;

    let package_name = "com.lessonplanner.browser";
    let temp_remote = "/data/local/tmp/lesson_planner.db";
    let activity = "com.lessonplanner.browser/.MainActivity";

    let p = PathBuf::from(db_path.clone());
    if !p.exists() {
        return Err(format!("Database file does not exist: {}", db_path));
    }

    let device = detect_single_adb_device()?;
    ensure_package_installed(&device, package_name)?;
    let mut steps: Vec<serde_json::Value> = Vec::new();

    let record_ok = |name: &str, output: String| -> serde_json::Value {
        serde_json::json!({ "step": name, "ok": true, "output": output })
    };
    let record_err = |name: &str, output: String| -> serde_json::Value {
        serde_json::json!({ "step": name, "ok": false, "output": output })
    };

    let mut adb_push_cmd = std::process::Command::new("adb");
    adb_push_cmd
        .arg("-s")
        .arg(&device)
        .arg("push")
        .arg(&db_path)
        .arg(temp_remote);
    match run_command_capture(adb_push_cmd) {
        Ok(out) => steps.push(record_ok("adb_push", out)),
        Err(out) => {
            steps.push(record_err("adb_push", out.clone()));
            return Err(format!("ADB push failed: {}", out));
        }
    }

    let mut adb_stop_cmd = std::process::Command::new("adb");
    adb_stop_cmd
        .arg("-s")
        .arg(&device)
        .args(["shell", "am", "force-stop", package_name]);
    let _ = run_command_capture(adb_stop_cmd)
        .map(|out| steps.push(record_ok("force_stop", out)))
        .map_err(|out| {
            steps.push(record_err("force_stop", out.clone()));
            out
        });

    let mut adb_mkdir_cmd = std::process::Command::new("adb");
    adb_mkdir_cmd.arg("-s").arg(&device).args([
        "shell",
        "run-as",
        package_name,
        "mkdir",
        "-p",
        "databases",
    ]);
    match run_command_capture(adb_mkdir_cmd) {
        Ok(out) => steps.push(record_ok("run_as_mkdir", out)),
        Err(out) => {
            steps.push(record_err("run_as_mkdir", out.clone()));
            return Err(format!(
                "run-as mkdir failed (is the app debuggable?): {}",
                out
            ));
        }
    }

    let mut adb_cp_cmd = std::process::Command::new("adb");
    adb_cp_cmd.arg("-s").arg(&device).args([
        "shell",
        "run-as",
        package_name,
        "cp",
        temp_remote,
        "databases/lesson_planner.db",
    ]);
    match run_command_capture(adb_cp_cmd) {
        Ok(out) => steps.push(record_ok("run_as_cp", out)),
        Err(out) => {
            steps.push(record_err("run_as_cp", out.clone()));
            return Err(format!(
                "run-as cp failed (is the app debuggable?): {}",
                out
            ));
        }
    }

    let mut adb_rm_cmd = std::process::Command::new("adb");
    adb_rm_cmd
        .arg("-s")
        .arg(&device)
        .args(["shell", "rm", temp_remote]);
    let _ = run_command_capture(adb_rm_cmd)
        .map(|out| steps.push(record_ok("rm_temp", out)))
        .map_err(|out| {
            steps.push(record_err("rm_temp", out.clone()));
            out
        });

    let mut adb_start_cmd = std::process::Command::new("adb");
    adb_start_cmd
        .arg("-s")
        .arg(&device)
        .args(["shell", "am", "start", "-n", activity]);
    match run_command_capture(adb_start_cmd) {
        Ok(out) => steps.push(record_ok("start_app", out)),
        Err(out) => {
            steps.push(record_err("start_app", out.clone()));
            return Err(format!("Failed to restart app: {}", out));
        }
    }

    Ok(serde_json::json!({
        "device_id": device,
        "package": package_name,
        "db_path": db_path,
        "steps": steps
    }))
}

#[tauri::command]
fn open_file(_app: tauri::AppHandle, path: String) -> Result<(), String> {
    tauri_plugin_opener::open_path(&path, None::<&str>).map_err(|e| e.to_string())
}

#[tauri::command]
async fn save_file_dialog(_window: tauri::Window, source_path: String) -> Result<String, String> {
    use std::path::Path;
    // Note: In Tauri v2.0, dialog functionality is handled via plugin
    // For now, we'll use a simpler approach or handle via frontend
    // TODO: Update to use tauri-plugin-dialog when needed

    let source = Path::new(&source_path);

    // Check if source exists
    if !source.exists() {
        return Err(format!("Source file does not exist: {}", source_path));
    }

    // For now, return the source path
    // In production, use tauri-plugin-dialog for save dialog
    Ok(source_path)
}

/// Load environment variables from .env file for the sidecar process
/// Returns a HashMap with Supabase-related environment variables
fn load_env_vars_for_sidecar() -> HashMap<String, String> {
    let mut env_vars = HashMap::new();

    // Find project root (where .env file should be)
    let project_root = std::env::current_exe()
        .ok()
        .and_then(|exe| {
            exe.parent() // target/debug or target/release
                .and_then(|p| p.parent()) // target
                .and_then(|p| p.parent()) // src-tauri
                .and_then(|p| p.parent()) // frontend
                .and_then(|p| p.parent()) // project root (D:\LP)
                .map(|p| p.to_path_buf())
        })
        .or_else(|| {
            std::env::current_dir().ok().and_then(|cwd| {
                if cwd.ends_with("frontend") || cwd.ends_with("src-tauri") {
                    cwd.parent().map(|p| p.to_path_buf())
                } else {
                    Some(cwd)
                }
            })
        });

    if let Some(root) = project_root {
        let env_file = root.join(".env");
        eprintln!("[Sidecar] Looking for .env file at: {}", env_file.display());

        if env_file.exists() {
            // Try to load .env file using dotenv crate
            // If it fails, we'll manually parse the file for the variables we need
            let dotenv_loaded = dotenv::from_path(&env_file).is_ok();

            if !dotenv_loaded {
                eprintln!(
                    "[Sidecar] dotenv parsing failed, trying manual parse for Supabase variables"
                );
                // Manually parse .env file for Supabase variables
                if let Ok(content) = std::fs::read_to_string(&env_file) {
                    for line in content.lines() {
                        let line = line.trim();
                        // Skip comments and empty lines
                        if line.is_empty() || line.starts_with('#') {
                            continue;
                        }
                        // Parse KEY=VALUE format
                        if let Some(equal_pos) = line.find('=') {
                            let key = line[..equal_pos].trim();
                            let value = line[equal_pos + 1..].trim();
                            // Remove quotes if present
                            let value = value.trim_matches('"').trim_matches('\'');

                            // Check if this is a Supabase variable we need
                            if key == "SUPABASE_URL_PROJECT1"
                                || key == "SUPABASE_KEY_PROJECT1"
                                || key == "SUPABASE_URL_PROJECT2"
                                || key == "SUPABASE_KEY_PROJECT2"
                                || key == "SUPABASE_URL"
                                || key == "SUPABASE_KEY"
                                || key == "SUPABASE_PROJECT"
                            {
                                env_vars.insert(key.to_string(), value.to_string());
                                eprintln!(
                                    "[Sidecar] Found env var from manual parse: {} (length: {})",
                                    key,
                                    value.len()
                                );
                            }
                        }
                    }
                }
            } else {
                eprintln!("[Sidecar] Loaded .env file successfully with dotenv");
            }
        } else {
            eprintln!("[Sidecar] .env file not found at: {}", env_file.display());
        }
    }

    // Extract Supabase-related environment variables from current environment
    // These might have been loaded by dotenv or set elsewhere
    let supabase_vars = [
        "SUPABASE_URL_PROJECT1",
        "SUPABASE_KEY_PROJECT1",
        "SUPABASE_URL_PROJECT2",
        "SUPABASE_KEY_PROJECT2",
        "SUPABASE_URL", // Legacy
        "SUPABASE_KEY", // Legacy
        "SUPABASE_PROJECT",
    ];

    for var_name in &supabase_vars {
        // Only add if not already in env_vars (from manual parse)
        if !env_vars.contains_key(*var_name) {
            if let Ok(value) = std::env::var(var_name) {
                let value_len = value.len();
                env_vars.insert(var_name.to_string(), value);
                eprintln!(
                    "[Sidecar] Found env var from environment: {} (length: {})",
                    var_name, value_len
                );
            }
        }
    }

    eprintln!(
        "[Sidecar] Loaded {} environment variables for sidecar",
        env_vars.len()
    );
    env_vars
}

#[tauri::command]
async fn trigger_sync(app: tauri::AppHandle, user_id: String) -> Result<serde_json::Value, String> {
    let bridge = app.state::<SidecarBridge>();

    // Set app handle for Android (needed for shell plugin)
    #[cfg(target_os = "android")]
    {
        bridge.set_app_handle(app.clone());
    }

    let request_id = uuid::Uuid::new_v4().to_string();

    eprintln!("[Sidecar] trigger_sync called, starting binary detection...");
    use std::io::Write;
    let _ = std::io::stderr().flush();

    // Try to find bundled binary first, fallback to source mode
    // Find executable directory to locate binaries folder
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|exe| exe.parent().map(|p| p.to_path_buf()));

    if let Some(ref dir) = exe_dir {
        eprintln!("[Sidecar] Executable directory: {}", dir.display());
    } else {
        eprintln!("[Sidecar] WARNING: Could not determine executable directory");
    }

    // Try to find bundled binary
    #[cfg(target_os = "windows")]
    let binary_name = "python-sync-processor-x86_64-pc-windows-msvc.exe";
    #[cfg(target_os = "linux")]
    let binary_name = "python-sync-processor-linux";
    #[cfg(target_os = "macos")]
    let binary_name = "python-sync-processor-aarch64-apple-darwin"; // or x86_64 depending on arch
    #[cfg(target_os = "android")]
    let binary_name = "python-sync-processor-aarch64-linux-android";

    // Try multiple locations for bundled binary
    let bundled_binary = {
        // Option 1: Relative to executable (dev mode: target/debug/)
        // exe_dir = target/debug/, so: .. -> target, .. -> src-tauri, then binaries/
        eprintln!("[Sidecar] Starting path1 check, exe_dir is: {:?}", exe_dir);
        let path1 = exe_dir
            .as_ref()
            .and_then(|dir| {
                eprintln!("[Sidecar] path1: exe_dir = {}", dir.display());
                let p1 = dir.parent()?; // target
                eprintln!("[Sidecar] path1: p1 (target) = {:?}", p1);
                let p2 = p1.parent()?; // src-tauri
                eprintln!("[Sidecar] path1: p2 (src-tauri) = {:?}", p2);
                let full_path = p2.join("binaries").join(binary_name);
                let exists = full_path.exists();
                eprintln!(
                    "[Sidecar] path1: full_path = {} (exists: {})",
                    full_path.display(),
                    exists
                );
                Some(full_path)
            })
            .filter(|p| {
                let exists = p.exists();
                eprintln!(
                    "[Sidecar] path1: After filter, path = {} (exists: {})",
                    p.display(),
                    exists
                );
                exists
            });

        // Option 2: Try from current working directory
        let cwd = std::env::current_dir().ok();
        eprintln!("[Sidecar] path2: current_dir = {:?}", cwd);
        let path2 = cwd.and_then(|cwd| {
            // Try: cwd/src-tauri/binaries/
            let p = cwd.join("src-tauri").join("binaries").join(binary_name);
            eprintln!(
                "[Sidecar] path2: Trying cwd/src-tauri/binaries: {} (exists: {})",
                p.display(),
                p.exists()
            );
            if p.exists() {
                return Some(p);
            }
            // Try: cwd/frontend/src-tauri/binaries/
            let p = cwd
                .join("frontend")
                .join("src-tauri")
                .join("binaries")
                .join(binary_name);
            eprintln!(
                "[Sidecar] path2: Trying cwd/frontend/src-tauri/binaries: {} (exists: {})",
                p.display(),
                p.exists()
            );
            if p.exists() {
                return Some(p);
            }
            // Try: cwd/../frontend/src-tauri/binaries/ (if in src-tauri)
            if let Some(parent) = cwd.parent() {
                let p = parent
                    .join("frontend")
                    .join("src-tauri")
                    .join("binaries")
                    .join(binary_name);
                eprintln!(
                    "[Sidecar] path2: Trying parent/frontend/src-tauri/binaries: {} (exists: {})",
                    p.display(),
                    p.exists()
                );
                if p.exists() {
                    return Some(p);
                }
            }
            None
        });

        // Option 3: Try absolute path (dev fallback for Windows)
        #[cfg(windows)]
        let path3 = {
            let abs_path =
                std::path::PathBuf::from(r"d:\LP\frontend\src-tauri\binaries").join(binary_name);
            let exists = abs_path.exists();
            eprintln!(
                "[Sidecar] path3: Trying absolute path: {} (exists: {})",
                abs_path.display(),
                exists
            );
            if exists {
                Some(abs_path)
            } else {
                None
            }
        };
        #[cfg(not(windows))]
        let path3: Option<std::path::PathBuf> = None;

        // Try paths in order
        let found = path1.or(path2).or(path3);
        if let Some(ref p) = found {
            eprintln!("[Sidecar] Found bundled binary at: {}", p.display());
        } else {
            eprintln!("[Sidecar] Bundled binary not found in any location");
        }
        found
    };

    // Load environment variables from .env file for bundled binary
    let env_vars = load_env_vars_for_sidecar();

    let spawn_result = {
        #[cfg(target_os = "android")]
        {
            // On Android, always use Tauri sidecar (Tauri resolves the binary automatically)
            eprintln!("[Sidecar] Using Android Tauri sidecar (binary resolved by Tauri)");
            // The executable path is ignored on Android - bridge uses sidecar name from config
            bridge.spawn_with_env("python-sync-processor", &[], None, Some(&env_vars))
        }

        #[cfg(not(target_os = "android"))]
        {
            if let Some(binary_path) = bundled_binary {
                // Use bundled binary (no args needed, binary is self-contained)
                eprintln!("[Sidecar] Using bundled binary: {}", binary_path.display());
                bridge.spawn_with_env(binary_path.to_str().unwrap(), &[], None, Some(&env_vars))
            } else {
                eprintln!("[Sidecar] Bundled binary not found, falling back to source mode");
                // Fallback to source mode: use Python interpreter
                #[cfg(target_os = "windows")]
                let python_exe = "python";
                #[cfg(not(target_os = "windows"))]
                let python_exe = "python3";

                // Find project root for source mode
                let project_root = std::env::current_exe()
                    .ok()
                    .and_then(|exe| {
                        exe.parent() // target/debug or target/release
                            .and_then(|p| p.parent()) // target
                            .and_then(|p| p.parent()) // src-tauri
                            .and_then(|p| p.parent()) // frontend
                            .and_then(|p| p.parent()) // project root (D:\LP)
                            .map(|p| p.to_path_buf())
                    })
                    .or_else(|| {
                        std::env::current_dir().ok().and_then(|cwd| {
                            if cwd.ends_with("frontend") {
                                cwd.parent().map(|p| p.to_path_buf())
                            } else {
                                Some(cwd)
                            }
                        })
                    });

                let root = project_root
                    .as_deref()
                    .map(|p| p.display().to_string())
                    .unwrap_or_else(|| "unknown".to_string());
                eprintln!(
                    "[Sidecar] Using source mode: {} -m backend.sidecar_main (root: {})",
                    python_exe, root
                );
                // Source mode: Python will read .env file itself, but we can still pass env vars for consistency
                bridge.spawn_with_env(
                    python_exe,
                    &["-m", "backend.sidecar_main"],
                    project_root.as_deref(),
                    Some(&env_vars),
                )
            }
        }
    };

    if let Err(e) = spawn_result {
        eprintln!("Failed to spawn Python sidecar: {}", e);
        return Err(format!("Failed to start Python sidecar: {}. Make sure Python is installed and backend module is accessible, or bundled binary is available.", e));
    }

    // Send sync command to Python
    let cmd = RustMessage::command(&request_id, "full_sync", Some(&user_id));
    bridge.send(&cmd)?;

    // Handle IPC loop (SQL requests from Python)
    loop {
        let msg = bridge.receive()?;
        match msg {
            PythonMessage::SqlQuery {
                request_id: rid,
                sql,
                params,
            } => {
                let result = db_commands::sql_query(sql, params).await;
                let response = match result {
                    Ok(data) => RustMessage::sql_response(&rid, serde_json::json!(data)),
                    Err(e) => RustMessage::error(&rid, &e),
                };
                bridge.send(&response)?;
            }
            PythonMessage::SqlExecute {
                request_id: rid,
                sql,
                params,
            } => {
                let result = db_commands::sql_execute(sql, params).await;
                let response = match result {
                    Ok(data) => RustMessage::sql_response(&rid, serde_json::json!(data)),
                    Err(e) => RustMessage::error(&rid, &e),
                };
                bridge.send(&response)?;
            }
            PythonMessage::Response {
                request_id: rid,
                status,
                data,
                error,
            } => {
                if rid == request_id {
                    return if status == "success" {
                        Ok(data.unwrap_or(serde_json::json!({})))
                    } else {
                        Err(error.unwrap_or("Unknown error".into()))
                    };
                }
            }
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Add panic hook to capture actual error message
    std::panic::set_hook(Box::new(|panic_info| {
        let location = panic_info
            .location()
            .unwrap_or_else(|| std::panic::Location::caller());
        let msg = match panic_info.payload().downcast_ref::<&str>() {
            Some(s) => *s,
            None => match panic_info.payload().downcast_ref::<String>() {
                Some(s) => &s[..],
                None => "Unknown panic message",
            },
        };
        eprintln!("PANIC: {} at {}:{}", msg, location.file(), location.line());
    }));

    // Initialize database
    // For Android, use app data directory; for desktop, use user data directory
    #[cfg(target_os = "android")]
    let db_path = std::path::PathBuf::from(
        "/data/data/com.lessonplanner.browser/databases/lesson_planner.db",
    );

    #[cfg(not(target_os = "android"))]
    let db_path = std::env::var("APPDATA")
        .or_else(|_| std::env::var("HOME"))
        .map(|p| std::path::PathBuf::from(p).join("lesson_planner.db"))
        .unwrap_or_else(|_| std::path::PathBuf::from("lesson_planner.db"));

    eprintln!("[DB] Initializing database at: {}", db_path.display());
    if let Err(e) = db_commands::init_database(db_path) {
        eprintln!("Failed to initialize database: {}", e);
    }

    eprintln!("[Bridge] Creating SidecarBridge...");
    let bridge = SidecarBridge::new();

    eprintln!("[Tauri] Building app...");
    let builder = tauri::Builder::default();

    #[cfg(not(target_os = "android"))]
    let builder = builder.plugin(tauri_plugin_dialog::init());

    eprintln!("[Tauri] Running app...");
    builder
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(bridge)
        .invoke_handler(tauri::generate_handler![
            show_in_folder,
            install_tablet_apk_latest,
            build_tablet_apk,
            push_tablet_db,
            open_file,
            save_file_dialog,
            trigger_sync,
            db_commands::sql_query,
            db_commands::sql_execute,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
