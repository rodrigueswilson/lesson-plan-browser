#!/usr/bin/env python3
"""
Count lines of code for refactor tracking (section 0.5 and triage).

Hybrid: use cloc for SLOC when available; otherwise physical (non-empty) lines.
Run from project root: python tools/refactor/count_loc.py [--json | --markdown] [--no-cloc]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Single source for include/exclude (aligned with REFACTORING_PRIORITIES_AND_TOOLS 0.5)
INCLUDE_DIRS = ("backend", "frontend/src", "tools")
EXCLUDE_DIR_NAMES = (
    "archive",
    "node_modules",
    "__pycache__",
    ".tauri",
    ".venv",
    "venv",
    "build",
    "dist",
    ".git",
)
EXCLUDE_FILE_PATTERNS = (".min.js", ".min.css")
SOURCE_EXTENSIONS = (".py", ".ts", ".tsx", ".js", ".jsx")


def get_root() -> Path:
    """Project root (directory containing .git or backend/)."""
    cwd = Path.cwd().resolve()
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".git").exists():
            return parent
        if (parent / "backend").is_dir() and (parent / "tools").is_dir():
            return parent
    return cwd


def _should_skip_dir(path: Path, root: Path) -> bool:
    for part in path.relative_to(root).parts:
        if part in EXCLUDE_DIR_NAMES:
            return True
    return False


def _should_skip_file(path: Path) -> bool:
    name = path.name
    for pattern in EXCLUDE_FILE_PATTERNS:
        if pattern in name:
            return True
    return False


def run_cloc(root: Path, force_no_cloc: bool) -> dict | None:
    """Run cloc on include dirs; return per-file SLOC dict or None."""
    if force_no_cloc:
        return None
    include_paths = [str(root / d) for d in INCLUDE_DIRS if (root / d).exists()]
    if not include_paths:
        return None
    exclude = ",".join(EXCLUDE_DIR_NAMES)
    cmd = [
        "cloc",
        "--by-file",
        "--json",
        f"--exclude-dir={exclude}",
        *include_paths,
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        # cloc --by-file --json: either (1) top-level keys are file paths with {"code": N},
        # or (2) top-level keys are language names with {filepath: {"code": N}}.
        out = {}
        root_s = str(root).replace("\\", "/")
        for key, val in data.items():
            if key == "header" or not isinstance(val, dict):
                continue
            # Case (1): key is file path, val is {"code": N, ...}
            code = val.get("code")
            if code is not None and isinstance(code, (int, float)):
                p = key.replace("\\", "/")
                if p.startswith(root_s + "/"):
                    p = p[len(root_s) + 1 :]
                out[p] = int(code)
                continue
            # Case (2): key is language, val is {filepath: {"code": N}, ...}
            for path, stats in val.items():
                if not isinstance(stats, dict):
                    continue
                code = stats.get("code")
                if code is None or not isinstance(code, (int, float)):
                    continue
                p = path.replace("\\", "/")
                if p.startswith(root_s + "/"):
                    p = p[len(root_s) + 1 :]
                out[p] = int(code)
        return out if out else None
    except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired):
        return None


def count_physical(root: Path) -> dict[str, int]:
    """Count non-empty lines per file in include dirs (fallback)."""
    counts: dict[str, int] = {}
    for dir_name in INCLUDE_DIRS:
        dir_path = root / dir_name
        if not dir_path.is_dir():
            continue
        for path in dir_path.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in SOURCE_EXTENSIONS:
                continue
            try:
                rel = path.relative_to(root)
            except ValueError:
                continue
            if _should_skip_dir(path.parent, root) or _should_skip_file(path):
                continue
            key = str(rel).replace("\\", "/")
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            n = sum(1 for line in text.splitlines() if line.strip())
            counts[key] = n
    return counts


def by_directory(file_counts: dict[str, int]) -> dict[str, int]:
    """Aggregate file counts by top-level directory."""
    by_dir: dict[str, int] = {}
    for path, n in file_counts.items():
        top = path.split("/")[0] if "/" in path else path
        by_dir[top] = by_dir.get(top, 0) + n
    return by_dir


def sorted_files(file_counts: dict[str, int]) -> list[tuple[str, int]]:
    """List (path, count) sorted by count descending."""
    return sorted(file_counts.items(), key=lambda x: -x[1])


def output_text(
    file_counts: dict[str, int],
    mode: str,
    root: Path,
) -> None:
    """Print human-readable summary."""
    by_dir = by_directory(file_counts)
    total = sum(file_counts.values())
    print(f"Mode: {mode}")
    print(f"Root: {root}")
    print(f"Total: {total} lines")
    print("\nBy directory:")
    for d, n in sorted(by_dir.items(), key=lambda x: -x[1]):
        print(f"  {d}: {n}")
    print("\nTop files (by count):")
    for path, n in sorted_files(file_counts)[:40]:
        print(f"  {n:6}  {path}")


def output_json(
    file_counts: dict[str, int],
    mode: str,
    root: Path,
) -> None:
    """Print JSON: mode, root, by_directory, files (sorted)."""
    by_dir = by_directory(file_counts)
    files = sorted_files(file_counts)
    obj = {
        "mode": mode,
        "root": str(root),
        "total": sum(file_counts.values()),
        "by_directory": by_dir,
        "files": [{"path": p, "lines": n} for p, n in files],
    }
    print(json.dumps(obj, indent=2))


def output_markdown(
    file_counts: dict[str, int],
    mode: str,
) -> None:
    """Print Markdown table for pasting into section 0.5."""
    print(f"<!-- Mode: {mode} -->")
    print()
    print("| Lines | File |")
    print("| -----:| ------ |")
    for path, n in sorted_files(file_counts):
        print(f"| {n} | `{path}` |")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Count lines of code (hybrid: cloc or physical fallback). Run from project root."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON (by_directory, files).",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output Markdown table for section 0.5.",
    )
    parser.add_argument(
        "--no-cloc",
        action="store_true",
        help="Force physical-line fallback (do not use cloc).",
    )
    parser.add_argument(
        "--biggest",
        nargs="?",
        type=int,
        const=1,
        default=0,
        metavar="N",
        help="Print paths of the N biggest files (one per line). --biggest alone prints 1; --biggest 3 prints 3.",
    )
    parser.add_argument(
        "--over",
        type=int,
        default=0,
        metavar="N",
        help="Print paths of all files with more than N lines (one per line, sorted by count descending). Use for refactor targets (e.g. --over 400).",
    )
    args = parser.parse_args()

    root = get_root()
    file_counts = run_cloc(root, force_no_cloc=args.no_cloc)
    if file_counts is not None:
        mode = "SLOC (cloc)"
    else:
        file_counts = count_physical(root)
        mode = "physical lines (non-empty)"

    if args.over > 0:
        threshold = args.over
        files = sorted_files(file_counts)
        for path, count in files:
            if count > threshold:
                print(path)
        return 0

    if args.biggest > 0:
        n = args.biggest
        files = sorted_files(file_counts)
        for path, _ in files[:n]:
            print(path)
        return 0

    if args.json:
        output_json(file_counts, mode, root)
    elif args.markdown:
        output_markdown(file_counts, mode)
    else:
        output_text(file_counts, mode, root)

    return 0


if __name__ == "__main__":
    sys.exit(main())
