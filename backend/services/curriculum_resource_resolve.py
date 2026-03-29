"""Local-first resolution for curriculum resources (Google Doc ids in lesson HTML)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from backend.database.curriculum import CurriculumDatabase

_MEDIA_TYPE_BY_SUFFIX: Dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".html": "text/html; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
}


def media_type_for_curriculum_path(path: Path) -> str:
    """Content-Type for FileResponse; default octet-stream for unknown extensions."""
    return _MEDIA_TYPE_BY_SUFFIX.get(path.suffix.lower(), "application/octet-stream")


def _discovered_local_path(google_id: str) -> Optional[str]:
    """On-disk export (CURRICULUM_LOCAL_FILES_ROOT and/or reference_docs/scraped layouts)."""
    return CurriculumDatabase.discover_local_path_for_google_doc(google_id)


def _effective_local_path_str(google_id: str, row: Optional[Dict[str, Any]]) -> Optional[str]:
    """Prefer resources.local_path; else discover on disk."""
    if row:
        lp = (row.get("local_path") or "").strip()
        if lp:
            return lp
    return _discovered_local_path(google_id)


def resolve_resource_open_url(
    google_id: str,
    row: Optional[Dict[str, Any]],
) -> Tuple[str, str]:
    """
    Return (url, source) where source is 'local', 'remote', or 'remote_inferred'.

    Local URL is same-origin path to the file-serving route (client opens in new tab).
    """
    base = "/api/curriculum/resources/google-id"
    file_url = f"{base}/{google_id}/file"
    inferred = f"https://docs.google.com/document/d/{google_id}/edit"

    original = inferred
    if row and (row.get("original_url") or "").strip():
        original = (row.get("original_url") or "").strip()

    local_path = _effective_local_path_str(google_id, row)
    if not local_path:
        if not row:
            return inferred, "remote_inferred"
        return original, "remote"

    path = Path(local_path)
    if not path.is_file():
        if not row:
            return inferred, "remote_inferred"
        return original, "remote"

    if not CurriculumDatabase.path_is_under_export_roots(path):
        if not row:
            return inferred, "remote_inferred"
        return original, "remote"
    return file_url, "local"


def validated_local_file_path(google_id: str, row: Optional[Dict[str, Any]]) -> Optional[Path]:
    """Return Path to serve if safe and file exists, else None."""
    if not google_id:
        return None
    local_path = _effective_local_path_str(google_id, row)
    if not local_path:
        return None
    path = Path(local_path)
    if not path.is_file():
        return None
    if not CurriculumDatabase.path_is_under_export_roots(path):
        return None
    return path.resolve()
