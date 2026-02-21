# Database Archive Log

This document tracks redundant or conflicting database files that have been moved to the archives for safety and clarity.

## 2026-01-05 19:17

| Original Path | Archive Name | Reason |
|---------------|--------------|--------|
| `data/lesson_plans.db` | `lesson_plans_root_20260105.db` | Redundant (real data is in `lesson_planner.db`) |
| `backend/lesson_plans.db` | `lesson_plans_backend_20260105.db` | Redundant / Potential conflict |
| `backend/data/lesson_planner.db` | `lesson_planner_backend_data_20260105.db` | Accidental copy creating localized data |

## 2026-01-05 19:20 - Maintenance Run

A full database maintenance was performed via `db_maintenance.py`:
- **Backup**: Created `lesson_planner_backup_20260105_191950.db`.
- **Cleanup**: 9 'password' users deleted.
- **Pruning**: 21 redundant completed plans and 10 failed plans removed.
- **Result**: Database is consolidated and contains only active users (2) and unique weekly plans (25).

**Note**: All application logic has been consolidated to use the single source of truth at `d:/LP/data/lesson_planner.db`.
