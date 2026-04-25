from docx import Document
from lxml import etree

path = r"d:\LP\reference_docs\scraped\3rd grade_unit 2_docx\Copy of Unit_2__Area_and_Multiplication.docx"
doc = Document(path)

# Define namespaces
nsmap = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'
}

print(f"Total elements: {len(list(doc.element.body.iter()))}")

# Look for AlternateContent
alt_content = doc.element.xpath('//mc:AlternateContent', namespaces=nsmap)
print(f"Total mc:AlternateContent: {len(alt_content)}")

if alt_content:
    for i, alt in enumerate(alt_content[:5]):
        choices = alt.xpath('.//mc:Choice', namespaces=nsmap)
        fallbacks = alt.xpath('.//mc:Fallback', namespaces=nsmap)
        print(f"Alt {i}: Choices={len(choices)}, Fallbacks={len(fallbacks)}")
        if choices:
            # Print text of first choice
            text = "".join(choices[0].xpath('.//w:t/text()', namespaces=nsmap))
            print(f"  Choice 0 Text Sample: {text[:100]}")

# Look for paragraphs and tables inside AlternateContent
p_in_alt = doc.element.xpath('//mc:Choice//w:p', namespaces=nsmap)
tbl_in_alt = doc.element.xpath('//mc:Choice//w:tbl', namespaces=nsmap)
print(f"\nInside mc:Choice:")
print(f"  w:p: {len(p_in_alt)}")
print(f"  w:tbl: {len(tbl_in_alt)}")
