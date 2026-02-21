//! SQL execution commands for local database using rusqlite

use rusqlite::{Connection, Row, ToSql};
use serde::{Deserialize, Serialize};
use std::env;
use std::fs;
use std::sync::Mutex;
use std::path::PathBuf;

// Global database connection (thread-safe)
static DB: Mutex<Option<Connection>> = Mutex::new(None);

#[derive(Debug, Serialize, Deserialize)]
pub struct ExecResult {
    pub rows_affected: u64,
    pub last_insert_id: i64,
}

/// Attempt to find and copy a bundled database from known asset locations.
/// Returns true if a bundled database was successfully copied.
#[cfg(target_os = "android")]
fn try_copy_bundled_database(target_path: &PathBuf) -> bool {
    // On Android, the build script places the bundled database in these potential locations:
    // 1. The APK's assets directory (accessible via app's internal storage after extraction)
    // 2. A known location where we might stage the database
    
    let bundled_paths = vec![
        // Path where Tauri might extract bundled assets
        PathBuf::from("/data/data/com.lessonplanner.browser/files/databases/lesson_planner_bundled.db"),
        // External storage path (requires MANAGE_EXTERNAL_STORAGE permission)
        PathBuf::from("/sdcard/Android/data/com.lessonplanner.browser/files/databases/lesson_planner.db"),
        // Alternative internal path
        PathBuf::from("/data/data/com.lessonplanner.browser/cache/databases/lesson_planner.db"),
    ];
    
    for bundled_path in bundled_paths {
        if bundled_path.exists() {
            eprintln!("[DB] Found bundled database at: {}", bundled_path.display());
            
            // Check if bundled DB has actual data (file size > 0)
            if let Ok(metadata) = fs::metadata(&bundled_path) {
                if metadata.len() > 0 {
                    // Attempt to copy the bundled database
                    match fs::copy(&bundled_path, target_path) {
                        Ok(bytes) => {
                            eprintln!("[DB] Copied bundled database ({} bytes) to: {}", bytes, target_path.display());
                            return true;
                        }
                        Err(e) => {
                            eprintln!("[DB] Failed to copy bundled database: {}", e);
                        }
                    }
                }
            }
        }
    }
    
    eprintln!("[DB] No bundled database found. Database will be empty.");
    eprintln!("[DB] To populate data, use: .\\update-tablet.ps1 or .\\copy-db-to-tablet.ps1");
    false
}

#[cfg(not(target_os = "android"))]
fn try_copy_bundled_database(_target_path: &PathBuf) -> bool {
    // On desktop, we don't attempt to copy bundled databases
    false
}

/// Check if the database has any user data (i.e., is not empty)
fn database_has_data(conn: &Connection) -> bool {
    match conn.query_row("SELECT COUNT(*) FROM users", [], |row| row.get::<_, i64>(0)) {
        Ok(count) => count > 0,
        Err(_) => false,
    }
}

pub fn init_database(db_path: PathBuf) -> Result<(), String> {
    // Ensure parent directory exists (especially for Android)
    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|e| format!("Failed to create database directory: {}", e))?;
    }
    
    // Check if database file exists and has content
    let db_exists = db_path.exists() && fs::metadata(&db_path).map(|m| m.len() > 0).unwrap_or(false);
    
    // If database doesn't exist or is empty, try to copy from bundled assets
    if !db_exists {
        eprintln!("[DB] Database not found or empty at: {}", db_path.display());
        try_copy_bundled_database(&db_path);
    }
    
    let mut db_guard = DB.lock().map_err(|e| format!("Lock error: {}", e))?;
    
    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;
    
    // Run migrations (creates tables if they don't exist)
    run_migrations(&conn)?;
    
    // Check if database has actual data
    if !database_has_data(&conn) {
        eprintln!("[DB] WARNING: Database is empty (no users found).");
        eprintln!("[DB] Push data using: .\\update-tablet.ps1 or .\\copy-db-to-tablet.ps1");
    } else {
        eprintln!("[DB] Database initialized with existing data.");
    }
    
    *db_guard = Some(conn);
    Ok(())
}

