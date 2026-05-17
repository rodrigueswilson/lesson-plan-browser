# Grade 2 Science Book UI - Current status (handoff)

Date: 2026-04-18

## What is implemented

- Backend exposes workbook extracts in lesson bundle:
  - `GET /api/curriculum/lessons/{lesson_id}/bundle?include_book_extracts=true&book_extract_max_pages=60`
  - `GET /api/curriculum/lessons/{lesson_id}/book-extracts?offset=&limit=`
- Explorer UI has a visible `Science Book` separator/button and a `Science Book` content section.
- Ingestion script is present and runnable:
  - `python tools/db/ingest_g2_science_book_pdf.py --force`

## Verified data state (local machine)

- Local SQLite has populated workbook rows:
  - `g2_science_book_lesson_extract` has 99 rows total.
  - 20 Grade 2 Science lessons have at least 1 linked page.
- Live API can return extract rows (example):
  - `Science_2_Mod1_PropertiesOfMatter_L1` returns `book_page_extracts` count = 3.

## Current user-visible problem

- In UI, `Science Book` can still show:
  - "No workbook pages linked for this lesson yet..."
- This makes the section low-value for lesson planning in its current state.
- Standards content shown at lesson end can be badly extracted/corrupted in some lessons (example reported: Module 1 Lesson 1).

## Additional blocker: standards extraction quality

- Reported symptom pattern:
  - Standards codes appear, but neighboring non-standards content is merged into the same block.
  - Repeated OCR/token fragments appear (`ession`, `esson`, `essential`, `essment.`).
  - Career text and "Stage 3 - Learning Plan" text leak into the standards area.
- Likely root cause:
  - Weak section-boundary detection and over-capture in standards parsing/extraction.
  - Missing post-filter pass for broken OCR tokens and malformed lines.
- Impact:
  - Standards are not trustworthy enough for instructional planning.
  - Teacher-facing lesson plan quality is reduced when standards block is noisy.

## Why this can happen now

- **Cache staleness risk in current Explorer behavior:**
  - If a lesson payload in memory already has `book_page_extracts: []`, the current `fetchLessonDetails` returns from memory and does not force a network refresh for that lesson in the same session.
  - Result: UI can keep showing empty even when API/DB already has rows.
- **Lesson-level coverage quality is still weak for planning needs:**
  - Alignment is title-in-head heuristic (v1), so page assignment quality is uneven.
  - Text is raw `pdfplumber` output and not pedagogically chunked.

## Product impact (current)

- The section exists, but reliability/utility is not high enough to support lesson-plan authoring decisions.
- Current output is better as reference/debug data than as planning-ready content.

## Next session: recommended work order

1. **Fix standards extraction reliability first (must-have):**
   - Reproduce with `Science_2_Mod1_PropertiesOfMatter_L1` and capture raw source snippets.
   - Tighten section boundaries so standards stop before career/stage-plan blocks.
   - Keep only valid `code + description` pairs; drop junk OCR fragments (`ession`, etc.).
   - Add regression fixtures/tests using the failing sample text.
2. **Fix freshness first (must-have):**
   - For `Science_2_*` lessons, always revalidate from network after rendering cached data (stale-while-revalidate), even if cached `book_page_extracts` exists and is empty.
   - Add explicit "last updated" / "from cache vs live" indicator in the section.
3. **Improve alignment quality (must-have):**
   - Add deterministic override coverage for known bad page spans in `tools/db/g2_science_book_page_overrides.json`.
   - Add integration assertions for expected min page counts per lesson (or per-module allowlist).
4. **Make content planning-friendly (must-have):**
   - Add lightweight chunking/labeling (activity/question/read-aloud signals) instead of only full-page raw text.
   - Add concise summary panel for each lesson's workbook evidence.
5. **QA pass with target lessons (must-have):**
   - Validate at least one lesson per module end-to-end in UI against PDF pages.
   - Record false positives/negatives and update overrides.

## Quick verification commands

```bash
python tools/db/ingest_g2_science_book_pdf.py --force
python -c "import sqlite3; c=sqlite3.connect('data/curriculum.db'); print(c.execute('select count(*) from g2_science_book_lesson_extract').fetchone()[0])"
python -c "import json,urllib.request; lid='Science_2_Mod1_PropertiesOfMatter_L1'; u=f'http://localhost:8000/api/curriculum/lessons/{lid}/bundle?include_book_extracts=true&book_extract_max_pages=60'; d=json.load(urllib.request.urlopen(u)); print(len(d.get('book_page_extracts') or []))"
```

