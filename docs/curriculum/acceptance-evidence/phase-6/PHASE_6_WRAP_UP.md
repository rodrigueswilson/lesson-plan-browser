# Phase 6 wrap-up — Navigator and semantic progression

## Result: **CLOSED** (2026-03-29)

Phase 6 (curriculum navigator) is **complete** per `docs/curriculum/PHASED_ROLLOUT_PLAN.md`: FTS-backed lesson search with highlighted snippets, semantic related-units (manual table plus adjacent-grade suggestions), Explorer UI for search and “Related units” with rationale. Automated gates were re-run at closure; see test gate files below.

**Branch naming:** Work is on `curriculum/phase-5-cross-grade-sample`. The plan-named branch **`curriculum/phase-6-navigator-semantic-links`** points at the **tip** commit that includes both the **implementation** (`feat(curriculum): Phase 6 FTS search and semantic unit links`) and the **closure documentation** commit (`docs: close Phase 6 navigator …`) in history. Pushing and merging to `master` remain normal repository policy.

## Exit criteria (plan vs actual)

| Plan criterion | Status |
|----------------|--------|
| FTS5 (or approved index) with highlighted results | Met: `lessons_fts` + `GET /api/curriculum/search`, `snippet_html` with `<mark>` |
| Cross-grade semantic links (manual + assisted) | Met: `unit_semantic_links` + `GET /api/curriculum/units/{unit_id}/semantic-links` |
| Rationale display | Met: API fields and Explorer “Related units” panel |
| Stable UX + regression tests | Met: `CurriculumExplorer.tsx`, `tests/test_curriculum_fts_and_links.py` + gate slice |
| Branch `curriculum/phase-6-navigator-semantic-links` | **Met** as branch pointer at closure commit (see note above). |

## Curator note: manual `unit_semantic_links`

There is no write API for links (YAGNI). Staff may insert rows with SQLite (after `ensure_unit_semantic_links_table()` has run once, e.g. via any curriculum API hit):

```sql
INSERT INTO unit_semantic_links (id, from_unit_id, to_unit_id, link_kind, rationale, source)
VALUES (lower(hex(randomblob(16))), 'SOURCE_UNIT_ID', 'TARGET_UNIT_ID', 'vertical', 'Short rationale text', 'manual');
```

`link_kind` and `source` are descriptive; `UNIQUE (from_unit_id, to_unit_id, link_kind)` applies. Suggested links are computed at read time and omit collisions with manual targets.

## Evidence paths

- `docs/curriculum/acceptance-evidence/phase-6/PHASE_6_EXECUTION.md`
- `docs/curriculum/acceptance-evidence/phase-6/test-gate-6-1-*.txt`, `test-gate-6-post-*.txt`
- `docs/curriculum/acceptance-evidence/phase-6/test-gate-6-close-verify_curriculum_db.txt`
- `docs/curriculum/acceptance-evidence/phase-6/test-gate-6-close-pytest-phase-deps.txt`
- `docs/curriculum/acceptance-evidence/phase-6/test-gate-6-close-lesson-browser-build.txt`
- Code: `backend/database/curriculum.py` (`ensure_lessons_fts_index`, `ensure_unit_semantic_links_table`, `search_lessons_text`, `get_unit_semantic_links`), `backend/routers/curriculum.py`, `backend/schemas/curriculum.py`, `lesson-plan-browser/frontend/src/components/CurriculumExplorer.tsx`

## Next-phase trigger

Phase 7 (expansion readiness) per `PHASED_ROLLOUT_PLAN.md` when you are ready; program-wide bulk ingestion remains behind the plan’s Phase 5 + Phase 6 decision checkpoint (both phases now documented closed).
