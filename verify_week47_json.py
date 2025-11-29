#!/usr/bin/env python
"""Verify that JSON file content matches database lesson_json column for week 47.

This script compares the JSON files stored in week folders with the lesson_json
column stored in the database to ensure they match.

Optional dependency: deepdiff (for detailed difference reporting)
  Install with: pip install deepdiff
  Without it, the script will use a simpler comparison method.
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
try:
    from deepdiff import DeepDiff
    HAS_DEEPDIFF = True
except ImportError:
    HAS_DEEPDIFF = False

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent / "backend"))

try:
    from backend.file_manager import FileManager
except ImportError:
    print("Warning: Could not import FileManager, will use fallback logic")
    FileManager = None

DB_PATH = Path("data/lesson_planner.db")


def normalize_json(data: Any) -> Any:
    """Normalize JSON data for comparison (removes ordering differences, etc.)."""
    if isinstance(data, dict):
        # Sort keys recursively
        return {k: normalize_json(v) for k, v in sorted(data.items())}
    elif isinstance(data, list):
        return [normalize_json(item) for item in data]
    else:
        return data


def load_json_from_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load and parse JSON from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  Error reading JSON file {file_path}: {e}")
        return None


def load_json_from_db(db_cursor, plan_id: str) -> Optional[Dict[str, Any]]:
    """Load lesson_json from database for a plan."""
    db_cursor.execute(
        "SELECT lesson_json FROM weekly_plans WHERE id = ?",
        (plan_id,)
    )
    row = db_cursor.fetchone()
    if not row or not row[0]:
        return None
    
    lesson_json = row[0]
    
    # Parse if it's a string
    if isinstance(lesson_json, str):
        # Check if it's a minimal/null value
        trimmed = lesson_json.strip()
        if len(trimmed) <= 10 or trimmed.lower() in ['null', '{}', '[]', '""', '[]']:
            return None
        
        try:
            parsed = json.loads(lesson_json)
            # If it parsed to None, null, empty dict, or empty list, treat as missing
            if parsed is None or parsed == {} or parsed == []:
                return None
            return parsed
        except json.JSONDecodeError as e:
            print(f"  Error parsing JSON from database: {e}")
            return None
    
    # If it's already a dict/list, check if it's empty
    if isinstance(lesson_json, (dict, list)) and len(lesson_json) == 0:
        return None
    
    if lesson_json is None:
        return None
    
    return lesson_json


def find_json_files_for_plan(
    week_folder_path: Optional[str],
    user_base_path: Optional[str],
    week_of: str
) -> list[Path]:
    """Find JSON files for a plan using week_folder_path or base_path."""
    json_files = []
    
    # Try week_folder_path first
    if week_folder_path:
        folder = Path(week_folder_path)
        if folder.exists():
            json_files.extend(folder.glob("*.json"))
            if json_files:
                return json_files
    
    # Fallback: use FileManager if available
    if user_base_path and FileManager:
        try:
            fm = FileManager(user_base_path)
            week_folder = fm.get_week_folder(week_of)
            if week_folder.exists():
                json_files.extend(week_folder.glob("*.json"))
        except Exception as e:
            print(f"  Warning: FileManager failed: {e}")
    
    # Fallback: try to find week folder by pattern
    if user_base_path and not json_files:
        base = Path(user_base_path)
        if base.exists():
            # Look for folders matching week pattern (e.g., "25 W47" or contains "47")
            for folder in base.iterdir():
                if folder.is_dir() and ("47" in folder.name or "W47" in folder.name):
                    json_files.extend(folder.glob("*.json"))
    
    return json_files


def compare_json_simple(
    file_json: Dict[str, Any],
    db_json: Dict[str, Any]
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Simple JSON comparison using normalized string comparison.
    Returns (are_equal, diff_info)
    """
    try:
        file_normalized = normalize_json(file_json)
        db_normalized = normalize_json(db_json)
        
        file_str = json.dumps(file_normalized, sort_keys=True)
        db_str = json.dumps(db_normalized, sort_keys=True)
        
        if file_str == db_str:
            return True, None
        
        # Calculate basic difference stats
        file_keys = set(file_json.keys()) if isinstance(file_json, dict) else set()
        db_keys = set(db_json.keys()) if isinstance(db_json, dict) else set()
        
        diff_info = {
            "file_size": len(file_str),
            "db_size": len(db_str),
            "keys_only_in_file": list(file_keys - db_keys),
            "keys_only_in_db": list(db_keys - file_keys),
            "difference_bytes": abs(len(file_str) - len(db_str))
        }
        
        return False, diff_info
    except Exception as e:
        return False, {"error": str(e)}


