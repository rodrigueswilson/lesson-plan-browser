# Local Optimization & Architecture Plan

**Date:** November 18, 2025
**Context:** Transitioning from cloud-scale architectural ideas to optimized local desktop application architecture (Tauri + Python).

## 1. Executive Summary

The goal is to optimize the Bilingual Lesson Plan Builder for **local desktop execution** rather than cloud deployment. Previous research into heavy orchestration tools (Maestro, Kestra, Airflow) has been rejected in favor of lightweight, in-process libraries that respect the constraints of a distributed `.exe`/`.dmg` application.

**Selected Stack:**
- **Caching:** `diskcache` (Replaces Redis)
- **Parallelism:** `joblib` (Standard local multiprocessing)
- **Validation:** `pydantic` v2 (Enhanced models)

## 2. Architecture Constraints

Since this application runs locally on a user's machine:
1.  **No External Services:** We cannot require users to install Redis, PostgreSQL, or Docker.
2.  **File-System Based:** State and cache must persist to the local file system (SQLite + DiskCache).
3.  **Resource Aware:** Must respect the user's laptop CPU/RAM limits.

## 3. Implementation Plan

### A. Caching Layer (`diskcache`)

**Problem:** Repeated LLM calls and file parsing are slow and expensive.
**Solution:** Implement persistent disk caching.

**Implementation Details:**
- **Library:** `diskcache`
- **Location:** Application data directory (e.g., `%APPDATA%/BilingualBuilder/cache`)
- **TTL:**
    - Parsed DOCX content: 24 hours (invalidated on file modification time)
    - LLM Translations: 30 days (high re-use potential)
    - Slot Mappings: 7 days

**Code Pattern:**
```python
from diskcache import Cache
from pathlib import Path

# Initialize in standard app data location
cache_dir = Path.home() / ".bilingual_builder" / "cache"
cache = Cache(str(cache_dir), size_limit=int(1e9)) # 1GB limit

@cache.memoize(expire=86400)
def parse_heavy_file(file_path: str, mtime: float):
    # mtime ensures cache invalidation if file changes
    return parser.parse(file_path)
```

### B. Parallel Processing (`joblib`)

**Problem:** Processing 5-10 slots sequentially is too slow.
**Solution:** Process independent slots in parallel using local CPU cores.

**Implementation Details:**
- **Library:** `joblib`
- **Strategy:** `ThreadBackend` (preferred over ProcessBackend for text/API heavy tasks to avoid pickling overhead, though `ProcessBackend` is safer for heavy CPU parsing).
- **Concurrency:** Default to `CPU_COUNT - 1` to keep UI responsive.

**Code Pattern:**
```python
from joblib import Parallel, delayed

def process_week(user_slots):
    results = Parallel(n_jobs=-1, prefer="threads")(
        delayed(process_single_slot)(slot) 
        for slot in user_slots
    )
    return results
```

### C. Data Validation (`pydantic` v2)

**Problem:** Loose data typing causes runtime errors deep in the pipeline.
**Solution:** Enforce strict schemas at the entry point.

**Implementation Details:**
- **Library:** `pydantic` (Upgrade to v2 syntax)
- **Models:**
    - `SlotConfig`: Strict validation of slot inputs (1-10 range, valid subjects).
    - `LessonContent`: Validation of parsed content structure.
    - `TransformationResult`: Verification that LLM output matches expected schema.

## 4. Migration Steps

1.  **Dependency Update**:
    - Add `diskcache`, `joblib`.
    - Remove `redis` (if present in `requirements.txt`).

2.  **Cache Implementation**:
    - Create `backend/cache.py` utility module.
    - Wrap `DOCXParser` methods with `@cache.memoize`.

3.  **Refactor BatchProcessor**:
    - Replace `asyncio` loops with `joblib` parallel execution where CPU bound.
    - Integrate `SlotConfig` pydantic model for input validation.

4.  **Cleanup**:
    - Remove any Docker-compose references to Redis.
    - Remove unused complex orchestration code.

## 5. Database Implications

- **SQLite** remains the primary data store.
- **DiskCache** effectively acts as a secondary, ephemeral NoSQL store for performance.
- No schema changes required in SQLite (`class_slots` table remains authoritative).

## 6. Success Metrics

- **Processing Time:** < 2 minutes for a full 5-slot week (vs 10+ mins).
- **Cache Hit Rate:** > 80% for re-runs.
- **Installation Size:** Minimal increase (< 5MB).
