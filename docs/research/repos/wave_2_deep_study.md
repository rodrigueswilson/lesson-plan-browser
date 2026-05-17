# Wave 2 — Deep Pass 1 / Pass 2 (human or focused agent)

**Wave 1** seeded clones, SHAs, verdicts, and thin notes. **Wave 2** is the same **Runbooks [02](../runbooks/02_pass1_all_repositories.md) and [03](../runbooks/03_pass2_top_three.md)** with **real timeboxes** (60–90 min × 10 for Pass 1 refresh, or priority subset first).

**Newcomer summary:** [wave_2_learnings_for_newcomers.md](../wave_2_learnings_for_newcomers.md) (what Wave 2 smokes mean in plain language). **Progress:** Evidence-backed smokes — [wave_2_evidence.md](wave_2_evidence.md) (Docling: curriculum PDF + committed hyperlink test DOCX + **real unit-export DOCX compare**; notes: [DOCX_HYPERLINK_ARTIFACTS_COMPARE.md](DOCX_HYPERLINK_ARTIFACTS_COMPARE.md), [DOCX_REAL_UNIT_DOCLING_VS_LP_COMPARE.md](DOCX_REAL_UNIT_DOCLING_VS_LP_COMPARE.md)). **Instructor** live smoke and **optional structured-output pytest** recorded in [wave_2_evidence.md](wave_2_evidence.md) (2026-04-06). **LangExtract** live smokes through **Run J** (short fixture, synthetic lesson-scale, **real Grade 2 Unit 1 lesson 1 from `curriculum.db`**). **Spike index / venv:** [../spikes/README.md](../spikes/README.md).

## Prioritized repo order (suggested)

Align with backlog and **Dependency-candidate** rows:

1. **Instructor** — Run [smoke script](../spikes/instructor_curriculum_smoke/README.md); read retry/validation hooks in upstream `instructor` clone under `research/agentic_doc_extraction/clones/instructor` (compare with [backend/llm/transform_runner.py](../../../backend/llm/transform_runner.py)). Paste JSON summary into [wave_2_evidence.md](wave_2_evidence.md) when run.
2. **Docling (next after hyperlink fixture)** — Run on a **real unit-export DOCX** (nested tables, real lesson rows); compare tables and reading order to `RecursiveTableParser` / ingest output. The hyperlink fixture compare is documented only in [DOCX_HYPERLINK_ARTIFACTS_COMPARE.md](DOCX_HYPERLINK_ARTIFACTS_COMPARE.md).
3. **LangExtract** — Run README quick start on one lesson-length text; inspect grounding output structure vs audit needs; record in [wave_2_evidence.md](wave_2_evidence.md).

Then refresh remaining repos if **Verdict** is uncertain.

## Deliverables

- **Wave 2 pass notes:** [wave_2_pass1_notes.md](wave_2_pass1_notes.md) (linked from [agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md)); alternatively extend [wave_1_pass1_notes.md](wave_1_pass1_notes.md) with dated Wave 2 bullets only if consolidating into one file is preferred.
- Update **Pinned SHA** after `git pull` in each clone (or re-shallow-clone).
- If **Verdict** changes, add one line: `YYYY-MM-DD: reason` under repo section.
- For any proposed AI-assisted scraper integration, include field ownership, invocation triggers, failure policy, and verification gate per [runbook 05](../runbooks/05_research_to_product_backlog.md).

## Definition of done

- At least the **three** priority repos have **evidence-backed** answers (command output, file paths, or screenshots) attached to notes—not README-only summaries.
