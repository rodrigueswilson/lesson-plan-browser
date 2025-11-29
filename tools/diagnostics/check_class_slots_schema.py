from backend.database import Database

db = Database()

with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(class_slots)')
    columns = cursor.fetchall()
    
    print("class_slots table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
