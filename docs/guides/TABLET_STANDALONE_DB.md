# Tablet Standalone DB: API Contract and Pitfalls

This document is the **single source of truth** for the contract that keeps the tablet app working with the local SQLite database. It avoids regressions (e.g. "No weeks available") caused by HTTP calls or unsafe path/async usage in the API layer when the app runs in standalone mode.

## When standalone mode is active

Standalone mode is active when:

- The app is built as an **Android Tauri** build, and
- `VITE_ENABLE_STANDALONE_DB=true` (set by the canonical tablet build).

In that case the app uses the **local SQLite database** at the path chosen in the Rust layer ([lesson-plan-browser/frontend/src-tauri/src/lib.rs](../../lesson-plan-browser/frontend/src-tauri/src/lib.rs)); **no backend HTTP is available**.

For build and env details, see [lesson-plan-browser/ANDROID_BUILD_AUTOMATION.md](../../lesson-plan-browser/ANDROID_BUILD_AUTOMATION.md).

## Rule for the API layer

Any method in [shared/lesson-api/src/index.ts](../../shared/lesson-api/src/index.ts) that can be called from the tablet UI while in standalone mode **must** either:

1. Implement a **local-DB path** (using `canUseLocalDb` / `queryLocalDatabase`) and **not** call `request()`, or  
2. **Return a safe default** without calling `request()` (e.g. `return { data: null }` or `return { data: [] }`).

If a tablet-used method calls `request()` in standalone mode, the fetch fails and can break the UI (e.g. "No weeks available").

## Restrictions in local-DB paths

In the standalone branch of any method:

- **Do not** call async helpers that depend on filesystem or app data path (e.g. `getLessonPlanDirectory`, `getAppDataDirPath`) unless they are required and known to be safe on Android. On tablet they can throw or hang and cause unhandled rejections.
- Prefer **DB-only or in-memory data**. For example, use `folder_name: undefined` for sort keys and let the sort logic use the year-from-`week_of` heuristic.

## Tablet-used API surface (audit)

Methods used from [shared/lesson-browser](../../shared/lesson-browser) when the app is in tablet/standalone mode, and whether they have a standalone branch or safe default:

| Method | Standalone behavior |
|--------|---------------------|
| `userApi.list` | Local DB path (`canUseLocalDb`) |
| `userApi.get` | Local DB path |
| `userApi.getRecentWeeks` | Local DB path; `folder_name: undefined` (no path APIs) |
| `planApi.list` | Local DB path |
| `scheduleApi.getSchedule` | Local DB path |
| `scheduleApi.getCurrentLesson` | Safe default: `return { data: null }` (no backend on tablet) |
| `lessonApi.getPlanDetail` | Local DB path |
| `lessonApi.getLessonSteps` | Local DB path |
| `slotApi.list` | Local DB path (used indirectly via user/plan flows) |

When adding or changing a method that the tablet UI can call, ensure it appears in this table with a local-DB path or safe default. For implementation patterns (row transformers, `if (canUseLocalDb)` structure), see [lesson-plan-browser/PHASE9_IMPLEMENTATION_GUIDE.md](../../lesson-plan-browser/PHASE9_IMPLEMENTATION_GUIDE.md).

## Testing

When you add a new column to a standalone query in [shared/lesson-api](../../shared/lesson-api), update `REQUIRED_COLUMNS_BY_TABLE` (or the app-queries list) in [tests/test_tablet_db_export.py](../../tests/test_tablet_db_export.py) so the export compatibility tests stay green.

## Troubleshooting

Do **not** duplicate the full troubleshooting steps here. For "No weeks available", logcat (`adb logcat | findstr /i "LP DB"`), build, and push instructions, see:

- **[lesson-plan-browser/ANDROID_BUILD_AUTOMATION.md](../../lesson-plan-browser/ANDROID_BUILD_AUTOMATION.md)** — build, push, and troubleshooting section.

If you see `[LP] [API] WARNING: request() called in standalone mode` in logcat, a method used by the tablet is calling HTTP in standalone; add a local-DB branch or safe default and see this doc.

## Settings > Database (PC + FastAPI only)

The **Database** tab ([frontend/src/components/DatabaseSettings.tsx](../../frontend/src/components/DatabaseSettings.tsx), also loaded from the unified lesson-plan-browser app) talks **directly** to the FastAPI server (e.g. `http://localhost:8000/api/...`) for maintenance stats, `GET /api/users/{id}/plans/by-week` (with `?sort=school|recent`), per-plan JSON export, `POST .../plans/restore-from-export`, per-plan delete, full-database backup, and duplicate resolution. It does **not** go through [shared/lesson-api/src/index.ts](../../shared/lesson-api/src/index.ts) and has **no** `queryLocalDatabase` / standalone branch.

In **tablet standalone mode** there is no local FastAPI process, so those `fetch` calls will not keep the database functional on the device by themselves. Tablet data integrity still depends on the **lesson-api** contract in this document (local SQL paths and export column compatibility in [tests/test_tablet_db_export.py](../../tests/test_tablet_db_export.py)). If teachers need the same “versions by week / backup / delete” workflows on standalone Android, a future change would need either local SQL in lesson-api (mirroring the backend routes) or to hide/disable the Database tab when `canUseLocalDb` is true without a reachable API base URL.

## Related documentation

- [lesson-plan-browser/ANDROID_BUILD_AUTOMATION.md](../../lesson-plan-browser/ANDROID_BUILD_AUTOMATION.md) — canonical build, env, push, troubleshooting  
- [docs/LESSON_PLAN_BROWSER_ARCHITECTURE.md](../LESSON_PLAN_BROWSER_ARCHITECTURE.md) — high-level tablet/offline architecture  
- [lesson-plan-browser/PHASE9_IMPLEMENTATION_GUIDE.md](../../lesson-plan-browser/PHASE9_IMPLEMENTATION_GUIDE.md) — implementation patterns for standalone API methods  
- [docs/roadmap/design/DATABASE_ARCHITECTURE_AND_SYNC.md](../roadmap/design/DATABASE_ARCHITECTURE_AND_SYNC.md) — high-level DB/sync context (optional)
