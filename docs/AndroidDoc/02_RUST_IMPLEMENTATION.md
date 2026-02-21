# Phase 2: Rust IPC Bridge Implementation

## 2.0 Version Decision

**Decision:** Using Tauri v2.0 (tested and working)
- ✅ Desktop IPC tested and working
- ✅ Database operations verified
- ✅ Sync functionality confirmed
- Use `rusqlite` directly (works with both v1.5 and v2.0)
- Tauri v2.0 provides better plugin system and Android support

## 2.1 Cargo.toml Updates

**File:** `frontend/src-tauri/Cargo.toml`

```toml
[package]
name = "bilingual-lesson-planner"
version = "1.0.0"
description = "Bilingual Weekly Lesson Plan Builder"
edition = "2021"

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

[features]
default = ["custom-protocol"]
custom-protocol = ["tauri/custom-protocol"]
```

**Note:** Using `rusqlite` directly (works with both v1.5 and v2.0). Tauri v2.0 uses separate plugin crates instead of feature flags.

## 2.2 Sidecar Bridge Module

**File:** `frontend/src-tauri/src/bridge.rs`

```rust
//! Python Sidecar IPC Bridge

use std::io::{BufRead, BufReader, Write};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::Mutex;
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
#[serde(tag = "type")]
pub enum PythonMessage {
    #[serde(rename = "sql_query")]
    SqlQuery { request_id: String, sql: String, params: Vec<serde_json::Value> },
    #[serde(rename = "sql_execute")]
    SqlExecute { request_id: String, sql: String, params: Vec<serde_json::Value> },
    #[serde(rename = "response")]
    Response { request_id: String, status: String, data: Option<serde_json::Value>, error: Option<String> },
}

#[derive(Debug, Serialize)]
pub struct RustMessage {
    #[serde(rename = "type")]
    pub msg_type: String,
    pub request_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub command: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub status: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub user_id: Option<String>,
}

impl RustMessage {
    pub fn command(request_id: &str, command: &str, user_id: Option<&str>) -> Self {
        Self {
            msg_type: "command".to_string(),
            request_id: request_id.to_string(),
            command: Some(command.to_string()),
            status: None, data: None, error: None,
            user_id: user_id.map(|s| s.to_string()),
        }
    }

    pub fn sql_response(request_id: &str, data: serde_json::Value) -> Self {
        Self {
            msg_type: "sql_response".to_string(),
            request_id: request_id.to_string(),
            command: None,
            status: Some("success".to_string()),
            data: Some(data),
            error: None, user_id: None,
        }
    }

    pub fn error(request_id: &str, error: &str) -> Self {
        Self {
            msg_type: "sql_response".to_string(),
            request_id: request_id.to_string(),
            command: None,
            status: Some("error".to_string()),
            data: None,
            error: Some(error.to_string()),
            user_id: None,
        }
    }
}

pub struct SidecarBridge {
    process: Mutex<Option<Child>>,
    stdin: Mutex<Option<ChildStdin>>,
    stdout: Mutex<Option<BufReader<ChildStdout>>>,
    is_running: Mutex<bool>,
}

impl SidecarBridge {
    pub fn new() -> Self {
        Self {
            process: Mutex::new(None),
            stdin: Mutex::new(None),
            stdout: Mutex::new(None),
            is_running: Mutex::new(false),
        }
    }

    pub fn spawn(&self, python_exe: &str, args: &[&str]) -> Result<(), String> {
        let mut is_running = self.is_running.lock().map_err(|e| e.to_string())?;
        if *is_running { return Ok(()); }

        let mut child = Command::new(python_exe)
            .args(args)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .map_err(|e| format!("Spawn failed: {}", e))?;

        *self.stdin.lock().unwrap() = child.stdin.take();
        *self.stdout.lock().unwrap() = child.stdout.take().map(BufReader::new);
        *self.process.lock().unwrap() = Some(child);
        *is_running = true;
        Ok(())
    }

    pub fn send(&self, message: &RustMessage) -> Result<(), String> {
        let json = serde_json::to_string(message).map_err(|e| e.to_string())?;
        if let Some(stdin) = self.stdin.lock().unwrap().as_mut() {
            writeln!(stdin, "{}", json).map_err(|e| e.to_string())?;
            stdin.flush().map_err(|e| e.to_string())?;
        }
        Ok(())
    }

    pub fn receive(&self) -> Result<PythonMessage, String> {
        if let Some(stdout) = self.stdout.lock().unwrap().as_mut() {
            let mut line = String::new();
            stdout.read_line(&mut line).map_err(|e| e.to_string())?;
            serde_json::from_str(line.trim()).map_err(|e| e.to_string())
        } else {
            Err("Sidecar not running".into())
        }
    }

    pub fn shutdown(&self) -> Result<(), String> {
        if let Some(mut child) = self.process.lock().unwrap().take() {
            let _ = child.kill();
            let _ = child.wait();
        }
        *self.is_running.lock().unwrap() = false;
        Ok(())
    }
}
```

