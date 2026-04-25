import sys
from docx import Document
import re

def explore_unit_1(docx_path):
    doc = Document(docx_path)
    lesson_pattern = re.compile(r"LESSON\s+(\d+)", re.IGNORECASE)
    
    print(f"Exploratory Analysis of Unit 1: {docx_path}")
    print("-" * 50)
    
    found_lessons = 0
    for i, table in enumerate(doc.tables):
        first_cell_text = table.rows[0].cells[0].text.strip()
        if lesson_pattern.search(first_cell_text):
            found_lessons += 1
            print(f"Table {i} - Lesson Header: '{first_cell_text[:50]}'")
            print(f"  Rows: {len(table.rows)}")
            # Print first 5 rows' cell counts and content snippets
            for r_idx, row in enumerate(table.rows[:8]):
                unique_cells = []
                for c in row.cells:
                    if c not in unique_cells: unique_cells.append(c)
                
                cell_contents = [c.text.strip().replace('\n', ' ')[:30] for c in unique_cells]
                print(f"    Row {r_idx+1}: {len(unique_cells)} cells - {cell_contents}")
            print("-" * 20)
            if found_lessons >= 3: break # Just check first 3

if __name__ == "__main__":
    path = r"D:\LP\reference_docs\scraped\Unit_1__Introducing_Multiplication\originals\Unit_1__Introducing_Multiplication.docx"
    explore_unit_1(path)
