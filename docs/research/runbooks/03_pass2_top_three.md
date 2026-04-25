# Runbook 03 — Pass 2: triage and top three deep dives

This runbook is **Step 3**: pick **three** repositories for a deeper **happy-path trace** after Pass 1 is complete for all ten.

**Prerequisites:** [02_pass1_all_repositories.md](02_pass1_all_repositories.md) complete (no `TBD` verdicts).

**Next:** [04_bounded_spike.md](04_bounded_spike.md)

---

## Triage rubric

Score each of the ten repos **1–3** for **current** LP pain (not hypothetical):

| Score | Meaning |
|-------|---------|
| 1 | Low — interesting but no near-term lever on [tools/scraper](../../../tools/scraper) |
| 2 | Medium — could influence design or a future spike |
| 3 | High — directly addresses a live A1–A5 symptom you are hitting **this month** |

**Symptom reference** (from index):

- **A1** — Anchor / heading drift in `SubjectConfig` and `_resolve_field_from_anchors`
- **A2** — ELA table layout variance (`ela_lesson_plan_table`, `ela_summary_table`)
- **A3** — Validation gaps, `verify_curriculum_db`, when to add LLM second pass
- **A4** — Hyperlinks, `data-resource-id`, cell JSON vs HTML-only SSOT
- **A5** — API keys, offline requirement, batch cost

Weight **Dependency-candidate** and **Pattern-only** verdicts from Pass 1 when scores tie.

---

## Selection rule

- Choose exactly **three** repos for Pass 2 unless the team documents an exception (e.g. “fourth repo: legal review only”) in the index footnote or in [repos/](../repos/).
- Prefer **at least one** extraction/control-plane repo (e.g. Instructor, LangExtract) and **at least one** layout/normalization repo (e.g. Docling, Unstructured) when both classes scored high—unless your current fire is only A3, then skew to orchestration/extraction.

---

## Pass 2 trace template

For **each** of the three repos, record:

1. **Happy-path input** — e.g. “sample PDF path”, “URL string”, “DOCX bytes”, API payload type  
2. **Trigger** — CLI command or Python entry function (module path + symbol name)  
3. **Output** — file path, JSON shape, or object type (one sentence)  
4. **Module chain** — ordered bullet list of packages/modules touched (from reading source or debugger), **or** a small mermaid `flowchart` in a [repos/](../repos/) file  

**Example (illustrative only):**

```text
Input: teacher_guide.docx on disk
Trigger: python -m docling … (exact from upstream doc)
Output: Markdown string + optional JSON IR path
Modules: cli → pipeline → backend loader → converter → serializer
```

---

## Where to write results

- **Short traces (under ~6 lines):** append to the master table row in [agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md) as bullets under an implicit “Pass 2” note, or in adjacent **Deep notes** if your table format allows.
- **Long traces:** add a file under [repos/](../repos/) (e.g. `docling.md`), link it from **Deep notes**, keep the index row scannable.

---

## Index updates (Pass column)

- Set **Pass** to **`2`** for each of the three repos when Pass 2 is complete.
- Repos **not** deep-dived stay at **`1`** or **`1+`** unless you deliberately run a second-light pass (then `1+` with note).

---

## Definition of done (Step 3)

- Exactly **three** repos have Pass 2 trace notes (index or linked file).
- [agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md) **Definition of done**: second bullet satisfied (**three** repos with Pass 2 **or** spike—spike can substitute later in Runbook 04).
- You have a ranked idea of which **single** repo or pattern supports the upcoming **bounded spike** (Runbook 04).
