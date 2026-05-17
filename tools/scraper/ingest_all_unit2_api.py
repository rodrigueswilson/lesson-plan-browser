import json
import sqlite3
import re

path = r'd:\LP\temp_u2\unit2_api_raw.json'
db_path = r'd:\LP\data\curriculum.db'

with open(path, 'r', encoding='utf-8') as f:
    doc = json.load(f)

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
            p_html = "<p>"
            for element in chunk['paragraph'].get('elements', []):
                if 'textRun' in element:
                    txt = element['textRun'].get('content', "").replace('\n', '<br>')
                    style = element['textRun'].get('textStyle', {})
                    if style.get('bold'): txt = f"<b>{txt}</b>"
                    if style.get('italic'): txt = f"<i>{txt}</i>"
                    p_html += txt
            p_html += "</p>"
            html += p_html
    return html

def row_to_html(row):
    html = "<div class='row' style='display:flex; border-bottom:1px solid #eee; padding:5px;'>"
    cells = row.get('tableCells', [])
    for cell in cells:
        html += f"<div class='cell' style='flex:1; padding:5px;'>{cell_to_html(cell)}</div>"
    html += "</div>"
    return html

# 1. Map Lessons (from Row 57 onwards, 8 rows each)
lesson_map = {i: (57 + (i-1)*8, 57 + i*8) for i in range(1, 16)}

conn = sqlite3.connect(db_path)
c = conn.cursor()
unit_id = 'Math_3_U2_1hBoK4uk'

# 2. Extract Unit Overview (Rows 0 to 56)
overview_html = ""
for i in range(0, 57):
    overview_html += row_to_html(rows[i])
c.execute("UPDATE units_intro SET procedure_html = ? WHERE unit_id = ?", (overview_html, unit_id))
print(f"Updated Unit Overview: {len(overview_html)} bytes")

# 3. Extract each Lesson
for l_num, (start, end) in lesson_map.items():
    lesson_html = ""
    for i in range(start, end):
        lesson_html += row_to_html(rows[i])
    
    lesson_id = f"{unit_id}_L{l_num}"
    # Verify lesson exists
    c.execute("SELECT id FROM lessons WHERE id = ?", (lesson_id,))
    if c.fetchone():
        c.execute("UPDATE lessons SET procedure_html = ?, narrative_html = '' WHERE id = ?", (lesson_html, lesson_id))
        print(f"Updated Lesson {l_num}: {len(lesson_html)} bytes")
    else:
        # Insert if missing
        c.execute("INSERT INTO lessons (id, unit_id, lesson_number, procedure_html, narrative_html) VALUES (?, ?, ?, ?, ?)",
                  (lesson_id, unit_id, l_num, lesson_html, ""))
        print(f"Inserted Lesson {l_num}: {len(lesson_html)} bytes")

conn.commit()
conn.close()
print("All matches for Grade 3 Math Unit 2 updated from API JSON.")
