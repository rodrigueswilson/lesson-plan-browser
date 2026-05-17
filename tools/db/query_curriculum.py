import sqlite3
import json
import sys

def query_lesson(lesson_id: str):
    db_path = "d:\\LP\\data\\curriculum.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 1. Get Lesson Details
    c.execute("SELECT title, learning_intentions FROM lessons WHERE id = ?", (lesson_id,))
    lesson = c.fetchone()
    if not lesson:
        print(f"Lesson {lesson_id} not found.")
        return
    
    print(f"--- LESSON: {lesson[0]} ---")
    print(f"Objectives: {lesson[1]}")
    
    # 2. Get Standards
    c.execute("""
        SELECT s.code, s.description 
        FROM lesson_standards ls 
        JOIN standards s ON ls.standard_code = s.code 
        WHERE ls.lesson_id = ?
    """, (lesson_id,))
    standards = c.fetchall()
    print("\nSTANDARDS:")
    for code, desc in standards:
        print(f"  [{code}] {desc[:100]}...")
        
    # 3. Get Vocabulary with Level 1 Definitions
    c.execute("""
        SELECT v.term, v.level_1_def 
        FROM lesson_vocabulary lv 
        JOIN vocabulary v ON lv.vocab_id = v.id 
        WHERE lv.lesson_id = ?
    """, (lesson_id,))
    vocab = c.fetchall()
    print("\nVOCABULARY (Level 1):")
    for term, def1 in vocab:
        print(f"  {term}: {def1}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_lesson(sys.argv[1])
    else:
        # Default to Lesson 1 of Math Unit 1
        query_lesson("13jAzcMR9KqRj3P9rvgySxPWysPAGBh9GsftzT3sw8fg_L1")
