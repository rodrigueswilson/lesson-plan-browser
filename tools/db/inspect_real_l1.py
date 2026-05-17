import re

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    # Find the TOC and then skip it
    body_match = re.search(r'<body[^>]*>', content)
    if body_match:
        # Search for "LESSON 1" text after removing HTML tags temporary or just look for the text in the raw string
        # But raw string has many tags inside words.
        # Let's search for "LESSON" and "WHAT IS AREA" separately
        pos = content.find('WHAT IS AREA')
        if pos != -1:
            print(f"Found 'WHAT IS AREA' at byte pos {pos}")
            print(content[pos-500:pos+1000])
        else:
            print("String not found.")
