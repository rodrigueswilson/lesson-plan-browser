import json

path = r'd:\LP\temp_u2\unit2_api_raw.json'
with open(path, 'r', encoding='utf-8') as f:
    doc = json.load(f)

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
row = rows[57]
print(f"Row 57 has {len(row.get('tableCells', []))} cells.")
for i, cell in enumerate(row.get('tableCells', [])):
    cell_text = ""
    for content in cell.get('content', []):
        if 'paragraph' in content:
            for el in content['paragraph'].get('elements', []):
                if 'textRun' in el:
                    cell_text += el['textRun'].get('content', "")
    print(f"  Cell {i}: {cell_text.strip()[:200]}")
