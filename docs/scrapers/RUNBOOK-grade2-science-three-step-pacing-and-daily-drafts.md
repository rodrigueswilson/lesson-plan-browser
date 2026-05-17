# Runbook: Grade 2 Science three-step pacing and daily drafts

This runbook explains how to operate Grade 2 Science as a dedicated scraper/parser/ingest variation while preserving writer-cluster SSOT and supporting projected calendar views plus AI advisory daily drafts.

## Scope

- Subject: **Grade 2 Science**
- Position in system: add-on variation alongside Math and ELA ingestion patterns
- Unit source currently tracked in repo: [tools/db/g2_science_corpus.py](../../tools/db/g2_science_corpus.py)

## The three-step workflow

### Step 1 — Ingest and store writer-faithful clusters (SSOT)

Goal: keep source as close as possible to how curriculum writers authored lessons/day bands.

Operational commands (repo root):

```powershell
python tools/db/ingest_wave_unit.py --unit-id Science_2_U1_1SNRc-NF --grade 2 --subject Science --unit-number 1 --title "Grade 2 Science Unit 1: Matter" --doc-id 1SNRc-NFiJy41Jxrko8nZ158Od4gJxy1cojiNzEeOvXM
python tools/db/backfill_science_lesson_day_segments.py
```

If you already have an exported DOCX, add `--docx "<path-to-docx>"` to avoid Drive export.

SSOT intent:
- `lessons` keeps canonical lesson content fields.
- Science structured payloads stay aligned with writer clusters.
- Relational segment rows are derived support for readers and tooling, not a replacement for writer truth.

### Step 2 — Project clusters into the calendar UI

Goal: present a day-organized teacher experience without changing SSOT storage shape.

Placement logic requires explicit scheduling inputs:
- unit pacing target,
- start date,
- district/school calendar (holidays, closures, non-instructional days),
- optional policy constraints (for example, max minutes/day).

Important:
- Cluster records alone do not decide calendar placement.
- A 180-day UI is a computed projection, not the canonical source representation.

### Step 3 — Generate daily advisory drafts via AI

Goal: convert lesson clusters into day-sized draft plans, lesson by lesson.

Required behavior:
- AI reads SSOT lesson content and day counts.
- AI outputs advisory daily drafts (editable by teachers).
- AI does not overwrite SSOT source content.
- AI must not invent objectives/activities outside author intent.

Versioning rule:
- Any update to SSOT lesson content invalidates derived calendar/AI drafts for that lesson (or unit).

## Parser hardening and integration checks

Science ingest combines two mechanisms:

1. **Semantic stream** — `RecursiveTableParser` + `SubjectConfig.SCIENCE` anchors route text into lesson HTML fields (`procedure_html`, etc.). Generic anchors alone often miss Newark Science headings; extend [`tools/scraper/subject_config.py`](../../tools/scraper/subject_config.py) with **exact DOCX strings** used as section boundaries (examples that often apply: “THE LESSON IN ACTION,” “Do It Now in Science,” “Online Learning Activities”). Re-ingest and confirm `procedure_html` (and related fields) are populated on golden lessons.

2. **Structured tables pass** — [`tools/scraper/science_lesson_tables.py`](../../tools/scraper/science_lesson_tables.py) captures learning-intention / success-criteria grids and related structure. Harden this module when writers change grid shape or day labels (multi-column vs single-column, band wording).

**Integration cross-check:** On representative lessons, compare (a) rendered lesson HTML from the semantic path with (b) structured JSON / relational segments from the table pass. No critical instructional block should exist only in one path without an intentional design reason.

## Validation checklist

After ingest/backfill, run:

```powershell
python tools/scraper/verify_curriculum_db.py
```

Then confirm:

1. Schema gate passes (`curriculum_validation` reports no missing required tables/columns).
2. Lesson and structured payload coverage is as expected for the current Science variation.
3. Bundle API for a sample lesson returns lesson + standards/vocabulary + science day support fields used by UI.
4. For a canonical Science module unit, **`GET /api/curriculum/units/{unit_id}/science-day-outline`** returns non-empty **`lessons`** / **`total_writer_bands`** when `science_lesson_day_segments` rows exist (lightweight index for the explorer module overview; not a school calendar).

Optional test pass:

```powershell
python -m pytest tests/science_lesson_tables_test.py tests/science_lesson_day_segments_test.py tests/test_curriculum_lesson_bundle.py -q
```

## Troubleshooting

### A) Pacing mismatch (195 writer days vs 180 calendar days)

This is expected in the Grade 2 Science variation.
- Do not truncate SSOT source content to force fit.
- Resolve mismatch in projection/policy layer (calendar allocation decisions), not by deleting source detail.

### B) Missing derived daily drafts after content changes

Likely stale derived cache/version.
- Recompute projection and AI drafts for affected lessons/units.
- Keep source lesson content unchanged unless ingest itself changed.

### C) Ingest warnings on Science overview attachment

When parser warnings indicate missing overview matches:
- verify source DOCX/export quality,
- verify parser variation for current writer template patterns,
- rerun ingest + verify and check coverage deltas.

## Grade 2 Science planning reference (current analysis baseline)

| Module | Lessons | Days |
|---|---:|---:|
| Module 1 | 4 | 38 |
| Module 2 | 3 | 28 |
| Module 3 | 3 | 30 |
| Module 4 | 4 | 40 |
| Module 5 | 3 | 30 |
| Module 6 | 3 | 29 |
| **Total** | **20** | **195** |

Use these values as planning guidance in projection/AI layers until a newer validated analysis supersedes them.

## Related docs

- [ADR-003-grade2-science-cluster-ssot-and-daily-projection.md](./ADR-003-grade2-science-cluster-ssot-and-daily-projection.md)
- [CURRICULUM_EXTRACTION_ARCHITECTURE.md](./CURRICULUM_EXTRACTION_ARCHITECTURE.md)
- [tools/db/CURRICULUM_SCHEMA_SSOT.md](../../tools/db/CURRICULUM_SCHEMA_SSOT.md)
