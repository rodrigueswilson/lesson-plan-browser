"""
User-only tablet database export.

Creates a new SQLite database containing ONLY one user's data, using the tablet
schema (Tauri migrations) as the schema source of truth.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


TABLET_TABLES: Tuple[str, ...] = (
    "users",
    "class_slots",
    "weekly_plans",
    "schedules",
    "lesson_steps",
    "lesson_mode_sessions",
)


TABLET_MIGRATIONS_RELATIVE: Tuple[str, ...] = (
    "lesson-plan-browser/frontend/src-tauri/migrations/001_users.sql",
    "lesson-plan-browser/frontend/src-tauri/migrations/002_class_slots.sql",
    "lesson-plan-browser/frontend/src-tauri/migrations/003_weekly_plans.sql",
    "lesson-plan-browser/frontend/src-tauri/migrations/004_schedule_entries.sql",
    "lesson-plan-browser/frontend/src-tauri/migrations/005_lesson_steps.sql",
    "lesson-plan-browser/frontend/src-tauri/migrations/006_lesson_mode_sessions.sql",
)


@dataclass(frozen=True)
class TabletExportCounts:
    users: int
    class_slots: int
    weekly_plans: int
    schedules: int
    lesson_steps: int
    lesson_mode_sessions: int


@dataclass(frozen=True)
class TabletExportResult:
    user_id: str
    output_path: str
    output_bytes: int
    created_at: str
    counts: TabletExportCounts


class TabletDbExportError(RuntimeError):
    pass


def _format_fk_violations(violations: Sequence[Sequence[object]], limit: int = 25) -> str:
    """
    PRAGMA foreign_key_check rows: (table, rowid, parent, fkid)
    """
    lines: List[str] = []
    for idx, row in enumerate(violations[:limit], start=1):
        try:
            table, rowid, parent, fkid = row[0], row[1], row[2], row[3]
        except Exception:
            lines.append(f"{idx}. {row}")
            continue
        lines.append(f"{idx}. table={table} rowid={rowid} parent={parent} fkid={fkid}")
    remaining = len(violations) - min(len(violations), limit)
    if remaining > 0:
        lines.append(f"... and {remaining} more")
    return "\n".join(lines)


def _project_root() -> Path:
    # backend/ -> repo root
    return Path(__file__).resolve().parents[1]


def _read_tablet_migrations(project_root: Path) -> List[str]:
    sql_chunks: List[str] = []
    for rel in TABLET_MIGRATIONS_RELATIVE:
        path = project_root / rel
        if not path.exists():
            raise TabletDbExportError(
                f"Tablet migration SQL not found: {path}. "
                "Expected repo checkout with lesson-plan-browser/."
            )
        sql_chunks.append(path.read_text(encoding="utf-8"))
    return sql_chunks


def _table_columns(conn: sqlite3.Connection, schema: str, table: str) -> List[str]:
    rows = conn.execute(f"PRAGMA {schema}.table_info({table})").fetchall()
    # PRAGMA table_info: cid, name, type, notnull, dflt_value, pk
    return [r[1] for r in rows]


def _count_table(conn: sqlite3.Connection, schema: str, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0])


def _sqlite_now_expr() -> str:
    # Returns SQL expression for an ISO-ish timestamp (SQLite text)
    return "strftime('%Y-%m-%dT%H:%M:%fZ','now')"


def _select_expr_for_dest_col(
    *,
    src_schema: str,
    src_table: str,
    dest_col: str,
    src_cols: Sequence[str],
    coalesce_now_for: Optional[Sequence[str]] = None,
    coalesce_zero_for: Optional[Sequence[str]] = None,
) -> str:
    if dest_col in src_cols:
        base = f"{src_schema}.{src_table}.{dest_col}"
        if coalesce_now_for and dest_col in coalesce_now_for:
            return f"COALESCE({base}, {_sqlite_now_expr()}) AS {dest_col}"
        if coalesce_zero_for and dest_col in coalesce_zero_for:
            return f"COALESCE({base}, 0) AS {dest_col}"
        return f"{base} AS {dest_col}"

    # Column missing in source: provide safe default.
    if coalesce_now_for and dest_col in coalesce_now_for:
        return f"{_sqlite_now_expr()} AS {dest_col}"
    if coalesce_zero_for and dest_col in coalesce_zero_for:
        return f"0 AS {dest_col}"
    return f"NULL AS {dest_col}"


def export_user_tablet_db(
    *,
    source_db_path: Path,
    user_id: str,
    output_db_path: Path,
    vacuum: bool = True,
    keep_previous_backup: bool = True,
) -> TabletExportResult:
    """
    Export a user-only tablet DB.

    - Creates schema from tablet migrations (SSOT)
    - Copies only one user's rows
    - Writes atomically to avoid corrupt partial outputs
    """
    if not source_db_path.exists():
        raise TabletDbExportError(f"Source database not found: {source_db_path}")

    project_root = _project_root()
    migration_sql = _read_tablet_migrations(project_root)

    output_db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_db_path.with_suffix(output_db_path.suffix + ".tmp")

    if tmp_path.exists():
        tmp_path.unlink()

    # Optionally back up existing output
    if keep_previous_backup and output_db_path.exists():
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = output_db_path.with_name(f"{output_db_path.stem}_prev_{ts}{output_db_path.suffix}")
        try:
            output_db_path.replace(backup_path)
        except OSError:
            # If replace fails (e.g. cross-device), fall back to copy+keep
            import shutil

            shutil.copy2(output_db_path, backup_path)

    conn = sqlite3.connect(tmp_path.as_posix())
    attached = False
    try:
        # We'll enforce/validate foreign keys at the end, but during bulk copy we keep them off.
        # This avoids opaque "FOREIGN KEY constraint failed" mid-export and lets us provide
        # actionable diagnostics via PRAGMA foreign_key_check.
        conn.execute("PRAGMA foreign_keys = OFF;")
        # For an exported artifact, prefer a single-file DB (no WAL sidecar).
        conn.execute("PRAGMA journal_mode = DELETE;")
        conn.execute("PRAGMA synchronous = FULL;")

        # Create schema from tablet migrations (SSOT)
        for chunk in migration_sql:
            conn.executescript(chunk)

        # Attach source database
        conn.execute("ATTACH DATABASE ? AS src", (source_db_path.as_posix(),))
        attached = True

        # Ensure user exists in source
        exists = conn.execute(
            "SELECT 1 FROM src.users WHERE id = ? LIMIT 1", (user_id,)
        ).fetchone()
        if not exists:
            raise TabletDbExportError(f"User not found in source database: {user_id}")

        # Copy rows. We generate column-safe INSERTs based on dest schema.
        now_cols = ("created_at", "updated_at", "generated_at", "session_start_time", "last_updated")
        zero_cols = ("is_active", "is_running", "is_paused", "is_synced", "current_step_index", "remaining_time", "consolidated", "total_slots", "display_order")

        def copy_table(
            *,
            table: str,
            where_sql: str,
            where_params: Sequence[object],
            select_overrides: Optional[Dict[str, str]] = None,
        ) -> None:
            dest_cols = _table_columns(conn, "main", table)
            src_cols = _table_columns(conn, "src", table)

            select_exprs = [
                (
                    (select_overrides[c])
                    if (select_overrides and c in select_overrides)
                    else _select_expr_for_dest_col(
                        src_schema="src",
                        src_table=table,
                        dest_col=c,
                        src_cols=src_cols,
                        coalesce_now_for=now_cols,
                        coalesce_zero_for=zero_cols,
                    )
                )
                for c in dest_cols
            ]
            insert_cols_sql = ", ".join(dest_cols)
            select_sql = ", ".join(select_exprs)

            sql = (
                f"INSERT INTO main.{table} ({insert_cols_sql}) "
                f"SELECT {select_sql} FROM src.{table} WHERE {where_sql}"
            )
            try:
                conn.execute(sql, tuple(where_params))
            except sqlite3.IntegrityError as e:
                raise TabletDbExportError(f"Insert failed for table '{table}': {e}") from e

        # users (single row)
        copy_table(table="users", where_sql="id = ?", where_params=[user_id])

        # user-scoped
        copy_table(table="class_slots", where_sql="user_id = ?", where_params=[user_id])
        copy_table(table="weekly_plans", where_sql="user_id = ?", where_params=[user_id])
        copy_table(table="schedules", where_sql="user_id = ?", where_params=[user_id])

        # plan-scoped
        copy_table(
            table="lesson_steps",
            where_sql="lesson_plan_id IN (SELECT id FROM main.weekly_plans)",
            where_params=[],
        )

        # sessions: user + plan
        # Note: Some historical data can have lesson_mode_sessions.schedule_entry_id pointing to
        # a schedule row that isn't present in the exported subset (e.g. schedule changed).
        # We NULL it out if the referenced schedule row isn't present in main.schedules.
        schedule_entry_expr = (
            "CASE "
            "WHEN src.lesson_mode_sessions.schedule_entry_id IS NULL THEN NULL "
            "WHEN src.lesson_mode_sessions.schedule_entry_id IN (SELECT id FROM main.schedules) "
            "THEN src.lesson_mode_sessions.schedule_entry_id "
            "ELSE NULL "
            "END AS schedule_entry_id"
        )
        copy_table(
            table="lesson_mode_sessions",
            where_sql="user_id = ? AND lesson_plan_id IN (SELECT id FROM main.weekly_plans)",
            where_params=[user_id],
            select_overrides={"schedule_entry_id": schedule_entry_expr},
        )

        # Integrity checks
        conn.execute("PRAGMA foreign_keys = ON;")
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_violations:
            raise TabletDbExportError(
                "Foreign key check failed with "
                f"{len(fk_violations)} violation(s):\n{_format_fk_violations(fk_violations)}"
            )

        # Commit the copy transaction before DETACH/VACUUM (SQLite restriction).
        conn.commit()

        # DETACH must not be run inside an open transaction.
        conn.execute("DETACH DATABASE src")
        attached = False

        # Compact file size (VACUUM must run outside any transaction).
        if vacuum:
            conn.execute("VACUUM;")

        counts = TabletExportCounts(
            users=_count_table(conn, "main", "users"),
            class_slots=_count_table(conn, "main", "class_slots"),
            weekly_plans=_count_table(conn, "main", "weekly_plans"),
            schedules=_count_table(conn, "main", "schedules"),
            lesson_steps=_count_table(conn, "main", "lesson_steps"),
            lesson_mode_sessions=_count_table(conn, "main", "lesson_mode_sessions"),
        )
    finally:
        try:
            if attached:
                conn.execute("DETACH DATABASE src")
        except Exception:
            pass
        conn.close()

    # Atomic replace
    tmp_stat = tmp_path.stat()
    os.replace(tmp_path.as_posix(), output_db_path.as_posix())

    return TabletExportResult(
        user_id=user_id,
        output_path=output_db_path.as_posix(),
        output_bytes=int(tmp_stat.st_size),
        created_at=datetime.utcnow().isoformat() + "Z",
        counts=counts,
    )

