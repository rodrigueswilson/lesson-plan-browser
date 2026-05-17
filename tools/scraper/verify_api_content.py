import json

path = r'd:\LP\temp_u2\unit2_api_raw.json'
with open(path, 'r', encoding='utf-8') as f:
    doc = json.load(f)

# Convert to string for broad search
s = json.dumps(doc)

print(f"Total Length: {len(s)}")
print(f"Index of '2.OA': {s.find('2.OA')}")
print(f"Index of 'WHAT IS AREA': {s.find('WHAT IS AREA')}")
print(f"Index of 'LESSON 1': {s.find('LESSON 1')}")

# Check first 1000 chars of tab 0 text
if 'tabs' in doc:
    tab = doc['tabs'][0]
    content = tab.get('documentTab', {}).get('body', {}).get('content', [])
    text = ""
    for el in content[:50]: # First 50 elements
        if 'paragraph' in el:
            for seg in el['paragraph'].get('elements', []):
                if 'textRun' in seg:
                    text += seg['textRun'].get('content', "")
    print(f"First 500 chars of text: {text[:500]}")
