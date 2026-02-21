import sqlite3
from pathlib import Path

def main():
    db_path = Path("d:/LP/data/lesson_planner.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"Scanning lesson_steps in {db_path} for 'Mock'...")
    
    query = "SELECT id, lesson_plan_id, step_name, display_content FROM lesson_steps"
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        mock_steps = []
        for row in rows:
            content = row['display_content'] or ""
            name = row['step_name'] or ""
            if "mock" in content.lower() or "mock" in name.lower():
                mock_steps.append(row)

        print(f"Found {len(mock_steps)} steps containing 'Mock':")
        for row in mock_steps:
            print(f" - Step ID: {row['id']}")
            print(f"   Plan ID: {row['lesson_plan_id']}")
            print(f"   Name: {row['step_name']}")
            print(f"   Content snippet: {str(row['display_content'])[:50]}...")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