fn run_migrations(conn: &Connection) -> Result<(), String> {
    // Create tables if they don't exist
    conn.execute(
        include_str!("../migrations/001_users.sql"),
        [],
    ).map_err(|e| format!("Migration 1 failed: {}", e))?;
    
    conn.execute(
        include_str!("../migrations/002_class_slots.sql"),
        [],
    ).map_err(|e| format!("Migration 2 failed: {}", e))?;
    
    conn.execute(
        include_str!("../migrations/003_weekly_plans.sql"),
        [],
    ).map_err(|e| format!("Migration 3 failed: {}", e))?;
    
    conn.execute(
        include_str!("../migrations/004_schedule_entries.sql"),
        [],
    ).map_err(|e| format!("Migration 4 failed: {}", e))?;
    
    conn.execute(
        include_str!("../migrations/005_lesson_steps.sql"),
        [],
    ).map_err(|e| format!("Migration 5 failed: {}", e))?;
    
    conn.execute(
        include_str!("../migrations/006_lesson_mode_sessions.sql"),
        [],
    ).map_err(|e| format!("Migration 6 failed: {}", e))?;
    
    Ok(())
}

fn resolve_app_data_dir() -> Result<PathBuf, String> {
    #[cfg(target_os = "android")]
    {
        Ok(PathBuf::from("/data/data/com.lessonplanner.browser/files"))
    }
    #[cfg(not(target_os = "android"))]
    {
        if let Ok(appdata) = env::var("APPDATA") {
            return Ok(PathBuf::from(appdata).join("lesson_plan_browser"));
        }
        if let Ok(home) = env::var("HOME") {
            return Ok(PathBuf::from(home).join(".lesson_plan_browser"));
        }
        Err("Unable to determine app data directory".to_string())
    }
}

fn row_to_json(row: &Row) -> Result<serde_json::Map<String, serde_json::Value>, rusqlite::Error> {
    let mut map = serde_json::Map::new();
    let column_count = row.as_ref().column_count();
    
    for i in 0..column_count {
        let column_name = row.as_ref().column_name(i)?;
        let value: rusqlite::types::Value = row.get(i)?;
        
        let json_value = match value {
            rusqlite::types::Value::Null => serde_json::Value::Null,
            rusqlite::types::Value::Integer(i) => serde_json::Value::Number(i.into()),
            rusqlite::types::Value::Real(f) => {
                serde_json::Value::Number(
                    serde_json::Number::from_f64(f).unwrap_or(0.into())
                )
            },
            rusqlite::types::Value::Text(s) => serde_json::Value::String(s),
            rusqlite::types::Value::Blob(b) => {
                // Encode blob as base64 string
                use base64::{Engine as _, engine::general_purpose};
                serde_json::Value::String(general_purpose::STANDARD.encode(b))
            },
        };
        
        map.insert(column_name.to_string(), json_value);
    }
    
    Ok(map)
}

// Helper to convert JSON params to rusqlite params
fn json_to_sqlite_params(params: Vec<serde_json::Value>) -> Vec<Box<dyn ToSql>> {
    params.into_iter().map(|v| {
        let sql_value: Box<dyn ToSql> = match v {
            serde_json::Value::Null => Box::new(rusqlite::types::Null),
            serde_json::Value::Number(n) => {
                if let Some(i) = n.as_i64() {
                    Box::new(i)
                } else if let Some(f) = n.as_f64() {
                    Box::new(f)
                } else {
                    Box::new(n.to_string())
                }
            },
            serde_json::Value::String(s) => Box::new(s),
            serde_json::Value::Bool(b) => Box::new(if b { 1i64 } else { 0i64 }),
            serde_json::Value::Array(_) | serde_json::Value::Object(_) => {
                // Serialize complex types to JSON string
                Box::new(serde_json::to_string(&v).unwrap_or_else(|_| "{}".to_string()))
            },
        };
        sql_value
    }).collect()
}

