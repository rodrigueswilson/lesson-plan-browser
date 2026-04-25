# Grade 2 Inspire Science student PDF: inventory, SSOT parity, crosswalk, and golden QA

This document records how we use the on-disk **student workbook PDF** next to the scraped **teacher** export as a **QA and planning complement**. Seeded rows in **`g2_science_book_lesson_supplement`** (plus bundle API) make that consultable in-app. It does **not** replace curriculum SSOT (see [ADR-003](ADR-003-grade2-science-cluster-ssot-and-daily-projection.md)).

## 1. Source artifact and extraction

| Item | Value |
| --- | --- |
| PDF path | `reference_docs/scraped/Copy_of__2nd_Grade_Science/originals/Inspire_Science_Grade2_Paired_Read_Aloud_TeachersEdition_9780021344871.pdf` |
| ISBN (filename) | 9780021344871 |
| Pages | 324 |
| Extractor | `pdfplumber` via [`tools/scraper/g2_inspire_science_student_pdf_inventory.py`](../../tools/scraper/g2_inspire_science_student_pdf_inventory.py) |
| Machine index | `reference_docs/scraped/Copy_of__2nd_Grade_Science/originals/Inspire_Science_Grade2_Paired_Read_Aloud_TeachersEdition_9780021344871.inventory.json` (regenerate with the script) |

**What the PDF actually is:** Text extraction and page sampling show a **full Inspire Science Grade 2 student workbook / “Be a Scientist” journal** (module openers, probes, inquiry pages, wrap-ups), not a slim standalone “stories only” pamphlet. The Anna’s Archive / McGraw-Hill filename uses “Science Paired Read Aloud”; treat the file as **student-facing workbook evidence** for exercises and module boundaries, and use the **teacher** export [`Tab_1.md`](../../reference_docs/scraped/Copy_of__2nd_Grade_Science/Tab_1/Tab_1.md) for explicit **Science Paired Read Aloud** subsection titles (e.g. “From Nature or From People”, “Abe and Abby’s Big Surprise”).

**Extraction quality:** Headers are noisy in `pdfplumber` output (fonts / text order). Use the JSON **per-page `head` previews** plus the **module_signals** list for coarse alignment; rely on human PDF viewing for fine layout.

## 2. Structure parity vs canonical SSOT

Canonical module and lesson titles are defined in [`tools/db/g2_science_canonical_ssot.py`](../../tools/db/g2_science_canonical_ssot.py) (`g2_science_modules()`).

**Match:** All six writer module themes appear in the PDF (`Properties of Matter`, `Changes to Matter`, `Plants and Their Needs`, `Living Things in Habitats`, `Earth’s Surface Changes`, `Earth’s Surface` / describe Earth’s surface). `module_signals` in the inventory JSON records **MODULE OPENER** / **MODULE WRAP-UP** pages with those themes.

**Important mismatch (print order vs canonical module number):** In this PDF, **physical page order** is not `Mod1 … Mod6` in the same order as `module_number` 1–6 in the database. Approximate **first MODULE OPENER page per theme** (from `inventory.json`):

| `module_hint` (PDF) | First MODULE-style page (approx.) |
| --- | ---: |
| PropertiesOfMatter | 8 |
| ChangesToMatter | 62 |
| EarthSurface (canonical Mod 6) | 106 |
| EarthSurfaceChanges (canonical Mod 5) | 148 |
| LivingThingsInHabitats (canonical Mod 4) | 194 |
| PlantsAndTheirNeeds (canonical Mod 3) | 250 |

Canonical order in SSOT / `curriculum.db` remains **1 Matter, 2 Changes, 3 Plants, 4 Habitats, 5 Surface Changes, 6 Earth Surface**. The book is still **one Grade 2 course**; only the **binding order** of modules in this PDF differs from `unit_number` ordering.

## 3. Book surface patterns (compare to DOCX lesson flow)

