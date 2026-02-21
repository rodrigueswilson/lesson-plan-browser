
import zipfile
from lxml import etree
import glob
import os

def inspect_styles(filepath):
    print(f"Inspecting styles in: {filepath}")
    if not os.path.exists(filepath):
        print("File not found.")
        return

    with zipfile.ZipFile(filepath, 'r') as z:
        try:
            styles_xml = z.read('word/styles.xml')
            root = etree.fromstring(styles_xml)
            
            # 1. Check docDefaults
            doc_defaults = root.xpath(".//w:docDefaults", namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
            if doc_defaults:
                print("\n--- Document Defaults ---")
                print(etree.tostring(doc_defaults[0], pretty_print=True).decode())
            else:
                print("\n--- No Document Defaults found ---")

            # 2. Check specific styles: Normal and Hyperlink
            styles = root.xpath(".//w:style", namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
            for style in styles:
                style_id = style.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}styleId')
                if style_id in ['Normal', 'Hyperlink']:
                    print(f"\n--- Style: {style_id} ---")
                    print(etree.tostring(style, pretty_print=True).decode())

        except KeyError:
            print("word/styles.xml not found in ZIP.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    latest_file = max(glob.glob("test_output/2025-12-22/originals/combined_originals_*.docx"), key=os.path.getmtime)
    inspect_styles(latest_file)
