"""Check main DB and tablet export for week 10 lesson_json."""
import sqlite3
from pathlib import Path

def check_db(path: Path, label: str):
    if not path.exists():
        print(f"{label}: not found at {path}")
        return
    conn = sqlite3.connect(str(path))
    cur = conn.execute("PRAGMA table_info(weekly_plans)")
    cols = [r[1] for r in cur.fetchall()]
    print(f"{label}: {path}")
    print(f"  weekly_plans columns: {cols}")
    has_lesson_json = "lesson_json" in cols
    print(f"  has lesson_json: {has_lesson_json}")
    # Week 10: 03/02-03/06 or 03-02-03-06
    cur = conn.execute(
        "SELECT id, week_of, length(lesson_json) as len FROM weekly_plans WHERE week_of LIKE '%03%02%' OR week_of LIKE '%3/2%' OR week_of LIKE '%03-02%' LIMIT 10"
    )
    rows = cur.fetchall()
    print(f"  week-10-like plans: {len(rows)}")
    for row in rows:
        print(f"    id={row[0]}, week_of={row[1]}, lesson_json length={row[2]}")
    conn.close()

# Main DB (config uses backend/data or similar)
for base in [Path("backend/data/lesson_planner.db"), Path("data/lesson_planner.db")]:
    check_db(base, "Main DB")
    break
# Tablet export for user from logs
export_dir = Path("data/tablet_db_exports")
if not export_dir.exists():
    export_dir = Path("backend/data/tablet_db_exports")
for user_dir in list(export_dir.iterdir())[:1] if export_dir.exists() else []:
    db = user_dir / "lesson_planner.db"
    check_db(db, "Tablet export")
