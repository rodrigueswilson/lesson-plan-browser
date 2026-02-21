
import sqlite3
import json
import os
import re

db_path = "d:/LP/data/lesson_planner.db"
if not os.path.exists(db_path):
    db_path = "d:/LP/backend/lesson_planner.db"

def instruction_audit():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- INSTRUCTION CONTENT AUDIT ---")
    try:
        cursor.execute("""
            SELECT source_file_name, content_json, full_text 
            FROM original_lesson_plans 
            WHERE user_id = '29fa9ed7-3174-4999-86fd-40a542c28cff'
        """)
        rows = cursor.fetchall()
        for row in rows:
            filename = row[0]
            content_json = json.loads(row[1]) if isinstance(row[1], str) else row[1]
            full_text = row[2]
            
            print(f"\nFile: {filename}")
            
            # 1. Search in grid cells
            found_in_grid = False
            if "table_content" in content_json:
                for day, data in content_json["table_content"].items():
                    for label, text in data.items():
                        if re.search(r"instruction|activity|procedure|step", label, re.I):
                            print(f"  [GRID] Found '{label}' in {day} table.")
                            found_in_grid = True
            
            # 2. Search in full text outside grid keywords
            if not found_in_grid:
                 patterns = [r"Instruction:", r"Activities:", r"Procedure:", r"Lesson Steps:"]
                 for p in patterns:
                     match = re.search(p, full_text, re.I)
                     if match:
                         context = full_text[match.start():match.start()+100].replace('\n', ' ')
                         print(f"  [TEXT] Found '{p}' in full text: '{context}...'")
            
            if not found_in_grid:
                print("  [WARNING] No explicit 'Instruction' label found in this document.")

    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    instruction_audit()
