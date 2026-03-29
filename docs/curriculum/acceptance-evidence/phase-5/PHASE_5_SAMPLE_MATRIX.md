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
| 4–5 | ELA | `Uncategorized_Grade` → `ELA` → `04_-_Fourth_Grade_Unit_Description_and_Summary_of_Key_Learning` | `1jeeDNSMhT4k_-kMzR65EszWgKkCznHOn0KMVtdp4ofs` | `ELA_4_compendium_sample` (TBD) | **PENDING** | Export/ingest not run (OAuth). |
| 4–5 | ELA | `Uncategorized_Grade` → `ELA` → `05_-_Fifth_Grade_Unit_Description_and_Summary_of_Key_Learning` | `1vRv3y0geSVJBGOHfgtplWNygz4nfwSE4RwAM1GbZQWY` | `ELA_5_compendium_sample` (TBD) | **PENDING** | Export/ingest not run (OAuth). |
| 4–5 | Math | `Uncategorized_Grade` → `Math` → `Unit 4_Understanding_Addition_and_Subtraction` | `1aMiqygM9kCrQ0DKFGPma3lKT91lJQkAUF-H8TvQMbus` | `Math_4_5_sample_U4` (TBD) | **PENDING** | Representative ES layout; ingest pending. |
| 4–5 | Math | `Uncategorized_Grade` → `Math` → `Unit 5_Numbers_to_1000` | `1S9fRcM1-6futZzmOgOEg3eQ1hfRh8YpXHfjmyiPTu08` | `Math_4_5_sample_U5` (TBD) | **PENDING** | Alternate ES pattern; ingest pending. |
| 6–8 | ELA | `Uncategorized_Grade` → `ELA` → `Unit 2` (multi-grade) | `1iVNkWwfzOsu9p7zJsCHqrlWFFQ-p33GsmjqUXP1nFfY` | `ELA_6_U2_sample` (TBD) | **PENDING** | G6 Percy Jackson unit guide. |
| 6–8 | ELA | `Uncategorized_Grade` → `ELA` → `Unit 1` (multi-grade) | `1ordR_c50CNntMjqavOQR9JHgfzklI2CUprYDjgfOdOU` | `ELA_8_U1_sample` (TBD) | **PENDING** | G8 Make Lemonade. |
| 6–8 | Math | `Uncategorized_Grade` → `Math` → `Unit 8_Pythagorean_Theorem_and_Irrational_Numbers` | `1BBR66X-WrHrPdHs8OFUhFtEaCQ-uvQeVIDQaJwes1GU` | `Math_8_U8_sample` (TBD) | **PENDING** | MS geometry / irrational numbers. |

## Parser / tooling exception log (this session)

| Step | Outcome | Exception / error class |
|------|---------|-------------------------|
| `python tools/scraper/export_doc_ids_to_docx.py … 1jeeDNSMhT4k_-kMzR65EszWgKkCznHOn0KMVtdp4ofs` | FAIL (no DOCX) | `google.auth.exceptions.RefreshError` — `invalid_grant: Token has been expired or revoked.` |

Operator recovery: refresh OAuth per `tools/scraper/SETUP.md`, or place an exported DOCX under `reference_docs/scraped/…` and call `RecursiveTableParser.ingest_to_curriculum` / `ingest_wave_unit.py` as appropriate.

## Pass threshold (plan)

- 100% pass on **critical** gates for all matrix rows before Phase 5 merge.
- Fidelity spot checks: ≥95% policy applies to executed rows only; **PENDING rows count as failing Phase 5 exit until ingested and verified.**

## Commands per row (after DOCX available)

```text
python tools/db/ingest_wave_unit.py --unit-id <UNIT_ID> --grade <N> --subject Math|ELA --unit-number <N> --title "..." --doc-id <DOC_ID>
python tools/scraper/verify_curriculum_db.py --ingest-report ingest_reports/<run_id>.json
```

For oversized compendiums, use tab export pattern from `tools/scraper/export_doc_ids_to_docx.py` and `gdoc_tab_to_docx.py` (see Phase 4 notes).
