from bs4 import BeautifulSoup
import os

path = r'd:\LP\temp_u2\originals\Unit_2__Area_and_Multiplication.html'
with open(path, 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f, 'html.parser')

tables = soup.find_all('table')
print(f"HTML has {len(tables)} tables.")

if tables:
    main_table = tables[0]
    rows = main_table.find_all('tr')
    print(f"Main Table has {len(rows)} rows.")
    
    # Check Lesson 1 row (expecting Row 57 to have 'LESSON 1: WHAT IS AREA?')
    if len(rows) > 57:
        l1_row = rows[57]
        print(f"Row 57 text: {l1_row.get_text().strip()[:100]}")
