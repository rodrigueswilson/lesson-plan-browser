# Lesson-Plan Alignment Audit Prompt (Enriched)

You are an expert Python backend engineer and software architect. Your task is to systematically audit and fix misalignments between the database schema, Pydantic (and related) models, and API endpoints for the bilingual lesson-plan automation backend.

## Project Context
- **Language / Frameworks**: Python + FastAPI (`backend/api.py`), SQLModel/SQLAlchemy for ORM (`backend/schema.py`), and Pydantic v2 for request/response modeling (`backend/models.py`, `backend/models_slot.py`).
- **Storage**: SQLite by default via `backend/database.SQLiteDatabase`, with optional Supabase support. Schema management lives in `backend/migrations/*.py` and `sql/*.sql`.
- **Domain**: Preschool/elementary lesson plans spanning users, class slots, weeks, days, activities, materials, co-teaching strategies, and WIDA-aligned metadata.
- **Schema validation**: `schemas/lesson_output_schema.json` defines the authoritative JSON contract that LLM output and rendering pipelines must satisfy. `tools/validate_schema` enforces it, and `tools/batch_processor.py` orchestrates ingest → transform → render.

## Repository Anchors
- **Domain / Pydantic models**: `backend/models.py` (API contracts) and `backend/models_slot.py` (slot + lesson JSON helpers).
- **ORM tables**: `backend/schema.py` plus migrations in `backend/migrations/` and Supabase DDL in `sql/`.
- **API surface**: `backend/api.py` exposes users, slots, weekly plans, schedules, lesson steps, analytics, and utility routes.
- **Database abstraction**: `backend/database.py` implements `DatabaseInterface` (`backend/database_interface.py`) for SQLite (and is the hook for Supabase).
- **Lesson data schema**: `schemas/lesson_output_schema.json` (unit/week/day/activity/material definitions used by validation and rendering).

---

## Step 1 – Map The Current State

- **LessonPlan**
  - *Models*: `WeeklyPlanResponse`, `LessonPlanDetailResponse`, `RenderRequest`, `TransformRequest` (`backend/models.py`), plus helper structures in `backend/models_slot.py`.
  - *Database*: `WeeklyPlan` SQLModel in `backend/schema.py` → `weekly_plans` table (columns: `id`, `user_id`, `week_of`, `status`, `output_file`, `week_folder_path`, `consolidated`, `total_slots`, `generated_at`, `processing_time_ms`, `total_tokens`, `total_cost_usd`, `llm_model`, `error_message`, `lesson_json` JSON).
  - *API touchpoints*: `POST /api/process-week`, `GET /api/users/{user_id}/plans`, `GET /api/plans/{plan_id}`, `GET /api/plans/{plan_id}/download`, `POST /api/render`, `POST /api/transform`. Batch orchestration in `tools/batch_processor.py`.

- **Unit**
  - *Models*: `DailyPlanData.unit_lesson` (`backend/models_slot.py`) and `schemas/lesson_output_schema.json > definitions.day_plan.unit_lesson`.
  - *Database*: Stored inside `weekly_plans.lesson_json["days"][day]["unit_lesson"]`.
  - *API*: Surfaced via `GET /api/plans/{plan_id}` (lesson JSON), produced/validated through `/api/transform` and `/api/render`.

- **Week**
  - *Models*: `WeeklyPlanCreate`, `BatchProcessRequest`, `BatchProcessResponse` (`backend/models.py`), slot metadata in `backend/models_slot.py`.
  - *Database*: `weekly_plans.week_of` plus related `class_slots` rows (`backend/schema.py` / `backend/migrations/add_structured_names.py`). Week detection utilities live in `backend/week_detector.py`.
  - *API*: `/api/process-week`, `/api/users/{user_id}/plans`, `/api/users/{user_id}/slots`, `/api/recent-weeks`, `/api/test-weeks`.

- **Day**
  - *Models*: `DailyPlanData` (`backend/models_slot.py`), `ScheduleEntryCreate/Update/Response`, `LessonStepCreate/Response` (`backend/models.py`).
  - *Database*: `ScheduleEntry` SQLModel/table (`schedules`) and `LessonStep` SQLModel/table (`lesson_steps`) in `backend/schema.py` plus migrations `backend/migrations/create_schedules_table.py` & `backend/migrations/create_lesson_steps_table.py`.
  - *API*: Schedule CRUD endpoints (`/api/schedules*`), lesson-step endpoints (`/api/lesson-steps/{plan_id}/{day}/{slot}` and `/api/lesson-steps/generate`), and batch processing (per-day progress events).

