#!/usr/bin/env python3
"""
Consolidate tool scripts from root to tools/ directories.
Moves scripts according to Phase 6.2 criteria.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Target directories
TOOLS_DIAGNOSTICS = Path("tools/diagnostics")
TOOLS_MAINTENANCE = Path("tools/maintenance")
TOOLS_UTILITIES = Path("tools/utilities")

# Ensure directories exist
for dir_path in [TOOLS_DIAGNOSTICS, TOOLS_MAINTENANCE, TOOLS_UTILITIES]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Root directory
ROOT_DIR = Path(".")

# Analyze scripts → tools/diagnostics/
ANALYZE_SCRIPTS = [
    "analyze_input_hyperlinks.py",
    "analyze_output_hyperlinks.py",
    "analyze_teacher_files.py",
    "comprehensive_analysis_both_folders.py",
    "comprehensive_diagnostic.py",
    "diagnostic_hyperlink_analysis.py",
    "diagnostic_scripts.py",
]

# Debug scripts → tools/diagnostics/
DEBUG_SCRIPTS = [
    "debug_extraction.py",
    "debug_file_resolution.py",
    "debug_lesson_json.py",
    "debug_slot5.py",
]

# Diagnostic scripts → tools/diagnostics/
DIAGNOSTIC_SCRIPTS = [
    "diagnose_crash.py",
    "diagnose_cross_contamination.py",
]

# Fix scripts → tools/maintenance/
FIX_SCRIPTS = [
    "fix_daniela_file_patterns.py",
    "fix_daniela_parent_folder.py",
    "fix_daniela_path.py",
    "fix_daniela_slots_paths.py",
    "fix_daniela_teachers.py",
    "fix_wilson_patterns.py",
]

# Cleanup scripts → tools/maintenance/
CLEANUP_SCRIPTS = [
    "cleanup_demo_data.py",
    "cleanup_semantic.py",
    "cleanup_stuck_plans.py",
    "cleanup_users.py",
    "clear_cache.py",
    "clear_daniela_slot_files.py",
]

# Configuration scripts → tools/maintenance/
CONFIG_SCRIPTS = [
    "configure_test_slot.py",
    "configure_wilson_slots.py",
]

# Audit scripts → tools/maintenance/
AUDIT_SCRIPTS = [
    "metadata_audit.py",
    "pre_implementation_audit.py",
]

# Verification scripts → tools/maintenance/
VERIFY_SCRIPTS = [
    "verify_backend_code.py",
    "verify_both_outputs.py",
    "verify_config.py",
    "verify_daniela_config.py",
    "verify_hyperlink_placement_auto.py",
    "verify_hyperlink_placement.py",
    "verify_migration.py",
]

# Validation scripts → tools/maintenance/
VALIDATE_SCRIPTS = [
    "validate_assumptions.py",
]

# Utility scripts → tools/utilities/
UTILITY_SCRIPTS = [
    "create_media_fixtures.py",
    "find_lesson_plans.py",
    "generate_demo_data.py",
    "generate_level2_demo_data.py",
    "list_daniela_files.py",
    "list_wilson_files.py",
    "query_metrics.py",
    "quick_check_morais_output.py",
    "recalculate_costs.py",
    "run_analytics_tests.py",
    "simulate_improvements.py",
    "test_file_matching.py",
]

def move_file(source_path, dest_dir):
    """Move a file to destination directory."""
    if not source_path.exists():
        return False, f"File not found: {source_path}"
    
    dest_path = dest_dir / source_path.name
    
    # If destination exists, skip (already moved)
    if dest_path.exists():
        return False, f"Already exists: {dest_path}"
    
    try:
        shutil.move(str(source_path), str(dest_path))
        return True, f"Moved to {dest_path}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Consolidate tool scripts."""
    moved = []
    skipped = []
    errors = []
    
    # Move analyze scripts
    print("Moving analyze scripts to tools/diagnostics/...")
    for filename in ANALYZE_SCRIPTS:
        source = ROOT_DIR / filename
        success, message = move_file(source, TOOLS_DIAGNOSTICS)
        if success:
            moved.append((filename, "diagnostics", message))
        elif "not found" in message.lower():
            skipped.append((filename, "diagnostics", message))
        else:
            errors.append((filename, "diagnostics", message))
    
    # Move debug scripts
    print("Moving debug scripts to tools/diagnostics/...")
    for filename in DEBUG_SCRIPTS:
        source = ROOT_DIR / filename
        success, message = move_file(source, TOOLS_DIAGNOSTICS)
        if success:
            moved.append((filename, "diagnostics", message))
        elif "not found" in message.lower():
            skipped.append((filename, "diagnostics", message))
        else:
            errors.append((filename, "diagnostics", message))
    
    # Move diagnostic scripts
    print("Moving diagnostic scripts to tools/diagnostics/...")
    for filename in DIAGNOSTIC_SCRIPTS:
        source = ROOT_DIR / filename
        success, message = move_file(source, TOOLS_DIAGNOSTICS)
        if success:
            moved.append((filename, "diagnostics", message))
        elif "not found" in message.lower():
            skipped.append((filename, "diagnostics", message))
        else:
            errors.append((filename, "diagnostics", message))
    
    # Move fix scripts
    print("Moving fix scripts to tools/maintenance/...")
    for filename in FIX_SCRIPTS:
        source = ROOT_DIR / filename
        success, message = move_file(source, TOOLS_MAINTENANCE)
        if success:
            moved.append((filename, "maintenance", message))
        elif "not found" in message.lower():
            skipped.append((filename, "maintenance", message))
        else:
            errors.append((filename, "maintenance", message))
    
    # Move cleanup scripts
    print("Moving cleanup scripts to tools/maintenance/...")
    for filename in CLEANUP_SCRIPTS:
        source = ROOT_DIR / filename
        success, message = move_file(source, TOOLS_MAINTENANCE)
        if success:
            moved.append((filename, "maintenance", message))
        elif "not found" in message.lower():
            skipped.append((filename, "maintenance", message))
        else:
            errors.append((filename, "maintenance", message))
    
    # Move config scripts
    print("Moving config scripts to tools/maintenance/...")
    for filename in CONFIG_SCRIPTS:
        source = ROOT_DIR / filename
        success, message = move_file(source, TOOLS_MAINTENANCE)
        if success:
            moved.append((filename, "maintenance", message))
        elif "not found" in message.lower():
            skipped.append((filename, "maintenance", message))
        else:
            errors.append((filename, "maintenance", message))
    
    # Move audit scripts
    print("Moving audit scripts to tools/maintenance/...")
    for filename in AUDIT_SCRIPTS:
        source = ROOT_DIR / filename
        success, message = move_file(source, TOOLS_MAINTENANCE)
        if success:
            moved.append((filename, "maintenance", message))
        elif "not found" in message.lower():
            skipped.append((filename, "maintenance", message))
        else:
            errors.append((filename, "maintenance", message))
    
    # Move verify scripts
    print("Moving verify scripts to tools/maintenance/...")
    for filename in VERIFY_SCRIPTS:
        source = ROOT_DIR / filename
        success, message = move_file(source, TOOLS_MAINTENANCE)
        if success:
            moved.append((filename, "maintenance", message))
        elif "not found" in message.lower():
            skipped.append((filename, "maintenance", message))
        else:
            errors.append((filename, "maintenance", message))
    
    # Move validate scripts
    print("Moving validate scripts to tools/maintenance/...")
    for filename in VALIDATE_SCRIPTS:
        source = ROOT_DIR / filename
        success, message = move_file(source, TOOLS_MAINTENANCE)
        if success:
            moved.append((filename, "maintenance", message))
        elif "not found" in message.lower():
            skipped.append((filename, "maintenance", message))
        else:
            errors.append((filename, "maintenance", message))
    
    # Move utility scripts
    print("Moving utility scripts to tools/utilities/...")
    for filename in UTILITY_SCRIPTS:
        source = ROOT_DIR / filename
        success, message = move_file(source, TOOLS_UTILITIES)
        if success:
            moved.append((filename, "utilities", message))
        elif "not found" in message.lower():
            skipped.append((filename, "utilities", message))
        else:
            errors.append((filename, "utilities", message))
    
    # Print summary
    print(f"\n=== Consolidation Summary ===")
    print(f"Files moved: {len(moved)}")
    print(f"Files skipped (not found): {len(skipped)}")
    print(f"Errors: {len(errors)}")
    
    if moved:
        print(f"\n=== Moved Files ===")
        for filename, category, message in moved:
            print(f"  {category}: {filename}")
    
    if errors:
        print(f"\n=== Errors ===")
        for filename, category, message in errors:
            print(f"  {category}: {filename} - {message}")
    
    return len(moved), len(errors)

if __name__ == "__main__":
    moved_count, error_count = main()
    exit(0 if error_count == 0 else 1)

