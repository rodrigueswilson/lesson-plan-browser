"""Tests for local-first curriculum resource URL resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.database.curriculum import CurriculumDatabase
from backend.services.curriculum_resource_resolve import (
    media_type_for_curriculum_path,
    resolve_resource_open_url,
    validated_local_file_path,
)


def _patch_export_roots(monkeypatch: pytest.MonkeyPatch, *roots: Path) -> None:
    r = [p.resolve() for p in roots]
    monkeypatch.setattr(
        CurriculumDatabase,
        "curriculum_export_search_roots",
        staticmethod(lambda: list(r)),
    )


def test_resolve_without_row_uses_inferred_drive_url_when_no_local_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "backend.database.curriculum.CurriculumDatabase.discover_local_path_for_google_doc",
        staticmethod(lambda _gid: None),
    )
    url, source = resolve_resource_open_url("abc123XYZ", None)
    assert source == "remote_inferred"
    assert "abc123XYZ" in url


def test_resolve_without_row_uses_local_when_disk_export_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gid = "abc123XYZ"
    doc = tmp_path / f"{gid}.docx"
    doc.write_bytes(b"x")

    def _discover(google_id: str) -> str | None:
        p = tmp_path / f"{google_id}.docx"
        return str(p.resolve()) if p.is_file() else None

    monkeypatch.setattr(
        "backend.database.curriculum.CurriculumDatabase.discover_local_path_for_google_doc",
        staticmethod(_discover),
    )
    _patch_export_roots(monkeypatch, tmp_path)

    url, source = resolve_resource_open_url(gid, None)
    assert source == "local"
    assert url == f"/api/curriculum/resources/google-id/{gid}/file"


def test_validated_path_without_row_when_disk_export_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gid = "id1"
    doc = tmp_path / f"{gid}.pdf"
    doc.write_bytes(b"%PDF-1.4")

    def _discover(google_id: str) -> str | None:
        p = tmp_path / f"{google_id}.pdf"
        return str(p.resolve()) if p.is_file() else None

    monkeypatch.setattr(
        "backend.database.curriculum.CurriculumDatabase.discover_local_path_for_google_doc",
        staticmethod(_discover),
    )
    _patch_export_roots(monkeypatch, tmp_path)

    path = validated_local_file_path(gid, None)
    assert path is not None
    assert path.resolve() == doc.resolve()


def test_resolve_with_row_no_local_path_uses_original() -> None:
    url, source = resolve_resource_open_url(
        "id1",
        {"original_url": "https://example.com/x", "local_path": None},
    )
    assert source == "remote"
    assert url == "https://example.com/x"


def test_resolve_row_falls_back_to_discover_when_local_path_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gid = "rowFallback"
    doc = tmp_path / f"{gid}.docx"
    doc.write_bytes(b"y")

    def _discover(google_id: str) -> str | None:
        p = tmp_path / f"{google_id}.docx"
        return str(p.resolve()) if p.is_file() else None

    monkeypatch.setattr(
        "backend.database.curriculum.CurriculumDatabase.discover_local_path_for_google_doc",
        staticmethod(_discover),
    )
    _patch_export_roots(monkeypatch, tmp_path)

    url, source = resolve_resource_open_url(
        gid,
        {"original_url": "https://docs.google.com/document/d/x/edit", "local_path": None},
    )
    assert source == "local"
    assert url.endswith(f"/{gid}/file")


def test_discover_finds_export_doc_ids_style_nested(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """tools/scraper/export_doc_ids_to_docx.py -> {stem}_{doc_id[:8]}.docx"""
    scraped_root = tmp_path / "reference_docs" / "scraped"
    batch = scraped_root / "batch"
    batch.mkdir(parents=True)
    gid = "1_yHvguDhJIZmrIwY3ZcW-BIhfQH5VtH2xs1KtKlnNVY"
    f = batch / f"Grade_3_ELA_All_Units_{gid[:8]}.docx"
    f.write_bytes(b"PK")
    monkeypatch.setattr(
        CurriculumDatabase,
        "curriculum_export_search_roots",
        staticmethod(lambda: [scraped_root.resolve()]),
    )
    out = CurriculumDatabase.discover_local_path_for_google_doc(gid)
    assert out == str(f.resolve())


def test_discover_finds_docs_api_json_stem_and_html_sibling(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """export_doc_ids_to_docx fallback writes *.docs-api.json; pathlib .stem is wrong for sidecars."""
    scraped = tmp_path / "reference_docs" / "scraped" / "grade3_ela_exports"
    scraped.mkdir(parents=True)
    gid = "abcDEFGHijklmnop"
    base = f"MyExport_{gid[:8]}"
    (scraped / f"{base}.docs-api.json").write_text(
        '{"documentId": "' + gid + '"}',
        encoding="utf-8",
    )
    html = scraped / f"{base}.html"
    html.write_bytes(b"<!doctype html><title>x</title>")
    monkeypatch.setattr(CurriculumDatabase, "repo_root", staticmethod(lambda: tmp_path))
    monkeypatch.setattr(
        CurriculumDatabase,
        "curriculum_export_search_roots",
        staticmethod(lambda: [(tmp_path / "reference_docs" / "scraped").resolve()]),
    )
    out = CurriculumDatabase.discover_local_path_for_google_doc(gid)
    assert out == str(html.resolve())


def test_discover_finds_main_scraper_originals_sibling_docx(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """tools/scraper/main.py -> .../originals/{safe_title}.json + .docx"""
    scraped = tmp_path / "reference_docs" / "scraped"
    orig = scraped / "Grade_3" / "ELA" / "Unit_8" / "originals"
    orig.mkdir(parents=True)
    gid = "abcDEFGHijklmnopQRST"
    (orig / "My_Document_Title.json").write_text(
        '{"documentId": "' + gid + '", "title": "My Document Title"}',
        encoding="utf-8",
    )
    docx = orig / "My_Document_Title.docx"
    docx.write_bytes(b"PK")
    monkeypatch.setattr(
        CurriculumDatabase,
        "curriculum_export_search_roots",
        staticmethod(lambda: [scraped.resolve()]),
    )
    monkeypatch.setattr(CurriculumDatabase, "repo_root", staticmethod(lambda: tmp_path))
    out = CurriculumDatabase.discover_local_path_for_google_doc(gid)
    assert out == str(docx.resolve())


def test_media_type_for_curriculum_path() -> None:
    assert media_type_for_curriculum_path(Path("a.pdf")) == "application/pdf"
    assert (
        media_type_for_curriculum_path(Path("a.docx"))
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert media_type_for_curriculum_path(Path("a.bin")) == "application/octet-stream"
