// Library entry point for Android builds
// This is used when building for Android (shared library)

mod db_commands;

use tauri_plugin_shell::ShellExt;

#[tauri::command]
fn open_file(app: tauri::AppHandle, path: String) -> Result<(), String> {
    app.shell().open(path, None).map_err(|e| e.to_string())
}

/// Log a message from the frontend so it appears in adb logcat (for debugging standalone DB / "No weeks" issues).
#[tauri::command]
fn log_to_native(_app: tauri::AppHandle, message: String) -> Result<(), String> {
    eprintln!("[LP] {}", message);
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Add panic hook to capture actual error message
    std::panic::set_hook(Box::new(|panic_info| {
        let location = panic_info.location().unwrap_or_else(|| std::panic::Location::caller());
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
    // For Android: run-as writes to CWD (app data dir), which can be /data/user/0/... on some devices
    // while the app may resolve /data/data/... differently. Try both so we open the DB wherever push wrote it.
    #[cfg(target_os = "android")]
    let db_path = {
        use std::fs;
        let candidates = [
            "/data/user/0/com.lessonplanner.browser/databases/lesson_planner.db",
            "/data/data/com.lessonplanner.browser/databases/lesson_planner.db",
        ];
        candidates
            .iter()
            .map(std::path::PathBuf::from)
            .find(|p| p.exists() && fs::metadata(p).map(|m| m.len() > 0).unwrap_or(false))
            .unwrap_or_else(|| std::path::PathBuf::from(candidates[0]))
    };

    #[cfg(not(target_os = "android"))]
    let db_path = std::env::var("APPDATA")
        .or_else(|_| std::env::var("HOME"))
        .map(|p| std::path::PathBuf::from(p).join("lesson_planner.db"))
        .unwrap_or_else(|_| std::path::PathBuf::from("lesson_planner.db"));

    eprintln!("[DB] Initializing database at: {}", db_path.display());
    if let Err(e) = db_commands::init_database(db_path) {
        eprintln!("Failed to initialize database: {}", e);
    }
    
    eprintln!("[Tauri] Building app...");
    let builder = tauri::Builder::default();
    
    eprintln!("[Tauri] Running app...");
    builder
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            open_file,
            log_to_native,
            db_commands::sql_query,
            db_commands::sql_execute,
            db_commands::get_app_data_dir,
            db_commands::read_json_file,
            db_commands::write_json_file,
            db_commands::list_json_files,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

