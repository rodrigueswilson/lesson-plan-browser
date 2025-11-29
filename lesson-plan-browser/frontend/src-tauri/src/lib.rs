// Library entry point for Android builds
// This is used when building for Android (shared library)

mod db_commands;

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
    // For Android, use app data directory; for desktop, use user data directory
    #[cfg(target_os = "android")]
    let db_path = std::path::PathBuf::from("/data/data/com.lessonplanner.browser/databases/lesson_planner.db");
    
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
        .invoke_handler(tauri::generate_handler![
            db_commands::sql_query,
            db_commands::sql_execute,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

