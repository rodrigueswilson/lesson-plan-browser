
import sqlite3
import json
import re
from pathlib import Path

def check_vocab_links():
    db_path = Path("data/lesson_planner.db")
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    total_vocab_items = 0
    vocab_with_links = 0
    overlapping_links = 0

    # Check weekly_plans table first (the source of truth for the JSON)
    cursor.execute("SELECT lesson_json FROM weekly_plans")
    plans = cursor.fetchall()
    
    for plan in plans:
        try:
            data = json.loads(plan['lesson_json'])
            days = data.get('days', {})
            for day_name, day_data in days.items():
                if not isinstance(day_data, dict): continue
                
                vocab_list = day_data.get('vocabulary_cognates', [])
                vocab_words = []
                for item in vocab_list:
                    english = item.get('english', '')
                    total_vocab_items += 1
                    vocab_words.append(english.lower())
                    if '[' in english or '(' in english:
                        print(f"DEBUG: Found possible link in vocab list: {english}")
                        vocab_with_links += 1

                day_json_str = json.dumps(day_data)
                for match in link_pattern.finditer(day_json_str):
                    label = match.group(1).lower()
                    for v in vocab_words:
                        if v and (v in label or label in v):
                            print(f"DEBUG: Found overlap! Vocab: '{v}', Link Label: '{match.group(1)}'")
                            overlapping_links += 1
        except:
            pass

    # Also check lesson_steps table
    cursor.execute("SELECT display_content, vocabulary_cognates FROM lesson_steps")
    steps = cursor.fetchall()
    for step in steps:
        display_content = step['display_content'] or ''
        vocab_json = step['vocabulary_cognates']
        
        vocab_words = []
        if vocab_json:
            try:
                vocab_list = json.loads(vocab_json) if isinstance(vocab_json, str) else vocab_json
                for item in vocab_list:
                    english = item.get('english', '')
                    total_vocab_items += 1
                    vocab_words.append(english.lower())
                    if '[' in english or '(' in english:
                        print(f"DEBUG: Found possible link in vocab list (step): {english}")
                        vocab_with_links += 1
            except:
                pass

        for match in link_pattern.finditer(display_content):
            label = match.group(1).lower()
            for v in vocab_words:
                if v and (v in label or label in v):
                    print(f"DEBUG: Found overlap in step! Vocab: '{v}', Link Label: '{match.group(1)}'")
                    overlapping_links += 1

    print(f"\nResults:")
    print(f"Total vocabulary items checked: {total_vocab_items}")
    print(f"Vocabulary items containing link syntax: {vocab_with_links}")
    print(f"Occurrences of vocabulary words overlapping with link labels: {overlapping_links}")

    conn.close()

if __name__ == "__main__":
    check_vocab_links()