Regenerate: `python tools/scraper/g2_inspire_science_student_pdf_inventory.py` (writes `*.inventory.json` and `*.book_patterns.json`) or `python tools/scraper/g2_inspire_science_student_pdf_inventory.py --only-patterns`.

**Keyword counts (324 pages)** from [`...9780021344871.book_patterns.json`](../../reference_docs/scraped/Copy_of__2nd_Grade_Science/originals/Inspire_Science_Grade2_Paired_Read_Aloud_TeachersEdition_9780021344871.book_patterns.json): 12 `MODULE_OPENER`, 12 `MODULE_WRAP_UP`, 9 `ASSESS_LESSON_READINESS`, 46 pages mentioning “Inquiry”, 25 with Obtain/Communicate band language, 17 `PERFORMANCE_TASK`, 6 evaluate-style headers.

**Lesson title in page head** counts (first ~480 chars): noisy for short words (e.g. “Habitats”); use **with** canonical title length and seed script spans, not as sole join key.

**Improving curriculum DOCX comparison:** (1) DOCX / DB are organized by **writer module + lesson** and **day segments**; the PDF repeats **module opener → readiness probe → inquiry bands → obtain/communicate → performance** per lesson. (2) Map on **canonical lesson title** + **module theme**, not monolithic `Lesson N:` from the long teacher Doc. (3) Expect **Unicode / font** noise in PDF text; prefer **page images** or manual QA for final paired-read story boundaries. (4) Teacher `Tab_1` uses **“Science Paired Read Aloud”**, **Science File**, **Digital Interactive**, and **Leveled Readers**—treat those as **parallel artifact types** when complementing `procedure_html` / `science_li_sc_day_structured`.

## 4. All 20 lessons: DB supplement + golden metrics

**Seed (PDF + Tab_1 → SQLite):** [`tools/db/seed_g2_science_book_lesson_supplement.py`](../../tools/db/seed_g2_science_book_lesson_supplement.py) fills `g2_science_book_lesson_supplement` for every `Science_2_Mod*` lesson. Re-run after changing the PDF or Tab_1 export.

**API:** `GET /api/curriculum/lessons/{lesson_id}/bundle` includes optional `book_lesson_supplement` (see [`CurriculumBookLessonSupplement`](../../backend/schemas/curriculum.py)). Workbook page text: query `include_book_extracts=true` (and optional `book_extract_max_pages`, default 20, max 60) for a capped list, or `GET /api/curriculum/lessons/{lesson_id}/book-extracts?offset=&limit=` for pagination. Response `body_text` may end with `...[truncated]` when very long.

**Text ingest (SQLite):** [`tools/db/ingest_g2_science_book_pdf.py`](../../tools/db/ingest_g2_science_book_pdf.py) writes **`g2_science_book_lesson_extract`** (per-page rows). Optional overrides: [`tools/db/g2_science_book_page_overrides.json`](../../tools/db/g2_science_book_page_overrides.json).

**Runbook (repo root):**

1. Prefer `--dry-run` first (counts and assignment preview; no DB writes).
2. Stop the API if it holds a lock on `data/curriculum.db`, then run a full ingest: `python tools/db/ingest_g2_science_book_pdf.py --force` (or set `CURRICULUM_DB_PATH`). Full run **requires** `--force` so stale page-to-lesson rows are cleared before re-insert.
3. Single lesson: `python tools/db/ingest_g2_science_book_pdf.py --lesson-id Science_2_Mod1_PropertiesOfMatter_L1` (clears rows for that lesson only, then inserts matching pages).

**Manual QA checklist (after ingest):**

- Spot-check one lesson: open the PDF at reported page numbers and compare visible text to `bundle?include_book_extracts=true` (or `book-extracts`).
- Note pages with `char_count` very low or empty in logs (`low_text_pages`); expect scan-like pages until OCR exists.
- For lessons with short titles, confirm `alignment_ambiguous` / `alignment_confidence` in DB or API; add overrides JSON entries for systematic mis-assignments.
- Confirm `COUNT(*)` from `g2_science_book_lesson_extract` grouped by `lesson_id` matches expectations for the 20 canonical Science lessons (allow zeros only where PDF has no title-in-head match and no override).

