# Large Google Docs: Drive export limits, tabs, and Grade 3 ELA compendium

**Date:** 2026-03-28  
**Scope:** Download/export strategy for native Google Docs that exceed Drive API export limits, with emphasis on **navigation tabs** as split boundaries.

## Summary

- **Drive API** `files.export` to DOCX/PDF fails for the Grade 3 ELA compendium with **`exportSizeLimitExceeded`** (document too large for server-side export).
- **Docs API** `documents.get(..., includeTabsContent=true)` succeeds and produces a large JSON snapshot (local fallback in `tools/scraper/export_doc_ids_to_docx.py`).
- The compendium **`1_yHvguDhJIZmrIwY3ZcW-BIhfQH5VtH2xs1KtKlnNVY`** is organized as **11 top-level tabs** (no nested `childTabs` in this doc): **Front Matter** plus **Grade 3 Units 1–9, 11**. There is **no Unit 10 tab** in this file (Unit 10 / Charlotte’s Web exists as a separate registry entry).
- **Unit 8** tab id: `t.2plykckkv6ev`, title `Grade 3 Unit 8`, ~98k approximate visible characters in paragraph/table text (see measured run below).

## Official references (for ongoing research)

- [Work with tabs](https://developers.google.com/workspace/docs/api/how-tos/tabs) — `includeTabsContent`, `document.tabs`, `tab.documentTab.body`, `childTabs`.
- [Drive: Download & export files](https://developers.google.com/drive/api/guides/manage-downloads) — `files.export`, MIME types, limits.
- [files.export](https://developers.google.com/drive/api/reference/rest/v3/files/export) — `exportSizeLimitExceeded`.

Community threads (verify dates; API behavior may change): search `exportSizeLimitExceeded` and `Drive API export 10MB` on Stack Overflow and [google-api-python-client issues](https://github.com/googleapis/google-api-python-client/issues).

## Empirical: tab tree (Docs API JSON)

Source: `reference_docs/scraped/grade3_ela_exports/Grade_3_ELA_All_Units_including_8_1_yHvguD.docs-api.json`  
Tool: `python tools/scraper/inspect_gdoc_tabs.py --json-path <path> --chars`

| # | tabId | Title | Structural elements | approx_chars | ~JSON bytes (single tab subtree) |
|---|--------|--------|---------------------|--------------|----------------------------------|
| 1 | t.0 | Front Matter | 352 | 47,083 | ~676 KB |
| 2 | t.uptgcfiqu8pr | Grade 3 Unit 1 | 46 | 117,763 | ~2.2 MB |
| 3 | t.u1cg95g8dfbs | Grade 3 Unit 2 | 37 | 99,542 | ~1.8 MB |
| 4 | t.9vfaqefj1p25 | Grade 3 Unit 3 | 48 | 117,788 | ~2.1 MB |
| 5 | t.kofvr9ldt5q6 | Grade 3 Unit 4 | 52 | 94,628 | ~2.0 MB |
| 6 | t.fho0ezypio1v | Grade 3 Unit 5 | 51 | 101,535 | ~2.1 MB |
| 7 | t.vhmo4oy2ur6b | Grade 3 Unit 6 | 266 | 85,612 | ~3.1 MB |
| 8 | t.887358ewlz8r | Grade 3 Unit 7 | 57 | 135,010 | ~2.5 MB |
| 9 | t.2plykckkv6ev | **Grade 3 Unit 8** | 44 | **98,402** | ~1.5 MB |
| 10 | t.jnhkzzhqs688 | Grade 3 Unit 9 | 44 | 99,882 | ~1.6 MB |
| 11 | t.evno8y9mxkm8 | Grade 3 Unit 11 | 80 | 74,535 | ~1.1 MB |

**Note:** `approx_chars` counts `textRun.content` in paragraphs and table cells only; it is a lower-bound proxy, not rendered DOCX size.

## Implications

1. **Drive API does not export “one tab”.** Export is per **file id**. Tab-aware splitting requires **Docs API** (or manual) steps to produce **separate files** or **non-DOCX** pipelines.
2. **Per-tab local DOCX:** `gdoc_tab_to_docx.py` synthesizes `.docx` from one tab in the API JSON (best-effort layout; good for pipeline smoke and often sufficient for ingest).
3. **Optional:** new Google Doc + `files.export` for a closer match to Google’s native Word export.
4. **Operational path:** browser **File → Download → Microsoft Word (.docx)** when API JSON is unavailable; keep **`.docs-api.json`** for tab-scoped synthesis.
5. **Phase 4 sample `ELA_3_U8_sample`:** use **Unit 8** synthesized DOCX or a browser export; tab id `t.2plykckkv6ev`.

## Repo tooling

| Tool | Role |
|------|------|
| `tools/scraper/export_doc_ids_to_docx.py` | DOCX/PDF export; JSON fallback; presets `grade3-ela-all-units`, `grade3-ela-sample` |
| `tools/scraper/inspect_gdoc_tabs.py` | Tab tree + optional char / JSON-size estimates from live API or `.docs-api.json` |
| `tools/scraper/gdoc_tab_to_docx.py` | **Synthesize a local .docx from one tab** of a `.docs-api.json` (or live fetch); bypasses Drive export size limit |
| `tools/scraper/docs_client.py` | Docs + Drive clients; `get_document` already uses `includeTabsContent=True` |

### Example: Grade 3 Unit 8 only (for `ELA_3_U8_sample` ingest)

After a JSON snapshot exists (from exporter fallback or `--write-json` on `inspect_gdoc_tabs.py`):

```text
python tools/scraper/gdoc_tab_to_docx.py --json-path reference_docs/scraped/grade3_ela_exports/Grade_3_ELA_All_Units_including_8_1_yHvguD.docs-api.json ^
  --tab-title "Grade 3 Unit 8" --out reference_docs/scraped/grade3_ela_exports/Grade3_ELA_Unit8_from_api_tab.docx
```

Smoke (2026-03-28): output ~62 KB DOCX; `RecursiveTableParser.parse_to_stream` produced hundreds of items (structure accepted by pipeline).

## Recommended next steps (prioritized)

1. **Done in repo:** `gdoc_tab_to_docx.py` builds **Unit 8–only DOCX** from the API JSON (no new Google Doc required). Prefer verifying **ingest quality** against a browser-exported Unit 8 DOCX when available.
2. **Optional:** Duplicate one tab into a new Google Doc and `files.export` for pixel-perfect Word output if synthesis fidelity is insufficient.
3. **Document** any Stack Overflow / Issue Tracker workaround (e.g. legacy `exportLinks`) against **current** Drive v3 docs before relying on it in production.
4. **Registry:** keep a single SSOT row for the compendium id; Unit 10 remains a separate linked doc in `scraped_registry.json` unless the district adds a tab later.
