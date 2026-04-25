"""Extract plans/lesson-steps/lesson-mode/user-plans/status from api.py into backend/routers/plans.py."""
from pathlib import Path

api_path = Path(__file__).resolve().parent.parent / "backend" / "api.py"
lines = api_path.read_text(encoding="utf-8").splitlines()
# Lines 942-2942 (0-based 941-2942) = from "# Lesson Plan" through end of get_week_status
block = lines[941:2942]
text = "\n".join(block)
text = text.replace("@app.", "@router.")
# Paths: strip /api prefix so mount prefix="/api" gives same URLs
text = text.replace('"/api/plans/{plan_id}"', '"/plans/{plan_id}"')
text = text.replace('"/api/plans/{plan_id}/download"', '"/plans/{plan_id}/download"')
text = text.replace('"/api/lesson-steps/{plan_id}/{day}/{slot}"', '"/lesson-steps/{plan_id}/{day}/{slot}"')
text = text.replace('"/api/lesson-steps/generate"', '"/lesson-steps/generate"')
text = text.replace('"/api/lesson-mode/session"', '"/lesson-mode/session"')
text = text.replace('"/api/lesson-mode/session/active"', '"/lesson-mode/session/active"')
text = text.replace('"/api/lesson-mode/session/{session_id}"', '"/lesson-mode/session/{session_id}"')
text = text.replace('"/api/lesson-mode/session/{session_id}/end"', '"/lesson-mode/session/{session_id}/end"')
text = text.replace('"/api/users/{user_id}/plans"', '"/users/{user_id}/plans"')
text = text.replace('"/api/plans/status/{user_id}/{week_of}"', '"/plans/status/{user_id}/{week_of}"')
# Multi-line decorators
for old, new in [
    ('    "/api/plans/{plan_id}",', '    "/plans/{plan_id}",'),
    ('    "/api/plans/{plan_id}/download",', '    "/plans/{plan_id}/download",'),
    ('    "/api/lesson-steps/{plan_id}/{day}/{slot}",', '    "/lesson-steps/{plan_id}/{day}/{slot}",'),
    ('    "/api/lesson-steps/generate",', '    "/lesson-steps/generate",'),
    ('    "/api/lesson-mode/session",', '    "/lesson-mode/session",'),
    ('    "/api/lesson-mode/session/active",', '    "/lesson-mode/session/active",'),
    ('    "/api/lesson-mode/session/{session_id}",', '    "/lesson-mode/session/{session_id}",'),
    ('    "/api/users/{user_id}/plans",', '    "/users/{user_id}/plans",'),
    ('    "/api/plans/status/{user_id}/{week_of}",', '    "/plans/status/{user_id}/{week_of}",'),
]:
    text = text.replace(old, new)

header = '''"""
Plans, lesson steps, lesson mode, and week status API endpoints.
"""
import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from backend.authorization import get_current_user_id, verify_user_access
from backend.config import settings
from backend.database import get_db
from backend.models import (
    LessonModeSessionCreate,
    LessonModeSessionResponse,
    LessonPlanDetailResponse,
    LessonStepResponse,
    ScheduleEntryResponse,
    WeeklyPlanResponse,
    WeekStatusResponse,
)
from backend.rate_limiter import rate_limit_auth, rate_limit_general
from backend.telemetry import logger
from backend.utils.lesson_json_enricher import enrich_lesson_json_from_steps

router = APIRouter()

'''

out = header + text
out_path = Path(__file__).resolve().parent.parent / "backend" / "routers" / "plans.py"
out_path.write_text(out, encoding="utf-8")
print("Written", out_path)
