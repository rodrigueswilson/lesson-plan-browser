from backend.database import Database

db = Database()

with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(weekly_plans)')
    columns = cursor.fetchall()
    
    print("weekly_plans table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
