## Bilingual Weekly Plan Builder — App Overview

### Definition
An app that ingests weekly `.docx` lesson plans from primary teachers, auto-selects configured subject tables, transforms them into WIDA‑enhanced bilingual plans, and compiles a single `.docx` output that conforms to the district template.

### Short Description
- Weekly workflow with zero typing: select files/subjects once, then one-click compile every week.
- Robust table detection across varied `.docx` formats (header+main pairs, weekly grids, daily blocks).
- WIDA‑aligned bilingual transformation using local strategy packs and optional LLM integration.
- Output normalized to `input/Lesson Plan Template SY'25-26.docx`.
- Manual weekly run by the teacher; not auto‑scheduled.

## Problem Framing

### Users & Jobs-To-Be-Done
- Teacher (bilingual): Turn multiple primary lesson plans into one bilingual weekly plan fast, with no re-selection.
- Admin/Coach (optional): Ensure consistency/fidelity to WIDA, export/share.

### Inputs (weekly)
- `.docx` files in `d:/LP/input/`, filenames include teacher names:
  - Davies → Math
  - Lang → ELA
  - Savoca → ELA, ELA/SS, Science, Math
  - Piret → subjects configurable (confirm per profile)
- Strategy/WIDA data:
  - `strategies_pack_v2/_index.json`
  - `wida_framework_reference.json`
  - `wida_strategy_enhancements.json`

### Profiles, Dynamic Paths, and Week Discovery
- Multiple profiles with distinct input roots are supported (e.g.,
  - User: `F:/rodri/Documents/OneDrive/AS/Lesson Plan`
  - Spouse: `F:/rodri/Documents/OneDrive/AS/Daniela LP`
)
- ISO‑week subfolders are discovered automatically under an input root using the pattern `YY WNN` (e.g., `25 W38`, `25 W39`).
- On each run, the app selects the most recent ISO‑week folder under the chosen profile’s root. If none exist, it falls back to the root itself.
- Output management:
  - Default output folder: the current (or next) ISO‑week folder (e.g., `25 W39`).
  - If the expected next week folder/file does not exist, the app creates the folder and writes the compiled output there.
  - Suggested default filename: `User name - 25 W39 - Week of YYYY-MM-DD.docx`

Pseudo‑logic for week discovery and output placement:
```text
1) Given profile.input_root, list subfolders matching ^\d{2} W\d{2}$
2) Sort by (YY, ISO week) ascending; pick latest as currentWeek
3) Derive nextWeek using ISO week increment with year rollover (W52→W01)
4) Use currentWeek for compiling last week, or nextWeek when generating the upcoming week by default
5) Ensure output directory exists (create if missing), then write output filename
```

### Outputs (weekly)
- One compiled `.docx` that mirrors the district template, containing only selected subjects per teacher.

### Core Constraints
- Table structures may vary (merged cells, synonyms for headings, different day/period formats).
- Preserve heading info (teacher, grade, subject, week).
- No student Personally Identifiable Information (PII) stored in plans; optional LLM usage gated by user-provided API key.

### Prompt alignment and intentional deviation
- Alignment: Follows two‑phase strategy selection, generates all three objectives, applies proficiency‑tier scaffolds, limits to 2–3 strategies/lesson, and cites JSON evidence.
- Intentional deviation: The prompt says “Output table mirrors input structure exactly.” This app normalizes outputs to the district template `input/Lesson Plan Template SY'25-26.docx` regardless of input variation to ensure consistency and save time.

## Selector Concept (“Weekly Intake Profile”)

### Purpose
Record, once, which files and subject tables to use per teacher so the weekly run needs no re-selection.

