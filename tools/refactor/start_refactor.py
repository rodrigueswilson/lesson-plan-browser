#!/usr/bin/env python3
"""
Start a single-file refactor: create branch from master and write a minimal plan.

Usage (from project root):
  python tools/refactor/start_refactor.py <file_path> [<file_path> ...]
  python tools/refactor/start_refactor.py --list files_to_refactor.txt
  python tools/refactor/start_refactor.py --dry-run <file_path>

Options:
  --list FILE     Read paths from file (one per line). Lines starting with # are ignored.
                  Lines containing "(done" are treated as completed and skipped. The first
                  remaining path is used (creates branch + plan); or use --batch to process all.
  --batch         With --list: process every path (create branch, write plan, print next steps).
                  Without --batch, only the first path in --list is used.
  --no-branch     Do not create or checkout branch; only write plan and print LOC.
  --dry-run       Print what would be done; do not create branch or write files.
  --plan-dir DIR  Directory for plan files (default: docs/refactor/plans).
  --force        Overwrite existing plan file (default: skip write if plan exists).
  --update-plan  Refresh existing plan (LOC and analysis); write even if plan exists.

Run from project root. Paths are relative to project root (e.g. tools/docx_renderer/renderer.py).
If plan already exists, script skips writing unless --force or --update-plan is given.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# Reuse count_loc's root and include dirs
INCLUDE_DIRS = ("backend", "frontend/src", "tools")

# Path prefix (relative to root) -> test command for plan. First match wins.
PATH_TO_TEST_COMMAND = [
    ("tools/docx_renderer", "pytest tests/ -q -k \"docx or renderer\""),
    ("tools/docx_parser", "pytest tests/ -q -k \"docx or parser\""),
    ("tools/batch_processor", "pytest tests/ -q -k \"batch or combine or slot or week\""),
    ("backend/routers", "pytest tests/test_api.py tests/test_database_crud.py -q"),
    ("backend/llm", "pytest tests/ -q -k \"llm\""),
    ("backend/database", "pytest tests/test_database_crud.py -q"),
    ("backend/", "pytest tests/test_api.py tests/test_database_crud.py -q"),
    ("tools/", "pytest tests/ -q"),
]


def get_root() -> Path:
    """Project root (directory containing .git or backend/)."""
    cwd = Path.cwd().resolve()
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".git").exists():
            return parent
        if (parent / "backend").is_dir() and (parent / "tools").is_dir():
            return parent
    return cwd


def count_nonempty_lines(path: Path) -> int:
    """Count non-empty lines in file (same metric as count_loc physical)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return sum(1 for line in text.splitlines() if line.strip())
    except OSError:
        return 0


def path_to_branch_name(rel_path: str) -> str:
    """Turn relative file path into a short branch suffix, e.g. refactor/slim-docx-renderer."""
    # Normalize: backslash to slash, no leading slash
    rel = rel_path.replace("\\", "/").lstrip("/")
    parts = rel.replace(".py", "").replace(".ts", "").replace(".tsx", "").split("/")
    if len(parts) >= 2:
        # e.g. tools/docx_renderer/renderer -> docx-renderer (underscores to hyphens)
        suffix = "-".join(parts[-2:]).replace("_", "-")
    else:
        suffix = (parts[-1] if parts else "file").replace("_", "-")
    # Safe branch name: lowercase, alphanumeric and hyphen
    suffix = re.sub(r"[^a-zA-Z0-9-]", "-", suffix).lower()
    suffix = re.sub(r"-+", "-", suffix).strip("-")
    return f"refactor/slim-{suffix}" if suffix else "refactor/slim-file"


def path_to_plan_stem(rel_path: str) -> str:
    """Turn relative file path into plan filename stem, e.g. slim_docx_renderer."""
    rel = rel_path.replace("\\", "/").lstrip("/")
    stem = rel.replace(".py", "").replace(".ts", "").replace(".tsx", "")
    stem = re.sub(r"[^a-zA-Z0-9/_-]", "_", stem).replace("/", "_")
    return f"slim_{stem}"


