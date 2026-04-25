import sqlite3
import os

def init_resource_table(db_path: str = r"d:\LP\data\curriculum.db"):
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create resources table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        id TEXT PRIMARY KEY,          -- Unique Google ID or internal ID
        original_url TEXT NOT NULL,   -- Original web URL
        local_path TEXT,              -- Path to local file if downloaded
        resource_type TEXT,           -- 'google_doc', 'google_drive', 'web'
        last_sync DATETIME,           -- Last time it was synced/checked
        metadata JSON                 -- Extra info (title, size, etc.)
    )
    """)

    # Create lesson_resources junction table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lesson_resources (
        lesson_id TEXT,
        resource_id TEXT,
        FOREIGN KEY(lesson_id) REFERENCES lessons(id),
        FOREIGN KEY(resource_id) REFERENCES resources(id),
        PRIMARY KEY(lesson_id, resource_id)
    )
    """)

    conn.commit()
    conn.close()
    print("Resource tables initialized successfully.")

if __name__ == "__main__":
    init_resource_table()
