CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    name TEXT NOT NULL,
    base_path_override TEXT,
    template_path TEXT,
    signature_image_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    sync_status TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

