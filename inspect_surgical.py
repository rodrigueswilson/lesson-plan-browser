
import zipfile
import os
import glob
from lxml import etree

def get_latest_output():
    files = glob.glob("test_output/2025-12-22/originals/combined_originals_*.docx")
    if not files: return None
    return max(files, key=os.path.getmtime)

def inspect_xml_surgical(filepath, xml_path):
    print(f"\n--- {xml_path} in {os.path.basename(filepath)} ---")
    with zipfile.ZipFile(filepath, 'r') as z:
        try:
            data = z.read(xml_path)
            root = etree.fromstring(data)
            print(etree.tostring(root, pretty_print=True).decode())
        except KeyError:
            print(f"NOT FOUND: {xml_path}")

def run_diagnostics():
    template = "input/Lesson Plan Template SY'25-26.docx"
    output = get_latest_output()
    
    if not output:
        print("No output file found.")
        return

    # Check Styles
    inspect_xml_surgical(output, 'word/styles.xml')
    
    # Check Document Relationships (CRITICAL for Hyperlinks)
    inspect_xml_surgical(output, 'word/_rels/document.xml.rels')

if __name__ == "__main__":
    run_diagnostics()
