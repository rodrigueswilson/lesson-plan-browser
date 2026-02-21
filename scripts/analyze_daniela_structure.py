
import sqlite3
import json
import os

db_path = "d:/LP/data/lesson_planner.db"
if not os.path.exists(db_path):
    db_path = "d:/LP/backend/lesson_planner.db"

def analyze_daniela_data():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- ANALYZING STRUCTURE FOR DANIELA SILVA'S TEACHERS ---")
    try:
        cursor.execute("""
            SELECT source_file_name, content_json 
            FROM original_lesson_plans 
            WHERE user_id = '29fa9ed7-3174-4999-86fd-40a542c28cff'
        """)
        rows = cursor.fetchall()
        for row in rows:
            filename = row[0]
            content_json = json.loads(row[1]) if isinstance(row[1], str) else row[1]
            
            print(f"\nFile: {filename}")
            if "table_content" in content_json:
                tables = content_json["table_content"]
                # Just show the first day found to see the row labels
                days = list(tables.keys())
                if days:
                    first_day = days[0]
                    labels = list(tables[first_day].keys())
                    print(f"Row Labels found for {first_day}:")
                    for label in labels:
                        print(f"  - {label}")
                else:
                    print("No days found in table_content.")
            else:
                print("No table_content found in content_json.")
                
    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    analyze_daniela_data()
