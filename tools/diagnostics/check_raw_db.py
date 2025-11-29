"""
Check raw database to see what's actually stored for vocabulary_cognates.
"""
import sys
import sqlite3
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

db_path = Path("data/lesson_plans.db")
if not db_path.exists():
    print(f"[FAIL] Database not found: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Check vocabulary step
plan_id = "plan_20251122160826"
cursor.execute("""
    SELECT step_name, vocabulary_cognates, sentence_frames
    FROM lesson_steps
    WHERE lesson_plan_id = ? 
    AND day_of_week = 'monday' 
    AND slot_number = 1
    AND step_name LIKE '%Vocabulary%'
""", (plan_id,))

row = cursor.fetchone()
if row:
    step_name, vocab_raw, frames_raw = row
    print(f"Step: {step_name}")
    print(f"\nRaw vocabulary_cognates from DB (type: {type(vocab_raw)}):")
    print(f"  Value: {vocab_raw}")
    print(f"\nRaw sentence_frames from DB (type: {type(frames_raw)}):")
    print(f"  Value: {frames_raw}")
    
    # Try to parse as JSON
    import json
    if vocab_raw:
        try:
            vocab_parsed = json.loads(vocab_raw)
            print(f"\nParsed vocabulary_cognates: {type(vocab_parsed)} = {len(vocab_parsed) if isinstance(vocab_parsed, list) else vocab_parsed}")
        except:
            print(f"\n[FAIL] Cannot parse vocabulary_cognates as JSON")
    else:
        print(f"\n[FAIL] vocabulary_cognates is NULL in database")
    
    if frames_raw:
        try:
            frames_parsed = json.loads(frames_raw)
            print(f"\nParsed sentence_frames: {type(frames_parsed)} = {len(frames_parsed) if isinstance(frames_parsed, list) else frames_parsed}")
        except:
            print(f"\n[FAIL] Cannot parse sentence_frames as JSON")
    else:
        print(f"\n[FAIL] sentence_frames is NULL in database")
else:
    print("[FAIL] Vocabulary step not found in database")

conn.close()

