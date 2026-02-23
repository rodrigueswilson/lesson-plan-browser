"""
Section name to keyword mappings for matching hyperlinks and images to cells.
"""

SECTION_MAPPINGS = {
    "unit_lesson": ["unit", "lesson", "module"],
    "objective": ["objective", "goal", "swbat"],
    "anticipatory_set": ["anticipatory", "warm up", "hook", "do now", "entry"],
    "tailored_instruction": [
        "instruction",
        "activity",
        "procedure",
        "lesson",
        "tailored",
        "differentiation",
    ],
    "misconceptions": ["misconception", "misconceptions", "error", "pitfall"],
    "assessment": ["assessment", "check", "evaluate", "exit ticket"],
    "homework": ["homework", "assignment", "practice"],
}


def section_matches(section_name: str, hint: str) -> bool:
    """Return True if hint matches section_name (exact or via SECTION_MAPPINGS)."""
    if not hint:
        return False
    hint = hint.lower().strip()
    if hint == section_name:
        return True
    if section_name not in SECTION_MAPPINGS:
        return False
    keywords = SECTION_MAPPINGS[section_name]
    if hint in keywords:
        return True
    return any(kw in hint for kw in keywords if len(kw) > 3)
