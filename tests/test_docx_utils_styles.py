"""
Tests for DOCX style normalization utilities (normalize_styles_via_file, etc.).
Session 8: combined-original styles.
"""

import pytest
from docx import Document
from io import BytesIO

from tools.docx_utils import diagnose_style_conflicts, normalize_styles_via_file


def test_normalize_styles_via_file_returns_valid_stream():
    """normalize_styles_via_file returns a non-empty BytesIO and result opens as a doc with styles."""
    master = Document()
    master.add_paragraph("Master")
    target = Document()
    target.add_paragraph("Target")

    stream = normalize_styles_via_file(master, target)
    assert stream is not None
    assert isinstance(stream, BytesIO)
    assert len(stream.getvalue()) > 0

    stream.seek(0)
    doc = Document(stream)
    assert len(doc.styles) >= 1


def test_diagnose_style_conflicts_returns_dict():
    """diagnose_style_conflicts returns a dict with expected keys."""
    master = Document()
    target = Document()
    diagnosis = diagnose_style_conflicts(master, target)
    assert isinstance(diagnosis, dict)
    assert "style_counts" in diagnosis
    assert "conflicting_styles" in diagnosis
    assert diagnosis["style_counts"]["master"] >= 0
    assert diagnosis["style_counts"]["target"] >= 0