**Curated paired-read / resource headings** (column `paired_read_block_title`) summarize Tab_1 / teacher blocks; **PDF page spans** are **heuristic** (title appears in top-of-page text window; alias `Forests and Grasslands` used for `Forest and Grasslands`).

| `lesson_id` | SSOT title | PDF pages (est.) | `first_page_workbook_pattern` | `paired_read_block_title` (abridged) |
| --- | --- | --- | --- | --- |
| `Science_2_Mod1_PropertiesOfMatter_L1` | Describe Matter | 10–11 | ASSESS_LESSON_READINESS | Matter Is All Around Us; Irene's Exploration |
| `Science_2_Mod1_PropertiesOfMatter_L2` | Solids | 25–34 | OTHER_WORKSHEET | From Nature or From People |
| `Science_2_Mod1_PropertiesOfMatter_L3` | Liquids and Gases | 36–45 | OTHER_WORKSHEET | Paired read + Science File |
| `Science_2_Mod1_PropertiesOfMatter_L4` | Use Matter | 53 | OTHER_WORKSHEET | Material Matters; Matter, Properties, and Making Things |
| `Science_2_Mod2_ChangesToMatter_L1` | Put Matter Together | 64–67 | OTHER_WORKSHEET | Rearranging matter / blocks |
| `Science_2_Mod2_ChangesToMatter_L2` | Mixtures | 80–89 | INQUIRY_WORKSHEET | Mixtures video; digital interactives; Science File |
| `Science_2_Mod2_ChangesToMatter_L3` | Temperature Changes Matter | 92–95 | ASSESS_LESSON_READINESS | Abe and Abby's Big Surprise; Matter, Temperature, and Change |
| `Science_2_Mod3_PlantsAndTheirNeeds_L1` | Plants Need Water | 252–261 | OTHER_WORKSHEET | Which Way to Sprout? |
| `Science_2_Mod3_PlantsAndTheirNeeds_L2` | Plants Need Light | 264–267 | ASSESS_LESSON_READINESS | How Plants Use Their Parts to Live and Grow |
| `Science_2_Mod3_PlantsAndTheirNeeds_L3` | Plants Make More Plants | 278–281 | ASSESS_LESSON_READINESS | Little Seed's Journey; Making New Plants |
| `Science_2_Mod4_LivingThingsInHabitats_L1` | Habitats | 194–204 | OTHER_WORKSHEET | Plant and Animal Habitats; The Dream Home |
| `Science_2_Mod4_LivingThingsInHabitats_L2` | Forest and Grasslands | 210–213 | OTHER_WORKSHEET | Forest Habitats; rainfall / digital resources |
| `Science_2_Mod4_LivingThingsInHabitats_L3` | Water Habitats | 224–227 | OTHER_WORKSHEET | A Home For Maggie |
| `Science_2_Mod4_LivingThingsInHabitats_L4` | Hot and Cold Deserts | 236–241 | OTHER_WORKSHEET | Extreme Habitats; Mystery of the Sphinx |
| `Science_2_Mod5_EarthSurfaceChanges_L1` | Weathering and Erosion | 150–153 | OTHER_WORKSHEET | Landforms / weathering Explain blocks |
| `Science_2_Mod5_EarthSurfaceChanges_L2` | Quick Changes to Earth's Surface | 165–167 | OTHER_WORKSHEET | Volcanoes / quick changes |
| `Science_2_Mod5_EarthSurfaceChanges_L3` | Slowing Earth's Changes | 178–189 | OTHER_WORKSHEET | Beach erosion; design solutions |
| `Science_2_Mod6_EarthSurface_L1` | Describe Earth's Surface | 108–115 | OTHER_WORKSHEET | Maps Show Earth's Features |
| `Science_2_Mod6_EarthSurface_L2` | Oceans | 228–229 | OTHER_WORKSHEET | Ocean research; Oceans and Ponds |
| `Science_2_Mod6_EarthSurface_L3` | Fresh Water | 132–143 | ASSESS_LESSON_READINESS | Fresh water; glacier model; simulation |

