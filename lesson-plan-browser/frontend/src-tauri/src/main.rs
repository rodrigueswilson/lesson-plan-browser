// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod db_commands;

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
    
    tauri::Builder::default()
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
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

// For Android, main() just calls lib.rs::run()
#[cfg(target_os = "android")]
fn main() {
    lesson_plan_browser::run();
}

