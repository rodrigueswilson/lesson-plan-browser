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
    
    # Parallel processing metrics
    is_parallel: Optional[bool] = Field(default=False, description="Whether this operation was processed in parallel")
    parallel_slot_count: Optional[int] = Field(default=None, description="Number of slots processed in parallel")
    sequential_time_ms: Optional[float] = Field(default=None, description="Estimated time if processed sequentially")
    rate_limit_errors: Optional[int] = Field(default=0, description="Number of rate limit errors encountered")
    concurrency_level: Optional[int] = Field(default=None, description="Actual concurrency level used")
    tpm_usage: Optional[int] = Field(default=None, description="Tokens per minute usage at time of request")
    rpm_usage: Optional[int] = Field(default=None, description="Requests per minute usage at time of request")


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


class OriginalLessonPlan(SQLModel, table=True):
    """Store original lesson plan content from primary teachers before LLM transformation."""
    
    __tablename__ = "original_lesson_plans"
    
    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    week_of: str
    slot_number: int
    subject: str
    grade: str
    homeroom: Optional[str] = None
    
    # Source file information
    source_file_path: str
    source_file_name: str
    primary_teacher_name: Optional[str] = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Extracted content (structured)
    content_json: Dict[str, Any] = Field(sa_column=Column(JSON))  # Full extracted content
    full_text: Optional[str] = None  # Plain text version for LLM
    
    # Per-day content breakdown (optional, for easier querying)
    monday_content: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    tuesday_content: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    wednesday_content: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    thursday_content: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    friday_content: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    
    # Metadata
    available_days: Optional[List[str]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    has_no_school: bool = Field(default=False)
    content_hash: Optional[str] = None  # Hash for change detection
    
    # Status
    status: str = Field(default="extracted")  # 'extracted', 'processed', 'error'
    error_message: Optional[str] = None
    
    # Timestamps
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
