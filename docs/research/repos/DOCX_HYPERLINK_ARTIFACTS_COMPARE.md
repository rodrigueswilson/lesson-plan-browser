# DOCX hyperlink test — three artifacts (reference)

**Fixture:** `docs/archive/test-files/test_hyperlink_robustness.docx`  
**Purpose:** Record what each artifact measures so future compares do not conflate **layout export**, **LP parser SSOT**, and **curriculum regex scans**.

## Artifacts

| Artifact | Path (typical) | Producer |
|----------|----------------|----------|
| Docling Markdown | `docling_test_hyperlink.md` (repo root; regenerable) | `docs/research/spikes/docling_curriculum_smoke/smoke_convert.py` with `DOCLING_SMOKE_SOURCE` → fixture DOCX |
| LP hyperlink dump | `docs/research/repos/lp_hyperlink_dump_test_hyperlink.json` | `docs/research/spikes/lp_parser_hyperlink_dump/dump_lp_hyperlinks.py` |
| Math scan | `docs/research/repos/scan_test_hyperlink.json` | `python tools/scraper/scan_curriculum_docx.py <docx> --subject Math --json-out …` |

## Commands (repo root)

```text
python docs/research/spikes/docling_curriculum_smoke/smoke_convert.py
python docs/research/spikes/lp_parser_hyperlink_dump/dump_lp_hyperlinks.py
python tools/scraper/scan_curriculum_docx.py docs/archive/test-files/test_hyperlink_robustness.docx --subject Math --json-out docs/research/repos/scan_test_hyperlink.json
```

## Comparison (what matches, what does not)

**Agrees on scale:** For this fixture, Docling’s linear structure and LP `parse_to_stream` align with **76** top-level stream items — same as **`stream_items` / `paragraph_items`** in the Math scan summary.

**Hyperlinks (Docling vs LP):** Both surface **four** links: anchor text `Lenni Lenape`, targets `http://example.com/0` … `/3`. LP adds `json_to_html` snippets (`<a href>` with `target` / `rel`); **`data-resource-id`** appears only when the URL matches the Google Doc id regex in `table_extractor.py` (not for `example.com`).

**Presentation:** Docling Markdown may show a different bullet glyph than LP (`ò` vs `•`) for the same list paragraphs; that is a rendering/encoding artifact, not a URL disagreement.

**Math scan:** Reports **0** `lesson_title_hits` and **0** `standards_token_hits` — expected for a hyperlink/layout test file. It does **not** extract hyperlinks or tables; do **not** use it alone to judge Docling vs LP fidelity.

## When to use which

| Need | Use |
|------|-----|
| Tables + reading order in MD | Docling (or similar layout exporter) |
| Runs, URLs, `google_id`, ingest HTML shape | LP dump or real `RecursiveTableParser` ingest path |
| “Does this DOCX look like our Math lesson plan?” | `scan_curriculum_docx.py` with appropriate `--subject` |

## Evidence log

Run history and maintainer notes: [wave_2_evidence.md](wave_2_evidence.md) (Runs B–C).

**LP tag:** A4 (provenance / SSOT — hyperlinks, `data-resource-id`).