def get_test_command(rel_path_str: str) -> str:
    """Return suggested test command for the given path (first matching prefix)."""
    norm = rel_path_str.replace("\\", "/")
    for prefix, cmd in PATH_TO_TEST_COMMAND:
        if norm.startswith(prefix) or norm == prefix.rstrip("/"):
            return cmd
    return "pytest tests/ -q"


def plan_template(
    file_path: str,
    loc: int,
    branch: str,
    plan_path: Path,
    public_api_lines: list[str] | None = None,
    extraction_bullets: list[str] | None = None,
    test_command: str | None = None,
) -> str:
    """Build plan content. Uses analysis when provided; otherwise placeholders."""
    if public_api_lines is None:
        public_api_lines = [
            "- List any module-level exports, class names, or function signatures that callers depend on.",
            "- Do not change these; only move implementation into new modules.",
        ]
    if extraction_bullets is None:
        extraction_bullets = [
            "1. (Identify logical units: e.g. \"X + Y helpers\" -> new module `.../x_y.py`; keep facade in original.)",
            "2. ...",
            "3. ...",
        ]
    if test_command is None:
        test_command = "pytest tests/ -q"

    public_api_section = "\n".join(public_api_lines)
    extractions_section = "\n".join(extraction_bullets)

    return f"""# Refactor: {file_path}

## Current state

- **File:** `{file_path}` ({loc} non-empty lines, same metric as count_loc physical)
- **Branch:** `{branch}` (create from `master`)

## Public API to preserve

{public_api_section}

## Suggested extractions

{extractions_section}

## Steps (one commit per extraction)

1. Create branch from master: `git checkout master && git pull && git checkout -b {branch}`
2. Extract first unit into new module; update imports; run tests; commit.
3. Repeat for each extraction.
4. Update REFACTORING_PRIORITIES_AND_TOOLS.md (0.1, 1.4, 0.5 LOC) and merge to master.

## Test command

```bash
{test_command}
```

**CI parity** (SQLite GitHub Actions; pytest marker `unit` \u2014 see [CONTRIBUTING](../../CONTRIBUTING.md)):

```bash
python -m pytest tests/ -m unit -q
```

## References

- [GIT_DURING_REFACTORING.md](GIT_DURING_REFACTORING.md)
- [REFACTORING_TOOLS_FOR_CURSOR.md](REFACTORING_TOOLS_FOR_CURSOR.md)
"""


def ensure_master_and_branch(root: Path, branch: str, dry_run: bool) -> bool:
    """Checkout master, pull, create branch. Return True on success."""
    if dry_run:
        print(f"[dry-run] would: git checkout master && git pull && git checkout -b {branch}")
        return True
    for cmd in [
        ["git", "checkout", "master"],
        ["git", "pull", "origin", "master"],
        ["git", "checkout", "-b", branch],
    ]:
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr or r.stdout, file=sys.stderr)
            return False
    return True


