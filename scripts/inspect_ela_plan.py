import sqlite3
import json
from pathlib import Path

def main():
    db_path = Path("d:/LP/data/lesson_planner.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"Searching for ELA plan in week 01-05-01-09...")
    
    # Broad search for ELA in that week
    query = """
        SELECT id, week_of, lesson_json, generated_at 
        FROM weekly_plans 
        WHERE week_of LIKE '%01-05%' 
          AND (lesson_json LIKE '%ELA%' OR lesson_json LIKE '%English%')
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    found = False
    for row in rows:
        data = json.loads(row['lesson_json'])
        # Check Grade 3
        if data.get('metadata', {}).get('grade') != '3':
            continue
            
        print(f"\nFound Candidate Plan: {row['id']}")
        print(f"Week: {row['week_of']}")
        
        # Check Thursday
        days = data.get('days', {})
        thursday = days.get('thursday', {})
        if not thursday:
            print(" - Thursday is empty")
            continue
            
        # Check times or content
        print(f" - Thursday Unit/Lesson: {thursday.get('unit_lesson', 'N/A')}")
        
        obj = thursday.get('objective', {})
        print(f" - Student Goal: {obj.get('student_goal', 'N/A')}")
        print(f" - WIDA: {obj.get('wida_objective', 'N/A')}")
        
        has_mock = "mock" in str(thursday).lower()
        print(f" - Contains 'mock' (case-insensitive): {has_mock}")
        found = True

    if not found:
        print("\nNo ELA Grade 3 plan found for week 01-05-01-09.")

    conn.close()

if __name__ == "__main__":
    main()
