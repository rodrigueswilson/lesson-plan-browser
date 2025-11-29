"""Check page setup and all table widths in the template."""

from docx import Document
from docx.shared import Inches, Twips

# Load template
doc = Document("input/Lesson Plan Template SY'25-26.docx")

print("=" * 80)
print("PAGE SETUP")
print("=" * 80)

# Get page dimensions
sections = doc.sections
for i, section in enumerate(sections):
    print(f"\nSection {i}:")
    print(f"  Page width: {section.page_width.inches:.2f} inches")
    print(f"  Page height: {section.page_height.inches:.2f} inches")
    print(f"  Left margin: {section.left_margin.inches:.2f} inches")
    print(f"  Right margin: {section.right_margin.inches:.2f} inches")
    print(f"  Top margin: {section.top_margin.inches:.2f} inches")
    print(f"  Bottom margin: {section.bottom_margin.inches:.2f} inches")
    
    # Calculate available width
    available_width = section.page_width.inches - section.left_margin.inches - section.right_margin.inches
    print(f"  Available width (page - margins): {available_width:.2f} inches")

print("\n" + "=" * 80)
print("TABLE WIDTHS")
print("=" * 80)

for i, table in enumerate(doc.tables):
    # Get table identifier
    table_text = "\n".join([cell.text for row in table.rows for cell in row.cells])
    table_name = "Unknown"
    
    if "Required Signatures" in table_text:
        table_name = "Signature Table"
    elif "Monday" in table_text and "Tuesday" in table_text:
        table_name = "Daily Plans Table"
    elif "Teacher:" in table_text or "Grade:" in table_text:
        table_name = "Metadata Table"
    
    # Get table width from XML
    tbl_element = table._element
    tblPr = tbl_element.tblPr
    tblW = tblPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblW')
    
    if tblW is not None:
        width_type = tblW.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
        width_value = tblW.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')
        
        if width_type == 'dxa':  # Twentieths of a point
            width_twips = int(width_value)
            width_inches = Twips(width_twips).inches
            print(f"\nTable {i} ({table_name}):")
            print(f"  Width type: {width_type}")
            print(f"  Width: {width_twips} twips = {width_inches:.2f} inches")
            print(f"  Columns: {len(table.columns)}")
        elif width_type == 'pct':  # Percentage
            print(f"\nTable {i} ({table_name}):")
            print(f"  Width type: {width_type} (percentage)")
            print(f"  Width: {width_value} (50ths of a percent)")
            print(f"  Columns: {len(table.columns)}")
        elif width_type == 'auto':
            print(f"\nTable {i} ({table_name}):")
            print(f"  Width type: {width_type} (auto-sized)")
            print(f"  Columns: {len(table.columns)}")
    else:
        print(f"\nTable {i} ({table_name}):")
        print(f"  Width: Not specified (defaults to auto)")
        print(f"  Columns: {len(table.columns)}")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

print("\nStandard table width in code: 6.5 inches")
print("Available page width: ~6.5 inches (8.5\" page - 1\" margins)")
print("\nRECOMMENDATION:")
print("  - Daily Plans Table: Should be 6.5 inches (standard)")
print("  - Metadata Table: Should be 6.5 inches (standard)")
print("  - Signature Table: Currently 10.07 inches - NEEDS INVESTIGATION")
print("    * May be intentionally wider")
print("    * Or may need to be standardized to 6.5 inches")
