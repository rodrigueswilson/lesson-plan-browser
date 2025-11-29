#!/usr/bin/env python
"""
Verify tablet database state and query compatibility before making API changes.

This script checks:
1. Database schema (which columns exist)
2. lesson_json data availability
3. SQL query compatibility
4. Data structure validation
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(r"D:\LP\data\lesson_planner.db")


def get_table_schema(conn: sqlite3.Connection, table_name: str) -> List[str]:
    """Get list of column names for a table."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return columns


def check_column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """Check if a specific column exists in a table."""
    columns = get_table_schema(conn, table)
    return column in columns


def test_query(
    conn: sqlite3.Connection, sql: str, params: tuple = ()
) -> tuple[bool, Optional[List[Dict]], Optional[str]]:
    """Test a SQL query and return success status, results, and error message."""
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in rows]
        return True, results, None
    except sqlite3.Error as e:
        return False, None, str(e)


def analyze_lesson_json(lesson_json: Any) -> Dict[str, Any]:
    """Analyze lesson_json content and return statistics."""
    if not lesson_json:
        return {"has_content": False, "type": type(lesson_json).__name__, "size": 0}

    if isinstance(lesson_json, str):
        try:
            parsed = json.loads(lesson_json)
            lesson_json = parsed
        except json.JSONDecodeError:
            return {
                "has_content": False,
                "type": "invalid_json_string",
                "size": len(lesson_json),
            }

    if not isinstance(lesson_json, dict):
        return {"has_content": False, "type": type(lesson_json).__name__, "size": 0}

    # Analyze structure
    analysis = {
        "has_content": True,
        "type": "dict",
        "has_metadata": "metadata" in lesson_json,
        "has_days": "days" in lesson_json,
        "days_count": len(lesson_json.get("days", {})),
        "has_hyperlinks": "_hyperlinks" in lesson_json,
        "hyperlinks_count": len(lesson_json.get("_hyperlinks", [])),
    }

    # Count slots across all days
    total_slots = 0
    if "days" in lesson_json:
        for day_name, day_data in lesson_json["days"].items():
            if isinstance(day_data, dict) and "slots" in day_data:
                total_slots += len(day_data["slots"])
    analysis["total_slots"] = total_slots

    # Check for vocabulary and sentence frames
    has_vocab = False
    has_frames = False
    if "days" in lesson_json:
        for day_name, day_data in lesson_json["days"].items():
            if isinstance(day_data, dict) and "slots" in day_data:
                for slot in day_data["slots"]:
                    if isinstance(slot, dict):
                        if slot.get("vocabulary_cognates"):
                            has_vocab = True
                        if slot.get("sentence_frames"):
                            has_frames = True
                        if has_vocab and has_frames:
                            break
                if has_vocab and has_frames:
                    break
    analysis["has_vocabulary"] = has_vocab
    analysis["has_sentence_frames"] = has_frames

    return analysis


