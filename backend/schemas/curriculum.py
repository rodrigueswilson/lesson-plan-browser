"""OpenAPI models for curriculum routes (lesson detail SSOT for generated clients)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ExplorerUnit(BaseModel):
    id: str
    title: str
    number: int


class ExplorerSubject(BaseModel):
    name: str
    units: List[ExplorerUnit]


class ExplorerGrade(BaseModel):
    name: str
    subjects: List[ExplorerSubject]


class CurriculumLessonSummary(BaseModel):
    id: str
    lesson_number: int
    title: str


class CurriculumLessonDetail(BaseModel):
    """Fields persisted on `lessons` (see tools/db/initialize_db.py)."""

    model_config = ConfigDict(extra="allow")

    id: str
    unit_id: str
    lesson_number: int
    title: str
    learning_intentions: Optional[str] = None
    daily_instructional_task: Optional[str] = None
    success_criteria: Optional[str] = None
    essential_questions: Optional[str] = None
    procedure: Optional[str] = None
    materials: Optional[str] = None
    lesson_narrative: Optional[str] = None
    instructional_resources: Optional[str] = None
    purpose: Optional[str] = None
    mlr: Optional[str] = None
    objectives_student: Optional[str] = None
    procedure_html: Optional[str] = None
    narrative_html: Optional[str] = None
    vocabulary: Optional[str] = None
    practices: Optional[str] = None
    procedures: Optional[str] = None
    differentiation: Optional[str] = None
    standards_structured: Optional[str] = Field(
        default=None,
        description="JSON array of {panel, section, code, description_lines[]}",
    )
    ela_key_learning_summary: Optional[str] = Field(
        default=None,
        description="JSON from unit Summary of Key Learning matrix (ELA ingest).",
    )
    ela_lesson_plan_structured: Optional[str] = Field(
        default=None,
        description="JSON from per-lesson detailed ELA plan table (ELA ingest).",
    )
    source_doc_id: Optional[str] = None
    source_url: Optional[str] = None
    ingested_at: Optional[str] = None
    ingest_run_id: Optional[str] = None
    ingest_parser_version: Optional[str] = None
    content_hash: Optional[str] = None


class CurriculumVocabularyTerm(BaseModel):
    term: str
    translated_term: str
    leveled_definitions: List[Dict[str, Any]]


class CurriculumStandardRow(BaseModel):
    code: str
    description: Optional[str] = None
    subject: Optional[str] = None


class CurriculumSearchHit(BaseModel):
    id: str
    unit_id: str
    lesson_number: int
    title: str


class CurriculumGapsResponse(BaseModel):
    total_planned_doc_refs: int
    gap_doc_refs: int
    gaps: Dict[str, Any] = Field(
        default_factory=dict,
        description="Nested grade -> subject -> unit -> lesson -> {doc_id: title}",
    )


class UnitIntroResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    unit_id: Optional[str] = None
    essential_questions: Optional[str] = None
    enduring_understandings: Optional[str] = None
    procedure_html: Optional[str] = None
    narrative_html: Optional[str] = None
    source_doc_id: Optional[str] = None
    source_url: Optional[str] = None
    ingested_at: Optional[str] = None
    ingest_run_id: Optional[str] = None
    ingest_parser_version: Optional[str] = None
