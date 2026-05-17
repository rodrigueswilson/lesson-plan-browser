# Wave 2 — evidence log (automated session 2026-03-29)

Commits in this session add **runnable smokes**; this file records what actually ran on the maintainer machine.

## Docling

### Run A — curriculum PDF

- **Status:** Success.
- **Input:** `Copy_of_02___Second_Grade_Unit_Description_and_Summary_of_Key_Learning/Grade_2_Unit_1/resources/originals/PDF_1qgoZUKbW28_8SWOMlHzUIIGHKxtGD1s6.pdf`
- **Command:** `python docs/research/spikes/docling_curriculum_smoke/smoke_convert.py`
- **Notes:** First run pulled RapidOCR / layout weights (~minutes, GPU if available). Markdown preview included `## Fix the Sentence Worksheet` and list items.

### Run B — committed DOCX (hyperlinks + tables)

- **Status:** Success (2026-03-29).
- **Input:** `docs/archive/test-files/test_hyperlink_robustness.docx`
- **Command:** `DOCLING_SMOKE_SOURCE` set to that path (script now **falls back** to this DOCX when the curriculum PDF tree is absent).
- **Notes:** Weekly planning tables rendered as GitHub-flavored markdown tables; **Referenced Links** as `[Lenni Lenape](http://example.com/N)` (generic URLs, not `data-resource-id`). Pillow logged a non-fatal image warning.
- **Artifact:** [smoke_convert.py](../spikes/docling_curriculum_smoke/smoke_convert.py)

### Run D — real unit-export DOCX (Wave 2 required compare)

- **Status:** Success (2026-03-30).
- **Input fixture:** `reference_docs/scraped/batch_8_linked_mar2026/Unit_2__Area_and_Multiplication/originals/Unit_2__Area_and_Multiplication.docx`
- **Command:** `DOCLING_SMOKE_SOURCE="D:\LP\reference_docs\scraped\batch_8_linked_mar2026\Unit_2__Area_and_Multiplication\originals\Unit_2__Area_and_Multiplication.docx" python docs/research/spikes/docling_curriculum_smoke/smoke_convert.py`
- **Output artifacts:**
  - `docs/research/repos/docling_real_unit2_smoke_output.txt` (script output with 8k clip)
  - `docs/research/repos/docling_real_unit2_full.md` (full Docling markdown export for this unit)
- **Output summary:** Docling exported a very large markdown payload (`2,814,217` chars) with substantial table/link material (`|` count `1246`, markdown HTTP links `408`, `LESSON n` token count `105`), but the markdown is emitted as one giant line/table-centric view in this run.
- **One-sentence interpretation:** Useful as a layout-preserving secondary artifact, but not a direct replacement for deterministic section routing in LP.

### Run E — LP parser evidence on same real unit DOCX

- **Status:** Success (2026-03-30).
- **Input fixture:** `reference_docs/scraped/batch_8_linked_mar2026/Unit_2__Area_and_Multiplication/originals/Unit_2__Area_and_Multiplication.docx`
- **Commands:**
  - `python docs/research/spikes/lp_parser_hyperlink_dump/dump_lp_hyperlinks.py "D:\LP\reference_docs\scraped\batch_8_linked_mar2026\Unit_2__Area_and_Multiplication\originals\Unit_2__Area_and_Multiplication.docx" --json-out docs/research/repos/lp_hyperlink_dump_unit2_area_multiplication.json`
  - `python tools/scraper/scan_curriculum_docx.py "D:\LP\reference_docs\scraped\batch_8_linked_mar2026\Unit_2__Area_and_Multiplication\originals\Unit_2__Area_and_Multiplication.docx" --subject Math --json-out docs/research/repos/scan_unit2_area_multiplication_math.json`
- **Output artifacts:**
  - `docs/research/repos/lp_hyperlink_dump_unit2_area_multiplication.json`
  - `docs/research/repos/scan_unit2_area_multiplication_math.json`
- **Output summary:** LP scan reports `stream_items=1907`, `lesson_title_hits=37`, `standards_token_hits=184`; hyperlink dump reports `hyperlink_run_count=475`, `paragraphs_with_hyperlinks=377`, with `45` runs carrying parsed `google_id`.
- **One-sentence interpretation:** Deterministic LP parser remains stronger for section/heading routing and provenance-aware link semantics, while Docling is best treated as optional second-pass evidence (A4) rather than SSOT extraction.

### Run C — same DOCX, LP `RecursiveTableParser` hyperlinks

