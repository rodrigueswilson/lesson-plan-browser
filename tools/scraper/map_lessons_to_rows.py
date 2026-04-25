import json
import re

path = r'd:\LP\temp_u2\unit2_api_raw.json'
with open(path, 'r', encoding='utf-8') as f:
    doc = json.load(f)

# Content is in Tab 0
tab = doc['tabs'][0]
doc_tab = tab.get('documentTab', {})
content = doc_tab.get('body', {}).get('content', [])

table = None
for el in content:
    if 'table' in el:
        table = el['table']
        break

if not table:
    print("Table not found.")
    exit()

rows = table.get('tableRows', [])
lesson_markers = []

def get_text_from_row(row):
    text = ""
    for cell in row.get('tableCells', []):
        for content_chunk in cell.get('content', []):
            if 'paragraph' in content_chunk:
                for element in content_chunk['paragraph'].get('elements', []):
                    if 'textRun' in element:
                        text += element['textRun'].get('content', "")
    return text.strip()

# Scan for LESSON X
for i, row in enumerate(rows):
    txt = get_text_from_row(row)
    # Match "LESSON X" at the start of a cell
    match = re.search(r'^LESSON\s*(\d+)', txt, re.IGNORECASE)
    if match:
        l_num = int(match.group(1))
        # Check if it's the real section and not a TOC
        # Heuristic: TOC has links, but let's just look at the density later
        lesson_markers.append({'row': i, 'num': l_num, 'text': txt})

print(f"Found {len(lesson_markers)} markers.")

# Final Deduplication: For each lesson number, the one with the MOST content after it wins
lesson_segments = {}
for i, marker in enumerate(lesson_markers):
    num = marker['num']
    start_row = marker['row']
    # End row is either the next marker's row or end of table
    end_row = lesson_markers[i+1]['row'] if i+1 < len(lesson_markers) else len(rows)
    payload = end_row - start_row
    
    if num not in lesson_segments or payload > lesson_segments[num]['payload']:
        lesson_segments[num] = {
            'start': start_row,
            'end': end_row,
            'payload': payload,
            'text': marker['text']
        }

# Print Final Map
for num in sorted(lesson_segments.keys()):
    seg = lesson_segments[num]
    print(f"Lesson {num}: Rows {seg['start']} to {seg['end']} (Payload: {seg['payload']})")
    
# Save Map for the segmenter
with open(r'd:\LP\temp_u2\unit2_row_map.json', 'w') as f:
    json.dump(lesson_segments, f, indent=2)
