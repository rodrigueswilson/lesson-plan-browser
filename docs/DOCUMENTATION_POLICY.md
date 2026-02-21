# Documentation Policy

This policy defines how project documentation is organized and maintained.

---

## Current system (implemented features)

- **Status:** Implemented features and phases are listed in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md). That file is the single source of truth for "what is done."
- **Reference:** Architecture, guides, training, and examples under [docs/](.) (except `roadmap/` and `archive/`) describe the current system. The main [README.md](../README.md) at repo root links to key docs.

---

## Roadmap (planned work)

- **Location:** All planned modules and features are indexed in [roadmap/README.md](roadmap/README.md).
- **Design docs:** Detailed design and architecture for planned work live under [roadmap/design/](roadmap/design/) (formerly `expansionNov/`). Links and images in those docs are preserved; internal links use relative paths within that folder.
- **Planning docs:** Documents in [planning/](planning/) may describe either implemented work (e.g. TABLET_TAB_PLAN) or remaining work (e.g. FEATURE_ENHANCEMENT_PLAN remaining items). Each has a status note at the top.

---

## Archive

- **Location:** Archived documentation lives under [archive/](archive/) only. Do not create a second archive elsewhere.
- **Criteria for archiving:** Move a doc to archive when it is (1) **superseded** by another doc, (2) **obsolete** (no longer reflects code or process), (3) a **completed one-off** (e.g. session summaries, PHASE_X_COMPLETE logs, bug-fix logs that are historical only), or (4) **explicitly deprecated**.
- **Do not archive:** IMPLEMENTATION_STATUS, active roadmap/planning docs, current guides, training, deployment runbooks, or ADRs (mark superseded and link to new ADR instead).
- **Process:** When archiving a doc: (1) Add a short notice at the top (e.g. "Archived on YYYY-MM-DD. Reason: superseded by X. See [link] for current information."); (2) Move the file to the appropriate subdir under `archive/`; (3) Update [archive/ROOT_ARCHIVE_INDEX.md](archive/ROOT_ARCHIVE_INDEX.md) (or archive index) with original path, new path, date, reason; (4) Fix any in-repo links that pointed to the old path.

---

## Architecture decision records (ADRs)

- **Location:** [decisions/](decisions/).
- **Rule:** Do not delete ADRs. To supersede a decision, add a new ADR and mark the old one as superseded with a link to the new one.
