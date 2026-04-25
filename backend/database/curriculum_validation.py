"""
Validate curriculum SQLite schema before serving curriculum API routes.

SSOT: tools/db/initialize_db.py (+ tools/db/CURRICULUM_SCHEMA_SSOT.md).
"""

from __future__ import annotations

import os
import sqlite3
from typing import Dict, List, Optional, Set, Tuple

REQUIRED_TABLES: Tuple[str, ...] = (
    "units",
    "lessons",
    "standards",
    "lesson_standards",
    "vocabulary_items",
    "vocabulary_translations",
    "lesson_vocabulary",
    "resources",
    "lesson_resources",
    "science_lesson_day_segments",
)

# Minimum columns expected by backend/database/curriculum.py
REQUIRED_COLUMNS: Dict[str, Set[str]] = {
    "units": {
        "id",
        "source_doc_id",
        "source_url",
        "ingested_at",
        "ingest_run_id",
        "ingest_parser_version",
    },
    "lessons": {
        "id",
        "unit_id",
        "lesson_number",
        "title",
        "procedure_html",
        "narrative_html",
        "standards_structured",
        "ela_key_learning_summary",
        "ela_lesson_plan_structured",
        "science_doc_lesson_number",
        "science_li_sc_day_structured",
        "source_doc_id",
        "source_url",
        "ingested_at",
        "ingest_run_id",
        "ingest_parser_version",
        "content_hash",
    },
    "resources": {"id", "original_url", "resource_type"},
    "lesson_resources": {"lesson_id", "resource_id"},
    "lesson_vocabulary": {"lesson_id", "vocab_item_id"},
    "vocabulary_items": {"id", "base_term_en"},
    "vocabulary_translations": {
        "vocab_item_id",
        "language_code",
        "translated_term",
        "level_1_def",
        "level_5_def",
    },
    "science_lesson_day_segments": {
        "id",
        "lesson_id",
        "segment_index",
        "day_label",
        "science_doc_lesson_number",
        "learning_intention_html",
        "success_criteria_html",
        "brief_overview_html",
        "lesson_in_action_html",
        "experimental_splits_json",
    },
}

_cache_mtime: Optional[float] = None
_cached_issues: Optional[List[str]] = None


def _table_columns(conn: sqlite3.Connection, table: str) -> Set[str]:
    cur = conn.execute("PRAGMA table_info(%s)" % table)
    return {row[1] for row in cur.fetchall()}


def validate_curriculum_db(db_path: Optional[str] = None) -> List[str]:
    """Return a list of human-readable issues; empty means OK."""
    path = db_path or os.environ.get("CURRICULUM_DB_PATH")
    if not path:
        # Match CurriculumDatabase.__init__ default when env not set
        path = r"d:\LP\data\curriculum.db"
    issues: List[str] = []
    if not os.path.isfile(path):
        issues.append(f"curriculum database file not found: {path}")
        return issues

    # Apply idempotent ALTERs for known lesson/unit columns before checking PRAGMA
    # (avoids 503 curriculum routes when code expects newer schema than the DB file).
    try:
        from backend.database.curriculum import CurriculumDatabase

        CurriculumDatabase(db_path=path).ensure_provenance_columns()
    except Exception:
        pass

    conn = sqlite3.connect(path)
    try:
        existing = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        for t in REQUIRED_TABLES:
            if t not in existing:
                issues.append(f"missing table: {t}")

        for table, cols in REQUIRED_COLUMNS.items():
            if table not in existing:
                continue
            have = _table_columns(conn, table)
            for c in cols:
                if c not in have:
                    issues.append(f"missing column: {table}.{c}")
    finally:
        conn.close()

    return issues


def get_curriculum_schema_issues(db_path: Optional[str] = None) -> List[str]:
    """Cached validation keyed by DB file mtime."""
    global _cache_mtime, _cached_issues
    path = db_path or os.environ.get("CURRICULUM_DB_PATH") or r"d:\LP\data\curriculum.db"
    if not os.path.isfile(path):
        return validate_curriculum_db(path)
    mtime = os.path.getmtime(path)
    if _cached_issues is not None and mtime == _cache_mtime:
        return _cached_issues
    _cached_issues = validate_curriculum_db(path)
    _cache_mtime = mtime
    return _cached_issues


def clear_curriculum_schema_cache() -> None:
    global _cache_mtime, _cached_issues
    _cache_mtime = None
    _cached_issues = None
