//! ADB push to tablet via `/data/local/tmp` + `run-as cp` protocol.
//!
//! This avoids Android 11+ scoped-storage / FUSE restrictions on
//! `/sdcard/Android/data/<own-pkg>/...` files written by the `shell` UID,
//! which on Android 13+ (especially Samsung) become invisible to the
//! app's process even via Java APIs. The tablet-side Rust import code
//! (`db_commands.rs`) already lists `/data/user/0/com.lessonplanner.browser/files/transfer/lesson_planner.db`
//! as a transfer candidate and applies it on the next `init_database()` call.
//!
//! Requires the installed APK to be debuggable (so `run-as` is allowed).
//! If a non-debuggable variant is detected, the flow auto-recovers by
//! uninstalling and reinstalling the latest debug APK found on disk.

use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::SystemTime;

const PACKAGE: &str = "com.lessonplanner.browser";
const ACTIVITY: &str = "com.lessonplanner.browser/.MainActivity";

/// Path inside the app's internal data dir (relative to `run-as` cwd).
/// Matches `INCOMING_TRANSFER_INTERNAL_PATH` in the tablet crate's
/// `db_commands.rs` (i.e. `/data/user/0/<pkg>/files/transfer/lesson_planner.db`).
const INTERNAL_TRANSFER_REL: &str = "files/transfer/lesson_planner.db";

fn run_command_capture(mut cmd: Command) -> Result<String, String> {
    let output = cmd.output().map_err(|e| e.to_string())?;
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    if output.status.success() {
        return Ok(format!("{}{}", stdout, stderr).trim().to_string());
    }
    Err(format!("{}{}", stdout, stderr).trim().to_string())
}

fn adb_shell(device: &str, script: &str) -> Result<String, String> {
    let mut cmd = Command::new("adb");
    cmd.arg("-s").arg(device).args(["shell", script]);
    run_command_capture(cmd)
}

fn random_tmp_name() -> String {
    let now_ms = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .map(|d| d.as_millis())
        .unwrap_or(0);
    let pid = std::process::id();
    format!("lp_xfer_{now_ms}_{pid}.db")
}

/// Returns true iff `run-as <pkg>` is permitted, i.e. the installed APK
/// has the `android:debuggable` flag set.
fn is_debuggable(device: &str) -> bool {
    let mut cmd = Command::new("adb");
    cmd.arg("-s")
        .arg(device)
        .args(["shell", &format!("run-as {} true", PACKAGE)]);
    cmd.output().map(|o| o.status.success()).unwrap_or(false)
}

fn walk_apks(dir: &Path, out: &mut Vec<PathBuf>) {
    let Ok(entries) = std::fs::read_dir(dir) else {
        return;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            walk_apks(&path, out);
        } else if path
            .extension()
            .and_then(|s| s.to_str())
            .map(|s| s.eq_ignore_ascii_case("apk"))
            .unwrap_or(false)
        {
            out.push(path);
        }
    }
}

fn find_latest_debug_apk() -> Option<PathBuf> {
    let root = crate::find_project_root_with_script("build-apk.ps1")
        .or_else(|_| std::env::current_dir().map_err(|e| e.to_string()))
        .unwrap_or_else(|_| PathBuf::from("."));

    let dirs = [
        root.join("lesson-plan-browser")
            .join("frontend")
            .join("src-tauri")
            .join("gen")
            .join("android"),
        root.join("lesson-plan-browser").join("dist").join("apk"),
    ];

    let mut all: Vec<PathBuf> = Vec::new();
    for dir in &dirs {
        walk_apks(dir, &mut all);
    }

    all.into_iter()
        .filter(|p| {
            p.file_name()
                .and_then(|s| s.to_str())
                .map(|s| {
                    let lower = s.to_ascii_lowercase();
                    lower.contains("-debug.") || lower.contains("debug-")
                })
                .unwrap_or(false)
        })
        .filter_map(|p| {
            std::fs::metadata(&p)
                .ok()
                .and_then(|m| m.modified().ok())
                .map(|t| (t, p))
        })
        .max_by_key(|(t, _)| *t)
        .map(|(_, p)| p)
}

fn auto_install_debug_apk(
    device: &str,
    steps: &mut Vec<serde_json::Value>,
    record_ok: &dyn Fn(&str, String) -> serde_json::Value,
    record_err: &dyn Fn(&str, String) -> serde_json::Value,
) -> Result<(), String> {
    let apk = find_latest_debug_apk().ok_or_else(|| {
        "Installed APK is not debuggable and no debug APK was found on disk. \
         Build a debug APK (e.g. `.\\scripts\\build-android-offline.ps1 -Target arm64`) \
         then retry the push."
            .to_string()
    })?;

    let mut uninstall = Command::new("adb");
    uninstall
        .arg("-s")
        .arg(device)
        .args(["uninstall", PACKAGE]);
    match run_command_capture(uninstall) {
        Ok(out) => steps.push(record_ok("auto_uninstall", out)),
        Err(out) => steps.push(record_err("auto_uninstall", out)),
    }

    let apk_str = apk.to_string_lossy().to_string();
    let mut install = Command::new("adb");
    install
        .arg("-s")
        .arg(device)
        .args(["install", "-r"])
        .arg(&apk_str);
    match run_command_capture(install) {
        Ok(out) => {
            steps.push(record_ok(
                "auto_install_debug_apk",
                format!("{}\nAPK: {}", out, apk_str),
            ));
            Ok(())
        }
        Err(out) => {
            steps.push(record_err("auto_install_debug_apk", out.clone()));
            Err(format!(
                "Auto-recovery failed: could not install debug APK from {apk_str}.\n\nDetails: {out}"
            ))
        }
    }
}