- **Status:** Success (2026-03-29).
- **Input:** `docs/archive/test-files/test_hyperlink_robustness.docx`
- **Command:** `python docs/research/spikes/lp_parser_hyperlink_dump/dump_lp_hyperlinks.py`
- **Artifact:** [lp_hyperlink_dump_test_hyperlink.json](lp_hyperlink_dump_test_hyperlink.json) (stream indices, anchor text, URL, optional `google_id`, `paragraph_html` via `json_to_html`).
- **Compare:** Docling [docling_test_hyperlink.md](../../../docling_test_hyperlink.md) lists the same four `http://example.com/0`–`/3` anchors; LP emits `<a href>` without `data-resource-id` on these generic URLs (field appears when the href matches a Google Doc id pattern).
- **Stable write-up:** [DOCX_HYPERLINK_ARTIFACTS_COMPARE.md](DOCX_HYPERLINK_ARTIFACTS_COMPARE.md) (three-artifact comparison and when to use each).

## Instructor

### Run F — live smoke (Wave 2 follow-up)

- **Status:** Success (2026-04-06).
- **Artifact:** [smoke_lesson_extract.py](../spikes/instructor_curriculum_smoke/smoke_lesson_extract.py)
- **Command:** `python docs/research/spikes/instructor_curriculum_smoke/smoke_lesson_extract.py` (from repo root; script loads `.env` via `load_dotenv`)
- **Model used:** Default `INSTRUCTOR_SMOKE_MODEL` (`gpt-4o-mini`) unless overridden in environment.
- **Output summary:** Printed JSON with `lesson_number: 3` and non-empty `procedure_html` matching the warm-up / activity / cool-down lines from the built-in fixture.
- **One-sentence interpretation:** Instructor plus the `LessonExtractStub` Pydantic model successfully structured the curriculum-like excerpt for this smoke.

## Backend — optional live pytest (structured outputs)

### Run G — `test_integration_with_real_api`

- **Status:** Success (2026-04-06).
- **Test:** `tests/test_structured_outputs.py::test_integration_with_real_api`
- **Command:** `RUN_STRUCTURED_OUTPUTS_API=1 python -m pytest tests/test_structured_outputs.py::test_integration_with_real_api -v`
- **Duration:** Approximately 3 minutes on a maintainer machine.
- **Keys:** Optional gate; prefer `OPENAI_API_KEY_TESTS` / `GPT5_API_KEY_TESTS` for isolation from lesson-plan keys; falls back to `OPENAI_API_KEY` / `GPT5_API_KEY` / `LLM_API_KEY` (see [verification_and_llm_ops.md](../../dev/verification_and_llm_ops.md)).
- **One-sentence interpretation:** Live OpenAI structured-output path completed a full `transform_lesson` call and passed the integration test when the gate and credentials were set.

## LangExtract

### Run H — smoke script (with `.env` load)

- **Status:** Success (live Gemini call after `LANGEXTRACT_API_KEY` set in repo-root `.env`).
- **Artifact:** [smoke_extract.py](../spikes/langextract_curriculum_smoke/smoke_extract.py) (loads repo-root `.env` via `load_dotenv`)
- **Command:** `python docs/research/spikes/langextract_curriculum_smoke/smoke_extract.py`
- **Output artifact:** [langextract_smoke_output.txt](langextract_smoke_output.txt) (summary lines only; upstream `langextract` may print colored progress to stderr)
- **Model used:** `gemini-2.5-flash` (default; override with `LANGEXTRACT_SMOKE_MODEL`)
- **Output summary:** `extractions_total=2`, `grounded=2`; `lesson_number` span `CharInterval(start_pos=0, end_pos=8)` on `Lesson 4`; `procedure` span `CharInterval(start_pos=34, end_pos=90)` on the warm-up / pairs sentence.
- **Duration:** Approximately 7–8 seconds on a maintainer machine (excluding dependency install).
- **One-sentence interpretation:** LangExtract returned **source-grounded** spans (`char_interval` on every extraction) for the short curriculum-like fixture, matching A4-style audit needs for a research spike (deterministic ingest SSOT unchanged). Post-run checks honor **`alignment_status`** (see Run J / [char_interval_verify.py](../spikes/langextract_curriculum_smoke/char_interval_verify.py)).
- **Prior skip note:** Earlier 2026-04-06 runs without a key only printed the skip message; setup checklist remains in [langextract_curriculum_smoke README](../spikes/langextract_curriculum_smoke/README.md).

