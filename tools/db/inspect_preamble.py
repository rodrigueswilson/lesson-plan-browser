import re

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    # Find start of body
    body_match = re.search(r'<body[^>]*>', content)
    if body_match:
        start = body_match.end()
        print(content[start:start+10000])
    else:
        print("Body not found.")
