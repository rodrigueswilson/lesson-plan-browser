import re

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    
    # Search for LESSON 1
    for match in re.finditer(r'LESSON\s*1', content, re.IGNORECASE):
        # Snippet
        start = max(0, match.start() - 100)
        end = min(len(content), match.end() + 200)
        print(f"Found 'LESSON 1' at {match.start()}: ...{content[start:end]}...")
