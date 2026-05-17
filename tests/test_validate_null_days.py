"""Regression tests for explicit null day values from Instructor model_dump."""

from backend.llm.strategy_pack_context import validate_ell_support_strategy_ids
from backend.llm.validation import validate_structure
from tools.docx_parser.instructional_day import NON_INSTRUCTIONAL_UNIT_LESSON


def _valid_day(unit_lesson: str = "Unit 1 Lesson 1") -> dict:
    return {
        "unit_lesson": unit_lesson,
        "objective": {
            "content_objective": "c",
            "student_goal": "s",
            "wida_objective": "w",
        },
        "anticipatory_set": {"original_content": "a", "bilingual_bridge": "b"},
        "tailored_instruction": {
            "original_content": "t",
            "co_teaching_model": {},
            "ell_support": [],
            "special_needs_support": [],
            "materials": [],
        },
        "misconceptions": {"original_content": "m", "linguistic_note": {}},
        "assessment": {"primary_assessment": "p", "bilingual_overlay": {}},
        "homework": {"original_content": "h", "family_connection": "f"},
        "vocabulary_cognates": [
            {
                "english": f"word{i}",
                "portuguese": f"palavra{i}",
                "is_cognate": False,
                "relevance_note": "note",
            }
            for i in range(6)
        ],
        "sentence_frames": [
            {
                "proficiency_level": "levels_1_2",
                "english": f"frame {i}",
                "portuguese": f"quadro {i}",
                "language_function": "describe",
                "frame_type": "frame",
            }
            for i in range(8)
        ],
    }


def _lesson_json(days: dict) -> dict:
    return {
        "metadata": {
            "week_of": "05/18-05/22",
            "grade": "6",
            "subject": "Social Studies",
        },
        "days": days,
    }


def test_validate_structure_null_days_partial_week_fills_non_available():
    lesson_json = _lesson_json(
        {
            "monday": None,
            "tuesday": None,
            "wednesday": None,
            "thursday": _valid_day("Lesson 2"),
            "friday": _valid_day("Lesson 3"),
        }
    )

    valid, err = validate_structure(
        lesson_json, available_days=["thursday", "friday"]
    )

    assert valid, err
    for day in ("monday", "tuesday", "wednesday"):
        assert lesson_json["days"][day]["unit_lesson"] == NON_INSTRUCTIONAL_UNIT_LESSON
    assert lesson_json["days"]["thursday"]["unit_lesson"] == "Lesson 2"
    assert lesson_json["days"]["friday"]["unit_lesson"] == "Lesson 3"


def test_validate_structure_null_available_day_fails_for_retry():
    lesson_json = _lesson_json(
        {
            "thursday": _valid_day("Lesson 2"),
            "friday": None,
        }
    )

    valid, err = validate_structure(
        lesson_json, available_days=["thursday", "friday"]
    )

    assert not valid
    assert "friday" in (err or "")


def test_validate_structure_only_monday_null_does_not_raise():
    lesson_json = _lesson_json({"monday": None})

    valid, err = validate_structure(lesson_json)

    assert valid, err
    assert isinstance(lesson_json["days"]["monday"], dict)
    assert lesson_json["days"]["monday"]["unit_lesson"] == "No School"


def test_validate_ell_support_strategy_ids_skips_null_day():
    ok, err, bad = validate_ell_support_strategy_ids({"days": {"monday": None}})
    assert ok
    assert err is None
    assert bad == []
