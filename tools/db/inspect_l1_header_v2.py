from bs4 import BeautifulSoup
import re

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    f.seek(4250000)
    chunk = f.read(100000)
    soup = BeautifulSoup(chunk, 'html.parser')
    for tag in soup.find_all(True):
        txt = tag.get_text().strip()
        if 'LESSON 1' in txt.upper() and len(txt) < 100:
            print(f"Tag: <{tag.name}>, Attrs: {tag.attrs}, Text: '{txt}'")