### Contents
- Expected files: filename patterns by teacher (e.g., “Davies”, “Lang”, “Savoca”, “Piret”).
- Subject filters per teacher (e.g., Davies→Math; Savoca→ELA/SS, Science, Math).
- Detection rules:
  - Pair header+main tables.
  - Subject extraction from header or inference from main table.
  - Day/period detection (Mon–Fri, M/T/W/Th/F, dates, or P1…; time ranges like 8:15–9:05).
  - Row-label synonym map (Objective, Anticipatory Set, Tailored Instruction, Misconception, Assessment, Homework).
- Teacher-specific overrides for idiosyncratic labels (e.g., Piret’s custom rows).
- Editable at any time; profile updates apply to future weeks.
- Multiple profiles supported (different teacher cohorts per user).

### Profile Setup UI (Selectable Inputs)
- Input root picker: choose a folder (e.g., `F:/rodri/Documents/OneDrive/AS/Lesson Plan` or `F:/rodri/Documents/OneDrive/AS/Daniela LP`). Stored per profile.
- Folder naming pattern: app expects ISO-week subfolders named `YY WNN` (e.g., `25 W38`). It validates and warns if the pattern isn’t found but does not rename existing folders.
- Teacher mapping: add teachers by name pattern (e.g., `Davies`, `Lang`, `Savoca`, `Piret`) and select subjects per teacher (multi-select: `ELA`, `ELA/SS`, `Science`, `Math`, etc.). Editable anytime.
- Subject synonyms: optional per-teacher overrides (e.g., map `ELA-SS`, `ELA & SS` → `ELA/SS`).
- Persistence: all selections saved to the profile; weekly runs reuse them automatically.

Example profile config (conceptual):
```json
{
  "profile_name": "2025-26-default",
  "input_root": "F:/rodri/Documents/OneDrive/AS/Lesson Plan",
  "teachers": {
    "Davies": { "file_pattern": "Davies", "subjects": ["Math"] },
    "Lang":   { "file_pattern": "Lang",   "subjects": ["ELA"] },
    "Savoca": { "file_pattern": "Savoca", "subjects": ["ELA","ELA/SS","Science","Math"] },
    "Piret":  { "file_pattern": "Piret",  "subjects": ["ELA","ELA/SS","Science","Math"] }
  },
  "subject_synonyms": { "ELA/SS": ["ELA-SS","ELA & SS","ELA Social Studies","ELA / SS"] }
}
```

## v1 Scope (Must-Haves)
- Load `.docx` files and auto-detect/pair tables (header+main, weekly grid, daily block).
- Apply “Weekly Intake Profile” to select only the configured subject tables per teacher.
- Extract normalized fields from varied headings/synonyms.
- Transform to bilingual WIDA‑enhanced content:
  - Student “I will…” goal
  - WIDA Bilingual Language Objective
  - ELL supports with 2–3 strategies and proficiency scaffolds (Levels 1–2, 3–4, 5–6)
  - At least one selected strategy must explicitly align to the chosen Key Language Use (KLU)
  - Family Connection activity included where applicable
- Render output to the district template and compile a single weekly `.docx`.
- Simple UI to manage profiles and run weekly compile.

## Non-Functional & Success Criteria
- Speed: p95 compile < 3s after files are loaded; weekly run < 10 minutes total.
- Zero student PII; plans stored locally unless exported/shared.
- Works offline after first load; sync when online.
- Accessibility: WCAG 2.2 AA (keyboard/focus/landmarks).
- Reliability: Detect/fail gracefully on unmatched tables; quick one-time remap saves to the profile.

## Technology Stack

### Platform & App Style
- Desktop wrapper: Tauri (small bundle, native integration)
- Frontend: React + TypeScript (lean), i18next (EN/PT)
- Backend: Python FastAPI over 127.0.0.1 (HTTP + SSE) — DOCX processing
- Packaging: PyInstaller one-file backend; Pydantic schemas (JSON Schema to client)
- Storage: SQLite (local-first); OS keychain for secrets (LLM keys, if used)
- Document processing: `python-docx` and `docxcompose`, district `.dotx` template
- LLM (optional): OpenAI/Anthropic via API key (opt-in, privacy-scrubbed)
- Updates: In-app “update available” notice → opens release page (no auto-update)
- Testing: Pytest (unit/integration), Playwright (E2E), axe for accessibility
- CI: GitHub Actions (lint, type-check, tests, SAST/secret scan)
- Diagrams-as-code: Mermaid (kept in repo with code)

