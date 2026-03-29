import json
import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


def _fts5_prefix_query(raw: str) -> Optional[str]:
    """
    Build a conservative FTS5 MATCH string (AND of prefix tokens).
    Returns None if nothing usable remains (caller should fall back to LIKE).
    """
    parts: List[str] = []
    for token in (raw or "").split():
        cleaned = "".join(c for c in token if c.isalnum() or c in "-_'")
        if len(cleaned) < 2:
            continue
        esc = cleaned.replace('"', '""')
        parts.append(f'"{esc}"*')
    if not parts:
        return None
    return " AND ".join(parts)

_UNIT_PROVENANCE_COLUMNS: Dict[str, str] = {
    "source_doc_id": "TEXT",
    "source_url": "TEXT",
    "ingested_at": "TEXT",
    "ingest_run_id": "TEXT",
    "ingest_parser_version": "TEXT",
}

_LESSON_PROVENANCE_COLUMNS: Dict[str, str] = {
    "source_doc_id": "TEXT",
    "source_url": "TEXT",
    "ingested_at": "TEXT",
    "ingest_run_id": "TEXT",
    "ingest_parser_version": "TEXT",
    "content_hash": "TEXT",
}

# Content columns required by curriculum_validation / newer schema (idempotent ALTER).
_LESSON_EXTRA_SCHEMA_COLUMNS: Dict[str, str] = {
    "ela_key_learning_summary": "TEXT",
    "ela_lesson_plan_structured": "TEXT",
}

