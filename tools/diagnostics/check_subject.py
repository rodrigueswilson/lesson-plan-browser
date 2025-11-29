from docx import Document

doc = Document(r'd:\LP\input\Lang Lesson Plans 9_15_25-9_19_25.docx')

print("Scanning for subject fields in metadata tables...")
for i, table in enumerate(doc.tables):
    print(f"\n=== Table {i} ===")
    for row_idx, row in enumerate(table.rows):
        for cell_idx, cell in enumerate(row.cells):
            text = cell.text.strip()
            if text and ('subject' in text.lower() or 'name:' in text.lower() or 'grade' in text.lower()):
                print(f"  Row {row_idx}, Cell {cell_idx}: {text[:150]}")
