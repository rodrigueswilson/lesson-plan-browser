"""
SQLite implementation of DatabaseInterface composing engine and domain modules.
"""

from contextlib import contextmanager
from pathlib import Path as PathType
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.database_interface import DatabaseInterface
from backend.schema import (
    ClassSlot,
    LessonModeSession,
    LessonStep,
    ScheduleEntry,
    User,
    WeeklyPlan,
)

from backend.database.engine import (
    build_engine,
    get_connection as engine_get_connection,
    hydrate_lesson_step as engine_hydrate_lesson_step,
    init_db as engine_init_db,
    _coerce_json_field as engine_coerce_json_field,
    _normalize_day as engine_normalize_day,
)
from backend.database import users as users_module
from backend.database import slots as slots_module
from backend.database import plans as plans_module
from backend.database import metrics as metrics_module
from backend.database import schedule as schedule_module
from backend.database import lesson_steps as lesson_steps_module
from backend.database import lesson_mode as lesson_mode_module


class SQLiteDatabase(DatabaseInterface):
    """SQLite implementation of DatabaseInterface using SQLModel."""

    def __init__(
        self,
        db_path: Optional[Union[str, PathType]] = None,
        use_ipc: bool = False,
        **kwargs,
    ):
        path_arg = db_path if db_path is not None else kwargs.get("db_path")
        self.use_ipc = use_ipc
        self.engine, self.db_path, _use_ipc, self._adapter = build_engine(
            db_path=path_arg, use_ipc=use_ipc, **kwargs
        )

    @staticmethod
    def _normalize_day(day: Optional[str]) -> Optional[str]:
        return engine_normalize_day(day)

    @staticmethod
    def _coerce_json_field(value: Any) -> Any:
        return engine_coerce_json_field(value)

    def _hydrate_lesson_step(self, step: LessonStep) -> LessonStep:
        return engine_hydrate_lesson_step(step, self._coerce_json_field)

    @contextmanager
    def get_connection(self):
        if self.use_ipc:
            raise NotImplementedError("get_connection not supported in IPC mode")
        with engine_get_connection(self.engine) as session:
            yield session

    def init_db(self):
        if self.use_ipc:
            return
        engine_init_db(self.engine)

    # User CRUD
    def create_user(
        self,
        first_name: str = None,
        last_name: str = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> str:
        return users_module.create_user(
            self, first_name, last_name, email, name
        )

    def get_user(self, user_id: str) -> Optional[User]:
        return users_module.get_user(self, user_id)

    def get_user_by_name(self, name: str) -> Optional[User]:
        return users_module.get_user_by_name(self, name)

    def list_users(self) -> List[User]:
        return users_module.list_users(self)

    def update_user(
        self,
        user_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ) -> bool:
        return users_module.update_user(
            self, user_id, first_name, last_name, email, name
        )

    def update_user_base_path(self, user_id: str, base_path: str) -> bool:
        return users_module.update_user_base_path(self, user_id, base_path)

    def update_user_template_paths(
        self,
        user_id: str,
        template_path: Optional[str] = None,
        signature_image_path: Optional[str] = None,
    ) -> bool:
        return users_module.update_user_template_paths(
            self, user_id, template_path, signature_image_path
        )

    def delete_user(self, user_id: str) -> bool:
        return users_module.delete_user(self, user_id)

    # Class slots
    def create_class_slot(
        self,
        user_id: str,
        slot_number: int,
        subject: str,
        grade: str,
        homeroom: Optional[str] = None,
        plan_group_label: Optional[str] = None,
        proficiency_levels: Optional[str] = None,
        primary_teacher_file: Optional[str] = None,
        primary_teacher_first_name: Optional[str] = None,
        primary_teacher_last_name: Optional[str] = None,
    ) -> str:
        return slots_module.create_class_slot(
            self,
            user_id,
            slot_number,
            subject,
            grade,
            homeroom=homeroom,
            plan_group_label=plan_group_label,
            proficiency_levels=proficiency_levels,
            primary_teacher_file=primary_teacher_file,
            primary_teacher_first_name=primary_teacher_first_name,
            primary_teacher_last_name=primary_teacher_last_name,
        )

    def get_user_slots(self, user_id: str) -> List[ClassSlot]:
        return slots_module.get_user_slots(self, user_id)

    def get_slot(self, slot_id: str) -> Optional[ClassSlot]:
        return slots_module.get_slot(self, slot_id)

    def update_class_slot(self, slot_id: str, **kwargs) -> bool:
        return slots_module.update_class_slot(self, slot_id, **kwargs)

    def delete_class_slot(self, slot_id: str) -> bool:
        return slots_module.delete_class_slot(self, slot_id)

    def delete_user_slots(self, user_id: str) -> int:
        return slots_module.delete_user_slots(self, user_id)

    # Weekly plans
    def create_weekly_plan(
        self,
        user_id: str,
        week_of: str,
        output_file: str,
        week_folder_path: str,
        consolidated: bool = False,
        total_slots: int = 1,
    ) -> str:
        return plans_module.create_weekly_plan(
            self,
            user_id,
            week_of,
            output_file,
            week_folder_path,
            consolidated=consolidated,
            total_slots=total_slots,
        )

    def get_weekly_plan(self, plan_id: str) -> Optional[WeeklyPlan]:
        return plans_module.get_weekly_plan(self, plan_id)

    def get_user_plans(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[WeeklyPlan]:
        return plans_module.get_user_plans(self, user_id, limit=limit)

    def update_weekly_plan(
        self,
        plan_id: str,
        status: Optional[str] = None,
        output_file: Optional[str] = None,
        error_message: Optional[str] = None,
        lesson_json: Optional[Dict[str, Any]] = None,
        total_slots: Optional[int] = None,
    ) -> bool:
        return plans_module.update_weekly_plan(
            self,
            plan_id,
            status=status,
            output_file=output_file,
            error_message=error_message,
            lesson_json=lesson_json,
            total_slots=total_slots,
        )

    # Original lesson plans
    def create_original_lesson_plan(self, plan_data: Dict[str, Any]) -> str:
        return plans_module.create_original_lesson_plan(self, plan_data)

    def get_original_lesson_plan(
        self, user_id: str, week_of: str, slot_number: int
    ):
        return plans_module.get_original_lesson_plan(
            self, user_id, week_of, slot_number
        )

    def get_original_lesson_plans_for_week(
        self, user_id: str, week_of: str
    ) -> List:
        return plans_module.get_original_lesson_plans_for_week(
            self, user_id, week_of
        )

    def get_original_lesson_plans_for_file(
        self, user_id: str, week_of: str, file_path: str
    ) -> List:
        return plans_module.get_original_lesson_plans_for_file(
            self, user_id, week_of, file_path
        )

    def update_original_lesson_plan_status(
        self, plan_id: str, status: str, error_message: Optional[str] = None
    ) -> bool:
        return plans_module.update_original_lesson_plan_status(
            self, plan_id, status, error_message=error_message
        )

    def delete_original_lesson_plans(self, user_id: str, week_of: str) -> int:
        return plans_module.delete_original_lesson_plans(
            self, user_id, week_of
        )

    # Metrics
    def save_performance_metric(
        self,
        operation_id: str,
        plan_id: str,
        operation_type: str,
        started_at: Any,
        completed_at: Any,
        duration_ms: float,
        tokens_input: int,
        tokens_output: int,
        tokens_total: int,
        llm_provider: str,
        llm_model: str,
        cost_usd: float,
        error_message: Optional[str],
        slot_number: Optional[int] = None,
        day_number: Optional[int] = None,
        is_parallel: Optional[bool] = None,
        parallel_slot_count: Optional[int] = None,
        sequential_time_ms: Optional[float] = None,
        rate_limit_errors: Optional[int] = None,
        concurrency_level: Optional[int] = None,
        tpm_usage: Optional[int] = None,
        rpm_usage: Optional[int] = None,
    ) -> None:
        metrics_module.save_performance_metric(
            self,
            operation_id,
            plan_id,
            operation_type,
            started_at,
            completed_at,
            duration_ms,
            tokens_input,
            tokens_output,
            tokens_total,
            llm_provider,
            llm_model,
            cost_usd,
            error_message,
            slot_number=slot_number,
            day_number=day_number,
            is_parallel=is_parallel,
            parallel_slot_count=parallel_slot_count,
            sequential_time_ms=sequential_time_ms,
            rate_limit_errors=rate_limit_errors,
            concurrency_level=concurrency_level,
            tpm_usage=tpm_usage,
            rpm_usage=rpm_usage,
        )

    def delete_old_metrics(self, days: int = 30) -> int:
        return metrics_module.delete_old_metrics(self, days)

    def get_plan_metrics(self, plan_id: str) -> List[Dict[str, Any]]:
        return metrics_module.get_plan_metrics(self, plan_id)

    def get_plan_summary(self, plan_id: str) -> Dict[str, Any]:
        return metrics_module.get_plan_summary(self, plan_id)

    def update_plan_summary(
        self,
        plan_id: str,
        processing_time_ms: Optional[float],
        total_tokens: Optional[int],
        total_cost_usd: Optional[float],
        llm_model: Optional[str],
    ) -> bool:
        return metrics_module.update_plan_summary(
            self,
            plan_id,
            processing_time_ms,
            total_tokens,
            total_cost_usd,
            llm_model,
        )

    def get_aggregate_stats(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return metrics_module.get_aggregate_stats(self, days, user_id=user_id)

    def get_daily_breakdown(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return metrics_module.get_daily_breakdown(self, days, user_id=user_id)

    def get_session_breakdown(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return metrics_module.get_session_breakdown(self, days, user_id=user_id)

    def get_operation_stats(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return metrics_module.get_operation_stats(self, days, user_id=user_id)

    def get_error_stats(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return metrics_module.get_error_stats(self, days, user_id=user_id)

    def get_parallel_processing_stats(
        self, days: int = 30, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return metrics_module.get_parallel_processing_stats(
            self, days, user_id=user_id
        )

    # Schedule
    def create_schedule_entry(self, entry_data: Dict[str, Any]) -> str:
        return schedule_module.create_schedule_entry(self, entry_data)

    def get_user_schedule(
        self,
        user_id: str,
        day_of_week: Optional[str] = None,
        homeroom: Optional[str] = None,
        grade: Optional[str] = None,
    ) -> List[ScheduleEntry]:
        return schedule_module.get_user_schedule(
            self, user_id, day_of_week=day_of_week,
            homeroom=homeroom, grade=grade
        )

    def get_current_lesson(self, user_id: str) -> Optional[ScheduleEntry]:
        return schedule_module.get_current_lesson(self, user_id)

    def update_schedule_entry(
        self, schedule_id: str, updates: Dict[str, Any]
    ) -> bool:
        return schedule_module.update_schedule_entry(
            self, schedule_id, updates
        )

    def delete_schedule_entry(self, schedule_id: str) -> bool:
        return schedule_module.delete_schedule_entry(self, schedule_id)

    def bulk_create_schedule_entries(
        self, entries: List[Dict[str, Any]]
    ) -> Tuple[int, List[str]]:
        return schedule_module.bulk_create_schedule_entries(self, entries)

    def clear_user_schedule(self, user_id: str) -> int:
        return schedule_module.clear_user_schedule(self, user_id)

    # Lesson steps
    def create_lesson_step(self, step_data: Dict[str, Any]) -> str:
        return lesson_steps_module.create_lesson_step(self, step_data)

    def delete_lesson_steps(
        self,
        plan_id: str,
        day_of_week: Optional[str] = None,
        slot_number: Optional[int] = None,
    ) -> int:
        return lesson_steps_module.delete_lesson_steps(
            self, plan_id, day_of_week=day_of_week, slot_number=slot_number
        )

    def get_lesson_steps(
        self,
        plan_id: str,
        day_of_week: Optional[str] = None,
        slot_number: Optional[int] = None,
    ) -> List[LessonStep]:
        return lesson_steps_module.get_lesson_steps(
            self, plan_id, day_of_week=day_of_week, slot_number=slot_number
        )

    # Lesson mode sessions
    def create_lesson_mode_session(self, session_data: Dict[str, Any]) -> str:
        return lesson_mode_module.create_lesson_mode_session(
            self, session_data
        )

    def get_lesson_mode_session(
        self, session_id: str
    ) -> Optional[LessonModeSession]:
        return lesson_mode_module.get_lesson_mode_session(self, session_id)

    def get_active_lesson_mode_session(
        self,
        user_id: str,
        lesson_plan_id: Optional[str] = None,
        day_of_week: Optional[str] = None,
        slot_number: Optional[int] = None,
    ) -> Optional[LessonModeSession]:
        return lesson_mode_module.get_active_lesson_mode_session(
            self,
            user_id,
            lesson_plan_id=lesson_plan_id,
            day_of_week=day_of_week,
            slot_number=slot_number,
        )

    def update_lesson_mode_session(
        self, session_id: str, updates: Dict[str, Any]
    ) -> bool:
        return lesson_mode_module.update_lesson_mode_session(
            self, session_id, updates
        )

    def end_lesson_mode_session(self, session_id: str) -> bool:
        return lesson_mode_module.end_lesson_mode_session(self, session_id)
