"""Unit tests for instructional vs assessment weekday detection."""

import pytest

from backend.services.lesson_steps.slot_data import (
    should_skip_lesson_steps_for_unit_lesson,
)
from tools.batch_processor_pkg.slot_flow_extract import get_available_days_from_content
from tools.docx_parser.instructional_day import (
    NON_INSTRUCTIONAL_UNIT_LESSON,
    infer_instructional_weekdays_from_table_content,
    is_instructional_lesson_day,
    is_testing_or_assessment_day,
    substantive_day_text,
)


@pytest.mark.unit
def test_substantive_day_text_accepts_lesson_snippet():
    assert substantive_day_text(
        "Students read Charlotte's Web chapter 3 and summarize main ideas."
    )


@pytest.mark.unit
def test_substantive_day_text_rejects_placeholders():
    assert not substantive_day_text("")
    assert not substantive_day_text("   ")
    assert not substantive_day_text("-")
    assert not substantive_day_text("n/a")


@pytest.mark.unit
def test_is_testing_or_assessment_day_detects_common_labels():
    assert is_testing_or_assessment_day("STAAR math")
    assert is_testing_or_assessment_day("State assessment — reading")
    assert is_testing_or_assessment_day("Students are testing today.")


@pytest.mark.unit
def test_is_instructional_lesson_day_excludes_assessment_and_no_school():
    assert is_instructional_lesson_day(
        "Unit 4 Lesson 2: fractions practice with manipulatives."
    )
    assert not is_instructional_lesson_day("No school — holiday.")
    assert not is_instructional_lesson_day("STAAR testing window — no class.")
    assert not is_instructional_lesson_day("--")


@pytest.mark.unit
def test_infer_instructional_weekdays_partial_week_exam_days():
    table = {
        "Monday": {"Unit/Lesson": "Lesson A", "Objective": "Read closely."},
        "Tuesday": {"Unit/Lesson": "Lesson B", "Objective": "Compare texts."},
        "Wednesday": {"Unit/Lesson": "STAAR", "Objective": ""},
        "Thursday": {"Unit/Lesson": "state testing", "Objective": ""},
        "Friday": {"Unit/Lesson": "MAP test", "Objective": ""},
    }
    assert infer_instructional_weekdays_from_table_content(table) == [
        "monday",
        "tuesday",
    ]


@pytest.mark.unit
def test_infer_instructional_weekdays_all_assessment_returns_empty():
    table = {
        "Monday": {"Unit/Lesson": "STAAR"},
        "Tuesday": {"Unit/Lesson": "STAAR"},
        "Wednesday": {"Unit/Lesson": "benchmark assessment"},
        "Thursday": {"Unit/Lesson": "district assessment"},
        "Friday": {"Unit/Lesson": "exam day"},
    }
    assert infer_instructional_weekdays_from_table_content(table) == []


@pytest.mark.unit
def test_infer_instructional_weekdays_all_days_legacy_monday_only():
    assert infer_instructional_weekdays_from_table_content(
        {"All Days": {"Lesson Content": "Single block text"}}
    ) == ["monday"]


@pytest.mark.unit
def test_get_available_days_from_content_missing_table_returns_none():
    assert get_available_days_from_content({"full_text": "only narrative"}) is None


@pytest.mark.unit
def test_get_available_days_from_content_empty_instructional_returns_empty_list():
    content = {
        "table_content": {
            "Monday": {},
            "Tuesday": {},
            "Wednesday": {},
            "Thursday": {},
            "Friday": {},
        }
    }
    assert get_available_days_from_content(content) == []


@pytest.mark.unit
def test_non_instructional_unit_lesson_constant_stable():
    assert "assessment" in NON_INSTRUCTIONAL_UNIT_LESSON.lower()


@pytest.mark.unit
def test_should_skip_lesson_steps_for_non_instructional_and_no_school():
    assert should_skip_lesson_steps_for_unit_lesson(NON_INSTRUCTIONAL_UNIT_LESSON)
    assert should_skip_lesson_steps_for_unit_lesson("No School week")
    assert not should_skip_lesson_steps_for_unit_lesson("Unit 3 Lesson 4")
