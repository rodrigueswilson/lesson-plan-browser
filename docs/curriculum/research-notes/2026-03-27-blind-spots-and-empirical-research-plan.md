# Plan: Correct research blind spots, bias, and run empirical / export–parser research

**Purpose:** Turn prior work (GitHub/SO prior-art, pipeline outline) into **ground-truth research on your corpus**, **named failure modes**, and **decidable** export-vs-parser questions—without scope creep into new parser stacks.

**Depends on:** [SAMPLE_MATRIX_AND_ADAPTATION_ALERTS.md](../SAMPLE_MATRIX_AND_ADAPTATION_ALERTS.md), [QUALITY_GATES.md](../QUALITY_GATES.md), [CURRICULUM_EXTRACTION_ARCHITECTURE.md](../../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md), [2026-03-26-prior-art-memo.md](./2026-03-26-prior-art-memo.md).

**Non-goals (YAGNI):** Adopting Docling/Unstructured as SSOT; broad SO “library tourism”; full PDF pipeline; new microservices.

---

## Part A — Blind spots and how to close them

These were **under-weighted** relative to public-repo research. Each row is a **closed deliverable** you can tick.

| Blind spot | Risk | Mitigation (what to do) | Deliverable | Owner |
|------------|------|-------------------------|-------------|--------|
| **Corpus-agnostic prior art** | Optimizes for generic DOCX, not *your* templates | Run **Part B** on [sample matrix](../SAMPLE_MATRIX_AND_ADAPTATION_ALERTS.md) units first; do not add new libs until a **failure class** is top-ranked | `empirical-profile/` JSON or CSV bundle per wave (see §2) | Engineering |
| **Export fidelity unknown** | Bugs filed against parser when Google export is the culprit | Run **Part C** on a stratified sample | `export-vs-parser/` report per unit or per lesson (see §3) | Engineering |
| **Unnamed failures** | Cannot prioritize fixes or alerts | Run **Part D** workshop + lock enum | `docs/curriculum/FAILURE_TAXONOMY.md` (or section in adaptation doc) | PO + engineering |
| **Non-Docs / non-exportable links** | Silent content gaps | Extend crawler/ingest **inventory**: count skipped link types per unit; missing procedure enrichment where applicable | One table per unit: skipped types + doc ids | Engineering |
| **Ops / quotas / large files** | Flaky batch, mysterious timeouts | Document **observed** limits (export size, run time) for your jobs; link official Drive/Docs docs | Short **runbook** section in scraper README or `docs/curriculum/` | Ops / engineering |
| **Unicode / normalization** | Silent drift in gates | Pick **one** policy (NFKC or not; quotes; soft hyphen); add **one** verifier rule + fixtures | ADR-length note + test cases | Engineering |
| **PII / license in artifacts** | Leak in logs, reports, screenshots | Redaction checklist for archived evidence; scrub before external SO/GitHub | [QUALITY_GATES](../QUALITY_GATES.md) or acceptance checklist bullet | PO |
| **Human-in-the-loop threshold** | Endless parser tweaks | Rule: **top 2 failure classes** from Part B get code; rest Yellow + alert until repeated | Decision log in adaptation alerts | PO |

---

## Part B — Bias in what we researched (and correction)

| Bias | Correction |
|------|------------|
| **GitHub-first** | Treat repos as **pattern catalog** only; **acceptance** is always **your DB + gates** (`verify_curriculum_db.py`, `test_curriculum_gaps.py`, matrix policy). |
| **DOCX-centric** | Explicitly log **JSON/API** and **HTML export** artifacts for the same `documentId` where ambiguity exists (Part C). |
| **Tool-complete tests elsewhere** | No external project proves **extraction → curriculum.db**; your **ingest_reports + verifiers** are the SSOT for E2E. |

**Ceremony (one hour):** Team re-reads [2026-03-26-prior-art-reflexive-review.md](./2026-03-26-prior-art-reflexive-review.md) and agrees: *no new dependency* without ADR + failure-class evidence.

---

## Part C — “Research now”: empirical profiling (ordered)

**Objective:** Quantify **structure and outcome** per lesson/unit so template variance is **data**, not opinion.

