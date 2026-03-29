import os
import re
import sqlite3
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from backend.config import settings
from backend.database.curriculum import CurriculumDatabase
from backend.database.curriculum_validation import get_curriculum_schema_issues
from backend.schemas.curriculum import (
    CurriculumGapsResponse,
    CurriculumLessonDetail,
    CurriculumResourceResolve,
    CurriculumSearchHit,
    CurriculumStandardRow,
    CurriculumVocabularyTerm,
    ExplorerGrade,
    SemanticUnitLinkRow,
)
from backend.services.curriculum_gaps import compute_planned_and_gaps
from backend.services.curriculum_resource_resolve import (
    media_type_for_curriculum_path,
    resolve_resource_open_url,
    validated_local_file_path,
)

router = APIRouter(tags=["curriculum"])


def require_curriculum_schema() -> None:
    issues = get_curriculum_schema_issues()
    if issues:
        raise HTTPException(
            status_code=503,
            detail={"curriculum_schema_errors": issues},
        )


CURRICULUM_DEPS = [Depends(require_curriculum_schema)]


@router.get("/curriculum/explorer", dependencies=CURRICULUM_DEPS, response_model=List[ExplorerGrade])
async def get_explorer():
    """Returns the Grade -> Subject -> Unit hierarchy."""
    curriculum = CurriculumDatabase()
    return curriculum.get_explorer_hierarchy()


@router.get("/curriculum/registry-tree", dependencies=CURRICULUM_DEPS)
async def get_registry_tree() -> Dict[str, Any]:
    """Static Grade -> Subject -> Unit -> {doc_id: title} from scraped_registry.json (Navigator phase 1)."""
    curriculum = CurriculumDatabase()
    data = curriculum.load_scraped_registry()
    if not data:
        raise HTTPException(
            status_code=404,
            detail="scraped_registry.json not found or empty (set SCRAPED_REGISTRY_PATH?)",
        )
    return data


@router.get("/curriculum/search", dependencies=CURRICULUM_DEPS, response_model=List[CurriculumSearchHit])
async def search_curriculum(
    q: str = Query(..., min_length=2, description="FTS5 match on title / procedure / narrative HTML"),
    limit: int = Query(40, ge=1, le=200),
):
    """Lesson search via FTS5 (snippet + highlights) with LIKE fallback if FTS fails."""
    curriculum = CurriculumDatabase()
    return curriculum.search_lessons_text(q, limit=limit)


@router.get(
    "/curriculum/units/{unit_id}/semantic-links",
    dependencies=CURRICULUM_DEPS,
    response_model=List[SemanticUnitLinkRow],
)
async def get_unit_semantic_links(unit_id: str):
    """Manual cross-unit links plus same-subject adjacent-grade suggestions."""
    curriculum = CurriculumDatabase()
    return curriculum.get_unit_semantic_links(unit_id)


@router.get("/curriculum/units/{unit_id}/lessons", dependencies=CURRICULUM_DEPS)
async def get_unit_lessons(unit_id: str):
    """Returns all lessons for a specific unit."""
    curriculum = CurriculumDatabase()
    return curriculum.get_unit_lessons(unit_id)


@router.get("/curriculum/units/{unit_id}/intro", dependencies=CURRICULUM_DEPS)
async def get_unit_intro(unit_id: str):
    """Returns the unit introduction (overview)."""
    curriculum = CurriculumDatabase()
    return curriculum.get_unit_intro(unit_id)


@router.get(
    "/curriculum/lessons/{lesson_id}",
    dependencies=CURRICULUM_DEPS,
    response_model=CurriculumLessonDetail,
)
async def get_lesson_details(lesson_id: str):
    """Returns full details for a single lesson."""
    curriculum = CurriculumDatabase()
    details = curriculum.get_lesson_details(lesson_id)
    if not details:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return details


@router.get(
    "/curriculum/lessons/{lesson_id}/vocabulary",
    dependencies=CURRICULUM_DEPS,
    response_model=List[CurriculumVocabularyTerm],
)
async def get_lesson_vocabulary(lesson_id: str):
    """Returns enriched bilingual vocabulary for a lesson."""
    curriculum = CurriculumDatabase()
    return curriculum.get_lesson_vocabulary(lesson_id)


@router.get(
    "/curriculum/lessons/{lesson_id}/standards",
    dependencies=CURRICULUM_DEPS,
    response_model=List[CurriculumStandardRow],
)
async def get_lesson_standards(lesson_id: str):
    """Returns curriculum standards (codes and descriptions) linked to a lesson."""
    curriculum = CurriculumDatabase()
    return curriculum.get_lesson_standards(lesson_id)


@router.get(
    "/curriculum/gaps",
    dependencies=CURRICULUM_DEPS,
    response_model=CurriculumGapsResponse,
)
async def get_curriculum_gaps():
    """
    Compare Google Doc links in original_lesson_plans (lesson planner DB) to scraped_registry.json
    and reference_docs/scrapped_curriculum_doc_ids.json (intentional non-targets).
    Gap Manager UI can poll this endpoint; full ingestion triggers remain CLI/batch for now.
    """
    registry_path = str(CurriculumDatabase().scraped_registry_path())
    db_path = str(settings.SQLITE_DB_PATH)
    if not os.path.isfile(db_path):
        raise HTTPException(status_code=503, detail=f"lesson planner DB not found: {db_path}")
    try:
        _planned, gaps, total_found, gap_count = compute_planned_and_gaps(
            db_path, registry_path
        )
    except sqlite3.OperationalError as e:
        msg = str(e).lower()
        if "no such table" in msg:
            raise HTTPException(
                status_code=503,
                detail="Gap detection requires table original_lesson_plans in the lesson planner database.",
            ) from e
        raise HTTPException(status_code=503, detail=str(e)) from e
    return CurriculumGapsResponse(
        total_planned_doc_refs=total_found,
        gap_doc_refs=gap_count,
        gaps=gaps,
    )


_GOOGLE_DOC_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


@router.get(
    "/curriculum/resources/google-id/{google_id}/resolve",
    dependencies=CURRICULUM_DEPS,
    response_model=CurriculumResourceResolve,
)
async def resolve_curriculum_google_resource(google_id: str):
    """Local-first open URL for `data-resource-id` links in lesson HTML."""
    if not _GOOGLE_DOC_ID_RE.match(google_id or ""):
        raise HTTPException(status_code=400, detail="Invalid google_id")
    curriculum = CurriculumDatabase()
    row = curriculum.get_resource_by_id(google_id)
    url, source = resolve_resource_open_url(google_id, row)
    return CurriculumResourceResolve(url=url, source=source)


@router.get(
    "/curriculum/resources/google-id/{google_id}/file",
    dependencies=CURRICULUM_DEPS,
)
async def serve_curriculum_google_resource_file(google_id: str):
    """Stream local export when resources row and/or CURRICULUM_LOCAL_FILES_ROOT match."""
    if not _GOOGLE_DOC_ID_RE.match(google_id or ""):
        raise HTTPException(status_code=400, detail="Invalid google_id")
    curriculum = CurriculumDatabase()
    row = curriculum.get_resource_by_id(google_id)
    path = validated_local_file_path(google_id, row)
    if path is None:
        raise HTTPException(status_code=404, detail="Local file not available")
    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type=media_type_for_curriculum_path(path),
    )
