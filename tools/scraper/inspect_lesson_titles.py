import json
import re

path = r'd:\LP\temp_u2\unit2_api_raw.json'
with open(path, 'r', encoding='utf-8') as f:
    doc = json.load(f)

table = doc['tabs'][0]['documentTab']['body']['content'][0]['table']
rows = table.get('tableRows', [])

def get_row_text(row):
    text = ""
    for cell in row.get('tableCells', []):
        for chunk in cell.get('content', []):
            if 'paragraph' in chunk:
                for el in chunk['paragraph'].get('elements', []):
                    if 'textRun' in el:
                        text += el['textRun'].get('content', "")
    return text.strip()

for i, row in enumerate(rows):
    txt = get_row_text(row)
    if 'LESSON' in txt.upper():
        print(f"Row {i}: {txt[:100]}")
