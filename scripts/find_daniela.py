
import sqlite3
import os

db_path = "d:/LP/data/lesson_planner.db"
if not os.path.exists(db_path):
    # Try another common location if not there
    db_path = "d:/LP/backend/lesson_planner.db"

def query_users():
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- USERS ---")
    try:
        cursor.execute("SELECT id, name, email FROM users WHERE name LIKE '%Daniela%' OR name LIKE '%Silva%'")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
        
    print("\n--- RECENT ORIGINAL PLANS ---")
    try:
        cursor.execute("SELECT user_id, source_file_name, primary_teacher_name FROM original_lesson_plans LIMIT 10")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    query_users()
