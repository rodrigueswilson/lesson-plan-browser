# Known curriculum UI limits (backlog)

## In-cell section titles (ELA detailed lesson / matrix HTML)

Rich labels such as **Learning Procedures**, **Daily Instructional Task**, and **Teacher Notes** are partially restored in the Explorer using display-time heuristics in `lesson-plan-browser/frontend/src/utils/enrichRichHtmlTitles.ts` (bold vs italic Teacher Note, prefix-through-colon wrapping, `<p>` and `<li>` handling, Unicode space normalization).

**Remaining gaps** (deferred to a later development phase):

- Mixed or nested HTML from DOCX ingest (e.g. nested lists, wrappers other than `<p>` / `<li>`).
- Edge-case spacing or punctuation from Word exports that do not match title patterns.
- A more durable approach may combine **ingest-time** structure (explicit section nodes or HTML classes from the parser) with lighter **display-time** styling.

Revisit when curriculum ingest and schema work prioritizes presentation fidelity over heuristic enrichment.

## Local-first document links (Drive still opens)

If lesson links or Source URL still open **Google Drive** despite local exports, see **[LOCAL_FIRST_LINKS_BACKLOG.md](LOCAL_FIRST_LINKS_BACKLOG.md)**. Revisit is scheduled with the **end of the phased navigator plan** (Phase 4.2), not as part of the in-cell title heuristic work above.

## Math: two links per lesson (portal vs. teacher guide)

Lesson **title → curriculum website** must stay a direct pass-through (not scraped). **Teacher guide PDF** should be prominent and local when available; future structured extraction from PDFs may feed pacing and generated plans. See **[MATH_LESSON_PORTAL_AND_TEACHER_GUIDE_UX.md](MATH_LESSON_PORTAL_AND_TEACHER_GUIDE_UX.md)**.
