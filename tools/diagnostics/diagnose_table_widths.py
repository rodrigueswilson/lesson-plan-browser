"""
Diagnose why tables have different right edges despite setting same width.
Check for cell spacing, borders, and actual rendered widths.
"""

from docx import Document
from docx.oxml.ns import qn

TEMPLATE_PATH = r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\Lesson Plan Template.docx'

doc = Document(TEMPLATE_PATH)

print("=" * 80)
print("DETAILED TABLE WIDTH DIAGNOSIS")
print("=" * 80)

for i, table in enumerate(doc.tables):
    print(f"\n{'='*80}")
    print(f"TABLE {i+1}")
    print(f"{'='*80}")
    
    tbl = table._element
    tblPr = tbl.tblPr
    
    # Table width
    print(f"\n1. TABLE WIDTH:")
    try:
        if hasattr(table, 'width') and table.width:
            print(f"   table.width: {table.width} EMUs = {table.width/914400:.4f} inches")
        else:
            print(f"   table.width attribute not available")
    except:
        print(f"   Could not read table.width")
    
    # Check tblW in XML
    if tblPr is not None:
        tblW_list = tblPr.findall(qn('w:tblW'))
        for tblW in tblW_list:
            w_val = tblW.get(qn('w:w'))
            w_type = tblW.get(qn('w:type'))
            print(f"   XML tblW: w={w_val}, type={w_type}")
    
    # Table indent
    print(f"\n2. TABLE INDENT (tblInd):")
    if tblPr is not None:
        tblInd_list = tblPr.findall(qn('w:tblInd'))
        if tblInd_list:
            for tblInd in tblInd_list:
                ind_val = tblInd.get(qn('w:w'))
                ind_type = tblInd.get(qn('w:type'))
                if ind_type == 'dxa':
                    ind_inches = int(ind_val) / 1440 if ind_val else 0
                    print(f"   tblInd: w={ind_val}, type={ind_type} ({ind_inches:.4f} inches)")
                else:
                    print(f"   tblInd: w={ind_val}, type={ind_type}")
        else:
            print(f"   No tblInd found")
    
    # Cell spacing
    print(f"\n3. CELL SPACING (tblCellSpacing):")
    if tblPr is not None:
        spacing_list = tblPr.findall(qn('w:tblCellSpacing'))
        if spacing_list:
            for spacing in spacing_list:
                sp_val = spacing.get(qn('w:w'))
                sp_type = spacing.get(qn('w:type'))
                print(f"   tblCellSpacing: w={sp_val}, type={sp_type}")
        else:
            print(f"   No cell spacing")
    
    # Borders
    print(f"\n4. BORDERS (tblBorders):")
    if tblPr is not None:
        borders_list = tblPr.findall(qn('w:tblBorders'))
        if borders_list:
            print(f"   tblBorders element found")
            for borders in borders_list:
                for border_elem in borders:
                    border_name = border_elem.tag.split('}')[-1]
                    sz = border_elem.get(qn('w:sz'))
                    print(f"     {border_name}: sz={sz} (eighths of a point)")
        else:
            print(f"   No border settings")
    
    # Column widths
    print(f"\n5. COLUMN WIDTHS:")
    total_col_width = 0
    for j, column in enumerate(table.columns):
        if column.width:
            total_col_width += column.width
            print(f"   Column {j+1}: {column.width} EMUs = {column.width/914400:.4f} inches")
    
    if total_col_width > 0:
        print(f"   TOTAL: {total_col_width} EMUs = {total_col_width/914400:.4f} inches")
    
    # Cell margins
    print(f"\n6. CELL MARGINS (tblCellMar):")
    if tblPr is not None:
        cellMar_list = tblPr.findall(qn('w:tblCellMar'))
        if cellMar_list:
            for cellMar in cellMar_list:
                for margin in cellMar:
                    margin_name = margin.tag.split('}')[-1]
                    m_val = margin.get(qn('w:w'))
                    m_type = margin.get(qn('w:type'))
                    print(f"   {margin_name}: w={m_val}, type={m_type}")
        else:
            print(f"   No cell margins defined")
    
    # Layout type
    print(f"\n7. LAYOUT:")
    try:
        if hasattr(table, 'allow_autofit'):
            print(f"   allow_autofit: {table.allow_autofit}")
    except:
        pass
    if tblPr is not None:
        layout_list = tblPr.findall(qn('w:tblLayout'))
        if layout_list:
            for layout in layout_list:
                layout_type = layout.get(qn('w:type'))
                print(f"   tblLayout type: {layout_type}")
        else:
            print(f"   No tblLayout specified")

print("\n" + "=" * 80)