def main():
    print("=" * 80)
    print("TABLET DATABASE VERIFICATION")
    print("=" * 80)
    print(f"\nDatabase: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"\n❌ ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    print(f"✓ Database file exists ({DB_PATH.stat().st_size / 1024 / 1024:.2f} MB)")

    conn = sqlite3.connect(DB_PATH)

    # 1. Check table schema
    print("\n" + "=" * 80)
    print("1. CHECKING TABLE SCHEMA")
    print("=" * 80)

    weekly_plans_columns = get_table_schema(conn, "weekly_plans")
    print(f"\nweekly_plans columns ({len(weekly_plans_columns)}):")
    for col in weekly_plans_columns:
        print(f"  - {col}")

    # Check for potentially missing columns
    required_columns = [
        "id",
        "user_id",
        "week_of",
        "status",
        "generated_at",
        "output_file",
        "lesson_json",
    ]
    optional_columns = ["created_at", "updated_at"]

    print("\nRequired columns check:")
    missing_required = []
    for col in required_columns:
        exists = col in weekly_plans_columns
        status = "✓" if exists else "❌"
        print(f"  {status} {col}")
        if not exists:
            missing_required.append(col)

    print("\nOptional columns check:")
    missing_optional = []
    for col in optional_columns:
        exists = col in weekly_plans_columns
        status = "✓" if exists else "⚠️"
        print(f"  {status} {col}")
        if not exists:
            missing_optional.append(col)

    if missing_required:
        print(f"\n❌ CRITICAL: Missing required columns: {missing_required}")
        print("   The database schema is incomplete!")
        sys.exit(1)

    if missing_optional:
        print(f"\n⚠️  WARNING: Missing optional columns: {missing_optional}")
        print("   Queries selecting these columns will fail!")

    # 2. Test queries
    print("\n" + "=" * 80)
    print("2. TESTING SQL QUERIES")
    print("=" * 80)

    # Get a sample plan ID
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM weekly_plans LIMIT 1")
    sample_plan = cursor.fetchone()

    if not sample_plan:
        print("\n❌ ERROR: No plans found in database")
        sys.exit(1)

    sample_plan_id = sample_plan[0]
    print(f"\nTesting with plan ID: {sample_plan_id}")

    # Test query WITHOUT optional columns (safe query)
    safe_query = """
        SELECT id, user_id, week_of, status, generated_at, output_file, lesson_json
        FROM weekly_plans
        WHERE id = ?
        LIMIT 1
    """
    print("\nTest 1: Safe query (without optional columns)")
    success, results, error = test_query(conn, safe_query, (sample_plan_id,))
    if success:
        print("  ✓ Query succeeded")
        if results:
            print(f"  ✓ Returned {len(results)} row(s)")
            row = results[0]
            print(f"  ✓ Columns returned: {list(row.keys())}")
        else:
            print("  ⚠️  No rows returned")
    else:
        print(f"  ❌ Query failed: {error}")

    # Test query WITH optional columns (current query)
    current_query = """
        SELECT id, user_id, week_of, status, generated_at, output_file, lesson_json, created_at, updated_at
        FROM weekly_plans
        WHERE id = ?
        LIMIT 1
    """
    print("\nTest 2: Current query (with optional columns)")
    success, results, error = test_query(conn, current_query, (sample_plan_id,))
    if success:
        print("  ✓ Query succeeded")
        if results:
            print(f"  ✓ Returned {len(results)} row(s)")
            row = results[0]
            print(f"  ✓ Columns returned: {list(row.keys())}")
        else:
            print("  ⚠️  No rows returned")
    else:
        print(f"  ❌ Query failed: {error}")
        if missing_optional:
            print("  ⚠️  This query will fail on tablet if columns are missing!")

    # 3. Analyze lesson_json data
    print("\n" + "=" * 80)
    print("3. ANALYZING LESSON_JSON DATA")
    print("=" * 80)

    cursor.execute(
        """
        SELECT id, user_id, week_of, lesson_json
        FROM weekly_plans
        ORDER BY generated_at DESC
        """
    )
    plans = cursor.fetchall()
    total_plans = len(plans)
    print(f"\nTotal plans: {total_plans}")

    plans_with_json = []
    plans_without_json = []
    sample_analyses = []

    for plan_id, user_id, week_of, lesson_json in plans:
        if lesson_json:
            plans_with_json.append(plan_id)
            if len(sample_analyses) < 3:
                analysis = analyze_lesson_json(lesson_json)
                sample_analyses.append(
                    {
                        "plan_id": plan_id,
                        "week_of": week_of,
                        **analysis,
                    }
                )
        else:
            plans_without_json.append(plan_id)

    print(f"Plans with lesson_json: {len(plans_with_json)}")
    print(f"Plans without lesson_json: {len(plans_without_json)}")

    if sample_analyses:
        print("\nSample lesson_json analysis:")
        for sample in sample_analyses:
            print(f"\nPlan {sample['plan_id']} ({sample['week_of']}):")
            print(f"  - Has content: {sample['has_content']}")
            print(f"  - Days: {sample['days_count']}")
            print(f"  - Total slots: {sample['total_slots']}")
            print(f"  - Vocabulary present: {sample['has_vocabulary']}")
            print(f"  - Sentence frames present: {sample['has_sentence_frames']}")
            print(
                f"  - Hyperlinks: {sample['has_hyperlinks']} ({sample['hyperlinks_count']})"
            )
    else:
        print("\nNo lesson_json content found to analyze.")

    conn.close()
