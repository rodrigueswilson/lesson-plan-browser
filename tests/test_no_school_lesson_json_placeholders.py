"""No-school lesson JSON: section placeholders empty; unit_lesson carries the label."""

from backend.llm.validation import validate_structure
from tools.batch_processor_pkg.slot_flow_no_school import build_no_school_day_json


def _minimal_valid_monday() -> dict:
    """Single day with 6 vocab and 8 frames (required for validate_structure on lesson days)."""
    return {
        "unit_lesson": "Unit 1",
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
                "english": f"w{i}",
                "portuguese": f"p{i}",
                "is_cognate": False,
                "relevance_note": "n",
            }
            for i in range(6)
        ],
        "sentence_frames": [
            {
                "proficiency_level": "levels_1_2",
                "english": f"e{i}",
                "portuguese": f"pt{i}",
                "language_function": "describe",
                "frame_type": "frame",
            }
            for i in range(8)
        ],
    }


def test_build_no_school_day_json_uses_empty_section_bodies():
    slot = {"grade": "3", "subject": "Math", "homeroom": "A"}
    j = build_no_school_day_json("1/6-1/10/2025", slot, [])
    mon = j["days"]["monday"]
    assert mon["unit_lesson"] == "No School"
    assert mon["objective"]["content_objective"] == "No School"
    assert mon["anticipatory_set"]["original_content"] == ""
    assert mon["anticipatory_set"]["bilingual_bridge"] == ""
    assert mon["tailored_instruction"]["original_content"] == ""
    assert mon["misconceptions"]["original_content"] == ""
    assert mon["assessment"]["primary_assessment"] == ""
    assert mon["homework"]["original_content"] == ""
    assert mon["homework"]["family_connection"] == ""


def test_validate_structure_inserts_empty_sections_for_missing_no_school_days():
    lesson_json = {
        "metadata": {
            "week_of": "02/09-02/13",
            "grade": "2",
            "subject": "ELA",
        },
        "days": {"monday": _minimal_valid_monday()},
    }
    valid, err = validate_structure(lesson_json)
    assert valid, err
    for day in ("tuesday", "wednesday", "thursday", "friday"):
        d = lesson_json["days"][day]
        assert d["unit_lesson"] == "No School"
        assert d["anticipatory_set"]["original_content"] == ""
        assert d["tailored_instruction"]["original_content"] == ""
        assert d["assessment"]["primary_assessment"] == ""
        assert d["homework"]["original_content"] == ""
