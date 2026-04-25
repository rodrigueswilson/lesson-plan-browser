# Phase 0 sub-stage: Prior art and external landscape research

**Status:** Planning artifact  
**Parent:** [Phase 0 in `PHASED_ROLLOUT_PLAN.md`](./PHASED_ROLLOUT_PLAN.md)  
**Pipeline SSOT (architecture):** [`docs/scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md`](../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md)

## Purpose

Time-boxed research (recommended: **one or two focused sessions**, half-day each) to learn from **GitHub projects**, **library docs**, and **Stack Overflow / community discussions** that overlap our problem: *curriculum-grade document extraction, faithful structure preservation, and normalized ingestion into SQLite (and API consumption).*  

**Goal:** reduce blind spots, borrow proven patterns, and record **what we will not adopt** so implementation stays SSOT-aligned and YAGNI-clean.

**Non-goals:** rewriting the pipeline during the research sessions, or adopting a second extraction stack without an ADR and phase gate.

## Session mechanics (systematic)

1. **Before:** Copy the topic checklist below into a dated note (see [Documentation deliverables](#documentation-deliverables)).
2. **During:** For each topic, capture 2–5 bullets: *finding*, *source (URL)*, *applies? yes/no/partial*, *follow-up*.
3. **After:** Produce the memo + integration table; **one** optional spike ticket if something is clearly worth prototyping.

---

## Topic map: from documents to database (aligned to our pipeline)

The rows mirror the end-to-end flow in `CURRICULUM_EXTRACTION_ARCHITECTURE.md`: fetch/export → transform (DOCX/JSON) → persist → API/validation.

### Topic 1 — Source documents and export surfaces

**What we do today:** Google Docs API / Drive export to DOCX and JSON; local DOCX as canonical parse input for `RecursiveTableParser`; optional HTML/JSON sidecars in other tooling.

**Sub-topics**

- **1.1** Google Docs fidelity: what is lost in **DOCX export** vs **Docs API JSON** (tables, merged cells, lists, headings, links).
- **1.2** Large documents: chunking, revision history, and practical limits for batch export.
- **1.3** Alternative sources in the wild: PDF, plaintext LMS exports, and when teams use **HTML snapshots** instead of DOCX.

**Research prompts (GitHub / SO)**

- Compare pipelines that use **Docs API JSON** as primary vs **DOCX** as primary for *tables*.
- Search for failure modes: merged cells, nested tables, list numbering, soft line breaks.

---

### Topic 2 — Acquisition layer: HTTP, auth, quotas, reliability

**What we do today:** `DocsClient` (OAuth), `export_document`, retries, temp files.

**Sub-topics**

- **2.1** OAuth and token refresh patterns for long batch jobs.
- **2.2** Rate limits, exponential backoff, idempotent retries.
- **2.3** Partial failure: resume strategies (checkpointing exports per `documentId`).

**Research prompts**

- Libraries and recipes for **resilient Google API** clients in Python.
- Stack Overflow threads on **Drive export** timeouts and large file handling.

---

### Topic 3 — DOCX / OOXML parsing and layout preservation

**What we do today:** `python-docx` traversals, custom recursive table handling, hyperlinks, runs, soft-break merge heuristics.

**Sub-topics**

- **3.1** `python-docx` strengths/limits vs direct **OOXML (lxml)** vs **docling / unstructured / mammoth**-class tools (conceptual comparison, not fad chasing).
- **3.2** Table models: grid spans, `vMerge`, nested tables, width heuristics.
- **3.3** Run-level fidelity (bold/italic, hyperlinks) vs paragraph-level shortcuts.
- **3.4** Memory and speed tradeoffs on multi-megabyte DOCX.

**Research prompts**

- Projects that parse **nested tables** or **legal/curriculum** tabular layouts.
- Issues filed against popular DOCX libraries for **merged cells** or **revision markup**.

---

### Topic 4 — Semantic interpretation: segments, anchors, and subject variance

**What we do today:** `SubjectConfig` anchors and regexes; semantic stream; standards panels; procedure vs standards boundary guards.

**Sub-topics**

- **4.1** Rule-based sectioning vs **finite-state / line-based parsers** vs lightweight ML (when each is justified).
- **4.2** Normalizing heading variants (“Warm-up”, “Warm Up”, “Activity 1”) without overfitting one district’s template.
- **4.3** **Multi-lesson** document segmentation (TOC noise vs real headers).
- **4.4** Cross-subject patterns: ELA vs Math section vocabulary; shared framework (WIDA-style overlays) without coupling parsers to one publisher.

**Research prompts**

- Parsers for **syllabi**, **lesson plans**, or **standards-aligned** docs.
- Techniques for **robust header detection** in messy Office exports.

---

### Topic 5 — Enrichment and secondary fetches (linked docs)

**What we do today:** Recursive fetch of linked Google Docs into DOCX for Procedure enrichment; skip non-exportable types.

**Sub-topics**

- **5.1** Controlling recursion depth, cycles, and deduplication.
- **5.2** Detecting **non-document** links early (Slides, PDF, Drive folders).
- **5.3** Caching exports by `documentId` + revision to avoid thrash.

**Research prompts**

- Web crawlers / doc pipelines with **strict breadth limits** and **same-domain** rules adapted to “same curriculum bundle.”

---

### Topic 6 — Data model, SQLite, migrations, validation

**What we do today:** `curriculum.db` normalized schema; `curriculum_validation` gates; `upsert_lesson` column filtering; provenance columns.

**Sub-topics**

- **6.1** Schema migration strategies for SQLite (expand/contract, one-writer discipline).
- **6.2** Validation at boot vs validation in CI (`verify_curriculum_db.py` pattern).
- **6.3** When to use **JSON columns** vs **side tables** for variable-shaped blobs (e.g. standards panels).
- **6.4** ORMs vs raw SQL for this codebase’s style (fit with existing FastAPI + small DB layer).

**Research prompts**

- Small service patterns: **schema drift detection** in production.
- Stack Overflow on **SQLite ALTER TABLE** and zero-downtime local apps.

---

### Topic 7 — API surface, contracts, and consumer ergonomics

**What we do today:** FastAPI routers, Pydantic models, OpenAPI as contract for generated clients.

**Sub-topics**

- **7.1** Versioning and backward compatibility for lesson payloads.
- **7.2** Field-level documentation for generated clients (provenance, structured standards).
- **7.3** Pagination/search patterns for curriculum browsers at scale (future FTS).

---

### Topic 8 — Quality, regression testing, and “definition of faithful”

**What we do today:** `verify_curriculum_db.py`, standards leakage checks, structured standards shape checks, ingest manifests.

**Sub-topics**

- **8.1** Golden-file / snapshot testing for HTML excerpts (stability vs brittle).
- **8.2** Property-based tests for tokenization and heading guards.
- **8.3** Diff tooling for “expected paragraph order” vs source.

**Research prompts**

- Open-source **document diff** or **HTML normalization** prior to compare.
- Testing strategies for **extract-transform-load** when upstream format drifts.

---

### Topic 9 — Observability, provenance, and operational safety

**What we do today:** `ingest_reports/*.json`, parser version fields, run ids.

**Sub-topics**

- **9.1** Structured logging fields that help diagnose parser mistakes by `documentId` + `ingest_run_id`.
- **9.2** Redaction/PII: what curriculum docs sometimes embed in headers/footers.
- **9.3** Run manifests: minimum viable vs enterprise audit trails.

---

## Questions and blind spots (high leverage for this project)

These are easy to miss but disproportionately affect multi-unit scale-up.

- **Canonical input SSOT:** For each curriculum family, is **DOCX export** always the legal source of truth, or do we sometimes need **JSON** or **HTML** as parallel SSOT? What breaks if we pick wrong?
- **Template stratification:** Can we classify units into **2–4 structural archetypes** early so SubjectConfig does not become a mega-switch?
- **Failure taxonomy:** Do we have named failure classes (“wrong section”, “lost merge”, “spurious lesson boundary”, “standards leak”) with owners?
- **Human-in-the-loop hook:** Where would a **minimum** correction UI or override file pay off vs more code?
- **Determinism:** Are ingest runs **reproducible** given the same DOCX bytes and parser version?
- **Unicode and punctuation:** Normalization policies (quotes, dashes, soft hyphen) and tests that catch silent corruption.
- **Licenses:** Third-party code or datasets from research must align with project licensing and **no** leaking of copyrighted curriculum text into public artifacts.
- **Agent/tooling fit:** Extraction code that is **testable in isolation** (pure functions for buffers, golden streams) helps automated refactors; research should flag libraries that compose well with **small fixtures** vs “black box” pipelines.

---

## Reflexive review (final session, mandatory)

**Purpose:** Step back from the pile of links and notes. Decide whether this sub-stage **earned its cost** and what you will do differently next time.

**Who:** Product owner (you) plus whoever executed the research (human and/or agent). The review is allowed to conclude that research added **little**—that is a valid outcome if documented.

### Prompts (answer in the reflexive memo)

**Validity of the process**

- Did we research the **right** slice of the pipeline (topics 1–9), or did we drift into generic browsing?
- Was the time box respected? If not, what caused slippage?
- Was the **Adopt / Defer / Reject** discipline used, or did we accumulate “interesting” without decisions?

**Impact on the plan**

- List **concrete** changes: updates to `PHASED_ROLLOUT_PLAN.md`, phase ordering, a **new** risk, a **cancelled** idea, a dependency rejected, a spike scheduled or killed.
- If **nothing** changed: state that explicitly and explain why (e.g. “confirmed current approach” is still valuable).

**Learning for the future**

- Should we **repeat** a similar research pass before **Phase 3**, **Phase 4**, or only when a **trigger** fires (see below)?
- What **one** process tweak would make the next cycle smarter (narrower topics, stricter source quota, mandatory prototype for “Adopt”)?

### Triggers to repeat this research pattern later

Consider a **light** prior-art pass (shorter than Phase 0) when **any** of these are true:

- New **canonical document shape** (e.g. first ELA unit with a different table grammar, or PDF ingress).
- A phase goal that **changes extraction SSOT** or adds a **major** dependency.
- Repeated **same-class** parser incidents in production or acceptance (signal that assumptions are wrong).

You may **skip** a full repeat when changes are **localized** and covered by existing gates and fixtures.

### Anti-patterns to flag in the reflexive memo

- No traceable link between findings and **Adopt/Defer/Reject**.
- Tail-heavy work: many sources, few decisions.
- “Library tourism” without a hypothesis tied to a topic id (1–9).

---

## Documentation deliverables (what “done” looks like)

All artifacts live under version control, ideally beside other curriculum control docs.

| Artifact | Path (recommended) | Purpose |
|----------|-------------------|---------|
| Research memo | `docs/curriculum/research-notes/YYYY-MM-DD-prior-art-memo.md` | Executive summary, decisions, non-goals |
| Source log | Same memo or `.../YYYY-MM-DD-sources.md` | Table: URL, topic id (1–9), takeaway, adopt? |
| **Reflexive review memo** | `docs/curriculum/research-notes/YYYY-MM-DD-prior-art-reflexive-review.md` | Process validity, plan deltas, repeat/skip criteria |
| Risk register delta | Optional section in memo | Top 5 risks with mitigations |
| Spike outcomes | `docs/curriculum/research-notes/spikes/<name>.md` | If a prototype was built, record result and discard branch |
| Index | `docs/curriculum/research-notes/README.md` | Links to dated notes |

**Naming:** One folder per research cycle or per month; avoid orphan filenames in repo root.

---

## Integrating findings into code (controlled path)

Research must not bypass phase gates.

1. **Classify each finding**
   - **Adopt now** (small, clear win, fits SSOT).
   - **Defer** (tag with phase: e.g. Phase 3 template resilience).
   - **Reject** (record reason; prevents re-litigation).
2. **If adopting**
   - Prefer **one** focused PR with: code change, tests or verifier update, short note in `docs/scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md` or `subject_config` docs if behavior changes.
   - Bump **`ingest_parser_version`** or documented parser version string when extraction semantics change.
3. **If deferring**
   - Add a row to `SAMPLE_MATRIX_AND_ADAPTATION_ALERTS.md` or the phase checklist so it surfaces when that phase starts.
4. **If a new dependency**
   - Require explicit justification (weight, maintenance, license), and an ADR if it changes the extraction SSOT story.

---

## Evidence checklist (sub-stage exit)

- [ ] Topic map **1–9** touched with at least **one** sourced note each (link or citation).
- [ ] Memo filed under `docs/curriculum/research-notes/` with **Adopt / Defer / Reject** table.
- [ ] At least **three** “blind spot” items from this doc explicitly answered or marked as open with owner/date.
- [ ] **Reflexive review memo** filed: process validity, **whether the plan changed** (yes/no + how), **repeat vs skip** guidance for future phases.
- [ ] No silent dependency decisions: anything proposed for install is listed with **license** and **why ours**.

---

## Suggested Stack Overflow search patterns (examples)

Use quoted phrases and narrow tags `[python]`, `[google-api]`, `[python-docx]`, `[sqlite]`, `[docx]`, `[xml]`.

- `"python-docx" merged cells`
- `Google Docs API` export `docx` tables
- `sqlite` migration `add column` production
- `ETL`, `pytest` snapshot HTML
- `beautifulsoup` vs `lxml` large HTML lesson plan

Adapt patterns to each **Topic 1–9** question list.
