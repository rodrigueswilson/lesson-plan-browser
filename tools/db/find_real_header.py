import re

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    
    # Search for "1: WHAT IS AREA"
    for match in re.finditer(r'1:\s*WHAT IS AREA', content, re.IGNORECASE):
        start = max(0, match.start() - 100)
        end = min(len(content), match.end() + 200)
        print(f"Found '1: WHAT IS AREA' at {match.start()}: ...{content[start:end]}...")
