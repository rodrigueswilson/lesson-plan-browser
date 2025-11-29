from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(primary_key=True)
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: str  # Legacy full name
    base_path_override: Optional[str] = None
    template_path: Optional[str] = None
    signature_image_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ClassSlot(SQLModel, table=True):
    __tablename__ = "class_slots"

    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    slot_number: int
    subject: str
    grade: str
    homeroom: Optional[str] = None
    plan_group_label: Optional[str] = None
    proficiency_levels: Optional[str] = None
    primary_teacher_file: Optional[str] = None
    primary_teacher_name: Optional[str] = None
    primary_teacher_first_name: Optional[str] = None
    primary_teacher_last_name: Optional[str] = None
    primary_teacher_file_pattern: Optional[str] = None
    display_order: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WeeklyPlan(SQLModel, table=True):
    __tablename__ = "weekly_plans"

    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    week_of: str
    status: str = "pending"
    output_file: Optional[str] = None
    week_folder_path: Optional[str] = None
    consolidated: int = 0  # 0 or 1
    total_slots: int = 1
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = None
    total_tokens: Optional[int] = None
    total_cost_usd: Optional[float] = None
    llm_model: Optional[str] = None
    error_message: Optional[str] = None
    lesson_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))


class ScheduleEntry(SQLModel, table=True):
    __tablename__ = "schedules"

    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    day_of_week: str
    slot_number: int
    start_time: str
    end_time: str
    subject: Optional[str] = None
    grade: Optional[str] = None
    homeroom: Optional[str] = None
    plan_slot_group_id: Optional[str] = Field(default=None, index=True)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PerformanceMetric(SQLModel, table=True):
    __tablename__ = "performance_metrics"

    id: str = Field(primary_key=True)
    plan_id: str = Field(index=True)
    slot_number: Optional[int] = None
    day_number: Optional[int] = None
    operation_type: str
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    tokens_total: Optional[int] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    cost_usd: Optional[float] = None
    error_message: Optional[str] = None


class LessonStep(SQLModel, table=True):
    __tablename__ = "lesson_steps"

    id: str = Field(primary_key=True)
    lesson_plan_id: str = Field(index=True)
    day_of_week: str
    slot_number: int
    step_number: int
    step_name: str
    duration_minutes: int
    start_time_offset: int
    content_type: str
    display_content: str
    hidden_content: Optional[List[str]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    sentence_frames: Optional[List[Dict[str, str]]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    materials_needed: Optional[List[str]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    vocabulary_cognates: Optional[List[Dict[str, Any]]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LessonModeSession(SQLModel, table=True):
    """Lesson mode session for state persistence."""

    __tablename__ = "lesson_mode_sessions"

    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    lesson_plan_id: str = Field(index=True)
    schedule_entry_id: Optional[str] = None
    day_of_week: str
    slot_number: int
    current_step_index: int = Field(default=0)
    remaining_time: int = Field(default=0)  # seconds
    is_running: bool = Field(default=False)
    is_paused: bool = Field(default=False)
    is_synced: bool = Field(default=False)
    timer_start_time: Optional[datetime] = None
    paused_at: Optional[int] = None  # seconds
    adjusted_durations: Optional[Dict[str, int]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )  # {step_index: adjusted_duration_seconds}
    session_start_time: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
