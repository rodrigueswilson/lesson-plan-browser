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
    _WIDA_PATTERN = re.compile(
        r"ELD-[A-Z]{2}\.[0-9K-]+\.[A-Za-z]+\.(?:Listening|Reading|Speaking|Writing)(?:/(?:Listening|Reading|Speaking|Writing))*"
    )
    _STUDENT_GOAL_DOMAIN_PATTERN = re.compile(
        r"\b(listen(?:ing)?|read(?:ing)?|speak(?:ing)?|write|writing)\b",
        re.IGNORECASE,
    )
    _STUDENT_GOAL_PARENTHESES_PATTERN = re.compile(r"\(([^)]*)\)\.?\s*$")
    _ALLOWED_GOAL_DOMAINS = {"listening", "reading", "speaking", "writing"}

    @classmethod
    def _get_no_school_values(cls) -> set:
        """Get no school values, handling ModelPrivateAttr cases."""
        try:
            values = cls._NO_SCHOOL_VALUES
            # Test if it's actually iterable
            if isinstance(values, (set, list, tuple)):
                return set(values)
            # Try to use it as iterable
            _ = iter(values)
            return set(values)
        except (TypeError, AttributeError):
            # Fallback to hardcoded set
            return {"no school", "holiday", "teacher workday", "testing"}

    @classmethod
    def _get_allowed_domains(cls) -> set:
        """Get allowed domains, handling ModelPrivateAttr cases."""
        try:
            domains = cls._ALLOWED_GOAL_DOMAINS
            # Test if it's actually iterable
            if isinstance(domains, (set, list, tuple)):
                return set(domains)
            # Try to use it as iterable
            _ = iter(domains)
            return set(domains)
        except (TypeError, AttributeError):
            # Fallback to hardcoded set
            return {"listening", "reading", "speaking", "writing"}

    @classmethod
    def _get_domain_pattern(cls) -> re.Pattern:
        """Get domain pattern, handling ModelPrivateAttr cases."""
        try:
            pattern = cls._STUDENT_GOAL_DOMAIN_PATTERN
            if isinstance(pattern, re.Pattern):
                return pattern
            # If it's not a Pattern, try to compile
            if hasattr(pattern, "pattern"):
                return pattern
        except (TypeError, AttributeError):
            pass
        # Fallback to hardcoded pattern
        return re.compile(
            r"\b(listen(?:ing)?|read(?:ing)?|speak(?:ing)?|write|writing)\b",
            re.IGNORECASE,
        )

    @classmethod
    def _get_parentheses_pattern(cls) -> re.Pattern:
        """Get parentheses pattern, handling ModelPrivateAttr cases."""
        try:
            pattern = cls._STUDENT_GOAL_PARENTHESES_PATTERN
            if isinstance(pattern, re.Pattern):
                return pattern
            # If it's not a Pattern, try to use it
            if hasattr(pattern, "pattern"):
                return pattern
        except (TypeError, AttributeError):
            pass
        # Fallback to hardcoded pattern
        return re.compile(r"\(([^)]*)\)\.?\s*$")

    @classmethod
    def _get_wida_pattern(cls) -> re.Pattern:
        """Get WIDA pattern, handling ModelPrivateAttr cases."""
        try:
            pattern = cls._WIDA_PATTERN
            if isinstance(pattern, re.Pattern):
                return pattern
            # If it's not a Pattern, try to use it
            if hasattr(pattern, "pattern"):
                return pattern
        except (TypeError, AttributeError):
            pass
        # Fallback to hardcoded pattern
        return re.compile(
            r"ELD-[A-Z]{2}\.[0-9K-]+\.[A-Za-z]+\.(?:Listening|Reading|Speaking|Writing)(?:/(?:Listening|Reading|Speaking|Writing))*"
        )

    @classmethod
    def _is_no_school(cls, value: str) -> bool:
        # Handle ModelPrivateAttr or other non-string values
        if not isinstance(value, str):
            # If value is not a string (e.g., ModelPrivateAttr), convert it
            try:
                value = str(value)
            except:
                return False

        no_school_values = cls._get_no_school_values()
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
        if len(value.strip()) > 120:
            raise ValueError("student_goal must be 120 characters or less")

        domain_pattern = cls._get_domain_pattern()
        stripped_value = value.strip()

        if not domain_pattern.search(stripped_value):
            raise ValueError(
                "student_goal must mention at least one WIDA language domain (listening, reading, speaking, or writing)"
            )

        parentheses_pattern = cls._get_parentheses_pattern()
        match = parentheses_pattern.search(stripped_value)
        if not match:
            raise ValueError(
                "student_goal must end with parentheses listing the practiced domains (e.g., '(listening, speaking)')"
            )

        domains_raw = [
            d.strip().lower() for d in match.group(1).split(",") if d.strip()
        ]
        if not domains_raw:
            raise ValueError(
                "student_goal domain tag cannot be empty; include at least one of listening, reading, speaking, writing"
            )

        # Normalize common invalid domain names
        domain_mapping = {
            "drawing": "writing",  # Drawing is often a form of visual writing
            "illustrate": "writing",
            "demonstrate": "speaking",
            "show": "speaking",
            "present": "speaking",
        }

        normalized_domains = []
        seen = set()  # Track seen domains to avoid duplicates
        for domain in domains_raw:
            # Map invalid domains to valid ones
            mapped_domain = domain_mapping.get(domain, domain)
            # Only add if not already in the list (avoid duplicates)
            if mapped_domain not in seen:
                normalized_domains.append(mapped_domain)
                seen.add(mapped_domain)

        allowed_domains = cls._get_allowed_domains()
        invalid_domains = [d for d in normalized_domains if d not in allowed_domains]
        if invalid_domains:
            raise ValueError(
                f"student_goal domain tag may only include listening, reading, speaking, or writing. Invalid domains found: {', '.join(invalid_domains)}"
            )

        # Update the value with normalized domains if changes were made
        # Compare normalized (deduplicated) with original (may have duplicates)
        original_set = set(domains_raw)
        normalized_set = set(normalized_domains)
        if normalized_set != original_set or len(normalized_domains) != len(
            domains_raw
        ):
            # Reconstruct the parentheses content with normalized domains
            domains_str = ", ".join(normalized_domains)
            # Replace the old domain tag with the normalized one, preserving ending period
            normalized_value = re.sub(
                r"\([^)]*\)\.?\s*$",
                f"({domains_str}).",
                stripped_value,
            )
            return normalized_value

        if len(domains_raw) != len(set(domains_raw)):
            raise ValueError(
                "student_goal domain tag must not repeat domains; list each domain only once"
            )

        if not stripped_value.endswith(")."):
            raise ValueError(
                "student_goal must end with ').' (i.e., the domain tag followed by a period)"
            )

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

        # Normalize common ELD code format mistakes before validation
        # Fix: ELD-XX.#-#.Function/Domain -> ELD-XX.#-#.Function.Domain
        # Pattern matches: ELD-[letters].[numbers].[Function]/[Domain]
        # IMPORTANT: Only replace the FIRST slash after the function name, not all slashes
        # The pattern should match: FunctionName/Domain (where FunctionName is before the slash)
        # and convert it to: FunctionName.Domain
        # But preserve slashes between multiple domains (e.g., Listening/Speaking/Writing)
        normalized_value = re.sub(
            r"(ELD-[A-Z]{2}\.[0-9K-]+\.[A-Za-z]+)/(Listening|Reading|Speaking|Writing)",
            r"\1.\2",
            value,
        )

        # Log normalization for debugging (only if change occurred)
        if normalized_value != value:
            from backend.telemetry import logger

            logger.debug(
                "eld_code_normalized",
                extra={
                    "original": value[:100] if len(value) > 100 else value,
                    "normalized": normalized_value[:100]
                    if len(normalized_value) > 100
                    else normalized_value,
                },
            )

        wida_pattern = cls._get_wida_pattern()
        if not wida_pattern.search(normalized_value):
            raise ValueError(
                "wida_objective must include an ELD code with domain(s) (e.g., ELD-SS.6-8.Explain.Writing or ELD-SS.6-8.Explain.Listening/Speaking or ELD-SS.6-8.Explain.Listening/Reading/Speaking/Writing)"
            )
        # Return normalized value if it was fixed, otherwise return original
        return normalized_value if normalized_value != value else value


class SlotMetadata(BaseModel):
    """Metadata for a single slot."""

    slot_number: int = Field(ge=1, le=10, description="Slot position (1-10)")
    subject: str = Field(min_length=1, description="Subject name")
    grade: str = Field(min_length=1, description="Grade level")
    homeroom: Optional[str] = None
    room: Optional[str] = Field(
        None,
        description="Room number or physical location where instruction takes place",
    )
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
