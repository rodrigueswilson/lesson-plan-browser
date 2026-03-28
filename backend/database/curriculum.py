import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

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
        """Substring search over title and main HTML fields (interim; FTS5 planned)."""
        q = (query or "").strip()
        if len(q) < 2:
            return []
        if limit < 1 or limit > 200:
            limit = 40
        pat = f"%{q}%"
        sql = """
        SELECT id, unit_id, lesson_number, title
        FROM lessons
        WHERE title LIKE ? OR IFNULL(procedure_html, '') LIKE ?
           OR IFNULL(narrative_html, '') LIKE ?
        ORDER BY unit_id, lesson_number
        LIMIT ?
        """
        with self._get_conn() as conn:
            rows = conn.execute(sql, (pat, pat, pat, limit)).fetchall()
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
        
        with self._get_conn() as conn:
            conn.execute(query, list(valid_data.values()))
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

    def upsert_lesson_resource(self, lesson_id: str, res: Dict[str, Any]):
        """Upserts a resource and links it to a lesson (Double Strategy)."""
        import hashlib
        from datetime import datetime
        import json
        
        res_id = res.get("google_id") or hashlib.md5(res["url"].encode()).hexdigest()
        res_type = "google_doc" if res.get("google_id") else "web"
        
        with self._get_conn() as conn:
            # 1. Upsert resource
            conn.execute("""
                INSERT INTO resources (id, original_url, resource_type, last_sync, metadata)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET last_sync = excluded.last_sync
            """, (res_id, res["url"], res_type, datetime.now().isoformat(), json.dumps({"text": res["text"]})))
            
            # 2. Link to lesson
            conn.execute("INSERT OR IGNORE INTO lesson_resources (lesson_id, resource_id) VALUES (?, ?)", 
                         (lesson_id, res_id))
            conn.commit()
