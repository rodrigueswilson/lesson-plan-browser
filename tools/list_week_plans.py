import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.config import settings
import sqlite3
p = Path(settings.SQLITE_DB_PATH).resolve()
c = sqlite3.connect(str(p))
rows = c.execute(
    "SELECT id, week_of, generated_at FROM weekly_plans WHERE week_of = ? ORDER BY generated_at",
    ("02-23-02-27",),
).fetchall()
print("Main DB path:", p)
print("Plans 02-23-02-27:", rows)
c.close()
