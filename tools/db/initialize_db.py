import sqlite3
import os

db_path = r"d:\LP\data\curriculum.db"

# Backup old if exists
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
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

conn.commit()
conn.close()
print("Database initialized clean with Enhanced Vocabulary Schema.")
