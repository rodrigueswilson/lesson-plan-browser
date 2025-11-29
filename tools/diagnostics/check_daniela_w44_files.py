from docx import Document
import os

folder = r"F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W44"

print(f"Checking files in: {folder}\n")

for filename in os.listdir(folder):
    if filename.endswith('.docx') and not filename.startswith('~$'):
        filepath = os.path.join(folder, filename)
        print(f"=== {filename} ===")
        
        try:
            doc = Document(filepath)
            
            # Check first few tables for metadata
            for i, table in enumerate(doc.tables[:3]):
                for row in table.rows:
                    for cell in row.cells:
                        text = cell.text.strip()
                        if 'subject' in text.lower() or 'name:' in text.lower():
                            print(f"  Table {i}: {text[:100]}")
        except Exception as e:
            print(f"  Error: {e}")
        
        print()