- **Activity**
  - *Models*: `LessonStepCreate/Response` and JSON schema definitions for `tailored_instruction`, `co_teaching_model.phase_plan`, `ell_strategy`, `bilingual_overlay` (`schemas/lesson_output_schema.json`).
  - *Database*: `lesson_steps` rows plus `weekly_plans.lesson_json["days"][day]["tailored_instruction"]["phase_plan"]`.
  - *API*: `/api/lesson-steps/*` for CRUD/generation, `/api/process-week` + `tools/batch_processor.py` to persist activities from LLM output.

- **Material**
  - *Models*: `tailored_instruction.materials` arrays (JSON schema) and `LessonStep.materials_needed` (`backend/models.py`).
  - *Database*: Stored as JSON strings in `lesson_steps.materials_needed` and embedded under `weekly_plans.lesson_json["days"][day]["tailored_instruction"]["materials"]`.
  - *API*: Served via `/api/lesson-steps/*`, `/api/plans/{plan_id}`, and consumed by `/api/render` when templating DOCX documents.

---

## Step 2 – Misalignments To Fix

- **LessonStep (API vs ORM vs migration drift)**
  - *Problem*: `LessonStepCreate` / `LessonStepResponse` (`backend/models.py`) and the migration-defined table (`backend/migrations/create_lesson_steps_table.py`) expect columns such as `lesson_plan_id`, `step_name`, `start_time_offset`, `content_type`, `display_content`, `hidden_content`, `sentence_frames`, and JSON arrays. The current SQLModel in `backend/schema.py` still exposes legacy fields (`plan_id`, `content`) and omits the newer columns, so `SQLModel.metadata.create_all` and the ORM layer are out of sync with both the DB and the API contract.
  - *Locations*: `backend/models.py` (LessonStep models), `backend/schema.py` (class `LessonStep`), `backend/migrations/create_lesson_steps_table.py`.
  - *Impact*: `SQLiteDatabase.create_lesson_step` instantiates the stale SQLModel, so inserting current payloads raises `TypeError` or silently drops data. `GET /api/lesson-steps/...` also cannot return the richer structure because the ORM has no fields for it.
  - *Suggested fix*: Update `backend/schema.LessonStep` to match the migration (including correct column names and JSON/list fields), and cascade those changes through the database helper methods.

- **Missing `delete_lesson_steps` implementation**
  - *Problem*: `backend/api.py` (`generate_lesson_steps`) and `test_lesson_mode_api.py` call `db.delete_lesson_steps`, but `DatabaseInterface` and `SQLiteDatabase` never implement this method.
  - *Locations*: `backend/api.py` (lesson-step generation), `test_lesson_mode_api.py`, `backend/database.py`, `backend/database_interface.py`.
  - *Impact*: Lesson-step regeneration currently raises `AttributeError`, preventing updates and breaking tests.
  - *Suggested fix*: Extend the interface and SQLite implementation with a scoped delete (plan/day/slot), and ensure Supabase parity when that backend is re-enabled.

- **LessonStep JSON serialization mismatch**
  - *Problem*: The migration stores `hidden_content`, `sentence_frames`, and `materials_needed` as serialized TEXT blobs. The API surfaces them as `List[str]` / `List[Dict[str,str]]`, but `SQLiteDatabase.create_lesson_step` simply forwards whatever objects it receives into the SQLModel without JSON encoding, and `get_lesson_steps` returns raw SQLModel objects without decoding.
  - *Locations*: `backend/migrations/create_lesson_steps_table.py`, `backend/models.py` (LessonStep models), `backend/database.py` (`create_lesson_step`, `get_lesson_steps`).
  - *Impact*: Depending on the SQLModel definition, inserts fail or data is stored as Python `repr` strings that cannot be deserialized later, and API responses will not match the schema.
  - *Suggested fix*: Normalize serialization at the database layer (encode lists/dicts before insert, decode on read) or use SQLAlchemy JSON columns for these fields once the SQLModel is corrected.

