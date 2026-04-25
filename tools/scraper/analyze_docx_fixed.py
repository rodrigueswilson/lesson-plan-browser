from docx import Document
import os

path = r"d:\LP\reference_docs\scraped\3rd grade_unit 2_docx\Copy of Unit_2__Area_and_Multiplication.docx"
doc = Document(path)

print(f"Total w:p: {len(doc.element.xpath('//w:p'))}")
print(f"Total w:tbl: {len(doc.element.xpath('//w:tbl'))}")
print(f"Total w:sdt: {len(doc.element.xpath('//w:sdt'))}")

# Check body children
print("\nBody Children Tags:")
for child in doc.element.body:
    print(child.tag.split('}')[-1])

# Check if there are sdt elements in the body
sdt_elements = doc.element.xpath('./w:sdt', namespaces=doc.element.nsmap)
print(f"\nSDT at body level: {len(sdt_elements)}")

if sdt_elements:
    for i, sdt in enumerate(sdt_elements):
        content = sdt.xpath('.//w:sdtContent', namespaces=doc.element.nsmap)
        if content:
            print(f"SDT {i} Content Children:")
            for child in content[0]:
                print(f"  - {child.tag.split('}')[-1]}")