/// Push a local `lesson_planner.db` to the tablet, restart the app, and
/// import on the next `init_database`.
pub fn push_tablet_database(device: &str, local_path: &Path) -> Result<serde_json::Value, String> {
    let record_ok = |name: &str, output: String| -> serde_json::Value {
        serde_json::json!({ "step": name, "ok": true, "output": output })
    };
    let record_err = |name: &str, output: String| -> serde_json::Value {
        serde_json::json!({ "step": name, "ok": false, "output": output })
    };

    let local_display = local_path.to_string_lossy().to_string();
    let local_size = std::fs::metadata(local_path).map(|m| m.len()).unwrap_or(0);
    let mut steps: Vec<serde_json::Value> = Vec::new();

    let mut force_stop = Command::new("adb");
    force_stop
        .arg("-s")
        .arg(device)
        .args(["shell", "am", "force-stop", PACKAGE]);
    match run_command_capture(force_stop) {
        Ok(out) => steps.push(record_ok("force_stop", out)),
        Err(out) => steps.push(record_err("force_stop", out)),
    }

    if !is_debuggable(device) {
        steps.push(record_ok(
            "debuggable_probe",
            "non-debuggable APK detected; attempting auto-recovery".to_string(),
        ));
        auto_install_debug_apk(device, &mut steps, &record_ok, &record_err)?;
        if !is_debuggable(device) {
            return Err(
                "Auto-recovery installed an APK but run-as is still rejected. \
                 The APK on disk may be a release/non-debuggable variant. \
                 Build a debug APK and retry."
                    .to_string(),
            );
        }
        let mut restop = Command::new("adb");
        restop
            .arg("-s")
            .arg(device)
            .args(["shell", "am", "force-stop", PACKAGE]);
        let _ = run_command_capture(restop);
    } else {
        steps.push(record_ok("debuggable_probe", "ok".to_string()));
    }

    let tmp_name = random_tmp_name();
    let tmp_remote = format!("/data/local/tmp/{}", tmp_name);
    let mut adb_push_cmd = Command::new("adb");
    adb_push_cmd
        .arg("-s")
        .arg(device)
        .arg("push")
        .arg(local_path)
        .arg(&tmp_remote);
    match run_command_capture(adb_push_cmd) {
        Ok(out) => steps.push(record_ok("adb_push_tmp", out)),
        Err(out) => {
            steps.push(record_err("adb_push_tmp", out.clone()));
            return Err(format!(
                "ADB push to {tmp_remote} failed.\n\nDetails: {out}"
            ));
        }
    }

    let stage_script = format!(
        "run-as {pkg} sh -c 'mkdir -p files/transfer && cp {tmp} {dest} && chmod 600 {dest}'",
        pkg = PACKAGE,
        tmp = tmp_remote,
        dest = INTERNAL_TRANSFER_REL,
    );
    match adb_shell(device, &stage_script) {
        Ok(out) => steps.push(record_ok("run_as_stage", out)),
        Err(out) => {
            steps.push(record_err("run_as_stage", out.clone()));
            let _ = adb_shell(device, &format!("rm -f {tmp_remote}"));
            return Err(format!(
                "run-as stage into {INTERNAL_TRANSFER_REL} failed.\n\nDetails: {out}"
            ));
        }
    }

    let _ = adb_shell(device, &format!("rm -f {tmp_remote}"));
    steps.push(record_ok("cleanup_tmp", tmp_remote.clone()));

    let verify_script = format!(
        "run-as {pkg} stat -c '%n %s' {dest} 2>&1 || run-as {pkg} ls -la {dest} 2>&1",
        pkg = PACKAGE,
        dest = INTERNAL_TRANSFER_REL,
    );
    match adb_shell(device, &verify_script) {
        Ok(out) => steps.push(record_ok(
            "verify_internal_target",
            format!("local_size={local_size} {out}"),
        )),
        Err(out) => steps.push(record_err("verify_internal_target", out)),
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
        "method": "run_as_internal",
        "remote_target": format!("/data/data/{PACKAGE}/{INTERNAL_TRANSFER_REL}"),
        "local_size": local_size,
        "steps": steps,
    }))
}
