"""
File-based style normalization for DOCX (zip/temp file approach).
Replaces styles, numbering, font table, and docProps via temporary files.
"""

import logging
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

from docx import Document

try:
    import structlog
    _log = structlog.get_logger(__name__)
except ImportError:
    _log = logging.getLogger(__name__)


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
                        replacement_data[xml_file] = master_zip.read(xml_file)
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

            with zipfile.ZipFile(target_path, 'r') as target_zip:
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as output_zip:
                    files_copied = 0
                    for item in target_zip.infolist():
                        if item.filename not in replacement_data:
                            data = target_zip.read(item.filename)
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
