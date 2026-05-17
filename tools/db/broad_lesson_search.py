import re
from bs4 import BeautifulSoup

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    soup = BeautifulSoup(f, 'html.parser')
    
    descendants = list(soup.descendants)
    for tag in soup.find_all(['p', 'span']):
        txt = tag.get_text().strip()
        if 'LESSON' in txt.upper():
            pos = descendants.index(tag) if tag in descendants else -1
            is_link = bool(tag.find('a') or tag.name == 'a' or tag.find_parent('a'))
            # Print only if it's NOT a link or if it looks interesting
            if not is_link or pos > 10000:
                 print(f"Found: pos={pos}, link={is_link}, text='{txt[:100]}'")
