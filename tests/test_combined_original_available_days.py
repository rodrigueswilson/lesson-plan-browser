"""Regression: parallel file-group extraction must infer available_days from table_content."""

from tools.batch_processor_pkg.slot_flow_extract import get_available_days_from_content


def test_parser_like_payload_without_available_days_key_is_not_empty_list_when_instructional():
    """Simulates extract_subject_content_for_slot output: no available_days key."""
    content = {
        "full_text": "narrative",
        "table_content": {
            "monday": {
                "Unit / Lesson": (
                    "Unit 3 Lesson 9: MEASURE TO FIND THE AREA AND PERIMETER "
                    "with sufficient text for substantive_day_text"
                ),
            },
            "tuesday": {"Unit / Lesson": "NJ-SLA testing day benchmark assessment"},
            "wednesday": {
                "Unit / Lesson": (
                    "Unit 4 Lesson 1: Compare fractions using visual models "
                    "and number lines for grade instruction"
                ),
            },
            "thursday": {"Unit / Lesson": ""},
            "friday": {"Unit / Lesson": "n/a"},
        },
    }
    days = get_available_days_from_content(content)
    assert days is not None
    assert "monday" in days
    assert "wednesday" in days
    assert "tuesday" not in days


def test_parser_like_payload_no_table_content_returns_none_not_empty_list():
    content = {"full_text": "only narrative without structured table_content"}
    assert get_available_days_from_content(content) is None


def test_old_bug_pattern_get_available_days_vs_default_empty():
    """Document why .get('available_days', []) was wrong: missing key is not []."""
    content = {
        "full_text": "x",
        "table_content": {
            "monday": {"Unit": "Unit 1 Lesson 2: Regular lesson prose here with enough length"}
        },
    }
    wrong_if_used = content.get("available_days", [])
    assert wrong_if_used == []
    correct = get_available_days_from_content(content)
    assert correct == ["monday"]
