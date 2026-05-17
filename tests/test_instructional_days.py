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
def test_is_testing_or_assessment_day_detects_njsla_and_non_instructional():
    assert is_testing_or_assessment_day("NJ-SLA")
    assert is_testing_or_assessment_day("NJSLA")
    assert is_testing_or_assessment_day("NJ SLA reading")
    assert not is_testing_or_assessment_day(
        "See district non-instructional calendar boilerplate"
    )
    assert is_testing_or_assessment_day("exam period — morning")
    assert is_testing_or_assessment_day("mid-year exam prep")


@pytest.mark.unit
def test_is_testing_or_assessment_day_standalone_exam_cell_only():
    assert is_testing_or_assessment_day("exam")
    assert is_testing_or_assessment_day("  exam day  ")
    assert not is_testing_or_assessment_day(
        "Students prepare for the unit exam next week."
    )


@pytest.mark.unit
def test_is_instructional_lesson_day_short_njsla_and_non_instructional():
    assert not is_instructional_lesson_day("NJSLA")
    assert not is_instructional_lesson_day("benchmark assessment")
    assert is_instructional_lesson_day(
        "Unit 4 Lesson 2: fractions practice with manipulatives."
    )


@pytest.mark.unit
def test_is_instructional_lesson_day_long_text_with_exam_word_not_standalone():
    assert is_instructional_lesson_day(
        "Students prepare for the unit exam next week."
    )


@pytest.mark.unit
def test_infer_instructional_weekdays_mixed_non_instructional_day():
    table = {
        "Monday": {"Unit/Lesson": "Lesson A", "Objective": "Read closely."},
        "Tuesday": {"Unit/Lesson": "Lesson B", "Objective": "Compare texts."},
        "Wednesday": {"Unit/Lesson": "benchmark assessment window", "Objective": ""},
        "Thursday": {"Unit/Lesson": "NJ-SLA", "Objective": ""},
        "Friday": {"Unit/Lesson": "exam period block 1", "Objective": ""},
    }
    assert infer_instructional_weekdays_from_table_content(table) == [
        "monday",
        "tuesday",
    ]


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
def test_infer_instructional_weekdays_notes_column_does_not_poison_unit_lesson():
    """District/notes text must not mark a day non-instructional if Unit/Lesson is a real lesson."""
    table = {
        "Monday": {
            "Unit/Lesson": (
                "Unit 2 Lesson 3: Add and subtract within 100 using concrete models "
                "and story problems for grade two instruction."
            ),
            "Notes": "NJ-SLA testing week district assessment window benchmark",
        },
        "Tuesday": {
            "Unit/Lesson": "Lesson B with enough words for substantive classification.",
            "Notes": "",
        },
        "Wednesday": {"Unit/Lesson": "NJ-SLA", "Notes": "ignored when primary is assessment"},
        "Thursday": {"Unit/Lesson": "Lesson D continuation", "Objective": "Practice fluency."},
        "Friday": {"Unit/Lesson": "Lesson E wrap-up and review stations.", "Notes": "exam period"},
    }
    assert infer_instructional_weekdays_from_table_content(table) == [
        "monday",
        "tuesday",
        "thursday",
        "friday",
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