### Run I — lesson-scale text file (`LANGEXTRACT_SMOKE_INPUT_FILE`)

- **Status:** Success (2026-04-06).
- **Input:** [lesson_length_sample.txt](../spikes/langextract_curriculum_smoke/fixtures/lesson_length_sample.txt) (`1671` UTF-8 chars).
- **Command:** `LANGEXTRACT_SMOKE_INPUT_FILE=docs/research/spikes/langextract_curriculum_smoke/fixtures/lesson_length_sample.txt python docs/research/spikes/langextract_curriculum_smoke/smoke_extract.py` (from repo root; PowerShell: set env var then same `python` invocation).
- **Output artifact:** [langextract_smoke_output.txt](langextract_smoke_output.txt) (Run I block).
- **Output summary:** `extractions_total=7`, `grounded=7`; one `lesson_number` span on `Lesson 7`; six `procedure` class extractions with intervals covering warm-up, main activity, extension, small-group support, focus questions, and exit ticket segments.
- **Duration:** Approximately 10–12 seconds on a maintainer machine (including upstream progress on stderr).
- **One-sentence interpretation:** At lesson-scale length, LangExtract still returned **all source-grounded** spans for this synthetic lesson block, supporting continued **Dependency-candidate** status for A4-style audits (deterministic ingest SSOT unchanged).

### Run J — real lesson from `curriculum.db` (Grade 2 Unit 1, lesson 1)

- **Status:** Success (2026-04-07).
- **Source:** `units.id` `Math_2_U1_15E1iQ_x`, `lessons.lesson_number=1`, `lessons.id` `Math_2_U1_15E1iQ_x_L1`. Plain text built from `narrative_html` + `procedure_html` (HTML stripped) via [export_lesson_text_from_db.py](../spikes/langextract_curriculum_smoke/export_lesson_text_from_db.py).
- **Fixture:** [g2_u1_lesson_01_from_db.txt](../spikes/langextract_curriculum_smoke/fixtures/g2_u1_lesson_01_from_db.txt) (`4112` UTF-8 chars).
- **Command:** `python docs/research/spikes/langextract_curriculum_smoke/export_lesson_text_from_db.py --unit-id Math_2_U1_15E1iQ_x --lesson-number 1 --out docs/research/spikes/langextract_curriculum_smoke/fixtures/g2_u1_lesson_01_from_db.txt` then `LANGEXTRACT_SMOKE_INPUT_FILE=docs/research/spikes/langextract_curriculum_smoke/fixtures/g2_u1_lesson_01_from_db.txt python docs/research/spikes/langextract_curriculum_smoke/smoke_extract.py`.
- **Output artifact:** [langextract_smoke_output.txt](langextract_smoke_output.txt) (Run J block).
- **Output summary:** `extractions_total=7`, `grounded=7`; spans include `Lesson 1`, `Activity 1`, and multiple `procedure` segments aligned with warm-up / Activity 1 / access supports. Post-run checks use **LangExtract `alignment_status`**: strict `slice == extraction_text` only for `match_exact`; `match_lesser` / `match_fuzzy` accept library-aligned non-exact spans ([char_interval_verify.py](../spikes/langextract_curriculum_smoke/char_interval_verify.py)). Success line **`char_interval_verify_ok`**. Optional **`LANGEXTRACT_SMOKE_REQUIRE_EXACT_ALIGNMENT=1`** restores an all-`match_exact` gate.
- **Ops notes:** Gemini free tier may return **429** if run back-to-back with other calls; wait ~20s and retry. On Windows, `smoke_extract.py` sets **UTF-8 stdout** so Unicode (en dash, minus U+2212) prints without `UnicodeEncodeError`.
- **One-sentence interpretation:** LangExtract remains **fully grounded** on **ingest-shaped** real lesson text, supporting A4 audit spikes; the same plain export used as model input is what the verifier slices (offsets apply to that string, not raw HTML).

## Deterministic-first contract check (Wave 2)

- No production changes were made to `tools/scraper`; this session only added/updated Wave 2 evidence artifacts and notes.
- Deterministic parser output remains SSOT for curriculum routing and DB writes; Docling/Instruct/LangExtract are recorded as optional second-pass candidates only.

## Pip / env

- `pip install docling` completed with resolver note: `cor-data-analysis` wanted older `typer` (local conda env).
- `pip install langextract` completed with `anthropic` / `anyio` pin warning—verify project venv policy before adding to main app dependencies.
- Prefer isolated venv: [../spikes/README.md](../spikes/README.md).
