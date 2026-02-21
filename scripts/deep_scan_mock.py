import sqlite3
import json
from pathlib import Path

def main():
    db_path = Path("d:/LP/data/lesson_planner.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"Deep scanning {db_path} for any 'Mock' content...")
    
    query = "SELECT id, week_of, CAST(lesson_json as TEXT) as json_str, generated_at FROM weekly_plans"
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        mock_candidates = []
        
        for row in rows:
            json_str = row['json_str']
            # converting to lower to be case insensitive, though 'Mock' is usually Title Case
            if "mock" in json_str.lower():
                # Filter out false positives if any (unlikely in this context but possible)
                # Let's inspect context
                
                # Check specific keys if possible, or just print it
                mock_candidates.append(row)

        print(f"Found {len(mock_candidates)} plans containing 'mock' (case-insensitive):")
        
        for row in mock_candidates:
            print(f"\nPLAN ID: {row['id']}")
            print(f"Week: {row['week_of']}")
            print(f"Generated: {row['generated_at']}")
            
            # Print a snippet where 'mock' appears
            json_str = row['json_str']
            idx = json_str.lower().find("mock")
            start = max(0, idx - 50)
            end = min(len(json_str), idx + 100)
            snippet = json_str[start:end].replace("\n", " ")
            print(f"Snippet: ...{snippet}...")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