### C.1 Sampling SSOT

- Use **Wave 1** rows from [SAMPLE_MATRIX_AND_ADAPTATION_ALERTS.md](../SAMPLE_MATRIX_AND_ADAPTATION_ALERTS.md) at minimum: G3 Math Unit 2 (anchor), then Unit 1 and one “high variance” row.
- Add **one ELA** row when Phase 4 prep starts (or sooner if cross-subject risk is high).

### C.2 Metrics to collect (per lesson, or per unit aggregate)

Define each metric so it can be computed from **existing** artifacts (DOCX path + optional saved Docs JSON) without a new parser stack.

| Metric | Definition / computation idea | Why |
|--------|-------------------------------|-----|
| `lesson_key` | Unit id + lesson number or title slug | Join rows |
| `source_doc_id` | From provenance | Traceability |
| `table_count` | Count `w:tbl` (or `python-docx` `document.tables` + nested walk if you already have it) | Complexity |
| `max_table_depth` | Max nesting depth of tables | Nested layout risk |
| `merged_cell_events` | Count of vertical merge continues / grid spans (from OOXML or library) | Merge fragility |
| `anchors_matched` | List of `SubjectConfig` anchor keys that fired | Routing health |
| `anchors_missing` | Expected anchors for subject − matched | Template drift |
| `gates_result` | Pass/fail per [QUALITY_GATES.md](../QUALITY_GATES.md) Gate A–D | Outcome |
| `adaptation_status` | Green/Yellow/Red per sample matrix | Program view |
| `db_null_fields` | Required lesson fields that are NULL/empty after ingest | Functional gap |

**Storage:** `docs/curriculum/research-notes/empirical-profile/YYYY-MM-DD-waveN-profile.json` (or CSV per table). Keep **small**; no full HTML body in public repo if license-sensitive—use hashes + lengths + gate flags.

### C.3 Execution steps

1. **Baseline:** Run ingest + verifiers on anchor unit; store profile + ingest report path.
2. **Expand:** Same script/protocol for each additional matrix row **before** parser changes.
3. **Cluster:** Sort lessons/units by `anchors_missing`, `merged_cell_events`, `gates_result`. Produce a **short** “archetype candidates” list (e.g. 2–4 patterns)—**hypotheses**, not final taxonomy.
4. **Review:** PO labels each cluster **Accept as-is / Tune anchors / New archetype / Blocked**.

### C.4 Exit criteria (profiling pass)

- [ ] Every **Wave 1** matrix row has a profile artifact.
- [ ] **Top 3** structural outliers are named with **lesson ids** and **metric values**.
- [ ] **Failure taxonomy** (Part E) tags are applied to at least **10** concrete failures from this pass.

---

## Part D — Export vs parser checks (ordered)

**Objective:** For ambiguous failures, decide **export distortion** vs **parser logic** with a **repeatable protocol**.

### D.1 Prerequisites

- Frozen **`documentId`** + optional **revision id** (if you adopt revision pinning later).
- Saved artifacts in a **private** or redacted store as needed:
  - **A:** Drive-exported **DOCX** (current path).
  - **B:** `documents.get` **JSON** (tabs + body)—already supported by your client.
  - **C:** Optional **HTML** export if you already use it in `main.py`.

### D.2 Comparative dimensions (not full semantic diff)

| Dimension | DOCX path | JSON path | Interpretation |
|-----------|-----------|----------|----------------|
| Table count (approx.) | Count tables | Count `table` structural elements | Large mismatch → export or tab model |
| Paragraph order in lesson block | Stream order from parser | Structural order in JSON | Reordering / split paragraphs |
| Hyperlinks in procedure | From DOCX runs | From `link` in JSON | Lost links in export |
| Anchor strings present | Text scan in DOCX extraction | Plain text flatten of JSON | Anchor visible in one only → routing bug vs missing text |

### D.3 Per-failure workflow

1. Pick a lesson with **Yellow/Red** and a **single** primary symptom (e.g. empty `procedure_html`).
2. Run **D.2** checks; record **same / different** with one paragraph.
3. Classify:
   - **Export issue** → track in failure taxonomy; consider JSON-assisted spot check or Google-side workaround; do not “fix parser” blindly.
   - **Parser issue** → tie to taxonomy class; minimal code + fixture.
   - **Template issue** → `SubjectConfig` / archetype; document in adaptation alerts.

