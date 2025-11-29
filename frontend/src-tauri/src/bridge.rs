//! Python Sidecar IPC Bridge
//!
//! On desktop: Uses std::process::Command to spawn Python directly
//! On Android: Will use Tauri shell plugin API (implementation pending)

use std::collections::HashMap;
use std::io::{BufRead, BufReader, Write};
#[cfg(not(target_os = "android"))]
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

#[cfg(not(target_os = "android"))]
pub struct SidecarBridge {
    process: Mutex<Option<Child>>,
    stdin: Mutex<Option<ChildStdin>>,
    stdout: Mutex<Option<BufReader<ChildStdout>>>,
    is_running: Mutex<bool>,
}

#[cfg(target_os = "android")]
pub struct SidecarBridge {
    app_handle: Mutex<Option<tauri::AppHandle>>,
    sidecar_handle: Mutex<Option<tauri_plugin_shell::process::CommandChild>>,
    stdin: Mutex<Option<std::process::ChildStdin>>,
    stdout: Mutex<Option<std::io::BufReader<std::process::ChildStdout>>>,
    is_running: Mutex<bool>,
}

impl SidecarBridge {
    pub fn new() -> Self {
        #[cfg(not(target_os = "android"))]
        {
            Self {
                process: Mutex::new(None),
                stdin: Mutex::new(None),
                stdout: Mutex::new(None),
                is_running: Mutex::new(false),
            }
        }
        #[cfg(target_os = "android")]
        {
            Self {
                app_handle: Mutex::new(None),
                sidecar_handle: Mutex::new(None),
                stdin: Mutex::new(None),
                stdout: Mutex::new(None),
                is_running: Mutex::new(false),
            }
        }
    }

    #[cfg(not(target_os = "android"))]
    pub fn spawn(&self, executable: &str, args: &[&str], working_dir: Option<&std::path::Path>) -> Result<(), String> {
        self.spawn_with_env(executable, args, working_dir, None)
    }
    
    #[cfg(not(target_os = "android"))]
    pub fn spawn_with_env(&self, executable: &str, args: &[&str], working_dir: Option<&std::path::Path>, env_vars: Option<&HashMap<String, String>>) -> Result<(), String> {
        let mut is_running = self.is_running.lock().map_err(|e| e.to_string())?;
        if *is_running { 
            eprintln!("[Sidecar] Sidecar already running, reusing existing process");
            return Ok(()); 
        }
        eprintln!("[Sidecar] Spawning sidecar: {} {:?} (working_dir: {:?})", executable, args, working_dir);

        let mut cmd = Command::new(executable);
        if !args.is_empty() {
            cmd.args(args);
        }
        cmd.stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit());
        
        if let Some(dir) = working_dir {
            cmd.current_dir(dir);
        }
        
        // Set environment variables if provided
        if let Some(envs) = env_vars {
            eprintln!("[Sidecar] Setting {} environment variables", envs.len());
            for (key, value) in envs {
                cmd.env(key, value);
            }
        }
        
        let mut child = cmd.spawn()
            .map_err(|e| format!("Spawn failed: {}", e))?;

        *self.stdin.lock().unwrap() = child.stdin.take();
        *self.stdout.lock().unwrap() = child.stdout.take().map(BufReader::new);
        *self.process.lock().unwrap() = Some(child);
        *is_running = true;
        Ok(())
    }

    #[cfg(target_os = "android")]
    pub fn spawn(&self, _python_exe: &str, _args: &[&str], _working_dir: Option<&std::path::Path>) -> Result<(), String> {
        self.spawn_with_env(_python_exe, _args, _working_dir, None)
    }
    
    #[cfg(target_os = "android")]
    pub fn spawn_with_env(&self, _python_exe: &str, _args: &[&str], _working_dir: Option<&std::path::Path>, _env_vars: Option<&HashMap<String, String>>) -> Result<(), String> {
        // Android sidecar not implemented - just return ok for now to avoid panic during startup
        eprintln!("[Sidecar] Android sidecar called but not implemented - returning success");
        Ok(())
    }

    #[cfg(not(target_os = "android"))]
    pub fn send(&self, message: &RustMessage) -> Result<(), String> {
        let json = serde_json::to_string(message).map_err(|e| e.to_string())?;
        if let Some(stdin) = self.stdin.lock().unwrap().as_mut() {
            writeln!(stdin, "{}", json).map_err(|e| e.to_string())?;
            stdin.flush().map_err(|e| e.to_string())?;
        }
        Ok(())
    }

    #[cfg(target_os = "android")]
    pub fn send(&self, message: &RustMessage) -> Result<(), String> {
        use std::io::Write;
        
        let json = serde_json::to_string(message).map_err(|e| e.to_string())?;
        
        if let Some(stdin) = self.stdin.lock().unwrap().as_mut() {
            writeln!(stdin, "{}", json).map_err(|e| format!("Failed to write to sidecar stdin: {}", e))?;
            stdin.flush().map_err(|e| format!("Failed to flush stdin: {}", e))?;
        } else {
            return Err("No stdin available for sidecar".into());
        }
        
        Ok(())
    }

    #[cfg(not(target_os = "android"))]
    pub fn receive(&self) -> Result<PythonMessage, String> {
        if let Some(stdout) = self.stdout.lock().unwrap().as_mut() {
            let mut line = String::new();
            stdout.read_line(&mut line).map_err(|e| e.to_string())?;
            serde_json::from_str(line.trim()).map_err(|e| e.to_string())
        } else {
            Err("Sidecar not running".into())
        }
    }

    #[cfg(target_os = "android")]
    pub fn receive(&self) -> Result<PythonMessage, String> {
        use std::io::BufRead;
        
        if let Some(stdout) = self.stdout.lock().unwrap().as_mut() {
            let mut line = String::new();
            stdout.read_line(&mut line)
                .map_err(|e| format!("Failed to read from sidecar stdout: {}", e))?;
            serde_json::from_str(line.trim()).map_err(|e| e.to_string())
        } else {
            Err("No stdout available for sidecar".into())
        }
    }

    #[cfg(not(target_os = "android"))]
    pub fn shutdown(&self) -> Result<(), String> {
        if let Some(mut child) = self.process.lock().unwrap().take() {
            let _ = child.kill();
        }
        *self.is_running.lock().unwrap() = false;
        Ok(())
    }

    #[cfg(target_os = "android")]
    pub fn shutdown(&self) -> Result<(), String> {
        if let Some(mut child) = self.sidecar_handle.lock().unwrap().take() {
            child.kill().map_err(|e| format!("Failed to kill sidecar: {}", e))?;
        }
        *self.is_running.lock().unwrap() = false;
        Ok(())
    }
    
    // set_app_handle is available for all platforms, but only needed on Android
    pub fn set_app_handle(&self, app: tauri::AppHandle) {
        #[cfg(target_os = "android")]
        {
            *self.app_handle.lock().unwrap() = Some(app);
        }
        #[cfg(not(target_os = "android"))]
        {
            let _ = app; // Suppress unused warning on non-Android platforms
        }
    }
}
