"""Sentence-frame extraction skips No School and Non-instructional (assessment) like objectives."""

from backend.services.sentence_frames.extraction import extract_sentence_frames
from backend.services.sentence_frames_pdf_generator import SentenceFramesPDFGenerator
from tools.docx_parser.instructional_day import NON_INSTRUCTIONAL_UNIT_LESSON


def _sample_frames():
    return [
        {
            "proficiency_level": "levels_1_2",
            "english": "**Sample** frame",
            "language_function": "explain",
        },
        {"proficiency_level": "levels_1_2", "english": "b", "language_function": "describe"},
        {"proficiency_level": "levels_1_2", "english": "c", "language_function": "justify"},
        {"proficiency_level": "levels_3_4", "english": "d", "language_function": "compare"},
        {"proficiency_level": "levels_3_4", "english": "e", "language_function": "analyze"},
        {"proficiency_level": "levels_3_4", "english": "f", "language_function": "evaluate"},
        {"proficiency_level": "levels_5_6", "english": "g", "language_function": "argue"},
        {"proficiency_level": "levels_5_6", "english": "h", "language_function": "summarize"},
    ]


def test_extract_sentence_frames_skips_non_instructional_multi_slot():
    lesson_json = {
        "metadata": {
            "week_of": "January 6-10, 2026",
            "grade": "3",
            "subject": "ELA",
        },
        "days": {
            "monday": {
                "slots": [
                    {
                        "slot_number": 1,
                        "subject": "ELA",
                        "unit_lesson": NON_INSTRUCTIONAL_UNIT_LESSON,
                        "sentence_frames": _sample_frames(),
                    },
                    {
                        "slot_number": 2,
                        "subject": "ELA",
                        "unit_lesson": "Unit 1: Reading",
                        "sentence_frames": _sample_frames(),
                    },
                ],
            },
        },
    }
    rows = extract_sentence_frames(lesson_json)
    assert len(rows) == 1
    assert rows[0]["slot_number"] == 2
    assert "Reading" in rows[0]["unit_lesson"]


def test_extract_sentence_frames_skips_non_instructional_single_day():
    lesson_json = {
        "metadata": {
            "week_of": "January 6-10, 2026",
            "grade": "4",
            "subject": "Math",
        },
        "days": {
            "tuesday": {
                "unit_lesson": NON_INSTRUCTIONAL_UNIT_LESSON,
                "sentence_frames": _sample_frames(),
            },
        },
    }
    assert extract_sentence_frames(lesson_json) == []


def test_extract_sentence_frames_all_non_instructional_week_returns_empty():
    lesson_json = {
        "metadata": {
            "week_of": "Feb 3-7, 2026",
            "grade": "3",
            "subject": "Science",
        },
        "days": {
            "monday": {
                "slots": [
                    {
                        "slot_number": 1,
                        "unit_lesson": NON_INSTRUCTIONAL_UNIT_LESSON,
                        "sentence_frames": [],
                    },
                ],
            },
        },
    }
    assert extract_sentence_frames(lesson_json) == []


def test_sentence_frames_pdf_generator_extract_aligns_with_extract_sentence_frames():
    lesson_json = {
        "metadata": {"week_of": "Jan 6-10", "grade": "3", "subject": "Art"},
        "days": {
            "wednesday": {
                "slots": [
                    {
                        "slot_number": 1,
                        "unit_lesson": NON_INSTRUCTIONAL_UNIT_LESSON,
                        "sentence_frames": _sample_frames(),
                    },
                    {
                        "slot_number": 2,
                        "unit_lesson": "Unit 2",
                        "sentence_frames": _sample_frames(),
                    },
                ],
            },
        },
    }
    gen = SentenceFramesPDFGenerator()
    assert gen.extract_sentence_frames(lesson_json) == extract_sentence_frames(lesson_json)