class CurriculumDatabase:
    def __init__(self, db_path: str = r"d:\LP\data\curriculum.db"):
        self.db_path = db_path
        self.ensure_provenance_columns()

    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[2]

    def scraped_registry_path(self) -> Path:
        override = os.environ.get("SCRAPED_REGISTRY_PATH")
        if override:
            return Path(override)
        return self.repo_root() / "reference_docs" / "scraped_registry.json"

    def load_scraped_registry(self) -> Dict[str, Any]:
        p = self.scraped_registry_path()
        if not p.is_file():
            return {}
        with p.open(encoding="utf-8") as f:
            return json.load(f)

    def search_lessons_text(self, query: str, limit: int = 40) -> List[Dict[str, Any]]:
        """Full-text search (FTS5) with HTML snippet highlights; falls back to LIKE."""
        q = (query or "").strip()
        if len(q) < 2:
            return []
        if limit < 1 or limit > 200:
            limit = 40
        self.ensure_lessons_fts_index()
        fts_q = _fts5_prefix_query(q)
        with self._get_conn() as conn:
            fts_ready = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='lessons_fts'"
            ).fetchone()
            if fts_q and fts_ready:
                try:
                    sql_fts = """
                    SELECT
                        l.id,
                        l.unit_id,
                        l.lesson_number,
                        l.title,
                        snippet(
                            lessons_fts,
                            2,
                            '<mark>',
                            '</mark>',
                            ' … ',
                            20
                        ) AS snippet_html,
                        bm25(lessons_fts) AS fts_rank
                    FROM lessons_fts
                    JOIN lessons l ON l.id = lessons_fts.lesson_id
                    WHERE lessons_fts MATCH ?
                    ORDER BY fts_rank
                    LIMIT ?
                    """
                    rows = conn.execute(sql_fts, (fts_q, limit)).fetchall()
                    return [dict(r) for r in rows]
                except sqlite3.OperationalError as exc:
                    logger.warning("FTS search failed, using LIKE fallback: %s", exc)
            pat = f"%{q}%"
            sql_like = """
            SELECT id, unit_id, lesson_number, title, NULL AS snippet_html, NULL AS fts_rank
            FROM lessons
            WHERE title LIKE ? OR IFNULL(procedure_html, '') LIKE ?
               OR IFNULL(narrative_html, '') LIKE ?
            ORDER BY unit_id, lesson_number
            LIMIT ?
            """
            rows = conn.execute(sql_like, (pat, pat, pat, limit)).fetchall()
            return [dict(r) for r in rows]

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_explorer_hierarchy(self) -> List[Dict[str, Any]]:
        """Returns the Grade -> Subject -> Unit hierarchy."""
        query = """
        SELECT grade, subject, id as unit_id, title as unit_title, unit_number
        FROM units
        ORDER BY grade, subject, unit_number
        """
        hierarchy = {}
        with self._get_conn() as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                grade_num = row['grade']
                grade = f"Grade {grade_num}" if grade_num > 0 else "Uncategorized"
                subject = row['subject']
                
                if grade not in hierarchy:
                    hierarchy[grade] = {}
                if subject not in hierarchy[grade]:
                    hierarchy[grade][subject] = []
                    
                hierarchy[grade][subject].append({
                    "id": row['unit_id'],
                    "title": row['unit_title'],
                    "number": row['unit_number']
                })
            
        # Convert to list for API consistency
        final_list = []
        for grade, subjects in hierarchy.items():
            grade_item = {"name": grade, "subjects": []}
            for subject, units in subjects.items():
                grade_item["subjects"].append({
                    "name": subject,
                    "units": units
                })
            final_list.append(grade_item)
            
        return final_list

    def get_unit_lessons(self, unit_id: str) -> List[Dict[str, Any]]:
        """Returns all lessons for a specific unit."""
        query = "SELECT id, lesson_number, title FROM lessons WHERE unit_id = ? ORDER BY lesson_number"
        with self._get_conn() as conn:
            rows = conn.execute(query, (unit_id,)).fetchall()
            return [dict(r) for r in rows]

    def get_unit_intro(self, unit_id: str) -> Optional[Dict[str, Any]]:
        """Returns introductory content for a unit."""
        query = """
        SELECT
            ui.*,
            u.source_doc_id,
            u.source_url,
            u.ingested_at,
            u.ingest_run_id,
            u.ingest_parser_version
        FROM units_intro ui
        LEFT JOIN units u ON u.id = ui.unit_id
        WHERE ui.unit_id = ?
        """
        with self._get_conn() as conn:
            row = conn.execute(query, (unit_id,)).fetchone()
            return dict(row) if row else None

    def ensure_provenance_columns(self) -> None:
        """Ensure curriculum provenance fields exist for units and lessons."""
        with self._get_conn() as conn:
            units_cols = {
                row["name"] for row in conn.execute("PRAGMA table_info(units)").fetchall()
            }
            lessons_cols = {
                row["name"] for row in conn.execute("PRAGMA table_info(lessons)").fetchall()
            }
            for col, col_type in _UNIT_PROVENANCE_COLUMNS.items():
                if col not in units_cols:
                    conn.execute(f"ALTER TABLE units ADD COLUMN {col} {col_type}")
            for col, col_type in _LESSON_PROVENANCE_COLUMNS.items():
                if col not in lessons_cols:
                    conn.execute(f"ALTER TABLE lessons ADD COLUMN {col} {col_type}")
            for col, col_type in _LESSON_EXTRA_SCHEMA_COLUMNS.items():
                if col not in lessons_cols:
                    conn.execute(f"ALTER TABLE lessons ADD COLUMN {col} {col_type}")
            conn.commit()
        self.ensure_lessons_fts_index()
        self.ensure_unit_semantic_links_table()

    def ensure_lessons_fts_index(self) -> None:
        """Create or rebuild FTS5 index over lesson title + HTML body (Phase 6 navigator).

        Rows are synchronized from ``upsert_lesson`` (no DB triggers; SQLite FTS5 + ON CONFLICT
        UPDATE paths proved brittle with AFTER UPDATE/DELETE triggers on this schema).
        """
        fts_ddl = """
        CREATE VIRTUAL TABLE IF NOT EXISTS lessons_fts USING fts5(
            lesson_id UNINDEXED,
            title,
            body
        );
        """
        with self._get_conn() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            if "lessons" not in tables:
                return
            for trg in ("lessons_fts_ai", "lessons_fts_ad", "lessons_fts_au"):
                conn.execute(f"DROP TRIGGER IF EXISTS {trg}")
            conn.executescript(fts_ddl)
            n_lessons = conn.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
            n_fts = conn.execute("SELECT COUNT(*) FROM lessons_fts").fetchone()[0]
            if n_lessons != n_fts:
                conn.execute("DELETE FROM lessons_fts")
                conn.execute(
                    """
                    INSERT INTO lessons_fts(lesson_id, title, body)
                    SELECT
                        id,
                        COALESCE(title, ''),
                        COALESCE(procedure_html, '') || ' ' || COALESCE(narrative_html, '')
                    FROM lessons
                    """
                )
            conn.commit()

    def _replace_lesson_fts_row(self, conn: sqlite3.Connection, lesson_id: str) -> None:
        if not conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='lessons_fts'"
        ).fetchone():
            return
        conn.execute("DELETE FROM lessons_fts WHERE lesson_id = ?", (lesson_id,))
        row = conn.execute(
            """
            SELECT
                id,
                COALESCE(title, '') AS title,
                COALESCE(procedure_html, '') || ' ' || COALESCE(narrative_html, '') AS body
            FROM lessons
            WHERE id = ?
            """,
            (lesson_id,),
        ).fetchone()
        if row:
            conn.execute(
                "INSERT INTO lessons_fts(lesson_id, title, body) VALUES (?, ?, ?)",
                (row["id"], row["title"], row["body"]),
            )

    def ensure_unit_semantic_links_table(self) -> None:
        """Curator/staff links between units (manual) plus API-level grade-band suggestions."""
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS unit_semantic_links (
                    id TEXT PRIMARY KEY,
                    from_unit_id TEXT NOT NULL,
                    to_unit_id TEXT NOT NULL,
                    link_kind TEXT NOT NULL DEFAULT 'related',
                    rationale TEXT NOT NULL DEFAULT '',
                    source TEXT NOT NULL DEFAULT 'manual',
                    FOREIGN KEY (from_unit_id) REFERENCES units(id),
                    FOREIGN KEY (to_unit_id) REFERENCES units(id),
                    UNIQUE (from_unit_id, to_unit_id, link_kind)
                )
                """
            )
            conn.commit()

    def get_unit_semantic_links(self, unit_id: str) -> List[Dict[str, Any]]:
        """Manual links from DB merged with cross-grade suggestions (same subject, adjacent grade)."""
        out: List[Dict[str, Any]] = []
        seen_to: Set[str] = set()
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT
                    l.id AS link_id,
                    l.to_unit_id,
                    l.link_kind,
                    l.rationale,
                    l.source,
                    u.title AS to_unit_title,
                    u.grade AS to_grade,
                    u.unit_number AS to_unit_number
                FROM unit_semantic_links l
                JOIN units u ON u.id = l.to_unit_id
                WHERE l.from_unit_id = ?
                ORDER BY l.source, l.link_kind, u.grade, u.unit_number
                """,
                (unit_id,),
            ).fetchall()
            for r in rows:
                d = dict(r)
                tid = d["to_unit_id"]
                seen_to.add(tid)
                out.append(
                    {
                        "id": d["link_id"],
                        "to_unit_id": tid,
                        "to_unit_title": d["to_unit_title"],
                        "to_grade": d["to_grade"],
                        "to_unit_number": d["to_unit_number"],
                        "link_kind": d["link_kind"],
                        "rationale": d["rationale"] or "",
                        "source": d["source"] or "manual",
                    }
                )

            cur = conn.execute(
                "SELECT grade, subject FROM units WHERE id = ?",
                (unit_id,),
            ).fetchone()
            if not cur:
                return out
            grade, subject = cur["grade"], cur["subject"]
            if grade is None or not subject:
                return out
            for delta in (-1, 1):
                ng = int(grade) + delta
                if ng < 0:
                    continue
                peers = conn.execute(
                    """
                    SELECT id, title, unit_number, grade
                    FROM units
                    WHERE subject = ? AND grade = ? AND id != ?
                    ORDER BY unit_number, title
                    """,
                    (subject, ng, unit_id),
                ).fetchall()
                for p in peers:
                    pid = p["id"]
                    if pid in seen_to:
                        continue
                    seen_to.add(pid)
                    out.append(
                        {
                            "id": None,
                            "to_unit_id": pid,
                            "to_unit_title": p["title"],
                            "to_grade": p["grade"],
                            "to_unit_number": p["unit_number"],
                            "link_kind": "vertical_band",
                            "rationale": (
                                f"Same {subject} in Grade {ng} (suggested adjacent band)."
                            ),
                            "source": "suggested",
                        }
                    )
        return out

    def get_lesson_details(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        """Returns full details for a single lesson."""
        query = "SELECT * FROM lessons WHERE id = ?"
        with self._get_conn() as conn:
            row = conn.execute(query, (lesson_id,)).fetchone()
            return dict(row) if row else None

    def get_lesson_vocabulary(self, lesson_id: str) -> List[Dict[str, Any]]:
        """Returns enriched bilingual vocabulary for a lesson."""
        with self._get_conn() as conn:
            vi_cols = {
                row[1] for row in conn.execute("PRAGMA table_info(vocabulary_items)")
            }
            mw_col = "vi.mw_definition_en" if "mw_definition_en" in vi_cols else "NULL AS mw_definition_en"
            query = f"""
        SELECT
            vi.base_term_en AS term,
            {mw_col},
            vt.translated_term,
            vt.level_1_def,
            vt.level_2_def,
            vt.level_3_def,
            vt.level_4_def,
            vt.level_5_def,
            vt.level_6_def
        FROM lesson_vocabulary lv
        JOIN vocabulary_items vi ON lv.vocab_item_id = vi.id
        LEFT JOIN vocabulary_translations vt
            ON vi.id = vt.vocab_item_id AND vt.language_code = 'pt'
        WHERE lv.lesson_id = ?
        """
            rows = conn.execute(query, (lesson_id,)).fetchall()
            result = []
            for row in rows:
                levels = [
                    row["level_1_def"],
                    row["level_2_def"],
                    row["level_3_def"],
                    row["level_4_def"],
                    row["level_5_def"],
                    row["level_6_def"],
                ]
                leveled = []
                for lv in levels:
                    leveled.append({
                        "definition": lv,
                        "definition_pt": lv,
                    })
                if not any(levels) and row["mw_definition_en"]:
                    leveled[4] = {
                        "definition": row["mw_definition_en"],
                        "definition_pt": row["mw_definition_en"],
                    }
                tr = row["translated_term"]
                if not tr:
                    tr = row["term"]
                result.append({
                    "term": row["term"],
                    "translated_term": tr,
                    "leveled_definitions": leveled,
                })
            return result

    def get_lesson_standards(self, lesson_id: str) -> List[Dict[str, Any]]:
        """Returns standards linked to a lesson (code + description)."""
        query = """
        SELECT s.code, s.description, s.subject
        FROM lesson_standards ls
        JOIN standards s ON s.code = ls.standard_code
        WHERE ls.lesson_id = ?
        ORDER BY s.code
        """
        with self._get_conn() as conn:
            rows = conn.execute(query, (lesson_id,)).fetchall()
            return [dict(r) for r in rows]

    def upsert_lesson(self, lesson_data: Dict[str, Any]):
        """Inserts or updates a lesson record."""
        requested_columns = [
            "id", "unit_id", "lesson_number", "title", "learning_intentions",
            "daily_instructional_task", "success_criteria", "essential_questions",
            "procedure", "materials", "lesson_narrative", "instructional_resources",
            "purpose", "mlr", "objectives_student", "procedure_html", "narrative_html",
            "vocabulary", "practices", "procedures", "differentiation",
            "standards_structured",
            "ela_key_learning_summary",
            "ela_lesson_plan_structured",
            "source_doc_id", "source_url", "ingested_at", "ingest_run_id",
            "ingest_parser_version", "content_hash",
        ]

        with self._get_conn() as conn:
            table_cols = {
                row["name"] for row in conn.execute("PRAGMA table_info(lessons)").fetchall()
            }

        allowed = [c for c in requested_columns if c in table_cols]
        valid_data = {k: v for k, v in lesson_data.items() if k in allowed}
        requested_in_payload: Set[str] = {
            k for k in lesson_data.keys() if k in requested_columns
        }
        dropped = requested_in_payload - set(valid_data.keys())
        if dropped:
            logger.warning(
                "upsert_lesson dropped keys (not in lessons table or empty): %s",
                sorted(dropped),
            )
        if not valid_data:
            return
        
        # Prepare SQL
        placeholders = ", ".join(["?"] * len(valid_data))
        cols = ", ".join(valid_data.keys())
        updates = ", ".join([f"{k} = EXCLUDED.{k}" for k in valid_data.keys() if k != "id"])
        
        query = f"""
        INSERT INTO lessons ({cols})
        VALUES ({placeholders})
        ON CONFLICT(id) DO UPDATE SET {updates}
        """
        lesson_id = valid_data.get("id")
        with self._get_conn() as conn:
            conn.execute(query, list(valid_data.values()))
            if lesson_id:
                self._replace_lesson_fts_row(conn, str(lesson_id))
            conn.commit()

    def update_unit_intro(self, unit_id: str, data: Dict[str, Any]):
        """Updates unit introductory content."""
        columns = ["essential_questions", "enduring_understandings", "procedure_html", "narrative_html"]
        valid_data = {k: v for k, v in data.items() if k in columns}
        
        if not valid_data:
            return
            
        set_clause = ", ".join([f"{k} = ?" for k in valid_data.keys()])
        query = f"UPDATE units_intro SET {set_clause} WHERE unit_id = ?"
        
        with self._get_conn() as conn:
            conn.execute(query, list(valid_data.values()) + [unit_id])
            conn.commit()

    def upsert_standard(self, code: str, description: str = "", subject: str = "Math"):
        """Upserts a standard to the standards table."""
        query = "INSERT INTO standards (code, description, subject) VALUES (?, ?, ?) ON CONFLICT(code) DO UPDATE SET description = excluded.description"
        with self._get_conn() as conn:
            conn.execute(query, (code, description, subject))
            conn.commit()

    def link_lesson_to_standard(self, lesson_id: str, standard_code: str):
        """Links a lesson to a standard."""
        query = "INSERT OR IGNORE INTO lesson_standards (lesson_id, standard_code) VALUES (?, ?)"
        with self._get_conn() as conn:
            conn.execute(query, (lesson_id, standard_code))
            conn.commit()

    def link_lesson_to_vocabulary(self, lesson_id: str, term: str):
        """Links a lesson to a vocabulary term."""
        import uuid
        with self._get_conn() as conn:
            # Check if exists
            row = conn.execute("SELECT id FROM vocabulary_items WHERE base_term_en = ?", (term,)).fetchone()
            if row:
                vocab_item_id = row[0]
            else:
                vocab_item_id = str(uuid.uuid4())
                conn.execute("INSERT INTO vocabulary_items (id, base_term_en) VALUES (?, ?)", (vocab_item_id, term))
            
            conn.execute("INSERT OR IGNORE INTO lesson_vocabulary (lesson_id, vocab_item_id) VALUES (?, ?)", (lesson_id, vocab_item_id))
            conn.commit()

    @staticmethod
    def curriculum_export_search_roots() -> List[Path]:
        """
        Directories used to discover and (with resolve service) serve local curriculum exports.

        Includes optional CURRICULUM_LOCAL_FILES_ROOT and repo reference_docs/scraped (tools/scraper
        hierarchical layout + export_doc_ids_to_docx outputs often live here).
        """
        roots: List[Path] = []
        try:
            from backend.config import settings

            configured = settings.curriculum_local_files_root
            if configured is not None and configured.is_dir():
                roots.append(configured.resolve())
        except ImportError:
            pass
        scraped = CurriculumDatabase.repo_root() / "reference_docs" / "scraped"
        if scraped.is_dir():
            sr = scraped.resolve()
            if sr not in roots:
                roots.append(sr)
        return roots

    @staticmethod
    def path_is_under_export_roots(candidate: Path) -> bool:
        """True if path is under at least one export root, or if no roots are configured (legacy)."""
        roots = CurriculumDatabase.curriculum_export_search_roots()
        if not roots:
            return True
        resolved = candidate.resolve()
        for root in roots:
            try:
                resolved.relative_to(root.resolve())
                return True
            except ValueError:
                continue
        return False

    @staticmethod
    def discover_local_path_for_google_doc(google_id: str) -> Optional[str]:
        """
        Find an on-disk export for a Google Doc id.

        Resolution order:
        1. `{google_id}.{ext}` under each search root (flat; matches CURRICULUM_LOCAL_FILES_ROOT convention).
        2. `*_{google_id[:8]}.{ext}` up to depth 3 under each root (matches tools/scraper/export_doc_ids_to_docx.py).
        3. Under reference_docs/scraped: `**/originals/*.json` or `**/*.docs-api.json` containing
           documentId, with sibling exports (`{base}.docx`/`.pdf`/`.html`/`.md`) or `{base}_by_tab/*.docx`.
        """
        if not google_id:
            return None
        roots = CurriculumDatabase.curriculum_export_search_roots()
        if not roots:
            return None

        exts = (".docx", ".pdf", ".html", ".md")
        id8 = google_id[:8] if len(google_id) >= 8 else google_id
        doc_id_re = re.compile(r'"documentId"\s*:\s*"' + re.escape(google_id) + r'"')

        def pick_preferred(paths: List[Path]) -> Optional[Path]:
            if not paths:
                return None
            paths = sorted({p.resolve() for p in paths if p.is_file()})
            for ext in (".docx", ".pdf", ".html", ".md"):
                for p in paths:
                    if p.suffix.lower() == ext:
                        return p
            return paths[0]

        for root in roots:
            for ext in exts:
                p = root / f"{google_id}{ext}"
                if p.is_file():
                    return str(p.resolve())

        glob_matches: List[Path] = []
        for root in roots:
            for ext in exts:
                for p in root.rglob(f"*_{id8}{ext}"):
                    if p.is_file():
                        glob_matches.append(p)
        chosen = pick_preferred(glob_matches)
        if chosen:
            return str(chosen.resolve())

        scraped = CurriculumDatabase.repo_root() / "reference_docs" / "scraped"
        if not scraped.is_dir():
            return None
        _max_read = 4_000_000

        def export_stem_for_sidecars(json_path: Path) -> str:
            """Match sibling exports: main.py uses {title}.json; export script uses {stem}_{id8}.docs-api.json."""
            name = json_path.name
            if name.endswith(".docs-api.json"):
                return name[: -len(".docs-api.json")]
            return json_path.stem

        for json_path in list(scraped.rglob("originals/*.json")) + list(
            scraped.rglob("*.docs-api.json")
        ):
            try:
                raw = json_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if len(raw) > _max_read:
                raw = raw[:_max_read]
            if not doc_id_re.search(raw):
                continue
            parent = json_path.parent
            stem = export_stem_for_sidecars(json_path)
            for ext in (".docx", ".pdf", ".html", ".md"):
                cand = parent / f"{stem}{ext}"
                if cand.is_file():
                    return str(cand.resolve())
            tab_dir = parent / f"{stem}_by_tab"
            if tab_dir.is_dir():
                tab_docx = sorted(tab_dir.glob("*.docx"))
                if tab_docx:
                    return str(tab_docx[0].resolve())
        return None

    def get_resource_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT id, original_url, local_path, resource_type, metadata FROM resources WHERE id = ?",
                (resource_id,),
            ).fetchone()
            return dict(row) if row else None

    def upsert_lesson_resource(self, lesson_id: str, res: Dict[str, Any]):
        """Upserts a resource and links it to a lesson (Double Strategy)."""
        import hashlib
        from datetime import datetime
        import json

        res_id = res.get("google_id") or hashlib.md5(res["url"].encode()).hexdigest()
        res_type = "google_doc" if res.get("google_id") else "web"
        local_path: Optional[str] = None
        if res.get("google_id"):
            local_path = self.discover_local_path_for_google_doc(res["google_id"])

        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT INTO resources (id, original_url, local_path, resource_type, last_sync, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    last_sync = excluded.last_sync,
                    local_path = COALESCE(excluded.local_path, resources.local_path)
                """,
                (
                    res_id,
                    res["url"],
                    local_path,
                    res_type,
                    datetime.now().isoformat(),
                    json.dumps({"text": res["text"]}),
                ),
            )

            conn.execute(
                "INSERT OR IGNORE INTO lesson_resources (lesson_id, resource_id) VALUES (?, ?)",
                (lesson_id, res_id),
            )
            conn.commit()
