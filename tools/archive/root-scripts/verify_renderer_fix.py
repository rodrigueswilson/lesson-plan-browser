import sys
import os
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Add project root to path
sys.path.append(os.path.abspath("d:/LP"))

from tools.docx_renderer import DOCXRenderer

def test_force_font_tnr8_fix():
    print("Testing _force_font_tnr8 fix...")
    
    # 1. Create a dummy document and run
    doc = Document()
    p = doc.add_paragraph("Test text")
    run = p.runs[0]
    
    # 2. Add some initial formatting (Simulate existing formatting)
    r_elem = run._element
    rPr = r_elem.get_or_add_rPr()
    
    # Add dummy bold and color to ensure extraction works
    b = OxmlElement("w:b")
    rPr.append(b)
    
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "FF0000")
    rPr.append(color)
    
    # 3. Instantiate Renderer
    renderer = DOCXRenderer("input/Lesson Plan Template SY'25-26.docx")
    
    # 4. Call the fixed method
    try:
        print("Calling _force_font_tnr8...")
        renderer._force_font_tnr8(run, is_bold=True)
        print("SUCCESS: _force_font_tnr8 executed without error.")
    except UnboundLocalError as e:
        print(f"FAILURE: UnboundLocalError caught: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"FAILURE: Unexpected exception: {e}")
        sys.exit(1)

    # 5. Verify variables were theoretically used (we can't easily check internal locals, but success means no crash)
    print("Verification passed.")

if __name__ == "__main__":
    test_force_font_tnr8_fix()
