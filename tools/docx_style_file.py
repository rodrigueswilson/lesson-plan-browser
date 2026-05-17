"""
File-based style normalization for DOCX (zip/temp file approach).
Replaces styles, numbering, font table, and docProps via temporary files.
"""

import logging
import re
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

from docx import Document
from docx.oxml.ns import qn
from lxml import etree

try:
    import structlog
    _log = structlog.get_logger(__name__)
except ImportError:
    _log = logging.getLogger(__name__)


REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
HYPERLINK_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
)


def _repair_styles_xml(styles_xml: bytes) -> bytes:
    """Repair style definitions that Word reports as a generic "Styles 1" issue."""
    root = etree.fromstring(styles_xml)
    repaired_count = 0

    for style in root.findall(qn("w:style")):
        if style.find(qn("w:name")) is not None:
            continue

        style_id = style.get(qn("w:styleId"))
        if not style_id:
            continue

        name = etree.Element(qn("w:name"))
        name.set(qn("w:val"), style_id)
        style.insert(0, name)
        repaired_count += 1

    if repaired_count:
        _log.warning(
            "styles_xml_missing_names_repaired",
            extra={"repaired_count": repaired_count},
        )

    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=True,
    )


def _repair_document_hyperlink_relationships(
    document_xml: bytes,
    relationships_xml: bytes,
) -> tuple[bytes, bytes]:
    """Give repeated external hyperlink elements their own relationship IDs."""
    document_root = etree.fromstring(document_xml)
    relationships_root = etree.fromstring(relationships_xml)
    relationship_tag = f"{{{REL_NS}}}Relationship"
    r_id_attr = qn("r:id")

    relationships_by_id = {
        rel.get("Id"): rel for rel in relationships_root.findall(relationship_tag)
    }
    hyperlink_elements = [
        element
        for element in document_root.findall(f".//{qn('w:hyperlink')}")
        if element.get(r_id_attr) in relationships_by_id
    ]
    hyperlink_counts: dict[str, int] = {}
    for hyperlink in hyperlink_elements:
        rel_id = hyperlink.get(r_id_attr)
        relationship = relationships_by_id[rel_id]
        if (
            relationship.get("Type") == HYPERLINK_REL_TYPE
            and relationship.get("TargetMode") == "External"
        ):
            hyperlink_counts[rel_id] = hyperlink_counts.get(rel_id, 0) + 1

    repeated_rel_ids = {
        rel_id for rel_id, count in hyperlink_counts.items() if count > 1
    }
    if not repeated_rel_ids:
        return document_xml, relationships_xml

    used_ids = set(relationships_by_id)
    next_id = _next_relationship_id(used_ids)
    seen_counts: dict[str, int] = {}
    repaired_count = 0

    for hyperlink in hyperlink_elements:
        rel_id = hyperlink.get(r_id_attr)
        if rel_id not in repeated_rel_ids:
            continue

        seen_counts[rel_id] = seen_counts.get(rel_id, 0) + 1
        if seen_counts[rel_id] == 1:
            continue

        source_relationship = relationships_by_id[rel_id]
        while f"rId{next_id}" in used_ids:
            next_id += 1
        new_rel_id = f"rId{next_id}"
        next_id += 1
        used_ids.add(new_rel_id)

        new_relationship = etree.Element(relationship_tag)
        new_relationship.set("Id", new_rel_id)
        new_relationship.set("Type", source_relationship.get("Type"))
        new_relationship.set("Target", source_relationship.get("Target"))
        new_relationship.set("TargetMode", source_relationship.get("TargetMode"))
        relationships_root.append(new_relationship)
        hyperlink.set(r_id_attr, new_rel_id)
        repaired_count += 1

    if repaired_count:
        _log.warning(
            "document_hyperlink_relationships_repaired",
            extra={"repaired_count": repaired_count},
        )

    return (
        etree.tostring(
            document_root,
            xml_declaration=True,
            encoding="UTF-8",
            standalone=True,
        ),
        etree.tostring(
            relationships_root,
            xml_declaration=True,
            encoding="UTF-8",
            standalone=True,
        ),
    )


def _next_relationship_id(used_ids: set[str]) -> int:
    numeric_ids = [
        int(match.group(1))
        for rel_id in used_ids
        if (match := re.fullmatch(r"rId(\d+)", rel_id))
    ]
    return max(numeric_ids, default=0) + 1


def normalize_styles_via_file(master_doc: Document, target_doc: Document) -> Optional[BytesIO]:
    """
    Replace styles, numbering, font table, and docProps (custom.xml, core.xml) by using
    temporary files and zipfile. Replacing docProps avoids "Word found unreadable content"
    when merged DOCX have corrupt or conflicting custom properties.

    Returns a BytesIO stream containing the normalized document, or None if failed.
    The caller should reload the document from this stream.
    """
    _log.warning("file_based_normalization_started")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            master_path = Path(temp_dir) / "master.docx"
            target_path = Path(temp_dir) / "target.docx"
            output_path = Path(temp_dir) / "target_normalized.docx"

            master_doc.save(str(master_path))
            target_doc.save(str(target_path))
            _log.debug("documents_saved_to_temp")

            files_to_replace = [
                'word/styles.xml',
                'word/numbering.xml',
                'word/fontTable.xml',
                'docProps/custom.xml',
                'docProps/core.xml',
            ]

            replacement_data = {}
            with zipfile.ZipFile(master_path, 'r') as master_zip:
                master_files = master_zip.namelist()
                for xml_file in files_to_replace:
                    if xml_file in master_files:
                        data = master_zip.read(xml_file)
                        if xml_file == 'word/styles.xml':
                            data = _repair_styles_xml(data)
                        replacement_data[xml_file] = data
                        _log.debug("extracted_from_master", extra={"file": xml_file})

            missing = [f for f in files_to_replace if f not in replacement_data]
            if missing:
                _log.debug(
                    "replacement_files_not_in_master",
                    extra={"missing": missing, "note": "only parts present in template are replaced"},
                )
            if not replacement_data:
                _log.warning("no_replacement_files_found_in_master")
                return None

            package_overrides = {}
            with zipfile.ZipFile(target_path, 'r') as target_zip:
                target_files = set(target_zip.namelist())
                if (
                    "word/document.xml" in target_files
                    and "word/_rels/document.xml.rels" in target_files
                ):
                    (
                        package_overrides["word/document.xml"],
                        package_overrides["word/_rels/document.xml.rels"],
                    ) = _repair_document_hyperlink_relationships(
                        target_zip.read("word/document.xml"),
                        target_zip.read("word/_rels/document.xml.rels"),
                    )

                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as output_zip:
                    files_copied = 0
                    for item in target_zip.infolist():
                        if item.filename not in replacement_data:
                            data = package_overrides.get(
                                item.filename,
                                target_zip.read(item.filename),
                            )
                            output_zip.writestr(item, data)
                            files_copied += 1
                    for filename, data in replacement_data.items():
                        output_zip.writestr(filename, data)
                    _log.debug("files_replaced_in_zip", extra={
                        "files_copied": files_copied,
                        "files_replaced": list(replacement_data.keys()),
                    })

            with open(output_path, 'rb') as f:
                normalized_data = BytesIO(f.read())

            _log.warning("styles_and_numbering_replaced_via_file", extra={
                "replaced_files": list(replacement_data.keys()),
                "success": True,
            })
            return normalized_data

    except Exception as e:
        _log.error("file_based_style_replacement_failed", extra={
            "error": str(e),
            "error_type": type(e).__name__
        }, exc_info=True)
        return None
