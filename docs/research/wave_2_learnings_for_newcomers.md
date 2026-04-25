# Wave 2 research — what we learned (for newcomers)

This page explains **in plain language** what the Wave 2 smokes and compares showed. For **commands, dates, and raw numbers**, use the evidence log: [repos/wave_2_evidence.md](repos/wave_2_evidence.md).

## Two ideas to keep separate

1. **Deterministic parsing** — Code in `tools/scraper` reads exported curriculum documents in a **repeatable** way. That path is the **authoritative source** for structure and what gets written to the curriculum database (see [CURRICULUM_EXTRACTION_ARCHITECTURE.md](../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md)).
2. **AI and layout tools** — Docling, Instructor, live OpenAI tests, and LangExtract were **experiments** to see what each could do. They are **optional second-pass** ideas, not silent replacements for the main parser unless product explicitly decides otherwise (issue/ADR).

The **Extraction contract (research stance)** section in [agentic_doc_extraction_index.md](agentic_doc_extraction_index.md) states this policy in checklist form.

## What each kind of test showed

### Docling (document to Markdown)

Docling can turn curriculum **PDFs and DOCX** into **Markdown** with **tables and links**. On a **full unit DOCX**, the export can be **very large** and sometimes **one long linear/table-heavy view**, which is awkward to use the same way the app uses **section and lesson routing**.

**Takeaway:** Useful as a **secondary layout artifact**; not a drop-in replacement for `RecursiveTableParser` / ingest routing.

### LP parser vs Docling (same real unit DOCX)

The same **real unit** file was run through Docling and through LP tooling (hyperlink dump + `scan_curriculum_docx.py`). LP reported **many structured stream items**, **lesson title hits**, **standards hits**, and **hundreds of hyperlinks**, including **Google-id** metadata where the parser supports it.

**Takeaway:** LP remains **stronger for ingest-oriented structure and provenance** (headings, sections, link semantics). Docling is **stronger for a readable Markdown export** of layout.

### Hyperlink fixture DOCX

A **small test DOCX** checked that **hyperlinks** appear in both Docling Markdown and LP dumps. LP adds **`data-resource-id`**-style behavior when URLs match **Google Doc** patterns; generic `example.com` links do not get that field.

**Takeaway:** Agreement on “there is a link”; LP carries **extra product-specific** semantics for curriculum URLs. Details: [repos/DOCX_HYPERLINK_ARTIFACTS_COMPARE.md](repos/DOCX_HYPERLINK_ARTIFACTS_COMPARE.md).

### Instructor smoke (tiny structured extract)

A **short curriculum-like paragraph** was sent through Instructor + a small Pydantic model. The script returned **JSON** with a **lesson number** and **procedure text** aligned with the fixture.

**Takeaway:** For a **small, clear excerpt**, structured LLM output is **feasible** as a pattern for a **future optional** fill-in pass—not a new SSOT parser by itself.

### Live pytest: structured outputs integration

With an **explicit environment gate** and valid OpenAI credentials, `tests/test_structured_outputs.py::test_integration_with_real_api` ran a **full** `transform_lesson` call and **passed** (slow, uses API quota).

**Takeaway:** The **production-shaped** OpenAI structured-output path is **verified** when enabled; it is separate from the small research spikes. How to run it: [verification_and_llm_ops.md](../dev/verification_and_llm_ops.md).

### LangExtract smoke (grounded spans)

With **`LANGEXTRACT_API_KEY`** in repo-root `.env`, the LangExtract smoke returned **extractions** each tied to a **character interval** in the **input text** (see [langextract_smoke_output.txt](repos/langextract_smoke_output.txt)). A follow-up run used **plain text exported from `curriculum.db`** for **Grade 2 Unit 1, lesson 1** (same fields the app stores after ingest); all extractions remained grounded (Run J in [wave_2_evidence.md](repos/wave_2_evidence.md)). The spike verifier follows upstream **`alignment_status`**: only `match_exact` rows must match the slice byte-for-byte; partial / fuzzy alignments are accepted as the library intended.

**Takeaway:** Good **research signal** for **auditability** (“this field came from this substring”). Still **research-only** relative to deterministic ingest.

## One-sentence summary

**Keep deterministic `tools/scraper` in charge of curriculum structure and DB writes; use Wave 2 evidence to choose narrow, explicit second-pass options later—Docling for layout export, Instructor/structured outputs for structured generation, LangExtract for span-grounded auditing—only when a concrete gap justifies the cost and scope.**

## Where to go next

- Evidence and metrics: [repos/wave_2_evidence.md](repos/wave_2_evidence.md)
- Deep-study checklist: [repos/wave_2_deep_study.md](repos/wave_2_deep_study.md)
- Runnable spikes: [spikes/README.md](spikes/README.md)
