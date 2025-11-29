"""
API Request/Response Models for Bilingual Lesson Plan Builder.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ValidationRequest(BaseModel):
    """Request to validate lesson plan JSON."""

    json_data: Dict[str, Any] = Field(..., description="Lesson plan JSON to validate")


class ValidationError(BaseModel):
    """Validation error detail."""

    field: str
    message: str
    value: Optional[Any] = None


class ValidationResponse(BaseModel):
    """Response from validation."""

    valid: bool
    errors: Optional[List[ValidationError]] = None
    warnings: Optional[List[str]] = None


class RenderRequest(BaseModel):
    """Request to render lesson plan to DOCX."""

    json_data: Dict[str, Any] = Field(..., description="Validated lesson plan JSON")
    output_filename: Optional[str] = Field(
        default="lesson_plan.docx", description="Output filename for DOCX"
    )
    template_path: Optional[str] = Field(
        default="input/Lesson Plan Template SY'25-26.docx",
        description="Path to district template",
    )


class RenderResponse(BaseModel):
    """Response from rendering."""

    success: bool
    output_path: Optional[str] = None
    file_size: Optional[int] = None
    render_time_ms: Optional[float] = None
    errors: Optional[List[str]] = None


class ProgressUpdate(BaseModel):
    """Progress update for SSE streaming."""

    stage: str
    progress: int  # 0-100
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TransformRequest(BaseModel):
    """Request to transform primary teacher content to bilingual lesson plan."""

    primary_content: str = Field(..., description="Primary teacher's lesson content")
    grade: str = Field(..., description="Grade level (e.g., '6', '7')")
    subject: str = Field(..., description="Subject area")
    week_of: str = Field(..., description="Week date range (MM/DD-MM/DD)")
    teacher_name: Optional[str] = Field(None, description="Bilingual teacher name")
    homeroom: Optional[str] = Field(None, description="Homeroom/class identifier")
    provider: Optional[str] = Field(
        "openai", description="LLM provider (openai or anthropic)"
    )


class TransformResponse(BaseModel):
    """Response from LLM transformation."""

    success: bool
    lesson_json: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    transform_time_ms: Optional[float] = None


# User Profile Models


class UserCreate(BaseModel):
    """Request to create a new user."""

    first_name: str = Field(..., min_length=1, description="User's first name")
    last_name: str = Field(..., min_length=1, description="User's last name")
    email: Optional[str] = Field(None, description="User's email address")

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_parts(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()


class UserUpdate(BaseModel):
    """Request to update user profile."""

    first_name: Optional[str] = Field(
        None, min_length=1, description="User's first name"
    )
    last_name: Optional[str] = Field(None, min_length=1, description="User's last name")
    email: Optional[str] = Field(None, description="User's email address")

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_parts(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip() if v else v


class UserResponse(BaseModel):
    """User profile response."""

    id: str
    name: str  # Computed for backward compatibility
    first_name: str
    last_name: str
    email: Optional[str] = None
    base_path_override: Optional[str] = None
    template_path: Optional[str] = None
    signature_image_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClassSlotCreate(BaseModel):
    """Request to create a class slot."""

    slot_number: int = Field(..., ge=1, le=6, description="Slot number (1-6)")
    subject: str = Field(..., description="Subject name")
    grade: str = Field(..., description="Grade level")
    homeroom: Optional[str] = Field(None, description="Homeroom/class identifier")
    plan_group_label: Optional[str] = Field(
        None, description="Default linked lesson group label"
    )
    proficiency_levels: Optional[str] = Field(
        None, description="JSON string of proficiency levels"
    )
    primary_teacher_file: Optional[str] = Field(
        None, description="Path to primary teacher's DOCX file"
    )
    primary_teacher_first_name: Optional[str] = Field(
        None, description="Primary teacher's first name"
    )
    primary_teacher_last_name: Optional[str] = Field(
        None, description="Primary teacher's last name"
    )

    @field_validator("primary_teacher_first_name", "primary_teacher_last_name")
    @classmethod
    def validate_teacher_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip()
        return v


class ClassSlotUpdate(BaseModel):
    """Request to update a class slot."""

    subject: Optional[str] = None
    grade: Optional[str] = None
    homeroom: Optional[str] = None
    plan_group_label: Optional[str] = None
    proficiency_levels: Optional[str] = None
    primary_teacher_file: Optional[str] = None
    primary_teacher_name: Optional[str] = None
    primary_teacher_file_pattern: Optional[str] = None
    primary_teacher_first_name: Optional[str] = None
    primary_teacher_last_name: Optional[str] = None
    slot_number: Optional[int] = Field(None, ge=1, le=10)
    display_order: Optional[int] = None

    @field_validator("primary_teacher_first_name", "primary_teacher_last_name")
    @classmethod
    def validate_teacher_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip()
        return v


class ClassSlotResponse(BaseModel):
    """Class slot response."""

    id: str
    user_id: str
    slot_number: int
    subject: str
    grade: str
    homeroom: Optional[str] = None
    plan_group_label: Optional[str] = None
    proficiency_levels: Optional[str] = None
    primary_teacher_file: Optional[str] = None
    primary_teacher_name: Optional[str] = None  # Computed for backward compatibility
    primary_teacher_first_name: Optional[str] = None
    primary_teacher_last_name: Optional[str] = None
    primary_teacher_file_pattern: Optional[str] = None
    display_order: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WeeklyPlanCreate(BaseModel):
    """Request to create a weekly plan."""

    week_of: str = Field(..., description="Week date range (MM/DD-MM/DD)")


class WeeklyPlanResponse(BaseModel):
    """Weekly plan response."""

    id: str
    user_id: str
    week_of: str
    generated_at: datetime
    output_file: Optional[str] = None
    status: str
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BatchProcessRequest(BaseModel):
    """Request to process all class slots for a week."""

    user_id: str = Field(..., description="User ID")
    week_of: str = Field(..., description="Week date range (MM/DD-MM/DD)")
    provider: Optional[str] = Field(
        "openai", description="LLM provider (openai or anthropic)"
    )
    slot_ids: Optional[List[str]] = Field(
        None, description="Optional list of specific slot IDs to process"
    )


class BatchProcessResponse(BaseModel):
    """Response from batch processing."""

    success: bool
    plan_id: str
    output_file: Optional[str] = None
    processed_slots: int
    failed_slots: int
    total_time_ms: Optional[float] = None
    errors: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


# Schedule Models


class ScheduleEntryCreate(BaseModel):
    """Request to create a schedule entry."""

    user_id: str
    day_of_week: str = Field(
        ..., description="Day of week: monday, tuesday, wednesday, thursday, friday"
    )
    start_time: str = Field(
        ..., description="Start time in HH:MM format (e.g., '08:15')"
    )
    end_time: str = Field(..., description="End time in HH:MM format (e.g., '08:30')")
    subject: str = Field(
        ..., description="Subject name (e.g., 'ELA', 'MATH', 'PREP', 'Lunch')"
    )
    homeroom: Optional[str] = Field(
        None, description="Homeroom identifier (e.g., 'T5', '209', 'T2')"
    )
    grade: Optional[str] = Field(None, description="Grade level (e.g., '5', '2', 'K')")
    slot_number: int = Field(..., description="Sequential slot number")
    is_active: bool = Field(True, description="Whether this is an active class period")
    plan_slot_group_id: Optional[str] = Field(
        None,
        description="Identifier used to link multiple periods to the same lesson plan slot",
    )


class ScheduleEntryUpdate(BaseModel):
    """Request to update a schedule entry."""

    subject: Optional[str] = None
    homeroom: Optional[str] = None
    grade: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_active: Optional[bool] = None
    plan_slot_group_id: Optional[str] = None


class ScheduleEntryResponse(BaseModel):
    """Response with schedule entry data."""

    id: str
    user_id: str
    day_of_week: str
    start_time: str
    end_time: str
    subject: str
    homeroom: Optional[str]
    grade: Optional[str]
    slot_number: int
    plan_slot_group_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScheduleBulkCreateRequest(BaseModel):
    """Request to bulk create schedule entries."""

    entries: List[ScheduleEntryCreate]


class ScheduleBulkCreateResponse(BaseModel):
    """Response from bulk create."""

    success: bool
    created_count: int
    errors: Optional[List[str]] = None


# Lesson Steps Models


class LessonStepCreate(BaseModel):
    """Request to create a lesson step."""

    lesson_plan_id: str
    day_of_week: str  # 'monday', 'tuesday', etc.
    slot_number: int
    step_number: int
    step_name: str
    duration_minutes: int
    start_time_offset: int  # minutes from lesson start
    content_type: (
        str  # 'objective', 'sentence_frames', 'materials', 'instruction', 'assessment'
    )
    display_content: str
    hidden_content: Optional[List[str]] = None
    sentence_frames: Optional[List[Dict[str, str]]] = (
        None  # [{portuguese: str, english: str}]
    )
    materials_needed: Optional[List[str]] = None
    vocabulary_cognates: Optional[List[Dict[str, Any]]] = None


class LessonStepResponse(BaseModel):
    """Response with lesson step data."""

    id: str
    lesson_plan_id: str
    day_of_week: str
    slot_number: int
    step_number: int
    step_name: str
    duration_minutes: int
    start_time_offset: int
    content_type: str
    display_content: str
    hidden_content: Optional[List[str]] = None
    sentence_frames: Optional[List[Dict[str, str]]] = None
    materials_needed: Optional[List[str]] = None
    vocabulary_cognates: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LessonPlanDetailResponse(BaseModel):
    """Response with full lesson plan JSON."""

    id: str
    user_id: str
    week_of: str
    lesson_json: Dict[str, Any]
    status: str
    generated_at: datetime
    output_file: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Lesson Mode Session Models


class LessonModeSessionCreate(BaseModel):
    """Request to create or update a lesson mode session."""

    user_id: str
    lesson_plan_id: str
    schedule_entry_id: Optional[str] = None
    day_of_week: str
    slot_number: int
    current_step_index: int = 0
    remaining_time: int = 0  # seconds
    is_running: bool = False
    is_paused: bool = False
    is_synced: bool = False
    timer_start_time: Optional[datetime] = None
    paused_at: Optional[int] = None
    adjusted_durations: Optional[Dict[str, int]] = None


class LessonModeSessionResponse(BaseModel):
    """Response with lesson mode session data."""

    id: str
    user_id: str
    lesson_plan_id: str
    schedule_entry_id: Optional[str] = None
    day_of_week: str
    slot_number: int
    current_step_index: int
    remaining_time: int
    is_running: bool
    is_paused: bool
    is_synced: bool
    timer_start_time: Optional[Union[datetime, str]] = None
    paused_at: Optional[int] = None
    adjusted_durations: Optional[Dict[str, int]] = None
    session_start_time: Union[datetime, str]
    last_updated: Union[datetime, str]
    ended_at: Optional[Union[datetime, str]] = None

    @field_validator('session_start_time', 'last_updated', 'ended_at', 'timer_start_time', mode='after')
    @classmethod
    def serialize_datetime(cls, v: Any) -> Optional[str]:
        """Convert datetime objects to ISO format strings immediately upon validation."""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)

    model_config = ConfigDict(from_attributes=True)
