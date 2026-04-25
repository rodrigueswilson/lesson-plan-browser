//! ADB "push to tablet" without `run-as` (works for release / non-debuggable installs).
//! DB is written to app-specific external storage; the Android app copies it in on next launch.
//! Matches `scripts/sync-to-tablet.ps1` path.

use std::path::Path;
use std::process::Command;

const PACKAGE: &str = "com.lessonplanner.browser";
const ACTIVITY: &str = "com.lessonplanner.browser/.MainActivity";

/// Host-side ADB path where we `adb push` the file (same on device and for `ls` from shell user).
pub const INCOMING_TRANSFER_PATH: &str =
    "/sdcard/Android/data/com.lessonplanner.browser/files/transfer/lesson_planner.db";

fn run_command_capture(mut cmd: Command) -> Result<String, String> {
    let output = cmd.output().map_err(|e| e.to_string())?;
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    if output.status.success() {
        return Ok(format!("{}{}", stdout, stderr).trim().to_string());
    }
    Err(format!("{}{}", stdout, stderr).trim().to_string())
}

/// After `adb push` to the incoming path and app restart, copy the file into internal SQLite path.
#[cfg(target_os = "android")]
pub fn apply_incoming_transfer_if_present(db_path: &Path) {
    if let Some(parent) = Path::new(INCOMING_TRANSFER_PATH).parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let pending = Path::new(INCOMING_TRANSFER_PATH);
    let Ok(meta) = std::fs::metadata(pending) else {
        return;
    };
    if meta.len() == 0 {
        return;
    }
    let target_str = db_path.to_string_lossy();
    for suffix in ["-wal", "-shm"] {
        let p = format!("{target_str}{suffix}");
        let _ = std::fs::remove_file(p);
    }
    let _ = std::fs::remove_file(db_path);
    match std::fs::copy(pending, db_path) {
        Ok(bytes) => {
            eprintln!(
                "[DB] Imported {bytes} bytes from ADB transfer ({INCOMING_TRANSFER_PATH}) to {}",
                db_path.display()
            );
            let _ = std::fs::remove_file(pending);
        }
        Err(e) => {
            eprintln!("[DB] Could not import transfer database: {e}");
        }
    }
}

/// Push a local `lesson_planner.db` to the tablet, restart the app, and import on the next `init_database`.
pub fn push_tablet_database(device: &str, local_path: &Path) -> Result<serde_json::Value, String> {
    let record_ok = |name: &str, output: String| -> serde_json::Value {
        serde_json::json!({ "step": name, "ok": true, "output": output })
    };
    let record_err = |name: &str, output: String| -> serde_json::Value {
        serde_json::json!({ "step": name, "ok": false, "output": output })
    };

    let local_display = local_path.to_string_lossy();
    let mut steps: Vec<serde_json::Value> = Vec::new();

    let mut adb_stop_cmd = Command::new("adb");
    adb_stop_cmd
        .arg("-s")
        .arg(device)
        .args(["shell", "am", "force-stop", PACKAGE]);
    let _ = run_command_capture(adb_stop_cmd)
        .map(|out| steps.push(record_ok("force_stop", out)))
        .map_err(|out| {
            steps.push(record_err("force_stop", out.clone()));
            out
        });

    if let Some(transfer_parent) = Path::new(INCOMING_TRANSFER_PATH)
        .parent()
        .and_then(|p| p.to_str())
    {
        let mut m = Command::new("adb");
        m.arg("-s")
            .arg(device)
            .args(["shell", "mkdir", "-p", transfer_parent]);
        if let Ok(out) = run_command_capture(m) {
            steps.push(record_ok("shell_mkdir_transfer", out));
        }
    }

    let mut adb_push_cmd = Command::new("adb");
    adb_push_cmd
        .arg("-s")
        .arg(device)
        .arg("push")
        .arg(local_path)
        .arg(INCOMING_TRANSFER_PATH);
    match run_command_capture(adb_push_cmd) {
        Ok(out) => steps.push(record_ok("adb_push_transfer", out)),
        Err(out) => {
            steps.push(record_err("adb_push_transfer", out.clone()));
            return Err(format!(
                "ADB push to transfer path failed. Open the app once on the tablet, then try again. Target path: {INCOMING_TRANSFER_PATH}\n\nDetails: {out}"
            ));
        }
    }

    // Confirm file landed (no run-as required).
    let check = format!("ls -la {INCOMING_TRANSFER_PATH} 2>&1");
    let mut adb_check = Command::new("adb");
    adb_check.arg("-s").arg(device).args(["shell", &check]);
    if let Ok(out) = run_command_capture(adb_check) {
        steps.push(record_ok("verify_db_file", out));
    }

    let mut adb_start_cmd = Command::new("adb");
    adb_start_cmd
        .arg("-s")
        .arg(device)
        .args(["shell", "am", "start", "-n", ACTIVITY]);
    match run_command_capture(adb_start_cmd) {
        Ok(out) => steps.push(record_ok("start_app", out)),
        Err(out) => {
            steps.push(record_err("start_app", out.clone()));
            return Err(format!("Failed to restart app: {out}"));
        }
    }

    Ok(serde_json::json!({
        "device_id": device,
        "package": PACKAGE,
        "db_path": local_display,
        "method": "external_transfer",
        "remote_incoming": INCOMING_TRANSFER_PATH,
        "steps": steps
    }))
}
