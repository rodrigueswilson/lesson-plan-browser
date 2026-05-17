"""Regression: transform stub branch when available_days is explicitly empty (Phase 7 plan)."""

from unittest.mock import MagicMock

import pytest

from tools.batch_processor_pkg.context import SlotProcessingContext
from tools.batch_processor_pkg.transform import transform_slot_with_llm
from tools.docx_parser.instructional_day import NON_INSTRUCTIONAL_UNIT_LESSON


@pytest.mark.asyncio
async def test_transform_skips_llm_when_available_days_empty_list():
    """Empty list means inferencer found zero instructional days -> non-instructional week stub."""
    processor = MagicMock()
    processor._user_first_name = ""
    processor._user_last_name = ""
    processor._user_name = ""
    processor._build_teacher_name.return_value = "Test Teacher"
    processor._no_school_day_stub.return_value = {"unit_lesson": "No School"}
    llm = MagicMock()
    processor.llm_service = llm

    slot = {
        "slot_number": 3,
        "subject": "Math",
        "grade": "2",
        "homeroom": "A",
    }
    ctx = SlotProcessingContext(
        slot=slot,
        slot_index=1,
        total_slots=1,
        extracted_content="primary text",
        available_days=[],
        no_school_days=None,
    )

    await transform_slot_with_llm(
        processor, ctx, "01/06-01/10/2026", "openai", plan_id=None
    )

    llm.transform_lesson.assert_not_called()
    assert ctx.lesson_json is not None
    assert ctx.lesson_json["days"]["monday"]["unit_lesson"] == NON_INSTRUCTIONAL_UNIT_LESSON
    assert ctx.lesson_json["days"]["friday"]["unit_lesson"] == NON_INSTRUCTIONAL_UNIT_LESSON


@pytest.mark.asyncio
async def test_transform_calls_llm_when_available_days_none(monkeypatch):
    """None means unknown/table absent semantics -> LLM path (mock successful transform)."""
    processor = MagicMock()
    processor._user_first_name = ""
    processor._user_last_name = ""
    processor._user_name = ""
    processor._build_teacher_name.return_value = "Test Teacher"
    processor._scrub_hyperlinks = MagicMock()

    minimal_lesson = {
        "metadata": {
            "teacher_name": "T",
            "grade": "2",
            "subject": "Math",
            "week_of": "01/06-01/10/2026",
        },
        "days": {
            "monday": {
                "unit_lesson": "U1",
                "objective": {
                    "content_objective": "c",
                    "student_goal": "s",
                    "wida_objective": "w",
                },
            },
        },
    }
    llm = MagicMock()
    llm.transform_lesson.return_value = (True, minimal_lesson, None)
    processor.llm_service = llm

    slot = {"slot_number": 1, "subject": "Math", "grade": "2"}
    ctx = SlotProcessingContext(
        slot=slot,
        slot_index=1,
        total_slots=1,
        extracted_content="long enough primary text for the transform path",
        available_days=None,
    )

    async def fake_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(
        "tools.batch_processor_pkg.transform.asyncio.to_thread", fake_to_thread
    )

    out = await transform_slot_with_llm(
        processor, ctx, "01/06-01/10/2026", "openai", plan_id=None
    )

    assert llm.transform_lesson.called
    assert out.lesson_json is not None