## Domain Model (High-Level)

### Core Entities
- TeacherFile (discovered weekly, matched by pattern)
- WeeklyIntakeProfile (per school year; expected files, subject filters, detection rules)
- LessonTable (paired header+main or normalized weekly/daily block)
- Plan (bilingual output per lesson/day)
- Strategy & WIDAReferences (read-only catalogs)

### Data Lifecycle
- Ingest `.docx` → Detect & Select tables (profile) → Extract fields → Transform (WIDA/strategies/LLM) → Render to template → Compile weekly `.docx` → Archive/export.

## Architecture

### Style
- Well‑modularized monolith (v1):
  - Modules: `ingest-docx`, `selector`, `extract-normalize`, `wida-selection`, `objective-gen`, `render-docx`, `export`, `profiles`, `audit`.
- Async only for heavy export/merging; core flow remains synchronous.

### Selection/Detection Highlights
- Header detection keys: Name, Grade, Homeroom, Subject, Week of.
- Day detection: MONDAY…FRIDAY, Mon…Fri, M/T/W/Th/F, date headers, or period/time formats.
- Subject normalization:
  - ELA/SS variants: ELA-SS, ELA & SS, ELA Social Studies, ELA / SS.
- Row-label synonyms (teacher‑overridable):
  - Objective; Anticipatory Set (Do Now/Hook/Warm-up); Tailored Instruction (Differentiation/ELL Support/Modifications/Accommodations); Misconception (Common Errors); Assessment (Exit Ticket/CFU); Homework (HW/Assignment).

## Implementation Standards (Finalized)

- DOCX-only (v1): Inputs and outputs are strictly `.docx`. No PDF code or UI.

- Template conventions
  - Authoritative template: `input/Lesson Plan Template SY'25-26.docx`.
  - Header is static ("Ann Street School", "Lesson Plan SY’ 25-26"); do not modify it.
  - Dynamic fields (teacher, week, grade, subject, period, etc.) are populated only in body tables.
  - Body bookmarks (if used) follow UPPERCASE_UNDERSCORE naming: `TEACHER_NAME`, `WEEK_OF`, `GRADE_LEVEL`, `SUBJECT`.
  - Optional body bookmarks: `SCHOOL_YEAR`, `WEEK_DATES`, `HOMEROOM`, `PERIOD`, `TEACHER_GRADE`, `SUBJECT_PERIOD`.
  - Body processing order: Bookmarks preferred; fallback to careful run-level text replacement only when bookmarks absent.

- Numbering preservation
  - Strategy: Overwrite the entire numbering part from the template on every run (no merge).
  - Cache: Monitor template file modification time; refresh cached numbering when the template changes.
  - Fallback: Recreate a basic district-appropriate list style if overwrite fails.

- Overflow and continuation
  - Capacity heuristic: Use calibrated capacity (~70% of raw estimate based on font size/line spacing/cell size).
  - Truncation: Prefer sentence-boundary truncation; never truncate before ~70% of capacity.
  - Continuation copy: small "...(continued below)"; medium "...(see details at end)"; large "...(expanded version in appendix)".
  - Overflow placement: appendix/end-of-document when needed; include an "Additional Details" header.

- SSE streaming (progress UI)
  - Backend: `text/event-stream` with no-cache headers, 50ms delay between messages, initial "connected" and final "complete" events.
  - Frontend: Heartbeat every 10s; connection timeout 30s; up to 3 reconnect attempts with 2s delay; batch process messages to avoid UI jank.

## Proficiency Range Handling (Explicit and Exemplified)

