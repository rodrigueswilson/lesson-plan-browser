# Local-first document links — open backlog

**Status:** **OPEN** — users still report that Explorer hyperlinks and/or Source URL behavior open **Google Drive** instead of a local export, even when curriculum files exist under `reference_docs/scraped` or `CURRICULUM_LOCAL_FILES_ROOT`.

This note records the problem, what has been implemented, likely remaining causes, and a **revisit checklist** to execute at the **end of the curriculum navigator implementation plan** (after Phase 4.2 and integration testing), not as ad-hoc debugging during extraction-only phases.

## User-visible symptom

- Clicking in-lesson links or Source URL still lands on **docs.google.com** / Drive in some environments.
- Expectation: open a **same-origin** `/api/curriculum/resources/google-id/{id}/file` response (download or in-browser preview) when a matching file is on disk.

## Implemented behavior (reference)

Documented in [LOCAL_SOURCE_FILES.md](LOCAL_SOURCE_FILES.md). Code touchpoints:

| Area | Location |
|------|----------|
| Discovery (flat id, `*_{id8}.*`, `originals/*.json`, `*.docs-api.json`, sidecar docx/pdf/html/md, `_by_tab`) | [backend/database/curriculum.py](../../backend/database/curriculum.py) — `discover_local_path_for_google_doc`, `curriculum_export_search_roots`, `path_is_under_export_roots` |
| Resolve + file route | [backend/services/curriculum_resource_resolve.py](../../backend/services/curriculum_resource_resolve.py), [backend/routers/curriculum.py](../../backend/routers/curriculum.py) |
| Source Metadata link | [lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx](../../lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx) — `SourceUrlOpenRow` |
| In-lesson HTML links | Same file — `CurriculumRichHtml` intercepts `docs.google.com/document` anchors and calls `/resolve` |

Automated checks: [tests/test_curriculum_resource_resolve.py](../../tests/test_curriculum_resource_resolve.py).

## Why the issue can persist (hypotheses for revisit)

1. **Runtime wiring:** Frontend calls **relative** `/api/...` — if the Tauri shell or dev proxy does not forward to the FastAPI process, `fetch` fails and the UI falls back to the original Drive `href`.
2. **Curriculum API unavailable:** `require_curriculum_schema` or other **503** responses on curriculum routes cause silent fallback to Drive in the catch path.
3. **No servable file:** Discovery returns nothing when only a `.docs-api.json` exists with **no** sibling `.docx`/`.pdf`/`.html`, or when the on-disk **document id** does not match the link id (tabs, copies, shortened URLs).
4. **Link shape:** Links that are not `docs.google.com/document/d/...` (redirectors, `drive.google.com` file links, OAuth interstitials) are not intercepted.
5. **Browser vs Word:** Even when `/file` succeeds, **.docx** often **downloads** rather than launching Microsoft Word; users may perceive that as “still not local.” True “open in Word” likely needs a **Tauri** command (shell / opener) — called out in LOCAL_SOURCE_FILES.md.
6. **Caching / stale bundle:** Old frontend without `CurriculumRichHtml` intercept or old backend without expanded discovery.

## Revisit checklist (run at end of navigator implementation)

Execute when Phase 4.2 (Explorer UI) is feature-complete and can be tested end-to-end on a real desktop build:

1. **Network:** From the running app, confirm `GET /api/curriculum/resources/google-id/<known_id>/resolve` returns `"source":"local"` and a `/file` URL for a doc that exists under `reference_docs/scraped` (use browser devtools or Tauri webview network log).
2. **Logging:** Add optional client-side log when `/resolve` fails (status + body) and optional server log when discovery returns `None` for a requested id (behind DEBUG if needed).
3. **Ingest-time index (optional hardening):** Persist `google_doc_id → absolute_path` at ingest into SQLite so discovery does not depend on full-tree scans or heuristics.
4. **Tauri:** If product requirement is “open in Word,” implement download-to-temp + OS default application via Tauri opener; keep web behavior as download/preview.
5. **Documentation:** Update [LOCAL_SOURCE_FILES.md](LOCAL_SOURCE_FILES.md) operator steps once the above is verified on the supported install path.

## Related backlog

- [KNOWN_UI_LIMITS.md](KNOWN_UI_LIMITS.md) — in-cell title enrichment (separate issue).
- [MATH_LESSON_PORTAL_AND_TEACHER_GUIDE_UX.md](MATH_LESSON_PORTAL_AND_TEACHER_GUIDE_UX.md) — Math: curriculum **website** lesson link vs. **teacher guide PDF**; do not conflate with Google Doc local-first resolution.
