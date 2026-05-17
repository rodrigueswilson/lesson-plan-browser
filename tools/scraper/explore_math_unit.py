import sys
from docx import Document
import re

def explore_math_unit(docx_path):
    try:
        doc = Document(docx_path)
    except Exception as e:
        print(f"Error opening {docx_path}: {e}")
        return

    lesson_pattern = re.compile(r"LESSON\s+(\d+)", re.IGNORECASE)
    
    print(f"Exploratory Analysis: {docx_path}")
    print("-" * 50)
    
    found_lessons = 0
    for i, table in enumerate(doc.tables):
        # Look for "LESSON" in the first 2 rows to identify a lesson table
        is_lesson = False
        for r in table.rows[:2]:
            for c in r.cells:
                if lesson_pattern.search(c.text):
                    is_lesson = True
                    break
            if is_lesson: break
            
        if is_lesson:
            found_lessons += 1
            print(f"Table {i} - Lesson Table Found")
            print(f"  Rows: {len(table.rows)}")
            for r_idx, row in enumerate(table.rows[:8]):
                unique_cells = []
                for c in row.cells:
                    if c not in unique_cells: unique_cells.append(c)
                
                cell_contents = [c.text.strip().replace('\n', ' ')[:40] for c in unique_cells]
                print(f"    Row {r_idx+1}: {len(unique_cells)} cells - {cell_contents}")
            print("-" * 20)
            if found_lessons >= 2: break # Check first 2

if __name__ == "__main__":
    if len(sys.argv) > 1:
        explore_math_unit(sys.argv[1])
    else:
        print("Usage: python explore_math_unit.py <path_to_docx>")
