"""Check if tablet export DB contains plan_20260220172447."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config import settings
import sqlite3

export_dir = Path("data/tablet_db_exports/29fa9ed7-3174-4999-86fd-40a542c28cff")
db_path = export_dir / "lesson_planner.db"
if not db_path.exists():
    print("Tablet export DB not found:", db_path)
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
c = conn.cursor()
c.execute(
    "SELECT id, user_id, week_of, generated_at FROM weekly_plans WHERE week_of = ? ORDER BY generated_at",
    ("02-23-02-27",),
)
rows = c.fetchall()
print("Plans for 02-23-02-27 in tablet export:")
for r in rows:
    print(r)
c.execute("SELECT id, length(lesson_json) FROM weekly_plans WHERE id = ?", ("plan_20260220172447",))
row = c.fetchone()
print("plan_20260220172447 in export:", row)
conn.close()
