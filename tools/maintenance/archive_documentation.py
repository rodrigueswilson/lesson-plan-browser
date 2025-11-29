#!/usr/bin/env python3
"""
Archive documentation files according to decluttering plan.
Moves files from root to appropriate archive directories.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Archive directories
ARCHIVE_BASE = Path("docs/archive")
ARCHIVE_SESSIONS = ARCHIVE_BASE / "sessions"
ARCHIVE_FIXES = ARCHIVE_BASE / "fixes"
ARCHIVE_IMPLEMENTATIONS = ARCHIVE_BASE / "implementations"
ARCHIVE_ANALYSIS = ARCHIVE_BASE / "analysis"

# Ensure archive directories exist
for dir_path in [ARCHIVE_SESSIONS, ARCHIVE_FIXES, ARCHIVE_IMPLEMENTATIONS, ARCHIVE_ANALYSIS]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Files to archive
ROOT_DIR = Path(".")

# Session summaries → docs/archive/sessions/
SESSION_FILES = [
    "SESSION_1_COMPLETE.md",
    "SESSION_1_ENHANCEMENT_SUMMARY.md",
    "SESSION_10_COMPLETE.md",
    "SESSION_10_HYPERLINK_STRATEGY_VALIDATION.md",
    "SESSION_2_COMPLETE.md",
    "SESSION_3_COMPLETE.md",
    "SESSION_3_START.md",
    "SESSION_3_SUMMARY.md",
    "SESSION_3_TESTING_GUIDE.md",
    "SESSION_4_COMPLETE.md",
    "SESSION_4_PROGRESS.md",
    "SESSION_5_COMPLETE.md",
    "SESSION_6_COMPLETE.md",
    "SESSION_6_DETAILED_TRACKING_COMPLETE.md",
    "SESSION_6_SUMMARY.md",
    "SESSION_6_TESTING_COMPLETE.md",
    "SESSION_7_COMPLETE_DIAGNOSTIC_REPORT.md",
    "SESSION_7_COMPLETE.md",
    "SESSION_7_CRASH_DIAGNOSIS.md",
    "SESSION_7_CRASH_FIX.md",
    "SESSION_7_FINAL_STATUS.md",
    "SESSION_7_FINAL_SUMMARY.md",
    "SESSION_7_SOLUTION_FOUND.md",
    "SESSION_7_SUMMARY.md",
    "SESSION_7_TESTING_GUIDE.md",
    "SESSION_8_COMPLETE.md",
    "SESSION_8_FRONTEND_TIMEOUT_FIX.md",
    "SESSION_8_HANG_FIX_COMPLETE.md",
    "SESSION_8_SIGNATURE_FILTER.md",
    "SESSION_9_HYPERLINK_RESEARCH_PLAN.md",
]

NEXT_SESSION_FILES = [
    "NEXT_SESSION_DAY4.md",
    "NEXT_SESSION_DAY6.md",
    "NEXT_SESSION_DAY8.md",
    "NEXT_SESSION_FEATURES_REVISED.md",
    "NEXT_SESSION_FEATURES.md",
    "NEXT_SESSION_HYPERLINKS_IMAGES_FIX.md",
    "NEXT_SESSION_PLAN.md",
    "NEXT_SESSION_PROMPT.md",
    "NEXT_SESSION_ROADMAP.md",
    "NEXT_SESSION_START_HERE_v2.md",
    "NEXT_SESSION_START_HERE.md",
    "START_SESSION_5.md",
]

# Fix documentation → docs/archive/fixes/
FIX_FILES = [
    "ALL_FIXES_COMPLETE.md",
    "APPLY_FIX_CHECKLIST.md",
    "BATCH_PROCESSOR_FIX_CRITICAL.md",
    "CODE_REVIEW_FIXES_COMPLETE.md",
    "CONTENT_PRESERVATION_FIX_V2.md",
    "CONTENT_PRESERVATION_FIX.md",
    "CRITICAL_BUG_FIX_CROSS_SLOT_CONTAMINATION.md",
    "CRITICAL_BUGS_FIXED.md",
    "CRITICAL_FIX_INSTRUCTIONS.md",
    "CRITICAL_FIXES_APPLIED.md",
    "CRITICAL_FIXES_FOR_SLOT_EXTRACTION.md",
    "CRITICAL_FIXES_SUMMARY.md",
    "CROSS_SLOT_CONTAMINATION_FIX.md",
    "DATABASE_PATH_FIX.md",
    "DIAGNOSTIC_LOGGER_FIXES_NEEDED.md",
    "FRONTEND_FIX_INSTRUCTIONS.md",
    "FRONTEND_SPINNER_FIX.md",
    "HYPERLINK_CROSS_CONTAMINATION_FIX.md",
    "HYPERLINK_FIX_COMPLETE.md",
    "HYPERLINK_FIX_IMPLEMENTATION_SUMMARY.md",
    "HYPERLINK_FIX_SOLUTION_PLAN.md",
    "METADATA_FIX_SUMMARY.md",
    "MULTI_SLOT_HYPERLINK_FIX.md",
    "PHASE_4_FINAL_FIX.md",
    "PHASE_5_CRITICAL_FIX.md",
    "PROGRESS_BAR_BASE64_FIX.md",
    "PROGRESS_BAR_FIX.md",
    "QUICK_FIX_SUMMARY.md",
    "REMAINING_FIXES_SUMMARY.md",
    "SLOT_FILTERING_FIX_CRITICAL.md",
    "SLOT_ISOLATION_FIX_COMPLETE.md",
    "STRICT_SLOT_FILTERING_FIX.md",
    "TAURI_HTTP_FIX.md",
    "UNIT_LESSON_BOLD_FIX.md",
    "FILE_LOCKING_FIX.md",
]

# Implementation plans → docs/archive/implementations/
IMPLEMENTATION_FILES = [
    "COMPLETE_IMPLEMENTATION_SUMMARY.md",
    "COMPLETE_SLOT_EXTRACTION_PLAN.md",
    "DETAILED_TRACKING_COMPLETE.md",
    "DETAILED_TRACKING_IMPLEMENTATION_PROGRESS.md",
    "DETAILED_WORKFLOW_TRACKING_PLAN.md",
    "FINAL_IMPLEMENTATION_PLAN_REALISTIC.md",
    "FINAL_IMPLEMENTATION_PLAN.md",
    "FINAL_IMPLEMENTATION_STATUS.md",
    "IMPLEMENTATION_COMPLETE.md",
    "IMPLEMENTATION_PLAN_FINAL_V2.md",
    "IMPLEMENTATION_PLAN_FINAL_V3.md",
    "IMPLEMENTATION_PLAN_FINAL.md",
    "LEVEL_3_TRACKING_IMPLEMENTATION_PLAN.md",
    "MULTISLOT_INLINE_HYPERLINKS_COMPLETE.md",
    "MULTISLOT_INLINE_HYPERLINKS_FINAL.md",
    "MULTISLOT_INLINE_HYPERLINKS_PLAN_V2.md",
    "MULTISLOT_INLINE_HYPERLINKS_PLAN_V3.md",
    "MULTISLOT_INLINE_HYPERLINKS_PLAN.md",
    "PHASE_1_CHANGES_SUMMARY.md",
    "PHASE_1_DATE_FORMATTER_COMPLETE.md",
    "PHASE_1_DIAGNOSTIC_COMPLETE.md",
    "PHASE_2_DATABASE_MIGRATION_COMPLETE.md",
    "PHASE_2_QUICK_WINS_COMPLETE.md",
    "PHASE_3_COMPLETE_FINAL.md",
    "PHASE_3_DATABASE_CRUD_COMPLETE.md",
    "PHASE_4_FRONTEND_COMPLETE.md",
    "PHASE_4_FRONTEND_PARTIAL.md",
    "PHASE_5_RENDERING_COMPLETE.md",
    "SLOT_AWARE_EXTRACTION_COMPLETE.md",
    "SLOT_AWARE_EXTRACTION_IMPLEMENTED.md",
    "SLOT_AWARE_EXTRACTION_NEEDED.md",
    "STRUCTURE_BASED_PLACEMENT_COMPLETE.md",
    "TEACHER_NAME_WEEK_FORMAT_ACTUAL_PATHS.md",
    "TEACHER_NAME_WEEK_FORMAT_PLAN.md",
]

# Analysis documents → docs/archive/analysis/
ANALYSIS_FILES = [
    "HYPERLINK_ANALYSIS_FINDINGS.md",
    "HYPERLINK_BUG_COMPLETE_ANALYSIS.md",
    "HYPERLINK_FINDINGS_AND_SOLUTION.md",
    "IMAGE_CONTEXT_ANALYSIS.md",
    "COMPREHENSIVE_TABLE_ANALYSIS.md",
    "TABLE_STRUCTURE_ANALYSIS.md",
    "DATA_FLOW_ANALYSIS.md",
    "MULTI_SLOT_NOT_DETECTED_DIAGNOSIS.md",
    "BACKEND_CRASH_DIAGNOSIS.md",
    "FRONTEND_BACKEND_DIAGNOSIS.md",
    "DIAGNOSTIC_LOGGING_SUMMARY.md",
]

def move_file(source_path, dest_dir):
    """Move a file to destination directory."""
    if not source_path.exists():
        return False, f"File not found: {source_path}"
    
    dest_path = dest_dir / source_path.name
    
    # If destination exists, skip (already archived)
    if dest_path.exists():
        return False, f"Already exists: {dest_path}"
    
    try:
        shutil.move(str(source_path), str(dest_path))
        return True, f"Moved to {dest_path}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Archive files according to plan."""
    moved = []
    skipped = []
    errors = []
    
    # Move session files
    print("Archiving session files...")
    for filename in SESSION_FILES + NEXT_SESSION_FILES:
        source = ROOT_DIR / filename
        success, message = move_file(source, ARCHIVE_SESSIONS)
        if success:
            moved.append((filename, "sessions", message))
        elif "not found" in message.lower():
            skipped.append((filename, "sessions", message))
        else:
            errors.append((filename, "sessions", message))
    
    # Move fix files
    print("Archiving fix documentation...")
    for filename in FIX_FILES:
        source = ROOT_DIR / filename
        success, message = move_file(source, ARCHIVE_FIXES)
        if success:
            moved.append((filename, "fixes", message))
        elif "not found" in message.lower():
            skipped.append((filename, "fixes", message))
        else:
            errors.append((filename, "fixes", message))
    
    # Move implementation files
    print("Archiving implementation plans...")
    for filename in IMPLEMENTATION_FILES:
        source = ROOT_DIR / filename
        success, message = move_file(source, ARCHIVE_IMPLEMENTATIONS)
        if success:
            moved.append((filename, "implementations", message))
        elif "not found" in message.lower():
            skipped.append((filename, "implementations", message))
        else:
            errors.append((filename, "implementations", message))
    
    # Move analysis files
    print("Archiving analysis documents...")
    for filename in ANALYSIS_FILES:
        source = ROOT_DIR / filename
        success, message = move_file(source, ARCHIVE_ANALYSIS)
        if success:
            moved.append((filename, "analysis", message))
        elif "not found" in message.lower():
            skipped.append((filename, "analysis", message))
        else:
            errors.append((filename, "analysis", message))
    
    # Print summary
    print(f"\n=== Archive Summary ===")
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

