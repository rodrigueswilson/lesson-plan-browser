"""
Export Google Docs to DOCX via Drive API (for curriculum ingest and offline QA).

Native Google Docs are exported; uploaded .docx files on Drive are downloaded with
files.get_media (DocsClient.fetch_docx_for_curriculum_result).

Requires OAuth credentials under tools/scraper/credentials/ (see SETUP.md).

Usage (repo root):
  python tools/scraper/export_doc_ids_to_docx.py --out reference_docs/scraped/grade3_ela_exports DOC_ID1 DOC_ID2
  python tools/scraper/export_doc_ids_to_docx.py --preset grade3-ela-sample
  python tools/scraper/export_doc_ids_to_docx.py --preset grade3-ela-all-units

Presets are curated from reference_docs/scraped_registry.json (cross-subject / Phase 4 sample paths).

Very large Google Docs may hit the Drive API export limit for DOCX/PDF. By default this tool then
fetches the document via the Docs API and writes one synthesized .docx per navigation tab under
`{stem}_{id8}_by_tab/` (same approach as tools/scraper/main.py). If the doc has no tabs, it falls
back to PDF then a full JSON snapshot.

Inspect tab structure (navigation tabs) on a saved snapshot or live doc:
  python tools/scraper/inspect_gdoc_tabs.py --json-path path/to/file.docs-api.json --chars

Build a small .docx from one tab (bypasses Drive export size limit on the parent doc):
  python tools/scraper/gdoc_tab_to_docx.py --json-path path/to/file.docs-api.json --tab-title "Grade 3 Unit 8" --out Unit8.docx
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.scraper.docs_client import DocsClient
from tools.scraper.gdoc_docx_export import export_tab_parts_only, is_export_size_limited_error

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_PDF_MIME = "application/pdf"

# Google Doc IDs from scraped_registry.json (titles documented for operators).
PRESETS: dict[str, list[tuple[str, str]]] = {
    # Master compendium (all Grade 3 ELA units, including Unit 8); same ID as registry
    # Grade 3 / Uncategorized_Subject / 03_-_Third_Grade_Unit_Description_and_Summary_of_Key_Learning
    "grade3-ela-all-units": [
        ("1_yHvguDhJIZmrIwY3ZcW-BIhfQH5VtH2xs1KtKlnNVY", "Grade_3_ELA_All_Units_including_8"),
    ],
    "grade3-ela-sample": [
        ("1_yHvguDhJIZmrIwY3ZcW-BIhfQH5VtH2xs1KtKlnNVY", "Grade_3_ELA_All_Units_including_8"),
        ("14Vnl0MgL-w_ATz5LzuR-keQ3QWJcBlqeTYLIddPM0lg", "K-8_ELA_Pacing_Guide_SY_25-26"),
        ("1Mn99HCsUm19VGyivXTmgJMu8u0WYclb4j9DRWRVdv2s", "Grade_3_Unit_10_Charlottes_Web"),
        ("1-rlV9tpDNTmlqF5Vke8yXJmmq9nWNRsWuIokW_QIC6k", "ELA_3-5_Career_Readiness"),
    ],
    # Grade 3 / Science / Grade_3_Science_Curriculum in scraped_registry.json
    "grade3-science-curriculum": [
        ("1qXSzo0hV4JvXVjGfODDM6sViaypCtPJr", "Grade_3_Science_Curriculum"),
    ],
}


def _sanitize_filename(name: str) -> str:
    base = "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip()
    base = re.sub(r"_+", "_", base).strip("_")
    return (base or "export")[:180]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default=str(_REPO_ROOT / "reference_docs" / "scraped" / "exported_docx"),
        help="Output directory for .docx files",
    )
    ap.add_argument(
        "--preset",
        choices=sorted(PRESETS.keys()),
        default=None,
        help="Export a curated ID list from the curriculum registry notes",
    )
    ap.add_argument(
        "doc_ids",
        nargs="*",
        help="Google Doc file IDs (ignored if --preset is set)",
    )
    ap.add_argument(
        "--no-fallback",
        action="store_true",
        help="Skip PDF and Docs API JSON fallbacks when DOCX export fails",
    )
    args = ap.parse_args()
    use_fallback = not args.no_fallback

    if args.preset:
        jobs = [(doc_id, stem) for doc_id, stem in PRESETS[args.preset]]
    elif args.doc_ids:
        jobs = [(did, did[:12]) for did in args.doc_ids]
    else:
        ap.print_help()
        print("\nError: provide --preset or at least one DOC_ID.", file=sys.stderr)
        return 2

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    client = DocsClient()
    ok, failed = 0, 0
    for doc_id, stem in jobs:
        path = out_dir / f"{_sanitize_filename(stem)}_{doc_id[:8]}.docx"
        print(f"Exporting {doc_id} -> {path.name} ...", flush=True)
        docx_ok, docx_err = client.fetch_docx_for_curriculum_result(doc_id, str(path))
        if docx_ok and path.is_file() and path.stat().st_size > 0:
            ok += 1
            print(f"  OK DOCX ({path.stat().st_size} bytes)", flush=True)
            continue
        if path.is_file():
            path.unlink(missing_ok=True)

        size_limited = is_export_size_limited_error(docx_err)
        if use_fallback and size_limited:
            key = f"{_sanitize_filename(stem)}_{doc_id[:8]}"
            print("  DOCX blocked by Drive size limit; trying per-tab DOCX (Docs API) ...", flush=True)
            doc_api = client.get_document(doc_id)
            if doc_api:
                tab_dir = export_tab_parts_only(
                    doc_api,
                    str(out_dir),
                    key,
                    log_fn=lambda m: print(f"    {m}", flush=True),
                )
                if tab_dir:
                    ok += 1
                    print(f"  OK tab-split DOCX directory: {tab_dir}", flush=True)
                    continue

            pdf_path = out_dir / f"{key}.pdf"
            print(f"  Tab split unavailable or empty; trying PDF -> {pdf_path.name} ...", flush=True)
            pdf_ok, pdf_err = client.export_document_result(doc_id, str(pdf_path), mime_type=_PDF_MIME)
            if pdf_ok and pdf_path.is_file() and pdf_path.stat().st_size > 0:
                ok += 1
                print(f"  OK PDF ({pdf_path.stat().st_size} bytes)", flush=True)
                print(
                    "  NOTE: table_extractor ingest expects DOCX. In Google Docs use "
                    "File > Download > Microsoft Word (.docx) for this document.",
                    flush=True,
                )
                continue
            if not pdf_ok:
                print(f"  PDF export also failed: {pdf_err}", flush=True)

            json_path = out_dir / f"{key}.docs-api.json"
            print(f"  Trying Docs API JSON snapshot -> {json_path.name} ...", flush=True)
            if client.get_document_json(doc_id, str(json_path)) and json_path.is_file() and json_path.stat().st_size > 0:
                ok += 1
                print(f"  OK Docs API JSON ({json_path.stat().st_size} bytes)", flush=True)
                print(
                    "  NOTE: Use gdoc_tab_to_docx.py on this JSON or browser DOCX download for ingest.",
                    flush=True,
                )
                continue

        if not docx_ok:
            print(f"  DOCX export failed: {docx_err}", flush=True)
        failed += 1

    print(f"Done. {ok} exported, {failed} failed. Output: {out_dir}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
