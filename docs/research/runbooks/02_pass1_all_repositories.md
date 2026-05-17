# Runbook 02 — Pass 1 for all repositories

This runbook is **Step 2**: a **repeatable Pass 1** for each reference clone, then updating the master index.

**Prerequisites:** [01_workspace_and_clones.md](01_workspace_and_clones.md) complete for the repos you are studying.

**Next:** [03_pass2_top_three.md](03_pass2_top_three.md)

---

## Timeboxing

- **Budget 60–90 minutes per repository** for Pass 1 (license + README + one example + entry module + index questions).
- **Calendar options:** two Pass 1 sessions per day (2–3 hours total), or one repo per weekday (two weeks for ten repos). Adjust to team capacity; the important part is **finishing all ten rows** before relying on Pass 2 conclusions.

---

## Fixed study order

Process repositories in this order (matches [agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md)):

1. docling  
2. unstructured  
3. marker  
4. markitdown  
5. langextract  
6. instructor  
7. firecrawl  
8. crawl4ai  
9. scrapegraph-ai  
10. llama_index  

---

## Pass 1 checklist (repeat for each repo)

Work inside `research/agentic_doc_extraction/clones/<name>/`.

1. **License** — Open `LICENSE`, `LICENSE.md`, or PyPI/notice files. Note SPDX-style id if obvious (e.g. MIT, Apache-2.0, AGPL-3.0, GPL-3.0). Confirm **Quick** column in index still matches; fix if upstream changed.
2. **README** — Read the **Getting started** / **Install** / **Quickstart** section. Note CLI vs library usage.
3. **One example** — Run or read one minimal example: official tutorial, `examples/` script, or doc snippet. You do **not** need a green install if reading the code path is enough; if running code, use a **dedicated venv under spikes/** (see Runbook 04) rather than polluting each clone.
4. **Primary entry** — Identify the main package layout (e.g. `src/<pkg>/`, top-level Python package, `apps/` for TS). Record 1–2 sentence **entry point** note for yourself (e.g. “CLI `docling …`; Python `docling.document_converter`”).
5. **Research questions** — For the matching section in [agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md) (“Per-repository research questions”), draft **short bullet answers** in your notes (or directly in the index if space allows).

---

## Verdict guidance (Pass 1)

Choose one value for the **Verdict** column:

| Verdict | Meaning |
|--------|---------|
| **Adopt** | We plan to integrate this as a dependency or documented standard practice soon. |
| **Pattern-only** | Copy ideas (interfaces, loop shape), not the codebase. |
| **Dependency-candidate** | Likely PyPI/submodule candidate; needs spike or license review. |
| **Out-of-scope** | Does not fit current curriculum ingest; still learned from README. |
| **TBD** | Only before Pass 1 starts for that row; must be replaced after Pass 1. |

“Out-of-scope” is valid when Pass 1 shows the project targets web crawl only or contradicts local-first constraints.

---

## Index update SOP

Edit [docs/research/agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md) **master table** for each completed Pass 1:

| Column | What to set |
|--------|-------------|
| **LP tags** | Confirm A1–A5 still apply; add or remove if Pass 1 changed your view |
| **Verdict** | One of Adopt / Pattern-only / Dependency-candidate / Out-of-scope |
| **Pinned SHA** | `git -C clones/<name> rev-parse HEAD` |
| **Pass** | `1` when Pass 1 complete; use `1+` if you appended extra bullets in-row |
| **SPIKE / PR** | Leave empty until Runbook 04 |
| **Deep notes** | `—` or link to [repos/](../repos/) file if answers remain long |

Optionally add **date** inline in deep notes: `Pass1 2025-03-30.`

---

## Definition of done (Step 2)

- All **ten** master table rows have **Verdict** not `TBD`.
- All **Pinned SHA** fields filled (the commit you studied).
- **Pass** column reflects Pass 1 completion for all ten.
- [agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md) **Definition of done (each research wave)** section: first bullet satisfied for this wave.

Then proceed to Runbook 03 to select **three** repos for Pass 2.
