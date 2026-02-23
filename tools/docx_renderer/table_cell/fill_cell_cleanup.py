"""
Duplicate coordinate hyperlink removal for fill_cell.
"""

import re

from docx.oxml.ns import qn

from .. import logger


def remove_duplicate_coordinate_hyperlinks(
    cell,
    text: str,
    day_name: str = None,
    section_name: str = None,
    current_slot_number: int = None,
) -> bool:
    """
    Remove coordinate hyperlinks in the cell that are already present as markdown in text.
    Modifies cell in place. Returns True if cell still has coordinate hyperlinks after cleanup.
    """
    existing_hyperlinks = cell._element.xpath(".//w:hyperlink")
    has_coordinate_hyperlinks = len(existing_hyperlinks) > 0

    if not has_coordinate_hyperlinks or not text:
        return has_coordinate_hyperlinks

    hyperlinks_to_remove = []
    for hl_elem in existing_hyperlinks:
        try:
            r_id = hl_elem.get(qn("r:id"))
            if r_id and cell.paragraphs:
                para = cell.paragraphs[0]
                if r_id in para.part.rels:
                    url = para.part.rels[r_id].target_ref
                    link_text = "".join(
                        node.text for node in hl_elem.xpath(".//w:t") if node.text
                    )
                    if link_text and url:
                        markdown_pattern = rf"\[{re.escape(link_text)}\]\({re.escape(url)}\)"
                        if re.search(markdown_pattern, text, re.IGNORECASE):
                            hyperlinks_to_remove.append(hl_elem)
        except Exception:
            pass

    for hl_elem in hyperlinks_to_remove:
        try:
            parent = hl_elem.getparent()
            if parent is not None:
                parent.remove(hl_elem)
                try:
                    para_elem = parent.getparent()
                    if para_elem is not None and para_elem.tag == qn("w:p"):
                        runs = para_elem.xpath(".//w:r")
                        has_text = any(run.xpath(".//w:t") for run in runs)
                        if not has_text:
                            para_parent = para_elem.getparent()
                            if para_parent is not None:
                                para_parent.remove(para_elem)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(
                "failed_to_remove_duplicate_hyperlink",
                extra={
                    "error": str(e),
                    "cell": f"{day_name}_{section_name}"
                    if day_name and section_name
                    else "unknown",
                },
            )

    existing_hyperlinks = cell._element.xpath(".//w:hyperlink")
    has_coordinate_hyperlinks = len(existing_hyperlinks) > 0
    if hyperlinks_to_remove:
        logger.info(
            "removed_duplicate_coordinate_hyperlinks",
            extra={
                "removed_count": len(hyperlinks_to_remove),
                "cell": f"{day_name}_{section_name}"
                if day_name and section_name
                else "unknown",
                "slot": current_slot_number,
            },
        )
    return has_coordinate_hyperlinks
