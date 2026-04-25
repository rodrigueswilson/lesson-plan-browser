"""
Restore plan_20260220174959 (the one with "I will read and write about the poem")
from the 04fe8898 tablet export into main DB. Then delete plan_20260220172447.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.config import settings

PLAN_ID_POEM = "plan_20260220174959"  # has "read and write about the poem"
PLAN_ID_OTHER = "plan_20260220172447"
EXPORT_DB = Path("data/tablet_db_exports/04fe8898-cb89-4a73-affb-64a97a98f820/lesson_planner.db")
MAIN_DB = Path(settings.SQLITE_DB_PATH).resolve()


def copy_plan(export: sqlite3.Connection, main: sqlite3.Connection, plan_id: str) -> None:
    main_cols = [d[1] for d in main.execute("PRAGMA table_info(weekly_plans)").fetchall()]
    export_cols = [d[1] for d in export.execute("PRAGMA table_info(weekly_plans)").fetchall()]
    cols = [c for c in export_cols if c in main_cols]
    row = export.execute(f"SELECT {','.join(cols)} FROM weekly_plans WHERE id = ?", (plan_id,)).fetchone()
    if not row:
        raise SystemExit(f"Plan {plan_id} not in export.")
    main.execute(
        f"INSERT OR REPLACE INTO weekly_plans ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})",
        row,
    )
    steps = export.execute("SELECT * FROM lesson_steps WHERE lesson_plan_id = ?", (plan_id,)).fetchall()
    if steps:
        sc = [d[1] for d in export.execute("PRAGMA table_info(lesson_steps)").fetchall()]
        sc = [c for c in sc if c in [d[1] for d in main.execute("PRAGMA table_info(lesson_steps)").fetchall()]]
        for s in export.execute(f"SELECT {','.join(sc)} FROM lesson_steps WHERE lesson_plan_id = ?", (plan_id,)).fetchall():
            main.execute(f"INSERT OR REPLACE INTO lesson_steps ({','.join(sc)}) VALUES ({','.join('?'*len(sc))})", s)
        print(f"Restored {len(steps)} lesson_steps for {plan_id}")


def delete_plan(main: sqlite3.Connection, plan_id: str) -> None:
    main.execute("DELETE FROM lesson_steps WHERE lesson_plan_id = ?", (plan_id,))
    main.execute("DELETE FROM performance_metrics WHERE plan_id = ?", (plan_id,))
    main.execute("DELETE FROM lesson_mode_sessions WHERE lesson_plan_id = ?", (plan_id,))
    main.execute("DELETE FROM weekly_plans WHERE id = ?", (plan_id,))
    print(f"Deleted plan {plan_id} and dependents.")


def main():
    if not EXPORT_DB.exists():
        print(f"Export not found: {EXPORT_DB}")
        return 1
    export = sqlite3.connect(str(EXPORT_DB))
    main = sqlite3.connect(str(MAIN_DB))
    copy_plan(export, main, PLAN_ID_POEM)
    delete_plan(main, PLAN_ID_OTHER)
    main.commit()
    export.close()
    main.close()
    print(f"Done. Plan {PLAN_ID_POEM} (poem goal) restored; {PLAN_ID_OTHER} removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
