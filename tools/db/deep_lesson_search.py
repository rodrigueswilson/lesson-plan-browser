import re
from bs4 import BeautifulSoup

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    soup = BeautifulSoup(f, 'html.parser')
    
    descendants = list(soup.descendants)
    # Search EVERYTHING
    for tag in soup.find_all(True):
        if tag.name in ['script', 'style']: continue
        txt = tag.get_text().strip()
        if 'LESSON 1:' in txt.upper() and len(txt) < 200:
            pos = descendants.index(tag) if tag in descendants else -1
            is_link = bool(tag.find('a') or tag.name == 'a' or tag.find_parent('a'))
            print(f"Found tag <{tag.name}> at pos={pos}, link={is_link}, text='{txt}'")
