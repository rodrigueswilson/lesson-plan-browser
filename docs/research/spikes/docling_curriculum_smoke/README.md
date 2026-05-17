# Docling curriculum smoke (research only)

Converts a **local file or URL** to Markdown via Docling’s `DocumentConverter`, for **Wave 2** comparison with `RecursiveTableParser` / DOCX ingest.

**Default source order:** `DOCLING_SMOKE_SOURCE` if set; else Grade 2 Unit 1 curriculum **PDF** if `Copy_of_02___...` exists; else committed **[test_hyperlink_robustness.docx](../../../archive/test-files/test_hyperlink_robustness.docx)** (tables + example.com links); else Docling arXiv sample PDF URL.

## Setup

```bash
pip install "docling>=2.0"
```

Python **3.10+** required.

## Run

Default: see order above (curriculum PDF, then hyperlink test DOCX, then arXiv URL).

```bash
python docs/research/spikes/docling_curriculum_smoke/smoke_convert.py
```

Custom input:

```bash
set DOCLING_SMOKE_SOURCE=D:\path\to\unit.pdf
python docs/research/spikes/docling_curriculum_smoke/smoke_convert.py
```

Output: first ~4000 characters of Markdown to stdout (full doc can be large). Redirect to a file if needed:

```bash
python docs/research/spikes/docling_curriculum_smoke/smoke_convert.py > docling_out.md
```

## Notes

- First run may **download layout models** (network, disk).
- This is **not** wired to `tools/scraper` or `curriculum.db`; use output only for qualitative layout/table sanity vs existing pipeline.
