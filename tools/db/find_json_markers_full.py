import json

def walk_json(obj, markers, in_table=False):
    if isinstance(obj, dict):
        if 'paragraph' in obj:
            p = obj['paragraph']
            text = "".join([t.get('textRun', {}).get('content', '') for t in p.get('elements', []) if 'textRun' in t])
            if 'LESSON ' in text.upper() and (':' in text or '--' in text):
                markers.append({
                    'text': text.strip(),
                    'headingId': p.get('paragraphStyle', {}).get('headingId'),
                    'startIndex': obj.get('startIndex'),
                    'in_table': in_table
                })
        for k, v in obj.items():
            walk_json(v, markers, in_table or k == 'table')
    elif isinstance(obj, list):
        for v in obj:
            walk_json(v, markers, in_table)

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
    markers = []
    walk_json(data, markers)
    for m in markers:
        print(m)
