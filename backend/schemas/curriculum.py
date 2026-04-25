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
    science_doc_lesson_number: Optional[int] = Field(
        default=None,
        description="Curriculum-writer lesson number from Science DOCX module heading.",
    )
    science_li_sc_day_structured: Optional[str] = Field(
        default=None,
        description="JSON: Learning intention / success criteria by day segment (Science ingest).",
    )


class CurriculumScienceOutlineSegment(BaseModel):
    """Label-only row for module-level Science day-band index (no HTML)."""

    segment_index: int
    day_label: str


class CurriculumScienceOutlineLesson(BaseModel):
    lesson_id: str
    lesson_number: int
    title: str
    segments: List[CurriculumScienceOutlineSegment] = Field(default_factory=list)


class CurriculumUnitScienceDayOutline(BaseModel):
    """Writer cluster index for one unit (Science); not a calendar projection."""

    unit_id: str
    lessons: List[CurriculumScienceOutlineLesson] = Field(default_factory=list)
    total_writer_bands: int = 0


class CurriculumScienceDaySegment(BaseModel):
    """One writer day band for Science (relational; mirrors a segment in science_li_sc_day_structured)."""

    id: str
    lesson_id: str
    segment_index: int
    day_label: str
    science_doc_lesson_number: Optional[int] = None
    learning_intention_html: Optional[str] = None
    success_criteria_html: Optional[str] = None
    brief_overview_html: Optional[str] = None
    lesson_in_action_html: Optional[str] = None
    experimental_splits_json: Optional[str] = Field(
        default=None,
        description="JSON object with opening_html, during_html, closing_html, online_html when present.",
    )


class CurriculumBookLessonSupplement(BaseModel):
    """Student workbook / paired-read complement for one canonical Grade 2 Science lesson (see ADR-003)."""

    lesson_id: str
    source_pdf_label: str
    isbn13: Optional[str] = None
    pdf_page_start: Optional[int] = None
    pdf_page_end: Optional[int] = None
    pdf_title_hit_count: Optional[int] = None
    first_page_workbook_pattern: Optional[str] = None
    paired_read_block_title: Optional[str] = None
    teacher_curriculum_cue: Optional[str] = None
    format_notes: Optional[str] = None
    updated_at: Optional[str] = None


class CurriculumBookPageExtract(BaseModel):
    """One PDF page of student workbook text linked to a canonical lesson (g2_science_book_lesson_extract)."""

    id: str
    lesson_id: str
    page_number: int
    body_text: str
    char_count: Optional[int] = None
    content_sha256: Optional[str] = None
    alignment_confidence: str = "high"
    alignment_ambiguous: int = 0
    source_pdf_label: str
    ingest_parser_version: str
    ingested_at: Optional[str] = None


class CurriculumVocabularyTerm(BaseModel):
    term: str
    translated_term: str
    leveled_definitions: List[Dict[str, Any]]


class CurriculumStandardRow(BaseModel):
    code: str
    description: Optional[str] = None
    subject: Optional[str] = None


class CurriculumLessonBundle(BaseModel):
    """Single response for explorer: lesson row plus joined vocabulary and standards."""

    lesson: CurriculumLessonDetail
    vocabulary: List[CurriculumVocabularyTerm] = Field(default_factory=list)
    standards: List[CurriculumStandardRow] = Field(default_factory=list)
    science_day_segments: List[CurriculumScienceDaySegment] = Field(default_factory=list)
    book_lesson_supplement: Optional[CurriculumBookLessonSupplement] = Field(
        default=None,
        description="Inspire Grade 2 student workbook cross-reference when seeded (g2_science_book_lesson_supplement).",
    )
    book_page_extracts: List[CurriculumBookPageExtract] = Field(
        default_factory=list,
        description="Student workbook PDF text pages when include_book_extracts=true (capped).",
    )


class CurriculumSearchHit(BaseModel):
    id: str
    unit_id: str
    lesson_number: int
    title: str
    snippet_html: Optional[str] = Field(
        default=None,
        description="FTS5 snippet with <mark> around hits (body column); null when using LIKE fallback.",
    )
    fts_rank: Optional[float] = Field(
        default=None,
        description="BM25 rank when FTS used (lower is better); null for LIKE fallback.",
    )


class SemanticUnitLinkRow(BaseModel):
    """Manual curator link and/or adjacent-grade suggestion for cross-unit navigation."""

    id: Optional[str] = Field(default=None, description="Primary key when source=manual.")
    to_unit_id: str
    to_unit_title: str
    to_grade: Optional[int] = None
    to_unit_number: Optional[int] = None
    link_kind: str
    rationale: str
    source: str = Field(description="manual | suggested")


class CurriculumGapsResponse(BaseModel):
    total_planned_doc_refs: int
    gap_doc_refs: int
    gaps: Dict[str, Any] = Field(
        default_factory=dict,
        description="Nested grade -> subject -> unit -> lesson -> {doc_id: title}",
    )


class CurriculumResourceResolve(BaseModel):
    """Preferred URL to open a linked Google Doc (local file route vs original URL)."""

    url: str
    source: str = Field(description="local | remote | remote_inferred")


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
