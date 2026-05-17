import json
import sqlite3
import re
import uuid

path = r'd:\LP\temp_u2\unit2_api_raw.json'
db_path = r'd:\LP\data\curriculum.db'

with open(path, 'r', encoding='utf-8') as f:
    doc = json.load(f)

# Get table rows from Tab 1
content = doc['tabs'][0]['documentTab']['body']['content']
table = None
for el in content:
    if 'table' in el:
        table = el['table']
        break

if not table:
    print("Table not found.")
    exit()

rows = table.get('tableRows', [])

def cell_to_html(cell):
    html = ""
    for content_chunk in cell.get('content', []):
        if 'paragraph' in content_chunk:
            p_html = "<p>"
            for element in content_chunk['paragraph'].get('elements', []):
                if 'textRun' in element:
                    txt = element['textRun'].get('content', "").replace('\n', '<br>')
                    # Basic styles: bold, italic
                    style = element['textRun'].get('textStyle', {})
                    if style.get('bold'): txt = f"<b>{txt}</b>"
                    if style.get('italic'): txt = f"<i>{txt}</i>"
                    p_html += txt
            p_html += "</p>"
            html += p_html
    return html

def row_to_html(row):
    html = "<div class='row' style='display:flex; border-bottom:1px solid #eee; padding:5px;'>"
    for cell in row.get('tableCells', []):
        html += f"<div class='cell' style='flex:1; padding:5px;'>{cell_to_html(cell)}</div>"
    html += "</div>"
    return html

# 1. Lesson 1 is Rows 57 to 64
l1_html = ""
for i in range(57, 65):
    l1_html += row_to_html(rows[i])

print(f"Generated {len(l1_html)} bytes of HTML for Lesson 1.")

# 2. Insert into DB (Test only for Lesson 1)
conn = sqlite3.connect(db_path)
c = conn.cursor()
unit_id = 'Math_3_U2_1hBoK4uk'
lesson_id = unit_id + '_L1'

# Update procedure_html
c.execute("UPDATE lessons SET procedure_html = ? WHERE id = ?", (l1_html, lesson_id))
conn.commit()
print(f"Updated Lesson 1 in database: {lesson_id}")
conn.close()
