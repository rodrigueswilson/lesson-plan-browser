
import sqlite3
import os

db_path = "d:/LP/data/lesson_planner.db"
if not os.path.exists(db_path):
    db_path = "d:/LP/backend/lesson_planner.db"

def find_paths():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- DANIELA SILVA PLANS ---")
    try:
        cursor.execute("""
            SELECT source_file_name, source_file_path 
            FROM original_lesson_plans 
            WHERE user_id = '29fa9ed7-3174-4999-86fd-40a542c28cff'
        """)
        rows = cursor.fetchall()
        for row in rows:
            print(f"File: {row[0]}")
            print(f"Path: {row[1]}\n")
    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    find_paths()
