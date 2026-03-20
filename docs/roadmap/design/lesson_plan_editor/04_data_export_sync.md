# Lesson Plan Editor – Data, export, and sync

**Status:** Outline  
**SSOT for sync schema:** [DATABASE_ARCHITECTURE_AND_SYNC.md](../DATABASE_ARCHITECTURE_AND_SYNC.md)

## 1. Persistence

- **Canonical store:** `lesson_json` on the weekly plan (and any slot-level representation the codebase already uses—see [backend/routers/plans.py](../../../../backend/routers/plans.py) and database layer).
- **After save:** Run the same **validation** used after LLM generation so invalid states never reach the DB.

## 2. Versioning and audit (TBD)

Document the chosen approach:

- Revision id or monotonic version per plan.
- **Provenance:** `manual` vs `assistant` (and optional model id, timestamp, user id).
- Whether to store **assistant chat** for support vs privacy-minimal metadata only.

## 3. DOCX and derived artifacts

- **Weekly DOCX** and **objectives** (or other exports) should be **regenerated from saved `lesson_json`** (or explicitly marked stale until user triggers regen—product decision).
- Renderer touchpoints: [tools/docx_renderer/](../../../../tools/docx_renderer/) (do not duplicate renderer logic in this doc; link only).

## 4. Tablet and multi-device

- After persist, sync layer must expose the **updated** plan to the tablet app (Supabase/SQLite per current architecture).
- **Conflicts:** If PC and tablet can both edit, define policy (last-write-wins, prompt, or lock) consistent with [DATABASE_ARCHITECTURE_AND_SYNC.md](../DATABASE_ARCHITECTURE_AND_SYNC.md).

## 5. Checklist for implementation spec

- [ ] Exact API contract for save (payload shape).
- [ ] Validator entry point reused from generation path.
- [ ] Export job: synchronous vs background vs on-download.
- [ ] Sync notification or pull model for tablet.
