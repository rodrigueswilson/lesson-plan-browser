-- LEGACY REFERENCE ONLY (not SSOT). See tools/db/CURRICULUM_SCHEMA_SSOT.md and tools/db/initialize_db.py.

-- Initial schema for curriculum database

CREATE TABLE IF NOT EXISTS units (
    id TEXT PRIMARY KEY,
    grade INTEGER NOT NULL,
    subject TEXT NOT NULL,
    unit_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    source TEXT,
    status TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS units_intro (
    unit_id TEXT PRIMARY KEY,
    essential_questions TEXT, -- JSON array
    enduring_understandings TEXT, -- JSON array
    rigor_conceptual TEXT,
    rigor_procedural TEXT,
    rigor_application TEXT,
    FOREIGN KEY(unit_id) REFERENCES units(id)
);

CREATE TABLE IF NOT EXISTS sections (
    id TEXT PRIMARY KEY,
    unit_id TEXT NOT NULL,
    section_id TEXT, -- e.g., "A", "B"
    title TEXT,
    FOREIGN KEY(unit_id) REFERENCES units(id)
);

CREATE TABLE IF NOT EXISTS lessons (
    id TEXT PRIMARY KEY,
    unit_id TEXT NOT NULL,
    section_id TEXT,
    lesson_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    learning_intentions TEXT, -- JSON array
    success_criteria TEXT, -- JSON array
    instructional_routines TEXT, -- JSON array
    daily_instructional_task TEXT,
    procedure_html TEXT,
    narrative_html TEXT,
    FOREIGN KEY(unit_id) REFERENCES units(id),
    FOREIGN KEY(section_id) REFERENCES sections(id)
);

CREATE TABLE IF NOT EXISTS standards (
    code TEXT PRIMARY KEY,
    description TEXT,
    subject TEXT
);

CREATE TABLE IF NOT EXISTS unit_standards (
    unit_id TEXT,
    standard_code TEXT,
    type TEXT, -- priority, supporting, etc.
    PRIMARY KEY(unit_id, standard_code),
    FOREIGN KEY(unit_id) REFERENCES units(id),
    FOREIGN KEY(standard_code) REFERENCES standards(code)
);

CREATE TABLE IF NOT EXISTS lesson_standards (
    lesson_id TEXT,
    standard_code TEXT,
    PRIMARY KEY(lesson_id, standard_code),
    FOREIGN KEY(lesson_id) REFERENCES lessons(id),
    FOREIGN KEY(standard_code) REFERENCES standards(code)
);

CREATE TABLE IF NOT EXISTS vocabulary (
    id TEXT PRIMARY KEY,
    term TEXT NOT NULL,
    definition TEXT,
    tier INTEGER,
    context TEXT
);

CREATE TABLE IF NOT EXISTS unit_vocabulary (
    unit_id TEXT,
    vocab_id TEXT,
    PRIMARY KEY(unit_id, vocab_id),
    FOREIGN KEY(unit_id) REFERENCES units(id),
    FOREIGN KEY(vocab_id) REFERENCES vocabulary(id)
);

CREATE TABLE IF NOT EXISTS lesson_vocabulary (
    lesson_id TEXT,
    vocab_id TEXT,
    PRIMARY KEY(lesson_id, vocab_id),
    FOREIGN KEY(lesson_id) REFERENCES lessons(id),
    FOREIGN KEY(vocab_id) REFERENCES vocabulary(id)
);

CREATE TABLE IF NOT EXISTS resources (
    id TEXT PRIMARY KEY,
    unit_id TEXT,
    lesson_id TEXT,
    title TEXT,
    type TEXT,
    url TEXT,
    FOREIGN KEY(unit_id) REFERENCES units(id),
    FOREIGN KEY(lesson_id) REFERENCES lessons(id)
);
