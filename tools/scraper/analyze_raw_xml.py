import zipfile
from lxml import etree

path = r"d:\LP\reference_docs\scraped\3rd grade_unit 2_docx\Copy of Unit_2__Area_and_Multiplication.docx"

with zipfile.ZipFile(path) as docx:
    xml_content = docx.read('word/document.xml')
    tree = etree.fromstring(xml_content)
    
    # Namespaces
    ns = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'
    }
    
    body = tree.find('.//w:body', namespaces=ns)
    print(f"Body Children: {[child.tag.split('}')[-1] for child in body]}")
    
    # Check for AlternateContent
    alt_content = tree.xpath('//mc:AlternateContent', namespaces=ns)
    print(f"Total mc:AlternateContent: {len(alt_content)}")
    
    # Total Tables and Paragraphs in the WHOLE XML
    all_p = tree.xpath('//w:p', namespaces=ns)
    all_tbl = tree.xpath('//w:tbl', namespaces=ns)
    print(f"Total w:p (global): {len(all_p)}")
    print(f"Total w:tbl (global): {len(all_tbl)}")
    
    # Check for SDT
    all_sdt = tree.xpath('//w:sdt', namespaces=ns)
    print(f"Total w:sdt (global): {len(all_sdt)}")

    # Check for content inside the first SDT if exists
    if all_sdt:
        sdt_content = all_sdt[0].xpath('.//w:sdtContent', namespaces=ns)
        if sdt_content:
            inner_p = sdt_content[0].xpath('.//w:p', namespaces=ns)
            inner_tbl = sdt_content[0].xpath('.//w:tbl', namespaces=ns)
            print(f"First SDT Content: w:p={len(inner_p)}, w:tbl={len(inner_tbl)}")
