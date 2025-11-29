"""
Fix all plans in the database that have vocabulary_cognates and sentence_frames in lesson_json
but don't have them properly saved in the lesson_steps.
"""

import sys
from pathlib import Path

import requests

sys.path.append(str(Path(__file__).parent))

from backend.database import get_db

API_BASE = "http://localhost:8000/api"

# Get user
users_response = requests.get(f"{API_BASE}/users")
users = users_response.json()
user_id = next(u["id"] for u in users if "Wilson" in u.get("name", ""))

# Get all plans for user
plans_response = requests.get(
    f"{API_BASE}/users/{user_id}/plans", headers={"X-Current-User-Id": user_id}
)
plans = plans_response.json()

print(f"Found {len(plans)} plans for user")

db = get_db()
fixed_count = 0

for plan in plans:
    plan_id = plan["id"]

    # Get plan detail
    detail_response = requests.get(
        f"{API_BASE}/plans/{plan_id}", headers={"X-Current-User-Id": user_id}
    )

    if detail_response.status_code != 200:
        continue

    detail = detail_response.json()
    lesson_json = detail.get("lesson_json", {})

    if not lesson_json:
        continue

    # Check if plan has vocabulary/frames in lesson_json
    days = lesson_json.get("days", {})
    monday = days.get("monday", {})
    slots = monday.get("slots", [])
    slot1 = next((s for s in slots if s.get("slot_number") == 1), None)

    if not slot1:
        continue

    vocab = slot1.get("vocabulary_cognates", [])
    frames = slot1.get("sentence_frames", [])

    if not vocab or not isinstance(vocab, list) or len(vocab) == 0:
        continue
    if not frames or not isinstance(frames, list) or len(frames) == 0:
        continue

    print(f"\nPlan {plan_id} has vocabulary/frames in lesson_json")
    print(f"  vocabulary_cognates: {len(vocab)} items")
    print(f"  sentence_frames: {len(frames)} items")

    # Check if steps exist and need fixing
    steps = db.get_lesson_steps(plan_id, day_of_week="monday", slot_number=1)

    if not steps:
        print("  No steps found - will be generated on next access")
        continue

    # Find vocabulary and frames steps
    vocab_step = next((s for s in steps if "vocabulary" in s.step_name.lower()), None)
    frames_step = next((s for s in steps if s.content_type == "sentence_frames"), None)

    # Fix vocabulary step
    if vocab_step:
        if not vocab_step.vocabulary_cognates or (
            isinstance(vocab_step.vocabulary_cognates, list)
            and len(vocab_step.vocabulary_cognates) == 0
        ):
            print(f"  Fixing vocabulary step: {vocab_step.id}")
            from sqlmodel import Session

            from backend.schema import LessonStep

            with Session(db.engine) as session:
                step = session.get(LessonStep, vocab_step.id)
                if step:
                    step.vocabulary_cognates = vocab
                    session.add(step)
                    session.commit()
                    print("    [OK] Updated vocabulary_cognates")
                    fixed_count += 1
    else:
        print("  No vocabulary step found - will be generated on next access")

    # Fix frames step
    if frames_step:
        if not frames_step.sentence_frames or (
            isinstance(frames_step.sentence_frames, list)
            and len(frames_step.sentence_frames) == 0
        ):
            print(f"  Fixing sentence frames step: {frames_step.id}")
            from sqlmodel import Session

            from backend.schema import LessonStep

            with Session(db.engine) as session:
                step = session.get(LessonStep, frames_step.id)
                if step:
                    step.sentence_frames = frames
                    session.add(step)
                    session.commit()
                    print("    [OK] Updated sentence_frames")
                    fixed_count += 1
    else:
        print("  No sentence frames step found - will be generated on next access")

print(f"\n{'=' * 60}")
print(f"Fixed {fixed_count} steps across all plans")
print(f"{'=' * 60}")
