# Math: lesson portal link vs. teacher guide (UX and future extraction)

**Status:** **Requirements / backlog** — to be implemented and validated when Math navigator and Explorer work are consolidated with the other phased curriculum tasks (see [PHASED_ROLLOUT_PLAN.md](PHASED_ROLLOUT_PLAN.md), especially after Phase 3 Math corpus UI and cross-phase integration).

## Context in the source materials

In Grade 3 Math (and similar district layouts), each **lesson** is often associated with **two different kinds of links**:

1. **Lesson title link (curriculum website)**  
   - The visible lesson name links to the **live curriculum portal** (e.g. district IM / `ilclassroom.com` lesson or resource URLs).  
   - Teachers use this **during instruction** to jump straight to the official lesson experience on the web.  
   - **We do not intend to scrape that website** as part of the core curriculum DB pipeline; the product need is **faithful deep-linking** in the UI (open the real URL in the browser / webview).

2. **Teacher guide link (PDF)**  
   - A **separate** link (often adjacent in the pacing or unit table) points to a **teacher guide** document, commonly a **PDF** (detailed procedures, commentary, and assets).  
   - These guides are **high value** for planning; many are **already downloaded** under the scraper tree (e.g. `reference_docs/scraped/...`) as part of `tools/scraper` workflows.  
   - The UI should surface the teacher guide in a **prominent, predictable place** (e.g. dedicated control next to the lesson, not buried only inside long HTML), and prefer **local file open** when a copy exists on disk, with fallback to the original URL.

## Product rules (summary)

| Asset | Behavior |
|-------|----------|
| Lesson title → portal URL | Always open the **external** HTTPS URL as stored or normalized; do not replace with local Google Doc resolution. |
| Teacher guide PDF | Prefer **local** copy when discoverable (same patterns as [LOCAL_SOURCE_FILES.md](LOCAL_SOURCE_FILES.md) where applicable); otherwise open/download from URL; **prominent** placement in lesson detail. |

## Interaction with local-first Google Doc resolution

The Explorer’s `CurriculumRichHtml` logic that resolves **`docs.google.com/document`** links to local exports must **not** change behavior for **non-Google** lesson portal URLs. Any future heuristics should treat **host + path** explicitly so ilclassroom (and similar) links remain **pass-through**.

Document overlap with [LOCAL_FIRST_LINKS_BACKLOG.md](LOCAL_FIRST_LINKS_BACKLOG.md): that backlog focuses on Drive vs. local **Google Doc** exports; **this** document focuses on **two-link Math UX** (portal vs. PDF guide).

## Future work (post–navigator phases)

After the navigator and Math lesson views are stable:

1. **Structured extraction from teacher guides**  
   - Parse PDF (or source DOCX where available) into structured fields aligned with lesson schema: objectives, activity sequence, suggested timing, assessments, vocabulary, etc.  
   - Use that structure to **support generated lesson plans** and **pacing** suggestions, always with human review and district policy gates.

2. **Data model**  
   - Explicit association: `lesson_id` ↔ `portal_url` ↔ `teacher_guide_asset_id` (file path or stored blob reference) so the UI does not rely only on adjacent links in HTML.

3. **Acceptance**  
   - Teacher can open portal in one click from the lesson header.  
   - Teacher guide is one click away in a labeled area (e.g. “Teacher guide (PDF)”).  
   - No regression: portal links are not swallowed by Google-only resolvers.

## Revisit trigger

Schedule design and implementation work for this document **together with** the end-of-phase integration pass for Math + Explorer (after Phase 3 Math UI hooks and Phase 4+ navigation are far enough along to test real lesson rows). Track alongside the checklist in [LOCAL_FIRST_LINKS_BACKLOG.md](LOCAL_FIRST_LINKS_BACKLOG.md) where both affect link behavior in the same views.
