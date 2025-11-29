# Android Migration Plan: Bilingual Lesson Planner

## Overview

This directory contains the complete migration plan for deploying the Bilingual Lesson Planner on Android tablets using a **Python Sidecar architecture**.

## Key Architecture Decision

**Python Sidecar Pattern** - Maximizes code reuse by keeping all business logic in Python while Rust handles SQLite execution via IPC.

```
React UI → Rust Bridge → Python Sidecar → Supabase
                ↓
           SQLite (local)
```

## Document Index

| File | Description |
|------|-------------|
| `PLAN_UPDATES.md` | **NEW:** Summary of recent plan improvements |
| `01_ENVIRONMENT_SETUP.md` | Prerequisites, Rust targets, Android SDK setup |
| `02_RUST_IMPLEMENTATION.md` | IPC bridge, SQL commands (using rusqlite), main.rs changes |
| `03_PYTHON_ADAPTATION.md` | Sidecar entry point, IPC database adapter |
| `04_CONFIGURATION.md` | Cargo.toml, tauri.conf.json updates (v2.0 format) |
| `05_BUILD_DEPLOY.md` | Build commands, APK generation, testing |
| `06_CHECKLIST.md` | Step-by-step implementation checklist (includes Phase 0) |

## Quick Start

1. **Read `PLAN_UPDATES.md`** - Review recent improvements and changes
2. **Phase 0:** Test minimal IPC on desktop (see `06_CHECKLIST.md`)
3. Read `01_ENVIRONMENT_SETUP.md` - Set up Android development environment
4. Implement Rust changes from `02_RUST_IMPLEMENTATION.md` (using rusqlite)
5. Adapt Python code per `03_PYTHON_ADAPTATION.md` (critical methods first)
6. Update configs from `04_CONFIGURATION.md` (v2.0 format)
7. Build and deploy using `05_BUILD_DEPLOY.md`
8. Track progress with `06_CHECKLIST.md`

## Architecture Summary

- **Rust/Tauri v2.0**: UI shell + SQLite execution via `rusqlite` (direct SQLite bindings)
- **Python Sidecar**: Business logic, Supabase sync, conflict resolution
- **IPC**: JSON messages over stdin/stdout
- **Database**: Local SQLite for offline, Supabase for cloud sync

## Key Implementation Notes

- **Tauri Version**: Using v2.0 (tested and working on desktop)
- **SQLite**: Using `rusqlite` directly (works with both v1.5 and v2.0)
- **Incremental Approach**: Start with critical database methods, expand as needed
- **Desktop First**: ✅ IPC tested and working on desktop
- **Configuration**: Uses bundled assets (no `devUrl`), direct API connection for Tauri
