"""Science curriculum: lesson heading heuristics in table_extractor."""

from tools.scraper.table_extractor import (
    _is_science_subject,
    _science_lesson_title_is_structural_noise,
    _science_lesson_title_too_weak,
)


def test_science_lesson_title_too_weak():
    assert _science_lesson_title_too_weak("") is True
    assert _science_lesson_title_too_weak(":") is True
    assert _science_lesson_title_too_weak("What is Matter?") is False


def test_science_lesson_title_is_structural_noise():
    assert _science_lesson_title_is_structural_noise("Resources") is True
    assert _science_lesson_title_is_structural_noise("days") is True
    assert _science_lesson_title_is_structural_noise("Vocabulary") is True
    assert _science_lesson_title_is_structural_noise("Describe Matter") is False
    assert _science_lesson_title_is_structural_noise("Additional Resources") is False


def test_is_science_subject():
    assert _is_science_subject("Science") is True
    assert _is_science_subject("SCI") is True
    assert _is_science_subject("Math") is False
