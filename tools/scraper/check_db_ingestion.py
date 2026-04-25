import sqlite3
import json
import os

db_path = r"d:\LP\data\lesson_planner.db"

def check_ingestion():
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check table existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='original_lesson_plans'")
        if not cursor.fetchone():
            print("Table 'original_lesson_plans' does not exist!")
            return

        # Check total count
        cursor.execute("SELECT COUNT(*) FROM original_lesson_plans")
        count = cursor.fetchone()[0]
        print(f"Total records in original_lesson_plans: {count}")

        if count > 0:
            # Show last 1
            cursor.execute("SELECT id, content_json FROM original_lesson_plans ORDER BY extracted_at DESC LIMIT 1")
            row = cursor.fetchone()
            
            content = json.loads(row[1]) if isinstance(row[1], str) else row[1]
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            
            print("\nSearching for Day Headers in Tables:")
            found_days = []
            for t_idx, item in enumerate(content):
                if item["type"] == "table":
                    for r_idx, r in enumerate(item["rows"]):
                        row_text = ""
                        for c in r["cells"]:
                            for i in c["content"]:
                                if i["type"] == "paragraph": row_text += i["text"] + " "
                        
                        for day in days:
                            if day.lower() in row_text.lower() and len(row_text) < 50:
                                print(f"  Found '{day}' in Table {t_idx}, Row {r_idx}: [{row_text.strip()}]")
                                found_days.append(day)
            
            if not found_days:
                print("  No obvious day headers found in any table.")
                # Print first 2000 chars of full_text to see what's in there
                cursor.execute("SELECT full_text FROM original_lesson_plans WHERE id = ?", (row[0],))
                full_text = cursor.fetchone()[0]
                print(f"\nFull Text Snippet (first 1000 chars):\n{full_text[:1000]}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_ingestion()
