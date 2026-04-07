# Wave 2 ELA Autonomous Rollout — 2026-04-07

## Scope
- Baseline lock on:
  - `ELA_2_U8_sample`
  - `ELA_3_U8_sample`
- Wave 2 expansion targets (auto-selected):
  - `ELA_2_U7_wave2` (Grade 2 Unit 7)
  - `ELA_3_U7_wave2` (Grade 3 Unit 7)

## Selection rationale
- Local artifacts were available without manual intervention:
  - Grade 2 compendium exported into tab DOCX files.
  - Grade 3 compendium available as `.docs-api.json`, with tab-to-DOCX synthesis.
- Structural diversity vs Unit 8:
  - Grade 2 Unit 7 has different tab size/profile from Unit 8 and denser link distribution.
  - Grade 3 Unit 7 uses a different lesson set/profile than Unit 8.

## Source artifacts used
- Grade 2 Unit 7 tab DOCX:
  - `reference_docs/scraped/grade2_ela_exports/1Du6ukeZavMK_1Du6ukeZ_by_tab/1Du6ukeZavMK_1Du6ukeZ__Grade 2 Unit 7__t_2plykckkv6ev.docx`
- Grade 3 Unit 7 synthesized DOCX:
  - `reference_docs/scraped/grade3_ela_exports/Grade3_ELA_Unit7_from_api_tab.docx`
  - built from:
    - `reference_docs/scraped/grade3_ela_exports/Grade_3_ELA_All_Units_including_8_1_yHvguD.docs-api.json`
    - tab id `t.887358ewlz8r`

## Commands executed
- Baseline reports:
  - `python tools/db/wave1_ela_unit8_compare.py --unit-id ELA_2_U8_sample`
  - `python tools/db/wave1_ela_unit8_compare.py --unit-id ELA_3_U8_sample`
  - `python tools/scraper/verify_curriculum_db.py`
- Wave 2 ingest:
  - `python tools/db/ingest_wave_unit.py --unit-id ELA_2_U7_wave2 ... --docx <Grade2Unit7TabDocx>`
  - `python tools/scraper/gdoc_tab_to_docx.py --json-path <Grade3DocsApiJson> --tab-id t.887358ewlz8r --out <Grade3Unit7Docx>`
  - `python tools/db/ingest_wave_unit.py --unit-id ELA_3_U7_wave2 ... --docx <Grade3Unit7Docx>`
- Wave 2 gates:
  - `python tools/db/wave1_ela_unit8_compare.py --unit-id ELA_2_U7_wave2`
  - `python tools/db/wave1_ela_unit8_compare.py --unit-id ELA_3_U7_wave2`
  - `python tools/scraper/verify_curriculum_db.py`
- UI spot-check script:
  - `python tools/db/wave2_ui_spotcheck.py --units ELA_2_U7_wave2 ELA_3_U7_wave2`

## Ingest report artifacts
- `ingest_reports/2026-04-07T18-56-42Z_260a3c92.json` (G3 U7 initial ingest)
- `ingest_reports/2026-04-07T18-59-26Z_59acc651.json` (G2 U7 re-ingest after link persistence fix)

## Gate outcomes

### Baseline units
- `ELA_2_U8_sample`: PASS
  - structured present for all lessons
  - SSOT clean (`ela_key_learning_summary` absent when structured exists)
  - Google Doc links persisted to `resources`
- `ELA_3_U8_sample`: PASS
  - structured present for all lessons
  - SSOT clean

### Wave 2 units
- `ELA_2_U7_wave2`: PASS (after fix)
  - `18/18` lessons structured
  - SSOT clean
  - `14` unique Google Doc IDs in structured HTML
  - `0` missing `resources` rows for those IDs
- `ELA_3_U7_wave2`: PASS
  - `16/16` lessons structured
  - SSOT clean
  - no Google Doc links present in structured HTML for this unit export

### Verifier
- `python tools/scraper/verify_curriculum_db.py`: PASS

## Conditional fix applied during Wave 2
- Problem discovered:
  - `ELA_2_U7_wave2` initially had Google Doc links in structured HTML but no matching `resources` rows.
- Root cause:
  - links merged from structured HTML lacked `google_id`, so `upsert_lesson_resource` stored hash IDs instead of Google IDs.
- Fix:
  - In `tools/scraper/table_extractor.py`, `_merge_links_into_resources` now derives and stores `google_id` for Google Doc URLs.
  - Added structured JSON link extraction helper and ingest-time merge:
    - `_collect_links_from_ela_structured_json`
  - Added tests in `tests/test_ela_lesson_plan_table.py`.
- Validation:
  - `pytest tests/test_ela_lesson_plan_table.py` => PASS (`12 passed`)
  - Re-ingest + wave compare confirms missing resources dropped from `14` to `0`.

## UI spot-check results (script-aided)
- Sampled first/middle/last lessons for each wave unit:
  - `ELA_2_U7_wave2`: lessons `1, 10, 18`
  - `ELA_3_U7_wave2`: lessons `1, 9, 16`
- Observations:
  - structured payload present in all sampled lessons
  - anticipatory/procedure cells show bold headings + bullets
  - no bolded list-item regressions in routines (`<li><b>` not observed)
  - vocabulary/resources cells non-empty in sampled lessons
  - all sampled Google Doc links had matching `resources` rows where present

## Residual risks
- Spot-check coverage is sampled, not exhaustive visual QA for every lesson.
- Some exports encode special characters inconsistently (legacy source text issue), but did not break ingest gates.
- `learning_procedures_html`, `engagement_with_content_html`, `daily_instructional_task_html` remain `0/x` for these tab families; this is expected for current template shape and fallback rendering paths.

## Conclusion
- Wave 2 autonomous rollout for selected Grade 2 and Grade 3 ELA units is complete and passes deterministic ingest/SSOT/link gates after one targeted ingest fix.
