## Android Build Blocker – 2025-11-29

### Summary
Attempts to generate, install, and seed the tablet APK consistently fail during the Gradle phase (`tauri android android-studio-script --target aarch64`). The Tauri CLI panics with:

```
failed to build WebSocket client:
  Io(Os { code: 10061, kind: ConnectionRefused, message: "No connection could be made because the target machine actively refused it." })
Execution failed for task ':app:rustBuildArm64Debug'.
> A problem occurred starting process 'command 'npm.bat''
```

This prevents `gradlew assembleArm64Debug` from finishing, so the APK never gets produced for installation/DB seeding.

### What We Tried

1. **Configured Tauri env vars**
   - Set `TAURI_CLI_NO_DEV_SERVER=1`, `TAURI_CLI_GENERATE_DEVSERVER_CONFIG=0`, and later the new `TAURI_CLI_NO_DEV_SERVER_WAIT=true` via `set_tauri_env.py`.
   - Restarted shells to ensure the env vars took effect.

2. **Manual dev server attempts**
   - Launched `npm run tauri dev` (both desktop and Android env) in dedicated PowerShell windows, verified `localhost:1420` was reachable, and retried the build while the server was running.
   - Killed stale Node/Tauri processes using `netstat/Get-Process` to free port 1420.

3. **CLI upgrades**
   - Updated project-local and global `@tauri-apps/cli` to the latest version (2.9.4 → latest).
   - Re-ran the entire build script after the upgrade.

4. **Manual build steps**
   - Ran `npm run prepare:env`, `npm run build:tauri`, then `cd src-tauri\gen\android && .\gradlew.bat assembleArm64Debug` to bypass the Python wrapper. The same panic occurs.

5. **Configuration tweaks**
   - Added `src-tauri/tauri.android.conf.json` with `"devUrl": "tauri://localhost"` to eliminate any dependency on the live dev server.

### Current State

Despite all changes, the Tauri CLI still tries to open a WebSocket during `tauri android android-studio-script`, fails to connect (even when a dev server is running), and terminates the Gradle build with the same error. No APK is produced.

### Next Steps for Tomorrow

1. **Capture full stack trace:** run the build with `RUST_BACKTRACE=1` to produce a detailed crash log.
2. **Report upstream:** file an issue with Tauri (include stack trace, CLI version, env vars set, and reproduction steps). This appears to be a regression where the CLI ignores `NO_DEV_SERVER` flags on Windows.
3. **Explore alternate build flows:** if a Tauri fix is delayed, investigate building the Rust/Android project manually without the CLI wrapper or using an older CLI version known to work.

Until the CLI bug is addressed, the tablet APK cannot be generated via the current workflow.

