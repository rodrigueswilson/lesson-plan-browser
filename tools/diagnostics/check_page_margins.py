"""
Check the actual page margins and calculate correct table width.
"""

from docx import Document
from docx.shared import Inches

TEMPLATE_PATH = r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\Lesson Plan Template.docx'

doc = Document(TEMPLATE_PATH)

print("=" * 80)
print("PAGE SETUP AND MARGIN ANALYSIS")
print("=" * 80)

# Get page dimensions and margins from first section
section = doc.sections[0]

print(f"\nPAGE DIMENSIONS:")
print(f"  Page width: {section.page_width} EMUs = {section.page_width.inches:.2f} inches")
print(f"  Page height: {section.page_height} EMUs = {section.page_height.inches:.2f} inches")

print(f"\nMARGINS:")
print(f"  Left margin: {section.left_margin} EMUs = {section.left_margin.inches:.2f} inches")
print(f"  Right margin: {section.right_margin} EMUs = {section.right_margin.inches:.2f} inches")
print(f"  Top margin: {section.top_margin} EMUs = {section.top_margin.inches:.2f} inches")
print(f"  Bottom margin: {section.bottom_margin} EMUs = {section.bottom_margin.inches:.2f} inches")

# Calculate available width
available_width_emus = section.page_width - section.left_margin - section.right_margin
available_width_inches = available_width_emus / 914400

print(f"\nAVAILABLE WIDTH FOR CONTENT:")
print(f"  {available_width_emus} EMUs = {available_width_inches:.4f} inches")

# Calculate in different units
available_width_dxa = int(available_width_inches * 1440)

print(f"\nCORRECT TABLE WIDTH SHOULD BE:")
print(f"  {available_width_inches:.4f} inches")
print(f"  {available_width_emus} EMUs")
print(f"  {available_width_dxa} DXA")

# Check current table widths
print(f"\nCURRENT TABLE WIDTHS:")
for i, table in enumerate(doc.tables):
    tbl = table._element
    tblPr = tbl.tblPr
    if tblPr is not None:
        from docx.oxml.ns import qn
        tblW_list = tblPr.findall(qn('w:tblW'))
        for tblW in tblW_list:
            w_val = tblW.get(qn('w:w'))
            w_type = tblW.get(qn('w:type'))
            if w_type == 'dxa':
                w_inches = int(w_val) / 1440
                print(f"  Table {i+1}: {w_val} DXA = {w_inches:.4f} inches")

# Calculate difference
current_table_width_inches = 7.5
difference = available_width_inches - current_table_width_inches

print(f"\nDISCREPANCY:")
print(f"  Current table width: {current_table_width_inches:.4f} inches")
print(f"  Should be: {available_width_inches:.4f} inches")
print(f"  Difference: {difference:.4f} inches ({difference * 2:.4f} inches total margin excess)")

print("\n" + "=" * 80)
