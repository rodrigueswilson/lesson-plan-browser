"""Rules for omitting objectives and sentence-frame print/export rows (DOCX, PDF)."""

from tools.docx_parser.instructional_day import NON_INSTRUCTIONAL_UNIT_LESSON

_NON_INSTRUCTIONAL_LOWER = NON_INSTRUCTIONAL_UNIT_LESSON.strip().lower()


def should_omit_objectives_for_unit_lesson(unit_lesson: str) -> bool:
    """True when this slot/day should not appear in objectives documents."""
    if not unit_lesson or not unit_lesson.strip():
        return False
    ul = unit_lesson.strip().lower()
    if ul == "no school":
        return True
    return ul == _NON_INSTRUCTIONAL_LOWER


def should_omit_sentence_frames_for_unit_lesson(unit_lesson: str) -> bool:
    """True when this slot/day should not appear in sentence-frames print/export."""
    return should_omit_objectives_for_unit_lesson(unit_lesson)


def should_omit_objectives_from_triple(
    content_objective: str,
    student_goal: str,
    wida_objective: str,
) -> bool:
    """True when all three fields are No School or non-instructional placeholders."""
    c = (content_objective or "").strip().lower()
    s = (student_goal or "").strip().lower()
    w = (wida_objective or "").strip().lower()
    if c == "no school" and s == "no school" and w == "no school":
        return True
    if c == _NON_INSTRUCTIONAL_LOWER and s == _NON_INSTRUCTIONAL_LOWER and w == _NON_INSTRUCTIONAL_LOWER:
        return True
    return False
