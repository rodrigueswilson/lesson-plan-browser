# Phase 5 – Cross-grade representative sample matrix (Grades 2–8)

**SSOT:** `docs/curriculum/PHASED_ROLLOUT_PLAN.md` — Phase 5, Stages B/C (“Representative sampling strategy”).  
**Registry SSOT:** `reference_docs/scraped_registry.json`.

## Variance classes (template / edge intent)

| Class | Intent | Example sources |
|--------|--------|-----------------|
| `math_im_elementary` | IM-style unit guide, elementary | Grade 2–3 `Math` keys |
| `math_im_upper_ms` | IM-style unit guide, upper ES / MS | `Uncategorized_Grade` → `Math` (e.g. measurement, Pythagorean) |
| `ela_compendium_tabs` | Multi-tab “Summary of Key Learning” compendium | `04_-_Fourth_*`, `05_-_Fifth_*`, G3 `03_-_Third_*` |
| `ela_unit_guide_ms_hs` | Full per-grade ELA unit Google Doc | `Grade 6_ELA_Unit *` … `Grade 8_ELA_Unit *` under `Uncategorized_Grade` → `ELA` |
| `ela_partial_structured` | Summary matrix present; per-lesson structured table sparse or absent | Observed `ELA_2_U8_sample` (see below) |

## Stage C clusters — curated primary rows

Each row lists registry navigation (top-level keys), canonical Doc ID, proposed `unit_id` seed for `ingest_wave_unit.py` (operator), and gate status for **this session**.

| Cluster | Subject | Registry path (ellipsis) | Doc ID | Proposed unit_id | Ingest + verify | Notes |
|---------|---------|--------------------------|--------|------------------|-----------------|-------|
| 2–3 | Math | `Grade 2` → `Math` → `Unit 1_...` | `15E1iQ_xlIaAes5NPDAdkNRm4-0eYV7PwQ6nOlOnjSnU` | `Math_2_U1_15E1iQ_x` | **PASS** | 15 lessons in DB; aligns with `math_im_elementary`. |
| 2–3 | Math | `Grade 3` → `Math` (corpus) | (multiple) | `Math_3_U2_1hBoK4uk` etc. | **PASS** | Phase 3 ladder + full G3 Math corpus in DB. |
| 2–3 | ELA | `Grade 2` → `Uncategorized_Subject` → `Copy_of_02_-_Second_Grade_...` | `1Du6ukeZavMKEZt0nCzamwd7OfH4Jr-Liygqdwo2gjak` | `ELA_2_U8_sample` | **PASS** | 15 lessons; `ela_key_learning_summary` populated on all lessons; **`ela_lesson_plan_structured` = 0** (edge: partial structured). |
| 2–3 | ELA | `Grade 3` → `Uncategorized_Subject` → `03_-_Third_Grade_...` | `1_yHvguDhJIZmrIwY3ZcW-BIhfQH5VtH2xs1KtKlnNVY` | `ELA_3_U8_sample` | **PASS** | 12 lessons; both `ela_key_learning_summary` and `ela_lesson_plan_structured` populated (Phase 4.1 path). |
| 4–5 | ELA | `Uncategorized_Grade` → `ELA` → `04_-_Fourth_Grade_Unit_Description_and_Summary_of_Key_Learning` | `1jeeDNSMhT4k_-kMzR65EszWgKkCznHOn0KMVtdp4ofs` | `ELA_4_compendium_sample` | **PASS** | **21** lessons. Local `originals/*.json` tab build → `gdoc_tab_to_docx.py` → `ingest_wave_unit.py --docx …`. Latest ingest report: `ingest_reports/2026-03-29T15-31-35Z_bf3db7f9.json`. |
| 4–5 | ELA | `Uncategorized_Grade` → `ELA` → `05_-_Fifth_Grade_Unit_Description_and_Summary_of_Key_Learning` | `1vRv3y0geSVJBGOHfgtplWNygz4nfwSE4RwAM1GbZQWY` | `ELA_5_compendium_sample` | **PASS** | **15** lessons. Same local-JSON path as G4. Latest ingest report: `ingest_reports/2026-03-29T15-31-43Z_2e186224.json`. |
| 4–5 | Math | `Uncategorized_Grade` → `Math` → `Unit 4_Understanding_Addition_and_Subtraction` | `1aMiqygM9kCrQ0DKFGPma3lKT91lJQkAUF-H8TvQMbus` | `Math_4_5_sample_U4` (TBD) | **DEFERRED** | Phase 5 **closed without DB ingest** for this row (no local root-`documentId` JSON). Revisit only if these units are loaded later. |
| 4–5 | Math | `Uncategorized_Grade` → `Math` → `Unit 5_Numbers_to_1000` | `1S9fRcM1-6futZzmOgOEg3eQ1hfRh8YpXHfjmyiPTu08` | `Math_4_5_sample_U5` (TBD) | **DEFERRED** | Same as U4: documented for registry traceability; not ingested in Phase 5. |
| 6–8 | ELA | `Uncategorized_Grade` → `ELA` → `Unit 2` (multi-grade) | `1iVNkWwfzOsu9p7zJsCHqrlWFFQ-p33GsmjqUXP1nFfY` | `ELA_6_U1_sample` | **PASS** | **34** lessons. Merged Front Matter + unit tab via `phase5_vertical_sample_ingest.py`. Paragraph “Lesson *” anchors were absent in synthesized DOCX; `RecursiveTableParser` **coalesces from the Summary of Key Learning table** when coverage is sparse (see `table_extractor.py`). Report: `ingest_reports/2026-03-29T15-31-53Z_6efea611.json`. |
| 6–8 | ELA | `Uncategorized_Grade` → `ELA` → `Unit 1` (multi-grade) | `1ordR_c50CNntMjqavOQR9JHgfzklI2CUprYDjgfOdOU` | `ELA_8_U1_sample` | **PASS** | **24** lessons. Same merged-tab + summary-coalesce path as G6. Titles lean on learning-intention lines when daily-task headings are generic. Report: `ingest_reports/2026-03-29T15-32-31Z_74fa96f5.json`. |
| 6–8 | Math | `Uncategorized_Grade` → `Math` → `Unit 8_Pythagorean_Theorem_and_Irrational_Numbers` | `1BBR66X-WrHrPdHs8OFUhFtEaCQ-uvQeVIDQaJwes1GU` | `Math_8_U8_sample` | **PASS** | **20** lessons. Local JSON + tab DOCX. Latest ingest report: `ingest_reports/2026-03-29T15-31-50Z_6fa3b915.json`. |