### D.4 Exit criteria (export–parser pass)

- [ ] At least **5** historical failures classified with **export/parser/template** labels.
- [ ] **One** written example (redacted) archived under `acceptance-evidence/` or internal store referencing artifact paths.

---

## Part E — Failure taxonomy (binds profiling + export checks)

**Objective:** A **small enum** (8–12 values) used in `ingest_reports`, adaptation alerts, and profiling rows.

### E.1 Suggested starter set (edit after empirical pass)

| Code | Meaning | Typical next action |
|------|---------|---------------------|
| `ANCHOR_MISS` | No `SubjectConfig` match | Extend anchors / archetype |
| `TABLE_GRID` | Non-rectangular or merge breaks assumptions | Table handler / tests |
| `BOUNDARY_LEAK` | Procedure text in standards | Guards in `flush_buffer` |
| `EXPORT_LOSS` | JSON has structure DOCX lacks (or vice versa) | Export–parser protocol |
| `LINK_SKIP` | Linked doc not ingestible | Inventory / manual |
| `SCHEMA_GATE` | `verify_curriculum_db` / validation | DB or ingest mapping |
| `EMPTY_FIELD` | Gate: required field empty | Trace upstream to above |
| `UNKNOWN` | Unclassified | Triage bucket (cap % of total) |

### E.2 Rules

- Every **Yellow/Red** unit gets **≥1** primary code + optional secondary.
- **Unknown** rate must fall after each wave (or scope is too wide).

### E.3 Deliverable

- `docs/curriculum/FAILURE_TAXONOMY.md` (new) or a section appended to [SAMPLE_MATRIX_AND_ADAPTATION_ALERTS.md](../SAMPLE_MATRIX_AND_ADAPTATION_ALERTS.md) §4—**pick one SSOT** (avoid two enums).

---

## Part F — Timeline (suggested sequencing)

| Week | Focus | Outputs |
|------|--------|---------|
| **1** | **E** Taxonomy v0 + anchor unit profile | `FAILURE_TAXONOMY.md`, first profile JSON |
| **2** | **C** Wave 1 full profiling | Profile bundle + “top outliers” memo |
| **3** | **D** Export–parser on top 3 outliers | Classification memo + 1 archived example |
| **4** | Fix **top 2 failure classes** only (code or config) | PRs + rerun profiles + gate evidence |

Adjust cadence to team size; do not start Week 4 until Week 2 data exists (data-driven).

---

## Part G — Stack Overflow / external questions (only when useful)

Ask on SO or library issues **after**:

1. Minimal reproducible **snippet** (structure only; no copyrighted lesson text), and  
2. Internal label: **export vs parser** (Part D).

Good targets: `python-docx` merge edge, specific `HttpError` from Drive, SQLite migration. Poor targets: “how to parse our curriculum.”

---

## Part H — Links to existing artifacts

- Pipeline / prior-art outline: [2026-03-26-pipeline-functions-vs-prior-art-outline.md](./2026-03-26-pipeline-functions-vs-prior-art-outline.md)
- Repo evidence: [2026-03-26-pipeline-outline-repo-evidence.md](./2026-03-26-pipeline-outline-repo-evidence.md)
- Failure taxonomy SSOT: [FAILURE_TAXONOMY.md](../FAILURE_TAXONOMY.md)
- Ingest report shape: `_build_ingest_report` in `tools/scraper/table_extractor.py` plus `ingest_stats` / auto-tags; codes applied via `tools/scraper/ingest_failure_codes.py` and optional `verify_curriculum_db.py --ingest-report`

---

## Checklist (executive)

- [ ] **A:** Blind-spot table owners assigned  
- [ ] **C:** Wave 1 empirical profiles filed  
- [ ] **D:** ≥5 failures export/parser classified  
- [ ] **E:** Single SSOT taxonomy doc + codes in reports/alerts  
- [ ] **F:** Top 2 classes addressed with evidence  

When all are true, **bias from generic prior-art is materially corrected** for the current rollout phase.
