"""
Check the lesson JSON in the database for recent Wilson and Daniela lesson plans.
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = r'd:\LP\data\lesson_plans.db'

def check_recent_lessons():
    """Check recent lesson plans in database."""
    
    print("="*80)
    print("CHECKING LESSON JSON IN DATABASE")
    print("="*80)
    print()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get recent weekly plans
        cursor.execute("""
            SELECT id, user_id, week_of, generated_at, output_file, status
            FROM weekly_plans
            ORDER BY generated_at DESC
            LIMIT 10
        """)
        
        lessons = cursor.fetchall()
        
        print(f"Found {len(lessons)} recent lesson plans:")
        print()
        
        for i, (plan_id, user_id, week_of, generated_at, output_file, status) in enumerate(lessons, 1):
            print(f"{i}. ID: {plan_id}")
            print(f"   User: {user_id}")
            print(f"   Week: {week_of}")
            print(f"   Generated: {generated_at}")
            print(f"   Output: {output_file}")
            print(f"   Status: {status}")
            
            # Note: Lesson JSON is not stored in DB, it's generated on-the-fly
            # The output file is the rendered DOCX
            # We need to check if hyperlinks were passed to the renderer
            
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    check_recent_lessons()
