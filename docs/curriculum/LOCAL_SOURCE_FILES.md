# Local curriculum source files (Google Doc exports)

The Explorer **Source URL** row and in-lesson links that carry a Google Doc id can open a **local export** instead of the browser tab to Google Drive when files are placed on disk and the backend is configured.

**If links still open Drive in your environment**, treat that as a **known open issue** until the navigator phase is integration-tested. See **[LOCAL_FIRST_LINKS_BACKLOG.md](LOCAL_FIRST_LINKS_BACKLOG.md)** (symptoms, hypotheses, revisit checklist). The phased plan calls for revisiting this at **end of Phase 4.2** — [PHASED_ROLLOUT_PLAN.md](PHASED_ROLLOUT_PLAN.md) § *Revisit: local-first document links*.

## Search roots (where the API looks)

`CurriculumDatabase.curriculum_export_search_roots()` ([backend/database/curriculum.py](backend/database/curriculum.py)) builds the allow-list for **discovery** and **serving**:

1. **`CURRICULUM_LOCAL_FILES_ROOT`** (optional env) — operator drop folder.
2. **`<repo>/reference_docs/scraped`** when that directory exists — default output of `tools/scraper/main.py` and related export scripts.

Files must stay **under** at least one of these roots to be streamed by `/file`.

## File naming (discovery order)

The id must match **`source_doc_id`** and/or the URL segment `/document/d/<id>/`.

| Layout | Pattern | Origin |
|--------|---------|--------|
| Flat by full id | `{google_doc_id}.docx` (also `.pdf`, `.html`, `.md`) | Simple export or `CURRICULUM_LOCAL_FILES_ROOT` |
| Export batch | `*{google_doc_id[:8]}.docx` anywhere under a search root (recursive) | [tools/scraper/export_doc_ids_to_docx.py](tools/scraper/export_doc_ids_to_docx.py) (`{stem}_{id[:8]}.docx`) |
| Scraper tree | `**/originals/{title}.json` or `**/*.docs-api.json` with `"documentId": "<id>"` and sibling `{base}.docx` / `.pdf` / `.html` / `.md`, or `{base}_by_tab/*.docx` (`{base}` is the filename without `.json` / `.docs-api.json`) | [tools/scraper/main.py](tools/scraper/main.py), [export_doc_ids_to_docx.py](tools/scraper/export_doc_ids_to_docx.py) |

Discovery is implemented in `CurriculumDatabase.discover_local_path_for_google_doc`. Resolution and streaming:

- `GET /api/curriculum/resources/google-id/{id}/resolve` — `{ "url", "source" }` with `source` of `local`, `remote`, or `remote_inferred`
- `GET /api/curriculum/resources/google-id/{id}/file` — serves the file when local

A row in the `resources` table is **not** required if a matching file is found on disk ([backend/services/curriculum_resource_resolve.py](backend/services/curriculum_resource_resolve.py)).

## Browser vs desktop behavior

- **WebView / browser:** Opening the local route typically **downloads** `.docx` or opens **PDF** in-tab, depending on the browser and `Content-Type`. Browsers cannot jump straight to `file://` paths from `http://localhost` for security reasons.
- **Tauri (future):** For one-click “open in Microsoft Word,” add a desktop command that writes or references a temp file and uses the OS default application (Tauri shell / opener). The web flow above remains the portable baseline.

## Related UI

- Explorer Source Metadata uses `SourceUrlOpenRow` in [lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx](lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx): it resolves on click and shows a small **Opens: …** badge when the resolve endpoint succeeds.
- `CurriculumRichHtml` intercepts **any** `docs.google.com/document` link (not only anchors with `data-resource-id`), parses the doc id from `href`, and runs the same `/resolve` flow so older ingest HTML still opens local exports when found.

## See also

- Known UI backlog for in-cell titles: [KNOWN_UI_LIMITS.md](KNOWN_UI_LIMITS.md)