def process_one(
    root: Path,
    file_path: str,
    plan_dir: Path,
    no_branch: bool,
    dry_run: bool,
    force: bool = False,
    update_plan: bool = False,
) -> bool:
    """Create branch (unless no_branch), write plan; return True on success."""
    full = root / file_path.replace("/", os.sep)
    if not full.is_file():
        print(f"Error: not a file: {full}", file=sys.stderr)
        return False

    # Must be under backend, frontend/src, or tools
    try:
        rel = full.relative_to(root)
        rel_str = str(rel).replace("\\", "/")
    except ValueError:
        print(f"Error: {file_path} is not under project root", file=sys.stderr)
        return False
    if not any(rel_str.startswith(d + "/") or rel_str == d for d in INCLUDE_DIRS):
        print(f"Error: {file_path} must be under one of {INCLUDE_DIRS}", file=sys.stderr)
        return False

    loc = count_nonempty_lines(full)
    branch = path_to_branch_name(rel_str)
    plan_stem = path_to_plan_stem(rel_str)
    plan_path = plan_dir / f"{plan_stem}.md"

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from tools.refactor.plan_analyzer import analyze_for_plan
    analysis = analyze_for_plan(full, rel_str)
    test_cmd = get_test_command(rel_str)
    content = plan_template(
        rel_str,
        loc,
        branch,
        plan_path,
        public_api_lines=analysis.public_api_lines or None,
        extraction_bullets=analysis.extraction_bullets or None,
        test_command=test_cmd,
    )

    if not no_branch and not dry_run:
        if not ensure_master_and_branch(root, branch, dry_run=False):
            return False
    elif not no_branch and dry_run:
        ensure_master_and_branch(root, branch, dry_run=True)

    if dry_run:
        print(f"[dry-run] would write plan: {plan_path}")
        print(content[:600] + "...")
        return True

    plan_exists = plan_path.is_file()
    if plan_exists and not force and not update_plan:
        print(f"Plan already exists: {plan_path}")
        print("Use --force to overwrite or --update-plan to refresh LOC and analysis.")
        print(f"File: {rel_str} ({loc} lines)  Branch: {branch}")
        return True

    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(content, encoding="utf-8")

    print(f"File: {rel_str} ({loc} lines)")
    print(f"Branch: {branch}")
    print(f"Plan: {plan_path}")
    if analysis.public_api_lines or analysis.extraction_bullets:
        print("(Public API and suggested extractions pre-filled from AST.)")
    print("Next: implement extractions (see plan), run tests, commit per step, then merge to master.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Start a single-file refactor: create branch and write plan.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="File path(s) relative to project root (e.g. tools/docx_renderer/renderer.py)",
    )
    parser.add_argument(
        "--list",
        metavar="FILE",
        help="Read paths from file (one per line).",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="With --list: process every path (create branch + plan for first; others get plan only, no branch).",
    )
    parser.add_argument(
        "--no-branch",
        action="store_true",
        help="Do not create branch; only write plan and print LOC.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done; do not create branch or write files.",
    )
    parser.add_argument(
        "--plan-dir",
        default="docs/refactor/plans",
        metavar="DIR",
        help="Directory for plan files (default: docs/refactor/plans).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing plan file.",
    )
    parser.add_argument(
        "--update-plan",
        action="store_true",
        help="Refresh existing plan (LOC and analysis); write even if plan exists.",
    )
    args = parser.parse_args()

    root = get_root()
    plan_dir = root / args.plan_dir.replace("/", os.sep)

    paths = list(args.paths)
    if args.list:
        list_path = root / args.list.replace("/", os.sep)
        if not list_path.is_file():
            print(f"Error: list file not found: {list_path}", file=sys.stderr)
            return 1
        with open(list_path, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                if "(done" in s.lower():
                    continue
                path = s.split(" (")[0].split("#")[0].strip()
                if path:
                    paths.append(path)

    if not paths:
        if args.list:
            print("No remaining refactor targets in list (all marked done or commented).", file=sys.stderr)
            print("Edit the list file to add paths or remove '(done...)' to re-queue a file.", file=sys.stderr)
            return 1
        parser.print_help()
        return 0

    if args.batch and len(paths) > 1:
        # Batch: write a plan for each; create branch only for the first
        for i, p in enumerate(paths):
            if i > 0 and not args.no_branch and not args.dry_run:
                subprocess.run(["git", "checkout", "master"], cwd=root, capture_output=True)
            ok = process_one(
                root, p, plan_dir,
                no_branch=(i > 0), dry_run=args.dry_run,
                force=args.force, update_plan=args.update_plan,
            )
            if not ok:
                return 1
        return 0

    # Single or first path only
    ok = process_one(
        root, paths[0], plan_dir,
        args.no_branch, args.dry_run,
        force=args.force, update_plan=args.update_plan,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
