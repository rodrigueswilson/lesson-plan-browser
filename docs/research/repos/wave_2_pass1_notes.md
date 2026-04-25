# Wave 2 — Pass 1 / evidence consolidation (2026-04-06)

Dated summary of **what ran** in Wave 2 and how it reinforces Pass 1 verdicts. Raw commands and numbers: [wave_2_evidence.md](wave_2_evidence.md). Plain-language summary: [wave_2_learnings_for_newcomers.md](../wave_2_learnings_for_newcomers.md).

## Docling

- **Ran:** Curriculum PDF smoke; committed hyperlink DOCX; **real unit-export DOCX** (Unit 2 Area and Multiplication) vs LP scan and hyperlink dump ([wave_2_evidence.md](wave_2_evidence.md) Runs A–E). Compare write-up: [DOCX_REAL_UNIT_DOCLING_VS_LP_COMPARE.md](DOCX_REAL_UNIT_DOCLING_VS_LP_COMPARE.md).
- **Verdict reinforcement:** **Dependency-candidate** for **layout / Markdown export** beside ingest, not SSOT. Strong on tables and bulk conversion; weak substitute for `RecursiveTableParser` lesson/section routing and Google-id hyperlink semantics.

## LangExtract

- **Ran:** Short-fixture smoke with grounded `char_interval` (Run H). **Lesson-scale** synthetic text (Run I). **Real ingest-shaped lesson** — Grade 2 Unit 1 lesson 1 from `curriculum.db` (`narrative_html` + `procedure_html` stripped to plain text, Run J — [wave_2_evidence.md](wave_2_evidence.md)); helper [export_lesson_text_from_db.py](../spikes/langextract_curriculum_smoke/export_lesson_text_from_db.py).
- **Verdict reinforcement:** **Dependency-candidate** for **A4-style audit** (span-grounded extractions). Long-document behavior remains “verify per use case”; upstream documents chunking for long inputs (see [wave_1_pass1_notes.md](wave_1_pass1_notes.md#langextract)).

## Instructor

- **Ran:** Live smoke with `LessonExtractStub` ([wave_2_evidence.md](wave_2_evidence.md) Run F). Backend structured-output integration exercised via pytest ([wave_2_evidence.md](wave_2_evidence.md) Run G).
- **Deep compare:** Retry/validation layering vs LP: [instructor_vs_transform_runner.md](instructor_vs_transform_runner.md).
- **Verdict reinforcement:** **Dependency-candidate** for **schema-first OpenAI calls**; LP already uses the `instructor` library on the lesson-transform path, with **additional** domain validation and retries in [backend/llm/transform_runner.py](../../../backend/llm/transform_runner.py).

## Remaining master-table rows (Pass 1 complete; optional Pass 2)

No new bounded spikes were run in this wave for **Unstructured**, **MarkItDown**, or **Marker**. When ingest gaps appear, use [runbooks/02_pass1_all_repositories.md](../runbooks/02_pass1_all_repositories.md) and [runbooks/03_pass2_top_three.md](../runbooks/03_pass2_top_three.md). **Marker** remains GPL-3.0: sidecar or compliance review before any packaging link ([agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md) license table).

## Links

- Deep study checklist: [wave_2_deep_study.md](wave_2_deep_study.md)
- Spikes index: [../spikes/README.md](../spikes/README.md)
