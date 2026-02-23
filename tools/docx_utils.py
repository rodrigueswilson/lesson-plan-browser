"""
Utility functions for DOCX manipulation.
Follows DRY principle - reusable across modules.
"""

import logging

from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from tools.docx_table_utils import (
    get_table_info,
    normalize_all_tables,
    normalize_table_column_widths,
)
from tools.docx_style_utils import (
    diagnose_style_conflicts,
    normalize_styles_from_master,
    normalize_styles_via_file,
)

try:
    import structlog
    _log = structlog.get_logger(__name__)
except ImportError:
    _log = logging.getLogger(__name__)

__all__ = [
    "diagnose_style_conflicts",
    "ensure_hyperlink_style",
    "get_table_info",
    "normalize_all_tables",
    "normalize_styles_from_master",
    "normalize_styles_via_file",
    "normalize_table_column_widths",
    "remove_headers_footers",
    "strip_custom_styles",
    "strip_problematic_elements",
    "strip_sections",
]


def strip_custom_styles(doc: Document, master_doc: Document) -> None:
    """
    Map all paragraphs and runs in doc to standard styles if their 
    current style is not present in master_doc.
    This prevents "unreadable content" errors where the document 
    references a style ID that no longer exists after normalization.
    """
    master_style_ids = {style.style_id for style in master_doc.styles}
    
    # 1. Map paragraphs
    for p in doc.paragraphs:
        if p.style.style_id not in master_style_ids:
            try:
                p.style = doc.styles['Normal']
            except:
                pass
                
    # 2. Map runs (character styles)
    for p in doc.paragraphs:
        for r in p.runs:
            if r.style and r.style.style_id not in master_style_ids:
                try:
                    r.style = doc.styles['Default Paragraph Font']
                except:
                    r.style = None
                    
    # 3. Map tables
    for t in doc.tables:
        if t.style and t.style.style_id not in master_style_ids:
            try:
                t.style = doc.styles['Table Grid']
            except:
                try:
                    t.style = doc.styles['Normal Table']
                except:
                    pass

def strip_problematic_elements(doc: Document) -> None:
    """
    Remove bookmarks, comments, and other elements that often cause 
    "unreadable content" errors after merging with docxcompose.
    """
    from docx.oxml.ns import qn
    
    # Use structlog if available
    _log.debug("stripping_problematic_elements_started")
    
    # 1. Remove all bookmarks (w:bookmarkStart, w:bookmarkEnd)
    # These often have duplicate IDs or names after merging
    count_bookmarks = 0
    for element in doc.element.xpath('.//w:bookmarkStart | .//w:bookmarkEnd'):
        element.getparent().remove(element)
        count_bookmarks += 1
        
    # 2. Remove all comments (w:commentReference, w:commentRangeStart, w:commentRangeEnd)
    count_comments = 0
    for element in doc.element.xpath('.//w:commentReference | .//w:commentRangeStart | .//w:commentRangeEnd'):
        element.getparent().remove(element)
        count_comments += 1
        
    # 3. Remove all proofing errors (w:proofErr)
    count_proof = 0
    for element in doc.element.xpath('.//w:proofErr'):
        element.getparent().remove(element)
        count_proof += 1

    if count_bookmarks > 0 or count_comments > 0 or count_proof > 0:
        _log.info("stripped_elements", extra={
            "bookmarks": count_bookmarks,
            "comments": count_comments,
            "proofing_errors": count_proof
        })
    else:
        _log.debug("no_problematic_elements_found_to_strip")

def remove_headers_footers(doc: Document) -> None:
    """
    Remove all headers and footers from a document to prevent 
    conflicts during merging.
    """
    for section in doc.sections:
        section.header.is_linked_to_previous = True
        section.footer.is_linked_to_previous = True
        # Also clear the content if possible
        try:
            for p in section.header.paragraphs:
                p.text = ""
            for p in section.footer.paragraphs:
                p.text = ""
        except:
            pass

def ensure_hyperlink_style(doc: Document) -> None:
    """
    Ensure the "Hyperlink" style exists in the document.
    This is critical because Word often expects this style for hyperlinks,
    and removing it during style normalization causes "unreadable content" errors.
    """
    if "Hyperlink" not in doc.styles:
        try:
            from docx.enum.style import WD_STYLE_TYPE
            from docx.shared import Pt, RGBColor
            style = doc.styles.add_style("Hyperlink", WD_STYLE_TYPE.CHARACTER)
            style.font.name = "Times New Roman"
            style.font.size = Pt(8)
            style.font.color.rgb = RGBColor(0, 0, 255)
            style.font.underline = True
        except Exception:
            pass

def strip_sections(doc: Document) -> None:
    """
    Remove all section properties from the document body to prevent 
    Word from creating multiple sections after merging.
    The document will inherit the section properties of the master document.
    """
    from docx.oxml.ns import qn
    
    # Remove sectPr from the body
    body = doc.element.body
    sectPrs = body.findall(qn('w:sectPr'))
    for sectPr in sectPrs:
        # Don't remove the last one if it's the only one, as Word needs it
        # But we want to remove any that are NOT the last one (which are section breaks)
        pass
    
    # Actually, the simplest way is to remove all sectPr from paragraphs
    for p in body.findall(qn('w:p')):
        pPr = p.find(qn('w:pPr'))
        if pPr is not None:
            sectPr = pPr.find(qn('w:sectPr'))
            if sectPr is not None:
                pPr.remove(sectPr)
