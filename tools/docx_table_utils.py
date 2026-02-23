"""
Table-related DOCX utilities: column width normalization and table info.
Re-exported from tools.docx_utils for backward compatibility.
"""

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches
from docx.table import Table
from docx import Document


def normalize_table_column_widths(
    table: Table, total_width_inches: float = 6.5
) -> None:
    """
    Set all columns in table to equal width.

    Args:
        table: python-docx Table object
        total_width_inches: Total width to distribute (default 6.5" for backward compatibility)
            IMPORTANT: Should be calculated from document page setup:
            available_width = (page_width - left_margin - right_margin) / 914400

    Example:
        >>> from docx import Document
        >>> doc = Document('input.docx')
        >>> for table in doc.tables:
        >>>     normalize_table_column_widths(table)
        >>> doc.save('output.docx')

    Note:
        - Width values must be integers (EMU units)
        - 1 inch = 914,400 EMU
        - Handles merged cells correctly
        - Empty tables are skipped
        - Sets table preferred width type to 'dxa' (twentieths of a point) to prevent auto-sizing
    """
    if not table.columns:
        return

    tbl_element = table._element
    tblPr = tbl_element.tblPr

    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)

    tblW.set(qn("w:type"), "dxa")
    tblW.set(qn("w:w"), str(int(Inches(total_width_inches))))

    layout_list = tblPr.findall(qn("w:tblLayout"))
    for layout in layout_list:
        tblPr.remove(layout)

    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)

    tblInd_list = tblPr.findall(qn("w:tblInd"))
    for tblInd in tblInd_list:
        tblPr.remove(tblInd)

    tblInd = OxmlElement("w:tblInd")
    tblInd.set(qn("w:w"), "0")
    tblInd.set(qn("w:type"), "dxa")
    tblPr.append(tblInd)

    col_width = int(Inches(total_width_inches) / len(table.columns))

    for column in table.columns:
        column.width = col_width


def normalize_all_tables(doc: Document, total_width_inches: float = 6.5) -> int:
    """
    Normalize column widths for all tables in document.

    Args:
        doc: python-docx Document object
        total_width_inches: Total width to distribute (default 6.5" for backward compatibility)
            IMPORTANT: Should be calculated from document page setup dynamically

    Returns:
        Number of tables normalized

    Example:
        >>> from docx import Document
        >>> doc = Document('input.docx')
        >>> count = normalize_all_tables(doc)
        >>> print(f"Normalized {count} tables")
        >>> doc.save('output.docx')
    """
    count = 0
    for table in doc.tables:
        normalize_table_column_widths(table, total_width_inches)
        count += 1

    return count


def get_table_info(table: Table) -> dict:
    """
    Get information about a table's structure.

    Args:
        table: python-docx Table object

    Returns:
        Dictionary with table information

    Example:
        >>> info = get_table_info(table)
        >>> print(f"Table has {info['num_columns']} columns")
    """
    info = {
        "num_rows": len(table.rows),
        "num_columns": len(table.columns),
        "column_widths": [col.width for col in table.columns] if table.columns else [],
        "has_merged_cells": False,
    }

    if table.rows:
        for row in table.rows:
            if len(row.cells) != len(table.columns):
                info["has_merged_cells"] = True
                break

    return info
