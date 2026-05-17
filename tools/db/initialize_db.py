import os
import sqlite3
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DB = _REPO_ROOT / "data" / "curriculum.db"
db_path = os.environ.get("CURRICULUM_DB_PATH", str(_DEFAULT_DB))

# Backup old if exists
db_path_obj = Path(db_path)
db_path_obj.parent.mkdir(parents=True, exist_ok=True)
if db_path_obj.exists():
    db_path_obj.unlink()

conn = sqlite3.connect(str(db_path_obj))
c = conn.cursor()

# Schema
c.execute("""
CREATE TABLE units (
    id TEXT PRIMARY KEY,
    grade INTEGER,
    subject TEXT,
    unit_number INTEGER,
    title TEXT,
    description TEXT,
    source TEXT,
    source_doc_id TEXT,
    source_url TEXT,
    ingested_at TEXT,
    ingest_run_id TEXT,
    ingest_parser_version TEXT
);
""")

c.execute("""
CREATE TABLE units_intro (
    unit_id TEXT PRIMARY KEY,
    essential_questions TEXT,
    enduring_understandings TEXT,
    FOREIGN KEY(unit_id) REFERENCES units(id)
);
""")

c.execute("""
CREATE TABLE lessons (
    id TEXT PRIMARY KEY,
    unit_id TEXT,
    lesson_number INTEGER,
    title TEXT,
    learning_intentions TEXT,
    daily_instructional_task TEXT,
    success_criteria TEXT,
    essential_questions TEXT,
    procedure TEXT,
    materials TEXT,
    lesson_narrative TEXT,
    instructional_resources TEXT,
    purpose TEXT,
    mlr TEXT,
    objectives_student TEXT,
    procedure_html TEXT,
    narrative_html TEXT,
    vocabulary TEXT,
    practices TEXT,
    procedures TEXT,
    differentiation TEXT,
    standards_structured TEXT,
    ela_key_learning_summary TEXT,
    ela_lesson_plan_structured TEXT,
    science_doc_lesson_number INTEGER,
    science_li_sc_day_structured TEXT,
    source_doc_id TEXT,
    source_url TEXT,
    ingested_at TEXT,
    ingest_run_id TEXT,
    ingest_parser_version TEXT,
    content_hash TEXT,
    FOREIGN KEY(unit_id) REFERENCES units(id)
);
""")

c.execute("""
CREATE TABLE standards (
    code TEXT PRIMARY KEY,
    description TEXT,
    subject TEXT
);
""")

c.execute("""
CREATE TABLE lesson_standards (
    lesson_id TEXT,
    standard_code TEXT,
    PRIMARY KEY(lesson_id, standard_code),
    FOREIGN KEY(lesson_id) REFERENCES lessons(id),
    FOREIGN KEY(standard_code) REFERENCES standards(code)
);
""")

c.execute("""
CREATE TABLE unit_standards (
    unit_id TEXT,
    standard_code TEXT,
    type TEXT,
    PRIMARY KEY(unit_id, standard_code),
    FOREIGN KEY(unit_id) REFERENCES units(id),
    FOREIGN KEY(standard_code) REFERENCES standards(code)
);
""")

# NEW Enhanced Vocabulary Relational Schema
c.execute("""
CREATE TABLE vocabulary_items (
    id TEXT PRIMARY KEY,
    base_term_en TEXT UNIQUE,
    category TEXT, -- 'everyday', 'cross-disciplinary', 'technical'
    subject TEXT,
    grade_cluster TEXT,
    mw_definition_en TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

c.execute("""
CREATE TABLE vocabulary_translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vocab_item_id TEXT,
    language_code TEXT, -- 'en', 'pt', 'es'
    translated_term TEXT,
    level_1_def TEXT,
    level_2_def TEXT,
    level_3_def TEXT,
    level_4_def TEXT,
    level_5_def TEXT,
    level_6_def TEXT,
    FOREIGN KEY(vocab_item_id) REFERENCES vocabulary_items(id)
);
""")

c.execute("""
CREATE TABLE vocabulary_audio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vocab_item_id TEXT,
    language_code TEXT,
    audio_url TEXT,
    provider TEXT, -- 'google_tts', etc.
    FOREIGN KEY(vocab_item_id) REFERENCES vocabulary_items(id)
);
""")

c.execute("""
CREATE TABLE lesson_vocabulary (
    lesson_id TEXT,
    vocab_item_id TEXT,
    PRIMARY KEY(lesson_id, vocab_item_id),
    FOREIGN KEY(lesson_id) REFERENCES lessons(id),
    FOREIGN KEY(vocab_item_id) REFERENCES vocabulary_items(id)
);
""")

c.execute("""
CREATE TABLE resources (
    id TEXT PRIMARY KEY,
    original_url TEXT NOT NULL,
    local_path TEXT,
    resource_type TEXT,
    last_sync TIMESTAMP,
    metadata TEXT
);
""")

c.execute("""
CREATE TABLE lesson_resources (
    lesson_id TEXT,
    resource_id TEXT,
    PRIMARY KEY(lesson_id, resource_id),
    FOREIGN KEY(lesson_id) REFERENCES lessons(id),
    FOREIGN KEY(resource_id) REFERENCES resources(id)
);
""")

c.execute("""
CREATE TABLE science_lesson_day_segments (
    id TEXT PRIMARY KEY,
    lesson_id TEXT NOT NULL,
    segment_index INTEGER NOT NULL,
    day_label TEXT NOT NULL,
    science_doc_lesson_number INTEGER,
    learning_intention_html TEXT,
    success_criteria_html TEXT,
    brief_overview_html TEXT,
    lesson_in_action_html TEXT,
    experimental_splits_json TEXT,
    FOREIGN KEY(lesson_id) REFERENCES lessons(id),
    UNIQUE(lesson_id, segment_index)
);
""")

c.execute(
    "CREATE INDEX IF NOT EXISTS idx_science_lesson_day_segments_lesson_id "
    "ON science_lesson_day_segments(lesson_id)"
)

conn.commit()
conn.close()
print(f"Database initialized clean with Enhanced Vocabulary Schema: {db_path_obj}")
