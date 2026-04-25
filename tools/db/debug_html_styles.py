import os

path = r'd:\LP\temp_u2\originals'
files = [x for x in os.listdir(path) if x.endswith('.html')]
if not files:
    print("No HTML found")
    exit()

full = os.path.join(path, files[0])
with open(full, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    
print(f"File size: {len(content)}")
print(f"Body at: {content.find('<body')}")
print(f"Style tag at: {content.find('<style')}")
print(f"Class count: {content.count('class=')}")
print(f"Style attr count: {content.count(' style=')}")
print(f"Example content near body start:")
body_start = content.find('<body')
if body_start != -1:
    print(content[body_start:body_start+500])