## Parser / tooling exception log (this session)

| Step | Outcome | Exception / error class |
|------|---------|-------------------------|
| `python tools/scraper/export_doc_ids_to_docx.py …` (Drive export) | FAIL (no DOCX) | `google.auth.exceptions.RefreshError` — `invalid_grant: Token has been expired or revoked.` |
| `python tools/db/ingest_wave_unit.py --docx …` from local `reference_docs/scraped/…/originals/*.json` (via `tools/db/phase5_vertical_sample_ingest.py` / `gdoc_tab_to_docx.py`) | **PASS** for matrix rows with snapshots (incl. G6/G8 merged tabs) | Bypasses OAuth. ELA MS/HS merged tabs use **summary-table lesson coalescing** in `RecursiveTableParser` when paragraph lesson anchors are missing or coverage is below **35%** of summary rows (with at least **5** summary rows). |
| Math G4/G5 matrix doc IDs | **DEFERRED** (Phase 5) | No DB ingest for this phase; see `PHASE_5_WRAP_UP.md` closure note. Future ingest: add matching `originals` JSON or DOCX + `ingest_wave_unit --docx`.

## Phase 5 closure (2026-03-29)

- **Executed** matrix rows: ingested, verified, and archived as in this table (**PASS** / evidence paths above).
- **Deferred** rows: Math G4/G5 only—registry and `unit_id` seeds preserved; no lesson data requirement for Phase 5 sign-off.

## Pass threshold (original plan vs closure)

- Original recommendation: 100% ingest on matrix rows before treating Phase 5 as fully “green.”
- **Actual closure:** Critical gates pass on **all ingested** Phase 5 sample units; deferred Math G4/G5 excluded by operator decision (documented in `PHASED_ROLLOUT_PLAN.md` Phase 5 addendum).

## Commands per row (after DOCX available)

```text
python tools/db/ingest_wave_unit.py --unit-id <UNIT_ID> --grade <N> --subject Math|ELA --unit-number <N> --title "..." --doc-id <DOC_ID> --docx <path\to\unit.docx>
python tools/scraper/verify_curriculum_db.py --ingest-report ingest_reports/<run_id>.json
```

For oversized compendiums, build a tab DOCX from local JSON with `tools/scraper/gdoc_tab_to_docx.py`, or run the orchestrator `python tools/db/phase5_vertical_sample_ingest.py` (see script docstring). Drive export remains `export_doc_ids_to_docx.py` when OAuth is valid.