## 2.3 Database Commands Module

**File:** `frontend/src-tauri/src/db_commands.rs`

```rust
//! SQL execution commands for Python IPC using rusqlite

use rusqlite::{Connection, params_from_iter, Row};
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use std::path::PathBuf;
use tauri::Manager;

// Global database connection (thread-safe)
static DB: Mutex<Option<Connection>> = Mutex::new(None);

#[derive(Debug, Serialize, Deserialize)]
pub struct ExecResult {
    pub rows_affected: u64,
    pub last_insert_id: i64,
}

pub fn init_database(db_path: PathBuf) -> Result<(), String> {
    let mut db_guard = DB.lock().map_err(|e| format!("Lock error: {}", e))?;
    
    let conn = Connection::open(&db_path)
        .map_err(|e| format!("Failed to open database: {}", e))?;
    
    // Run migrations
    run_migrations(&conn)?;
    
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
    
    Ok(())
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
// rusqlite accepts &[&dyn ToSql] or named parameters
fn json_to_sqlite_to_sql(params: Vec<serde_json::Value>) -> Vec<Box<dyn rusqlite::ToSql>> {
    params.into_iter().map(|v| {
        let sql_value: Box<dyn rusqlite::ToSql> = match v {
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
            _ => Box::new(v.to_string()),
        };
        sql_value
    }).collect()
}

#[tauri::command]
pub async fn sql_query(
    sql: String,
    params: Vec<serde_json::Value>,
) -> Result<Vec<serde_json::Map<String, serde_json::Value>>, String> {
    let db_guard = DB.lock().map_err(|e| format!("Lock error: {}", e))?;
    let conn = db_guard.as_ref().ok_or("Database not initialized")?;
    
    let sqlite_params = json_to_sqlite_to_sql(params);
    let param_refs: Vec<&dyn rusqlite::ToSql> = sqlite_params.iter().map(|p| p.as_ref()).collect();
    
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

#[tauri::command]
pub async fn sql_execute(
    sql: String,
    params: Vec<serde_json::Value>,
) -> Result<ExecResult, String> {
    let db_guard = DB.lock().map_err(|e| format!("Lock error: {}", e))?;
    let conn = db_guard.as_ref().ok_or("Database not initialized")?;
    
    let sqlite_params = json_to_sqlite_to_sql(params);
    let param_refs: Vec<&dyn rusqlite::ToSql> = sqlite_params.iter().map(|p| p.as_ref()).collect();
    
    let rows_affected = conn.execute(&sql, &param_refs[..])
        .map_err(|e| format!("SQL execute error: {}", e))?;
    
    let last_insert_id = conn.last_insert_rowid();
    
    Ok(ExecResult {
        rows_affected: rows_affected as u64,
        last_insert_id,
    })
}
```

**Note:** Using `rusqlite` directly instead of `tauri-plugin-sql`. Database connection is managed as a global static with Mutex for thread safety.

## 2.4 Main Entry Point

**File:** `frontend/src-tauri/src/main.rs`

```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod bridge;
mod db_commands;

use bridge::{SidecarBridge, RustMessage, PythonMessage};
use tauri::Manager;

#[tauri::command]
async fn trigger_sync(
    app: tauri::AppHandle,
    user_id: String,
) -> Result<serde_json::Value, String> {
    let bridge = app.state::<SidecarBridge>();
    let request_id = uuid::Uuid::new_v4().to_string();
    
    // Send sync command to Python
    let cmd = RustMessage::command(&request_id, "full_sync", Some(&user_id));
    bridge.send(&cmd)?;
    
    // Handle IPC loop (SQL requests from Python)
    loop {
        let msg = bridge.receive()?;
        match msg {
            PythonMessage::SqlQuery { request_id: rid, sql, params } => {
                let result = db_commands::sql_query(app.clone(), sql, params).await;
                let response = match result {
                    Ok(data) => RustMessage::sql_response(&rid, serde_json::json!(data)),
                    Err(e) => RustMessage::error(&rid, &e),
                };
                bridge.send(&response)?;
            }
            PythonMessage::SqlExecute { request_id: rid, sql, params } => {
                let result = db_commands::sql_execute(app.clone(), sql, params).await;
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

fn main() {
    // Initialize database
    let db_path = std::env::var("APPDATA")
        .or_else(|_| std::env::var("HOME"))
        .map(|p| std::path::PathBuf::from(p).join("lesson_planner.db"))
        .unwrap_or_else(|_| std::path::PathBuf::from("lesson_planner.db"));
    
    if let Err(e) = db_commands::init_database(db_path) {
        eprintln!("Failed to initialize database: {}", e);
    }
    
    let bridge = SidecarBridge::new();
    
    tauri::Builder::default()
        .manage(bridge)
        .invoke_handler(tauri::generate_handler![
            trigger_sync,
            db_commands::sql_query,
            db_commands::sql_execute,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

**Note:** Database initialization happens at startup. For Android, use app data directory path.
```
