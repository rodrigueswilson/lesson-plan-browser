"""One-off: list plans that might be for folder 26 W09."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config import settings
import sqlite3

p = Path(settings.SQLITE_DB_PATH).resolve()
conn = sqlite3.connect(str(p))
conn.row_factory = sqlite3.Row
c = conn.cursor()

# All plans, most recent first
c.execute(
    "SELECT id, user_id, week_of, week_folder_path, generated_at FROM weekly_plans ORDER BY generated_at DESC"
)
rows = c.fetchall()
print("All weekly_plans (most recent first), count:", len(rows))
for r in rows:
    d = dict(r)
    print(d)

# Plans where week_of or week_folder_path might be 26 W09
c.execute(
    """SELECT id, user_id, week_of, week_folder_path, generated_at
       FROM weekly_plans
       WHERE week_of LIKE ? OR week_of = ?
          OR (week_folder_path IS NOT NULL AND (week_folder_path LIKE ? OR week_folder_path LIKE ?))
       ORDER BY generated_at DESC""",
    ("%26%09%", "26 W09", "%26 W09%", "%26%W09%"),
)
matches = c.fetchall()
print("\nPlans matching 26 W09 (week_of or week_folder_path):", len(matches))
for r in matches:
    print(dict(r))

conn.close()
