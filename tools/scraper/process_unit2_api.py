import json

path = r'd:\LP\temp_u2\unit2_api_raw.json'
with open(path, 'r', encoding='utf-8') as f:
    doc = json.load(f)

# The content is in body.content
content = doc.get('body', {}).get('content', [])

print(f"Total StructuralElements: {len(content)}")

# Find the giant table
table = None
for el in content:
    if 'table' in el:
        table = el['table']
        break

if not table:
    print("No table found in the main content.")
    exit()

print(f"Main Table has {len(table.get('tableRows', []))} rows.")

# Scan rows for Lesson markers
lesson_map = []
for i, row in enumerate(table.get('tableRows', [])):
    row_text = ""
    for cell in row.get('tableCells', []):
        for content_chunk in cell.get('content', []):
            if 'paragraph' in content_chunk:
                for element in content_chunk['paragraph'].get('elements', []):
                    if 'textRun' in element:
                        row_text += element['textRun'].get('content', "")
    
    # Check for LESSON X
    import re
    match = re.search(r'LESSON\s*(\d+)', row_text, re.IGNORECASE)
    if match:
        l_num = int(match.group(1))
        # Exclude TOC links (TOC is usually at the start, check if it's a heading style if possible)
        print(f"Row {i}: Found {row_text.strip()[:100]} (Lesson {l_num})")
        lesson_map.append({'row': i, 'num': l_num, 'text': row_text.strip()})

# Verify spacing between lessons
for i in range(len(lesson_map)-1):
    diff = lesson_map[i+1]['row'] - lesson_map[i]['row']
    print(f"Lesson {lesson_map[i]['num']} -> {lesson_map[i+1]['num']}: {diff} rows")
