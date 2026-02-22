"""
Table extraction and cell text helpers for DOCX parsing.
"""

import re
from typing import List

from docx import Document
from docx.oxml.ns import qn


def extract_tables(doc: Document) -> List[List[List[str]]]:
    """Extract all tables from document.

    Returns:
        List of tables, where each table is a list of rows,
        and each row is a list of cell values
    """
    tables = []
    for table in doc.tables:
        table_data = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            table_data.append(row_data)
        tables.append(table_data)
    return tables


def is_signature_content(text: str) -> bool:
    """Check if text is part of signature/certification section.

    Args:
        text: Text to check

    Returns:
        True if text is signature content to exclude
    """
    signature_patterns = [
        r"i certify",
        r"certification",
        r"teacher signature",
        r"principal signature",
        r"administrator signature",
        r"aligned with.*standards",
        r"new jersey student learning",
        r"njsls",
        r"signature:",
        r"date:.*signature",
    ]
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in signature_patterns)


def get_cell_text_with_hyperlinks(cell) -> str:
    """Extract text from a cell, injecting markdown hyperlinks where they exist."""
    full_text = []
    for paragraph in cell.paragraphs:
        para_parts = []
        for child in paragraph._element:
            if child.tag == qn("w:r"):
                text = "".join(node.text for node in child.xpath(".//w:t") if node.text)
                if text:
                    para_parts.append(text)
            elif child.tag == qn("w:hyperlink"):
                try:
                    r_id = child.get(qn("r:id"))
                    if r_id and r_id in paragraph.part.rels:
                        url = paragraph.part.rels[r_id].target_ref
                        text = "".join(node.text for node in child.xpath(".//w:t") if node.text)
                        if text and url:
                            para_parts.append(f"[{text}]({url})")
                        elif text:
                            para_parts.append(text)
                except Exception:
                    text = "".join(node.text for node in child.xpath(".//w:t") if node.text)
                    if text:
                        para_parts.append(text)
        para_text = "".join(para_parts).strip()
        if para_text:
            full_text.append(para_text)
    return "\n".join(full_text).strip()
