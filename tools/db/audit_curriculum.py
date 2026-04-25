import sqlite3
import json

def audit():
    conn = sqlite3.connect(r"d:\LP\data\curriculum.db")
    c = conn.cursor()
    
    # 1. Lesson Content Audit
    c.execute("SELECT COUNT(*) FROM lessons")
    total_lessons = c.fetchone()[0]
    
    col_blanks = {}
    for col in ['learning_intentions', 'daily_instructional_task', 'success_criteria', 'essential_questions']:
        c.execute(f"SELECT COUNT(*) FROM lessons WHERE {col} IS NULL OR {col} = '' OR {col} = '[]' OR {col} = '\"[]\"'")
        col_blanks[col] = c.fetchone()[0]
        
    print(f"--- DATABASE AUDIT ---")
    print(f"Total Lessons: {total_lessons}")
    for col, count in col_blanks.items():
        percent = (count / total_lessons) * 100 if total_lessons > 0 else 0
        status = "✅ PASS" if percent < 20 else "❌ FAIL"
        print(f"{col:25}: {total_lessons - count:4} / {total_lessons:4} ({100-percent:5.1f}%) {status}")

    # 2. Vocabulary Audit
    c.execute("SELECT COUNT(*) FROM vocabulary_items")
    total_vocab = c.fetchone()[0]
    print(f"Total Vocabulary Terms: {total_vocab}")
    
    # 3. Unit Intro Audit
    c.execute("SELECT COUNT(*) FROM units_intro")
    total_intros = c.fetchone()[0]
    print(f"Total Unit Intros: {total_intros}")
    
    conn.close()

if __name__ == "__main__":
    audit()
