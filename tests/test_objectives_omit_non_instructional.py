"""Tests for omitting non-instructional assessment objectives from export."""

from backend.services.objectives.extraction import extract_objectives
from backend.services.objectives.omit import (
    should_omit_objectives_for_unit_lesson,
    should_omit_objectives_from_triple,
    should_omit_sentence_frames_for_unit_lesson,
)
from backend.services.objectives_pdf_generator import ObjectivesPDFGenerator
from tools.docx_parser.instructional_day import NON_INSTRUCTIONAL_UNIT_LESSON


def _objective_row(content: str, student: str, wida: str) -> dict:
    return {
        "content_objective": content,
        "student_goal": student,
        "wida_objective": wida,
    }


def test_omit_helpers_unit_lesson_and_triple():
    assert should_omit_objectives_for_unit_lesson(NON_INSTRUCTIONAL_UNIT_LESSON)
    assert should_omit_sentence_frames_for_unit_lesson(NON_INSTRUCTIONAL_UNIT_LESSON)
    assert should_omit_objectives_for_unit_lesson("no school")
    assert should_omit_sentence_frames_for_unit_lesson("no school")
    assert should_omit_objectives_for_unit_lesson("No School")
    assert not should_omit_objectives_for_unit_lesson("")
    assert not should_omit_sentence_frames_for_unit_lesson("")
    assert not should_omit_objectives_for_unit_lesson("  ")
    assert not should_omit_objectives_for_unit_lesson("Unit 3 Lesson 1: Math")

    label = NON_INSTRUCTIONAL_UNIT_LESSON
    assert should_omit_objectives_from_triple(label, label, label)
    assert should_omit_objectives_from_triple("no school", "no school", "no school")
    assert not should_omit_objectives_from_triple("a", "b", "c")
    assert not should_omit_objectives_from_triple(label, label, "other")


def test_extract_objectives_skips_non_instructional_slot():
    lesson_json = {
        "metadata": {
            "week_of": "January 6-10, 2025",
            "grade": "3",
            "subject": "Math",
        },
        "days": {
            "monday": {
                "slots": [
                    {
                        "slot_number": 1,
                        "subject": "Math",
                        "unit_lesson": NON_INSTRUCTIONAL_UNIT_LESSON,
                        "teacher_name": "",
                        "objective": _objective_row(
                            NON_INSTRUCTIONAL_UNIT_LESSON,
                            NON_INSTRUCTIONAL_UNIT_LESSON,
                            NON_INSTRUCTIONAL_UNIT_LESSON,
                        ),
                    },
                    {
                        "slot_number": 2,
                        "subject": "Math",
                        "unit_lesson": "Unit 2 Lesson 5: Fractions",
                        "teacher_name": "Smith",
                        "objective": _objective_row(
                            "Content goal",
                            "Student goal",
                            "WIDA goal",
                        ),
                    },
                ],
            },
        },
    }
    rows = extract_objectives(lesson_json)
    assert len(rows) == 1
    assert rows[0]["slot_number"] == 2
    assert "Fractions" in rows[0]["unit_lesson"]


def test_objectives_pdf_generator_skips_non_instructional_multi_slot():
    lesson_json = {
        "metadata": {
            "week_of": "January 6-10, 2025",
            "grade": "3",
            "subject": "Math",
            "homeroom": "A",
        },
        "days": {
            "tuesday": {
                "slots": [
                    {
                        "slot_number": 1,
                        "subject": "ELA",
                        "unit_lesson": NON_INSTRUCTIONAL_UNIT_LESSON,
                        "objective": _objective_row(
                            NON_INSTRUCTIONAL_UNIT_LESSON,
                            NON_INSTRUCTIONAL_UNIT_LESSON,
                            NON_INSTRUCTIONAL_UNIT_LESSON,
                        ),
                    },
                    {
                        "slot_number": 2,
                        "subject": "ELA",
                        "unit_lesson": "Unit 1: Reading",
                        "objective": _objective_row("c", "s", "w"),
                    },
                ],
            },
        },
    }
    gen = ObjectivesPDFGenerator()
    rows = gen.extract_objectives(lesson_json)
    assert len(rows) == 1
    assert rows[0]["slot_number"] == 2


def test_objectives_pdf_generator_skips_non_instructional_single_day():
    lesson_json = {
        "metadata": {
            "week_of": "January 6-10, 2025",
            "grade": "4",
            "subject": "Science",
            "homeroom": "B",
        },
        "days": {
            "wednesday": {
                "unit_lesson": NON_INSTRUCTIONAL_UNIT_LESSON,
                "objective": _objective_row(
                    NON_INSTRUCTIONAL_UNIT_LESSON,
                    NON_INSTRUCTIONAL_UNIT_LESSON,
                    NON_INSTRUCTIONAL_UNIT_LESSON,
                ),
            },
        },
    }
    gen = ObjectivesPDFGenerator()
    rows = gen.extract_objectives(lesson_json)
    assert rows == []