**Golden bundle audit (all 20)** — [`tools/scraper/g2_science_golden_bundle_audit.py`](../../tools/scraper/g2_science_golden_bundle_audit.py): `procedure_html` length, `science_li_sc_day_structured` length, segment count, `body_has_paired` = substring `Paired`/`paired` in `procedure_html`, `science_li_sc_day_structured`, or `narrative_html`.

```
lesson_id	title	proc_len	struct_len	segments	body_has_paired
Science_2_Mod1_PropertiesOfMatter_L1	Describe Matter	0	294169	25	1
Science_2_Mod1_PropertiesOfMatter_L2	Solids	0	113513	5	1
Science_2_Mod1_PropertiesOfMatter_L3	Liquids and Gases	0	90700	5	1
Science_2_Mod1_PropertiesOfMatter_L4	Use Matter	0	25491	5	1
Science_2_Mod2_ChangesToMatter_L1	Put Matter Together	0	91597	52	1
Science_2_Mod2_ChangesToMatter_L2	Mixtures	0	35472	5	1
Science_2_Mod2_ChangesToMatter_L3	Temperature Changes Matter	0	284451	19	1
Science_2_Mod3_PlantsAndTheirNeeds_L1	Plants Need Water	0	328643	53	1
Science_2_Mod3_PlantsAndTheirNeeds_L2	Plants Need Light	0	3471	4	0
Science_2_Mod3_PlantsAndTheirNeeds_L3	Plants Make More Plants	0	3583	5	0
Science_2_Mod4_LivingThingsInHabitats_L1	Habitats	0	396265	53	1
Science_2_Mod4_LivingThingsInHabitats_L2	Forest and Grasslands	0	113513	5	1
Science_2_Mod4_LivingThingsInHabitats_L3	Water Habitats	0	52656	4	1
Science_2_Mod4_LivingThingsInHabitats_L4	Hot and Cold Deserts	0	50831	5	1
Science_2_Mod5_EarthSurfaceChanges_L1	Weathering and Erosion	0	102394	25	1
Science_2_Mod5_EarthSurfaceChanges_L2	Quick Changes to Earth's Surface	0	3824	5	0
Science_2_Mod5_EarthSurfaceChanges_L3	Slowing Earth's Changes	0	26599	7	1
Science_2_Mod6_EarthSurface_L1	Describe Earth's Surface	0	114139	31	1
Science_2_Mod6_EarthSurface_L2	Oceans	0	35472	5	1
Science_2_Mod6_EarthSurface_L3	Fresh Water	0	152192	11	1
```

**Observations:** Same as before: Science body is in **`science_li_sc_day_structured`** / **`science_lesson_day_segments`**, not `procedure_html`. **`body_has_paired` = 0** for Plants Need Light, Plants Make More Plants, Quick Changes: use `book_lesson_supplement.teacher_curriculum_cue` and curated headings, or extend the substring check (e.g. “read aloud”, story titles).

## 5. Explicit non-goals (policy)

- **`g2_science_book_lesson_supplement` is advisory metadata**, not a second SSOT for instructional HTML. Teacher DOCX ingest + [`g2_science_canonical_ssot.py`](../../tools/db/g2_science_canonical_ssot.py) remain authoritative per ADR-003.
- **`g2_science_book_lesson_extract`** stores **derived** workbook plain text for search and grounding; it does **not** replace `procedure_html`, `science_li_sc_day_structured`, or segment tables.
- **Calendar / AI daily drafts** remain ADR-003 Steps 2–3.

## 6. Optional next steps

- Tighten **PDF page spans** (per paired-read story, not whole lesson) using TOC or layout rules; store in new columns if needed.
- If large `*.inventory.json` files should not be versioned, add them to `.gitignore` and document regeneration.
- Extend pytest coverage on real `curriculum.db` snapshots if CI gains a checked-in minimal Science fixture.
