from backend.database import Database

db = Database()

with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Database tables:")
    for table in tables:
        print(f"  - {table[0]}")