def compare_json_content(
    file_json: Dict[str, Any],
    db_json: Dict[str, Any]
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Compare two JSON structures.
    Returns (are_equal, diff_dict)
    """
    try:
        if HAS_DEEPDIFF:
            diff = DeepDiff(
                normalize_json(file_json),
                normalize_json(db_json),
                ignore_order=True,
                verbose_level=2
            )
            
            if not diff:
                return True, None
            else:
                return False, diff.to_dict()
        else:
            # Fallback to simple comparison
            return compare_json_simple(file_json, db_json)
    except Exception as e:
        print(f"  Error comparing JSON: {e}")
        return False, {"error": str(e)}


def verify_week47_plans():
    """Main verification function."""
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH.absolute()}")
        return
    
    print(f"Loading database: {DB_PATH.absolute()}")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Find all plans for week 47
    # Week 47 could be stored as "W47", "11-17-11-21", "47", etc.
    cur.execute("""
        SELECT wp.id, wp.user_id, wp.week_of, wp.week_folder_path, 
               wp.lesson_json IS NOT NULL as has_lesson_json,
               LENGTH(COALESCE(wp.lesson_json, '')) as json_size,
               u.name, u.base_path_override
        FROM weekly_plans wp
        JOIN users u ON wp.user_id = u.id
        WHERE wp.week_of LIKE '%47%' 
           OR wp.week_of LIKE '%11-17%'
           OR wp.week_of LIKE '%W47%'
        ORDER BY wp.week_of DESC
    """)
    
    plans = cur.fetchall()
    
    if not plans:
        print("No plans found for week 47")
        conn.close()
        return
    
    print(f"\nFound {len(plans)} plan(s) for week 47:\n")
    
    results = {
        "total": len(plans),
        "matched": 0,
        "mismatched": 0,
        "missing_file": 0,
        "missing_db": 0,
        "errors": 0
    }
    
    for plan_id, user_id, week_of, week_folder_path, has_lesson_json, json_size, user_name, base_path in plans:
        print(f"\n{'=' * 80}")
        print(f"Plan ID: {plan_id}")
        print(f"User: {user_name}")
        print(f"Week: {week_of}")
        print(f"Has lesson_json in DB: {has_lesson_json} ({json_size} bytes)")
        print(f"Week folder path: {week_folder_path or 'Not set'}")
        print(f"User base path: {base_path or 'Not set'}")
        
        # Load JSON from database
        db_json = load_json_from_db(cur, plan_id)
        
        # Check if it's just a null/empty value
        if not db_json or (isinstance(db_json, dict) and len(db_json) == 0):
            print("  ❌ No lesson_json in database (NULL or empty)")
            results["missing_db"] += 1
            continue
        
        # Check if it's a minimal/null JSON value
        db_json_str = json.dumps(db_json) if db_json else ""
        if len(db_json_str) <= 10 or db_json_str.strip() in ['null', '{}', '[]', '""']:
            print(f"  ❌ lesson_json in database is empty/null ({len(db_json_str)} bytes)")
            results["missing_db"] += 1
            continue
        
        print(f"  ✓ Database JSON loaded ({len(db_json_str)} bytes)")
        
        # Find JSON files
        json_files = find_json_files_for_plan(week_folder_path, base_path, week_of)
        
        if not json_files:
            print("  ❌ No JSON files found on disk")
            results["missing_file"] += 1
            continue
        
        print(f"  ✓ Found {len(json_files)} JSON file(s) on disk")
        
        # Compare each JSON file with database
        matched_any = False
        for json_file in json_files:
            print(f"\n  Comparing with: {json_file.name}")
            
            file_json = load_json_from_file(json_file)
            if not file_json:
                results["errors"] += 1
                continue
            
            print(f"    File JSON loaded ({len(json.dumps(file_json))} bytes)")
            
            # Compare
            are_equal, diff = compare_json_content(file_json, db_json)
            
            if are_equal:
                print(f"    ✅ MATCH: File content matches database exactly")
                matched_any = True
                results["matched"] += 1
                break  # Found a match, no need to check other files
            else:
                print(f"    ❌ MISMATCH: File content differs from database")
                if diff:
                    if 'error' in diff:
                        print(f"      Error: {diff['error']}")
                    elif HAS_DEEPDIFF:
                        # DeepDiff format
                        diff_types = list(diff.keys())
                        print(f"      Difference types: {', '.join(diff_types)}")
                        
                        if 'values_changed' in diff:
                            changes = list(diff['values_changed'].items())[:3]
                            for path, change_info in changes:
                                print(f"      Changed: {path}")
                        
                        if 'dictionary_item_added' in diff:
                            added = list(diff['dictionary_item_added'])[:3]
                            print(f"      Added in DB: {len(added)} item(s)")
                        
                        if 'dictionary_item_removed' in diff:
                            removed = list(diff['dictionary_item_removed'])[:3]
                            print(f"      Removed from DB: {len(removed)} item(s)")
                    else:
                        # Simple comparison format
                        print(f"      File size: {diff.get('file_size', 0)} bytes")
                        print(f"      DB size: {diff.get('db_size', 0)} bytes")
                        print(f"      Size difference: {diff.get('difference_bytes', 0)} bytes")
                        if diff.get('keys_only_in_file'):
                            print(f"      Keys only in file: {diff['keys_only_in_file'][:5]}")
                        if diff.get('keys_only_in_db'):
                            print(f"      Keys only in DB: {diff['keys_only_in_db'][:5]}")
        
        if not matched_any:
            results["mismatched"] += 1
    
    # Summary
    print(f"\n{'=' * 80}")
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Total plans checked: {results['total']}")
    print(f"✅ Matched: {results['matched']}")
    print(f"❌ Mismatched: {results['mismatched']}")
    print(f"⚠️  Missing file: {results['missing_file']}")
    print(f"⚠️  Missing DB: {results['missing_db']}")
    print(f"❌ Errors: {results['errors']}")
    
    if results['matched'] == results['total'] - results['missing_file'] - results['missing_db'] - results['errors']:
        print("\n✅ All available plans match!")
    elif results['mismatched'] > 0:
        print(f"\n⚠️  {results['mismatched']} plan(s) have mismatched content")
        print("   This means the JSON file on disk differs from what's stored in the database.")
        print("   Consider running a backfill script to update the database with file contents.")
    elif results['missing_db'] > 0 or results['missing_file'] > 0:
        print(f"\n⚠️  Some plans are missing data (DB: {results['missing_db']}, Files: {results['missing_file']})")
        print("   Plans with missing DB content need to be backfilled from JSON files.")
        print("   Plans with missing files may have only been stored in the database.")
    
    print("\n" + "=" * 80)
    print("Note: Size differences may indicate:")
    print("  - Database has fewer fields (e.g., missing _hyperlinks, _images)")
    print("  - File has additional metadata fields")
    print("  - Different versions saved at different times")
    print("=" * 80)
    
    conn.close()


if __name__ == "__main__":
    try:
        verify_week47_plans()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