#[allow(dead_code)]
#[tauri::command]
pub async fn sql_query(
    sql: String,
    params: Vec<serde_json::Value>,
) -> Result<Vec<serde_json::Map<String, serde_json::Value>>, String> {
    let db_guard = DB.lock().map_err(|e| format!("Lock error: {}", e))?;
    let conn = db_guard.as_ref().ok_or("Database not initialized")?;
    
    let sqlite_params = json_to_sqlite_params(params);
    let param_refs: Vec<&dyn ToSql> = sqlite_params.iter().map(|p| p.as_ref()).collect();
    
    let mut stmt = conn.prepare(&sql)
        .map_err(|e| format!("SQL prepare error: {}", e))?;
    
    let rows = stmt.query_map(&param_refs[..], |row| {
        row_to_json(row)
    }).map_err(|e| format!("SQL query error: {}", e))?;
    
    let mut results = Vec::new();
    for row_result in rows {
        results.push(row_result.map_err(|e| format!("Row error: {}", e))?);
    }
    
    Ok(results)
}

#[allow(dead_code)]
#[tauri::command]
pub async fn sql_execute(
    sql: String,
    params: Vec<serde_json::Value>,
) -> Result<ExecResult, String> {
    let db_guard = DB.lock().map_err(|e| format!("Lock error: {}", e))?;
    let conn = db_guard.as_ref().ok_or("Database not initialized")?;
    
    let sqlite_params = json_to_sqlite_params(params);
    let param_refs: Vec<&dyn ToSql> = sqlite_params.iter().map(|p| p.as_ref()).collect();
    
    let rows_affected = conn.execute(&sql, &param_refs[..])
        .map_err(|e| format!("SQL execute error: {}", e))?;
    
    let last_insert_id = conn.last_insert_rowid();
    
    Ok(ExecResult {
        rows_affected: rows_affected as u64,
        last_insert_id,
    })
}

#[allow(dead_code)]
#[tauri::command]
pub async fn get_app_data_dir() -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(|| -> Result<String, String> {
        let dir = resolve_app_data_dir()?;
        fs::create_dir_all(&dir).map_err(|e| format!("Failed to create app data dir: {}", e))?;
        Ok(dir.to_string_lossy().into_owned())
    })
    .await
    .map_err(|e| e.to_string())?
}

#[allow(dead_code)]
#[deprecated(note = "Use database lesson_json column instead. This command will be removed in a future version.")]
#[tauri::command]
pub async fn read_json_file(path: String) -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(move || -> Result<String, String> {
        let path_buf = PathBuf::from(path);
        fs::read_to_string(&path_buf).map_err(|e| format!("Failed to read JSON file: {}", e))
    })
    .await
    .map_err(|e| e.to_string())?
}

#[allow(dead_code)]
#[deprecated(note = "Use database lesson_json column instead. This command will be removed in a future version.")]
#[tauri::command]
pub async fn write_json_file(path: String, content: String) -> Result<(), String> {
    tauri::async_runtime::spawn_blocking(move || -> Result<(), String> {
        let path_buf = PathBuf::from(path);
        if let Some(parent) = path_buf.parent() {
            fs::create_dir_all(parent).map_err(|e| format!("Failed to create parent directory: {}", e))?;
        }
        fs::write(&path_buf, content).map_err(|e| format!("Failed to write JSON file: {}", e))?;
        Ok(())
    })
    .await
    .map_err(|e| e.to_string())?
}

#[allow(dead_code)]
#[deprecated(note = "Use database query instead. This command will be removed in a future version.")]
#[tauri::command]
pub async fn list_json_files(base_path: String) -> Result<Vec<String>, String> {
    tauri::async_runtime::spawn_blocking(move || -> Result<Vec<String>, String> {
        let base = PathBuf::from(base_path);
        fs::create_dir_all(&base).map_err(|e| format!("Failed to create base directory: {}", e))?;
        let mut files: Vec<String> = Vec::new();
        if base.exists() {
            for entry in fs::read_dir(&base).map_err(|e| format!("Failed to read directory: {}", e))? {
                let entry = entry.map_err(|e| format!("Failed to read entry: {}", e))?;
                let file_type = entry.file_type().map_err(|e| format!("Failed to read file type: {}", e))?;
                if file_type.is_file() {
                    if let Some(ext) = entry.path().extension().and_then(|v| v.to_str()) {
                        if !ext.eq_ignore_ascii_case("json") {
                            continue;
                        }
                    } else {
                        continue;
                    }
                    if let Some(name) = entry.file_name().to_str() {
                        files.push(name.to_string());
                    }
                }
            }
        }
        files.sort();
        files.reverse();
        Ok(files)
    })
    .await
    .map_err(|e| e.to_string())?
}