- **Duplicated `BatchProcessRequest` definitions**
  - *Problem*: `backend/models.py` and `backend/models_slot.py` each declare a `BatchProcessRequest` with conflicting validation rules (e.g., `week_of` format `MM/DD-MM/DD` vs ISO `YYYY-MM-DD`, optional `plan_id`). Different modules import different versions (`backend/api.py` uses the API model; tooling may use the slot model), violating SSOT and risking divergent behavior between API layer and batch processor internals.
  - *Locations*: `backend/models.py`, `backend/models_slot.py`, `tools/batch_processor.py`.
  - *Impact*: Developers can unknowingly rely on different validation constraints, and future refactors can break either API clients or batch jobs.
  - *Suggested fix*: Consolidate to a single definition (likely the API-facing one), update imports, and document the accepted `week_of` representation so both DB records and API contracts stay aligned.

---

## Step 3 – Repair Strategy

1. **Declare the single source of truth**
   - Treat `schemas/lesson_output_schema.json` + `backend/models.py` as the canonical API/domain contract.
   - Treat `backend/schema.py` as the canonical persisted schema; migrations should evolve this file, not diverge from it.

2. **Reconcile `LessonStep` across layers**
   - Update `backend/schema.LessonStep` to mirror the migration (new columns, JSON fields, consistent naming).
   - Regenerate / migrate the SQLite table (or craft an ALTER migration) so existing installs pick up the new columns.
   - Update `backend/database.py` CRUD helpers to honor the new attributes and default values.

3. **Implement the missing database operations**
   - Add `delete_lesson_steps` to `DatabaseInterface` and `SQLiteDatabase`, supporting optional filters (`day_of_week`, `slot_number`) to minimize destructive updates.
   - Ensure Supabase-equivalent SQL exists in `sql/create_lesson_steps_table_supabase.sql` or new migration scripts for cloud deployments.

4. **Normalize JSON serialization for arrays/dicts**
   - When persisting list/dict fields (`hidden_content`, `sentence_frames`, `materials_needed`), serialize to JSON strings (or upgrade to actual JSON columns). When reading, deserialize before returning to the API layer so Pydantic responses remain structured.
   - Consider lightweight helper methods inside `SQLiteDatabase` (e.g., `_json_dump` / `_json_load`) to keep the logic DRY.

5. **Deduplicate `BatchProcessRequest`**
   - Retain one definition (e.g., in `backend/models.py`), update `tools/batch_processor.py` and any scripts/tests to import it, and document the accepted `week_of` format so DB rows, API payloads, and CLI tooling remain consistent.

6. **Backwards-compatibility**
   - Provide a migration path for existing `lesson_steps` rows (e.g., default `step_name` to `"Step {n}"` if missing).
   - Communicate any API contract changes (e.g., `week_of` formatting) and, if needed, support both formats temporarily by validating & normalizing inside the request model.

---

## Step 4 – First Fix Chunk (LessonPlan + LessonStep)

Focus the initial PR on aligning `LessonStep` persistence with the API contract while preserving `WeeklyPlan` usage:

1. **Update the ORM**
   - Replace the legacy `LessonStep` definition in `backend/schema.py` with one that matches the migration (new columns, JSON fields, matching names such as `lesson_plan_id`, `step_name`, `start_time_offset`, `content_type`, `display_content`, `hidden_content`, `sentence_frames`, `materials_needed`, `updated_at`).

2. **Extend the database interface**
   - Add `delete_lesson_steps` to `backend/database_interface.py` and implement it in `backend/database.py` using SQLModel’s query builder (scoped by plan/day/slot). Ensure callers (`backend/api.py`, tests) import the updated interface.

3. **Normalize serialization / add helpers**
   - In `SQLiteDatabase.create_lesson_step`, JSON-encode list/dict fields before constructing the SQLModel, ensure IDs + timestamps are set, and return the generated ID.
   - In `get_lesson_steps`, decode those columns before returning (so FastAPI responses already contain Python lists/dicts). Consider a small `_deserialize_lesson_step` helper.

4. **Backfill existing data**
   - Write a lightweight migration (or a one-off script) to migrate legacy `lesson_steps` rows (copy `content` into `display_content`, initialize missing JSON fields to empty lists) so old data remains usable.

5. **Keep changes scoped**
   - Defer Supabase-specific SQL updates to a follow-up PR if needed, but document the TODO inside `sql/create_lesson_steps_table_supabase.sql`.

### Illustrative diffs

