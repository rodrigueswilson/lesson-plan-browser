# Prior-art research memo — Phase 0 sub-stage

**Date:** 2026-03-26  
**Parent:** [PRIOR_ART_RESEARCH_SUBSTAGE.md](../PRIOR_ART_RESEARCH_SUBSTAGE.md)  
**Architecture SSOT:** [CURRICULUM_EXTRACTION_ARCHITECTURE.md](../../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md), [ADR-002](../../decisions/ADR-002-curriculum-schema-ssot.md)

## Executive summary

We ran a systematic pass over topics **1–9** (documents → API) against public docs, GitHub issues, and community threads. Findings reinforce the existing direction: **keep DOCX as the canonical parse surface** for layout-sensitive curriculum tables, use **Docs API JSON** where we need structural truth for Google-native features (tables API, merge operations), and **avoid parallel “second extraction stacks”** without an ADR. Reliability patterns from `google-api-core` retries and Drive export limits materially affect batch design. **`python-docx` remains adequate but not innocent** for merged and nested tables—custom OOXML awareness or guarded heuristics stay justified.

**Spike scheduled:** None. No prototype rose to “clear win within Phase 0 scope.”

**Full URL log:** [2026-03-26-sources.md](./2026-03-26-sources.md)

---

## Adopt / Defer / Reject

| Finding | Classification | Phase / note |
|--------|----------------|--------------|
| Use `google.api_core.retry` (and library defaults for 429/5xx) for export/GET operations | **Adopt** (if not already uniform) | Phase 0–1 acquisition hardening |
| Treat **Drive `files.export` ~10 MB** export limit as a hard planning constraint; use documented **download / LRO** paths for oversize Workspace exports | **Adopt** (operational) | Phase 0 baseline, Phase 7 scale-up |
| Continue **heading styles + SubjectConfig anchors** as primary segmentation; add tolerance tests rather than ML header classifiers | **Defer** | Phase 3–4 template resilience |
| **Docling / unstructured / mammoth** as alternate primary extractors | **Reject** (as new SSOT) | Would duplicate stack; revisit only with ADR |
| **`fastapi-versioning` or URL `/v1`** routes for lesson payloads | **Defer** | Phase 6+ when external clients multiply |
| **Snapshot / golden** outputs for HTML excerpts; **Hypothesis** for tokenizer-style guards | **Defer** | Phase 1–3 as gates tighten |
| **`htmlcompare`-style normalization** before diffing HTML | **Defer** | Phase 3+ fidelity tooling |
| **`structlog` bound context** (`documentId`, `ingest_run_id`) | **Defer** | Nice-to-have; evaluate against current logging |

---

## Blind spots (from sub-stage doc) — status

| Blind spot | Resolution (2026-03-26) |
|------------|-------------------------|
| **Canonical input SSOT** | **Partial:** For Google-sourced curriculum, **exported DOCX** remains the practical SSOT for `RecursiveTableParser` and teacher-faithful layout; **Docs API JSON** is the authoritative structural API for Docs-native features when we need programmatic certainty (tables REST model). Parallel HTML/JSON SSOT requires an explicit ADR—**not opened** in this pass. Owner: *curriculum lead* for any unit family that cannot tolerate DOCX loss. |
| **Template stratification (2–4 archetypes)** | **Open.** Research supports classifying by **heading/list/table grammar**, not by publisher name. Owner: *TBD*; target Phase 3 kickoff. |
| **Failure taxonomy** | **Open.** Sub-stage prompts (“wrong section”, “lost merge”, etc.) should become a short enum in ingest reports. Owner: *TBD*; Phase 1 manifest work. |
| **Human-in-the-loop / override file** | **Partial:** Prefer **fixtures + verifier gates** first; minimal override (e.g. per-unit YAML patches) only after repeatable failure class. Owner: *product*. |
| **Determinism** | **Partial:** Same DOCX bytes + same parser version should yield same DB rows; document **non-deterministic** sources (live API without pinned revision). Owner: *engineering* in ingest manifest. |
| **Unicode / punctuation normalization** | **Open.** Needs explicit policy + tests (quotes, soft hyphen, NBSP). Owner: *TBD*; Phase 1–2. |
| **Licenses** | **Confirmed:** Research sources are documentary; no new third-party runtime dependency adopted from this memo. Any future adopt row must cite license (e.g. verify on PyPI/GitHub). |
| **Agent/tooling fit (testable pure functions)** | **Confirmed:** Prior art (Hypothesis, snapshots, htmlcompare) favors **small fixtures** and **deterministic compare**—aligned with refactor-friendly extraction code. |

---

## Top risks (memo section)

1. **Export size / timeout** on large units → gate batch jobs on size; implement LRO/download path before bulk Phase 7.
2. **`python-docx` + complex merges** → regression traps; keep golden extracts for worst tables.
3. **Segmentation drift** (“Warm-up” variants) without archetype strategy → SubjectConfig sprawl; mitigate in Phase 3.
4. **Schema migration** mistakes on SQLite (`NOT NULL` without default) → scripted migrations + `user_version`.
5. **Snapshot brittleness** if HTML whitespace churns → normalize before compare if we adopt snapshot tests at scale.

---

## Evidence checklist (sub-stage exit)

- [x] Topics **1–9** each have at least one sourced note (see source log).
- [x] Memo with **Adopt / Defer / Reject** table (above).
- [x] **≥3** blind spot items explicitly answered or **open with owner** (table above).
- [x] Reflexive review filed: [2026-03-26-prior-art-reflexive-review.md](./2026-03-26-prior-art-reflexive-review.md).
- [x] No silent dependency installs; deferrals name license check on adoption.
