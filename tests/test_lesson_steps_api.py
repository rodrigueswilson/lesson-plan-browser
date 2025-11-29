"""
Integration tests for lesson-step endpoints.

Validates that:
1. /api/lesson-steps/generate creates rows from phase_plan data.
2. /api/lesson-steps/{plan_id}/{day}/{slot} returns JSON fields as lists/dicts.
3. Regeneration replaces existing steps via delete_lesson_steps.
"""

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api import app  # noqa: E402
from backend.database import get_db  # noqa: E402


def _seed_plan():
    """Create a weekly plan with minimal lesson_json for testing."""
    db = get_db()
    user_id = db.create_user(first_name="Lesson", last_name="Tester", email="lesson.tester@example.com")
    plan_id = db.create_weekly_plan(
        user_id=user_id,
        week_of="10/06-10/10",
        output_file="test.docx",
        week_folder_path="tests/output",
    )
    phase_plan = [
        {
            "phase_name": "Warmup",
            "duration_minutes": 5,
            "content_type": "instruction",
            "description": "Greet students and review objectives.",
            "sentence_frames": [{"portuguese": "Bom dia", "english": "Good morning"}],
            "materials": ["Objective slide"],
        },
        {
            "phase_name": "Guided Practice",
            "duration_minutes": 10,
            "content_type": "instruction",
            "description": "Model the target skill.",
            "sentence_frames": [{"portuguese": "Eu posso", "english": "I can"}],
            "materials": ["Whiteboard", "Markers"],
        },
    ]
    lesson_json = {
        "days": {
            "monday": {
                "unit_lesson": "Unit One Lesson Seven",
                "vocabulary_cognates": [
                    {"english": "law", "portuguese": "lei", "is_cognate": False},
                    {"english": "system", "portuguese": "sistema", "is_cognate": True},
                    {"english": "banking", "portuguese": "banco", "is_cognate": False},
                    {"english": "economy", "portuguese": "economia", "is_cognate": True},
                    {"english": "trade", "portuguese": "comércio", "is_cognate": False},
                    {"english": "peace", "portuguese": "paz", "is_cognate": False},
                ],
                "sentence_frames": [
                    {
                        "proficiency_level": "levels_1_2",
                        "english": "This is ___",
                        "portuguese": "Isto é ___",
                        "frame_type": "frame"
                    },
                    {
                        "proficiency_level": "levels_1_2",
                        "english": "I see ___",
                        "portuguese": "Eu vejo ___",
                        "frame_type": "frame"
                    },
                    {
                        "proficiency_level": "levels_1_2",
                        "english": "It has ___",
                        "portuguese": "Tem ___",
                        "frame_type": "frame"
                    },
                    {
                        "proficiency_level": "levels_3_4",
                        "english": "First ___, then ___",
                        "portuguese": "Primeiro ___, depois ___",
                        "frame_type": "frame"
                    },
                    {
                        "proficiency_level": "levels_3_4",
                        "english": "This shows ___ because ___",
                        "portuguese": "Isso mostra ___ porque ___",
                        "frame_type": "frame"
                    },
                    {
                        "proficiency_level": "levels_3_4",
                        "english": "I think ___ because ___",
                        "portuguese": "Eu acho ___ porque ___",
                        "frame_type": "frame"
                    },
                    {
                        "proficiency_level": "levels_5_6",
                        "english": "Evidence suggests that ___",
                        "portuguese": "As evidências sugerem que ___",
                        "frame_type": "stem"
                    },
                    {
                        "proficiency_level": "levels_5_6",
                        "english": "How does ___ relate to ___?",
                        "portuguese": "Como ___ se relaciona com ___?",
                        "frame_type": "open_question"
                    },
                ],
                "tailored_instruction": {
                    "co_teaching_model": {
                        "phase_plan": phase_plan,
                    }
                }
            }
        }
    }
    db.update_weekly_plan(plan_id, status="ready", lesson_json=lesson_json)
    return db, user_id, plan_id, lesson_json


@pytest.mark.anyio
async def test_lesson_steps_round_trip():
    """Ensure lesson-step generation persists JSON arrays correctly and is idempotent."""
    db, user_id, plan_id, lesson_json = _seed_plan()
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            # Initial generation
            response = await async_client.post(
                "/api/lesson-steps/generate",
                params={"plan_id": plan_id, "day": "monday", "slot": 1},
            )
            assert response.status_code == 200
            generated = response.json()
            assert len(generated) == 2
            assert generated[0]["step_name"] == "Warmup"
            assert isinstance(generated[0]["sentence_frames"], list)
            assert isinstance(generated[0]["sentence_frames"][0], dict)
            assert isinstance(generated[0]["materials_needed"], list)

            # Verify persisted records return structured JSON
            fetch = await async_client.get(f"/api/lesson-steps/{plan_id}/monday/1")
            assert fetch.status_code == 200
            stored = fetch.json()
            assert len(stored) == 2
            assert stored[0]["step_name"] == "Warmup"
            assert stored[0]["sentence_frames"][0]["english"] == "Good morning"
            assert stored[0]["materials_needed"][0] == "Objective slide"

            # Verify day-level sentence_frames are preserved in lesson_json
            plan_detail = await async_client.get(f"/api/plans/{plan_id}")
            assert plan_detail.status_code == 200
            plan_data = plan_detail.json()
            monday_data = plan_data["lesson_json"]["days"]["monday"]
            
            # Day-level sentence_frames should exist and have 8 items
            assert "sentence_frames" in monday_data
            assert len(monday_data["sentence_frames"]) == 8
            assert monday_data["sentence_frames"][0]["proficiency_level"] == "levels_1_2"
            assert monday_data["sentence_frames"][0]["frame_type"] == "frame"
            
            # Day-level vocabulary_cognates should exist and have 6 items
            assert "vocabulary_cognates" in monday_data
            assert len(monday_data["vocabulary_cognates"]) == 6
            assert monday_data["vocabulary_cognates"][0]["english"] == "law"
            assert monday_data["vocabulary_cognates"][0]["portuguese"] == "lei"
            
            # Phase-level sentence_frames should still work (different structure)
            phase_frames = monday_data["tailored_instruction"]["co_teaching_model"]["phase_plan"][0]["sentence_frames"]
            assert isinstance(phase_frames, list)
            assert phase_frames[0]["english"] == "Good morning"

            # Update plan JSON and ensure regeneration replaces old steps
            lesson_json["days"]["monday"]["tailored_instruction"]["co_teaching_model"]["phase_plan"][0][
                "phase_name"
            ] = "Revised Warmup"
            db.update_weekly_plan(plan_id, lesson_json=lesson_json)

            second_response = await async_client.post(
                "/api/lesson-steps/generate",
                params={"plan_id": plan_id, "day": "monday", "slot": 1},
            )
            assert second_response.status_code == 200
            regenerated = second_response.json()
            assert regenerated[0]["step_name"] == "Revised Warmup"

            second_fetch = await async_client.get(f"/api/lesson-steps/{plan_id}/monday/1")
            assert second_fetch.status_code == 200
            stored_after = second_fetch.json()
            assert len(stored_after) == 2
            assert stored_after[0]["step_name"] == "Revised Warmup"
    finally:
        db.delete_user(user_id)

