from bs4 import BeautifulSoup
import re

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.html'
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    soup = BeautifulSoup(f, 'html.parser')
    
    lessons = []
    # Search for anything starting with LESSON
    for tag in soup.find_all(['p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = tag.get_text().strip().upper()
        if re.match(r'^LESSON\s*\d+', text):
            lessons.append({
                'tag': tag.name,
                'id': tag.get('id'),
                'class': tag.get('class'),
                'text': text[:100]
            })
            
    for l in lessons:
        print(l)
