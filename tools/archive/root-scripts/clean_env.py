#!/usr/bin/env python3
"""
Clean cache and kill Python processes script.
Clears Vite cache, browser build caches, error logs, and terminates all Python processes.

Note: Browser in-memory cache (React state) cannot be cleared by this script.
      Restart the browser application to clear in-memory lesson plan cache.
"""

import os
import platform
import shutil
import sys
from pathlib import Path

# Determine if we're on Windows
IS_WINDOWS = platform.system() == "Windows"


def clean_vite_cache():
    """Remove Vite cache directories."""
    vite_caches = [
        Path("frontend/node_modules/.vite"),
        Path("lesson-plan-browser/frontend/node_modules/.vite"),
    ]

    all_cleared = True
    for vite_cache in vite_caches:
        if vite_cache.exists():
            try:
                shutil.rmtree(vite_cache)
                print(f"[OK] Cleared Vite cache: {vite_cache}")
            except Exception as e:
                print(f"[ERROR] Failed to clear Vite cache {vite_cache}: {e}")
                all_cleared = False
        else:
            print(f"[INFO] Vite cache not found: {vite_cache}")

    return all_cleared


def clean_log_files():
    """Remove frontend log files."""
    log_files = [
        "frontend/frontend_error.log",
        "frontend/frontend_server.log",
        "lesson-plan-browser/frontend/frontend_error.log",
        "lesson-plan-browser/frontend/frontend_server.log",
    ]

    cleaned = 0
    for log_path in log_files:
        log_file = Path(log_path)
        if log_file.exists():
            try:
                log_file.unlink()
                print(f"[OK] Removed log file: {log_path}")
                cleaned += 1
            except Exception as e:
                print(f"[ERROR] Failed to remove {log_path}: {e}")
        else:
            print(f"[INFO] Log file not found: {log_path}")

    return cleaned > 0 or all(not Path(p).exists() for p in log_files)


def clean_browser_caches():
    """Remove browser build caches and dist directories.

    Note: Tauri target directory is NOT cleared as it contains compiled Rust code
    that takes significant time to rebuild. Clear it manually if needed.
    """
    browser_caches = [
        # Build output directories (can be regenerated quickly)
        Path("lesson-plan-browser/frontend/dist"),
        Path("frontend/dist"),
        # Note: Tauri target/ directory is NOT cleared (takes too long to rebuild)
        # Uncomment the line below if you really need to clear it:
        # Path("lesson-plan-browser/frontend/src-tauri/target"),
    ]

    all_cleared = True
    for cache_path in browser_caches:
        if cache_path.exists():
            try:
                if cache_path.is_dir():
                    shutil.rmtree(cache_path)
                    print(f"[OK] Cleared browser cache: {cache_path}")
                else:
                    cache_path.unlink()
                    print(f"[OK] Removed cache file: {cache_path}")
            except Exception as e:
                print(f"[ERROR] Failed to clear browser cache {cache_path}: {e}")
                all_cleared = False
        else:
            print(f"[INFO] Browser cache not found: {cache_path}")

    return all_cleared


def kill_python_processes():
    """Kill all Python processes."""
    if IS_WINDOWS:
        return kill_python_processes_windows()
    else:
        return kill_python_processes_unix()


def kill_python_processes_windows():
    """Kill Python processes on Windows."""
    try:
        import os
        import subprocess

        # Get current process ID to exclude it
        current_pid = str(os.getpid())

        # Get all Python processes
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

        # Also check for pythonw.exe
        result_w = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq pythonw.exe", "/FO", "CSV"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

        killed = 0

        # Parse and kill python.exe processes
        lines = result.stdout.strip().split("\n")
        if len(lines) > 1:  # More than just the header
            for line in lines[1:]:  # Skip header
                if line.strip() and "python.exe" in line.lower():
                    parts = line.split('","')
                    if len(parts) >= 2:
                        pid = parts[1].strip('"')
                        # Don't kill ourselves
                        if pid == current_pid:
                            continue
                        try:
                            subprocess.run(
                                ["taskkill", "/F", "/PID", pid],
                                capture_output=True,
                                check=False,
                            )
                            print(f"[OK] Killed Python process (PID: {pid})")
                            killed += 1
                        except Exception as e:
                            print(f"[ERROR] Failed to kill process {pid}: {e}")

        # Parse and kill pythonw.exe processes
        lines_w = result_w.stdout.strip().split("\n")
        if len(lines_w) > 1:  # More than just the header
            for line in lines_w[1:]:  # Skip header
                if line.strip() and "pythonw.exe" in line.lower():
                    parts = line.split('","')
                    if len(parts) >= 2:
                        pid = parts[1].strip('"')
                        # Don't kill ourselves
                        if pid == current_pid:
                            continue
                        try:
                            subprocess.run(
                                ["taskkill", "/F", "/PID", pid],
                                capture_output=True,
                                check=False,
                            )
                            print(f"[OK] Killed Pythonw process (PID: {pid})")
                            killed += 1
                        except Exception as e:
                            print(f"[ERROR] Failed to kill process {pid}: {e}")

        if killed == 0:
            print("[INFO] No Python processes found (excluding this script)")
        else:
            print(f"[OK] Killed {killed} Python process(es)")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to kill Python processes: {e}")
        return False