```diff
@@ backend/schema.py:class LessonStep(SQLModel, table=True)
-class LessonStep(SQLModel, table=True):
-    __tablename__ = "lesson_steps"
-    
-    id: str = Field(primary_key=True)
-    plan_id: str = Field(index=True)
-    day_of_week: str
-    slot_number: int
-    step_number: int
-    content: str
-    duration_minutes: Optional[int] = None
-    materials_needed: Optional[str] = None
-    created_at: datetime = Field(default_factory=datetime.utcnow)
+class LessonStep(SQLModel, table=True):
+    __tablename__ = "lesson_steps"
+
+    id: str = Field(primary_key=True)
+    lesson_plan_id: str = Field(index=True)
+    day_of_week: str
+    slot_number: int
+    step_number: int
+    step_name: str
+    duration_minutes: int
+    start_time_offset: int
+    content_type: str
+    display_content: str
+    hidden_content: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
+    sentence_frames: Optional[List[Dict[str, str]]] = Field(default=None, sa_column=Column(JSON))
+    materials_needed: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
+    created_at: datetime = Field(default_factory=datetime.utcnow)
+    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

```diff
@@ backend/database.py
-    def create_lesson_step(self, step_data: Dict[str, Any]) -> str:
-        """Create a lesson step."""
-        try:
-            step = LessonStep(**step_data)
-            with Session(self.engine) as session:
-                session.add(step)
-                session.commit()
-                session.refresh(step)
-                return step.id
-        except Exception as e:
-            logger.error(f"Error creating lesson step: {e}")
-            raise
+    def create_lesson_step(self, step_data: Dict[str, Any]) -> str:
+        """Create a lesson step with JSON-aware fields."""
+        payload = step_data.copy()
+        payload.setdefault("id", f"step_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
+        now = datetime.utcnow()
+        payload.setdefault("created_at", now)
+        payload.setdefault("updated_at", now)
+        for key in ("hidden_content", "sentence_frames", "materials_needed"):
+            if key in payload and payload[key] is not None:
+                payload[key] = json.dumps(payload[key])
+        step = LessonStep(**payload)
+        with Session(self.engine) as session:
+            session.add(step)
+            session.commit()
+            session.refresh(step)
+            return step.id
+
+    def delete_lesson_steps(
+        self,
+        plan_id: str,
+        day_of_week: Optional[str] = None,
+        slot_number: Optional[int] = None,
+    ) -> int:
+        """Delete lesson steps scoped to a plan/day/slot."""
+        with Session(self.engine) as session:
+            stmt = delete(LessonStep).where(LessonStep.lesson_plan_id == plan_id)
+            if day_of_week:
+                stmt = stmt.where(LessonStep.day_of_week == day_of_week)
+            if slot_number is not None:
+                stmt = stmt.where(LessonStep.slot_number == slot_number)
+            result = session.exec(stmt)
+            session.commit()
+            return result.rowcount or 0
+
+    def get_lesson_steps(...):
+        steps = list(session.exec(query).all())
+        for step in steps:
+            step.hidden_content = self._parse_json(step.hidden_content)
+            step.sentence_frames = self._parse_json(step.sentence_frames)
+            step.materials_needed = self._parse_json(step.materials_needed)
+        return steps
```

*(Helper `_parse_json` would simply return `None` for falsy values or `json.loads(value)` otherwise.)*

---

## Step 5 – Tests & Guarantees

1. **Database-level regression**
   - Extend `test_lesson_mode_api.py` (or move into `tests/`) to create → fetch → delete lesson steps through `SQLiteDatabase`, asserting that the round-trip preserves `hidden_content`, `sentence_frames`, `materials_needed`, and timestamps.
   - Add a reflection test that inspects `SQLModel.metadata.tables["lesson_steps"].columns` and compares them against the migration schema (ensuring future changes stay aligned).

2. **API contract checks**
   - Add FastAPI integration tests (e.g., under `tests/test_lesson_steps_api.py`) that hit `/api/lesson-steps/generate` and `/api/lesson-steps/{plan_id}/{day}/{slot}`, verifying that responses conform to `LessonStepResponse` (lists/dicts, required fields) and that regeneration clears/replaces prior steps.
   - Add a parametrized test for `/api/process-week` ensuring the stored `weekly_plans.lesson_json` echoes the JSON schema (use `schemas/lesson_output_schema.json` to validate the persisted payload).

3. **Property / schema validation**
   - Introduce a lightweight check that walks `LessonStepResponse.model_json_schema()` and compares key field names/types against `schemas/lesson_output_schema.json` definitions for `phase_plan` entries, flagging divergence early.
   - Consider using `schemathesis` or similar contract tests to ensure `/api/lesson-steps/*` responses remain in sync with the published schema when future migrations land.

These tests ensure that once `LessonStep` is realigned, any future schema drift is caught at the Pydantic, DB, and API layers before shipping.

