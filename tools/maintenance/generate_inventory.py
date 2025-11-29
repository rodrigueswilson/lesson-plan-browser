"""
Lightweight inventory generator for decluttering process.

Emits raw counts and file paths for each category of files to be organized.
Humans remain responsible for interpreting the output and making keep/archive/delete decisions.

Usage:
    python tools/maintenance/generate_inventory.py [--format json|text]
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any


def find_files_by_pattern(root_dir: Path, pattern: str) -> List[str]:
    """Find all files matching the given glob pattern."""
    files = list(root_dir.glob(f"**/{pattern}"))
    return sorted([str(f.relative_to(root_dir)) for f in files])


def categorize_files(files: List[str], categories: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Categorize files by their location."""
    result = {cat: [] for cat in categories.keys()}
    
    for file in files:
        categorized = False
        for category, prefixes in categories.items():
            if any(file.startswith(prefix) for prefix in prefixes):
                result[category].append(file)
                categorized = True
                break
        if not categorized:
            result.setdefault("other", []).append(file)
    
    return result


def generate_inventory(root_dir: Path) -> Dict[str, Any]:
    """Generate inventory of files to be decluttered."""
    
    inventory = {}
    
    # Diagnostic scripts (check_*.py)
    check_scripts = find_files_by_pattern(root_dir, "check_*.py")
    check_categories = categorize_files(check_scripts, {
        "root_level": [""],
        "in_tools": ["tools/"],
        "in_tools_archive": ["tools/archive/"],
        "in_tests": ["tests/"],
        "in_strategy_converter": ["tools/strategy_converter/"]
    })
    inventory["diagnostic_scripts"] = {
        "count": len(check_scripts),
        "by_location": {k: {"count": len(v), "files": v} for k, v in check_categories.items() if v}
    }
    
    # Test files (test_*.py)
    test_files = find_files_by_pattern(root_dir, "test_*.py")
    test_categories = categorize_files(test_files, {
        "root_level": [""],
        "in_tests": ["tests/"],
        "in_tools": ["tools/"],
        "in_strategy_converter": ["tools/strategy_converter/"]
    })
    inventory["test_files"] = {
        "count": len(test_files),
        "by_location": {k: {"count": len(v), "files": v} for k, v in test_categories.items() if v}
    }
    
    # Completed documentation (*_COMPLETE.md)
    complete_docs = find_files_by_pattern(root_dir, "*_COMPLETE.md")
    complete_categories = categorize_files(complete_docs, {
        "root_level": [""],
        "in_docs": ["docs/"]
    })
    inventory["completed_docs"] = {
        "count": len(complete_docs),
        "by_location": {k: {"count": len(v), "files": v} for k, v in complete_categories.items() if v}
    }
    
    # Session summaries (SESSION_*.md)
    session_docs = find_files_by_pattern(root_dir, "SESSION_*.md")
    session_categories = categorize_files(session_docs, {
        "root_level": [""],
        "in_docs": ["docs/"]
    })
    inventory["session_docs"] = {
        "count": len(session_docs),
        "by_location": {k: {"count": len(v), "files": v} for k, v in session_categories.items() if v}
    }
    
    # Backup files (*.backup, *_backup.*, *.bak)
    backup_files = []
    for pattern in ["*.backup", "*_backup.*", "*.bak"]:
        backup_files.extend(find_files_by_pattern(root_dir, pattern))
    backup_files = sorted(list(set(backup_files)))
    backup_categories = categorize_files(backup_files, {
        "root_level": [""],
        "in_data": ["data/"],
        "in_backend": ["backend/"]
    })
    inventory["backup_files"] = {
        "count": len(backup_files),
        "by_location": {k: {"count": len(v), "files": v} for k, v in backup_categories.items() if v}
    }
    
    return inventory


def format_text_output(inventory: Dict[str, Any]) -> str:
    """Format inventory as human-readable text."""
    lines = ["# Decluttering Inventory", "", f"Generated: {Path.cwd()}", ""]
    
    for category, data in inventory.items():
        category_title = category.replace("_", " ").title()
        lines.append(f"## {category_title}")
        lines.append(f"**Total:** {data['count']} files")
        lines.append("")
        
        for location, info in data.get("by_location", {}).items():
            location_title = location.replace("_", " ").title()
            lines.append(f"### {location_title} ({info['count']} files)")
            for file in info['files'][:10]:
                lines.append(f"- {file}")
            if len(info['files']) > 10:
                lines.append(f"... and {len(info['files']) - 10} more")
            lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate decluttering inventory")
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: stdout)"
    )
    
    args = parser.parse_args()
    
    # Find project root (where this script is located)
    script_path = Path(__file__).resolve()
    root_dir = script_path.parent.parent.parent
    
    # Generate inventory
    inventory = generate_inventory(root_dir)
    
    # Format output
    if args.format == "json":
        output = json.dumps(inventory, indent=2)
    else:
        output = format_text_output(inventory)
    
    # Write or print output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(output, encoding="utf-8")
        print(f"Inventory written to {output_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