def kill_python_processes_unix():
    """Kill Python processes on Unix-like systems."""
    try:
        import subprocess

        # Find all Python processes
        result = subprocess.run(
            ["pgrep", "-f", "python"], capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            print("[INFO] No Python processes found")
            return True

        pids = result.stdout.strip().split("\n")
        killed = 0

        for pid in pids:
            if pid.strip():
                try:
                    subprocess.run(
                        ["kill", "-9", pid.strip()], capture_output=True, check=False
                    )
                    print(f"[OK] Killed Python process (PID: {pid.strip()})")
                    killed += 1
                except Exception as e:
                    print(f"[ERROR] Failed to kill process {pid}: {e}")

        if killed > 0:
            print(f"[OK] Killed {killed} Python process(es)")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to kill Python processes: {e}")
        return False


def check_remaining_python_processes():
    """Check if there are any Python processes still running."""
    if IS_WINDOWS:
        return check_remaining_python_processes_windows()
    else:
        return check_remaining_python_processes_unix()


def check_remaining_python_processes_windows():
    """Check for remaining Python processes on Windows."""
    try:
        import os
        import subprocess
        import time

        # Get current process ID to exclude it
        current_pid = str(os.getpid())

        # Wait a moment for processes to terminate
        time.sleep(1)

        # Check for python.exe
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
            capture_output=True,
            text=True,
            check=False,
        )

        # Check for pythonw.exe
        result_w = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq pythonw.exe", "/FO", "CSV"],
            capture_output=True,
            text=True,
            check=False,
        )

        remaining_pids = []

        # Parse python.exe processes
        lines = result.stdout.strip().split("\n")
        for line in lines[1:]:  # Skip header
            if "python.exe" in line.lower():
                parts = line.split('","')
                if len(parts) >= 2:
                    pid = parts[1].strip('"')
                    # Exclude current process
                    if pid != current_pid:
                        remaining_pids.append(pid)

        # Parse pythonw.exe processes
        lines_w = result_w.stdout.strip().split("\n")
        for line in lines_w[1:]:  # Skip header
            if "pythonw.exe" in line.lower():
                parts = line.split('","')
                if len(parts) >= 2:
                    pid = parts[1].strip('"')
                    # Exclude current process
                    if pid != current_pid:
                        remaining_pids.append(pid)

        if remaining_pids:
            print(
                f"[FAILED] {len(remaining_pids)} Python process(es) are still running:"
            )
            for pid in remaining_pids:
                print(f"  - PID: {pid}")
            print("[WARNING] All Python processes were NOT stopped successfully")
            return False
        else:
            print("[SUCCESS] All Python processes have been stopped")
            print("[OK] Verified: No Python processes are running")
            return True

    except Exception as e:
        print(f"[ERROR] Failed to check for remaining Python processes: {e}")
        return False


def check_remaining_python_processes_unix():
    """Check for remaining Python processes on Unix-like systems."""
    try:
        import os
        import subprocess
        import time

        # Get current process ID to exclude it
        current_pid = str(os.getpid())

        # Wait a moment for processes to terminate
        time.sleep(1)

        # Find all Python processes
        result = subprocess.run(
            ["pgrep", "-f", "python"], capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            print("[OK] Verified: No Python processes are running")
            return True

        pids = [
            pid.strip()
            for pid in result.stdout.strip().split("\n")
            if pid.strip() and pid.strip() != current_pid
        ]

        if pids:
            print(f"[FAILED] {len(pids)} Python process(es) are still running:")
            for pid in pids:
                print(f"  - PID: {pid}")
            print("[WARNING] All Python processes were NOT stopped successfully")
            return False
        else:
            print("[SUCCESS] All Python processes have been stopped")
            print("[OK] Verified: No Python processes are running")
            return True

    except Exception as e:
        print(f"[ERROR] Failed to check for remaining Python processes: {e}")
        return False


def main():
    """Main function."""
    print("=" * 50)
    print("Cache Cleaner and Python Process Killer")
    print("=" * 50)
    print()

    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}")
    print()

    # Clean caches
    print("Cleaning caches...")
    print("-" * 50)
    vite_ok = clean_vite_cache()
    logs_ok = clean_log_files()
    browser_ok = clean_browser_caches()
    print()

    # Kill Python processes
    print("Killing Python processes...")
    print("-" * 50)
    sys.stdout.flush()
    python_ok = kill_python_processes()
    sys.stdout.flush()
    print()

    # Verify no Python processes remain
    print("Verifying Python processes are terminated...")
    print("-" * 50)
    verify_ok = check_remaining_python_processes()
    print()

    # Summary
    print("=" * 50)
    print("Summary:")
    print("-" * 50)
    print(f"Vite cache: {'[OK] Cleared' if vite_ok else '[ERROR] Failed'}")
    print(f"Log files: {'[OK] Cleared' if logs_ok else '[ERROR] Failed'}")
    print(f"Browser caches: {'[OK] Cleared' if browser_ok else '[ERROR] Failed'}")
    print(f"Python processes: {'[OK] Killed' if python_ok else '[ERROR] Failed'}")
    print(
        f"Verification: {'[OK] All processes stopped' if verify_ok else '[FAILED] Processes still running'}"
    )
    print("=" * 50)
    print()
    print("NOTE: Browser in-memory cache (React state) will be cleared")
    print("      when you restart the browser application.")
    print()

    # Final status
    if verify_ok:
        print(
            "[SUCCESS] FINAL STATUS: All Python processes have been successfully stopped"
        )
    else:
        print("[FAILED] FINAL STATUS: Some Python processes are still running")
    print()

    # Exit with appropriate code
    if all([vite_ok, logs_ok, browser_ok, python_ok, verify_ok]):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
