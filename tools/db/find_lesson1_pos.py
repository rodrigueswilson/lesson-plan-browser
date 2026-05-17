import re
from bs4 import BeautifulSoup

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    soup = BeautifulSoup(f, 'html.parser')
    
    markers = []
    # Find all "LESSON 1" and print their POS and whether they are links
    pattern = re.compile(rf'^\s*LESSON\s*1\b', re.IGNORECASE)
    descendants = list(soup.descendants)
    for tag in soup.find_all(['p', 'span']):
        if pattern.match(tag.get_text()):
            pos = descendants.index(tag) if tag in descendants else -1
            is_link = bool(tag.find('a') or tag.name == 'a' or tag.find_parent('a'))
            print(f"LESSON 1 Found: pos={pos}, is_link={is_link}, text='{tag.get_text().strip()[:50]}'")
