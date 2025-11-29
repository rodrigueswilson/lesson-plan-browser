
import sqlite3
import json
import os
from pathlib import Path

def verify_db():
    db_path = Path("data/lesson_planner.db")
    if not db_path.exists():
        if Path("../data/lesson_planner.db").exists():
            db_path = Path("../data/lesson_planner.db")
            
    print(f"Verifying database at {db_path}...")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    plan_id = 'plan_20251122160826'
    
    cursor.execute("""
        SELECT step_name, content_type, vocabulary_cognates, sentence_frames, display_content 
        FROM lesson_steps 
        WHERE lesson_plan_id = ? AND day_of_week = 'monday' AND slot_number = 1 
        AND (step_name LIKE '%Vocabulary%' OR content_type = 'sentence_frames')
    """, (plan_id,))
    
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"\nStep: {row['step_name']}")
        print(f"Type: {row['content_type']}")
        
        vocab = row['vocabulary_cognates']
        print(f"Vocabulary Cognates (Raw): {vocab}")
        if vocab:
            try:
                parsed = json.loads(vocab)
                print(f"Vocabulary Cognates (Parsed): {len(parsed)} items")
            except:
                print("Vocabulary Cognates: Not valid JSON")
                
        frames = row['sentence_frames']
        print(f"Sentence Frames (Raw): {frames}")
        if frames:
            try:
                parsed = json.loads(frames)
                print(f"Sentence Frames (Parsed): {len(parsed)} items")
            except:
                print("Sentence Frames: Not valid JSON")
                
        content = row['display_content']
        print(f"Display Content: {content[:100]}..." if content else "Display Content: None")

    conn.close()

if __name__ == "__main__":
    verify_db()
