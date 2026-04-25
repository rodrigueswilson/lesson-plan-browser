# Real unit DOCX compare — Docling vs LP parser (Wave 2)

**Scope:** Real unit-export DOCX comparison for table fidelity, reading order/section-routing relevance, and hyperlink/provenance behavior (A4).  
**Fixture:** `reference_docs/scraped/batch_8_linked_mar2026/Unit_2__Area_and_Multiplication/originals/Unit_2__Area_and_Multiplication.docx`

## Commands run (repo root)

```text
DOCLING_SMOKE_SOURCE="D:\LP\reference_docs\scraped\batch_8_linked_mar2026\Unit_2__Area_and_Multiplication\originals\Unit_2__Area_and_Multiplication.docx" python docs/research/spikes/docling_curriculum_smoke/smoke_convert.py
python docs/research/spikes/lp_parser_hyperlink_dump/dump_lp_hyperlinks.py "D:\LP\reference_docs\scraped\batch_8_linked_mar2026\Unit_2__Area_and_Multiplication\originals\Unit_2__Area_and_Multiplication.docx" --json-out docs/research/repos/lp_hyperlink_dump_unit2_area_multiplication.json
python tools/scraper/scan_curriculum_docx.py "D:\LP\reference_docs\scraped\batch_8_linked_mar2026\Unit_2__Area_and_Multiplication\originals\Unit_2__Area_and_Multiplication.docx" --subject Math --json-out docs/research/repos/scan_unit2_area_multiplication_math.json
```

## Artifacts

- Docling smoke output (clipped): `docs/research/repos/docling_real_unit2_smoke_output.txt`
- Docling full markdown export: `docs/research/repos/docling_real_unit2_full.md`
- LP hyperlink dump JSON: `docs/research/repos/lp_hyperlink_dump_unit2_area_multiplication.json`
- LP scan summary JSON: `docs/research/repos/scan_unit2_area_multiplication_math.json`

## Findings

### 1) Table fidelity and reading order

- **Docling:** High table retention signal (`|` count `1246`) and many markdown links (`408`), but the export is effectively one giant markdown line/table-centric block in this run, which makes deterministic section segmentation difficult to consume directly.
- **LP parser:** Produces structured stream records (`stream_items=1907`) that preserve traversal order for downstream deterministic routing.
- **Interpretation:** Docling is useful as auxiliary layout evidence; LP remains the reliable ingest baseline for structured section-level routing.

### 2) Heading/section routing relevance

- **LP scan evidence:** `lesson_title_hits=37`, `standards_token_hits=184`, including explicit lesson headers like `LESSON 1: WHAT IS AREA?` through `LESSON 15: NEW ROOM (OPTIONAL)`.
- **Docling output:** Contains lesson tokens (`LESSON n` count `105`) but without deterministic boundary metadata used by LP routing logic.
- **Interpretation:** For A1/A2 routing decisions, LP deterministic logic remains the operative path; Docling text alone does not replace routing heuristics.

### 3) Hyperlink/provenance behavior (A4)

- **LP hyperlink dump:** `hyperlink_run_count=475` across `377` paragraphs; `45` runs include parsed `google_id`.
- **Docling markdown:** Keeps link text/URLs, but no LP-specific provenance marker semantics (for example no `data-resource-id` attributes).
- **Interpretation:** Docling can preserve link presence, but LP parser remains the provenance SSOT for resource-id-aware behavior expected by local-first link workflows.

## Decision note (Wave 2)

- **Deterministic-first stays explicit:** No production parser behavior changes from this compare.
- **Docling status:** Remains `Dependency-candidate` for optional second-pass evidence generation, not deterministic ingest replacement.
