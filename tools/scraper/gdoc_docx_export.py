"""
Drive full-DOCX export with per-tab synthesis fallback (Docs API JSON in memory).

Used by tools/scraper/main.py and export_doc_ids_to_docx.py when
exportSizeLimitExceeded blocks a single-file export.
"""
from __future__ import annotations

import os
from typing import Any, Callable, Dict, List, Optional

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def is_export_size_limited_error(err: str) -> bool:
    if not err:
        return False
    lower = err.lower()
    return "exportsizelimitexceeded" in lower or "too large" in lower


def export_docx_full_or_tab_fallback(
    client: Any,
    document_id: str,
    doc: Dict[str, Any],
    originals_dir: str,
    safe_doc_title: str,
    *,
    log_fn: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    Try Drive export to a single .docx. On size limit, write one .docx per navigation tab.

    `doc` must be the same document as `document_id`, with includeTabsContent (e.g. client.get_document).

    Returns:
      mode: 'full' | 'tabs' | 'failed'
      full_docx: path or None
      tab_dir: directory containing tab parts, or None
      tab_docx_paths: list of paths
      error: message if failed
    """
    log = log_fn or (lambda _m: None)

    docx_path = os.path.join(originals_dir, f"{safe_doc_title}.docx")
    ok, err = client.export_document_result(document_id, docx_path, mime_type=_DOCX_MIME)
    if ok and os.path.isfile(docx_path) and os.path.getsize(docx_path) > 0:
        log(f"Exported full DOCX ({os.path.getsize(docx_path)} bytes)")
        return {
            "mode": "full",
            "full_docx": os.path.abspath(docx_path),
            "tab_dir": None,
            "tab_docx_paths": [],
            "error": None,
        }

    if os.path.isfile(docx_path):
        try:
            os.remove(docx_path)
        except OSError:
            pass

    if not is_export_size_limited_error(err):
        log(f"DOCX export failed: {err}")
        return {
            "mode": "failed",
            "full_docx": None,
            "tab_dir": None,
            "tab_docx_paths": [],
            "error": err,
        }

    tabs = doc.get("tabs") or []
    if not tabs:
        log("Drive size limit hit but document has no tabs; cannot split into tab DOCX files.")
        return {
            "mode": "failed",
            "full_docx": None,
            "tab_dir": None,
            "tab_docx_paths": [],
            "error": err,
        }

    from tools.scraper.gdoc_tab_to_docx import export_all_tabs_to_directory

    tab_dir = os.path.join(originals_dir, f"{safe_doc_title}_by_tab")
    paths = export_all_tabs_to_directory(doc, tab_dir, safe_doc_title)
    if not paths:
        log("Tab fallback produced no files.")
        return {
            "mode": "failed",
            "full_docx": None,
            "tab_dir": None,
            "tab_docx_paths": [],
            "error": err,
        }

    log(f"Full DOCX blocked by size limit; wrote {len(paths)} tab DOCX under {tab_dir}")
    return {
        "mode": "tabs",
        "full_docx": None,
        "tab_dir": os.path.abspath(tab_dir),
        "tab_docx_paths": paths,
        "error": None,
    }


def export_tab_parts_only(
    doc: Dict[str, Any],
    originals_dir: str,
    safe_doc_title: str,
    *,
    log_fn: Optional[Callable[[str], None]] = None,
) -> Optional[str]:
    """
    When full Drive export already failed: write one DOCX per tab under
    `{originals_dir}/{safe_doc_title}_by_tab/`. Returns absolute tab_dir or None.
    """
    log = log_fn or (lambda _m: None)
    if not doc.get("tabs"):
        return None
    from tools.scraper.gdoc_tab_to_docx import export_all_tabs_to_directory

    tab_dir = os.path.join(originals_dir, f"{safe_doc_title}_by_tab")
    paths = export_all_tabs_to_directory(doc, tab_dir, safe_doc_title)
    if not paths:
        return None
    log(f"Wrote {len(paths)} tab DOCX under {tab_dir}")
    return os.path.abspath(tab_dir)
