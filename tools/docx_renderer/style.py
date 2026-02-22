"""
Style and XML helpers for DOCX rendering.

Provides: sanitize_xml_text, is_signature_table, ensure_hyperlink_style,
force_font_tnr8, force_font_arial10, apply_originals_cleanup.
"""

# Fuzzy matching threshold for hyperlink/media placement (bilingual support)
FUZZY_MATCH_THRESHOLD = 0.50

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor


def sanitize_xml_text(text: str) -> str:
    """
    Sanitize text for XML compatibility in DOCX.

    Removes NULL bytes and control characters that are not allowed in XML.
    Preserves common whitespace characters (space, tab, newline, carriage return).

    Args:
        text: Input text that may contain invalid XML characters

    Returns:
        Sanitized text safe for XML/DOCX
    """
    if not text:
        return text

    result = []
    for char in text:
        code = ord(char)
        if code == 0x09 or code == 0x0A or code == 0x0D:
            result.append(char)
        elif code >= 0x20:
            if not (0xD800 <= code <= 0xDFFF):
                result.append(char)

    return "".join(result)


def is_signature_table(table) -> bool:
    """Check if a table is a signature table based on common headers."""
    if not table.rows:
        return False
    try:
        first_row_text = "".join(cell.text for cell in table.rows[0].cells).lower()
        return any(x in first_row_text for x in ["signature", "approver", "approved"])
    except Exception:
        return False


def ensure_hyperlink_style(doc: Document) -> None:
    """Ensure 'Hyperlink' style exists to prevent 'Styles 1' error in Word."""
    if "Hyperlink" not in doc.styles:
        try:
            from docx.enum.style import WD_STYLE_TYPE

            style = doc.styles.add_style("Hyperlink", WD_STYLE_TYPE.CHARACTER)
            style.font.name = "Times New Roman"
            style.font.size = Pt(8)
            style.font.color.rgb = RGBColor(0, 0, 255)
            style.font.underline = True
        except Exception:
            pass


def force_font_tnr8(run, is_bold: bool = False, is_hyperlink: bool = False) -> None:
    """Force Times New Roman 8pt on a Run object. Reconstructs w:rPr for correct XML order."""
    r_elem = run._element
    rPr = r_elem.get_or_add_rPr()

    existing_rStyle = rPr.find(qn("w:rStyle"))
    existing_color = rPr.find(qn("w:color"))
    existing_u = rPr.find(qn("w:u"))
    existing_b = rPr.find(qn("w:b"))
    existing_bCs = rPr.find(qn("w:bCs"))
    existing_i = rPr.find(qn("w:i"))
    existing_iCs = rPr.find(qn("w:iCs"))
    existing_sz = rPr.find(qn("w:sz"))
    existing_szCs = rPr.find(qn("w:szCs"))
    existing_vertAlign = rPr.find(qn("w:vertAlign"))

    for child in list(rPr):
        rPr.remove(child)

    if existing_rStyle is not None:
        rPr.append(existing_rStyle)

    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Times New Roman")
    rFonts.set(qn("w:hAnsi"), "Times New Roman")
    rFonts.set(qn("w:cs"), "Times New Roman")
    rFonts.set(qn("w:eastAsia"), "Times New Roman")
    rPr.append(rFonts)

    if is_bold:
        rPr.append(OxmlElement("w:b"))
        rPr.append(OxmlElement("w:bCs"))
    elif existing_b is not None:
        rPr.append(existing_b)
        rPr.append(existing_bCs if existing_bCs is not None else OxmlElement("w:bCs"))

    if is_hyperlink:
        color = OxmlElement("w:color")
        color.set(qn("w:val"), "0000FF")
        rPr.append(color)
    elif existing_color is not None:
        rPr.append(existing_color)

    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "16")
    rPr.append(sz)
    szCs = OxmlElement("w:szCs")
    szCs.set(qn("w:val"), "16")
    rPr.append(szCs)

    if is_hyperlink:
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rPr.append(u)
    elif existing_u is not None:
        rPr.append(existing_u)


def force_font_arial10(run, is_bold: bool = False) -> None:
    """Force Arial 10pt on a Run object. Used for metadata table formatting."""
    r_elem = run._element
    rPr = r_elem.get_or_add_rPr()

    existing_rStyle = rPr.find(qn("w:rStyle"))
    existing_color = rPr.find(qn("w:color"))
    existing_u = rPr.find(qn("w:u"))

    for child in list(rPr):
        rPr.remove(child)

    if existing_rStyle is not None:
        rPr.append(existing_rStyle)

    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Arial")
    rFonts.set(qn("w:hAnsi"), "Arial")
    rFonts.set(qn("w:cs"), "Arial")
    rFonts.set(qn("w:eastAsia"), "Arial")
    rPr.append(rFonts)

    if is_bold:
        rPr.append(OxmlElement("w:b"))
        rPr.append(OxmlElement("w:bCs"))

    if existing_color is not None:
        rPr.append(existing_color)

    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "20")
    rPr.append(sz)
    szCs = OxmlElement("w:szCs")
    szCs.set(qn("w:val"), "20")
    rPr.append(szCs)

    if existing_u is not None:
        rPr.append(existing_u)


def apply_originals_cleanup(
    doc: Document, daily_plans_table_idx: int, is_signature_table_fn
) -> None:
    """
    Remove signature tables and 'Required Signatures' paragraphs for originals mode.
    Call when is_originals is True after filling content.
    """
    all_tables = list(enumerate(doc.tables))
    for idx, table in reversed(all_tables):
        if idx > daily_plans_table_idx and is_signature_table_fn(table):
            for row in table.rows:
                for cell in row.cells:
                    cell.text = ""
            tbl = table._element
            tbl.getparent().remove(tbl)

    paras_to_remove = []
    for para in doc.paragraphs:
        if "Required Signatures" in para.text:
            paras_to_remove.append(para._element)

    for p_element in paras_to_remove:
        try:
            p_element.getparent().remove(p_element)
        except Exception:
            pass
