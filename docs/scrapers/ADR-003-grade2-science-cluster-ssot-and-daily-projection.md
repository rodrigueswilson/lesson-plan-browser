# ADR-003: Grade 2 Science cluster SSOT and daily projection

## Status

Accepted.

### Implementation status (snapshot)

**Aligned with this ADR today**

- **Step 1 (writer-cluster SSOT):** Curriculum SQLite holds Science lessons and clusters as ingested; relational **`science_lesson_day_segments`** mirrors writer day bands (labels + HTML fields) per lesson. Grade 2 Science is normalized to **six module units and twenty lessons** via the canonical SSOT merge path ([`tools/db/g2_science_canonical_ssot.py`](../../tools/db/g2_science_canonical_ssot.py), [`tools/db/canonicalize_g2_science_modules.py`](../../tools/db/canonicalize_g2_science_modules.py), and `ingest_wave_unit.py` with `--canonicalize-g2-science-modules`).
- **Explorer UI ([`lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx`](../../lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx)):** Units whose ids match the canonical Science module pattern (`_Mod` + digits + `_`) are labeled **Module N** (number taken from the id when present). The module **Preamble** (“Overview & TOC”) appears when there is a **unit intro** and/or **at least one writer day band** from the outline API (so modules without `units_intro` prose can still show the band index).
- **Read-only module index (precursor to Step 2, not a calendar):** **`GET /api/curriculum/units/{unit_id}/science-day-outline`** returns per-lesson **`segment_index`** + **`day_label`** only and a **`total_writer_bands`** count. This is **SSOT metadata for pacing context**, explicitly **not** mapped to school dates. Implemented in [`backend/database/curriculum.py`](../../backend/database/curriculum.py) (`get_unit_science_day_outline`) and [`backend/routers/curriculum.py`](../../backend/routers/curriculum.py). Lesson detail continues to use **`GET /api/curriculum/lessons/{lesson_id}/bundle`** (`science_day_segments`).
- **Canonical merge and repeating day labels:** When one canonical lesson merges **several** monolithic parser rows (see [`tools/db/g2_science_canonical_ssot.py`](../../tools/db/g2_science_canonical_ssot.py) `source_parser_lesson_numbers`), [`tools/db/canonicalize_g2_science_modules.py`](../../tools/db/canonicalize_g2_science_modules.py) **concatenates** each row’s `science_li_sc_day_structured` segments. **Day labels then repeat** (e.g. multiple "Day 1" bands) because each parser row names days within its own chunk. Segment rows are **not** SQL duplicates (`UNIQUE(lesson_id, segment_index)`). The module appendix **day totals** describe writer pacing intent; the **segment count** after merge can be higher until a future dedupe/renumber strategy exists.

**Not implemented yet (still per this ADR)**

- **Step 2:** Computed **calendar projection** (start date, district calendar, pacing policy) from SSOT clusters.
- **Step 3:** **AI advisory daily drafts** with versioning and invalidation on SSOT change.

**Ongoing (all subjects, Science called out in this ADR)**

- **`SubjectConfig.SCIENCE`** and **`science_lesson_tables.py`** must stay aligned with live DOCX headings and grid shapes; golden-lesson checks after changes.

## Context

Grade 2 Science in Newark-style guides mixes two realities:

1. **Writer-authored clusters** (for example, `Day 1`, `Days 2&3`, `Days 4-7`) with rich multi-day intent.
2. **District pacing/calendar constraints** (for example, 180-day planning surfaces and module pacing targets).

In practice, Grade 2 Science author content does not collapse cleanly into a rigid one-row-per-calendar-day storage model. The source can contain more instructional day-bands than pacing targets imply. If storage is forced into fixed calendar rows, the ingest path risks duplication, truncation, or loss of writer intent.

The Grade 2 Science pipeline is also a **subject variation** in this repo: Math and ELA have their own table anchors and parsers, and Science needs a variation that preserves writer structure before any downstream calendar or AI transformations.

## Decision

### Step 1: Database storage is writer-cluster SSOT

- Persist curriculum content as close as possible to writer-authored lesson clusters (lossless HTML/text plus structured metadata where available).
- Do not make 180-day calendar rows the canonical storage shape.
- Keep cluster semantics authoritative for Science ingest.

### Step 2: Calendar view is a computed projection

- Build the UI day view from SSOT cluster records.
- Placement requires explicit scheduling inputs (unit pacing metadata, start date, district calendar/closures), not lesson text alone.
- Projection can repeat shared cluster components across consecutive day slots without rewriting SSOT.

### Step 3: AI daily plans are derived advisory drafts

- AI reads SSOT lesson clusters and context (grade, standards, district tone) to propose day-by-day drafts.
- AI output is advisory and editable; it does not overwrite author SSOT.
- Derived outputs are versioned/invalidate-on-change when upstream SSOT changes.
- Grounding rule: generated drafts must cite/tightly paraphrase source intent and must not invent new objectives/activities outside the author spirit.

## Consequences

### Positive

- Reduces brittle parsing and data loss from forcing source into fixed 180-row storage.
- Preserves writer intent as canonical while still enabling calendar-friendly presentation.
- Creates a clean boundary between ingestion truth and pedagogical drafting assistance.
- Matches district philosophy that curriculum is guidance, not a locked script.

### Tradeoffs

- Requires an explicit projection layer (calendar computation) rather than direct DB row rendering.
- Requires cache/version invalidation logic for derived calendar/AI artifacts.
- Requires governance for AI grounding and teacher review workflows.

