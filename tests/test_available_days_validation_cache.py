"""Regression tests for partial-week validation and cached available_days."""

from types import SimpleNamespace

from backend.llm.validation import validate_structure
from tools.batch_processor_pkg.combined_original import _available_days_for_cached_record
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
            "week_of": "05/04-05/08",
            "grade": "3",
            "subject": "ELA",
        },
        "days": days,
    }


def test_validate_structure_partial_week_fills_non_available_as_assessment():
    lesson_json = _lesson_json(
        {
            "thursday": _valid_day("Lesson 2: Chapters 3-4"),
            "friday": _valid_day("Lesson 3: Chapters 5-6"),
        }
    )

    valid, err = validate_structure(
        lesson_json, available_days=["thursday", "friday"]
    )

    assert valid, err
    for day in ("monday", "tuesday", "wednesday"):
        assert lesson_json["days"][day]["unit_lesson"] == NON_INSTRUCTIONAL_UNIT_LESSON
        assert (
            lesson_json["days"][day]["objective"]["content_objective"]
            == NON_INSTRUCTIONAL_UNIT_LESSON
        )
    assert lesson_json["days"]["thursday"]["unit_lesson"].startswith("Lesson 2")
    assert lesson_json["days"]["friday"]["unit_lesson"].startswith("Lesson 3")


def test_validate_structure_missing_available_day_fails_for_retry():
    lesson_json = _lesson_json({"thursday": _valid_day("Lesson 2: Chapters 3-4")})

    valid, err = validate_structure(
        lesson_json, available_days=["thursday", "friday"]
    )

    assert not valid
    assert "friday" in (err or "")


def test_cached_available_days_recomputed_from_content_json():
    cached = SimpleNamespace(
        slot_number=2,
        subject="ELA/SS",
        available_days=[],
        content_json={
            "table_content": {
                "Monday": {"Unit/Lesson": "Unit 7 Lesson 14"},
                "Tuesday": {"Unit/Lesson": "Unit 7 Lesson 15"},
                "Wednesday": {"Unit/Lesson": "Unit 7 Lesson 16"},
                "Thursday": {"Unit/Lesson": "Unit 7 Lesson 17"},
                "Friday": {"Unit/Lesson": "Unit 7 Lesson 18"},
            }
        },
    )

    assert _available_days_for_cached_record(cached) == [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
    ]

