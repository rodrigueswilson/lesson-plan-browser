"""
Research-only: Docling DocumentConverter on a local curriculum PDF (or URL).
See README.md in this directory.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
_DEFAULT_PDF_REL = (
    "Copy_of_02___Second_Grade_Unit_Description_and_Summary_of_Key_Learning"
    "/Grade_2_Unit_1/resources/originals/PDF_1qgoZUKbW28_8SWOMlHzUIIGHKxtGD1s6.pdf"
)
# Committed test DOCX (hyperlinks + tables) when curriculum PDF tree is absent
_FALLBACK_DOCX_REL = "docs/archive/test-files/test_hyperlink_robustness.docx"


def _default_source() -> str:
    env = os.getenv("DOCLING_SMOKE_SOURCE")
    if env:
        return env
    pdf = _REPO / _DEFAULT_PDF_REL
    if pdf.is_file():
        return str(pdf)
    docx = _REPO / _FALLBACK_DOCX_REL
    if docx.is_file():
        return str(docx)
    return "https://arxiv.org/pdf/2408.09869"


def main() -> None:
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        print("Install: pip install 'docling>=2.0'", file=sys.stderr)
        sys.exit(1)

    source = _default_source()
    print(f"Source: {source}", file=sys.stderr)
    converter = DocumentConverter()
    result = converter.convert(source)
    md = result.document.export_to_markdown()
    clip = 8000
    out = md if len(md) <= clip else md[:clip] + "\n\n[... clipped ...]\n"
    print(out)


if __name__ == "__main__":
    main()