### Ingest hardening (ongoing, not a policy change)

Science guides use headings that generic section anchors may not recognize. Ingest quality depends on keeping **`SubjectConfig.SCIENCE`** procedure and related anchor lists aligned with **actual DOCX heading text** (for example, strings such as “THE LESSON IN ACTION,” “Do It Now in Science,” and “Online Learning Activities” when those appear as section boundaries). Missing anchors can misroute text or leave **`procedure_html`** empty until configuration is extended.

Learning intentions and success criteria grids are handled by a **dedicated second pass** ([`tools/scraper/science_lesson_tables.py`](../../tools/scraper/science_lesson_tables.py)), not by pretending ELA table rules apply. Writer template drift (multi-column vs single-column grids, day-label formats) requires **hardening that module** over time, not replacing the cluster SSOT model above.

**Integration check:** After anchor or table-parser changes, validate a few **golden lessons** end-to-end: the semantic stream (including rich HTML via `json_to_html`) and the structured table payload must together cover all instructional blocks teachers expect, with no critical content living in only one path.

## Grade 2 Science module/lesson/day appendix

This appendix documents the agreed working breakdown from curriculum analysis in this project conversation.

### Module totals

| Module | Module title | Lessons | Days |
|---|---|---:|---:|
| 1 | Properties of Matter | 4 | 38 |
| 2 | Changes to Matter | 3 | 28 |
| 3 | Plants and Their Needs | 3 | 30 |
| 4 | Living Things in Habitats | 4 | 40 |
| 5 | Earth's Surface Changes | 3 | 30 |
| 6 | Earth's Surface | 3 | 29 |
| **Total** |  | **20** | **195** |

### Lesson-level day counts

#### Module 1: Properties of Matter
- Lesson 1: Describe Matter — 10 days
- Lesson 2: Solids — 9 days
- Lesson 3: Liquids and Gases — 10 days
- Lesson 4: Use Matter — 9 days

#### Module 2: Changes to Matter
- Lesson 1: Put Matter Together — 9 days
- Lesson 2: Mixtures — 9 days
- Lesson 3: Temperature Changes Matter — 10 days

#### Module 3: Plants and Their Needs
- Lesson 1: Plants Need Water — 10 days
- Lesson 2: Plants Need Light — 10 days
- Lesson 3: Plants Make More Plants — 10 days (writer headings indicate spillover in some sections)

#### Module 4: Living Things in Habitats
- Lesson 1: Habitats — 10 days
- Lesson 2: Forest and Grasslands — 10 days
- Lesson 3: Water Habitats — 10 days
- Lesson 4: Hot and Cold Deserts — 10 days

#### Module 5: Earth's Surface Changes
- Lesson 1: Weathering and Erosion — 10 days
- Lesson 2: Quick Changes to Earth's Surface — 10 days
- Lesson 3: Slowing Earth's Changes — 10 days

#### Module 6: Earth's Surface
- Lesson 1: Describe Earth's Surface — 9 days
- Lesson 2: Oceans — 10 days
- Lesson 3: Fresh Water — 10 days

## Related references

- [tools/db/g2_science_corpus.py](../../tools/db/g2_science_corpus.py) — Grade 2 Science ingest target metadata.
- [CURRICULUM_EXTRACTION_ARCHITECTURE.md](./CURRICULUM_EXTRACTION_ARCHITECTURE.md) — scraper and ingest architecture baseline.
- [tools/db/CURRICULUM_SCHEMA_SSOT.md](../../tools/db/CURRICULUM_SCHEMA_SSOT.md) — DB schema SSOT.

---

## Next session handoff prompt

Copy the block below into a new chat when continuing this track.

```text
You are continuing the LP repo (lesson-plan-browser + curriculum.db). Grade 2 Science follows ADR-003: writer-cluster SSOT in SQLite; calendar UI must eventually be a computed projection (not the canonical storage shape); AI daily drafts are advisory and must not overwrite SSOT.

Current state (do not redo unless broken):
- Canonical G2 Science: six modules, twenty lessons (see tools/db/g2_science_canonical_ssot.py; ingest via tools/db/ingest_wave_unit.py with --canonicalize-g2-science-modules as documented in corpus/runbook).
- DB: science_lesson_day_segments + lesson bundle field science_day_segments on GET /api/curriculum/lessons/{lesson_id}/bundle.
- API: GET /api/curriculum/units/{unit_id}/science-day-outline returns lightweight per-lesson day_label index and total_writer_bands (not school-calendar mapped).
- UI: CurriculumExplorer.tsx labels Science module unit ids (_Mod\d+_) as "Module N"; module overview shows writer day bands from the outline when data exists; preamble row appears if unit intro exists and/or writer bands exist.

Still open per ADR-003: (1) school-calendar projection layer with explicit start date and non-instructional days, (2) AI advisory drafts with invalidation on SSOT change, (3) ongoing parser anchor/table hardening for SubjectConfig.SCIENCE and science_lesson_tables.py.

For this session, my priority is: [STATE ONE: e.g. first slice of calendar projection / parser fix for heading X / AI draft spike with grounding rules].

Read docs/scrapers/ADR-003-grade2-science-cluster-ssot-and-daily-projection.md (implementation status) and docs/scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md. After backend or ingest changes, run python tools/scraper/verify_curriculum_db.py and the pytest set in docs/scrapers/RUNBOOK-grade2-science-three-step-pacing-and-daily-drafts.md.
```
