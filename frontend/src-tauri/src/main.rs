// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod bridge;
mod db_commands;

use bridge::{SidecarBridge, RustMessage, PythonMessage};
use std::collections::HashMap;
use std::process::Command;
use tauri::Manager;

#[tauri::command]
fn show_in_folder(path: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .args(["/select,", &path])
            .spawn()
            .map_err(|e| format!("Failed to open Explorer: {}", e))?;
    }
    
    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .args(["-R", &path])
            .spawn()
            .map_err(|e| format!("Failed to open Finder: {}", e))?;
    }
    
    #[cfg(target_os = "linux")]
    {
        // Try to open the parent directory
        if let Some(parent) = std::path::Path::new(&path).parent() {
            Command::new("xdg-open")
                .arg(parent)
                .spawn()
                .map_err(|e| format!("Failed to open file manager: {}", e))?;
        }
    }
    
    Ok(())
}

#[tauri::command]
fn open_file(path: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        Command::new("cmd")
            .args(["/C", "start", "", &path])
            .spawn()
            .map_err(|e| format!("Failed to open file: {}", e))?;
    }
    
    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(&path)
            .spawn()
            .map_err(|e| format!("Failed to open file: {}", e))?;
    }
    
    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(&path)
            .spawn()
            .map_err(|e| format!("Failed to open file: {}", e))?;
    }
    
    Ok(())
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
            std::env::current_dir()
                .ok()
                .and_then(|cwd| {
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
                eprintln!("[Sidecar] dotenv parsing failed, trying manual parse for Supabase variables");
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
                            if key == "SUPABASE_URL_PROJECT1" || key == "SUPABASE_KEY_PROJECT1" ||
                               key == "SUPABASE_URL_PROJECT2" || key == "SUPABASE_KEY_PROJECT2" ||
                               key == "SUPABASE_URL" || key == "SUPABASE_KEY" ||
                               key == "SUPABASE_PROJECT" {
                                env_vars.insert(key.to_string(), value.to_string());
                                eprintln!("[Sidecar] Found env var from manual parse: {} (length: {})", key, value.len());
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
        "SUPABASE_URL",  // Legacy
        "SUPABASE_KEY",  // Legacy
        "SUPABASE_PROJECT",
    ];
    
    for var_name in &supabase_vars {
        // Only add if not already in env_vars (from manual parse)
        if !env_vars.contains_key(*var_name) {
            if let Ok(value) = std::env::var(var_name) {
                let value_len = value.len();
                env_vars.insert(var_name.to_string(), value);
                eprintln!("[Sidecar] Found env var from environment: {} (length: {})", var_name, value_len);
            }
        }
    }
    
    eprintln!("[Sidecar] Loaded {} environment variables for sidecar", env_vars.len());
    env_vars
}

#[tauri::command]
async fn trigger_sync(
    app: tauri::AppHandle,
    user_id: String,
) -> Result<serde_json::Value, String> {
    let bridge = app.state::<SidecarBridge>();
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
                eprintln!("[Sidecar] path1: full_path = {} (exists: {})", full_path.display(), exists);
                Some(full_path)
            })
            .filter(|p| {
                let exists = p.exists();
                eprintln!("[Sidecar] path1: After filter, path = {} (exists: {})", p.display(), exists);
                exists
            });
        
        // Option 2: Try from current working directory
        let cwd = std::env::current_dir().ok();
        eprintln!("[Sidecar] path2: current_dir = {:?}", cwd);
        let path2 = cwd
            .and_then(|cwd| {
                // Try: cwd/src-tauri/binaries/
                let p = cwd.join("src-tauri").join("binaries").join(binary_name);
                eprintln!("[Sidecar] path2: Trying cwd/src-tauri/binaries: {} (exists: {})", p.display(), p.exists());
                if p.exists() {
                    return Some(p);
                }
                // Try: cwd/frontend/src-tauri/binaries/
                let p = cwd.join("frontend").join("src-tauri").join("binaries").join(binary_name);
                eprintln!("[Sidecar] path2: Trying cwd/frontend/src-tauri/binaries: {} (exists: {})", p.display(), p.exists());
                if p.exists() {
                    return Some(p);
                }
                // Try: cwd/../frontend/src-tauri/binaries/ (if in src-tauri)
                if let Some(parent) = cwd.parent() {
                    let p = parent.join("frontend").join("src-tauri").join("binaries").join(binary_name);
                    eprintln!("[Sidecar] path2: Trying parent/frontend/src-tauri/binaries: {} (exists: {})", p.display(), p.exists());
                    if p.exists() {
                        return Some(p);
                    }
                }
                None
            });
        
        // Option 3: Try absolute path (dev fallback for Windows)
        #[cfg(windows)]
        let path3 = {
            let abs_path = std::path::PathBuf::from(r"d:\LP\frontend\src-tauri\binaries").join(binary_name);
            let exists = abs_path.exists();
            eprintln!("[Sidecar] path3: Trying absolute path: {} (exists: {})", abs_path.display(), exists);
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
    
    let spawn_result = if let Some(binary_path) = bundled_binary {
        // Use bundled binary (no args needed, binary is self-contained)
        eprintln!("[Sidecar] Using bundled binary: {}", binary_path.display());
        bridge.spawn_with_env(binary_path.to_str().unwrap(), &[], None, Some(&env_vars))
    } else {
        eprintln!("[Sidecar] Bundled binary not found, falling back to source mode");
        // Fallback to source mode: use Python interpreter
        #[cfg(target_os = "android")]
        let python_exe = "python";
        #[cfg(target_os = "windows")]
        let python_exe = "python";
        #[cfg(not(any(target_os = "android", target_os = "windows")))]
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
                std::env::current_dir()
                    .ok()
                    .and_then(|cwd| {
                        if cwd.ends_with("frontend") {
                            cwd.parent().map(|p| p.to_path_buf())
                        } else {
                            Some(cwd)
                        }
                    })
            });
        
        let root = project_root.as_deref().map(|p| p.display().to_string()).unwrap_or_else(|| "unknown".to_string());
        eprintln!("[Sidecar] Using source mode: {} -m backend.sidecar_main (root: {})", python_exe, root);
        // Source mode: Python will read .env file itself, but we can still pass env vars for consistency
        bridge.spawn_with_env(python_exe, &["-m", "backend.sidecar_main"], project_root.as_deref(), Some(&env_vars))
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
            PythonMessage::SqlQuery { request_id: rid, sql, params } => {
                let result = db_commands::sql_query(sql, params).await;
                let response = match result {
                    Ok(data) => RustMessage::sql_response(&rid, serde_json::json!(data)),
                    Err(e) => RustMessage::error(&rid, &e),
                };
                bridge.send(&response)?;
            }
            PythonMessage::SqlExecute { request_id: rid, sql, params } => {
                let result = db_commands::sql_execute(sql, params).await;
                let response = match result {
                    Ok(data) => RustMessage::sql_response(&rid, serde_json::json!(data)),
                    Err(e) => RustMessage::error(&rid, &e),
                };
                bridge.send(&response)?;
            }
            PythonMessage::Response { request_id: rid, status, data, error } => {
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

// For desktop builds, use main() as entry point
// For Android builds, use lib.rs::run() as entry point
#[cfg(not(target_os = "android"))]
fn main() {
    // Initialize database
    // For desktop, use user data directory
    let db_path = std::env::var("APPDATA")
        .or_else(|_| std::env::var("HOME"))
        .map(|p| std::path::PathBuf::from(p).join("lesson_planner.db"))
        .unwrap_or_else(|_| std::path::PathBuf::from("lesson_planner.db"));
    
    if let Err(e) = db_commands::init_database(db_path) {
        eprintln!("Failed to initialize database: {}", e);
    }
    
    let bridge = SidecarBridge::new();
    
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_shell::init())
        .manage(bridge)
        .invoke_handler(tauri::generate_handler![
            show_in_folder,
            open_file,
            save_file_dialog,
            trigger_sync,
            db_commands::sql_query,
            db_commands::sql_execute,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

// For Android, main() just calls lib.rs::run()
#[cfg(target_os = "android")]
fn main() {
    bilingual_lesson_planner::run();
}
