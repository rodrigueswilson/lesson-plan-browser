# Runbook 05 — Research to product backlog

This runbook is **Step 5**: turn Pass 1–2 findings and spike outcomes into **actionable** work for the LP codebase without duplicating extraction SSOT.

**Prerequisites:** [04_bounded_spike.md](04_bounded_spike.md) completed or explicitly skipped with reason.

**Next:** [06_license_hygiene_and_regression.md](06_license_hygiene_and_regression.md)

---

## Inputs

- [agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md) — verdicts, SPIKE / PR, LP tags  
- [CURRICULUM_EXTRACTION_ARCHITECTURE.md](../../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md) — pipeline SSOT  
- Optional spike artifacts under `research/agentic_doc_extraction/spikes/` (gitignored)

---

## Translation rules

For each **Dependency-candidate**, **Pattern-only** success, or **Adopt** row:

1. **GitHub issue** — Prefer a single issue with **acceptance criteria** and LP tag (A1–A5). Link the reference repo and your pinned SHA in the issue body for traceability.
2. **ADR (short)** — Use [docs/decisions/](../../decisions/) only when the choice is **architectural** (e.g. “second-pass LLM owns schema X”, “new dependency allowed in scraper venv”). Keep ADRs thin; link to index row.
3. **Deferred** — If valuable but not this quarter, add a bullet in the index **Deep notes**: `Deferred YYYY-MM: reason`.

Do **not** open issues for vague “investigate Docling” without a spike outcome or Pass 2 trace.

---

## SSOT alignment checklist

Before promoting work into [tools/scraper](../../../tools/scraper):

- **Single extraction narrative:** Curriculum structure, anchors, and DB writes remain documented in [CURRICULUM_EXTRACTION_ARCHITECTURE.md](../../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md). Extend that doc when the **pipeline** changes, do not fork a second architecture story in research-only files.
- **Provenance (A4):** Any new path must preserve or explicitly replace **hyperlink / `data-resource-id`** behavior with an ADR-level decision.
- **Deterministic baseline:** Keep deterministic extraction as the default authoritative output; AI/agentic logic is optional and explicitly scoped.
- **YAGNI:** Park “nice for future subjects” in Deferred unless a current unit is blocked.

---

## Required output for AI-assisted proposals

If a backlog item introduces AI/agentic extraction into `tools/scraper`, the issue or ADR must include:

1. **Field ownership matrix** — exact fields AI may populate/augment, and fields AI must not overwrite.
2. **Invocation triggers** — exact conditions (e.g., empty section, low-confidence parser classification, anchor mismatch class).
3. **Failure policy** — behavior for no key, timeout/rate limit, schema validation fail, and partial output.
4. **Verification gate** — required commands/fixtures and pass conditions before merge.

Reject backlog items that do not include these four sections.

---

## Minimum output (wave definition of done)

Per [agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md):

- **At least one** concrete next step for `tools/scraper` **documented** as: GitHub issue URL, PR link, or ADR filename **or** an explicit index note: **“No code change until &lt;trigger&gt;”** (e.g. until next failing unit ingest).

Record that link or quote in the index footer or in a **Wave log** bullet at the bottom of the index (optional single dated subsection).

---

## Backlog hygiene

| Avoid | Prefer |
|-------|--------|
| Duplicate issues for the same verdict | One issue referencing the index row + SHA |
| Copy-paste from reference repos into app without license sign-off | Dependency + thin adapter in `tools/scraper` |
| RAG/agent frameworks before deterministic ingest works | Deterministic first; LLM as optional second pass if ADR says so |

---

## Definition of done (Step 5)

- At least **one** tracked follow-up (issue / PR / ADR) **or** explicit “no change until …” in the index.
- Third bullet of the index **Definition of done** is satisfied for this wave.
- Runbook 06 run once for copyleft and revisit policy (can be same session).
