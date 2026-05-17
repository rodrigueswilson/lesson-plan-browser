import re
from bs4 import BeautifulSoup

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    soup = BeautifulSoup(f, 'html.parser')
    
    markers = []
    # Simplified version of extract_curriculum.py logic
    for l_num in range(1, 16):
        pattern = re.compile(rf'^\s*LESSON\s*{l_num}\b', re.IGNORECASE)
        for tag in soup.find_all(['p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if pattern.match(tag.get_text()):
                markers.append({
                    'num': l_num,
                    'tag_text': tag.get_text().strip()[:50],
                    'pos': list(soup.descendants).index(tag) if tag in soup.descendants else 0,
                    'is_link': bool(tag.find('a') or (tag.name == 'a'))
                })
                # No break here, find all occurrences
                
    # Sort and Print
    markers.sort(key=lambda x: x['pos'])
    for m in markers:
        print(m)