- Requirement: before generation, the user selects a WIDA proficiency range for the class (or uses a profile default). The app then applies level‑appropriate scaffolds from `wida_strategy_enhancements.json`.

- Examples by level band (template snippets):
  - Levels 1–2
    - Student goal: "I will label [terms] using a word bank on a diagram."
    - WIDA objective supports: visual supports, L1 bridges, gesture responses.
    - Frames (PT/EN): PT "Isso é ___" / EN "This is ___".
    - Assessment: non‑verbal demos, picture identification.
  - Levels 3–4
    - Student goal: "I will describe [topic] using sentence frames in 2–3 sentences."
    - WIDA objective supports: sentence frames, graphic organizers, strategic L1 use.
    - Frames (PT/EN): PT "A conexão é ___" / EN "The connection is ___".
    - Assessment: structured responses using frames; organizer completion.
  - Levels 5–6
    - Student goal: "I will explain [idea] using an organizer in a short paragraph."
    - WIDA objective supports: academic language models, discourse markers.
    - Frames (PT/EN): PT "Esta análise revela ___" / EN "This analysis reveals ___".
    - Assessment: academic discourse; extended responses with disciplinary features.

- KLU linkage: ensure at least one strategy and the objective explicitly reference the chosen Key Language Use (Narrate/Inform/Explain/Argue).

- Family Connection: provide a short bilingual home activity aligned to the proficiency band (e.g., L1 interview + English labels at 1–2; bilingual summary at 3–4; academic reflection at 5–6).

## Key Language Use (KLU) Templates (with PT/EN frames)

- Narrate (story, sequence, recount)
  - Student goal: "I will tell about [event] using sequence words and a visual."
  - Frames:
    - PT: "Primeiro ___, depois ___, no fim ___"  | EN: "First ___, then ___, finally ___"
  - Supports by level:
    - 1–2: picture sequence + L1 retell → English labels
    - 3–4: sentence frames for sequence and time words
    - 5–6: discourse markers and elaboration (because, therefore)

- Inform (describe, identify, report)
  - Student goal: "I will describe [topic] using a word bank and a chart."
  - Frames:
    - PT: "[Termo] significa ___"  | EN: "[Term] means ___"
  - Supports by level:
    - 1–2: labeled diagram with bilingual word bank
    - 3–4: compare/contrast chart with framed sentences
    - 5–6: precise definitions and examples with register notes

- Explain (cause/effect, process, reasoning)
  - Student goal: "I will explain [idea] using an organizer and evidence."
  - Frames:
    - PT: "Isso acontece porque ___"  | EN: "This happens because ___"
  - Supports by level:
    - 1–2: picture-based cause/effect pairs with L1 bridges
    - 3–4: sentence frames for cause/effect and examples
    - 5–6: multi-step explanation with discourse markers (consequently, therefore)

- Argue (claim, evidence, justification)
  - Student goal: "I will argue [claim] using evidence and a connector."
  - Frames:
    - PT: "Eu defendo que ___ porque ___"  | EN: "I claim that ___ because ___"
  - Supports by level:
    - 1–2: choose a claim card; match picture evidence; L1 talk → EN label
    - 3–4: sentence frames for claim/evidence/reason
    - 5–6: counterclaim and rebuttal with academic markers

## Open Questions
- Confirm Ms. Piret’s subjects to extract (default: ELA, ELA/SS, Science, Math—adjust as needed).
- Any additional teachers this year needing unique patterns?
- Preferred export naming convention (e.g., `Bilingual Plans - Week of YYYY-MM-DD.docx`)?

## Next Steps
- Configure the initial “2025–26” Weekly Intake Profile with teacher→subjects and synonyms (including Piret).
- Dry run on last week’s files; capture any remaps and save to profile.
- Lock in WIDA/strategy pack versions and test LLM-assisted transformations (optional).
- Finalize template styling and export checks.


