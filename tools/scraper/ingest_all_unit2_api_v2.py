import json
import sqlite3
import re

path = r'd:\LP\temp_u2\unit2_api_raw.json'
db_path = r'd:\LP\data\curriculum.db'

with open(path, 'r', encoding='utf-8') as f:
    doc = json.load(f)

# Find the main table in Tab 0
content = doc['tabs'][0]['documentTab']['body']['content']
table = None
for el in content:
    if 'table' in el:
        table = el['table']
        break
rows = table.get('tableRows', [])

def cell_to_html(cell):
    html = ""
    for chunk in cell.get('content', []):
        if 'paragraph' in chunk:
            p_html = "<p style='margin:4px 0;'>"
            for element in chunk['paragraph'].get('elements', []):
                if 'textRun' in element:
                    txt = element['textRun'].get('content', "").replace('\n', '<br>')
                    style = element['textRun'].get('textStyle', {})
                    if style.get('bold'): txt = f"<b>{txt}</b>"
                    if style.get('italic'): txt = f"<i>{txt}</i>"
                    if style.get('underline'): txt = f"<u>{txt}</u>"
                    p_html += txt
            p_html += "</p>"
            html += p_html
    return html

def row_to_html(row):
    cells = row.get('tableCells', [])
    html = "<tr>"
    for cell in cells:
        html += f"<td style='border:1px solid #ddd; padding:8px; vertical-align:top;'>{cell_to_html(cell)}</td>"
    html += "</tr>"
    return html

def extract_section_html(start_row, end_row):
    html = "<div style='overflow-x:auto; margin:10px 0;'>"
    html += "<table style='border-collapse:collapse; width:100%; min-width:800px; font-size:14px;'>"
    for i in range(start_row, end_row):
        html += row_to_html(rows[i])
    html += "</table></div>"
    return html

def get_row_text(row):
    text = ""
    for cell in row.get('tableCells', []):
        for chunk in cell.get('content', []):
            if 'paragraph' in chunk:
                for el in chunk['paragraph'].get('elements', []):
                    if 'textRun' in el:
                        text += el['textRun'].get('content', "")
    return text.strip()

# 1. Map Lessons (Rows 57 onwards, 8 rows each)
# Only 15 lessons in this unit
lesson_map = {i: (57 + (i-1)*8, 57 + i*8) for i in range(1, 16)}

conn = sqlite3.connect(db_path)
c = conn.cursor()
unit_id = 'Math_3_U2_1hBoK4uk'

# 2. Extract Unit Overview (Rows 0-56)
overview_html = extract_section_html(0, 57)
c.execute("UPDATE units_intro SET procedure_html = ? WHERE unit_id = ?", (overview_html, unit_id))
print(f"Updated Overview: {len(overview_html)} bytes")

# 3. Process Lessons
for l_num, (start, end) in lesson_map.items():
    # Extract Title from the first row of the window
    header_text = get_row_text(rows[start])
    # Match "LESSON X: TITLE" or similar
    title_match = re.search(r'LESSON\s*\d+[:\s]*(.*)', header_text, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else f"Lesson {l_num}"
    if not title: title = f"Lesson {l_num}"
    
    lesson_html = extract_section_html(start, end)
    lesson_id = f"{unit_id}_L{l_num}"
    
    c.execute("UPDATE lessons SET title = ?, procedure_html = ?, narrative_html = '' WHERE id = ?", 
              (title, lesson_html, lesson_id))
    print(f"Updated Lesson {l_num}: {title} ({len(lesson_html)} bytes)")

# 4. Clean up the "Lesson 23" and other orphans for this unit
c.execute(
    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='science_lesson_day_segments'"
)
if c.fetchone():
    c.execute(
        "DELETE FROM science_lesson_day_segments WHERE lesson_id IN "
        "(SELECT id FROM lessons WHERE unit_id = ? AND lesson_number > 15)",
        (unit_id,),
    )
c.execute("DELETE FROM lessons WHERE unit_id = ? AND lesson_number > 15", (unit_id,))
print("Cleaned up orphaned lessons (>15).")

conn.commit()
conn.close()
print("High-Fidelity V2 Ingestion Complete.")
