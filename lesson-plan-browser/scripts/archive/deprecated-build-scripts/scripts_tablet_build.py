#!/usr/bin/env python
"""
Tablet build & install automation for Lesson Plan Browser.

Usage examples:
  python scripts/tablet_build.py --mode release --install --seed-db
  python scripts/tablet_build.py --rollback-apk dist/apk/tablet-20250115-1430-release.apk
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Optional

IS_WINDOWS = os.name == "nt"
NPM_CMD = "npm.cmd" if IS_WINDOWS else "npm"
ADB_CMD = "adb.exe" if IS_WINDOWS else "adb"
GRADLE_CMD = "gradlew.bat" if IS_WINDOWS else "./gradlew"
REPO = pathlib.Path(__file__).resolve().parents[1]
FRONTEND = REPO / "frontend"
GEN_ANDROID = FRONTEND / "src-tauri" / "gen" / "android"
APK_OUTPUT = (
    GEN_ANDROID
    / "app"
    / "build"
    / "outputs"
    / "apk"
    / "arm64"
    / "debug"
    / "app-arm64-debug.apk"
)
ARCHIVE_DIR = REPO / "dist" / "apk"
DEFAULT_DB = REPO / "data" / "lesson_planner.db"
PACKAGE_NAME = "com.lessonplanner.browser"
MAIN_ACTIVITY = f"{PACKAGE_NAME}/.MainActivity"


def run(
    cmd: list[str],
    cwd: Optional[pathlib.Path] = None,
    env: Optional[dict[str, str]] = None,
) -> None:
    logging.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def build_vite(mode: str) -> None:
    env = os.environ.copy()
    env["TAURI_ENV_PLATFORM"] = "android"
    env["TAURI_ENV_TARGET_TRIPLE"] = "aarch64-linux-android"
    if mode == "release":
        env["NODE_ENV"] = "production"
        env["TAURI_DEBUG"] = "false"
    run([NPM_CMD, "run", "prepare:env"], cwd=FRONTEND, env=env)
    run([NPM_CMD, "run", "build:tauri"], cwd=FRONTEND, env=env)


def build_gradle() -> None:
    if IS_WINDOWS:
        cmd = ["cmd", "/c", GRADLE_CMD, "assembleArm64Debug"]
    else:
        gradle_path = GEN_ANDROID / "gradlew"
        gradle_path.chmod(gradle_path.stat().st_mode | 0o111)
        cmd = ["./gradlew", "assembleArm64Debug"]
    run(cmd, cwd=GEN_ANDROID)


def archive_apk(mode: str) -> pathlib.Path:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
    dst = ARCHIVE_DIR / f"tablet-{timestamp}-{mode}.apk"
    shutil.copy2(APK_OUTPUT, dst)
    logging.info("Archived APK to %s", dst)
    return dst


def install_apk(apk: pathlib.Path, device: str) -> None:
    run([ADB_CMD, "-s", device, "install", "-r", "-d", str(apk)])


def seed_database(device: str, db_path: pathlib.Path) -> None:
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    run(
        [
            ADB_CMD,
            "-s",
            device,
            "push",
            str(db_path),
            "/data/local/tmp/lesson_planner.db",
        ]
    )
    run(
        [
            ADB_CMD,
            "-s",
            device,
            "shell",
            "run-as",
            PACKAGE_NAME,
            "mkdir",
            "-p",
            "databases",
        ]
    )
    run(
        [
            ADB_CMD,
            "-s",
            device,
            "shell",
            "run-as",
            PACKAGE_NAME,
            "cp",
            "/data/local/tmp/lesson_planner.db",
            "databases/lesson_planner.db",
        ]
    )
    run([ADB_CMD, "-s", device, "shell", "rm", "/data/local/tmp/lesson_planner.db"])


def restart_app(device: str) -> None:
    run([ADB_CMD, "-s", device, "shell", "am", "force-stop", PACKAGE_NAME])
    run([ADB_CMD, "-s", device, "shell", "am", "start", "-n", MAIN_ACTIVITY])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build, archive, and install tablet APKs."
    )
    parser.add_argument("--mode", choices=["debug", "release"], default="debug")
    parser.add_argument("--device", default="R52Y90L71YP", help="ADB device ID")
    parser.add_argument(
        "--install", action="store_true", help="Install APK on device after build"
    )
    parser.add_argument(
        "--seed-db", action="store_true", help="Push lesson_planner.db to the tablet"
    )
    parser.add_argument(
        "--db-path", default=str(DEFAULT_DB), help="Path to lesson_planner.db"
    )
    parser.add_argument(
        "--rollback-apk", help="Skip build and install the specified APK archive"
    )
    parser.add_argument("--log-file", help="Optional log file path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    log_handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if args.log_file:
        pathlib.Path(args.log_file).parent.mkdir(parents=True, exist_ok=True)
        log_handlers.append(logging.FileHandler(args.log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=log_handlers,
    )

    if args.rollback_apk:
        apk = pathlib.Path(args.rollback_apk)
        if not apk.exists():
            logging.error("Rollback APK not found: %s", apk)
            sys.exit(1)
        install_apk(apk, args.device)
        restart_app(args.device)
        logging.info("Rollback complete.")
        return

    try:
        build_vite(args.mode)
        build_gradle()
        apk_path = archive_apk(args.mode)

        if args.install:
            install_apk(apk_path, args.device)
            if args.seed_db:
                seed_database(args.device, pathlib.Path(args.db_path))
            restart_app(args.device)
    except subprocess.CalledProcessError as exc:
        logging.error("Command failed with exit code %s: %s", exc.returncode, exc.cmd)
        sys.exit(exc.returncode)
    except Exception as exc:  # noqa: BLE001 - we want one catch-all for logging
        logging.error("Build failed: %s", exc)
        sys.exit(1)
    else:
        logging.info("Build complete. APK archived at %s", apk_path)


if __name__ == "__main__":
    main()
