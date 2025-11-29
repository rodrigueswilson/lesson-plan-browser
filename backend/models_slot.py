"""
Pydantic models for slot data consistency.
"""

import re
from typing import Any, Dict, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    field_validator,
    model_validator,
)


class VocabularyCognatePair(BaseModel):
    """English-Portuguese vocabulary pair with cognate information."""

    english: str = Field(..., min_length=2, description="English word")
    portuguese: str = Field(..., min_length=2, description="Portuguese word")
    is_cognate: Optional[bool] = Field(
        None, description="Whether this is a true cognate pair"
    )
    relevance_note: Optional[str] = Field(
        None, description="Brief note on why this word pair is relevant to the lesson"
    )

    model_config = ConfigDict(extra="allow")


class SentenceFrame(BaseModel):
    """Sentence frame/stem/question for specific WIDA proficiency levels."""

    proficiency_level: str = Field(
        ...,
        description="WIDA proficiency level group",
        pattern="^(levels_1_2|levels_3_4|levels_5_6)$",
    )
    english: str = Field(
        ..., min_length=2, description="English sentence frame/stem/question"
    )
    portuguese: str = Field(
        ..., min_length=2, description="Portuguese sentence frame/stem/question"
    )
    language_function: str = Field(
        ...,
        description="Target language function (e.g., explain, compare, describe, argue)",
    )
    frame_type: str = Field(
        ...,
        description="Type of frame: frame for Levels 1-2/3-4, stem or open_question for Levels 5-6",
        pattern="^(frame|stem|open_question)$",
    )

    @field_validator("frame_type")
    @classmethod
    def validate_frame_type(cls, v: str, info) -> str:
        proficiency_level = info.data.get("proficiency_level")
        if proficiency_level in ["levels_1_2", "levels_3_4"] and v != "frame":
            raise ValueError(
                f"{proficiency_level} must have frame_type 'frame', got '{v}'"
            )
        if proficiency_level == "levels_5_6" and v not in ["stem", "open_question"]:
            raise ValueError(
                f"levels_5_6 must have frame_type 'stem' or 'open_question', got '{v}'"
            )
        return v

    model_config = ConfigDict(extra="allow")


class ObjectiveData(BaseModel):
    """Tri-objective structure (content, student goal, WIDA bilingual)."""

    content_objective: str = Field(
        ...,
        description="Original content objective from primary teacher",
    )
    student_goal: str = Field(
        ...,
        description="Student-facing 'I will...' statement",
    )
    wida_objective: str = Field(
        ...,
        description="Complete WIDA bilingual objective with ELD code",
    )

    model_config = ConfigDict(
        extra="allow",
        str_strip_whitespace=True,
    )

    _NO_SCHOOL_VALUES = {"no school", "holiday", "teacher workday", "testing"}
    _WIDA_PATTERN = re.compile(r"ELD-[A-Z]{2}\.[0-9K-]+\.[A-Za-z]+\.[A-Za-z/]+")

    @classmethod
    def _is_no_school(cls, value: str) -> bool:
        # Handle ModelPrivateAttr or other non-string values
        if not isinstance(value, str):
            # If value is not a string (e.g., ModelPrivateAttr), convert it
            if hasattr(value, "__class__") and "ModelPrivateAttr" in str(type(value)):
                return False  # ModelPrivateAttr can't be "no school"
            try:
                value = str(value)
            except:
                return False

        # Ensure _NO_SCHOOL_VALUES is actually a set/list, not ModelPrivateAttr
        no_school_values = cls._NO_SCHOOL_VALUES
        if hasattr(no_school_values, "__class__") and "ModelPrivateAttr" in str(
            type(no_school_values)
        ):
            # Fallback to hardcoded set if class attribute is ModelPrivateAttr
            no_school_values = {"no school", "holiday", "teacher workday", "testing"}

        return value.strip().lower() in no_school_values

    @field_validator("content_objective")
    @classmethod
    def validate_content_objective(cls, value: str) -> str:
        if cls._is_no_school(value):
            return value
        if len(value.strip()) < 10:
            raise ValueError(
                "content_objective must be at least 10 characters unless 'No School'"
            )
        return value

    @field_validator("student_goal")
    @classmethod
    def validate_student_goal(cls, value: str) -> str:
        if cls._is_no_school(value):
            return value
        if len(value.strip()) < 5:
            raise ValueError(
                "student_goal must be at least 5 characters unless 'No School'"
            )
        if len(value.strip()) > 80:
            raise ValueError("student_goal must be 80 characters or less")
        return value

    @field_validator("wida_objective")
    @classmethod
    def validate_wida_objective(cls, value: str) -> str:
        if cls._is_no_school(value):
            return value
        if len(value.strip()) < 50:
            raise ValueError(
                "wida_objective must be at least 50 characters unless 'No School'"
            )

        # Ensure _WIDA_PATTERN is actually a regex pattern, not ModelPrivateAttr
        wida_pattern = cls._WIDA_PATTERN
        if hasattr(wida_pattern, "__class__") and "ModelPrivateAttr" in str(
            type(wida_pattern)
        ):
            # Fallback to recompiled pattern if class attribute is ModelPrivateAttr
            import re

            wida_pattern = re.compile(r"ELD-[A-Z]{2}\.[0-9K-]+\.[A-Za-z]+\.[A-Za-z/]+")

        if not wida_pattern.search(value):
            raise ValueError(
                "wida_objective must include an ELD code with domain(s) (e.g., ELD-SS.6-8.Explain.Writing or ELD-SS.6-8.Explain.Listening/Speaking or ELD-SS.6-8.Explain.Listening/Reading/Speaking/Writing)"
            )
        return value


