"""
Restore plan_20260220172447 from tablet export DB into the main lesson_planner.db,
then optionally delete plan_20260220174959 (the one we wrongly kept).

Tablet export path: data/tablet_db_exports/29fa9ed7-3174-4999-86fd-40a542c28cff/lesson_planner.db
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.config import settings

PLAN_ID_RESTORE = "plan_20260220172447"
PLAN_ID_DELETE = "plan_20260220174959"
EXPORT_DB = Path("data/tablet_db_exports/29fa9ed7-3174-4999-86fd-40a542c28cff/lesson_planner.db")
MAIN_DB = Path(settings.SQLITE_DB_PATH).resolve()


def main():
    if not EXPORT_DB.exists():
        print(f"Export DB not found: {EXPORT_DB}")
        return 1

    export = sqlite3.connect(str(EXPORT_DB))
    main = sqlite3.connect(str(MAIN_DB))

    # 1) Copy weekly_plans row from export to main (only columns that exist in main)
    main_cols = [d[1] for d in main.execute("PRAGMA table_info(weekly_plans)").fetchall()]
    export_cols = [d[1] for d in export.execute("PRAGMA table_info(weekly_plans)").fetchall()]
    cols_to_copy = [c for c in export_cols if c in main_cols]
    sel = ",".join(cols_to_copy)
    row = export.execute(
        f"SELECT {sel} FROM weekly_plans WHERE id = ?", (PLAN_ID_RESTORE,)
    ).fetchone()
    if not row:
        print(f"Plan {PLAN_ID_RESTORE} not found in export.")
        return 1

    placeholders = ",".join("?" for _ in cols_to_copy)
    main.execute(
        f"INSERT OR REPLACE INTO weekly_plans ({','.join(cols_to_copy)}) VALUES ({placeholders})",
        row,
    )

    # 2) Copy lesson_steps for this plan
    steps = export.execute(
        "SELECT * FROM lesson_steps WHERE lesson_plan_id = ?", (PLAN_ID_RESTORE,)
    ).fetchall()
    if steps:
        main_step_cols = [d[1] for d in main.execute("PRAGMA table_info(lesson_steps)").fetchall()]
        export_step_cols = [d[1] for d in export.execute("PRAGMA table_info(lesson_steps)").fetchall()]
        sc = [c for c in export_step_cols if c in main_step_cols]
        sel = ",".join(sc)
        steps_data = export.execute(
            f"SELECT {sel} FROM lesson_steps WHERE lesson_plan_id = ?", (PLAN_ID_RESTORE,)
        ).fetchall()
        ph = ",".join("?" for _ in sc)
        for s in steps_data:
            main.execute(
                f"INSERT OR REPLACE INTO lesson_steps ({','.join(sc)}) VALUES ({ph})",
                s,
            )
        print(f"Restored {len(steps_data)} lesson_steps for {PLAN_ID_RESTORE}")

    # 3) Copy performance_metrics for this plan (if table exists in export)
    try:
        metrics = export.execute(
            "SELECT * FROM performance_metrics WHERE plan_id = ?", (PLAN_ID_RESTORE,)
        ).fetchall()
    except sqlite3.OperationalError:
        metrics = []
    if metrics:
        main_m = [d[1] for d in main.execute("PRAGMA table_info(performance_metrics)").fetchall()]
        export_m = [d[1] for d in export.execute("PRAGMA table_info(performance_metrics)").fetchall()]
        m_cols = [c for c in export_m if c in main_m]
        sel = ",".join(m_cols)
        metrics_data = export.execute(
            f"SELECT {sel} FROM performance_metrics WHERE plan_id = ?", (PLAN_ID_RESTORE,)
        ).fetchall()
        ph = ",".join("?" for _ in m_cols)
        for m in metrics_data:
            main.execute(
                f"INSERT OR REPLACE INTO performance_metrics ({','.join(m_cols)}) VALUES ({ph})",
                m,
            )
        print(f"Restored {len(metrics_data)} performance_metrics for {PLAN_ID_RESTORE}")

    # 4) Copy lesson_mode_sessions for this plan (if table exists in export)
    try:
        sessions = export.execute(
            "SELECT * FROM lesson_mode_sessions WHERE lesson_plan_id = ?", (PLAN_ID_RESTORE,)
        ).fetchall()
    except sqlite3.OperationalError:
        sessions = []
    if sessions:
        main_s = [d[1] for d in main.execute("PRAGMA table_info(lesson_mode_sessions)").fetchall()]
        export_s = [d[1] for d in export.execute("PRAGMA table_info(lesson_mode_sessions)").fetchall()]
        s_cols = [c for c in export_s if c in main_s]
        sel = ",".join(s_cols)
        sessions_data = export.execute(
            f"SELECT {sel} FROM lesson_mode_sessions WHERE lesson_plan_id = ?", (PLAN_ID_RESTORE,)
        ).fetchall()
        ph = ",".join("?" for _ in s_cols)
        for s in sessions_data:
            main.execute(
                f"INSERT OR REPLACE INTO lesson_mode_sessions ({','.join(s_cols)}) VALUES ({ph})",
                s,
            )
        print(f"Restored {len(sessions_data)} lesson_mode_sessions for {PLAN_ID_RESTORE}")

    main.commit()
    export.close()
    main.close()

    print(f"Restored plan {PLAN_ID_RESTORE} from tablet export into {MAIN_DB}")
    print("Now run: python tools/delete_plan_by_week.py --plan-id " + PLAN_ID_DELETE + " --force")
    return 0


if __name__ == "__main__":
    sys.exit(main())
