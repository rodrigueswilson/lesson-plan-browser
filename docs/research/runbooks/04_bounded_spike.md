# Runbook 04 — Bounded spike (2–4 hours)

This runbook is **Step 4**: one **time-boxed** experiment that tests a hypothesis from Pass 1–2 against a **real LP concern** (A1–A5).

**Prerequisites:** [03_pass2_top_three.md](03_pass2_top_three.md) complete enough to know which pattern or dependency you are testing.

**Next:** [05_research_to_product_backlog.md](05_research_to_product_backlog.md)

---

## Pre-spike: choose one hypothesis

Pick **one** sentence tied to an LP tag, for example:

- “Wrapping extraction output with **Instructor** + a Pydantic lesson slice reduces empty `procedure_html` on unit X when anchors fail.”
- “**Docling** on exported DOCX preserves enough table structure to simplify ELA row detection for unit Y.”

Reject spikes that do not name **A1–A5** or a concrete artifact (file, unit id, validator output).

---

## Spike charter (copy and fill)

Paste into `research/agentic_doc_extraction/spikes/<topic>/CHARTER.md` or the spike folder README.

```markdown
## Charter

- **Date:**
- **Owner:**
- **Hypothesis:** (one sentence)
- **LP tags:** (e.g. A1, A3)
- **Time cap:** 2–4 hours (hard stop)

### Goal

What we will learn or prove.

### Non-goals

What we will not build (no production UI, no full unit ingest unless scoped).

### Success metric

Measurable signal (e.g. “validator passes for lesson 3”, “structured JSON validates”, “Docling runs on one DOCX without crash”).

### Failure metric

Clear negative outcome (e.g. “dependency install exceeds 30 min”, “GPL blocks use”, “output loses hyperlinks”).

### Artifacts

- Commands run (log path or inline)
- Output files (paths only; large files stay gitignored)

### Outcome (fill after spike)

One sentence + link to PR or issue if any.
```

---

## Location and isolation

- **Root:** `research/agentic_doc_extraction/spikes/<YYYYMMDD>-<short-topic>/`
- **Virtualenv:** Prefer `.venv` **inside** the spike folder (parent `spikes/` is gitignored).
- **Inputs:** Use copies of **sanitized** curriculum samples; do not commit PII or district-only filenames if avoidable.
- **Dependencies:** `pip install` only what this spike needs; pin versions in a `requirements-spike.txt` inside the spike folder if you want reproducibility (still gitignored).

---

## Execution discipline

- **Timer:** Start a visible timer for **2–4 hours**. When it fires, **stop** and record partial outcome.
- **Scope:** At most **one** primary library or pattern from the reference repos; avoid combining three new deps in one spike.
- **License check:** If the spike imports **AGPL** or **GPL** code paths, note in charter before you depend on them in production-bound plans (see Runbook 06).

---

## Abort criteria (still record outcome)

- Time exceeded  
- Install or environment failure after **30 minutes** of honest effort  
- Upstream requires API keys or hardware you do not have today  
- Discovery that the approach **breaks A4** (hyperlink / SSOT) — stop and document  

Partial failures are **valid** spike outcomes.

---

## After the spike: update the master index

Edit [docs/research/agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md):

| Column | Update |
|--------|--------|
| **SPIKE / PR** | One sentence outcome **or** link to draft PR / issue **or** path to charter under `spikes/` (for local team only—prefer PR URL when public) |
| **Verdict** | Change if spike proved **Out-of-scope** or promoted **Dependency-candidate** to **Adopt** / demoted |
| **Pass** | If spike **substitutes** for formal Pass 2 trace for that repo, note in row (e.g. `2s` for spike) per team convention |

---

## Definition of done (Step 4)

- One spike folder with **charter + outcome** (even if negative).
- Index **SPIKE / PR** column updated for the relevant repo(s).
- [agentic_doc_extraction_index.md](../agentic_doc_extraction_index.md) wave checklist: second bullet satisfied if you lacked three Pass-2 traces earlier—**spike counts** when documented.

---

## What not to do

- Do not merge spike code into `tools/scraper` **without** Runbook 05 (backlog / SSOT review).
- Do not commit `clones/` contents or large model weights.