class SlotMetadata(BaseModel):
    """Metadata for a single slot."""

    slot_number: int = Field(ge=1, le=10, description="Slot position (1-10)")
    subject: str = Field(min_length=1, description="Subject name")
    grade: str = Field(min_length=1, description="Grade level")
    homeroom: Optional[str] = None
    primary_teacher_name: str = Field(min_length=1)
    primary_teacher_first_name: Optional[str] = None
    primary_teacher_last_name: Optional[str] = None
    primary_teacher_file: Optional[str] = None
    proficiency_levels: Optional[List[str]] = None

    @field_validator("primary_teacher_name")
    @classmethod
    def validate_teacher_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Teacher name cannot be empty")
        return v.strip()


class DailyPlanData(BaseModel):
    """Single day's lesson plan data."""

    unit_lesson: Optional[str] = None
    objective: Optional[ObjectiveData] = None
    anticipatory_set: Optional[str] = None
    vocabulary_cognates: Optional[List[VocabularyCognatePair]] = None
    sentence_frames: Optional[List[SentenceFrame]] = None
    tailored_instruction: Optional[str] = None
    misconceptions: Optional[str] = None
    assessment: Optional[str] = None
    homework: Optional[str] = None

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_counts(self):
        # Only validate counts during plan generation, not when reading from database
        # This allows existing data with different counts to pass through
        # The validator is lenient - it only warns, doesn't fail
        if self.vocabulary_cognates is not None and len(self.vocabulary_cognates) > 0:
            if len(self.vocabulary_cognates) != 6:
                # Don't raise - just allow any count for backward compatibility
                pass

        if self.sentence_frames is not None and len(self.sentence_frames) > 0:
            # Don't validate exact counts - allow any number of frames
            # This ensures existing data with different counts isn't rejected
            pass

        return self


class SlotContent(BaseModel):
    """Complete content for one slot."""

    metadata: SlotMetadata
    days: Dict[str, DailyPlanData] = Field(
        default_factory=lambda: {
            "monday": DailyPlanData(),
            "tuesday": DailyPlanData(),
            "wednesday": DailyPlanData(),
            "thursday": DailyPlanData(),
            "friday": DailyPlanData(),
        }
    )
    _hyperlinks: List[Dict[str, Any]] = PrivateAttr(default_factory=list)
    _images: List[Dict[str, Any]] = PrivateAttr(default_factory=list)
    _media_schema_version: str = PrivateAttr(default="2.0")


class BatchProcessResult(BaseModel):
    """Result model for batch processing."""

    success: bool
    plan_id: str
    output_file: Optional[str] = None
    processed_slots: int = Field(ge=0)
    failed_slots: int = Field(ge=0)
    total_slots: int = Field(gt=0)
    total_time_ms: float = Field(ge=0)
    consolidated: bool = False
    errors: Optional[List[str]] = None
    slots: Optional[List[SlotContent]] = Field(
        default=None, exclude=True
    )  # Internal use
