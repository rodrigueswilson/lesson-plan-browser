"""One-off script to extract users/slots/schedules from api.py into backend/routers/users.py."""
from pathlib import Path

api_path = Path(__file__).resolve().parent.parent / "backend" / "api.py"
api = api_path.read_text(encoding="utf-8")
lines = api.splitlines()
block = lines[940:2212]
text = "\n".join(block)
text = text.replace("@app.", "@router.")
text = text.replace('"/api/users"', '"/users"')
text = text.replace('"/api/recent-weeks"', '"/recent-weeks"')
text = text.replace('"/api/users/{user_id}"', '"/users/{user_id}"')
text = text.replace('"/api/users/{user_id}/base-path"', '"/users/{user_id}/base-path"')
text = text.replace('"/api/users/{user_id}/template-paths"', '"/users/{user_id}/template-paths"')
text = text.replace('"/api/slots/{slot_id}"', '"/slots/{slot_id}"')
text = text.replace('"/api/schedules"', '"/schedules"')
text = text.replace('"/api/schedules/{user_id}"', '"/schedules/{user_id}"')
text = text.replace('"/api/schedules/{user_id}/current"', '"/schedules/{user_id}/current"')
text = text.replace('"/api/schedules/{schedule_id}"', '"/schedules/{schedule_id}"')
text = text.replace('"/api/schedules/{user_id}/bulk"', '"/schedules/{user_id}/bulk"')
text = text.replace('"/api/users/{user_id}/slots",', '"/users/{user_id}/slots",')

header = '''"""
Users, class slots, and schedules API endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.authorization import get_current_user_id, verify_slot_ownership, verify_user_access
from backend.config import settings
from backend.database import get_db
from backend.models import (
    ClassSlotCreate,
    ClassSlotResponse,
    ClassSlotUpdate,
    ScheduleBulkCreateRequest,
    ScheduleBulkCreateResponse,
    ScheduleEntryCreate,
    ScheduleEntryResponse,
    ScheduleEntryUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from backend.rate_limiter import rate_limit_auth, rate_limit_general
from backend.telemetry import logger
from backend.utils.schedule_utils import prepare_schedule_entry
from backend.week_detector import detect_weeks_from_folder, format_week_display

router = APIRouter()

'''

out = header + text
out_path = Path(__file__).resolve().parent.parent / "backend" / "routers" / "users.py"
out_path.write_text(out, encoding="utf-8")
print("Written", out_path)
